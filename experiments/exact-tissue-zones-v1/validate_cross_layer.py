"""Reuse PR32's actual cross-layer render test with the new embedded runtime."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_tissue_zones import activate_runtime

import validate_cross_layer_render

if __name__ == "__main__":
    validate_cross_layer_render.activate_runtime = activate_runtime
    validate_cross_layer_render.main()
