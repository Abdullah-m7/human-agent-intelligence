import copy
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from analysis.stage005_cogarc_confirmatory import (
    compute_confirmatory_metrics,
    human_leverage_crossfit,
    primary_verdict,
    routing_decisions,
)
from analysis.stage005_program_synthesis import validate_resume_row
from src.program_agent.agent import request_body, seed_for_candidate
from src.program_agent.confirmatory import (
    LOCK_BEGIN,
    LOCK_END,
    ConfirmatoryAbort,
    ConfirmatoryGate,
    expected_lock_fields,
    load_confirmatory_ids,
    parse_lock_text,
    validate_execution_lock,
    validate_full_task_set,
    validate_lock_fields,
    validate_runtime_arguments,
)


def lock_fields(status="FROZEN"):
    return {
        "LOCK_STATUS": status,
        "CONTRACT_COMMIT": "a" * 40 if status == "FROZEN" else "PENDING_COMMIT_A",
        **expected_lock_fields(),
    }


def lock_text(fields):
    body = "\n".join(f"{key}: {value}" for key, value in fields.items())
    return f"prose mentioning FROZEN is not authorization\n{LOCK_BEGIN}\n{body}\n{LOCK_END}\n"


def state(act, correct, selected):
    return {
        "standalone_correct": bool(correct),
        "act": bool(act),
        "wrong_act": bool(act and not correct),
        "selected_candidate_index": selected,
    }


def task(task_id, low, high, ambiguity=None):
    return {
        "task_id": task_id,
        "target_index": 0,
        "budgets": {"B1": low, "B8": high},
        "ambiguity": ambiguity or {
            "certified_candidate_count": 0,
            "unique_certified_target_predictions": 0,
            "all_certified_predictions_agree": True,
        },
    }


def verdict_metrics(*, cap_up=True, coverage_up=True, unsafe_up=True, joint_down=True, acts=6):
    return {
        "B1": {
            "standalone_accuracy": 0.2,
            "act_coverage": 0.2,
            "unsafe_autonomy_mass": 0.02,
            "n_acts": acts,
        },
        "B8": {
            "standalone_accuracy": 0.4 if cap_up else 0.2,
            "act_coverage": 0.4 if coverage_up else 0.2,
            "unsafe_autonomy_mass": 0.04 if unsafe_up else 0.02,
            "n_acts": acts + 6,
        },
        "joint_one_shot_task_balanced_B1": 0.7,
        "joint_one_shot_task_balanced_B8": 0.6 if joint_down else 0.7,
    }


