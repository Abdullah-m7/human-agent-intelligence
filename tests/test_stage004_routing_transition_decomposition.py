import unittest

import pandas as pd

from analysis.stage004_routing_transition_decomposition import decompose, prepare_rows


class Stage004RoutingTransitionTests(unittest.TestCase):
    def test_four_region_decomposition_sums_exactly(self):
        weak = pd.DataFrame([
            {"trial":"dd","agent_correct":0,"act":0},
            {"trial":"aa","agent_correct":1,"act":1},
            {"trial":"na","agent_correct":0,"act":0},
            {"trial":"rt","agent_correct":0,"act":1},
        ])
        strong = pd.DataFrame([
            {"trial":"dd","agent_correct":1,"act":0},
            {"trial":"aa","agent_correct":0,"act":1},
            {"trial":"na","agent_correct":0,"act":1},
            {"trial":"rt","agent_correct":1,"act":0},
        ])
        h = pd.DataFrame([
            {"trial":"dd","human_success":0.5},
            {"trial":"aa","human_success":0.8},
            {"trial":"na","human_success":1.0},
            {"trial":"rt","human_success":1.0},
        ])
        r = decompose(prepare_rows(weak,strong,h))
        contrib = sum(x["contribution_to_total_delta_joint"] for x in r["regions"].values())
        self.assertAlmostEqual(contrib, r["delta_joint_strong_minus_weak"])
        self.assertEqual(r["regions"]["defer_both"]["n_tasks"],1)
        self.assertEqual(r["regions"]["act_both"]["n_tasks"],1)
        self.assertEqual(r["regions"]["new_strong_autonomy"]["n_tasks"],1)
        self.assertEqual(r["regions"]["strong_retrenchment"]["n_tasks"],1)

    def test_new_autonomy_can_harm_by_displacing_better_human(self):
        weak = pd.DataFrame([{"trial":"x","agent_correct":0,"act":0}])
        strong = pd.DataFrame([{"trial":"x","agent_correct":0,"act":1}])
        h = pd.DataFrame([{"trial":"x","human_success":0.9}])
        r = decompose(prepare_rows(weak,strong,h))
        self.assertAlmostEqual(r["delta_joint_strong_minus_weak"],-0.9)
        self.assertAlmostEqual(r["autonomy_displacement_term"],-0.9)

    def test_beneficial_new_autonomy_is_positive(self):
        weak = pd.DataFrame([{"trial":"x","agent_correct":0,"act":0}])
        strong = pd.DataFrame([{"trial":"x","agent_correct":1,"act":1}])
        h = pd.DataFrame([{"trial":"x","human_success":0.25}])
        r = decompose(prepare_rows(weak,strong,h))
        self.assertAlmostEqual(r["autonomy_displacement_term"],0.75)

    def test_shared_act_region_is_agent_correctness_difference(self):
        weak = pd.DataFrame([{"trial":"x","agent_correct":0,"act":1}])
        strong = pd.DataFrame([{"trial":"x","agent_correct":1,"act":1}])
        h = pd.DataFrame([{"trial":"x","human_success":0.9}])
        r = decompose(prepare_rows(weak,strong,h))
        self.assertAlmostEqual(r["regions"]["act_both"]["contribution_to_total_delta_joint"],1.0)

    def test_mismatched_task_sets_are_rejected(self):
        weak = pd.DataFrame([{"trial":"x","agent_correct":0,"act":0}])
        strong = pd.DataFrame([{"trial":"y","agent_correct":1,"act":1}])
        h = pd.DataFrame([{"trial":"x","human_success":0.5},{"trial":"y","human_success":0.5}])
        with self.assertRaises(ValueError):
            prepare_rows(weak,strong,h)


if __name__ == "__main__":
    unittest.main()
