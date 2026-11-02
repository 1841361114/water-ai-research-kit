import itertools
import json
import math
import tempfile
import unittest
from pathlib import Path

from water_ai_research.audit import verify_manifest
from water_ai_research.demo import run_demo
from water_ai_research.metrics import regression_metrics
from water_ai_research.sensitivity import grouped_view_bounds


class MetricDemoTests(unittest.TestCase):
    def test_regression_hand_computed(self):
        result = regression_metrics([1, 2, 3], [2, 2, 2])
        self.assertAlmostEqual(result["mae"], 2 / 3)
        self.assertAlmostEqual(result["rmse"], math.sqrt(2 / 3))
        self.assertEqual(result["nse"], 0)
        self.assertEqual(regression_metrics([1, 2], [1, 2])["nse"], 1)

    def test_constant_nse_is_undefined(self):
        self.assertIsNone(regression_metrics([2, 2], [1, 3])["nse"])
        self.assertLess(regression_metrics([1, 2], [9, 9])["nse"], 0)

    def test_regression_no_silent_missing_filter(self):
        for observed, predicted in [([], []), ([1], []), ([1], [float("nan")])]:
            with self.assertRaises(ValueError):
                regression_metrics(observed, predicted)

    def test_group_bounds_against_exhaustive_enumeration(self):
        groups = {"a": [-2, 3], "b": [1, -1], "fixed": [4]}
        all_means = [math.fsum(choice) / 7 for choice in itertools.product(*groups.values())]
        result = grouped_view_bounds(groups, 7)
        self.assertAlmostEqual(result["lower"], min(all_means))
        self.assertAlmostEqual(result["upper"], max(all_means))

    def test_group_bounds_invalid(self):
        for groups, count in [({}, 1), ({"a": []}, 1), ({"a": [1]}, 0), ({"a": [math.inf]}, 1)]:
            with self.assertRaises(ValueError):
                grouped_view_bounds(groups, count)

    def test_demo_reproducibility_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / "a", Path(directory) / "b"
            first, second = run_demo(a), run_demo(b)
            self.assertEqual(first, second)
            self.assertTrue(first["synthetic"])
            self.assertFalse(first["scientific_validation"])
            for name in ["series.json", "protocol.json", "report.json", "manifest.json"]:
                self.assertEqual((a / name).read_bytes(), (b / name).read_bytes())
            verify_manifest(a, json.loads((a / "manifest.json").read_text()))
            with self.assertRaises(FileExistsError):
                run_demo(a)


if __name__ == "__main__":
    unittest.main()
