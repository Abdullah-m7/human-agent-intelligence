import unittest

from analysis.stage005_program_ambiguity import ambiguity_report


def candidate(task_id, index, certified, correct):
    return {
        "task_id": task_id,
        "candidate_index": index,
        "candidate_target_correct": correct,
        "evaluation": {
            "certified": certified,
            "source_sha256": f"hash-{task_id}-{index}",
        },
    }


def task(task_id, certified_count, unique_predictions, selected_correct):
    return {
        "task_id": task_id,
        "ambiguity": {
            "certified_candidate_count": certified_count,
            "unique_certified_target_predictions": unique_predictions,
            "all_certified_predictions_agree": unique_predictions <= 1,
        },
        "budgets": {
            "B8": {
                "selected_candidate_index": 1,
                "standalone_correct": selected_correct,
            }
        },
    }


class Stage005ProgramAmbiguityTests(unittest.TestCase):
    def test_separates_disagreement_from_unanimous_wrong(self):
        tasks = [task("disagree", 2, 2, True), task("wrong", 2, 1, False)]
        candidates = [
            candidate("disagree", 1, True, True),
            candidate("disagree", 2, True, False),
            candidate("wrong", 1, True, False),
            candidate("wrong", 2, True, False),
        ]
        report = ambiguity_report(tasks, candidates)
        self.assertEqual(report["n_tasks_with_multiple_certified_programs"], 2)
        self.assertEqual(report["n_tasks_with_certified_prediction_disagreement"], 1)
        self.assertEqual(report["n_tasks_with_unanimous_wrong_multiple_certified_programs"], 1)
        self.assertEqual(report["disagreement_tasks"][0]["task_id"], "disagree")
        self.assertEqual(report["unanimous_wrong_tasks"][0]["task_id"], "wrong")


if __name__ == "__main__":
    unittest.main()
