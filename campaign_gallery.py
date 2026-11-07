"""Select approved ExamBloom image adverts already uploaded into assets/campaigns.

Only publish existing files. Missing assets always fall back to the normal creative
generator, so a partial upload never breaks the live posting workflow.
"""
import datetime as dt
import json
from pathlib import Path

CAMPAIGNS = Path(__file__).parent / "assets" / "campaigns"
FIRST_DATE = dt.date(2026, 11, 9)
SALES_WEEKDAYS = (0, 1, 3, 4)  # Monday Tuesday Thursday Friday; Wed/Sat stay quizzes.

def scheduled_gallery_index(day):
    """One of 8 gallery positions per sales day, repeating every two weeks."""
    if day < FIRST_DATE or day.weekday() not in SALES_WEEKDAYS:
        return None
    n = sum(1 for offset in range((day - FIRST_DATE).days + 1)
            if (FIRST_DATE + dt.timedelta(days=offset)).weekday() in SALES_WEEKDAYS)
    return (n - 1) % 8

def select_campaign(day, root=None):
    index = scheduled_gallery_index(day)
    if index is None:
        return None
    folder = Path(root) if root is not None else CAMPAIGNS
    manifest = folder / "manifest.json"
    try:
        obj = json.loads(manifest.read_text(encoding="utf-8"))
        items = obj["campaigns"]
        if len(items) < 8:
            return None
        entry = items[index]
        name = entry["file"]
        # Restrict manifest to local, explicit JPGs within the campaign folder.
        if not isinstance(name, str) or Path(name).name != name or not name.lower().endswith((".jpg", ".jpeg")):
            return None
        asset = folder / name
        if not asset.is_file():
            return None
        return dict(entry, asset_path=asset)
    except (FileNotFoundError, ValueError, KeyError, TypeError, IndexError, OSError):
        return None

def as_post(entry, day, destination, url_for):
    heading = entry["headline"]
    cta = entry["cta"]
    detail = entry["detail"]
    hashtags = entry["hashtags"]
    return {
        "date": day.isoformat(),
        "category": "membership",
        "headline": heading,
        "detail": detail,
        "helper": "Practice tests • Guided learning • Daily games",
        "creative_id": "gallery-" + entry["id"],
        "gallery_asset": str(entry["asset_path"].relative_to(Path(__file__).parent)),
        "facebook_caption": (
            f"{heading[0]} {heading[1]}\n\n{detail}\n\n{cta} "
            f"{url_for(day, 'gallery-' + entry['id'], destination)}\n\n{hashtags}"
        ),
        "instagram_caption": (
            f"{heading[0]} {heading[1]}\n\n{detail}\n\n{cta} "
            f"Visit the website link in our profile.\n\n{hashtags}"
        ),
        "site": "https://exambloom.co.uk",
    }
