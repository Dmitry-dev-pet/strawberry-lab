from dataclasses import FrozenInstanceError
from math import pi, tau
import unittest

from exterior_shape import AcheneAnchor, ExteriorParams, ExteriorShape, PitField, cross, dot


class ExteriorShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = ExteriorParams()
        cls.shape = ExteriorShape(cls.params)
        cls.anchors = cls.shape.anchors()
        cls.pits = PitField(cls.anchors)

    def test_nominal_extents_and_asymmetric_silhouette(self):
        self.assertEqual(self.shape.point(0, 0)[2], self.params.height_mm)
        self.assertEqual(self.shape.point(pi, 0)[2], 0.0)
        samples = [self.shape.point(pi * j / 80, tau * i / 96)
                   for j in range(81) for i in range(96)]
        widths = [max(p[axis] for p in samples) - min(p[axis] for p in samples)
                  for axis in (0, 1)]
        self.assertAlmostEqual(max(widths), self.params.width_mm, delta=0.05)
        self.assertGreater(abs(widths[0] - widths[1]), 1.0)
        self.assertGreater(abs(self.shape.point(0, 0)[0] - self.shape.point(pi, 0)[0]), 1.0)

    def test_seed_is_reproducible_and_changes_placement(self):
        self.assertEqual(self.anchors, ExteriorShape(self.params).anchors())
        other = ExteriorShape(ExteriorParams(seed=10)).anchors()
        self.assertNotEqual(self.anchors[0].point, other[0].point)
        self.assertEqual(len(other), len(self.anchors))
        with self.assertRaises(FrozenInstanceError):
            self.params.seed = 10

    def test_anchors_follow_the_surface_and_expose_part_of_the_seed(self):
        self.assertEqual(len(self.anchors), self.params.achene_count)
        for anchor in self.anchors:
            self.assertEqual(anchor.point, self.shape.point(anchor.meridian, anchor.angle))
            self.assertAlmostEqual(dot(anchor.normal, anchor.normal), 1.0)
            self.assertAlmostEqual(dot(anchor.normal, anchor.long_axis), 0.0)
            self.assertAlmostEqual(dot(anchor.normal, anchor.side_axis), 0.0)
            self.assertAlmostEqual(dot(cross(anchor.side_axis, anchor.long_axis), anchor.normal), 1.0)
            self.assertGreater(anchor.length_mm, anchor.width_mm)
            self.assertGreater(anchor.width_mm, anchor.thickness_mm)
            floor, weight = self.pits.deform(self.shape, anchor.meridian, anchor.angle)
            inward = tuple(a - b for a, b in zip(anchor.point, floor))
            above_floor = tuple(a - b for a, b in zip(anchor.center, floor))
            self.assertAlmostEqual(dot(inward, anchor.normal), anchor.pit_depth_mm)
            self.assertAlmostEqual(dot(above_floor, anchor.normal), 0.19 * anchor.thickness_mm)
            self.assertEqual(weight, 1.0)

    def test_pit_is_elliptical_and_deformation_ends_at_its_footprint(self):
        anchor = AcheneAnchor(0.0, 0.0, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0),
                              (0.0, 1.0, 0.0), (1.0, 0.0, 0.0),
                              1.5, 0.8, 0.5, 1.4, 1.0, 0.32)
        pits = PitField([anchor])
        self.assertEqual(pits.sample(anchor.point), (0.32, 1.0))
        self.assertGreater(pits.sample((0.0, 0.8, 0.0))[0], pits.sample((0.8, 0.0, 0.0))[0])
        self.assertEqual(pits.sample((1.0, 0.0, 0.0)), (0.0, 0.0))
        self.assertEqual(pits.sample((0.0, 1.4, 0.0)), (0.0, 0.0))
        self.assertEqual(pits.sample((0.0, 0.0, 2.0)), (0.0, 0.0))

    def test_anchors_cover_tip_and_shoulder_without_collisions(self):
        self.assertGreater(max(a.point[2] for a in self.anchors), 44.0)
        self.assertLess(min(a.point[2] for a in self.anchors), 2.0)
        for index, anchor in enumerate(self.anchors):
            for other in self.anchors[:index]:
                separation = sum((a - b) ** 2 for a, b in zip(anchor.point, other.point))
                self.assertGreater(separation, 1.7 ** 2)


if __name__ == "__main__":
    unittest.main()
