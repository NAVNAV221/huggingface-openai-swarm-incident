import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "analysis"))
from stats import clopper_pearson, cohen_kappa, fisher_exact_two_sided, holm, one_sided_zero_upper, wilson  # noqa: E402


class StatsTests(unittest.TestCase):
    def test_zero_power_precision(self):
        self.assertAlmostEqual(one_sided_zero_upper(60), 0.0487029, places=6)
        lower, upper = clopper_pearson(0, 20)
        self.assertEqual(lower, 0)
        self.assertAlmostEqual(upper, 0.16843347, places=6)
        self.assertGreater(upper, one_sided_zero_upper(20))

    def test_exact_all_success_interval(self):
        lower, upper = clopper_pearson(20, 20)
        self.assertAlmostEqual(lower, 0.8315665, places=6)
        self.assertEqual(upper, 1)

    def test_wilson_zero(self):
        lower, upper = wilson(0, 20)
        self.assertEqual(lower, 0)
        self.assertAlmostEqual(upper, 0.16113, places=4)

    def test_fisher_all_zero_is_one(self):
        self.assertEqual(fisher_exact_two_sided(0, 60, 0, 60), 1)

    def test_holm(self):
        self.assertEqual(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])

    def test_kappa(self):
        self.assertEqual(cohen_kappa([True, False, True], [True, False, True]), 1)
        self.assertAlmostEqual(cohen_kappa([True, True, False, False], [True, False, True, False]), 0)
        self.assertIsNone(cohen_kappa([None], [True]))
        self.assertIsNone(cohen_kappa([True, True], [True, True]), "kappa undefined with no label variance")


if __name__ == "__main__":
    unittest.main()
