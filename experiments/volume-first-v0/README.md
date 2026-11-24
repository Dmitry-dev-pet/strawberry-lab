# Strawberry Lab — Volume First v0 (independent 3D source)

**Purpose:** test whether constructing tissue in **three-dimensional space first** gives more coherent sectional appearance than layering texture onto a cut mesh. This is an independent visual research prototype, **not** the author's Frucht strawberry, a proven photoreal reproduction, or measured botanical anatomy.

## What is delivered

- `outputs/tissue_3d.npz` — one deterministic **150³** sample volume (color, height, pith, discrete-fiber field, continuous radiating sheet field, amber pith). All views read the **same** field.
- `outputs/fibers_3d.npz` — **146 persistent 3D curves** stored without pickle, not just a painted 2D image.
- `outputs/strawberry-volumetric-3cut.blend` — Blender 5.2.4 scene with **three separate closed 3D half-fruit meshes** corresponding to cuts at **0°, 32°, 82°**. By default cut 0° is rendered; use `render_slice.py` to render any other one. Skin and cut share welded boundary vertices.
- `outputs/slice-000.png`, `slice-032.png`, `slice-082.png` and `three-cuts-one-volume.jpg` — genuine Blender Cycles renders, identical studio lighting/camera settings.
- `outputs/validation.json`, `build-report.json`, `tissue-metadata.json` — numerical evidence, scope and limitations.
- `outputs/frucht-versus-new-poc.jpg` — comparison generated privately from the owner-supplied Frucht video reference. **Do not publish the video frame in the public source repo.**

## Rebuild without chat context

A prebuilt `.blend` and volume are included; no prior Strawberry Lab `.blend` is required. Blender >=5.2 includes NumPy for the build step.

```bash
blender -b -t 4 --python build_static.py
blender -b -t 4 outputs/strawberry-volumetric-3cut.blend --python validate_static.py
blender -b -t 4 outputs/strawberry-volumetric-3cut.blend --python render_slice.py -- 0
blender -b -t 4 outputs/strawberry-volumetric-3cut.blend --python render_slice.py -- 32
blender -b -t 4 outputs/strawberry-volumetric-3cut.blend --python render_slice.py -- 82
python make_comparisons.py  # The three-cut montage; optional reference needs STRAWBERRY_FRUCHT_FRAME
```

Rebuilding the volume (not required for opening `.blend`) uses standard **Python 3 with NumPy and SciPy**:

```bash
python generate_field.py
```

## Validation and claims

All three meshes have **78,626 vertices**, **78,960 faces**, **0 nonmanifold edges**, **0 degenerate faces**, and **1 connected surface component**. Tissue colors, shape and height are sampled from one 3D coordinate system, not independently authored per cut. The centerline samples are identical across angles by construction. The outer half-fruit and its cut plane are explicit physical meshes with welded seams.

**Important limitations:** cutter orientation is *prebuilt* in Python; **not a live SDF/Boolean**. Volume sampling produces a coarse macro/mid-scale structure; fine fiber bundles, accurate achene pits, convincing calyx, physically calibrated wetness/SSS and artist-level microrelief are still missing. The 150³ voxel substrate cannot express infinitely thin real fibers. All tissue is **artist-generated**, not histology. Nothing from Frucht's Blender graphs or commercial assets is bundled or copied.

## Storage

Canonical source scripts and report belong in the `strawberry-lab` repository under `experiments/volume-first-v0/`. Binary Blender scene, field and renders are private in the versioned Strawberry Lab Google Drive folder. Retain `assets/manifest-volume-first-v0.json` for SHA-256 reproducibility.
