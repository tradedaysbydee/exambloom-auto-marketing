import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from bot import compose_post, SITE
from campaign_gallery import FIRST_DATE, scheduled_gallery_index, select_campaign

class CampaignGalleryTests(unittest.TestCase):
    def test_rotation_covers_all_eight_ads(self):
        days = [
            dt.date(2026, 11, 9), dt.date(2026, 11, 10),
            dt.date(2026, 11, 12), dt.date(2026, 11, 13),
            dt.date(2026, 11, 16), dt.date(2026, 11, 17),
            dt.date(2026, 11, 19), dt.date(2026, 11, 20),
        ]
        self.assertEqual([scheduled_gallery_index(day) for day in days],
                         list(range(8)))
        self.assertIsNone(scheduled_gallery_index(dt.date(2026, 11, 11)))
        self.assertIsNone(scheduled_gallery_index(dt.date(2026, 11, 14)))

    def test_unavailable_photo_does_not_break_live_post(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            rows = [{"id": str(i), "file": f"{i:02d}.jpg"} for i in range(8)]
            (folder / "manifest.json").write_text(json.dumps({"campaigns": rows}))
            self.assertIsNone(select_campaign(FIRST_DATE, folder))
            (folder / "00.jpg").write_bytes(b"dummy")
            selection = select_campaign(FIRST_DATE, folder)
            self.assertIsNotNone(selection)
            self.assertEqual(selection["file"], "00.jpg")
            self.assertIsNone(select_campaign(FIRST_DATE + dt.timedelta(days=1), folder))

    def test_campaign_manifest_has_eight_distinct_posts(self):
        manifest = Path(__file__).resolve().parent.parent / "assets" / "campaigns" / "manifest.json"
        obj = json.loads(manifest.read_text(encoding="utf-8"))
        rows = obj["campaigns"]
        self.assertEqual(len(rows), 8)
        self.assertEqual(len({row["file"] for row in rows}), 8)
        for row in rows:
            self.assertTrue(row["file"].endswith(".jpg"))
            self.assertIn("#ExamBloom", row["hashtags"])

    def test_quiz_days_remain_quizzes(self):
        weds = dt.date(2026, 11, 11)
        sat = dt.date(2026, 11, 14)
        self.assertEqual(compose_post(weds, SITE)["category"], "quiz")
        self.assertEqual(compose_post(sat, SITE)["category"], "quiz")

if __name__ == "__main__":
    unittest.main()
