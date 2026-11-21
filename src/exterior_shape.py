"""Pure geometry for an artist-built, whole strawberry in millimetres."""

from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from math import cos, floor, isfinite, pi, sin, sqrt, tau
from random import Random


Vec3 = tuple[float, float, float]
MERIDIAN_STEPS = 352
AZIMUTH_STEPS = 448


@dataclass(frozen=True)
class ExteriorParams:
    # Nominal body extents informed by Ariza 2011 Table 2, Camarosa (R0015–16).
    height_mm: float = 48.0
    width_mm: float = 32.5
    seed: int = 1729
    # Artist settings for count and dimensions, including pit size.
    achene_count: int = 264
    achene_length_mm: float = 1.37
    achene_width_mm: float = 0.75
    achene_thickness_mm: float = 0.48
    pit_length_mm: float = 2.72
    pit_width_mm: float = 1.96
    pit_depth_mm: float = 0.32

    def __post_init__(self):
        dimensions = (
            self.height_mm, self.width_mm, self.achene_length_mm,
            self.achene_width_mm, self.achene_thickness_mm, self.pit_length_mm,
            self.pit_width_mm, self.pit_depth_mm,
        )
        if any(not isfinite(value) or value <= 0 for value in dimensions):
            raise ValueError("Exterior dimensions must be positive finite millimetres")
        if self.achene_count < 1:
            raise ValueError("Achene count must be positive")


@dataclass(frozen=True)
class AcheneAnchor:
    meridian: float
    angle: float
    point: Vec3
    normal: Vec3
    long_axis: Vec3
    side_axis: Vec3
    length_mm: float
    width_mm: float
    thickness_mm: float
    pit_length_radius_mm: float
    pit_width_radius_mm: float
    pit_depth_mm: float

    @property
    def center(self) -> Vec3:
        # A little more than half the thickness remains exposed at the pit floor.
        return tuple(
            p + n * (0.19 * self.thickness_mm - self.pit_depth_mm)
            for p, n in zip(self.point, self.normal)
        )


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def unit(v: Vec3) -> Vec3:
    length = sqrt(dot(v, v))
    return tuple(value / length for value in v)


