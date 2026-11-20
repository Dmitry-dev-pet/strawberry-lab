#!/usr/bin/env python3
"""Verify a Strawberry Lab Drive snapshot downloaded into one directory.

Only standard library. Input files are never executed. Checks size, SHA-256,
PNG dimensions, GLB 2 header/length and .blend file signature.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys


def check_manifest(manifest: dict, folder: Path) -> dict:
    if manifest.get("schema_version") != "strawberry-lab-assets-v1":
        raise ValueError("Unsupported asset manifest schema")
    results = {"verified": [], "errors": []}
    seen = set()
    for a in manifest.get("files", []):
        name = a.get("name")
        if not isinstance(name, str) or Path(name).name != name or name in (".", "..") or name in seen:
            raise ValueError(f"Invalid or duplicate asset filename: {name!r}")
        seen.add(name)
        p = folder / name
        if not p.is_file() or p.is_symlink():
            results["errors"].append(f"{name}: missing or not a regular file")
            continue
        size = p.stat().st_size
        if size != a.get("size_bytes"):
            results["errors"].append(f"{name}: size mismatch: {size} != {a.get('size_bytes')}")
            continue
        with p.open("rb") as f:
            digest = hashlib.file_digest(f, "sha256").hexdigest()
        if digest != a.get("sha256"):
            results["errors"].append(f"{name}: SHA-256 mismatch")
            continue
        with p.open("rb") as f:
            header = f.read(32)
        if p.suffix == ".glb":
            if len(header) < 12 or header[:4] != b"glTF" or struct.unpack_from("<II", header, 4) != (2, size):
                results["errors"].append(f"{name}: invalid GLB 2 header or length")
                continue
        if p.suffix == ".blend" and not (header[:7] == b"BLENDER" or header[:4] == b"\x28\xb5\x2f\xfd"):
            results["errors"].append(f"{name}: unrecognized Blender or Zstandard-compressed Blender header")
            continue
        if p.suffix == ".png":
            if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
                results["errors"].append(f"{name}: invalid PNG header")
                continue
            wh = list(struct.unpack_from(">II", header, 16))
            if a.get("pixel_dimensions") and wh != a["pixel_dimensions"]:
                results["errors"].append(f"{name}: PNG resolution mismatch: {wh}")
                continue
        results["verified"].append(name)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("directory", type=Path)
    ns = parser.parse_args(argv)
    m = json.loads(ns.manifest.read_text(encoding="utf-8"))
    result = check_manifest(m, ns.directory)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
