import unittest

import pandas as pd

from analysis.paper04_task_bootstrap import paired_task_bootstrap, validate_matched_rates


class Paper04TaskBootstrapTests(unittest.TestCase):
    def setUp(self):
        rate_rows = []
        for task in ("a", "b", "c"):
            for q in range(1, 6):
                # Human success rises with receiver stratum; retry adds 0.1 where possible.
                h1 = min(0.1 * q + (0.05 if task == "b" else 0.0), 0.9)
                hf = min(h1 + 0.1, 1.0)
                rate_rows.append({
                    "trial": task,
                    "capability_stratum": q,
                    "human_first": h1,
                    "human_final": hf,
                    "n_human": 20,
                })
        self.rates = pd.DataFrame(rate_rows)
        self.agent = pd.DataFrame([
            {"trial":"a","agent_correct":1,"act":1},
            {"trial":"b","agent_correct":0,"act":1},
            {"trial":"c","agent_correct":0,"act":0},
        ])

    def test_matched_rates_require_all_five_strata(self):
        bad = self.rates[~((self.rates.trial == "a") & (self.rates.capability_stratum == 5))]
        with self.assertRaises(ValueError):
            validate_matched_rates(bad, self.agent, ["a", "b", "c"])

    def test_bootstrap_is_deterministic_given_seed(self):
        a = paired_task_bootstrap(self.rates, self.agent, ["a", "b", "c"], n_boot=50, seed=7)
        b = paired_task_bootstrap(self.rates, self.agent, ["a", "b", "c"], n_boot=50, seed=7)
        self.assertEqual(a, b)

    def test_bootstrap_uses_requested_number_of_draws(self):
        r = paired_task_bootstrap(self.rates, self.agent, ["a", "b", "c"], n_boot=37, seed=1)
        self.assertEqual(r["n_boot"], 37)
        for s in r["summaries"].values():
            self.assertEqual(s["n"], 37)

    def test_stronger_humans_make_wrong_autonomy_more_costly(self):
        r = paired_task_bootstrap(self.rates, self.agent, ["a", "b", "c"], n_boot=100, seed=9)
        harmful = r["summaries"]["one_shot_harmful_displacement_slope"]
        self.assertGreater(harmful["mean"], 0)
        self.assertGreater(harmful["fraction_gt_0"], 0.9)

    def test_retry_contract_changes_net_gradient_when_recovery_varies(self):
        # Give higher strata additional recovery specifically on autonomous tasks.
        rates = self.rates.copy()
        for idx, row in rates.iterrows():
            if row.trial in ("a", "b"):
                rates.at[idx, "human_final"] = min(row.human_first + 0.03 * row.capability_stratum, 1.0)
        r = paired_task_bootstrap(rates, self.agent, ["a", "b", "c"], n_boot=80, seed=4)
        delta = r["summaries"]["retry_minus_one_shot_net_slope"]
        self.assertNotEqual(delta["mean"], 0.0)

    def test_duplicate_input_task_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            paired_task_bootstrap(self.rates, self.agent, ["a", "a", "b"], n_boot=10)


if __name__ == "__main__":
    unittest.main()
