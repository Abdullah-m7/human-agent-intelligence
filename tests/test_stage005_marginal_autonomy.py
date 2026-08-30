import unittest

from analysis.stage005_marginal_autonomy import marginal_report


def state(correct=False, act=False, wrong=False):
    return {
        "standalone_correct": correct,
        "act": act,
        "act_correct": act and correct,
        "wrong_act": wrong,
        "selected_source_length": 20,
        "selected_ast_node_count": 10,
        "selected_branch_count": 1,
    }


class Stage005MarginalAutonomyTests(unittest.TestCase):
    def test_new_autonomy_precision_uses_defer_to_act_region_only(self):
        rows = [
            {
                "budgets": {
                    "B1": state(False, False),
                    "B2": state(True, True),
                    "B4": state(True, True),
                    "B8": state(True, True),
                },
                "ambiguity": {"certified_candidate_count": 2, "all_certified_predictions_agree": True},
            },
            {
                "budgets": {
                    "B1": state(False, False),
                    "B2": state(False, True, True),
                    "B4": state(False, True, True),
                    "B8": state(False, True, True),
                },
                "ambiguity": {"certified_candidate_count": 2, "all_certified_predictions_agree": False},
            },
        ]
        report = marginal_report(rows)
        first = report["transitions"][0]
        self.assertEqual(first["new_autonomy_n"], 2)
        self.assertEqual(first["new_autonomy_precision"], 0.5)
        self.assertEqual(first["delta_act_coverage"], 1.0)
        self.assertEqual(report["certified_program_ambiguity"]["disagreement_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
