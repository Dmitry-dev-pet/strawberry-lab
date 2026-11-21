"""Run the original one-frame renderer with the runtime stored in the selected scene."""

from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_tissue_zones import TEXT, activate_runtime

import render_exact_cut

activate_pr32 = render_exact_cut.activate_runtime


def activate_selected_runtime():
    return activate_runtime() if TEXT in bpy.data.texts else activate_pr32()


if __name__ == "__main__":
    render_exact_cut.activate_runtime = activate_selected_runtime
    render_exact_cut.main()