class ExteriorShape:
    """Asymmetric parametric surface. Meridian runs from crown to tip."""

    def __init__(self, params: ExteriorParams):
        self.params = params
        self.phase = Random(params.seed).uniform(0, tau)
        # Fit the wider of the two horizontal axes on the emission grid.
        rings = (
            self._outline(pi * j / MERIDIAN_STEPS)
            for j in range(MERIDIAN_STEPS + 1)
        )
        points = [
            self._xy(outline, tau * i / AZIMUTH_STEPS)
            for outline in rings
            for i in range(AZIMUTH_STEPS)
        ]
        x, y = zip(*points)
        self.xy_scale = params.width_mm / max(max(x) - min(x), max(y) - min(y))

    @staticmethod
    def _outline(meridian):
        h, s = cos(meridian), sin(meridian)
        # A broad shoulder, gently tapered cheek, and subtly off-axis tip.
        radius = s * (0.69 + 0.31 * h + 0.039 * cos(2 * meridian))
        return radius, -0.054 * h + 0.037 * s * s, 0.035 * h, h

    def _xy(self, outline, angle):
        radius, cx, cy, h = outline
        phase = angle + self.phase
        radius *= (1 + 0.039 * cos(2 * phase + 0.8 * h)
                   + 0.035 * cos(3 * phase - 0.9 * h)
                   + 0.015 * sin(5 * phase + 3 * h))
        return cx + radius * cos(angle), cy + radius * sin(angle)

    def point(self, meridian: float, angle: float) -> Vec3:
        outline = self._outline(meridian)
        x, y = self._xy(outline, angle)
        return x * self.xy_scale, y * self.xy_scale, 0.5 * self.params.height_mm * (1 + outline[-1])

    def tangents(self, meridian: float, angle: float) -> tuple[Vec3, Vec3]:
        step = 1e-4
        down = tuple((b - a) / (2 * step) for a, b in zip(
            self.point(meridian - step, angle), self.point(meridian + step, angle)))
        around = tuple((b - a) / (2 * step) for a, b in zip(
            self.point(meridian, angle - step), self.point(meridian, angle + step)))
        return down, around

    def normal(self, meridian: float, angle: float) -> Vec3:
        if meridian in (0.0, pi):
            return (0.0, 0.0, 1.0 if meridian == 0.0 else -1.0)
        down, around = self.tangents(meridian, angle)
        return unit(cross(down, around))

    def anchors(self) -> list[AcheneAnchor]:
        """Jittered phyllotaxis stratified by surface area, excluding the poles."""
        rng = Random(self.params.seed + 1)
        steps = 384
        top, bottom = 0.34, 3.00
        band = (bottom - top) / steps
        cdf = [0.0]
        for index in range(steps):
            meridian = top + (index + 0.5) * band
            area = 0.0
            for longitude in range(8):
                down, around = self.tangents(meridian, tau * longitude / 8)
                cross_section = cross(down, around)
                area += sqrt(dot(cross_section, cross_section))
            cdf.append(cdf[-1] + area)
        golden_angle = pi * (3 - sqrt(5))
        start = rng.uniform(0, tau)
        anchors = []
        jitter_mm = 0.45 * min(self.params.height_mm / 48.0, self.params.width_mm / 32.5, 1.0)
        for index in range(self.params.achene_count):
            target = cdf[-1] * (index + 0.5) / self.params.achene_count
            bucket = bisect_right(cdf, target) - 1
            fraction = (target - cdf[bucket]) / (cdf[bucket + 1] - cdf[bucket])
            meridian = top + (bucket + fraction) * band
            angle = (start + index * golden_angle) % tau
            down, around = self.tangents(meridian, angle)
            meridian += rng.uniform(-jitter_mm, jitter_mm) / sqrt(dot(down, down))
            angle = (angle + rng.uniform(-jitter_mm, jitter_mm) / sqrt(dot(around, around))) % tau

            normal = self.normal(meridian, angle)
            down, _ = self.tangents(meridian, angle)
            along = unit(down)
            across = cross(along, normal)
            tilt = rng.uniform(-0.31, 0.31)
            long_axis = tuple(a * cos(tilt) + b * sin(tilt) for a, b in zip(along, across))
            size = rng.uniform(0.78, 1.19)
            anchors.append(AcheneAnchor(
                meridian, angle, self.point(meridian, angle), normal,
                long_axis, cross(long_axis, normal),
                size * self.params.achene_length_mm,
                size * self.params.achene_width_mm * rng.uniform(0.87, 1.10),
                size * self.params.achene_thickness_mm,
                0.5 * self.params.pit_length_mm * size,
                0.5 * self.params.pit_width_mm * size,
                self.params.pit_depth_mm * rng.uniform(0.69, 1.28),
            ))
        return anchors


class PitField:
    """Compact elliptical depressions, accelerated by a local spatial grid."""

    def __init__(self, anchors: list[AcheneAnchor]):
        self.cell_size = 4.0
        self.cells = defaultdict(list)
        for anchor in anchors:
            radius = max(anchor.pit_length_radius_mm, anchor.pit_width_radius_mm) * 1.12
            low = self._key(tuple(value - radius for value in anchor.point))
            high = self._key(tuple(value + radius for value in anchor.point))
            for x in range(low[0], high[0] + 1):
                for y in range(low[1], high[1] + 1):
                    for z in range(low[2], high[2] + 1):
                        self.cells[x, y, z].append(anchor)

    def _key(self, point: Vec3) -> tuple[int, int, int]:
        return tuple(floor(value / self.cell_size) for value in point)

    def sample(self, point: Vec3) -> tuple[float, float]:
        """Depth in mm and a unit mask over the pit."""
        depth, mask = 0.0, 0.0
        for anchor in self.cells.get(self._key(point), ()):
            offset = tuple(a - b for a, b in zip(point, anchor.point))
            # The normal term keeps the footprint local on a curved surface.
            radius_squared = (
                (dot(offset, anchor.long_axis) / anchor.pit_length_radius_mm) ** 2
                + (dot(offset, anchor.side_axis) / anchor.pit_width_radius_mm) ** 2
                + (dot(offset, anchor.normal) / (0.62 * anchor.pit_width_radius_mm)) ** 2
            )
            if radius_squared < 1.0:
                weight = (1 - radius_squared ** 2) ** 3
                depth = max(depth, anchor.pit_depth_mm * weight)
                mask = max(mask, weight)
        return depth, mask

    def deform(self, shape: ExteriorShape, meridian: float, angle: float) -> tuple[Vec3, float]:
        point = shape.point(meridian, angle)
        depth, mask = self.sample(point)
        if depth:
            point = tuple(a - b * depth for a, b in zip(point, shape.normal(meridian, angle)))
        return point, mask
