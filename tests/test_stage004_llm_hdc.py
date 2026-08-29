import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_lock_parser_ignores_marker_inside_prose(self):
        text = "This prose mentions LOCK_STATUS: LOCKED but is not a status line."
        self.assertIsNone(m.lock_status(text))

    def test_lock_parser_rejects_multiple_status_lines(self):
        with self.assertRaises(ValueError):
            m.lock_status("LOCK_STATUS: DRAFT\nLOCK_STATUS: LOCKED\n")

    def test_eval_is_sealed_with_draft_lock_even_if_prose_mentions_locked_marker(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "lock.md"
            p.write_text(
                "LOCK_STATUS: DRAFT_DO_NOT_EVALUATE\n\n"
                "Explanatory prose may mention LOCK_STATUS: LOCKED without unlocking.\n",
                encoding="utf-8",
            )
            with patch.object(m, "LOCK_FILE", p):
                with self.assertRaises(SystemExit):
                    m.assert_phase_allowed("eval")

    def test_eval_allows_exact_unique_locked_status_line(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "lock.md"
            p.write_text("# Lock\n\nLOCK_STATUS: LOCKED\n", encoding="utf-8")
            with patch.object(m, "LOCK_FILE", p):
                m.assert_phase_allowed("eval")

    def test_eval_rejects_subset_flags(self):
        with self.assertRaises(SystemExit):
            m.assert_eval_scope("eval", 1, None)
        with self.assertRaises(SystemExit):
            m.assert_eval_scope("eval", None, ["abc"])
        m.assert_eval_scope("dev", 1, ["abc"])

    def test_resume_provenance_mismatch_is_rejected(self):
        expected = {
            "phase": "dev",
            "model": "m",
            "model_label": "label",
            "temperature": 0.0,
            "seed": 7,
            "participant_target_index": 0,
            "max_tokens": 120,
            "split_sha256": "s",
            "system_prompt_sha256": "p",
            "user_template_sha256": "u",
            "response_format_sha256": "r",
        }
        row = {"task_id": "t", **expected}
        m.validate_resume_row(row, expected, ["t"])
        bad = dict(row)
        bad["split_sha256"] = "different"
        with self.assertRaises(ValueError):
            m.validate_resume_row(bad, expected, ["t"])

    def test_resume_task_outside_phase_split_is_rejected(self):
        expected = {"phase": "dev"}
        row = {"task_id": "wrong", "phase": "dev"}
        with self.assertRaises(ValueError):
            m.validate_resume_row(row, expected, ["allowed"])

    def test_summary_reports_both_parse_rates(self):
        rows = [
            {
                "act": True,
                "production_correct": True,
                "wrong_act": False,
                "hdc_correct": True,
                "production_valid": True,
                "hdc_valid": True,
            },
            {
                "act": False,
                "production_correct": False,
                "wrong_act": False,
                "hdc_correct": False,
                "production_valid": False,
                "hdc_valid": True,
            },
        ]
        s = m.summarize(rows)
        self.assertEqual(s["production_parse_rate"], 0.5)
        self.assertEqual(s["hdc_parse_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
