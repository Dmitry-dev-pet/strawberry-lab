"""Exercise CPU atlas layout and interpolation without Blender or an input asset."""

import unittest

import numpy as np

from atlas import COLS, LO, N, ROWS, SPAN, TissueAtlas


class Fixture:
    size = (COLS*N, ROWS*N)
    packed_file = object()

    class colorspace_settings:
        name = "Non-Color"

    class pixels:
        @staticmethod
        def foreach_get(buffer):
            bottom_up = buffer.reshape(ROWS, N, COLS, N, 4)
            for k in range(N):
                tile = bottom_up[k//COLS, :, k%COLS, :, :]
                tile[..., 0] = 0
                tile[..., 1] = response(np.arange(N)[None, :], np.arange(N)[:, None], k)
                tile[..., 2] = 0
                tile[..., 3] = 1


def response(x, y, z):
    # Distinct slopes on every axis and a cross term whose interpolation must remain linear per axis.
    return (x + 2*y + 3*z)/1000 + x*z/1000000


def rest(x, y, z):
    return tuple(lo + span*index/(N - 1) for lo, span, index in zip(LO, SPAN, (x, y, z), strict=True))


class AtlasSamplingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.atlas = TissueAtlas(Fixture())

    def test_exact_voxel_centers_preserve_axes_and_row_order(self):
        for i, j, k in ((0, 0, 0), (17, 135, 14), (135, 17, 15), (130, 84, 149)):
            self.assertAlmostEqual(self.atlas.sample_green(rest(i, j, k)), response(i, j, k), places=7)

    def test_fractional_sampling_across_tile_row_never_uses_adjacent_uv_tile(self):
        for p in ((16.125, 134.375, 14.65), (149, 0, 44.5), (0, 149, 104.25)):
            self.assertAlmostEqual(self.atlas.sample_green(rest(*p)), response(*p), places=7)

    def test_clamps_xyz_independently_before_interpolation(self):
        self.assertAlmostEqual(self.atlas.sample_green(rest(-3, 172, 39.3)), response(0, 149, 39.3), places=7)
        self.assertAlmostEqual(self.atlas.sample_green(rest(172, 32.1, 155)), response(149, 32.1, 149), places=7)

    def test_rejects_rgba_source_with_color_management(self):
        linear = Fixture()
        linear.colorspace_settings = type("ColorSpace", (), {"name": "sRGB"})()
        with self.assertRaisesRegex(ValueError, "Non-Color"):
            TissueAtlas(linear)


if __name__ == "__main__":
    unittest.main()
