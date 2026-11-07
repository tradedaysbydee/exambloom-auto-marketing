"""Daily ExamBloom Buffer insights. Read-only to Buffer; no customer or billing data.
Uses documented personal-key post metrics; unavailable metrics remain unknown, not zero.
"""
import datetime as dt
import json
import os
import statistics
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

from buffer_publish import gql, ORG_QUERY, CHANNEL_QUERY, LOG
from bot import ROOT, git_save, today

OUT = ROOT / "data" / "performance.json"
REPORT = ROOT / "PERFORMANCE.md"
TARGET = 1_000_000

POSTS_QUERY = """query ExamBloomInsights($input: PostsInput!, $first: Int!, $after: String) {
  posts(input: $input, first: $first, after: $after) {
    edges { node {
      id status sentAt dueAt channelId
      metrics { type value unit }
      metricsUpdatedAt
    } }
    pageInfo { hasNextPage endCursor }
  }
}"""
POSTS_STATUS_QUERY = """query ExamBloomStatus($input: PostsInput!, $first: Int!, $after: String) {
  posts(input: $input, first: $first, after: $after) {
    edges { node { id status sentAt dueAt channelId } }
    pageInfo { hasNextPage endCursor }
  }
}"""

def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default

def metric_map(metrics):
    # Missing metrics are NOT zero; do not introduce zeros for unsupported values.
    return {str(m["type"]): float(m["value"]) for m in (metrics or []) if m.get("value") is not None}

def exposure(metrics):
    # Choose one exposure family per post, never add views + impressions + reach.
    for key in ("impressions", "views", "reach"):
        if key in metrics:
            return int(metrics[key]), key
    return None, None

def quality_score(metrics):
    seen, _ = exposure(metrics)
    if not seen or seen < 100:
        return None
    engagements = (
        metrics.get("reactions", 0) +
        2 * metrics.get("comments", 0) +
        5 * metrics.get("shares", 0) +
        4 * metrics.get("saves", 0) +
        4 * metrics.get("follows", 0) +
        3 * metrics.get("reposts", 0)
    )
    return round(1000 * engagements / seen, 3)

def find_posts(org_id, channel_id, with_metrics=True):
    cursor = None
    output = []
    for page_no in range(3):  # at most 300 recent posts per channel
        variables = {
            "input": {"organizationId": org_id,
                      "filter": {"status": ["sent"], "channelIds": [channel_id]}},
            "first": 100, "after": cursor
        }
        obj = gql(POSTS_QUERY if with_metrics else POSTS_STATUS_QUERY, variables)["posts"]
        output.extend(e["node"] for e in obj["edges"])
        next_page = obj.get("pageInfo") or {}
        cursor = next_page.get("endCursor")
        if not next_page.get("hasNextPage") or not cursor:
            break
    return output

