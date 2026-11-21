"""Build a scripts-disabled-safe tissue-zones scene from authenticated PR32."""

import argparse
from hashlib import sha256 as hash_bytes
import json
from pathlib import Path
import sys
from time import perf_counter

import bpy

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "integration-exact-cut-v1"
sys.path[:0] = [str(HERE), str(PREVIOUS)]
from build_exact_cut import GUIDE_TEXT, RUNTIME, TEXT as PRIOR_TEXT, runtime_source as prior_runtime_source
from integration import BODY, SCENE, script_args, sha256
from tissue_field import CONTROLS

PR32_SHA256 = "c6d39d20e90f75826167a5b4345752ef874d62641e0ff428f38a68050ec7da3c"
TEXT = "TISSUE_ZONES__RUN.py"
SCENE_FILE = "strawberry-tissue-zones.blend"


def replace(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Expected one PR32 source anchor: {old[:95]!r}")
    return source.replace(old, new, 1)


def runtime_source():
    cap = (PREVIOUS / "cap_geometry.py").read_text()
    cap = replace(cap, "from mathutils.noise import noise, voronoi\n", "")
    cap = replace(cap, "STRAND_FALLOFF_MM = 0.65\n", "")
    cap = replace(cap, "mm_per_unit, settings, strands):", "mm_per_unit, settings, strands, atlas):")
    cap = replace(cap, "        height_mm, strand_influence = settings\n", "")
    start = cap.index("            # Coherent rest-space cellular ridges")
    end = cap.index("            vertex.co += height * outward", start)
    cap = cap[:start] + """            components = tissue_components(rest, mm, atlas, strands)
            requested_mm = sum(strength*value for strength, value in zip(settings, components, strict=True))
            distance = boundary.distance(vertex.co, fade)
            height = min(requested_mm / mm, 0.45 * distance) * smoothstep(distance / fade)
""" + cap[end:]

    runtime = (PREVIOUS / "exact_runtime.py").read_text()
    runtime = replace(runtime, f'TEXT = "{PRIOR_TEXT}"', f'TEXT = "{TEXT}"')
    start = runtime.index("HEIGHT = ")
    end = runtime.index("TEXT = ", start)
    runtime = runtime[:start] + runtime[end:]
    start = runtime.index("        settings = (")
    end = runtime.index("        strand_key = ", start)
    runtime = runtime[:start] + """        settings = tuple(float(scene[key]) for key, _, _, _ in CONTROLS)
        if not (scale > 0 and all(0 <= value <= control[3]
                                  for value, control in zip(settings, CONTROLS, strict=True))):
            raise ValueError("Invalid scene scale or Exact tissue relief settings")
""" + runtime[end:]
    runtime = replace(runtime, "        self.strands = None\n", "        self.strands = None\n        self.atlas = None\n")
    runtime = replace(runtime, "        self.key = self.strand_key = self.strands = None",
                      "        self.key = self.strand_key = self.strands = self.atlas = None")
    runtime = replace(runtime, "if self.strand_key != key[3] and all(settings):",
                      "if self.strand_key != key[3] and settings[2]:")
    runtime = replace(runtime, "            mesh, stats = make_mesh(base, to_knife, to_rest, scale, settings, self.strands)",
        """            if self.atlas is None:
                self.atlas = TissueAtlas(bpy.data.images[ATLAS])
            strands = self.strands if settings[2] else None
            mesh, stats = make_mesh(base, to_knife, to_rest, scale, settings, strands, self.atlas)""")
    runtime = replace(runtime, '            layout.prop(context.scene, HEIGHT_CONTROL)\n'
                      '            layout.prop(context.scene, INFLUENCE_CONTROL, slider=True)',
                      '            for key, _, _, _ in CONTROLS:\n'
                      '                layout.prop(context.scene, key + "_control", slider=True)')
    runtime = replace(runtime, "    for name in (HEIGHT_CONTROL, INFLUENCE_CONTROL):",
                      '    for name in (key + "_control" for key, _, _, _ in CONTROLS):')
    start = runtime.index("    setattr(bpy.types.Scene, HEIGHT_CONTROL")
    end = runtime.index("    for name, handler in HANDLERS.items()", start)
    runtime = runtime[:start] + """    def accessors(key):
        def get(scene):
            return scene[key]

        def set_value(scene, value):
            scene[key] = value

        return get, set_value

    for key, label, default, maximum in CONTROLS:
        get, set_value = accessors(key)
        setattr(bpy.types.Scene, key + "_control", bpy.props.FloatProperty(
            name=label, min=0.0, max=maximum, default=default, precision=3,
            get=get, set=set_value,
            update=on_setting))
""" + runtime[end:]
    return "\n\n".join((cap, (HERE / "atlas.py").read_text(), (HERE / "tissue_field.py").read_text(), runtime))


def activate_runtime():
    text = bpy.data.texts[TEXT]
    exec(compile(text.as_string(), text.name, "exec"), {"__name__": "__main__"})
    return bpy.app.driver_namespace[RUNTIME]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(script_args())
    started = perf_counter()
    path = args.out.resolve() / SCENE_FILE
    receipt = path.with_name("build-report.json")
    if path.exists() or receipt.exists():
        raise FileExistsError("Use a fresh scene output path")
    source = args.source.resolve()
    if sha256(source) != PR32_SHA256:
        raise ValueError("Expected authenticated PR32")
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
    scene = bpy.context.scene
    assert scene.name == SCENE and bpy.data.texts[PRIOR_TEXT].as_string() == prior_runtime_source()
    bpy.data.texts.remove(bpy.data.texts[PRIOR_TEXT])
    for key in ("strawberry_exact_height_mm", "strawberry_exact_strand_influence"):
        del scene[key]
    for key, label, value, maximum in CONTROLS:
        scene[key] = value
        scene.id_properties_ui(key).update(min=0.0, max=maximum, default=value, description="ARTIST " + label)
    text = bpy.data.texts.new(TEXT)
    text.use_fake_user = True
    source_code = runtime_source()
    compile(source_code, TEXT, "exec")
    text.write(source_code)
    guide = bpy.data.texts[GUIDE_TEXT]
    prefix, heading, _ = guide.as_string().partition("\nEXACT CUT\n")
    assert heading
    guide.clear()
    guide.write(prefix + """
EXACT TISSUE ZONES

Open Scripting, select TISSUE_ZONES__RUN.py in the Text Editor, and click Run Script.
In the 3D View use N > Strawberry Cut > Exact in MATCHED or FLESH ONLY.
Move the shared knife or adjust Cortex, Pith and Vascular relief in the panel.
The sliders control independent ARTIST displacement contributions in millimetres.
Exact rebuilds on the CPU. Saving restores native Fast and preserves the sliders.
Run the Text again after reopening. Disable Exact Runtime removes its panel.
""")
    for screen in bpy.data.screens:
        for area in screen.areas:
            for space in area.spaces:
                if space.type == "TEXT_EDITOR":
                    space.text = text
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    report = {
        "blender": bpy.app.version_string, "source_sha256": PR32_SHA256, "scene_sha256": sha256(path),
        "runtime_sha256": hash_bytes(source_code.encode()).hexdigest(),
        "scene_bytes": path.stat().st_size, "objects": len(scene.objects),
        "body_vertices": len(scene.objects[BODY].data.vertices), "view_layers": list(scene.view_layers.keys()),
        "defaults_mm": {label: value for _, label, value, _ in CONTROLS},
        "build_seconds": perf_counter() - started,
    }
    receipt.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
