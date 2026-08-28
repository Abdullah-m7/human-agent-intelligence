import importlib.util
import json
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "analysis" / "stage004_llm_hdc.py"
spec = importlib.util.spec_from_file_location("stage004_llm_hdc", MODULE)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


class Stage004HdcTests(unittest.TestCase):
    def test_compact_grid_parser(self):
        g, err = m.parse_compact_grid('{"grid":"1,2;3,4"}')
        self.assertIsNone(err)
        self.assertEqual(g, [[1, 2], [3, 4]])

    def test_parser_rejects_non_arc_cells(self):
        g, err = m.parse_compact_grid('{"grid":"1,10;3,4"}')
        self.assertIsNone(g)
        self.assertEqual(err, "bad_cell")

    def test_strip_test_outputs_is_hard_leak_guard(self):
        task = {
            "train": [{"input": [[1]], "output": [[2]]}],
            "test": [{"input": [[3]], "output": [[4]]}],
        }
        visible = m.strip_test_outputs(task)
        self.assertEqual(visible["test"], [{"input": [[3]]}])
        self.assertNotIn("output", visible["test"][0])


    def test_participant_target_uses_first_query(self):
        task = {
            "test": [
                {"input": [[1]], "output": [[2]]},
                {"input": [[3]], "output": [[4]]},
            ]
        }
        self.assertEqual(m.participant_target(task), task["test"][0])

    def test_hdc_index_is_deterministic_and_bounded(self):
        a = m.hdc_index("abc123", 5)
        b = m.hdc_index("abc123", 5)
        self.assertEqual(a, b)
        self.assertGreaterEqual(a, 0)
        self.assertLess(a, 5)

    def test_eval_is_sealed_without_lock(self):
        # Repository intentionally has no confirmatory lock during development.
        if not m.LOCK_FILE.exists():
            with self.assertRaises(SystemExit):
                m.assert_phase_allowed("eval")


if __name__ == "__main__":
    unittest.main()
