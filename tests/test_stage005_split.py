import hashlib
import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SPLIT = REPO / "benchmarks" / "capability_twin" / "stage005_split.json"


class Stage005SplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.split = json.loads(SPLIT.read_text())

    def test_blacklist_has_all_75_cogarc_ids(self):
        blacklist = self.split["human_task_blacklist"]
        self.assertEqual(len(blacklist), 75)
        self.assertEqual(len(set(blacklist)), 75)

    def test_split_sizes_and_disjointness(self):
        engineering = set(self.split["engineering_tasks"])
        calibration = set(self.split["calibration_tasks"])
        blacklist = set(self.split["human_task_blacklist"])
        self.assertEqual(len(engineering), 20)
        self.assertEqual(len(calibration), 60)
        self.assertFalse(engineering & calibration)
        self.assertFalse(engineering & blacklist)
        self.assertFalse(calibration & blacklist)

    def test_mechanical_sha256_selection(self):
        blacklist = set(self.split["human_task_blacklist"])
        eligible = [task_id for task_id in self.split["source_training_task_ids"] if task_id not in blacklist]
        ranked = sorted(eligible, key=lambda task_id: (hashlib.sha256(task_id.encode()).hexdigest(), task_id))
        self.assertEqual(self.split["engineering_tasks"], ranked[:20])
        self.assertEqual(self.split["calibration_tasks"], ranked[20:80])


if __name__ == "__main__":
    unittest.main()