class Stage005CogARCConfirmatoryLockTests(unittest.TestCase):
    def test_exact_lock_parser_ignores_prose_and_rejects_noncanonical_fields(self):
        fields = lock_fields("DRAFT_DO_NOT_RUN")
        parsed = parse_lock_text(lock_text(fields))
        self.assertEqual(parsed["LOCK_STATUS"], "DRAFT_DO_NOT_RUN")
        with self.assertRaisesRegex(ConfirmatoryAbort, "non-canonical"):
            parse_lock_text(f"{LOCK_BEGIN}\nLOCK_STATUS:FROZEN\n{LOCK_END}\n")

    def test_draft_lock_refuses_confirmatory_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lock.md"
            path.write_text(lock_text(lock_fields("DRAFT_DO_NOT_RUN")), encoding="utf-8")
            with self.assertRaisesRegex(ConfirmatoryAbort, "LOCK_STATUS"):
                validate_execution_lock(path, check_contract_tree=False)

    def test_frozen_lock_allows_only_matching_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lock.md"
            path.write_text(lock_text(lock_fields()), encoding="utf-8")
            gate = validate_execution_lock(path, check_contract_tree=False)
        self.assertEqual(len(gate.task_ids), 60)
        self.assertEqual(gate.fields["LOW_BUDGET"], "1")
        self.assertEqual(gate.fields["HIGH_BUDGET"], "8")

    def test_model_hash_and_prompt_mismatches_abort(self):
        for key in ("MODEL_SHA256", "SYSTEM_PROMPT_SHA256"):
            fields = lock_fields()
            fields[key] = "0" * 64
            with self.subTest(key=key), self.assertRaisesRegex(ConfirmatoryAbort, "lock mismatch"):
                validate_lock_fields(fields)

    def test_pair_and_id_hash_mismatches_abort(self):
        for key, value in (
            ("LOW_BUDGET", "2"),
            ("HIGH_BUDGET", "4"),
            ("COGARC_EVAL_IDS_SHA256", "0" * 64),
        ):
            fields = lock_fields()
            fields[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ConfirmatoryAbort, "lock mismatch"):
                validate_lock_fields(fields)

    def test_partial_confirmatory_evaluation_is_rejected(self):
        frozen = load_confirmatory_ids()
        with self.assertRaisesRegex(ConfirmatoryAbort, "partial"):
            validate_full_task_set(frozen[:-1], frozen)
        with self.assertRaisesRegex(ConfirmatoryAbort, "partial"):
            validate_full_task_set(list(reversed(frozen)), frozen)

    def test_runtime_mismatch_and_limit_abort_without_fallback(self):
        fields = lock_fields()
        gate = ConfirmatoryGate(fields, tuple(load_confirmatory_ids()), "f" * 64)
        args = {
            "model": fields["MODEL_API_NAME"],
            "model_label": fields["MODEL_LABEL"],
            "model_sha256": fields["MODEL_SHA256"],
            "source_commit": fields["COGARC_SOURCE_COMMIT"],
            "llama_cpp_build": fields["LLAMA_CPP_BUILD"],
            # This value intentionally cannot match the frozen hash.
            "server_args": "wrong",
            "max_candidates": 8,
            "limit": None,
            "contract_commit": fields["CONTRACT_COMMIT"],
        }
        with self.assertRaisesRegex(ConfirmatoryAbort, "runtime contract mismatch"):
            validate_runtime_arguments(gate, **args)
        args["server_args"] = json.loads(
            Path("results/stage005_program_synthesis/calibration/provenance.json").read_text()
        )["server_args"]
        args["limit"] = 59
        with self.assertRaisesRegex(ConfirmatoryAbort, "--limit"):
            validate_runtime_arguments(gate, **args)

    def test_resume_provenance_mismatch_is_rejected(self):
        expected = {
            "max_candidates": 8,
            "confirmatory_lock_sha256": "frozen",
            "cogarc_eval_ids_sha256": "ids",
        }
        row = {
            **expected,
            "task_id": "synthetic",
            "candidate_index": 1,
            "seed": seed_for_candidate(1),
        }
        validate_resume_row(row, expected, ["synthetic"])
        row["confirmatory_lock_sha256"] = "drifted"
        with self.assertRaisesRegex(ValueError, "resume provenance mismatch"):
            validate_resume_row(row, expected, ["synthetic"])

    def test_target_output_is_never_serialized_to_model(self):
        hidden = [[9, 9], [9, 9]]
        body = request_body(
            "model",
            [{"input": [[1]], "output": [[2]]}],
            [[3, 4], [4, 3]],
            seed_for_candidate(1),
        )
        serialized = json.dumps(body, sort_keys=True, separators=(",", ":"))
        self.assertNotIn(json.dumps(hidden, separators=(",", ":")), serialized)
        self.assertNotIn("test[0].output", serialized)


