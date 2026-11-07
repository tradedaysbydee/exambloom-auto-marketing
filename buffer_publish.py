"""Publish the daily ExamBloom graphic to connected Instagram and TikTok via Buffer.
Requires owner's Buffer API key and connected channels. Defaults to preview/no posting.
See https://developers.buffer.com/reference.html for createPost GraphQL schema.
"""
import datetime as dt
import json
import os
import time
from pathlib import Path
from urllib.parse import quote

import requests

from bot import ROOT, git_save, SITE, today
from strategy import expected_cron_for

API = "https://api.buffer.com"
LOG = ROOT / "data" / "buffer_history.json"

ORG_QUERY = """query ExamBloomOrganizations { account { organizations { id } } }"""
CHANNEL_QUERY = """query ExamBloomChannels($input: ChannelsInput!) {
  channels(input: $input) { id name service isDisconnected isLocked }
}"""
POST_MUTATION = """mutation ExamBloomPublish($input: CreatePostInput!) {
  createPost(input: $input) {
    __typename
    ... on PostActionSuccess { post { id status schedulingType } }
    ... on MutationError { message }
  }
}"""

def gql(query, variables=None):
    token = os.environ.get("BUFFER_API_KEY", "").strip()
    if not token:
        raise RuntimeError("BUFFER_API_KEY is missing. Add it as a GitHub Actions secret.")
    try:
        response = requests.post(
            API,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"query": query, "variables": variables or {}}, timeout=45
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError("Buffer API is unavailable; inspect the GitHub Actions log.") from exc
    if payload.get("errors"):
        raise RuntimeError("Buffer GraphQL rejected a request: " +
                           str(payload["errors"][0].get("message", "Unknown error"))[:250])
    return payload.get("data", {})

def connected_channels():
    accounts = gql(ORG_QUERY)["account"]["organizations"]
    selected = {}
    for organization in accounts:
        channels = gql(CHANNEL_QUERY, {"input": {"organizationId": organization["id"]}})["channels"]
        for channel in channels:
            service = channel["service"].lower()
            if service not in ("instagram", "tiktok") or channel["isDisconnected"] or channel["isLocked"]:
                continue
            if service in selected:
                raise RuntimeError(f"Multiple {service} accounts connected to Buffer; select a single ExamBloom account.")
            selected[service] = channel
    if not selected:
        raise RuntimeError("Connect an Instagram professional account and/or TikTok to Buffer first.")
    return selected

def verify_image(url):
    for attempt in range(12):
        try:
            r = requests.get(url, timeout=20)
            if r.ok and r.headers.get("Content-Type", "").startswith("image/") and len(r.content) > 5000:
                return
        except requests.RequestException:
            pass
        time.sleep(5)
    raise RuntimeError("Generated image is not publicly accessible on GitHub.")

def build_input(channel, image_url, post):
    service = channel["service"].lower()
    if service == "instagram":
        metadata = {"instagram": {"type": "post", "shouldShareToFeed": True}}
        body = post["instagram_caption"]
    elif service == "tiktok":
        metadata = {"tiktok": {"title": post["headline"][0][:80]}}
        body = (
            f'{post["headline"][0]} {post["headline"][1]}\n\n'
            f'{post["detail"]}\n\n'
            "Parents: try ExamBloom via the link in our profile. "
            "#ExamBloom #ParentTips #UKParents #LearningAtHome"
        )
    else:
        raise ValueError("Unexpected channel")
    return {
        "channelId": channel["id"],
        "mode": "shareNow",
        "needsApproval": False,
        "schedulingType": "automatic",
        "aiAssisted": False,
        "saveToDraft": False,
        "text": body,
        "assets": [{
            "image": {
                "url": image_url,
                "metadata": {
                    "altText": "ExamBloom educational practice test promotion for UK parents"
                }
            }
        }],
        "metadata": metadata,
    }

def run():
    current = today()
    image_file = ROOT / "generated" / f"{current.isoformat()}.jpg"
    post_file = ROOT / "generated" / f"{current.isoformat()}.json"
    if not image_file.exists() or not post_file.exists():
        raise RuntimeError("Run python bot.py --preview first to generate today's post.")
    if os.environ.get("PUBLISH_ENABLED", "false").lower() != "true":
        print("SAFE MODE: Buffer posting disabled, files generated; no publishing.")
        return

    if os.environ.get("GITHUB_EVENT_NAME") == "schedule":
        expected = expected_cron_for(current, ROOT / "data" / "performance.json")
        triggered = os.environ.get("GITHUB_SCHEDULE", "").strip()
        if triggered != expected:
            print("Experiment: skipping this slot. Today's chosen cron:", expected)
            return
        print("Experiment: selected UK posting slot:", triggered)

    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    if not repo or "/" not in repo:
        raise RuntimeError("Buffer publishing must run inside the configured GitHub repository.")

    post = json.loads(post_file.read_text(encoding="utf-8"))
    git_save([f"generated/{image_file.name}", f"generated/{post_file.name}"],
             "Create ExamBloom " + current.isoformat() + " campaign")
    image_url = f"https://raw.githubusercontent.com/{repo}/{branch}/generated/{quote(image_file.name)}"
    verify_image(image_url)

    history = json.loads(LOG.read_text()) if LOG.exists() else {}
    record = history.setdefault(current.isoformat(), {})
    channels = connected_channels()
    errors = []
    for service in ("instagram", "tiktok"):
        if service not in channels or record.get(service):
            continue
        try:
            result = gql(POST_MUTATION, {"input": build_input(channels[service], image_url, post)})
            payload = result["createPost"]
            if payload["__typename"] != "PostActionSuccess":
                raise RuntimeError("Buffer rejected the post: " + str(payload.get("message", payload["__typename"]))[:250])
            record[service] = {
                "post_id": payload["post"]["id"],
                "status": payload["post"]["status"],
                "requested_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            }
            LOG.parent.mkdir(parents=True, exist_ok=True)
            LOG.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n")
            git_save(["data/buffer_history.json"], "Record ExamBloom Buffer publication")
            print(service, "accepted by Buffer:", payload["post"]["id"], payload["post"]["status"])
        except Exception as exc:
            errors.append(service + ": " + str(exc))
    if errors:
        raise RuntimeError(" | ".join(errors))
    print("Sent content to Buffer. Verify public publication in the Buffer dashboard.")

if __name__ == "__main__":
    run()
