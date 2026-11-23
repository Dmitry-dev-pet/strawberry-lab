# Strawberry Lab v17 — 3D rest-field intensity and smoothing A/B

**Date:** 2026-11-22/23 (Europe/Lisbon session)  
**Disposition:** ENGINEERING PASS (tested states); VISUAL TARGET FAIL, preserve original v12.  
**Repository destination:** draft research branch `experiment/sdf-exterior-restfield-20261122` of `Dmitry-dev-pet/strawberry-lab`, not `main`.

## Reproducible source and exact provenance

- Source is the *unchanged* owner-private Blender scene `strawberry-sdf-vertical-slice-v12-continuous-wet.blend` (SHA-256 `300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410cbb405b7`), recovered from Drive and opened with Blender autoexec disabled.
- Verified local Blender 5.2.4 LTS Linux x64 restored from owner's 17-part Drive package, original archive SHA-256 `2fd14c50987426897ba60237ee996edf2b4151f4b1a72a460ca20be58c1d2d86`.
- Original v12 baked 192³ red-channel field is supplied by the preceding v16 diagnostic (`source_r_field_192.npy`), extracted from the packed image via the included v16 script. Data axis order is Z,Y,X with source bounds X/Y = −18..18 mm, Z = −1..50 mm. The original G/B channels were preserved and checked as float32 image data after saving/reopening; alpha remained 1 throughout construction. Both shader samplers and both GN samplers bind the same new packed image.
- All unmeasured numbers remain **ARTIST**. Not a reconstruction of Frucht's closed commercial node tree, a biological measurement, or evidence of actual xylem/phloem diameter. No copied Frucht code, movie frames, other assets or ImageGen renderings.

## One controlled hypothesis, two alternatives

- **v17A — remap only**: monotonic intensity remapping of existing R field. No new fiber path geometry, rest-coordinate deformation, original material changes or new cell types.
- **v17B — remap after smoothing**: same monotonic intensity remapping applied to the original R field first filtered by a 3D Gaussian with sigma=(1.2,1.5,1.5) voxels in Z,Y,X, ~0.32 mm in Z and ~0.283 mm in X/Y. No additional geometry/material nodes; source R is replaced in an original 16×12 PNG atlas. Original Blender rest-space/cutter, 3D Voronoi cell geometry and subsurface/coat settings retained.
- The intensity knots X: `[0, .02, .05, .10, .15, .20, .30, .40, .60, .75, 1.0]`; mapped Y: `[0, .013, .055, .18, .34, .46, .62, .72, .83, .90, .95]`, with 8-bit quantization exactly as v12 source atlas.

## Actual Blender 5.2.4 evaluated cap-only metrics

Selection: material index **2** (cut flesh), 4-vertex cap polygons; area-weighted threshold from average of four vertex intensities. **No whole-fruit denominator**.

| Metric | Original v12 | v17A remap only | v17B smoothed remap |
|---|---:|---:|---:|
| Planar cut area R≥0.3 | **1.84%** | **7.59%** | **5.17%** |
| Bite area R≥0.3 | **1.22%** | **5.35%** | **3.37%** |
| Planar strong-R cap mesh components (edge-connected) | 34 | **132** | **33** |
| Bite strong-R cap mesh components | 13 | **224** | **14** |
| Largest high-R planar patch bbox diagonal | 0.96 mm | 28.52 mm | 3.54 mm |
| Largest high-R bite patch bbox diagonal | 3.88 mm | 4.84 mm | 5.02 mm |

**Important:** the bounding-box diagonal is a span proxy, not physical vessel length or path length; component counts use cap mesh edges and can include tiny disjoint islands. On low-R threshold R≥0.1, v17B merges a lot of diffuse halo into broad connected regions (11 planar, 6 bite), which can create washed-out tissue; this is not a fidelity metric.

### Engineering gates

- A and B were saved as editable `.blend` copies; source v12 kept unchanged. 2/2 shader + 2/2 GN packed atlas bindings checked; G/B pixel channels unchanged after readback.
- Actual native GN evaluated results on **5 poses per version**: whole, planar, bite, translated/rotated planar, translated/scaled spherical bite. **10/10** tested poses have zero non-manifold edges and positive signed volume. The original A/B diagnostic process completed 9 poses before a process timeout; the remaining v17B moved bite was checked independently in a fresh Blender process and passed. Do not represent this as a single uninterrupted 10-pose run.
- Pure-python trilinear rest-space R sampling against saved GN R attribute gave max absolute difference below `7.5e-5` in initial plane/bite, for both A and B.
- SDF controls, achene attachment policy, actual cutter shapes, shader node trees and Voronoi parameters are unchanged; evaluated cap vertex positions and volume change *slightly* because original GN cut-cell height is intentionally modulated by the new R field. Watertightness and volume do not prove absence of all triangle self-intersections or arbitrary cutter safety.

## Genuine Cycles qualitative A/B — FAIL

Nine original Blender 5.2.4 CPU Cycles frames with *identical* camera, lighting, frames (20 planar/macro; 40 bite), **640×640/16 samples** for original v12, v17A, v17B. The study ran at this reduced resolution to keep the CPU-only environment bounded. Images are untouched genuine Cycles PNGs, not AI images.

