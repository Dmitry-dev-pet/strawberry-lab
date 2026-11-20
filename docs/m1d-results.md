# Strawberry Lab M1d — live cutter-controlled achenes (20 November 2026)

**Status: implemented, saved, and validated in Blender 5.2.4 LTS. This resolves the M1c limitation where achene positions were clipped once in Python at generation time.**

## Architecture

In M1c, the original 539 achene anchor points had been replaced by a permanently truncated list (266 for the half-cut or 478 for the spherical cutter). Manually moving the cutter in Blender modified the SDF fruit body but could not restore deleted seeds.

M1d starts by restoring the **original full 539-point mesh** from the separately stored, editable M1a whole-fruit scene (including each point's `seed_euler` and `seed_size` attributes). It keeps the M1c body and cut shader intact.

It clones the existing seed-instancing Geometry Nodes group and wires this field evaluation **before** `Instance on Points`:

```text
SAME EDITABLE CUTTER OBJECT as the fruit-body SDF Boolean
  Object Info (RELATIVE)
    → Mesh to SDF Grid (voxel 0.023, signed distance)
    → Sample Grid at anchor Position
    → Compare (distance < -0.55 × voxel)
    → Delete Geometry (point-domain)
           ↑
    Original 539 seed anchors (mesh, seed_euler, seed_size)
           ↓
    Instance on Points → Realize Instances → Group Output
```

The point mask automatically recomputes when the cutter moves. There is **no per-frame Python filtering** or seed deletion after construction. A small hidden diagnostic object runs an independent copy of the SDF point filter so a validator can measure the actual surviving anchor count rather than infer it from the render.

Each saved `.blend` has keyframed cutter positions on frames **1 and 30**, with an intermediate test on frame 15. Opening the file and scrubbing the timeline updates both seed count and fruit-body geometry. The body’s own M1c SDF Geometry Nodes remains untouched.

## Three-pose validation after reopening each actual .blend

Blender CLI: `blender -b <file>.blend --python src/validate_live_cut.py`.

| Mode | Frame | Surviving seeds (of 539) | SDF body vertices | Non-manifold SDF edges |
| --- | ---: | ---: | ---: | ---: |
| Tilted half cut | 1 | 273 | 28,976 | **0** |
| Tilted half cut | 15 | 176 | 21,034 | **0** |
| Tilted half cut | 30 | 84 | 10,078 | **0** |
| Spherical bite | 1 | 481 | 30,892 | **0** |
| Spherical bite | 15 | 453 | 33,614 | **0** |
| Spherical bite | 30 | 539 | 44,474 | **0** |

Seed mesh vertex count is independently validated to equal **surviving anchors × 168** (the unchanged M1a achene prototype). Each test confirms that both GN groups reference the exact same cutter Blender object. **6/6 frame checks PASS, 2/2 saved scenes PASS.** The sphere moving fully within the fruit at frame 30 leaves a closed internal cavity, but has no visible surface bite; the skin is externally restored.

## Actual Cycles renders and GLB

- Four real, unedited Blender Cycles PNG, frame 1 and frame 30 for both cutters; comparison sheet is a layout of those exact four images.
- Two editable Blender scenes: `strawberry-m1d-half.blend` and `strawberry-m1d-bite.blend`.
- Four GLB **static geometry snapshots** of the original evaluated frame:
  - half frame 01 — 142,032 triangles; half frame 30 — 46,020 triangles.
  - bite frame 01 — 209,928 triangles; bite frame 30 — 254,952 triangles.
  - GLB parsed by `trimesh`; distinct frames have different SHA-256 and triangle counts.
- **Important exporter issue found and fixed**: calling Blender glTF export with `export_apply=True` on the original GN objects yielded identical frame 1 and frame 30 files, ignoring the evaluated pose. `src/export_pose_glb.py` now explicitly creates temporary meshes using `bpy.data.meshes.new_from_object(evaluated, depsgraph=...)` and exports these baked objects, with achene-count assertions. The Blender .blend is still the only **animated and editable** source.

## Source and reproducing the tests

```bash
# Fetch the stored M1c cut scene and the full M1a whole scene using
# the previous versioned manifests, or rebuild them from public code.
blender -b --python src/live_achene_mask.py -- \
  --scene /path/to/strawberry-m1c-half.blend \
  --anchors-from /path/to/strawberry-m1a-whole.blend \
  --out build/m1d --voxel 0.023 --no-render --no-glb

blender -b build/m1d/strawberry-m1d-half.blend --python src/validate_live_cut.py
blender -b build/m1d/strawberry-m1d-half.blend --python src/render_pose.py -- \
  --frame 30 --out build/m1d --resolution 720 --samples 18
blender -b build/m1d/strawberry-m1d-half.blend --python src/export_pose_glb.py -- \
  --frame 30 --out build/m1d
```

For the sphere, pass the M1c `bite.blend` scene instead of `half.blend`.

Public code: [live_achene_mask.py](../src/live_achene_mask.py), [validate_live_cut.py](../src/validate_live_cut.py), [render_pose.py](../src/render_pose.py), [export_pose_glb.py](../src/export_pose_glb.py).

Private owner storage: [Google Drive / v0.5-m1d-live-achenes](https://drive.google.com/drive/folders/1x4TCZEZM8LEzsK8BFBB0TtHBXTGnWj1m). The [manifest](../assets/manifest-m1d.json) lists **17 finished binary/report artifacts (40.76 MB)**; every file was downloaded back after upload and verified against the original full SHA-256 **17/17 PASS**. Earlier v0.1–M1c versions remain unchanged.

## What is still missing

1. **Seed/cut-edge physical intersection**: the current mask tests an achene's **centre point** against cutter SDF, not the entire actual achene geometry. Seeds near the boundary can still protrude into a cut; later perform per-instance SDF erosion by achene radius or exact seed-solid intersection/culling.
2. **Other attachments** (calyx, stem, possible hairs) are not yet dynamically cut; with extreme half-cuts they may look detached.
3. **Photoreal tissue quality remains below Frucht.** The SDF interior still looks too smooth; neither actual cellular histology nor realistic wet pores, intercellular cavities and vessel cross-sections have been calibrated.
4. **GLB exports are static**, and do not retain Blender Geometry Nodes, cutter animation or the full procedural Cycles rest-space shader. Matching browser appearance requires separate PBR material baking.
5. Some Blender file metadata is not byte-deterministic on rebuild. Provenance is secured by the SHA-256 of the saved Drive artifacts, not by promising a clean rebuild will be binary-identical.

This is an independently developed Strawberry Lab test; the closed commercial Frucht strawberry node tree was not used.

See [Issue #8](https://github.com/Dmitry-dev-pet/strawberry-lab/issues/8) and [Frucht technique audit](frucht-architecture-audit.md).
