import ast
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "experiments/sdf-exterior-2026-11-22/build_v14_nonperiodic_tears.py"


def load_dab(path: Path):
    src = path.read_text()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "dab":
            mod = ast.Module(body=[node], type_ignores=[])
            ast.fix_missing_locations(mod)
            return compile(mod, str(path), "exec")
    raise RuntimeError("dab not found")


class TestRasterDabCounts(unittest.TestCase):
    def setUp(self):
        n = 12
        self.n = n
        self.xs = np.linspace(-18, 18, n)
        self.ys = np.linspace(-18, 18, n)
        self.zs = np.linspace(-1, 50, n)
        self.step = np.array(
            [self.xs[1] - self.xs[0], self.ys[1] - self.ys[0], self.zs[1] - self.zs[0]],
            np.float32,
        )
        self.field = np.zeros((n, n, n), np.float32)
        self.code = load_dab(SOURCE)

    def _make_dab(self):
        field = self.field.copy()
        ns = {
            "np": np,
            "n": self.n,
            "xs": self.xs,
            "ys": self.ys,
            "zs": self.zs,
            "step": self.step,
            "field": field,
            "raster_points": 0,
            "raster_attempted": 0,
            "raster_skipped": 0,
        }
        exec(self.code, ns)
        return ns["dab"], field, ns

    def _assert_invariant(self, ns):
        self.assertEqual(ns["raster_attempted"], ns["raster_points"] + ns["raster_skipped"])

    def test_inside_point_mutates_and_counts_match(self):
        dab, field, ns = self._make_dab()
        init = field.copy()
        dab([0.0, 0.0, 10.0], 100.0, 3.0)
        self.assertFalse(np.array_equal(field, init))
        self.assertGreater(ns["raster_points"], 0)
        self._assert_invariant(ns)

    def test_near_boundary_point_mutates(self):
        dab, field, ns = self._make_dab()
        init = field.copy()
        dab([0.0, 0.0, -0.5], 50.0, 2.0)
        self.assertFalse(np.array_equal(field, init))
        self.assertGreater(ns["raster_points"], 0)
        self._assert_invariant(ns)

    def test_far_outside_points_are_skipped(self):
        dab, field, ns = self._make_dab()
        init = field.copy()
        outside = (
            [1000.0, 0.0, 10.0],
            [-1000.0, 0.0, 10.0],
            [0.0, 1000.0, 10.0],
            [0.0, -1000.0, 10.0],
            [0.0, 0.0, -1000.0],
            [0.0, 0.0, 1000.0],
        )
        for q in outside:
            prev = ns["raster_attempted"]
            dab(q, 100.0, 3.0)
            self.assertTrue(np.array_equal(field, init))
            self.assertEqual(ns["raster_attempted"], prev + 1)
        self.assertEqual(ns["raster_points"], 0)
        self.assertGreater(ns["raster_skipped"], 0)
        self._assert_invariant(ns)

    def test_metadata_keys_present_in_source(self):
        src = SOURCE.read_text()
        for key in ("raster_dabs", "raster_attempted", "raster_skipped"):
            self.assertIn(f'"{key}"', src)


if __name__ == "__main__":
    unittest.main()