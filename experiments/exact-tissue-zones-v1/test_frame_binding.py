"""Regression checks for authentic but mislabelled render receipts."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from compare_renders import PR32_SHA256, validate_frame_binding

HERE = Path(__file__).resolve().parent


class FrameBindingTests(unittest.TestCase):
    def setUp(self):
        self.pairs = json.loads((HERE / "render-qa.json").read_text())["pairs"]
        self.hashes = {"pr32": PR32_SHA256,
                       "zones": json.loads((HERE / "build-report.json").read_text())["scene_sha256"]}

    def test_actual_six_receipts_match_slots(self):
        for flavor, row in self.pairs.items():
            for version, receipt in row["frames"].items():
                validate_frame_binding(receipt, version, flavor, self.hashes)

    def test_old_frame_cannot_stand_for_new(self):
        with self.assertRaises(AssertionError):
            validate_frame_binding(self.pairs["saved-beauty"]["frames"]["pr32"],
                                   "zones", "saved-beauty", self.hashes)

    def test_saved_cut_cannot_stand_for_oblique(self):
        with self.assertRaises(AssertionError):
            validate_frame_binding(self.pairs["saved-clay"]["frames"]["zones"],
                                   "zones", "oblique-clay", self.hashes)

    def test_evaluated_pose_and_look_are_checked(self):
        original = self.pairs["saved-clay"]["frames"]["zones"]
        for key, value in (("evaluated_pose_y_xrot_zrot", [0, 0, 0]), ("look", "beauty")):
            receipt = deepcopy(original)
            receipt[key] = value
            with self.assertRaises(AssertionError):
                validate_frame_binding(receipt, "zones", "saved-clay", self.hashes)


if __name__ == "__main__":
    unittest.main()
