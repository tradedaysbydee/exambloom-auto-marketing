import datetime as dt
import tempfile
import unittest
from pathlib import Path

from bot import compose_post, render, SITE
from creative_library import OFFERS, QUIZZES
from insights import exposure, quality_score, metric_map

class SalesGrowthTests(unittest.TestCase):
    def test_creative_library_has_real_variation(self):
        self.assertGreaterEqual(len(OFFERS), 20)
        self.assertGreaterEqual(len(QUIZZES), 20)
        self.assertEqual(len({q[1] for q in QUIZZES}), len(QUIZZES))

    def test_creative_id_is_saved(self):
        for i in range(7):
            post = compose_post(dt.date(2026, 11, 2) + dt.timedelta(days=i), SITE)
            self.assertTrue(post["creative_id"].startswith(("offer-", "quiz-")))

    def test_no_double_counting_of_views(self):
        self.assertEqual(exposure({"impressions": 100, "views": 90, "reach": 80}), (100, "impressions"))
        self.assertEqual(exposure({"views": 90}), (90, "views"))
        self.assertEqual(exposure({}), (None, None))

    def test_missing_metrics_are_not_zero(self):
        self.assertNotIn("impressions", metric_map([{"type": "reactions", "value": 5}]))
        self.assertIsNone(quality_score({}))
        self.assertIsNone(quality_score({"views": 15, "reactions": 5}))

    def test_quiz_render_with_big_choices(self):
        p = compose_post(dt.date(2026, 11, 7), SITE)
        self.assertEqual(p["category"], "quiz")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "quiz.jpg"
            render(p, target)
            self.assertTrue(target.exists())
            self.assertGreater(target.stat().st_size, 10000)

if __name__ == "__main__":
    unittest.main()
