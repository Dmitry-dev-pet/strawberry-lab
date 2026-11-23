"""Shared names for the single-scene View Layer controls."""

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "integration-live-exterior-v1"))

PR30_SHA256 = "0b8af93c399d0077f51f864f7b9f55673b822a1755e2badcc626f5bfc6256bca"
SCENE_FILE = "strawberry-layer-modes.blend"
GUIDE_TEXT = "START HERE | Strawberry layer modes.txt"
UI_TEXT = "LAYER_MODES_CONTROLS__RUN.py"
PARK_KNIFE = "strawberry_park_knife"
CLIP_DIAGNOSTICS = "strawberry_clip_diagnostics"
MARKERS = "Markers | 539 diagnostic anchors"
MODES = {
    "whole": "WHOLE",
    "matched": "MATCHED",
    "flesh-only": "FLESH ONLY",
    "fibers-only": "FIBERS ONLY",
}
