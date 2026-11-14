"""Approved ExamBloom quiz pictures for Wednesday and Saturday social posts.

Preserves the old schedule until all ten specifically named pictures are present.
"""
import datetime as dt
import json
from pathlib import Path

CAMPAIGNS = Path(__file__).parent / "assets" / "campaigns"
FIRST_QUIZ_DATE = dt.date(2026, 11, 18)
QUIZ_WEEKDAYS = (2, 5)
REQUIRED_COUNT = 10

def select_quiz_campaign(day, root=None):
    if day < FIRST_QUIZ_DATE or day.weekday() not in QUIZ_WEEKDAYS:
        return None
    folder = Path(root) if root is not None else CAMPAIGNS
    try:
        entries = json.loads((folder / "quiz_manifest.json").read_text(encoding="utf-8"))["campaigns"]
        if len(entries) != REQUIRED_COUNT:
            return None
        for entry in entries:
            name = entry["file"]
            if (not isinstance(name, str) or Path(name).name != name
                    or not name.lower().endswith((".jpg", ".jpeg"))
                    or not (folder / name).is_file()):
                return None
        n = sum(1 for offset in range((day - FIRST_QUIZ_DATE).days + 1)
                if (FIRST_QUIZ_DATE + dt.timedelta(days=offset)).weekday() in QUIZ_WEEKDAYS)
        entry = entries[(n - 1) % len(entries)]
        return dict(entry, asset_path=folder / entry["file"])
    except (FileNotFoundError, ValueError, KeyError, TypeError, IndexError, OSError):
        return None
