# Strawberry Lab — Volume First v1: continuous thin 3D fibers

**Status:** experimental visual research, Blender 5.2.4 LTS, **not** commercial Frucht and **not** measured strawberry histology.

This milestone tests **one question**: can fine 3D source filaments produce clearly visible *geometric* cut relief on more than one oriented section while preserving the fruit skin and watertight geometry? The result answers **yes for geometric continuity**, but photographic fidelity still **fails**: long pale lines look too rigid and stylized.

## Contents and reproducibility

- `input-v0/strawberry-volumetric-3cut.blend` — prior unchanged Volume First v0 scene.
- `input-v0/fibers_3d.npz`, `input-v0/tissue_3d.npz` — previous v0 3D source data; neither is a cut-specific 2D texture.
- `outputs/fine_fibers_3d.npz` — **494 spatial polylines**, including the original 146 plus 348 independently generated fine lines, 45,928 points. One source for all angles.
- `outputs/strawberry-volume-first-v1.blend` — stronger diagnostic fiber/color geometry; all three cut mesh objects plus v0 objects and hidden actual 3D source curve.
- `outputs/strawberry-volume-first-v1-beauty.blend` — more restrained physical relief and material; intended main experiment.
- `outputs/beauty-000.png`, `beauty-032.png`, `beauty-082.png` — real Blender CPU Cycles full-frame renders (840×960, 20 samples; identical camera/lights).
- `outputs/comparison-full-0-and-82.jpg` — v0/v1 A/B at 0° and 82°.
- `outputs/macro-clay-ab.jpg` — close-up with original materials and with uniform clay. Uniform clay shows that fine ridges exist in actual mesh geometry, not only bump or color.
- `outputs/v1-three-angles.jpg`, validation/repro JSON, and relevant logs.

## Commands

Standard Python with NumPy and SciPy is required only to **generate the 3D source curves**. Blender includes NumPy; its built-in `mathutils.kdtree.KDTree` handles the 3D source sampling without SciPy. The optional SciPy acceleration is used if already installed in the Blender Python environment.

```bash
python3 generate_fine_fibers.py
blender -b input-v0/strawberry-volumetric-3cut.blend -t 4 --python build_fiber_relief.py -- \
  --out outputs/strawberry-volume-first-v1.blend
blender -b outputs/strawberry-volume-first-v1.blend -t 4 --python tune_beauty.py -- \
  outputs/strawberry-volume-first-v1-beauty.blend
blender -b outputs/strawberry-volume-first-v1-beauty.blend -t 4 --python validate_v1.py
blender -b outputs/strawberry-volume-first-v1-beauty.blend -t 4 --python render_v1.py -- \
  --angle 82 --mode fine --out outputs/beauty-082.png
```

The Blender scene includes three separate **static** half-fruit cut meshes for 0°, 32°, and 82° plus the original v0 half-fruit meshes; you may show/hide them to compare. The original 3D source curves are stored in the `.blend` (hidden) and `fine_fibers_3d.npz`. To reflect edits to the source curves on the cut surfaces, rerun the build script. This is deliberately **not** a live Boolean cutter or a true histological solid-cell model.

## Geometry checks

| Angle | Vertices | True displaced verts (>0.002 BU) | Max physical displacement | Nonmanifold | Connected components | Skin coordinate change |
|---|---:|---:|---:|---:|---:|---:|
| 0° | 78,626 | 5,418 | 0.007069 | 0 | 1 | 0 |
| 32° | 78,626 | 4,723 | 0.007069 | 0 | 1 | 0 |
| 82° | 78,626 | 4,940 | 0.007068 | 0 | 1 | 0 |

These values are measured from the saved Beauty scene. All cuts retain the same 78,960 polygons with no degenerate faces. We do not claim the absence of all geometric self-intersections, true botanical modeling, Frucht-equivalent wetness or live knife speed.

## Source ownership

All generation code and 3D curves are independently authored for Strawberry Lab; no commercial Frucht Blender file, proprietary nodes, GPL Kiwi code, or private Frucht frames are included.
