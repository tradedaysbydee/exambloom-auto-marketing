import datetime as dt
import tempfile
import unittest
from pathlib import Path

from bot import compose_post, render, SITE

class ExamBloomBotTests(unittest.TestCase):
    def test_five_sales_two_quiz_posts(self):
        monday = dt.date(2026, 11, 2)
        posts = [compose_post(monday + dt.timedelta(days=i), SITE) for i in range(7)]
        self.assertEqual(sum(p["category"] == "membership" for p in posts), 5)
        self.assertEqual(sum(p["category"] == "quiz" for p in posts), 2)

    def test_facebook_links_track_each_day(self):
        a = compose_post(dt.date(2026, 11, 6), SITE)
        b = compose_post(dt.date(2026, 11, 7), SITE)
        self.assertIn("utm_source=facebook", a["facebook_caption"])
        self.assertNotEqual(a["facebook_caption"], b["facebook_caption"])

    def test_render_creates_jpeg(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "post.jpg"
            render(compose_post(dt.date(2026, 11, 6), SITE), target)
            self.assertTrue(target.exists())
            self.assertGreater(target.stat().st_size, 10_000)

if __name__ == "__main__":
    unittest.main()
