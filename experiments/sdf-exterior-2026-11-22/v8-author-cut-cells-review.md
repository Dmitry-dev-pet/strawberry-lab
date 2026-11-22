# Strawberry Lab v8 — author-inspired cut cells with corrected rest-space lookup (22 Nov 2026)

**Status:** engineering PASS on tested poses, visual Frucht fidelity **NOT accepted**; no changes to `main`.
This *supersedes experimental v7*, whose Geometry Nodes voxel atlas lookup mistakenly applied smoothstep to normalized XYZ coordinates. It sampled the same image at **different positions from the material shader**. V8 removes that error: explicit linear clamp `max(0,min(1,x))`, linear XYZ mapping and Z interpolation, same atlas coordinates used by the material shader.

## Goal and method

The public explanation of Frucht describes small cut-face Voronoi bumps (flatter over pale fibers) plus separate wet-surface Voronoi layers. **It does not prove the strawberry contains individually modeled full 3D cell solids.**

V8 therefore returns to our independent **v4** base:
1. Keep live GN **Mesh→SDF Grid → SDF difference → Grid→Mesh**, 264 original achene solids and skin/outer pits.
2. Retain one packed rest-space **192³ RGB volume**; both material shader and GN sample its red-channel vascular intensity at the **same original 3D positions**, without rebuilding separate maps per cut.
3. Create a **small real mesh bump** from 3D warped Voronoi only on the exposed cut face (one native subdivision), reducing it over the sampled pale strands and fading it out near original skin.
4. Shade wetness independently with existing 3 Voronoi layers at restrained strength, not a second set of solid cells.
5. Keep all tissue/achene morphologies labeled **ARTIST**. No reconstructed histology or closed individual cell solids; Frucht's private source nodes were not copied.

## Native independent Blender 5.2.2 verification (autoexec disabled)

| Pose | Evaluated body vertices | Nonmanifold edges | Positive volume | Kept seed solids | Kept seed verts inside cutter |
| --- | ---: | ---: | :---: | ---: | ---: |
| Whole | 157,250 | 0 | Yes | 264 | n/a |
| Planar | 194,354 | 0 | Yes | 93 | 0 |
| Planar moved and tilted | 154,762 | 0 | Yes | 66 | 0 |
| Spherical bite | 344,634 | 0 | Yes | 227 | 0 |
| Bite moved and enlarged | 354,698 | 0 | Yes | 215 | 0 |

Physical mesh motion compared against identical geometry at 0 cell strength: **max 0.01839 mm**, at least **55,444** planar vertices and **41,217** bite vertices move more than 0.005 mm. This is **not** a shader-only bump. Same original volume image sample is exposed as `v8_vascular_intensity` in GN. Over strong vessel signal (red intensity >0.23), the actual cell relief amplitude is **0.325× planar / 0.315× bite** its amplitude without fiber flattening (about **67–68% suppression**); outside strands (<0.01) ratio is **1.0×**.

These tests verify two poses for each named cutter, NOT every possible orientation; crown is not yet cut-controlled.

## Cycles visual A/B

Three actual Blender Cycles renders, same 860×860 studio and 36 samples as v4: `sdf-v8-plane.png`, `sdf-v8-bite.png`, `sdf-v8-macro.png`; A/B pairs `comparison-v4-v8-*.png` place v4 left and v8 right. The visual change should be assessed from these exact renders, not an image-generation approximation.

**Visual assessment remains NOT ACCEPTED:** cells subtle, long pale strands visible without v5's extreme "caviar" morphology, but strands are still stylized and the bite has an overbright central patch; the difference relative to v4 is modest. An exact new A/B to Frucht video was *not* possible this run: the original video and contact-sheet in mounted Google Drive were placeholders that could not be decoded locally, so earlier source study is the only author-grounded reference.

## Reproduce

With `build/sdf-vertical-slice/strawberry-sdf-vertical-slice-v4.blend` present (from private owner Drive), Blender 5.2+, and the independent repo:

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/build_v8.py
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/validate_v8.py
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/render_v8.py
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/make_v8_comparison.py
```

Use `STRAWBERRY_SDF_OUT` to override output directory; all existing v4/v5/v6/v7 artifacts and scripts are untouched. Small code/JSON receipts go in draft PR #43, large .blend/PNG artifacts remain in owner Drive with SHA-256 hashes.

**Decision:** keep v8 as a more faithful *technical* implementation of the described idea, but do not merge. Next work needs the author reference frames actually available, rigorous visual match of cut/cells/fibers at the same scale, and localized glossy wet film. Avoid adding standalone whole-fruit cell meshes or rewriting the SDF cutter in the absence of evidence.


## Verified private binary deliverables

[Owner Drive v8 folder](https://drive.google.com/drive/folders/1U_1nExBgmu0es2va-JT0Y0AcMxPEFoQx) contains the editable [.blend](https://drive.google.com/file/d/13Q5SgERALXVbeWWBG_V-PpQXAhWPOOQW/view), true Cycles [macro A/B](https://drive.google.com/file/d/1uYxFhL1-JhU08Pyv50v7iy_yoleL8VYF/view), [plane A/B](https://drive.google.com/file/d/1xJrqhmRO2ps2M0sxc5jhpmrPDmcnRjgX/view), and [bite A/B](https://drive.google.com/file/d/19p6zKgKqbGaDU4ESTP2iN7MlQ6O071t_/view). The Drive folder was read back and file sizes matched the original Mac copies; local SHA-256 copy checks all matched. It remains owner-private and unmerged.
