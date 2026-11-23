"""Decode the existing Non-Color PNG as a rest-space trilinear lookup."""

from math import floor

import numpy as np

N = 150
COLS = 15
ROWS = 10
# SUBTRACT and DIVIDE defaults from the authenticated cap shader.
LO = tuple(map(float, np.float32([-1.3, -1.3, -1.23])))
SPAN = tuple(map(float, np.float32([2.6, 2.6, 2.28])))
ATLAS = "LIVE | ORIGINAL V0 native RGB volume atlas (150^3)"


class TissueAtlas:
    def __init__(self, image):
        if (tuple(image.size) != (N * COLS, N * ROWS)
                or image.colorspace_settings.name != "Non-Color" or not image.packed_file):
            raise ValueError("Expected the original packed 150³ Non-Color atlas")
        pixels = np.empty(N * COLS * N * ROWS * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        # Blender's buffer starts at the bottom left. Layout: [tile row, y, tile column, x, rgba].
        tiles = pixels.reshape(ROWS, N, COLS, N, 4)
        self.rgb = np.ascontiguousarray(tiles.transpose(0, 2, 1, 3, 4)[..., :3])
        self.rgb.shape = (N, N, N, 3)  # z, y, x, rgb
        self.green = memoryview(self.rgb[..., 1].copy())

    def grid(self, point):
        return tuple(min(N - 1, max(0.0, (p - lo) * (N - 1) / span))
                     for p, lo, span in zip(point, LO, SPAN, strict=True))

    def sample_green(self, point):
        x, y, z = self.grid(point)
        i, j, k = floor(x), floor(y), floor(z)
        ii, jj, kk = min(i + 1, N - 1), min(j + 1, N - 1), min(k + 1, N - 1)
        a, b, c = x - i, y - j, z - k
        g = self.green
        bottom = (1 - b) * ((1 - a) * g[k, j, i] + a * g[k, j, ii]) + b * (
            (1 - a) * g[k, jj, i] + a * g[k, jj, ii])
        top = (1 - b) * ((1 - a) * g[kk, j, i] + a * g[kk, j, ii]) + b * (
            (1 - a) * g[kk, jj, i] + a * g[kk, jj, ii])
        return (1 - c) * bottom + c * top