- v17A: the bright filaments and seed-linked marks become stronger but still look like bright strokes and white dots rather than connected internal tissue; the planar cut shows somewhat artificial lines, and the bite remains a smooth scooped bowl.
- v17B: smoothing reduces pixel-level clutter and merges some short fragments but visibly softens edges, giving pale, blurry blotches rather than the detailed wet fibrous relief seen in the original author footage. The previous baseline v12 remains a less intrusive visual control.
- On matched **8-bit PNGs**, source v12 vs A changes more than 8/255 in at least one RGB channel at 3.01% of whole plane pixels, 1.31% of bite pixels and 12.38% of macro pixels. Source v12 vs B: 1.49%, 0.72% and 6.81% respectively. These are *image-change* metrics only, not biological or visual-fidelity scores.
- **Conclusion:** stronger/longer numerical field signatures do not by themselves yield Frucht visual realism. Stop pure contrast/blur tuning. The next scoped hypothesis should address coherent tissue orientation and micro-relief response while preserving the same rest-space single source and independent scene QA. No new independent 3D vessel-object proliferation or unrelated seam fixes.

## How to reproduce

The archive contains exact scripts `prepare_fields.py`, `build_v17.py`, `qa_v17_native.py`, `qa_bite_moved_v17b.py`, `compare_field_connectivity.py`, `render_v17.py`, `render_batch.py`, `compare_cy_cycles.py`, `render_cap_maps.py`, `aggregate_results.py`; in the test environment they assume `/mnt/data/strawberry-v17` and `/mnt/data/strawberry-diagnostics` directories. For relocation, replace the literal root paths, or map matching directories. Requires original private v12 `.blend` and the preceding v16 extracted R field. Commands with fixed paths and verified runtime:

```bash
python prepare_fields.py
BLENDER=/mnt/data/blender-runtime/blender-5.2.4-linux-x64/blender
"$BLENDER" -t 4 -b --disable-autoexec --python build_v17.py
"$BLENDER" -t 4 -b --disable-autoexec --python qa_v17_native.py
"$BLENDER" -t 4 -b --disable-autoexec --python qa_bite_moved_v17b.py
python compare_field_connectivity.py
python render_batch.py
python compare_cy_cycles.py
```

The Blender QA master run in the original environment timed out after 9 states; use the separate moved-bite QA, and read the aggregated QA JSON rather than claiming a single complete master run. 

### Files and access

The user-visible comparison sheet is `comparison-v12-v17-plane-bite.png` (6 frames); a 9-frame macro contact sheet is `comparison-v12-v17-all-9-cycles.png`. `strawberry-v17-research-verified.zip` includes both original editable v17 scenes, packed RGB atlases, original nine Cycles PNGs, analysis code, JSON receipts, and diagnostic maps; hash-verified member-by-member. The original 25 MB v12 scene remains on private Drive and is not included in this derivative package. No public share setting was changed.

## Completed reproducibility addendum

The original 9-state exploratory Blender diagnostic was followed by two complete standalone core validators (one saved scene per process, auto-execution disabled). Each independently passed five native geometry states, so **10/10** states have positive volume and zero nonmanifold edges. These independent runs are separate from the initial timed-out exploratory process. Tested source: [isolated validator](validate_v17_restfield_blender.py), [field preparation](prepare_v17_restfield.py), [scene generator](build_v17_restfield_blender.py), and [Cycles renderer](render_v17_restfield.py).

**Final owner archive (private Drive with complete SHA-256 readback):** strawberry-v17-research-verified.zip, 93,472,945 bytes, 64 members, full per-member SHA-256 readback PASS, archive SHA-256 d24816549d6e33d4b9216fcb95de1e5e3e5760f0eae8ba032cda9f8d563bbe99. Contains two editable scenes, packed 192³ atlases, nine genuine 640px/16sample Cycles PNGs, contact sheets, R maps, caps, scripts, core validation receipts, and A/B numeric data. Uploaded to [owner-private Strawberry Lab / research-sdf-v17-restfield-20261123](https://drive.google.com/drive/folders/17470W2mjybEyVIdgxna4Q-hDqU_U2H99) as [strawberry-v17-research-verified.zip](https://drive.google.com/file/d/1z5NOM3Bv79Pn1lf397roITExeJyVVizy/view?usp=drivesdk). Independently downloaded the uploaded 93,472,945-byte ZIP and compared full SHA-256 to the local source: exact match d24816549d6e33d4b9216fcb95de1e5e3e5760f0eae8ba032cda9f8d563bbe99; all 64 ZIP members passed integrity validation. Original v12 stays in owner-private Drive and is excluded.

**Visual decision unchanged:** remap-only v17A creates too many isolated bright dots and streaks; v17B reduces field fragmentation while producing blurry pale spots. Neither gives convincing wet fibrous strawberry flesh compared to the original Frucht demonstration. Do not merge PR #43 or promote v17 to product main without owner visual acceptance.


### Direct owner Drive image previews (readback verified)

- [v12 vs v17A vs v17B — planar and bite, six genuine Cycles frames](https://drive.google.com/file/d/1sUmFb6S127j3qKYOYiqAIBe316O1eoUT/view?usp=drivesdk) — 1,082,059 bytes, uploaded and independently downloaded with SHA-256 `40c2ddf53c3af039cdb889cfb93e6878609d238bd32d1a68b4b3985dca49965c` matching local.
- [Nine-frame comparison including cut macro](https://drive.google.com/file/d/1zTgz2LEnxvWtvAKwwZd7zQUKvnJ43YXu/view?usp=drivesdk) — 1,953,157 bytes, independently downloaded SHA-256 `08e69044ddb1aae7d72aa528cac01ee7d08af63e240f70889c9f0d218c1f8e3d` matching local.
- [Owner-private artifact folder](https://drive.google.com/drive/folders/17470W2mjybEyVIdgxna4Q-hDqU_U2H99). No public sharing change.
