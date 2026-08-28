import unittest
import pandas as pd
from analysis.stage004_joint_metrics import summarize_joint


class Stage004JointMetricsTests(unittest.TestCase):
    def setUp(self):
        self.agent = pd.DataFrame([
            {"trial":"a","agent_correct":1,"act":1,"wrong_act":0,"hdc_correct":1},
            {"trial":"b","agent_correct":0,"act":1,"wrong_act":1,"hdc_correct":1},
            {"trial":"c","agent_correct":0,"act":0,"wrong_act":0,"hdc_correct":0},
        ])
        self.humans = pd.DataFrame([
            {"trial":"a","person_id":"p1","human_first":0,"human_final":1},
            {"trial":"a","person_id":"p2","human_first":1,"human_final":1},
            {"trial":"b","person_id":"p1","human_first":1,"human_final":1},
            {"trial":"b","person_id":"p2","human_first":1,"human_final":1},
            {"trial":"c","person_id":"p1","human_first":1,"human_final":1},
            {"trial":"c","person_id":"p2","human_first":0,"human_final":1},
        ])

    def test_unsafe_autonomy_and_act_precision(self):
        r=summarize_joint(self.agent,self.humans)
        self.assertAlmostEqual(r["act_coverage"],2/3)
        self.assertAlmostEqual(r["act_precision"],0.5)
        self.assertAlmostEqual(r["unsafe_autonomy_mass"],1/3)

    def test_bad_autonomy_can_make_joint_worse(self):
        r=summarize_joint(self.agent,self.humans)
        self.assertLess(r["task_balanced_joint_one_shot"],r["task_balanced_human_one_shot"])
        self.assertGreater(r["task_balanced_joint_retry3"],r["standalone_accuracy"])

    def test_hdc_diagnostics_separate_correct_and_wrong_production(self):
        r=summarize_joint(self.agent,self.humans)
        self.assertEqual(r["hdc_prod_correct_rate"],1.0)
        self.assertEqual(r["hdc_prod_wrong_rate"],0.5)


if __name__ == "__main__":
    unittest.main()
