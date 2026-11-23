# Strawberry Lab — same-source vascular field for cut geometry AND color (2026-11-23)

**Status: native Blender technical PASS on tested scenes; real Cycles visual FAIL.** This remains research in the existing draft PR #49 stacked on unmerged PR #48. **Do not merge this shader intervention to `main`.**

## Reason, not a new anatomy model

The current PR49 v20 bridge already re-rasterizes the **existing owned** v19/v20 557-component graph from the true 264 achene anchors. The native Geometry Nodes cut surface reads the **new 192³** vascular core R and wide halo H from that same rest-space. The material `SDF | inherited 150^3 tissue + own multiscale wetness` still reads its older **150³ RGB** source color atlas, without sampling the *new* R used for geometry. That mismatch can make source-color pale paths unrelated to physically raised veins.

Previous older-scene experiments **v13** (periodic ribbon-like stripes) and **v17** (intensity remapping) were technical PASS / visual FAIL. This is a narrower **color/geometry field-coherence** test against the current seed101 model. It does not rebuild graph topology, generate new vessels, or claim biological vessel diameters.

Source editable scene: owner-private [PR49 v20 bridge](https://drive.google.com/file/d/1huv9bwO4wcydPZEvnMbdBCIbfJCURvCa/view), SHA-256 `0b79e33b0725f807524061b1afe79671f4fcf1c6b5c429bd8203cec8d6a21bd2`.

## Bounded intervention

`build_shared_color.py` adds one `ShaderNodeAttribute` reading the actual evaluated point field **`sdf_v20_core`**, one smooth threshold R=.18–.55, and a weak warm artist color blend into Base Color. Crucially, the shader reads **the existing stored field from the very same evaluated SDF body**, not a new 2D mask or a separate duplicated 3D atlas. Its gain is a native driver-backed Body custom property `sdf_v20_color_gain`, reversible in saved `.blend` with scripts disabled.

Three saved variants of the same node graph, same original body, native seed guard, R/H atlas, 150³ atlas, lights and cameras:

| Variant | Gain | Maximum artist vascular color blend | Outcome |
|---|---:|---:|---|
| A | 0.0 | 0% | Exact current source image baseline |
| C | 0.25 | 6.25% | Softer pale spokes; still synthetic |
| B | 1.0 | 25% | Strong almost straight, wide pale spokes: clear visual failure |

These are **ARTIST color experiments**, not a new physical tissue structure or simulated lumen/juice. The right outcome may be to reject **all** these colors while retaining the architecture learning.

## Independently verified actual Blender 5.2.4

All `.blend` opened with script autoexecution disabled. For original A vs strong B **and** A vs restrained C, 5/5 evaluated states per pair: 0.32 mm WHOLE, center PLANE, open-side SPHERE; 0.20 mm center PLANE and open-side SPHERE. All have identical evaluated **body vertex SHA and 192³ vascular core point-attribute SHA**, identical source mesh and packed 150³ atlas; zero nonmanifold edges and positive signed body volume. There is no geometric deformation in this study. Original PR49 bridge geometry tests previously checked connectivity across ten poses, but this current QA does not add new self-intersection proofs.

A reference **read-only coverage analysis of the exact same current original scene** confirms that the vascular field is not absent on the cap: with area-weighted polygon-mean R≥0.30, **21.55%** of the center-plane cap and **14.22%** of the open-bite cap respond; H≥0.30 covers **45.09%** / **36.95%** respectively. Geometric cut relief maxima **0.1377 mm** plane and **0.1367 mm** bite. These thresholds/areas measure artist fields and *must not* be described as actual physical fiber area or histological diameters. Current field coverage is not directly comparable to former v16 numbers from a different scene.

**Original Cycles** at 640×640, 16 samples, seed 1729, saved-scene A/B/C real Blender renders:
- Plane: A, C and B (3 independent PNGs)
- Open-side bite: A and C (2 independent PNGs)
- The current A frames exactly match the archived previous PR49 v20-bridge halo PNGs (all RGB pixels exactly identical); source model and lighting have been proven preserved.
- Plane A→C changes **5.91%** of pixels above 2/255, A→B **7.44%**. Bite A→C changes **2.88%**. This measures **intervention effect, not realism or author approval**.

**Visual FAIL:** moderate C has slightly better connected color-to-geometry traces but still reads as bright spoke-like lines. Strong B worsens the effect. The broad white upper pith, weak surface microstructure and bowl-like bite remain. Do not keep increasing the color gain, 3D fiber count or wet specularity to compensate; physical connected tear anatomy is missing. No original author media is included or committed.

## Reproduction

With real Blender 5.2.4 and the private SHA-pinned source scene in `inputs/v20-bridge-portable.blend`, from repository root:

```bash
B=/path/to/blender
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-shared-vascular-color-2026-11-23/build_shared_color.py -- --source inputs/v20-bridge-portable.blend --outdir build/shared-color
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-shared-vascular-color-2026-11-23/variant_gain.py -- --source build/shared-color/shared-vascular-color-B.blend --out build/shared-color/shared-vascular-color-C.blend --gain .25
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-shared-vascular-color-2026-11-23/qa_shared_color.py -- build/shared-color/shared-vascular-color-A.blend build/shared-color/shared-vascular-color-B.blend build/shared-color/qa-ab.json
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-shared-vascular-color-2026-11-23/qa_shared_color.py -- build/shared-color/shared-vascular-color-A.blend build/shared-color/shared-vascular-color-C.blend build/shared-color/qa-ac.json .25
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-shared-vascular-color-2026-11-23/render_shared_color.py -- --scene build/shared-color/shared-vascular-color-C.blend --shot plane --out build/shared-color/plane-C.png --resolution 640 --samples 16
```

Builders refuse overwrites and verify exact owner source SHA. Existing source material/geometry/vascular packed atlases preserved. The large original source scene and licensed author references stay owner-private; only original project sources and compact QA evidence belong in public GitHub. This study's raw Blender binaries and original Cycles PNGs are available from its owner-private Drive bundle with SHA256 integrity manifest.

## Recommendation

Keep these as a measured failure and a working **shared-field material binding recipe**. Future changes should focus on *attached and branching tear structures that change the actual geometry and have physically meaningful cross-cut texture*, tested against real 10s/18–20s reference frames. Additional graph color tint alone is ruled out as a substantive improvement.
