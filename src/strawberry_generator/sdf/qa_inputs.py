"""Input contract for independent, layout-agnostic Blender SDF scene QA.

This module deliberately imports no Blender API so the input checks can be
exercised before opening and evaluating a potentially expensive .blend scene.
"""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path


def parse_qa_inputs(argv, expected_source_sha256):
    parser = ArgumentParser(description="Verify a saved SDF scene against an independently pinned source .blend")
    parser.add_argument("scene", type=Path, help="Saved native SDF .blend to evaluate")
    parser.add_argument("out", type=Path, help="New JSON QA receipt path")
    parser.add_argument("--source", type=Path, required=True, help="Pinned original PR40 seed101 .blend")
    args = parser.parse_args(argv)
    scene = args.scene.expanduser().resolve()
    source = args.source.expanduser().resolve()
    out = args.out.expanduser().resolve()
    if not scene.is_file():
        raise FileNotFoundError(f"SDF scene not found: {scene}")
    if not source.is_file():
        raise FileNotFoundError(f"Pinned original PR40 scene not found: {source}")
    if source == scene:
        raise ValueError("The SDF scene and the independent PR40 source must be different files")
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite existing QA receipt: {out}")
    actual = sha256(source.read_bytes()).hexdigest()
    if actual != expected_source_sha256:
        raise ValueError(f"Source scene SHA-256 mismatch: got {actual}, expected {expected_source_sha256}")
    return scene, out, source
