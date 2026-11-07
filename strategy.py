"""Evidence-led strategy, not platform algorithm manipulation.

Explores UK posting slots and content themes before exploiting a winner.
Requires sufficient real per-post Buffer metrics; otherwise uses fair rotation.
"""
import datetime as dt
import json
from pathlib import Path

from creative_library import OFFERS

SLOTS = [
    ("17 12 * * *", 12),
    ("17 18 * * *", 18),
    ("17 20 * * *", 20),
]
TOPICS = [
    "routine", "routine", "family", "11plus", "progress",
    "routine", "quiz", "11plus", "maths", "english",
    "reasoning", "routine", "routine", "routine", "quiz",
    "family", "learning_stages", "homework", "routine",
    "routine", "general", "family",
]
assert len(TOPICS) == len(OFFERS)

def history(performance_path):
    try:
        return json.loads(Path(performance_path).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}

def creative_topic(creative_id):
    if not isinstance(creative_id, str):
        return None
    try:
        kind, raw = creative_id.split("-", 1)
        idx = int(raw)
    except (TypeError, ValueError):
        return None
    if kind == "quiz":
        return "quiz"
    if kind == "offer" and 0 <= idx < len(TOPICS):
        return TOPICS[idx]
    return None

def choose_offer(day, baseline, performance_path):
    report = history(performance_path)
    best_topic = report.get("adaptive", {}).get("top_topic")
    if day.toordinal() % 5 == 0 or not best_topic:
        return baseline  # 20% exploration, always
    candidates = [i for i, topic in enumerate(TOPICS) if topic == best_topic]
    if not candidates:
        return baseline
    return candidates[(day.toordinal() // 5) % len(candidates)]

def select_slot(day, performance_path):
    report = history(performance_path)
    recommended = report.get("adaptive", {}).get("top_slot")
    # Keep testing 1 in 4 days. Never assume a winning slot without results.
    if recommended in (12, 18, 20) and day.toordinal() % 4:
        return recommended
    return SLOTS[day.toordinal() % len(SLOTS)][1]

def expected_cron_for(day, performance_path):
    selected = select_slot(day, performance_path)
    for expr, hour in SLOTS:
        if hour == selected:
            return expr
    raise RuntimeError("Unknown UK posting slot")
