# Strawberry Lab v14 — non-periodic seed-linked fibrils + native torn bite lip (22 November 2026)

**Status: engineering PASS, visual Frucht-fidelity FAIL; B gives only a minor rim improvement.** This is a bounded independently-authored experiment, not merged or recommended for product `main`. Source, scene, tests and actual render receipts are preserved. No paid Frucht/GPL node trees, textures, meshes or media copied.

## Problem / controlled hypothesis

The previous independent [v13 stripe study](v13-spatial-fibrils-negative-result.md) was geometrically sound but visually regressed into nearly parallel artificial lines. This test is **not another shader-frequency or coat adjustment**. Instead:

- **v14A field-only:** keep the unmodified original owner v12 Blender scene as parent and replace **R-channel only** of a shared 192³ rest-space atlas. From **264 existing actual achene anchors**, deterministic `numpy.random.default_rng(141126)` selects **72 seed-linked 3D cubic-Bézier main routes** (27 near the original cut plane + 45 distributed others), plus **139 3D side branches** sharing true parent positions. Build continuous 3D Gaussian tube kernels using 9,200 evaluated points, no periodic radial sheets; preserve green mottling and blue pith data before PNG encoding. Historical v12 R-field contributes at 22% amplitude, the new sparse field contributes at 83% amplitude. All widths/radii/positions are **ARTIST**, not biological vessel measurements.
- **v14B field + tear:** identical atlas, source, geometry nodes and camera as A, **only** `V14_TEAR_GAIN=1` vs 0. A native GN `Set Position` on the same bite cap adds spatial, non-periodic, rest-space noise conditioned by local vascular intensity and actual distance to the original skin near the bite rim (smooth fade over 1.85 mm). Signed displacement follows local normals. This changes the actual evaluated mesh, *not just material normal/roughness*.

Both variants use the original live SDF difference and actual 6,050-vertex scalloped cutter, the same shared `fruit_rest` field and native achene/cutter guard. The untouched files v8, v10, v11, v12 and visually rejected v13 are preserved.

## Grounded build and saved-scene QA

Rendered and validated with actual Blender **5.2.2 LTS** on Mac, with Blender scripts autoexecution disabled during independent reopening.

| State | A evaluated vertices | B evaluated vertices | Nonmanifold edges A/B | B max absolute physical tear |
|---|---:|---:|---:|---:|
| Whole | 157,250 | 157,250 | 0 / 0 | Not applicable |
| Plane | 194,354 | 194,354 | 0 / 0 | Not applied |
| Scalloped bite | 350,314 | 350,314 | 0 / 0 | 0.191544 mm |
| Moved/rotated plane | 154,762 | 154,762 | 0 / 0 | Not applied |
| Moved/enlarged bite | 361,858 | 361,858 | 0 / 0 | 0.164630 mm |

