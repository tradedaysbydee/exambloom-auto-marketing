import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from strategy import SLOTS, choose_offer, expected_cron_for, select_slot

class PostingExperimentTests(unittest.TestCase):
    def test_untrained_rotates_between_three_valid_slots(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "missing.json"
            results = [select_slot(dt.date(2026, 11, 10) + dt.timedelta(days=i), p)
                       for i in range(9)]
            self.assertEqual(set(results), {12, 18, 20})
            self.assertTrue(all(expected_cron_for(dt.date(2026, 11, 10) + dt.timedelta(days=i), p)
                                in [s[0] for s in SLOTS] for i in range(9)))

    def test_learned_topic_still_explores(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "history.json"
            p.write_text(json.dumps({"adaptive": {"top_topic": "maths", "top_slot": 20}}))
            days = [dt.date(2026, 11, 10) + dt.timedelta(days=i) for i in range(25)]
            self.assertIn(8, [choose_offer(d, 3, p) for d in days])
            self.assertIn(3, [choose_offer(d, 3, p) for d in days])
            self.assertIn(20, [select_slot(d, p) for d in days])

if __name__ == "__main__":
    unittest.main()
