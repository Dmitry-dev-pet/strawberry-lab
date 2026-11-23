# Live geometric cut relief on the PR31 strawberry

Open `strawberry-exact-cut.blend` in Blender 5.2.2 LTS. The file starts in MATCHED with the original live Boolean, called **Fast**. Use the native View Layer selector to switch among WHOLE, MATCHED, FLESH ONLY and FIBERS ONLY.

For **Exact**, open **Scripting**, select `EXACT_CUT__RUN.py` in the Text Editor and click **Run Script**. In the 3D View, open **N → Strawberry Cut** and choose **Exact** in MATCHED or FLESH ONLY. Move or rotate the Empty in **One shared knife**. The **Relief height (mm)** and **Strand influence** controls default to 0.23 and 0.65. Relief height is a scale for the field. Set height to zero for a tessellated flat cap. Set strand influence to zero to switch off the paths' contribution while keeping the base relief.

**Fast** or **Disable Exact Runtime** restores the native body output. Saving returns the scene to Fast and retains the control values. Reopening the file requires running the Text to opt in again. Undo and redo return the body to Fast. WHOLE parks the evaluated knife outside the fruit, and FIBERS ONLY uses its existing solid-collection exclusions.

## Geometry

This is a method adaptation of the independently owned M1e5 line, not an unchanged transplant of its SDF scene or complete relief graph. It implements local cap refinement, undeformed coordinates and a 3D curve-distance contribution on the current Boolean source. The Voronoi/noise field is newly tuned for this hull. It does not reproduce the old cavity or claim the old scene's exact appearance, biological cells, or a measured tissue surface. The 539 diagnostic anchors remain distinct from the 264 exterior achenes.

The runtime reads the body evaluated by the current native Boolean. It identifies cap faces by material and verifies their knife-local plane and orientation. In knife X/Z, a constrained Delaunay triangulation adds a staggered 0.27 mm sample grid inside the Boolean cap. BMesh replaces only the cap faces and interior connectivity. It reuses the original skin faces and seam vertices, with a sharp normal boundary and displacement fading to zero at the seam over 0.75 mm.

The relief is a rest-space Voronoi ridge and noise field, with a local uplift near the original 28 carrier and 539 branch curves. The 3D query uses the original polyline segments and interpolated bevel radii. The cap moves along the outward normal and retains each vertex's undeformed PR29 rest position as a mesh attribute. A transient copy of the cap material reads that attribute for both original packed atlas lookups. The field and its millimetre settings are artist parameters.

A hidden, derived mesh cache provides the Exact geometry through a temporary modifier on the canonical body. In WHOLE the modifier selects its native input by a View Layer driver. The existing knife, exterior modifiers, and diagnostic materials and sources continue to operate independently. The cache is rebuilt after relevant dependency updates, with a 120 ms queue interval, a pose-and-settings key and a reentry guard. If no cap exists, the body routes through Fast. A reconstruction error removes the cache and switches to Fast.

The local cap sampler limits the candidate grid to 60,000 vertices, including the original cap vertices. Closed topology and positive volume are checked before a cache is displayed. Extreme, degenerate or over-budget cuts can fall back to Fast. Knife changes rebuild synchronously on the CPU once the queued callback runs, so dragging can pause during reconstruction. Visual inspection used the headless Cycles output. The validator exercises the registered operators and drains callbacks queued by actual Blender dependency updates in the headless process.

## Reproduce

Run from the repository root with these authenticated owner-provided inputs.

Install the Python dependencies with `python3 -m venv .venv` and `.venv/bin/python -m pip install -r requirements.txt` when reproducing outside the existing workspace. In that case set `PYTHON=.venv/bin/python` in the commands below. Blender supplies its own Python dependencies.

| Input under `build/inputs/` | SHA-256 |
| --- | --- |
| `pr31-layer-modes.blend` | `509725824a8707aade9ca19153c95b4d2de6a2a5b49a827afbb6c0ca11cb4a53` |
| `pr30-corrected.blend` | `0b8af93c399d0077f51f864f7b9f55673b822a1755e2badcc626f5bfc6256bca` |
| `pr29-original.blend` | `56b6d516e8794fb855512978e90e37cd754374a594fb4c5103e672c960a031cf` |

The owned M1e5 source `m1e5-exact-original.blend` (SHA-256 `2082a81c0d2607faabdefefe0403deed997c703f2c3a1dfe96ea0338e6c4efb2`) provided comparison evidence via the [saved source assessment](../m1e5-integration-assessment/README.md). The builder starts from PR31 and the runtime uses the checked-in adapter source.

