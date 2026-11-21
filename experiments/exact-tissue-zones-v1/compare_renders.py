"""Verify matched render settings and compare clay granularity in fixed interior crops."""

import argparse
from hashlib import file_digest
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

PAIRS = (
    ("saved-beauty", "Saved pose / original color and studio"),
    ("saved-clay", "Saved pose / uniform clay"),
    ("oblique-clay", "Oblique cut / uniform clay"),
)
VERSIONS = (("pr32", "PR32 Exact"), ("zones", "Tissue Zones Exact"))
ROIS = {
    "saved-clay": {"cortex": (167, 176, 228, 272), "pith": (309, 176, 331, 272)},
    "oblique-clay": {"cortex": (168, 238, 225, 341), "pith": (305, 238, 327, 341)},
}
SETTINGS = ("quality", "look", "pose_y_xrot_zrot", "evaluated_pose_y_xrot_zrot", "view_layer",
            "resolution", "samples", "cycles_seed", "threads", "camera_world", "camera_ortho_scale", "lights")
PR32_SHA256 = "c6d39d20e90f75826167a5b4345752ef874d62641e0ff428f38a68050ec7da3c"


def validate_frame_binding(receipt, version, flavor, scene_hashes):
    """Bind evidence to its source and requested comparison slot, not just its partner."""
    assert receipt["scene_sha256"] == scene_hashes[version], (version, "scene_sha256")
    assert receipt["look"] == ("beauty" if flavor == "saved-beauty" else "clay"), (flavor, "look")
    expected_pose = (.08, 29, 32) if flavor == "oblique-clay" else (-.1, 0, -23)
    for key in ("pose_y_xrot_zrot", "evaluated_pose_y_xrot_zrot"):
        assert len(receipt[key]) == 3
        assert all(abs(a - b) < 1e-4 for a, b in zip(receipt[key], expected_pose, strict=True)), (flavor, key)
    assert receipt["view_layer"] == "MATCHED"
    assert receipt["cycles_seed"] == 1729


def rms(values):
    return float(np.sqrt(np.mean(np.square(values))))


def texture_metrics(image, box):
    # Filter the full frame before selecting the region to avoid crop-boundary artifacts.
    luminance = image.convert("L")
    original = np.asarray(luminance, dtype=float)
    lowpass = np.asarray(luminance.filter(ImageFilter.GaussianBlur(2.5)), dtype=float)
    x0, y0, x1, y1 = box
    region = np.s_[y0:y1, x0:x1]
    return {"pixels": (y1 - y0)*(x1 - x0),
            "high_pass_luminance_rms_8bit": rms((original - lowpass)[region]),
            "horizontal_gradient_rms_8bit_per_px": rms(np.diff(original[region], axis=1)),
            "vertical_gradient_rms_8bit_per_px": rms(np.diff(original[region], axis=0))}


def load_render(root, key, flavor):
    path = root / f"{key}-{flavor}.png"
    receipt = json.loads(path.with_suffix(".json").read_text())
    with path.open("rb") as stream:
        assert file_digest(stream, "sha256").hexdigest() == receipt["png_sha256"]
    with Image.open(path) as src:
        image = src.convert("RGB")
    assert image.size == tuple(receipt["resolution"]) == (650, 650)
    assert receipt["quality"] == "exact" and receipt["samples"] == 16 and receipt["threads"] == 4
    assert receipt["exact"]["cap"]
    return image, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renders", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--build-report", type=Path,
                        help="Defaults to build-report.json beside the renders directory")
    args = parser.parse_args()
    report_path = args.out / "render-qa.json"
    sheet_path = args.out / "comparison.png"
    if report_path.exists() or sheet_path.exists():
        raise FileExistsError("Use a fresh comparison destination")
    build = json.loads((args.build_report or args.renders.parent / "build-report.json").read_text())
    assert build["source_sha256"] == PR32_SHA256
    scene_hashes = {"pr32": PR32_SHA256, "zones": build["scene_sha256"]}
    assert scene_hashes["zones"] != scene_hashes["pr32"]
    images = {}
    rows = {}
    for flavor, _ in PAIRS:
        pair = [load_render(args.renders, key, flavor) for key, _ in VERSIONS]
        for (version, _), (_, receipt) in zip(VERSIONS, pair, strict=True):
            validate_frame_binding(receipt, version, flavor, scene_hashes)
        assert all(pair[0][1][key] == pair[1][1][key] for key in SETTINGS)
        images[flavor] = [image for image, _ in pair]
        frames = {key: receipt for (key, _), (_, receipt) in zip(VERSIONS, pair, strict=True)}
        regions = {zone: {"box_xyxy": box, **{
            key: texture_metrics(image, box) for (key, _), (image, _) in zip(VERSIONS, pair, strict=True)
        }} for zone, box in ROIS.get(flavor, {}).items()}
        for zone, data in regions.items():
            a, b = (data[version]["high_pass_luminance_rms_8bit"] for version, _ in VERSIONS)
            data["rms_ratio_zones_to_pr32"] = b/a
            assert 0 < b/a < (.47 if zone == "pith" else .90), data
        if regions:
            assert regions["pith"]["rms_ratio_zones_to_pr32"] < regions["cortex"]["rms_ratio_zones_to_pr32"]
        rows[flavor] = {"frames": frames, "interior_rectangles": regions}
    report_path.write_text(json.dumps({"status": "PASS", "paired_settings_identical": True,
                                      "source_and_slot_binding_verified": True,
                                      "expected_scene_sha256": scene_hashes, "pairs": rows},
                                      indent=2) + "\n")
    board = Image.new("RGB", (1056, 2000), "#22262a")
    draw = ImageDraw.Draw(board)
    title, caption, label = (ImageFont.load_default(size=n) for n in (30, 20, 17))
    draw.text((24, 13), "Strawberry cut relief", fill="white", font=title)
    for col, (_, name) in enumerate(VERSIONS):
        draw.text((24 + 520*col, 55), name, fill="white", font=caption)
    for row, (flavor, name) in enumerate(PAIRS):
        y = 92 + row*510
        draw.text((24, y), name, fill="#e2e6eb", font=caption)
        for col, image in enumerate(images[flavor]):
            frame = image.copy()
            overlay = ImageDraw.Draw(frame)
            for zone, box in ROIS.get(flavor, {}).items():
                overlay.rectangle(box, outline="#f9ad66" if zone == "cortex" else "#83ccfc", width=2)
            board.paste(frame.resize((468, 468), Image.Resampling.LANCZOS), (24 + 520*col, y + 29))
    y = 1630
    draw.text((24, y), "Saved clay crops at 2.5x", fill="#e2e6eb", font=caption)
    for col, image in enumerate(images["saved-clay"]):
        x = 24 + 520*col
        for zone, box in ROIS["saved-clay"].items():
            color = "#f9ad66" if zone == "cortex" else "#83ccfc"
            center = (box[0] + box[2])//2
            crop = image.crop((center-40, box[1]-5, center+40, box[3]+5))
            crop = crop.resize((200, 265), Image.Resampling.BICUBIC)
            draw.text((x, y + 33), zone.capitalize(), fill=color, font=label)
            board.paste(ImageOps.expand(crop, border=1, fill=color), (x, y+60))
            x += 228
    board.save(sheet_path)


if __name__ == "__main__":
    main()
