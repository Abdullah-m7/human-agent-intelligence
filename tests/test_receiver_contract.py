import unittest

import numpy as np

from src.receiver_contract import receiver_contract_profile


class ReceiverContractTests(unittest.TestCase):
    def test_no_autonomy_preserves_all_recovery(self):
        r = receiver_contract_profile(
            agent_correct=[0, 1],
            agent_act=[0, 0],
            human_first=[0.2, 0.6],
            human_final=[0.5, 0.9],
        )
        self.assertAlmostEqual(r["recovery_suppression_mass"], 0.0)
        self.assertAlmostEqual(r["recovery_capture_ratio"], 1.0)
        self.assertAlmostEqual(r["joint_recovery_value"], r["human_recovery_potential"])

    def test_full_autonomy_suppresses_all_human_recovery(self):
        r = receiver_contract_profile(
            agent_correct=[1, 0],
            agent_act=[1, 1],
            human_first=[0.2, 0.6],
            human_final=[0.5, 0.9],
        )
        self.assertAlmostEqual(r["joint_recovery_value"], 0.0)
        self.assertAlmostEqual(r["recovery_capture_ratio"], 0.0)
        self.assertAlmostEqual(r["recovery_suppression_mass"], r["human_recovery_potential"])

    def test_wrong_autonomy_is_more_costly_when_human_is_stronger(self):
        weak = receiver_contract_profile([0], [1], [0.2], [0.2])
        strong = receiver_contract_profile([0], [1], [0.9], [0.9])
        self.assertGreater(
            strong["one_shot"]["harmful_displacement_mass"],
            weak["one_shot"]["harmful_displacement_mass"],
        )
        self.assertLess(
            strong["one_shot"]["net_routing_value"],
            weak["one_shot"]["net_routing_value"],
        )

    def test_correct_autonomy_is_more_valuable_when_human_is_weaker(self):
        weak = receiver_contract_profile([1], [1], [0.2], [0.2])
        strong = receiver_contract_profile([1], [1], [0.9], [0.9])
        self.assertGreater(
            weak["one_shot"]["beneficial_autonomy_mass"],
            strong["one_shot"]["beneficial_autonomy_mass"],
        )

    def test_routing_identity_holds(self):
        r = receiver_contract_profile(
            agent_correct=[1, 0, 1, 0],
            agent_act=[1, 1, 0, 0],
            human_first=[0.1, 0.8, 0.4, 0.7],
            human_final=[0.3, 0.9, 0.8, 1.0],
        )
        for key in ("one_shot", "retry_enabled"):
            p = r[key]
            self.assertAlmostEqual(
                p["joint_performance"],
                p["human_baseline"] + p["net_routing_value"],
            )
            self.assertAlmostEqual(
                p["net_routing_value"],
                p["beneficial_autonomy_mass"] - p["harmful_displacement_mass"],
            )
        self.assertAlmostEqual(
            r["human_recovery_potential"],
            r["joint_recovery_value"] + r["recovery_suppression_mass"],
        )

    def test_final_must_dominate_first(self):
        with self.assertRaises(ValueError):
            receiver_contract_profile([1], [0], [0.8], [0.7])

    def test_inputs_must_share_shape(self):
        with self.assertRaises(ValueError):
            receiver_contract_profile([1, 0], [1], [0.2], [0.3])

    def test_zero_recovery_has_no_ratio(self):
        r = receiver_contract_profile([1], [0], [0.5], [0.5])
        self.assertIsNone(r["recovery_capture_ratio"])
        self.assertTrue(np.isclose(r["human_recovery_potential"], 0.0))


if __name__ == "__main__":
    unittest.main()