All ten evaluated bodies have **positive signed volume, nonzero face areas** (under this test's lower bound) and zero nonmanifold edges. The exposed geometric height attribute exists and is exactly zero on A; on B **6,866 / 9,132 vertices** exceeded 0.02 mm displacement for the bite / moved bite.

Independent closest-face signed-proximity tests on **actual cutter surfaces**, rather than a unit sphere approximation, found **zero retained achene *vertices* inside** either cutter: plane 16,554, moved plane 11,748, bite 40,228, moved bite 37,558 sampled vertices. The method does not prove absence of all triangle crossings/self-intersections; no SDF memory or VRAM measurement was added.

## Six genuine Cycles renders and visual verdict

Two independent Blender processes saved 3 frames per variant (plane, bite, cut macro), fixed **860×860 / CPU Cycles 36 samples** and inherited matching camera, lights and scene frames **20/40**. Original unmodified v12 renders are the baseline. No image-generation model was used.

- **Planar cut:** v14A/B remove v13's obviously periodic white stripes, but the new seed-linked 3D routes are too sparse/faint at this cutter pose. Relative to v12, the plane becomes **too uniformly red** and loses convincing fibrous macrostructure. Both A and B are visually unaccepted.
- **Bite:** B makes the *edge* visibly rougher than A, but the cavity still resembles an artificially carved smooth bowl. No exposed bundle pull-out, separated wet tissue lamellae or irregular depth fragmentation. Not enough for visual acceptance.
- **Macro:** A/B again look too uniform; B purposely does not act on the planar macro. The persistent tissue representation is the limiting factor, not the wet coat tuning.

Image pixel comparison (identically sized frame, same color decoding) confirms the intervention is **real and local**: A vs B is **exactly identical pixel-for-pixel** on plane and macro, while bite A vs B changes **1.69% of pixels by >0.01 max RGB channel** and **0.534% by >0.05**, with MAE RGB 0.000667. This is an objective *render-difference* check, NOT a quality score; scene A and B share the source but were independently rendered. Original v12 vs A plane changed 6.494% >0.01; v12 vs A macro changed 25.992% >0.01. The qualitative assessment remains **FAIL**.

No new side-by-side with copyrighted Frucht frames was distributed. Previously audited private Frucht frames at 10s and 18.2–19s remain a separate visual benchmark, not proof of matching camera or lighting.

## Exact reproduction, provenance and storage

Public, fully independently-authored scripts and JSON:
- [builder](build_v14_nonperiodic_tears.py) · [saved-scene geometry + actual cutter validator](validate_v14_nonperiodic_tears.py) · [true Cycles renderer](render_v14.py) · [pixel A/B analyzer](analyze_v14_image_ab.py) · [contact sheet builder](make_v14_contact_sheet.py).
- [Build hashes, source seed and counts](v14-build.json) · [10-state independent QA](v14-validation.json) · [pixel comparison](v14-pixel-ab.json) · [9-frame contact sheet receipt](v14-contact-sheet.json) · [28-member locally verified ZIP manifest](v14-archive-manifest.json). Six original Cycles render JSON receipts are in the same branch.

Owned original artifacts on the *user's Mac only* under `build/sdf-vertical-slice/` (ignored and not pushed to public GitHub):

| File | SHA-256 |
|---|---|
| `strawberry-sdf-vertical-slice-v14a-branch-field.blend` | `9f75ea3271ffed23481735d352d2dc45a7ecb8cdfdce50101efc6abe95224ee3` |
| `strawberry-sdf-vertical-slice-v14b-branch-tear.blend` | `8b2a5e122ae69e676a51a58ca149c0d0fd8a5d956bf6ac6ef013908cb684c91d` |
| `tissue-v14-seed-linked-branches-192.png` | `3217dbf3e50a8541c8886c8a7f780618bf4f2776a586759f83277810c4fa7a0c` |
| `comparison-v12-v14a-v14b-three-shots.png` | `98db9a81f35ea2dcdd45f033ddcdbcc4c8a72faa32ef4bdd973dbc1bcbc3adb9` |
| `strawberry-v14-AB-research.zip` | `4641c0f75895bf97e5d2b0042ef127466b7617d0d78918f1c1ba99952e6dd0fa` |

The **67,165,457-byte ZIP was reopened and all 28 members verified against individual SHA-256**. Contact sheet columns left-to-right: v12 / v14A / v14B; rows top-to-bottom: plane / bite / macro. Scene and atlas remain local; **no user Drive upload/readback is claimed**. The Mac's configured `gdrive` CLI could not access the pre-existing private v11-v12 Drive folder (404), so **no upload was attempted through a potentially different account**. The verified local archive is not a public download.

To regenerate, place a trusted copy of the owner-private unmodified v12 scene in `build/sdf-vertical-slice/`:

```bash
export STRAWBERRY_SDF_OUT="$PWD/build/sdf-vertical-slice"
B=/Applications/Blender.app/Contents/MacOS/Blender
"$B" --background --disable-autoexec --python experiments/sdf-exterior-2026-11-22/build_v14_nonperiodic_tears.py
"$B" --background --disable-autoexec --python experiments/sdf-exterior-2026-11-22/validate_v14_nonperiodic_tears.py
for variant in v14a v14b; do
  for shot in plane bite macro; do
    source="$STRAWBERRY_SDF_OUT/strawberry-sdf-vertical-slice-$([ "$variant" = v14a ] && echo v14a-branch-field || echo v14b-branch-tear).blend"
    "$B" --background "$source" --disable-autoexec --python experiments/sdf-exterior-2026-11-22/render_v14.py -- "$variant" "$shot"
  done
done
```

## Decision / next scientifically honest step

**Keep v14A/B unmerged as experimental controls.** The next real-quality hypothesis should not tweak field amplitude, noise scale or sheen again. Instead, explicitly represent **physical, attached 3D torn bundles and layered wet interior geometry** at one localized bite (for example, several SDF-unioned thin attached fibrous volumes from the same source coordinates), with an exposed-groove macro and independent cut/volume topology QA. The current shader/color field alone cannot supply 3D material pull-out; its thin curves may simply cross arbitrary planes as dots. A single bounded 3D ribbon/bundle geometry A/B is justified *before* large Fruit Engine refactoring. Scientific anatomy status remains **ARTIST/UNVALIDATED**.
