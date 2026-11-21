"""Verify paired render settings and summarize differences in the resulting pixels."""

import argparse
from hashlib import file_digest
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageStat

PAIRS = (
    ("beauty", "Packed atlas  /  saved pose"),
    ("clay-saved", "Uniform clay  /  saved pose"),
    ("clay-oblique", "Uniform clay  /  oblique pose"),
)
MATCHED_SETTINGS = ("scene_sha256", "look", "pose_y_xrot_zrot", "view_layer",
                    "evaluated_pose_y_xrot_zrot",
                    "resolution", "samples", "cycles_seed", "threads", "camera_world",
                    "camera_ortho_scale", "lights")


def load_render(folder, name, quality):
    path = folder / f"{name}-{quality}.png"
    receipt = json.loads(path.with_suffix(".json").read_text())
    assert receipt["quality"] == quality
    with path.open("rb") as stream:
        assert file_digest(stream, "sha256").hexdigest() == receipt["png_sha256"]
    with Image.open(path) as image:
        assert image.format == "PNG" and image.size == (650, 650)
        return image.convert("RGB"), receipt


def pixel_stats(fast, exact):
    channels = ImageChops.difference(fast, exact).split()
    largest = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
    hist = largest.histogram()
    return {"changed_pixels_over_8_rgb_levels": sum(hist[9:]),
            "fraction_over_8_rgb_levels": sum(hist[9:]) / sum(hist),
            "mean_max_channel_difference": ImageStat.Stat(largest).mean[0]}


def local_contrast(image):
    gray = image.convert("L")
    return ImageStat.Stat(ImageChops.difference(gray, gray.filter(ImageFilter.GaussianBlur(3)))).mean[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renders", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    contact_sheet = args.out.with_name("comparison.png")
    if args.out.exists() or contact_sheet.exists():
        raise FileExistsError("Use fresh report and comparison paths")
    tile = 410
    sheet = Image.new("RGB", (2 * tile + 30, 3 * (tile + 44) + 10), "#1d2228")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=20)
    report = {}
    for row, (name, label) in enumerate(PAIRS):
        fast, a = load_render(args.renders, name, "fast")
        exact, b = load_render(args.renders, name, "exact")
        expected_look = "beauty" if name == "beauty" else "clay"
        expected_pose = (0.08, 29, 32) if name == "clay-oblique" else (-0.1, 0, -23)
        for receipt in (a, b):
            assert receipt["look"] == expected_look, f"Unexpected look in {name}"
            assert receipt["view_layer"] == "MATCHED"
            for key in ("pose_y_xrot_zrot", "evaluated_pose_y_xrot_zrot"):
                assert len(receipt[key]) == 3
                assert all(abs(x - y) < 1e-4 for x, y in zip(receipt[key], expected_pose, strict=True)), (name, key)
        assert all(a[key] == b[key] for key in MATCHED_SETTINGS)
        assert a["exact"] is None and b["exact"]["max_displacement_mm"] > 0.05
        whole = pixel_stats(fast, exact)
        assert whole["fraction_over_8_rgb_levels"] > 0.01
        item = {"whole_frame": whole, "render_seconds": [a["render_seconds"], b["render_seconds"]]}
        if a["look"] == "clay":
            # This shared rectangle is inside the visible cut in both clay poses.
            box = (245, 220, 405, 405)
            fast_crop, exact_crop = fast.crop(box), exact.crop(box)
            fast_contrast, exact_contrast = local_contrast(fast_crop), local_contrast(exact_crop)
            assert exact_contrast > 2 * fast_contrast
            item["cap_crop"] = {
                "box": box, "pixels": pixel_stats(fast_crop, exact_crop),
                "local_luma_contrast_fast": fast_contrast, "local_luma_contrast_exact": exact_contrast,
            }
        report[name] = item
        for column, (quality, image) in enumerate((("Fast", fast), ("Exact", exact))):
            x, y = 10 + column * (tile + 10), 10 + row * (tile + 44)
            draw.text((x + 3, y + 4), f"{label}  ·  {quality}", fill="#e7eaee", font=font)
            sheet.paste(image.resize((tile, tile), Image.Resampling.LANCZOS), (x, y + 30))
    with args.out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    sheet.save(contact_sheet)


if __name__ == "__main__":
    main()
