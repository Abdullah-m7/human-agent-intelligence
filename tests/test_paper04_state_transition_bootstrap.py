import unittest

import pandas as pd

from analysis.paper04_state_transition_bootstrap import paired_state_transition_bootstrap


class Paper04StateTransitionBootstrapTests(unittest.TestCase):
    def setUp(self):
        rows = []
        for task in ("a", "b", "c", "d"):
            for q in range(1, 6):
                h1 = 0.10 + 0.15 * q
                hf = min(h1 + 0.10, 1.0)
                rows.append({
                    "trial": task,
                    "capability_stratum": q,
                    "human_first": h1,
                    "human_final": hf,
                    "n_human": 20,
                })
        self.rates = pd.DataFrame(rows)
        self.weak = pd.DataFrame([
            {"trial":"a","agent_correct":1,"act":1},
            {"trial":"b","agent_correct":0,"act":0},
            {"trial":"c","agent_correct":0,"act":0},
            {"trial":"d","agent_correct":0,"act":0},
        ])
        self.strong = pd.DataFrame([
            {"trial":"a","agent_correct":1,"act":1},
            {"trial":"b","agent_correct":1,"act":1},
            {"trial":"c","agent_correct":0,"act":1},
            {"trial":"d","agent_correct":0,"act":1},
        ])

    def test_transition_bootstrap_is_deterministic(self):
        a = paired_state_transition_bootstrap(self.rates,self.weak,self.strong,["a","b","c","d"],n_boot=50,seed=9)
        b = paired_state_transition_bootstrap(self.rates,self.weak,self.strong,["a","b","c","d"],n_boot=50,seed=9)
        self.assertEqual(a,b)

    def test_wrong_new_autonomy_harms_stronger_receivers_more(self):
        r = paired_state_transition_bootstrap(self.rates,self.weak,self.strong,["a","b","c","d"],n_boot=200,seed=3)
        slope = r["capability_gradient_of_transition"]["delta_one_shot_joint_slope"]
        self.assertLess(slope["mean"],0)
        self.assertGreater(slope["fraction_lt_0"],0.95)

    def test_harmful_displacement_increases_for_all_strata(self):
        r = paired_state_transition_bootstrap(self.rates,self.weak,self.strong,["a","b","c","d"],n_boot=100,seed=4)
        for q in range(1,6):
            s = r["by_capability_stratum"][str(q)]["delta_one_shot_harmful_displacement"]
            self.assertGreater(s["mean"],0)

    def test_recovery_capture_falls_when_strong_acts_on_more_tasks(self):
        r = paired_state_transition_bootstrap(self.rates,self.weak,self.strong,["a","b","c","d"],n_boot=100,seed=5)
        for q in range(1,6):
            s = r["by_capability_stratum"][str(q)]["delta_recovery_capture_ratio"]
            self.assertLess(s["mean"],0)

    def test_mismatched_agent_task_sets_are_rejected(self):
        bad = self.strong[self.strong.trial != "d"]
        with self.assertRaises(ValueError):
            paired_state_transition_bootstrap(self.rates,self.weak,bad,["a","b","c"],n_boot=10)

    def test_duplicate_bootstrap_task_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            paired_state_transition_bootstrap(self.rates,self.weak,self.strong,["a","a","b"],n_boot=10)


if __name__ == "__main__":
    unittest.main()
