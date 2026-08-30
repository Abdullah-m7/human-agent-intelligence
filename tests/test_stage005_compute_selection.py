import copy
import unittest

from analysis.stage005_compute_selection import (
    BudgetState,
    select_compute_pair,
    states_from_summary,
)


class Stage005ComputeSelectionTests(unittest.TestCase):
    def test_selects_largest_compute_separation(self):
        states = [
            BudgetState(1, 60, 0.10, 0.10),
            BudgetState(2, 60, 0.11, 0.12),
            BudgetState(4, 60, 0.12, 0.13),
            BudgetState(8, 60, 0.20, 0.20),
        ]
        selection = select_compute_pair(states)
        self.assertEqual(selection.verdict, "PAIR_SELECTED")
        self.assertEqual((selection.selected_low, selection.selected_high), (1, 8))

    def test_requires_strict_capability_and_coverage_increase(self):
        states = [
            BudgetState(1, 60, 0.10, 0.10),
            BudgetState(2, 60, 0.10, 0.12),
            BudgetState(4, 60, 0.10, 0.15),
            BudgetState(8, 60, 0.10, 0.20),
        ]
        self.assertEqual(select_compute_pair(states).verdict, "NO_VIABLE_COMPUTE_LADDER")

    def test_requires_low_coverage_floor(self):
        states = [
            BudgetState(1, 60, 0.10, 0.09),
            BudgetState(2, 60, 0.11, 0.09),
            BudgetState(4, 60, 0.12, 0.09),
            BudgetState(8, 60, 0.20, 0.20),
        ]
        self.assertEqual(select_compute_pair(states).verdict, "NO_VIABLE_COMPUTE_LADDER")

    def test_incomplete_calibration_is_rejected(self):
        states = [BudgetState(budget, 59, 0.10, 0.10) for budget in (1, 2, 4, 8)]
        self.assertEqual(select_compute_pair(states).verdict, "INCOMPLETE_CALIBRATION")

    def test_missing_budget_is_rejected(self):
        states = [BudgetState(budget, 60, 0.10, 0.10) for budget in (1, 2, 8)]
        self.assertEqual(select_compute_pair(states).verdict, "INCOMPLETE_CALIBRATION")

    def test_forbidden_metrics_cannot_change_selected_pair(self):
        summary = {
            "budgets": {
                "B1": {"budget": 1, "n_tasks": 60, "standalone_accuracy": 0.10, "act_coverage": 0.10},
                "B2": {"budget": 2, "n_tasks": 60, "standalone_accuracy": 0.11, "act_coverage": 0.11},
                "B4": {"budget": 4, "n_tasks": 60, "standalone_accuracy": 0.12, "act_coverage": 0.12},
                "B8": {"budget": 8, "n_tasks": 60, "standalone_accuracy": 0.20, "act_coverage": 0.20},
            },
            "unsafe_autonomy_mass": 0.99,
            "new_autonomy_precision": 0.0,
        }
        altered = copy.deepcopy(summary)
        altered["unsafe_autonomy_mass"] = 0.0
        altered["new_autonomy_precision"] = 1.0
        original = select_compute_pair(states_from_summary(summary))
        changed = select_compute_pair(states_from_summary(altered))
        self.assertEqual(original, changed)
        self.assertEqual((original.selected_low, original.selected_high), (1, 8))


if __name__ == "__main__":
    unittest.main()
