import unittest
import numpy as np

from src.capability_twin import (
    autonomy_profile,
    human_leverage,
    recovery_value,
    routed_outcome,
    unsafe_autonomy_mass,
    validate_nested_gate,
)


class CapabilityTwinTests(unittest.TestCase):
    def test_routing_uses_agent_only_on_act_rows(self):
        got = routed_outcome(np.array([1, 0, 1, 0]), np.array([1, 1, 0, 0]), np.array([0, 1, 0, 1]))
        self.assertTrue(np.array_equal(got, np.array([1, 0, 0, 1])))

    def test_human_leverage_can_be_negative_when_bad_autonomy_suppresses_human(self):
        a = np.array([1, 0, 0, 0]); act = np.array([1, 1, 0, 0]); h = np.array([1, 1, 1, 1])
        self.assertGreater(human_leverage(a, np.array([1, 0, 0, 0]), h), human_leverage(a, act, h))

    def test_retry_value_is_nonnegative_when_retry_dominates_first_attempt(self):
        a = np.array([1, 0, 0]); act = np.array([1, 0, 0]); h1 = np.array([1, 0, 1]); h3 = np.array([1, 1, 1])
        self.assertGreaterEqual(recovery_value(a, act, h1, h3), 0.0)

    def test_autonomy_profile_separates_safe_and_unsafe_mass(self):
        a = np.array([1, 0, 1, 0])
        act = np.array([1, 1, 0, 0])
        profile = autonomy_profile(a, act)
        self.assertAlmostEqual(profile["act_coverage"], 0.5)
        self.assertAlmostEqual(profile["act_precision"], 0.5)
        self.assertAlmostEqual(profile["safe_autonomy_mass"], 0.25)
        self.assertAlmostEqual(profile["unsafe_autonomy_mass"], 0.25)
        self.assertAlmostEqual(
            profile["act_coverage"],
            profile["safe_autonomy_mass"] + profile["unsafe_autonomy_mass"],
        )
        self.assertAlmostEqual(unsafe_autonomy_mass(a, act), 0.25)

    def test_autonomy_profile_is_not_coverage_minus_global_accuracy(self):
        # The agent is correct on a deferred row; global accuracy therefore cannot
        # be subtracted from ACT coverage to obtain unsafe autonomous mass.
        a = np.array([1, 0, 1, 0])
        act = np.array([1, 1, 0, 0])
        profile = autonomy_profile(a, act)
        self.assertNotAlmostEqual(profile["unsafe_autonomy_mass"], act.mean() - a.mean())

    def test_stricter_gate_is_nested(self):
        self.assertTrue(validate_nested_gate([0, 1, 2, 5], 1, 2))


if __name__ == "__main__":
    unittest.main()
