"""Names and poses shared by the scene builder, renderer and validator."""

from hashlib import file_digest
from math import radians
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE_SHA256 = "56b6d516e8794fb855512978e90e37cd754374a594fb4c5103e672c960a031cf"
SOURCE_SCENE = "LIVE MATCHED | shared movable plane"
SOURCE_BODY = SOURCE_SCENE + " | LIVE cut berry"
KNIFE = "LIVE CUT | move or rotate this Empty"
CUTTER = "LIVE CUT | Boolean subtraction volume (hidden in render)"
DIAGNOSTIC_COUNTS = {
    "V3 | 28-sag0.25 | CARRIERS": 28,
    "V4 | hook0.85 | BRANCHES": 539,
    "V2 | 539 seed positions and branch endpoints": 539,
}
ATLAS = "LIVE | ORIGINAL V0 native RGB volume atlas (150^3)"
REST = "Strawberry | PR29 rest space"
BODY = "Receptacle | canonical PR29 hull"
SCENE = "Strawberry | live exterior and cut"
DIAGNOSTICS = "Diagnostics | original paths and 539 markers"
WARNING = "539 diagnostic anchors != 264 exterior achenes. They are not biologically matched."
SCENE_FILE = "strawberry-integration.blend"
WHOLE_POSE = (-1.6, 0.0, 0.0)
CUT_POSE = (-0.10, 0.0, -23.0)


def script_args():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def sha256(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def check_source(path):
    digest = sha256(path)
    if digest != SOURCE_SHA256:
        raise ValueError(f"Expected the verified PR29 source .blend, got SHA-256 {digest} for {path}")


def pose_knife(knife, pose):
    offset, tilt, turn = pose
    knife.location = (0.0, offset, 0.0)
    knife.rotation_euler = (radians(tilt), 0.0, radians(turn))