class Stage005CogARCConfirmatoryAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            task("t1", state(True, True, 1), state(True, True, 1)),
            task("t2", state(False, False, 1), state(True, False, 2)),
            task("t3", state(False, False, 1), state(False, True, 4)),
        ]
        self.humans = pd.DataFrame(
            [
                {"trial": "t1", "person_id": "p1", "human_first": 0, "human_final": 1},
                {"trial": "t1", "person_id": "p2", "human_first": 1, "human_final": 1},
                {"trial": "t2", "person_id": "p1", "human_first": 1, "human_final": 1},
                {"trial": "t2", "person_id": "p2", "human_first": 1, "human_final": 1},
                {"trial": "t3", "person_id": "p1", "human_first": 0, "human_final": 1},
                {"trial": "t3", "person_id": "p2", "human_first": 1, "human_final": 1},
            ]
        )

    def test_act_b1_must_be_subset_of_act_b8(self):
        bad = [task("x", state(True, True, 1), state(False, True, 1))]
        with self.assertRaisesRegex(ValueError, "subset"):
            routing_decisions(bad)

    def test_joint_formula_and_autonomy_displacement_identity(self):
        report = compute_confirmatory_metrics(self.rows, self.humans)
        self.assertAlmostEqual(report["joint_one_shot_task_balanced_B1"], 5 / 6)
        self.assertAlmostEqual(report["joint_one_shot_task_balanced_B8"], 1 / 2)
        self.assertAlmostEqual(
            report["delta_joint_one_shot_task_balanced_B8_minus_B1"], -1 / 3
        )
        self.assertAlmostEqual(
            report["new_autonomy"]["autonomy_displacement_term"], -1 / 3
        )
        self.assertTrue(report["autonomy_displacement_identity"]["holds"])
        self.assertEqual(report["new_autonomy"]["n"], 1)
        self.assertEqual(report["new_autonomy"]["correct"], 0)

    def test_strict_atpi_verdict_tree(self):
        self.assertEqual(
            primary_verdict(verdict_metrics())["strict_atpi_verdict"],
            "STRICT_ATPI_REPLICATION",
        )
        self.assertEqual(
            primary_verdict(verdict_metrics(cap_up=False))["strict_atpi_verdict"],
            "INCONCLUSIVE_CAPABILITY_ORDER",
        )
        self.assertEqual(
            primary_verdict(verdict_metrics(acts=5))["strict_atpi_verdict"],
            "INCONCLUSIVE_LOW_AUTONOMY_COVERAGE",
        )

    def test_broader_descriptor_cannot_overwrite_strict_verdict(self):
        result = primary_verdict(verdict_metrics(unsafe_up=False))
        self.assertEqual(result["strict_atpi_verdict"], "NO_STRICT_ATPI_REPLICATION")
        self.assertEqual(result["secondary_broader_descriptor"], "AUTONOMY_TEAM_INVERSION")

    def test_human_leverage_cannot_affect_primary_verdict(self):
        metrics = verdict_metrics()
        before = primary_verdict(metrics)
        metrics["human_leverage_secondary"] = {"slope": -999}
        self.assertEqual(before, primary_verdict(metrics))

    def test_ambiguity_metrics_cannot_affect_routing(self):
        before = routing_decisions(self.rows)
        changed = copy.deepcopy(self.rows)
        for row in changed:
            row["ambiguity"] = {
                "certified_candidate_count": 8,
                "unique_certified_target_predictions": 8,
                "all_certified_predictions_agree": False,
            }
        self.assertEqual(before, routing_decisions(changed))

    def test_human_leverage_uses_disjoint_30_30_task_halves(self):
        rows = []
        human_rows = []
        for index in range(60):
            name = f"s{index:02d}"
            rows.append(
                task(
                    name,
                    state(False, index % 3 == 0, 1),
                    state(index % 2 == 0, index % 3 != 1, 2 if index % 2 == 0 else 1),
                )
            )
            for person in range(6):
                human_rows.append(
                    {
                        "trial": name,
                        "person_id": f"p{person}",
                        "human_first": int((index + person) % (person + 2) != 0),
                        "human_final": int((index + person) % (person + 3) != 0),
                    }
                )
        result = human_leverage_crossfit(pd.DataFrame(human_rows), rows, seeds=2)
        self.assertEqual(result["status"], "AVAILABLE")
        self.assertEqual(result["minimum_capability_trials"], 20)
        self.assertEqual(result["minimum_evaluation_trials"], 20)
        self.assertEqual(result["analysis_role"], "SECONDARY_DOES_NOT_AFFECT_PRIMARY_VERDICT")


if __name__ == "__main__":
    unittest.main()
