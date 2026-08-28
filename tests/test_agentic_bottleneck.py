import unittest

from src.agentic_bottleneck import Params, effective_agent, joint_accuracy, sensitivity


class AgenticBottleneckTests(unittest.TestCase):
    def base(self, **changes):
        data = dict(
            agent=0.75,
            human=0.65,
            specification=0.70,
            verification=0.70,
            specificity=0.90,
            autonomy=0.50,
            beta_spec=0.20,
        )
        data.update(changes)
        return Params(**data)

    def test_full_autonomy_equals_effective_agent(self):
        p = self.base(autonomy=1.0)
        self.assertAlmostEqual(joint_accuracy(p), effective_agent(p), places=12)

    def test_full_autonomy_removes_fallback_and_review_effects(self):
        p = self.base(autonomy=1.0)
        self.assertAlmostEqual(sensitivity(p, "human"), 0.0, places=8)
        self.assertAlmostEqual(sensitivity(p, "verification"), 0.0, places=8)
        self.assertAlmostEqual(sensitivity(p, "specificity"), 0.0, places=8)

    def test_specification_effect_persists_at_full_autonomy(self):
        p = self.base(autonomy=1.0, specification=0.60)
        self.assertGreater(sensitivity(p, "specification"), 0.0)
        self.assertAlmostEqual(sensitivity(p, "specification"), p.beta_spec, places=6)

    def test_human_sensitivity_falls_with_autonomy(self):
        low = abs(sensitivity(self.base(autonomy=0.0), "human"))
        mid = abs(sensitivity(self.base(autonomy=0.5), "human"))
        high = abs(sensitivity(self.base(autonomy=0.9), "human"))
        self.assertGreater(low, mid)
        self.assertGreater(mid, high)

    def test_verification_sensitivity_falls_with_autonomy(self):
        low = abs(sensitivity(self.base(autonomy=0.0), "verification"))
        mid = abs(sensitivity(self.base(autonomy=0.5), "verification"))
        high = abs(sensitivity(self.base(autonomy=0.9), "verification"))
        self.assertGreater(low, mid)
        self.assertGreater(mid, high)


if __name__ == "__main__":
    unittest.main()
