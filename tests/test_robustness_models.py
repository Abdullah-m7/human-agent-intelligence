import unittest

from src.agentic_bottleneck import Params, gated_accuracy, joint_accuracy
from src.robustness_models import (
    SelectiveReviewParams,
    bernoulli_joint,
    correlated_gated_accuracy,
    correlated_joint_accuracy,
    correlated_sensitivity,
    selective_profile,
    selective_sensitivity,
)


class CorrelatedErrorTests(unittest.TestCase):
    def base(self, **changes):
        data = dict(
            agent=0.78,
            human=0.67,
            specification=0.70,
            verification=0.72,
            specificity=0.90,
            autonomy=0.40,
            beta_spec=0.20,
        )
        data.update(changes)
        return Params(**data)

    def test_zero_correlation_matches_stage001(self):
        p = self.base()
        self.assertAlmostEqual(correlated_gated_accuracy(p, 0.0), gated_accuracy(p), places=12)
        self.assertAlmostEqual(correlated_joint_accuracy(p, 0.0), joint_accuracy(p), places=12)

    def test_joint_distribution_is_valid_when_requested_corr_is_infeasible(self):
        probs = bernoulli_joint(0.95, 0.20, -0.95)
        p11, p10, p01, p00, realized = probs
        for value in (p11, p10, p01, p00):
            self.assertGreaterEqual(value, -1e-12)
            self.assertLessEqual(value, 1.0 + 1e-12)
        self.assertAlmostEqual(sum((p11, p10, p01, p00)), 1.0, places=12)
        self.assertGreaterEqual(realized, -1.0)
        self.assertLessEqual(realized, 1.0)

    def test_full_autonomy_makes_error_correlation_irrelevant(self):
        p = self.base(autonomy=1.0)
        low = correlated_joint_accuracy(p, -0.5)
        high = correlated_joint_accuracy(p, 0.5)
        self.assertAlmostEqual(low, high, places=12)

    def test_fallback_sensitivity_attenuates_with_autonomy_under_correlation(self):
        low = abs(correlated_sensitivity(self.base(autonomy=0.0), 0.35, "human"))
        high = abs(correlated_sensitivity(self.base(autonomy=0.8), 0.35, "human"))
        self.assertGreater(low, high)


class SelectiveReviewTests(unittest.TestCase):
    def base(self, **changes):
        data = dict(
            agent=0.78,
            human=0.67,
            specification=0.70,
            verification=0.72,
            specificity=0.90,
            review_threshold=0.75,
            beta_spec=0.20,
            difficulty_scale=1.20,
            review_sharpness=35.0,
            difficulty_points=101,
        )
        data.update(changes)
        return SelectiveReviewParams(**data)

    def test_lower_review_threshold_increases_effective_autonomy(self):
        more_autonomous = selective_profile(self.base(review_threshold=0.60))["effective_autonomy"]
        less_autonomous = selective_profile(self.base(review_threshold=0.90))["effective_autonomy"]
        self.assertGreater(more_autonomous, less_autonomous)

    def test_human_sensitivity_is_lower_under_more_autonomous_policy(self):
        more_autonomous = abs(selective_sensitivity(self.base(review_threshold=0.60), "human"))
        less_autonomous = abs(selective_sensitivity(self.base(review_threshold=0.90), "human"))
        self.assertLess(more_autonomous, less_autonomous)

    def test_specification_sensitivity_persists_when_review_is_rare(self):
        p = self.base(review_threshold=0.55)
        profile = selective_profile(p)
        self.assertGreater(profile["effective_autonomy"], 0.5)
        self.assertGreater(abs(selective_sensitivity(p, "specification")), 0.01)


if __name__ == "__main__":
    unittest.main()
