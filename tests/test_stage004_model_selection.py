import unittest

from analysis.stage004_model_selection import (
    Candidate,
    assess,
    candidate_from_summary,
    select_pair,
)


def c(label, acc, prod=1.0, hdc=1.0, act=0.2, n=15, tokens=50.0):
    return Candidate(label, n, acc, prod, hdc, act, tokens)


class Stage004ModelSelectionTests(unittest.TestCase):
    def test_complete_positive_candidate_is_eligible(self):
        e = assess(c("gemma", 2 / 15, act=6 / 15))
        self.assertTrue(e.eligible)
        self.assertEqual(e.reasons, ())

    def test_incomplete_candidate_is_not_eligible(self):
        e = assess(c("qwen4", 0.5, n=6))
        self.assertFalse(e.eligible)
        self.assertTrue(any(x.startswith("incomplete_dev") for x in e.reasons))

    def test_zero_accuracy_and_low_act_are_nonviable(self):
        e = assess(c("dead", 0.0, act=0.0))
        self.assertFalse(e.eligible)
        self.assertIn("zero_standalone_accuracy", e.reasons)

    def test_hdc_parse_gate_is_enforced(self):
        e = assess(c("bad-hdc", 0.2, hdc=0.79))
        self.assertFalse(e.eligible)
        self.assertTrue(any(x.startswith("hdc_parse_below") for x in e.reasons))

    def test_pair_is_chosen_by_standalone_accuracy(self):
        s = select_pair([c("weak", 0.10), c("strong", 0.20)])
        self.assertEqual(s.verdict, "PAIR_SELECTED")
        self.assertEqual(s.weak_model, "weak")
        self.assertEqual(s.strong_model, "strong")

    def test_tied_top_state_does_not_manufacture_capability_order(self):
        s = select_pair([c("a", 0.30, tokens=20), c("b", 0.30, tokens=30), c("c", 0.20)])
        self.assertEqual(s.verdict, "PAIR_SELECTED")
        self.assertEqual(s.strong_model, "b")
        self.assertEqual(s.weak_model, "c")
        # The first tied candidate is skipped because the adjacent accuracy is equal.

    def test_all_tied_returns_no_strict_order(self):
        s = select_pair([c("a", 0.30), c("b", 0.30)])
        self.assertEqual(s.verdict, "NO_STRICT_CAPABILITY_ORDER")

    def test_fewer_than_two_eligible_returns_no_pair(self):
        s = select_pair([c("good", 0.20), c("bad", 0.0, act=0.0)])
        self.assertEqual(s.verdict, "NO_ELIGIBLE_LLM_PAIR")

    def test_forbidden_team_metrics_cannot_enter_candidate(self):
        base = {
            "model_label": "m",
            "n_tasks": 15,
            "standalone_accuracy": 0.2,
            "production_parse_rate": 1.0,
            "hdc_parse_rate": 1.0,
            "act_coverage": 0.2,
            "mean_production_completion_tokens": 10,
            "unsafe_autonomy_mass": 0.99,
            "act_precision": 0.01,
            "task_balanced_joint_one_shot": 0.0,
            "human_leverage": -99,
        }
        got = candidate_from_summary(base)
        self.assertFalse(hasattr(got, "unsafe_autonomy_mass"))
        self.assertFalse(hasattr(got, "act_precision"))
        self.assertFalse(hasattr(got, "task_balanced_joint_one_shot"))

    def test_forbidden_outcomes_do_not_change_selection(self):
        common = {
            "n_tasks": 15,
            "production_parse_rate": 1.0,
            "hdc_parse_rate": 1.0,
            "act_coverage": 0.2,
        }
        a1 = candidate_from_summary({"model_label": "a", "standalone_accuracy": 0.1, **common, "unsafe_autonomy_mass": 0.0})
        b1 = candidate_from_summary({"model_label": "b", "standalone_accuracy": 0.2, **common, "unsafe_autonomy_mass": 1.0})
        a2 = candidate_from_summary({"model_label": "a", "standalone_accuracy": 0.1, **common, "unsafe_autonomy_mass": 1.0})
        b2 = candidate_from_summary({"model_label": "b", "standalone_accuracy": 0.2, **common, "unsafe_autonomy_mass": 0.0})
        self.assertEqual(select_pair([a1, b1]), select_pair([a2, b2]))


if __name__ == "__main__":
    unittest.main()