```bash
BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
PYTHON=../strawberry-lab/.venv/bin/python
EXP=experiments/integration-exact-cut-v1
OUT=build/exact-cut-v1-reviewed
SCENE="$OUT/strawberry-exact-cut.blend"
export PYTHONDONTWRITEBYTECODE=1

"$BLENDER" -b --factory-startup -t 4 --python-exit-code 1 \
  --python "$EXP/build_exact_cut.py" -- \
  --source build/inputs/pr31-layer-modes.blend --out "$OUT"

"$BLENDER" -b --factory-startup -t 4 --python-exit-code 1 \
  --python "$EXP/validate_exact_cut.py" -- \
  --pr29 build/inputs/pr29-original.blend --pr30 build/inputs/pr30-corrected.blend \
  --pr31 build/inputs/pr31-layer-modes.blend --scene "$SCENE" \
  --out "$OUT/validation.json" > "$OUT/validation.log" 2>&1

mkdir -p "$OUT/renders"
render_one() {
  /usr/bin/time -l "$BLENDER" -b --factory-startup -t 4 --python-exit-code 1 \
    --python "$EXP/render_exact_cut.py" -- \
    --scene "$SCENE" --quality "$1" --look "$2" --pose "$3" \
    --out "$OUT/renders/$4-$1.png" > "$OUT/renders/$4-$1.log" 2>&1
}
for quality in fast exact; do
  render_one "$quality" beauty saved beauty || exit
  render_one "$quality" clay saved clay-saved || exit
  render_one "$quality" clay oblique clay-oblique || exit
done

"$PYTHON" "$EXP/validate_renders.py" \
  --renders "$OUT/renders" --out "$OUT/render-validation.json"
PYTHONPATH=src "$PYTHON" -m unittest discover -s tests -p 'test_*.py' -v \
  > "$OUT/unittest.log" 2>&1
```

Use a fresh `OUT`. Render validation and the contact sheet use Pillow. Each Cycles PNG is produced by its own Blender process with 650 × 650 pixels, 16 CPU samples, seed 1729 and four threads. Both members of each pair use the same knife pose, camera and lights. Clay uses a uniform shader without bump and hides the diagnostic layer collections for that render. The beauty pair uses the scene's original studio and packed atlas.

## Measured results

The editable scene saved with 284 original objects and a 30,242-vertex raw hull. Its SHA-256 is `c6d39d20e90f75826167a5b4345752ef874d62641e0ff428f38a68050ec7da3c`. The validator reopened the file with scripts disabled, then activated the embedded Text twice and exercised the registered quality controls.

| Knife Y, X tilt, Z turn | Fast vertices / triangles | Exact vertices / triangles | Maximum displacement | Fast update / Exact refresh |
| --- | ---: | ---: | ---: | ---: |
| −0.10, 0°, −23° | 17,989 / 35,974 | 38,136 / 76,268 | 0.265 mm | 1.254 / 1.427 s |
| 0, 0°, 0° | 15,311 / 30,618 | 35,746 / 71,488 | 0.262 mm | 1.073 / 1.624 s |
| −0.26, 0°, 0° | 21,554 / 43,104 | 39,149 / 78,294 | 0.264 mm | 1.228 / 1.343 s |
| +0.08, 29°, 32° | 12,553 / 25,102 | 31,321 / 62,638 | 0.261 mm | 1.114 / 1.268 s |

The four Exact meshes each had one connected component, zero nonmanifold edges, positive signed volume, and the same skin faces, pit values and seam edges as Fast. The original source geometry, relative transforms, atlas and exterior solver checks passed. MATCHED and FLESH ONLY evaluated to the same solid. The runtime bypassed the cache in WHOLE and kept the solids hidden in FIBERS ONLY. The checked knife edits include translation, rotation and a change to the stored pose while WHOLE had the effective knife parked. An injected reconstruction error restored the current Fast mesh. A file saved from Exact reopened in Fast.

Zero height produced zero measured displacement. At the oblique pose, strand influence contributed up to 0.069 mm of lift and changed 5,618 cap vertices by more than 0.001 mm. At default settings the clay renders visibly show a fine, pebbled surface. In the same interior crop, 51.3% of saved-pose pixels and 51.4% of oblique pixels changed by more than eight RGB levels. The packed-atlas pair shows the relief over the existing texture.

Refresh timing includes dependency evaluation and cache replacement. The final four-thread validator peaked at 757 MB RSS while other headless renders ran. An earlier isolated refresh benchmark was 0.88–0.91 s; the final pose timings above are 1.27–1.62 s under concurrent load, and some subsequent setting/cache updates took longer. This is not a realtime or interactive GUI latency measurement. The `build/exact-cut-v1-reviewed/` folder contains the scene, six original Cycles PNGs and per-render receipts, `comparison.png`, the validator reports and logs. All 107 existing Python tests passed.

## Review corrections and private artifacts

Independent Astra review confirmed geometry, original source digests, outer corner normals and zero detected nonadjacent triangle intersections on the four tested cuts. Both oblique Cycles re-renders matched the original pixels. It found a stale-cache path when rendering a cut layer while WHOLE remained selected; `on_render` now prepares the unparked cut context and restores the selected layer. `validate_cross_layer_render.py` renders MATCHED and FLESH ONLY after that transition and compares each with a freshly prepared control. Both decoded pixel comparisons pass. Render receipts now record the evaluated knife pose, and validation binds every row to its specified look and pose. See [review resolution](review-resolution.md).

```bash
"$BLENDER" -b --factory-startup -t 4 --python-exit-code 1 \
  --python "$EXP/validate_cross_layer_render.py" -- \
  --scene "$SCENE" --out build/exact-cross-layer-reproduction
```

[Reviewed owner-private Drive folder](https://drive.google.com/drive/folders/1lI2mvbP8d39M5AKvY51VDAcxSLM5FV3E) · [editable scene](https://drive.google.com/file/d/1fwGo8lgKWvBJLv3CkaeyalRVf7CJIvyt/view). The [artifact manifest](../../assets/manifest-integration-exact-cut-v1.json) records hashes and full-download verification. Earlier provisional files remain in the parent Drive folder and are superseded. No Blender binaries or media are checked into GitHub.
