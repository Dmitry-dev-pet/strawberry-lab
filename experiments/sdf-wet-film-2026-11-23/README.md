# Strawberry Lab — native rest-space wet-film investigation, 2026-11-23

**Engineering status:** tested separate wet-film surface works with the same editable SDF cutters, without modifying the current PR49 v20 core/halo body. **Visual verdict: FAIL / negative study. Do not merge this aesthetic variant into `main`.**

## Where this fits

This is a bounded continuation of stacked Strawberry Lab [PR #49](https://github.com/Dmitry-dev-pet/strawberry-lab/pull/49) on unmerged [PR #48](https://github.com/Dmitry-dev-pet/strawberry-lab/pull/48). We directly inspected the owned v20 bridge scene from [Drive](https://drive.google.com/drive/folders/1OOoU5er3PF4faursFhCbyx9Hgl3_G2AJ), SHA-256 `0b79e33b0725f807524061b1afe79671f4fcf1c6b5c429bd8203cec8d6a21bd2`.

**v21 material audit:** the old research v21 `Math.039 input[1]: .10→.02` was a light **color-outline** mix. In this actually merged generator's cap material, `Math.039 → Math.056 → Bump/Roughness`; Principled Base Color is driven from `Hue/Saturation/Value` reading the original packed 150³ atlas. `Mix (Legacy).004` is absent. Blindly copying the numeric coefficient would modify the wrong signal. `audit_color_chain.py` is a read-only Blender audit and generates `color-chain-audit.json` with this actual link path.

## Exact bounded experiment

Four isolated, saved Blender 5.2.4 LTS scenes, using **exactly one existing edited PR49 scene as the shared source**:

- **A:** separate native film GN object exists but `sdf_wetfilm_gain = 0`, so output is empty. A control for the exact same base body/material.
- **B:** 0.025-mm offset copy of **all** cut-face polygons. Separate film material mixes Transparent BSDF with reflective Principled shader. Original body, source seeds, 150³ atlas and 192³ core/halo unchanged. **Visual negative**: cut turns pale and waxy; an attempted 640×16 B render exceeded the bounded execution window (no claim of a completed high-res B render).
- **C:** patchy film using a **new independent original 3D Voronoi** sampled from the same `sdf_rest_position`, scale 46, local narrow distance mask. **Visual negative**: small white speckles.
- **D:** coarser patches scale 12 and weaker reflectance. **Visual negative**: bright polygonal cell-outline network returns, the precise defect previously reduced in research v21. This is *not* evidence of wet strawberry flesh.

The film is **real evaluated Geometry Nodes mesh**, independently removable and driven by the same cutter through live Geometry Nodes `Object Info`, material-index cut selection, face separation and surface-normal offset. It is a **zero-volume open surface**, **not** closed simulated liquid, not coherent droplets/menisci or measured fruit juice. It is not safe to call it Frucht-like wetness. Original Frucht code, nodes, asset meshes and images were neither imported nor published.

## Independent native QA (saved Blender files, `--disable-autoexec`)

- **A vs B:** 6/6 evaluated states (0.32 and 0.20 mm × whole / plane / open-side bite) preserve identical underlying body vertex positions (SHA-256), count and material cap faces. Film is absent in WHOLE and whenever switched OFF. B film at fine voxel has 37,250 cap polygons on plane and 48,114 at edge-bite, each conforming within 0.06mm of body.
- **A vs D:** same 6/6 checks. D film at 0.20mm has 11,976 distinct cap-patch polygons (plane) and 15,175 (open bite); at 0.32mm 4,789 and 5,983. Body remains byte-identical to A for each pose. Same original materials atlas. Film is open and expectedly not an independent watertight solid; *body* remains watertight (previous PR49 QA).
- Native interactive control, script autoexecution OFF: `sdf_wetfilm_gain=1→0→1` yields exact same film geometry hash after restoration; rotating the plane changes film geometry; switching to the open-side bite updates it. No Python handler in saved scene.
- `audit_color_chain.py` confirms the absence of v21's color-outline chain on the current source.
- Python sources compile; QA and render scripts execute against the exact pinned original scene.

## Real Cycles, matched evidence

- Preliminary **plane A/B/C/D**: 256×256, 4 samples, denoising enabled, fixed Blender camera/lights/seed=1729. This is only to detect obvious gross artifacts.
- Full independent comparison **plane and side-bite A/D**: 480×480, 8 samples, matched camera/light/cutter/color management/seed. Original image receipts record SHA and render time. `compare_wetfilm.py` checks all these settings before creating an editorial contact sheet. Underlying body remains the same, not a model comparison across different fruit scenes.
- `plane A vs D`: 12.21% pixels with max RGB change >10/255; mean absolute RGB difference 3.60/255, Cycles time 7.93s / 7.21s.
- `bite A vs D`: 7.57% pixels changed >10/255; mean 1.98/255, Cycles time 7.17s / 7.87s. Pixel percentages measure effect, **not visual quality**.
- The comparison shows a **false pale cellular mosaic** where the author reference shows integrated, irregular wet torn flesh. **Do not promote A/B/C/D as a positive visual improvement.** The very large bright pith and smooth cup-shaped bite still need anatomical/geometry work.

## Reproduce

All scripts are original project code. With Blender 5.2.4+ and owner-private v20 bridge file, run from the repo root (`B=/path/to/blender`):

```bash
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-wet-film-2026-11-23/audit_color_chain.py -- --scene inputs/v20-bridge-portable.blend --out build/wet-film/color.json
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-wet-film-2026-11-23/build_wetfilm.py -- --source inputs/v20-bridge-portable.blend --outdir build/wet-film/ab
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-wet-film-2026-11-23/build_local_wetfilm.py -- --source build/wet-film/ab/wetfilm-B.blend --out build/wet-film/ab/wetfilm-C.blend
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-wet-film-2026-11-23/build_wetfilm_D.py -- --source build/wet-film/ab/wetfilm-C.blend --out build/wet-film/ab/wetfilm-D.blend
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-wet-film-2026-11-23/validate_wetfilm.py -- --off build/wet-film/ab/wetfilm-A.blend --on build/wet-film/ab/wetfilm-D.blend --out build/wet-film/qa-A-D.json
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-wet-film-2026-11-23/qa_live_controls.py -- build/wet-film/ab/wetfilm-D.blend build/wet-film/qa-live.json
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-wet-film-2026-11-23/render_wetfilm.py -- --scene build/wet-film/ab/wetfilm-D.blend --shot bite --out build/wet-film/bite-D-480.png --resolution 480 --samples 8
```

The code refuses to overwrite primary scene outputs, and `build_wetfilm.py` pins its exact input scene SHA. Binary Blender scene serialization itself is not promised deterministic across hosts; verify evaluated geometry and original Cycles receipts instead.

## Decision and next test, no drift

**Negative mechanism.** Do **not** copy v21 socket values; do **not** add more Voronoi patch-density tweaks. The next distinct hypothesis, if pursued, must create **few geometrically attached liquid menisci/coherent micro-pools tied to already existing 3D rest vascular and tissue domains**, with a measured and bounded material response, instead of rendering polygonal boundaries as liquid. The author video remains a visual reference, not a source of transferable geometry/nodes. Test limited real Cycles plane and edge-bite and original body geometry before any merge.

**This document and scripts may live in draft PR49 as a recorded negative result.** Blender binaries and original images remain in an owner-private Drive folder, with SHA-256 manifest and readback verification; do not publish them to the repository.
