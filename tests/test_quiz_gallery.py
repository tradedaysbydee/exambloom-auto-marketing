import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from quiz_gallery import select_quiz_campaign


class QuizGalleryTests(unittest.TestCase):
    def test_requires_all_ten_approved_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            entries = [{"id": str(i), "file": f"{i:02d}.jpg"} for i in range(10)]
            (folder / "quiz_manifest.json").write_text(json.dumps({"campaigns": entries}))
            for item in entries[:-1]:
                (folder / item["file"]).write_bytes(b"fake jpg fixture")
            self.assertIsNone(select_quiz_campaign(dt.date(2026, 11, 18), folder))
            (folder / entries[-1]["file"]).write_bytes(b"fake jpg fixture")
            first = select_quiz_campaign(dt.date(2026, 11, 18), folder)
            second = select_quiz_campaign(dt.date(2026, 11, 21), folder)
            self.assertEqual(first["id"], "0")
            self.assertEqual(second["id"], "1")
            self.assertIsNone(select_quiz_campaign(dt.date(2026, 11, 19), folder))

    def test_rejects_paths_outside_campaign_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            entries = [{"id": str(i), "file": f"{i:02d}.jpg"} for i in range(9)]
            entries.append({"id": "bad", "file": "../private.jpg"})
            (folder / "quiz_manifest.json").write_text(json.dumps({"campaigns": entries}))
            for item in entries[:9]:
                (folder / item["file"]).write_bytes(b"fixture")
            self.assertIsNone(select_quiz_campaign(dt.date(2026, 11, 18), folder))


if __name__ == "__main__":
    unittest.main()
