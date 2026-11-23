# Annular central sheath and cutter-pose control (22 Nov 2026)

**Status: ENGINEERING PASS on the tested poses; VISUAL FAIL against Frucht. Research only. Not accepted, not merged into `main`.**

This is a **separate exploratory variant** of the existing [v9 filled-spindle experiment](owner-video-v9-v10-audit.md), and does **not** replace its `build_v9.py`, source artifacts, or the v10 independent ragged-bite branch. The locally saved file is named `strawberry-sdf-vertical-slice-v9-core-sheath.blend` to distinguish it from the pre-existing `...-v9.blend`.

## New, narrow hypothesis

The original owner-authorized Frucht video at 11 s shows a pale *sheath around a reddish interior*, not necessarily a completely pale solid pith. The original SDF v8 rest-space field already supports arbitrary cuts. Test an original artist-defined, tapered **annular blue-channel tissue field** around the fruit axis, not new cells, without rewriting the SDF or the achene/vascular graph. Source `R` vascular intensity and `G` mottling are unchanged; cut geometry and normal relief are unchanged. Pale pith tint is adjusted with that field. These are **ARTIST** parameters, not calibrated botany.

[Independent Python/Blender build](probe_annular_sheath.py) uses the saved v8 Blender scene and writes a separate editable scene; it refuses to overwrite an existing result. [Cut-pose comparison script](render_annular_center.py) changes the cutter and material **in a background render only** and leaves the saved scene unchanged.

## The key control: pose matters

At the original oblique cutter pose, the ring intersects tangentially and renders as one broad white patch; that apparent failure is not solely the material shader. The plane-face signed distance from point `(0,0,25)` was **-1.7456 mm**. Translate the original cutter by `normal * (-1.7456)` to put the slicing face through that reference axis point (while retaining the same rotation). The rendered blue field now shows two pale bands around a red middle, which is qualitatively closer to the 11 s Frucht frame. Spherical bite still exposes an oversized pale patch. Frucht camera, cutter and lighting are **not** exactly matched.

**Matched real Blender Cycles comparisons, v8 LEFT / annular variant RIGHT** (private owner-only Drive):
- [Central axial planar cut](https://drive.google.com/file/d/1bz0F1TAnON0RR6EmgwCP0cWZDdDSquyT/view), 720 px / 25 samples.
- [Original oblique planar pose](https://drive.google.com/file/d/14CokEupw9Egl_Z4Jk9OEITvPfOvDeHr8/view), 720 px resampled from 860 px / 36 samples.
- [Spherical bite](https://drive.google.com/file/d/16BRnmD7yyJDcyHcGz6niIEPuwywn54N4/view), 720 px resampled from 860 px / 36 samples.
- [Whole experiment folder with editable Blender scene and scripts](https://drive.google.com/drive/folders/1SWWvGQb14qbMNkQ1mh1JoUK9YzsxIsuR). Scene `sha256=4d9c339296b682282a4c48ab988d83e18abd3f1cf1bd0208f006edbd65e1e1bb`; the downloaded Drive scene and both central/bite comparison PNGs passed SHA-256 against the private manifest.

## Geometry verification (Blender 5.2.2, autoexecution disabled)

The evaluated mesh counts and volumes are numerically identical to v8:

| State | Body vertices | Signed volume (mm³ as model scale) | Nonmanifold edges |
|---|---:|---:|---:|
| Whole | 157250 | 21506.8336 | 0 |
| Original oblique planar | 194354 | 6779.2437 | 0 |
| Central-plane pose | 216706 | 8623.2122 | 0 |
| Original spherical bite | 344634 | 18926.0885 | 0 |

All signed volumes positive. The additional centered cutter pose retains **107 seed solids / 19046 evaluated vertices**; **0 retained achene vertices inside** the cuboid cutter. This is a bounded test, not a proof for all arbitrary cuts. The original v8's cutter-dependent seed policy, crown limitations, and SDF smoothing limitations remain.

## Reproduce

From a checkout of this branch with the existing private v8 scene in `build/sdf-vertical-slice/`:

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/probe_annular_sheath.py
$B -b build/sdf-vertical-slice/strawberry-sdf-vertical-slice-v9-core-sheath.blend --disable-autoexec --python experiments/sdf-exterior-2026-11-22/render_annular_center.py
```

**Decision:** this test confirms that cutter placement materially affects the visual diagnosis of the pale rest-space field. It does **not** attain Frucht fidelity. The sheath remains blurred and the bite overly smooth/waxy. Do not merge this experiment or enlarge it into separate whole-fruit cell meshes. Compare at matched cut poses and pursue natural wet fibrous surface detail as a distinct next hypothesis. No commercial Frucht files or GPL Kiwi nodes were copied into this public repository.
