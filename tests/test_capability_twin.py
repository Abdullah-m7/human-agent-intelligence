import unittest
import numpy as np

from src.capability_twin import autonomy_gap, human_leverage, recovery_value, routed_outcome, validate_nested_gate


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

    def test_autonomy_gap_separates_coverage_from_accuracy(self):
        self.assertAlmostEqual(autonomy_gap(0.333333, 0.493333), 0.16, places=5)

    def test_stricter_gate_is_nested(self):
        self.assertTrue(validate_nested_gate([0, 1, 2, 5], 1, 2))


if __name__ == "__main__":
    unittest.main()
