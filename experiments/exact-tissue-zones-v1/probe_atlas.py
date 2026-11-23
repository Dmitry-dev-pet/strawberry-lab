"""Inventory the authenticated atlas and independently evaluate the shader UV graph."""

import argparse
from hashlib import sha256
import json
from math import floor
from pathlib import Path
import sys

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from atlas import ATLAS, COLS, LO, N, ROWS, SPAN, TissueAtlas


def shader_sample(tree, image, pixels, point):
    def read(socket):
        return evaluate(socket.links[0].from_socket) if socket.is_linked else socket.default_value

    def evaluate(socket):
        node = socket.node
        if node.name == "PR29 rest coordinates":
            return point
        if node.type == "SEPXYZ":
            return read(node.inputs[0])["XYZ".index(socket.name)]
        if node.type == "COMBXYZ":
            return tuple(read(inp) for inp in node.inputs)
        if node.type == "TEX_IMAGE":
            assert node.image == image and node.interpolation == "Linear" and node.extension == "CLIP"
            u, v, _ = read(node.inputs[0])
            x, y = u * pixels.shape[1] - 0.5, v * pixels.shape[0] - 0.5
            x = min(pixels.shape[1] - 1, max(0, x))
            y = min(pixels.shape[0] - 1, max(0, y))
            i, j = floor(x), floor(y)
            a, b = x - i, y - j
            ii, jj = min(i + 1, pixels.shape[1] - 1), min(j + 1, pixels.shape[0] - 1)
            return ((1-b) * ((1-a) * pixels[j, i] + a * pixels[j, ii])
                    + b * ((1-a) * pixels[jj, i] + a * pixels[jj, ii]))
        if node.type == "MATH":
            a, b = map(read, node.inputs[:2])
            return {
                "MULTIPLY": lambda: a*b, "SUBTRACT": lambda: a-b, "DIVIDE": lambda: a/b,
                "ADD": lambda: a+b, "MINIMUM": lambda: min(a,b), "MAXIMUM": lambda: max(a,b),
                "FLOOR": lambda: floor(a), "FLOORED_MODULO": lambda: a % b,
            }[node.operation]()
        assert node.type == "MIX_RGB" and node.blend_type == "MIX"
        a, bottom, top = map(read, node.inputs)
        return (1-a)*bottom + a*top

    mix, = [node for node in tree.nodes if node.type == "MIX_RGB"]
    return evaluate(mix.outputs[0])


def inventory(scene):
    body = scene.objects["Receptacle | canonical PR29 hull"]
    tree = body.data.materials[1].node_tree
    sep, = [node for node in tree.nodes if node.type == "SEPXYZ"]
    subtracts = [socket.links[0].to_node for socket in sep.outputs]
    divides = [node.outputs[0].links[0].to_node for node in subtracts]
    assert tuple(node.inputs[1].default_value for node in subtracts) == LO
    assert tuple(node.inputs[1].default_value for node in divides) == SPAN
    image = bpy.data.images[ATLAS]
    atlas = TissueAtlas(image)
    pixels = np.empty(N * COLS * N * ROWS * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    pixels = pixels.reshape(N * ROWS, N * COLS, 4)
    xyz = [lo + scale * np.arange(N) / (N - 1) for lo, scale in zip(LO, SPAN, strict=True)]
    x, y, z = xyz[0][None, None, :], xyz[1][None, :, None], xyz[2][:, None, None]
    radius = np.hypot(x - .017*np.sin(6*z), y - .014*np.cos(4*z))
    t = np.clip((z + 1.18) / 2.16, 0, 1)
    hull = np.sin(np.pi*t)**.58 * (.36 + .92*t)
    interior = (z > -1.10) & (z < .90) & (radius < .86*hull)
    base_radius = .090 + .142*np.clip((z+1.14)/2.16, 0, 1)
    bins = [0, .05, .10, .15, .20, .25, .30, .40, .50, .60, .8, 1.01]
    subsets = {
        "all": atlas.rgb.reshape(-1, 3),
        "interior_reference": atlas.rgb[interior],
        "axial_amber_reference": atlas.rgb[interior & (radius < .07) & (abs(z - .2) < .30)],
        "core_reference": atlas.rgb[interior & (radius < .8*base_radius)],
        "boundary_reference": atlas.rgb[interior & (radius > .8*base_radius) & (radius < 1.3*base_radius)],
        "cortex_reference": atlas.rgb[interior & (radius > 1.8*base_radius)],
    }
    summary = {}
    for name, rgb in subsets.items():
        summary[name] = {
            "voxels": len(rgb),
            "percentiles_0_5_25_50_75_95_100": np.percentile(rgb, [0, 5, 25, 50, 75, 95, 100], axis=0).round(5).tolist(),
            "green_histogram": np.histogram(rgb[:, 1], bins=bins)[0].tolist(),
        }
    samples = [(x, 0, z) for z in (-.7, .2, .7) for x in (0, .10, .22, .36, .58)]
    rng = np.random.default_rng(921)
    comparisons = samples + [tuple(p) for p in rng.uniform(LO, np.add(LO, SPAN), (150, 3))]
    comparisons += [(LO[0], LO[1] + SPAN[1], LO[2] + SPAN[2]*k/(N-1)) for k in (0, 14, 15, 29.5, 30, 149)]
    errors = [abs(atlas.sample_green(p) - shader_sample(tree, image, pixels, p)[1]) for p in comparisons]
    assert max(errors) < 1e-5
    return {
        "blender": bpy.app.version_string, "atlas_sha256": sha256(image.packed_file.data).hexdigest(),
        "atlas_pixels": list(image.size), "colorspace": image.colorspace_settings.name,
        "rest_lower": LO, "rest_span": SPAN, "mm_per_rest_unit": scene.unit_settings.scale_length * 1000,
        "green_histogram_edges": bins, "voxel_statistics": summary,
        "rgb_samples": [{"rest": p, "rgb": [float(v) for v in shader_sample(tree, image, pixels, p)[:3]]}
                        for p in samples],
        "shader_graph_comparison_probes": len(errors), "max_green_error": float(max(errors)),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    args.out.write_text(json.dumps(inventory(bpy.context.scene), indent=2) + "\n")