def collect():
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    history = read_json(LOG, {})
    prior = read_json(OUT, {})
    records = prior.get("records", {})
    targets = {}
    for day, services in history.items():
        for service in ("instagram", "tiktok"):
            details = services.get(service)
            if details and details.get("post_id"):
                targets[details["post_id"]] = {"day": day, "platform": service}

    orgs = gql(ORG_QUERY)["account"]["organizations"]
    messages = []
    for org in orgs:
        channels = gql(CHANNEL_QUERY, {"input": {"organizationId": org["id"]}})["channels"]
        for chan in channels:
            platform = str(chan.get("service", "")).lower()
            if platform not in ("instagram", "tiktok"):
                continue
            try:
                posts = find_posts(org["id"], chan["id"], with_metrics=True)
                status_label = "metrics available"
            except Exception as exc:
                messages.append(platform + " metrics unavailable: " + str(exc)[:140])
                try:
                    posts = find_posts(org["id"], chan["id"], with_metrics=False)
                    status_label = "status only"
                except Exception as exc2:
                    messages.append(platform + " status unavailable: " + str(exc2)[:140])
                    continue
            for p in posts:
                item = targets.get(p["id"])
                if item is None or item["platform"] != platform:
                    continue
                metrics = metric_map(p.get("metrics"))
                entry = records.setdefault(p["id"], dict(item))
                entry.update({
                    "status": str(p.get("status", "unknown")),
                    "sent_at": p.get("sentAt"),
                    "metrics_updated_at": p.get("metricsUpdatedAt"),
                    "metrics": metrics if metrics else entry.get("metrics", {}),
                })
                entry["insights_state"] = status_label
                # Discover creative ID from original generated metadata if available.
                creative = read_json(ROOT / "generated" / (item["day"] + ".json"), {})
                entry["category"] = creative.get("category", "unknown")
                entry["creative_id"] = creative.get("creative_id", "unknown")

    # Respect the publisher history even while a newly submitted post is still 'sending'.
    for pid, item in targets.items():
        records.setdefault(pid, dict(item, status="submitted", metrics={}))
    by_platform = defaultdict(lambda: {"posts": 0, "with_metrics": 0,
                                        "exposure_events": 0, "reactions": 0,
                                        "comments": 0, "shares": 0, "saves": 0})
    observations = []
    for pid, item in records.items():
        if pid not in targets:
            continue
        platform = item["platform"]
        section = by_platform[platform]
        section["posts"] += 1
        m = item.get("metrics") or {}
        n, family = exposure(m)
        if n is None:
            continue
        section["with_metrics"] += 1
        section["exposure_events"] += n
        for metric_name in ("reactions", "comments", "shares", "saves"):
            section[metric_name] += int(m.get(metric_name, 0))
        points = quality_score(m)
        if points is not None and item.get("creative_id") not in (None, "unknown"):
            observations.append({"creative_id": item["creative_id"],
                                 "platform": platform, "score": points,
                                 "exposures": n})

    # Choose creative only with several independently observed posts.
    candidate_scores = defaultdict(list)
    for item in observations:
        candidate_scores[item["creative_id"]].append(item["score"])
    score_table = {
        key: {"sample_size": len(values), "median_quality_per_1000": round(statistics.median(values), 3)}
        for key, values in candidate_scores.items()
    }
    eligible = [(k, v) for k, v in score_table.items() if v["sample_size"] >= 3]
    winner = max(eligible, key=lambda e: e[1]["median_quality_per_1000"])[0] if eligible else None

    lifetime = sum(d["exposure_events"] for d in by_platform.values())
    result = {
        "updated_at": now,
        "goal": {"metric": "summed post exposure events (NOT unique people)",
                 "target": TARGET, "observed": lifetime},
        "platforms": dict(by_platform),
        "records": records,
        "adaptive": {"eligible_top_creative": winner, "creative_scores": score_table,
                     "minimum_posts_per_creative": 3,
                     "notes": "Engagement-weighted observations; no knowledge of ranking algorithms."},
        "issues": messages,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# ExamBloom organic marketing — performance history", "",
             f"Last checked (UTC): {now}", "",
             "**Goal:** 1,000,000 measured exposure events. This is not a count of unique people, "
             "nor a guarantee of reach. Views and impressions can count repeats.", "",
             "| Platform | Submitted posts | Posts with metrics | Exposure events | Reactions | Comments | Shares |",
             "|:--|--:|--:|--:|--:|--:|--:|"]
    for key in ("instagram", "tiktok"):
        d = by_platform[key]
        lines.append(f"| {key.title()} | {d['posts']} | {d['with_metrics']} | "
                     f"{d['exposure_events']:,} | {d['reactions']:,} | "
                     f"{d['comments']:,} | {d['shares']:,} |")
    lines.extend(["", f"**Observed exposure events:** {lifetime:,} / {TARGET:,} "
                  f"({lifetime/TARGET:.2%} of target)", "",
                  "Metrics are refreshed by Buffer roughly once per day. Missing measurements "
                  "are unknown, not zero. Comparing summed exposure events with unique reach is not valid.", "",
                  "**Sales:** Not available until ExamBloom's subscription checkout reports verified "
                  "purchases with campaign attribution. This report does not invent purchases.", "",
                  f"**Current experimental top creative:** {winner or 'Not enough evidence yet'}", ""])
    if messages:
        lines += ["**Data limitations:**", *("- " + s for s in messages), ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    return result

if __name__ == "__main__":
    data = collect()
    print("Exposure events recorded:", data["goal"]["observed"])
    print("Metric coverage:", {k: v["with_metrics"] for k, v in data["platforms"].items()})
    if data["issues"]:
        print("Warnings:", "; ".join(data["issues"]))
    git_save(["data/performance.json", "PERFORMANCE.md"],
             "Update ExamBloom social metrics and reach progress")
