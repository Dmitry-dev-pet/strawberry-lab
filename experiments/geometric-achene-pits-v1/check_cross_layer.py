"""Render one cross-layer Exact candidate/control in a fresh Blender process."""
import argparse
import json
from pathlib import Path
import resource
import sys
from time import perf_counter

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / name) for name in ("exact-tissue-zones-v1", "integration-exact-cut-v1")]
from build_tissue_zones import activate_runtime
import validate_cross_layer_render as cross_layer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("layer", choices=("MATCHED", "FLESH ONLY"))
    parser.add_argument("case", choices=("candidate", "control"))
    parser.add_argument("png", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    path = args.png.resolve()
    assert not path.exists() and not path.with_suffix(".json").exists()
    cross_layer.activate_runtime = activate_runtime
    started = perf_counter()
    _, receipt = cross_layer.render(args.scene.resolve(), path, args.layer, args.case == "candidate")
    receipt.update(layer=args.layer, case=args.case, source_sha256=cross_layer.sha256(args.scene),
                   elapsed_seconds=perf_counter() - started,
                   peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    path.with_suffix(".json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(receipt, flush=True)


if __name__ == "__main__":
    main()
