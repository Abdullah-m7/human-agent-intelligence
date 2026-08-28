import unittest

import pandas as pd

from analysis.paper04_receiver_contract import (
    analyze,
    build_crossfitted_receiver_panel,
    common_support_tasks,
    difficulty_adjusted_scores,
    leave_one_task_capability,
    task_stratum_rates,
    validate_human_panel,
)


class Paper04ReceiverAnalysisTests(unittest.TestCase):
    def test_target_task_outcome_does_not_enter_capability_score(self):
        base = pd.DataFrame([
            {"person_id":"p1","trial":"a","human_first":1,"human_final":1},
            {"person_id":"p1","trial":"b","human_first":0,"human_final":1},
            {"person_id":"p1","trial":"c","human_first":1,"human_final":1},
            {"person_id":"p2","trial":"a","human_first":0,"human_final":0},
            {"person_id":"p2","trial":"b","human_first":1,"human_final":1},
            {"person_id":"p2","trial":"c","human_first":1,"human_final":1},
        ])
        changed = base.copy()
        changed.loc[(changed.person_id == "p1") & (changed.trial == "a"), "human_first"] = 0
        changed.loc[(changed.person_id == "p1") & (changed.trial == "a"), "human_final"] = 0
        x = leave_one_task_capability(base, "a", min_history=2).set_index("person_id")
        y = leave_one_task_capability(changed, "a", min_history=2).set_index("person_id")
        self.assertEqual(x.loc["p1", "capability"], y.loc["p1", "capability"])
        self.assertEqual(x.loc["p1", "capability_stratum"], y.loc["p1", "capability_stratum"])

    def test_min_history_is_enforced(self):
        h = pd.DataFrame([
            {"person_id":"p1","trial":"a","human_first":1,"human_final":1},
            {"person_id":"p1","trial":"b","human_first":1,"human_final":1},
            {"person_id":"p1","trial":"c","human_first":1,"human_final":1},
            {"person_id":"p2","trial":"a","human_first":1,"human_final":1},
            {"person_id":"p2","trial":"b","human_first":0,"human_final":0},
            {"person_id":"p2","trial":"c","human_first":0,"human_final":0},
            {"person_id":"p3","trial":"a","human_first":0,"human_final":0},
            {"person_id":"p3","trial":"b","human_first":1,"human_final":1},
        ])
        got = leave_one_task_capability(h, "a", min_history=2)
        self.assertEqual(set(got.person_id), {"p1", "p2"})

    def test_difficulty_adjustment_distinguishes_same_raw_accuracy_on_different_task_mix(self):
        h = pd.DataFrame([
            {"person_id":"easy_person","trial":"e1","human_first":1},
            {"person_id":"easy_person","trial":"e2","human_first":1},
            {"person_id":"easy_peer","trial":"e1","human_first":1},
            {"person_id":"easy_peer","trial":"e2","human_first":1},
            {"person_id":"hard_person","trial":"h1","human_first":1},
            {"person_id":"hard_person","trial":"h2","human_first":1},
            {"person_id":"hard_peer","trial":"h1","human_first":0},
            {"person_id":"hard_peer","trial":"h2","human_first":0},
        ])
        s = difficulty_adjusted_scores(h, min_history=2).set_index("person_id")
        self.assertEqual(s.loc["easy_person", "raw_capability"], 1.0)
        self.assertEqual(s.loc["hard_person", "raw_capability"], 1.0)
        self.assertGreater(s.loc["hard_person", "capability"], s.loc["easy_person", "capability"])

    def test_crossfitted_panel_uses_heldout_outcome_after_scoring(self):
        h = pd.DataFrame([
            {"person_id":"p1","trial":"a","human_first":0,"human_final":1},
            {"person_id":"p1","trial":"b","human_first":1,"human_final":1},
            {"person_id":"p2","trial":"a","human_first":1,"human_final":1},
            {"person_id":"p2","trial":"b","human_first":0,"human_final":1},
        ])
        panel = build_crossfitted_receiver_panel(h, ["a", "b"], min_history=1)
        self.assertEqual(len(panel), 4)
        row = panel[(panel.person_id == "p1") & (panel.trial == "a")].iloc[0]
        self.assertEqual(row.capability, 1.0)
        self.assertEqual(row.human_first, 0)
        self.assertEqual(row.human_final, 1)

    def test_source_recovery_invariant_is_enforced(self):
        h = pd.DataFrame([
            {"person_id":"p1","trial":"a","human_first":1,"human_final":0},
        ])
        with self.assertRaises(ValueError):
            validate_human_panel(h)

    def test_duplicate_person_task_is_rejected(self):
        h = pd.DataFrame([
            {"person_id":"p1","trial":"a","human_first":1,"human_final":1},
            {"person_id":"p1","trial":"a","human_first":1,"human_final":1},
        ])
        with self.assertRaises(ValueError):
            validate_human_panel(h)

    def test_support_flag_is_explicit(self):
        panel = pd.DataFrame([
            {"person_id":"p1","trial":"a","human_first":1,"human_final":1,"capability":0.5,"raw_capability":0.6,"n_history":30,"capability_stratum":3},
            {"person_id":"p2","trial":"a","human_first":0,"human_final":1,"capability":0.5,"raw_capability":0.5,"n_history":30,"capability_stratum":3},
        ])
        rates = task_stratum_rates(panel, min_support=3)
        self.assertFalse(bool(rates.iloc[0].supported))
        self.assertEqual(rates.iloc[0].n_human, 2)

    def test_common_support_requires_every_stratum_on_same_task(self):
        rows = []
        for trial in ("t1", "t2"):
            for q in range(1, 6):
                rows.append({
                    "trial": trial,
                    "capability_stratum": q,
                    "n_human": 10 if not (trial == "t2" and q == 5) else 9,
                })
        rates = pd.DataFrame(rows)
        self.assertEqual(common_support_tasks(rates, min_support=10), ["t1"])

    def test_end_to_end_profiles_use_identical_common_tasks(self):
        rows = []
        # 25 people give each stratum reasonable support after cross-fitting.
        for i in range(25):
            pid = f"p{i:02d}"
            ability = i / 24
            for j in range(10):
                # Every history task is shared; performance increases with person index.
                first = int(i >= (j * 2))
                rows.append({"person_id":pid,"trial":f"h{j}","human_first":first,"human_final":first})
            rows.append({"person_id":pid,"trial":"t1","human_first":int(ability >= .4),"human_final":int(ability >= .2)})
            rows.append({"person_id":pid,"trial":"t2","human_first":int(ability >= .7),"human_final":int(ability >= .3)})
        humans = pd.DataFrame(rows)
        agent = pd.DataFrame([
            {"trial":"t1","agent_correct":0,"act":1},
            {"trial":"t2","agent_correct":1,"act":0},
        ])
        report, panel, rates = analyze(
            humans,
            agent,
            min_history=10,
            min_support=1,
            min_common_tasks=2,
            reliability_seeds=5,
        )
        self.assertGreater(len(panel), 0)
        self.assertGreater(len(rates), 0)
        profiles = report["primary_profiles_common_tasks"]
        supported = [v for v in profiles.values() if v["profile"]]
        self.assertEqual(len(supported), 5)
        self.assertEqual({v["n_supported_tasks"] for v in supported}, {2})
        self.assertEqual(
            {round(v["profile"]["agent_accuracy"], 12) for v in supported},
            {0.5},
        )
        for row in supported:
            p = row["profile"]
            self.assertAlmostEqual(
                p["human_recovery_potential"],
                p["joint_recovery_value"] + p["recovery_suppression_mass"],
            )


if __name__ == "__main__":
    unittest.main()
