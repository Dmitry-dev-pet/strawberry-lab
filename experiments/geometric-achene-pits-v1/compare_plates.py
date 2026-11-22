"""Check render pairing and create the labeled comparison sheet."""
import argparse
from hashlib import file_digest
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FRAMES = (("whole", "Whole fruit"), ("macro", "Achene macro"), ("clay", "Clay macro · bump off"))
SETTINGS = ("frame", "resolution", "view_layer", "samples", "seed", "threads", "denoise",
            "camera_matrix", "ortho_scale", "macro_anchor", "macro_anchor_centers_in_frame",
            "clay_override_and_all_bumps_muted", "lights")


def sha(path):
    with path.open("rb") as src:
        return file_digest(src, "sha256").hexdigest()


def read_plate(path, input_sha, expected_frame=None):
    receipt = json.loads(path.with_suffix(".json").read_text())
    assert sha(path) == receipt["png_sha256"] and receipt["source_sha256"] == input_sha
    if expected_frame is not None:
        assert receipt["frame"] == expected_frame, (expected_frame, receipt["frame"])
    with Image.open(path) as src:
        assert src.format == "PNG" and src.size == (1000, 1000)
        return src.convert("RGB"), receipt


def cross_layer(root, input_sha):
    outputs = {}
    for layer in ("matched", "flesh-only"):
        images, receipts = [], {}
        for case in ("candidate", "control"):
            path = root / f"{layer}-{case}.png"
            receipt = json.loads(path.with_suffix(".json").read_text())
            assert sha(path) == receipt["sha256"] and receipt["source_sha256"] == input_sha
            assert receipt["layer"].lower().replace(" ", "-") == layer and receipt["case"] == case
            receipts[case] = receipt
            with Image.open(path) as image:
                images.append(np.array(image.convert("RGBA")))
        assert np.array_equal(*images), layer
        assert receipts["candidate"]["refresh_count"] > receipts["control"]["refresh_count"]
        outputs[layer] = {"decoded_pixels_identical": True, **receipts}
    return outputs


def build(root, baseline, pitted):
    baseline_sha, scene_sha = sha(baseline), sha(pitted)
    frames = root / "renders"
    output = root / "comparison.png"
    receipt = root / "render-validation.json"
    assert not output.exists() and not receipt.exists()
    sheet = Image.new("RGB", (1592, 1106), (24, 22, 23))
    draw = ImageDraw.Draw(sheet)
    title = ImageFont.load_default(size=24)
    legend = ImageFont.load_default(size=18)
    report = {}
    for j, (kind, label) in enumerate(FRAMES):
        left = 20 + j * 524
        draw.text((left, 12), label, fill=(245, 241, 238), font=title)
        images, records = [], []
        for i, (scene, source_sha, caption) in enumerate((
                ("baseline", baseline_sha, "PR33 baseline"),
                ("pitted", scene_sha, "Smaller geometric pits / seated"))):
            img, record = read_plate(frames / f"{scene}-{kind}.png", source_sha, kind)
            assert record["clay_override_and_all_bumps_muted"] == (kind == "clay")
            images.append(img)
            records.append(record)
            top = 42 + i * 532
            sheet.paste(img.resize((508, 508), Image.Resampling.LANCZOS), (left, top + 24))
            draw.text((left, top + 1), caption, fill=(211, 204, 201), font=legend)
        assert all(records[0][name] == records[1][name] for name in SETTINGS), kind
        delta = np.asarray(images[0], dtype=np.float64) - np.asarray(images[1], dtype=np.float64)
        assert np.any(delta), kind
        report[kind] = {"settings_equal": True, "pixel_rgb_rms_8bit": float(np.sqrt(np.mean(delta**2))),
                        "baseline_render": records[0], "pitted_render": records[1]}
    cross = cross_layer(root / "cross-layer", scene_sha)
    sheet.save(output)
    receipt.write_text(json.dumps({"status": "PASS", "frames": report, "cross_layer": cross,
                                   "comparison_sha256": sha(output)}, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("root", "baseline", "pitted"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    build(args.root, args.baseline, args.pitted)
