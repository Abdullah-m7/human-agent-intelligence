import json
import unittest

from src.program_agent.agent import BASE_SEED, request_body, seed_for_candidate
from src.program_agent.candidate import (
    CandidateEvaluation,
    budget_state,
    evaluate_candidate,
    parse_program_response,
    select_best,
)
from analysis.stage005_program_synthesis import (
    attach_summary_provenance,
    validate_calibration_server_args,
    validate_resume_row,
)


def candidate(index, fit, certified=False, prediction=None, valid=True):
    return CandidateEvaluation(
        candidate_index=index,
        seed=seed_for_candidate(index),
        valid=valid,
        certified=certified,
        visible_train_exact_fit=fit,
        source="def solve(grid):\n    return grid",
        source_sha256=str(index),
        source_length=32,
        ast_node_count=8,
        branch_count=0,
        target_prediction=prediction or [[index]],
        error=None,
        sandbox_elapsed_s=0.01,
    )


class Stage005ProgramAgentTests(unittest.TestCase):
    def test_calibration_server_context_is_frozen(self):
        validate_calibration_server_args("llama-server --ctx-size 16384 --parallel 1")
        with self.assertRaisesRegex(SystemExit, "requires --ctx-size 16384"):
            validate_calibration_server_args("llama-server --ctx-size 8192 --parallel 1")
        with self.assertRaisesRegex(SystemExit, "exactly one"):
            validate_calibration_server_args("llama-server --parallel 1")

    def test_resume_provenance_mismatch_is_rejected(self):
        expected = {"max_candidates": 8, "system_prompt_sha256": "frozen"}
        row = {
            **expected,
            "task_id": "task",
            "candidate_index": 1,
            "seed": seed_for_candidate(1),
        }
        validate_resume_row(row, expected, ["task"])
        row["system_prompt_sha256"] = "drifted"
        with self.assertRaisesRegex(ValueError, "resume provenance mismatch"):
            validate_resume_row(row, expected, ["task"])

    def test_summary_metrics_are_not_overwritten_by_budget_provenance(self):
        metrics = {"budgets": {"B1": {"standalone_accuracy": 0.25}}}
        report = attach_summary_provenance(metrics, "engineering", ["task"], {"budgets": [1, 2, 4, 8]})
        self.assertEqual(report["budgets"], metrics["budgets"])
        self.assertEqual(report["budget_ladder"], [1, 2, 4, 8])

    def test_seed_schedule_is_fixed_and_one_based(self):
        self.assertEqual([seed_for_candidate(i) for i in range(1, 9)], [BASE_SEED + i for i in range(1, 9)])
        with self.assertRaises(ValueError):
            seed_for_candidate(0)

    def test_visible_training_fit_scoring_and_certification(self):
        training = [
            {"input": [[1]], "output": [[1]]},
            {"input": [[2]], "output": [[2]]},
        ]
        content = json.dumps({"program": "def solve(grid):\n    return grid"})
        result = evaluate_candidate(content, training, [[3]], 1, seed_for_candidate(1))
        self.assertTrue(result.valid, result.error)
        self.assertEqual(result.visible_train_exact_fit, 1.0)
        self.assertTrue(result.certified)
        self.assertEqual(result.target_prediction, [[3]])

    def test_raw_python_response_is_parsed(self):
        source = "def solve(grid):\n    return grid"
        self.assertEqual(parse_program_response(source), (source, None))

    def test_ranking_uses_fit_then_earliest_candidate(self):
        candidates = [candidate(1, 0.5), candidate(2, 1.0, True), candidate(3, 1.0, True)]
        self.assertEqual(select_best(candidates).candidate_index, 2)

    def test_invalid_candidate_is_excluded_from_ranking(self):
        candidates = [candidate(1, 1.0, True, valid=False), candidate(2, 0.5)]
        self.assertEqual(select_best(candidates).candidate_index, 2)

    def test_act_requires_train_perfect_selected_candidate(self):
        state = budget_state([candidate(1, 0.5, False, [[1]])], 1, [[1]])
        self.assertTrue(state["standalone_correct"])
        self.assertFalse(state["act"])
        certified = budget_state([candidate(1, 1.0, True, [[9]])], 1, [[1]])
        self.assertTrue(certified["act"])
        self.assertTrue(certified["wrong_act"])

    def test_budget_prefixes_are_literal_nested_candidate_sequences(self):
        candidates = [candidate(i, i / 8, i == 8) for i in range(1, 9)]
        states = {budget: budget_state(candidates, budget, [[99]]) for budget in (1, 2, 4, 8)}
        self.assertEqual([states[b]["candidate_count"] for b in (1, 2, 4, 8)], [1, 2, 4, 8])
        self.assertEqual([states[b]["selected_candidate_index"] for b in (1, 2, 4, 8)], [1, 2, 4, 8])

    def test_hidden_target_output_is_not_serialized(self):
        training = [{"input": [[1]], "output": [[2]]}]
        target_input = [[3, 4], [4, 3]]
        hidden_target_output = [[9, 8, 7], [6, 5, 9]]
        body = request_body("model", training, target_input, seed_for_candidate(1))
        serialized = json.dumps(body, sort_keys=True, separators=(",", ":"))
        self.assertIn("TARGET_INPUT", serialized)
        self.assertIn(json.dumps(target_input, separators=(",", ":")), serialized)
        self.assertNotIn(json.dumps(hidden_target_output, separators=(",", ":")), serialized)
        self.assertNotIn("hidden_target_output", serialized)


if __name__ == "__main__":
    unittest.main()
