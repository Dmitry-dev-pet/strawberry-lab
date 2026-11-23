# Strawberry SDF rest-space tissue: controlled A/B (23 Nov 2026)

**Status: research; NOT accepted for main.** Based on owner-private PR48 scene `new-qa.blend`, SHA256 `bfecf691df67cafff020971368f1afc877f4bac1165e851520bdcc1773f85ce1`. The PR48 vertex-intersection guard stays untouched; PR47 is already in main. Blender 5.2.4 LTS CPU; all new fields are original ARTIST parameters, not histologically calibrated measurements. No source code, assets, or materials from commercial/GPL Frucht were copied.

## Why not copy v20/v21 shader sockets?

The archived [PR46](https://github.com/Dmitry-dev-pet/strawberry-lab/pull/46) v20 has its own 192-cubed core/halo geometry atlas; v21 reduces a specific *color* outline chain at `Math.039`. Our merged SDF engine uses a distinct 150-cubed inherited tissue atlas and different material graph. Copying that named socket would change another signal. This experiment tests newly implemented 3D fields sampled in `sdf_rest_position`, not the original v20 graph or biological anatomy.

## Experiment 1: shader-only microfilament (visual negative)

`build_ab.py`: one anisotropic 3D noise field at rest-space scale `(120,108,26)` drives shader Bump and local roughness through exactly one gain, A=0 and B=1. `validate_ab.py` verifies identical evaluated mesh geometry/packed atlas for plane and bite. Six original 720px/20-sample Cycles frames (plane, macro, bite) have matched camera/light/pose/seed=1729 and show little substantive improvement. On plane approximately 7.94% of pixels differ by >2/255 in any channel: a detection metric, **not** a quality metric. Microfilaments alone leave the entire cut smooth.

## Experiment 2: native GN source-space cut relief (mechanism PASS, realism FAIL)

`build_geo_ab.py` adds one Set Position to the native SDF cut output, prior to Shade Smooth. Its offset is based on one deterministic, original `sdf_rest_position` 3D noise `(45,42,12)`, with an ARTIST radial pith suppression mask, smooth cutter-distance fade, and a WHOLE-mode gate. Existing body, seeds, materials, cutters and tissue atlas remain unchanged; no individual cell solids or free liquid layer are claimed.

Exactly one physical gain differs: A=0, C=0.35, B=1.0. The signed bounded field has source limit 0.095 mm and measured maximum displacements **0, 0.03325, 0.0950 mm** respectively. `validate_geo.py` compares A/B and A/C at voxels 0.32 and 0.20 mm in WHOLE/plane/side-bite: each of the 6 evaluated states in each comparison is one closed connected mesh with zero nonmanifold edges, finite positive volume and no degenerate triangles under 1e-10 mm2. WHOLE never changes. The matched side-bite and plane meshes change only positions (not connectivity), and packed atlas stays byte-identical. `live_controls_qa.py` reopens the scene with scripts disabled: 0.35 -> 0 -> 0.35 round-trips exactly; rotating the plane changes evaluated geometry.

**Original Cycles A/C/B:** 3 shots x 3 variants, 720x720, 20 samples, fixed seed 1729, matching camera/light within each view, including an open side-bite. Plane A/C changes >2/255 in 10.78% of pixels, A/B in 17.93%. This measures that a change is present, **not photorealistic quality**. A/C/B images show C's texture is restrained versus B's excessive regular ribbing. Neither resembles wet, nonperiodic, branching tissue at the author's reference quality; visual milestone remains FAIL. Geometry tests do not establish biological cell structure or exhaustive self-intersection safety for arbitrary poses.

## How to reproduce

Use Blender >=5.2, the pinned owner-private PR48 `new-qa.blend` from [Drive](https://drive.google.com/drive/folders/1kP4wbsqjXW0zOvISaCUB4EUTlmer4SUC) and set `B=/path/to/blender`. Run from repository root:

```bash
$B -b --factory-startup --disable-autoexec --python-exit-code 1 --python experiments/sdf-rest-relief-2026-11-23/build_geo_ab.py -- --source inputs/new-qa.blend --outdir build/geo-ab
$B -b --factory-startup --disable-autoexec --python-exit-code 1 --python experiments/sdf-rest-relief-2026-11-23/variant_gain.py -- --source build/geo-ab/pr49-rest-relief-B.blend --out build/geo-ab/pr49-rest-relief-C.blend --gain .35
$B -b --factory-startup --disable-autoexec --python-exit-code 1 --python experiments/sdf-rest-relief-2026-11-23/validate_geo.py -- build/geo-ab/pr49-rest-relief-A.blend build/geo-ab/pr49-rest-relief-C.blend build/geo-ab/geometry-ac.json .35
$B -b --factory-startup --disable-autoexec --python-exit-code 1 --python experiments/sdf-rest-relief-2026-11-23/live_controls_qa.py -- build/geo-ab/pr49-rest-relief-C.blend build/geo-ab/live-controls.json
$B -b --factory-startup --disable-autoexec --python-exit-code 1 --python experiments/sdf-rest-relief-2026-11-23/render_geo.py -- build/geo-ab/pr49-rest-relief-C.blend plane build/geo-ab/plane-C.png 720 20
```

Same source SHA is required; builders refuse to replace an existing output. Use `build_ab.py`/`validate_ab.py` to reproduce the negative shader-only control. `compare.py --root build/geo-ab` requires `renders/plane|macro|bite-A|C|B.png` and same-name JSON receipts created by `render_geo.py`, and validates matched settings before creating a contact sheet. Source `.blend` is private, not committed. Scene binary SHA may vary by Blender serialization; validation relies on re-opened evaluated mesh, graph and actual render receipts.

## Decision

Retain this bounded A/B as a reproducible research result, not a product merge. The gain 0.35 variant is a better diagnostic than the exaggerated gain 1.0, but owner visual acceptance has not happened. The next hypothesis should replace regular Z-aligned bands with specimen-oriented 3D branching/pore fields and a **separate wet-film geometry / scattering layer**, with geometry QA and original Cycles A/B. PR48 remains its own unmerged dependency. No library/GitHub original input, third-party references or existing main files were overwritten.

## Durable private evidence (owner-restricted)

[Private Drive folder — pr49-restspace-cut-relief-2026-11-23](https://drive.google.com/drive/folders/1inMppZwF-DCl_sbTF7Md_4lUWrzrGgAE): all **5/5** uploaded files were downloaded back and matched their local bytes by SHA-256. Original PR48 input/source and previous experiments are not overwritten.

- [Reproduction ZIP, all three scenes/9 Cycles PNGs/source/QA](https://drive.google.com/file/d/1J5HwmeN5ye2HWUvDOI4hGmSBy7LLGap6/view): 50,306,895 bytes, SHA256 `767f645bfa13922ca8dc67057a958520862f037133099cdca0487ee4ddb560c6`.
- [Editable moderate relief scene C](https://drive.google.com/file/d/1aMSoqBPph8BAVTHQMFG-wv_fQFtcsrxk/view): 11,571,950 bytes, SHA256 `51e044143cabfea157aa0244e59701a6e31a63e7d05284ff31fa521bacebb380`.
- [Nine-frame Cycles A/C/B comparison](https://drive.google.com/file/d/1eE7DePtU-zoXjpuo6roIL7ejqLHL2hoc/view): SHA256 `85f30821738ad315c75518fa9f62cfc7cb2c70ee9b862859dc4c22ac4fcd961c`.
- [Matched-image difference JSON](https://drive.google.com/file/d/1bHEWs8l5AhyQ4GnnWfhFcoLLRwbx0DFa/view): SHA256 `6858779a048af254477a82dfd24d130dd00fdbd9909f690f5b1687101cd67881`.
- [SHA manifest for entire ZIP](https://drive.google.com/file/d/1X88mbqeaO51ThPGPtyDCKBw6WHyMnxe3/view): SHA256 `b501fc954c0c75ace0265fd583ff093f9884631f1be1e7d45ca71c944c3b23ca`.

All generated images are genuine Blender Cycles outputs. The contact sheet itself resizes source PNGs only for comparison; raw frames and exact image receipts remain in the private ZIP.
