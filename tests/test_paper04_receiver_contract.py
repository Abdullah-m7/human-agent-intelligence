import unittest

import pandas as pd

from analysis.paper04_receiver_contract import (
    analyze,
    build_crossfitted_receiver_panel,
    leave_one_task_capability,
    task_stratum_rates,
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
        x = leave_one_task_capability(base, "a", min_history=2).set_index("person_id")
        y = leave_one_task_capability(changed, "a", min_history=2).set_index("person_id")
        self.assertEqual(x.loc["p1", "capability"], y.loc["p1", "capability"])
        self.assertEqual(x.loc["p1", "capability_stratum"], y.loc["p1", "capability_stratum"])

    def test_min_history_is_enforced(self):
        h = pd.DataFrame([
            {"person_id":"p1","trial":"a","human_first":1,"human_final":1},
            {"person_id":"p1","trial":"b","human_first":1,"human_final":1},
            {"person_id":"p2","trial":"a","human_first":1,"human_final":1},
        ])
        got = leave_one_task_capability(h, "a", min_history=1)
        self.assertEqual(set(got.person_id), {"p1"})

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

    def test_support_flag_is_explicit(self):
        panel = pd.DataFrame([
            {"person_id":"p1","trial":"a","human_first":1,"human_final":1,"capability":0.5,"n_history":30,"capability_stratum":3},
            {"person_id":"p2","trial":"a","human_first":0,"human_final":1,"capability":0.5,"n_history":30,"capability_stratum":3},
        ])
        rates = task_stratum_rates(panel, min_support=3)
        self.assertFalse(bool(rates.iloc[0].supported))
        self.assertEqual(rates.iloc[0].n_human, 2)

    def test_end_to_end_profiles_preserve_recovery_accounting(self):
        rows = []
        # Ten people with ordered capability histories plus two held-out agent tasks.
        for i in range(10):
            pid = f"p{i:02d}"
            # Five history tasks; stronger people succeed on more of them.
            for j in range(5):
                first = int(j < (i // 2 + 1))
                rows.append({"person_id":pid,"trial":f"h{j}","human_first":first,"human_final":first})
            # Human final can recover on target tasks.
            rows.append({"person_id":pid,"trial":"t1","human_first":int(i >= 5),"human_final":1})
            rows.append({"person_id":pid,"trial":"t2","human_first":int(i >= 7),"human_final":int(i >= 3)})
        humans = pd.DataFrame(rows)
        agent = pd.DataFrame([
            {"trial":"t1","agent_correct":0,"act":1},
            {"trial":"t2","agent_correct":1,"act":0},
        ])
        report, panel, rates = analyze(humans, agent, min_history=5, min_support=1)
        self.assertGreater(len(panel), 0)
        self.assertGreater(len(rates), 0)
        supported = [v for v in report["profiles"].values() if v["profile"]]
        self.assertGreaterEqual(len(supported), 2)
        for row in supported:
            p = row["profile"]
            self.assertAlmostEqual(
                p["human_recovery_potential"],
                p["joint_recovery_value"] + p["recovery_suppression_mass"],
            )


if __name__ == "__main__":
    unittest.main()
