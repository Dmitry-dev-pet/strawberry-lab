# Geometric achene pits — smaller, reseated engineering candidate

**Engineering QA: PASS. Visual acceptance: NOT ACCEPTED AS PHOTOREAL.** The selected file contains real depressions and correctly seated existing achenes, but several grazing-light rims remain angular/pale. This is a draft integration, not a claim of finished realism. The initial wider/deeper pits were visually rejected. Exactly one narrower/shallower lookdev change was made; a subsequent bounded seating correction repaired its exposure failure without lowering the acceptance threshold.

## Selected editable scene

`build/geometric-achene-pits-seated-v1/strawberry-geometric-achene-pits.blend`, SHA-256 `24a3f7a2b9b157aac3b5a8aa30aa1b84d2404be64df67f74705665de3dbf74b4`.

The file opens in MATCHED with native Fast and scripts disabled. WHOLE, MATCHED, FLESH ONLY and FIBERS ONLY remain native View Layers. The existing knife moves/rotates the cuts. Run embedded `TISSUE_ZONES__RUN.py` and choose Exact to retain PR33 tissue relief and its three controls. Saving restores Fast. Pits are baked into the editable hull; independently moving a seed does not move its pit.

## Actual geometry and seating

- Authenticate the PR33 source SHA `0f552c79054dec8ca82d2891bc2b5d6930eef64bc545e8188d808b946e1c66e2`. Read all264 existing objects and their stored `hull_anchor_rest`, normals, rotations and sizes. Do not generate a second hull, new seeds or new anchor mapping.
- Two local BMesh refinement passes bisect edges longer than0.45mm that cross support. New base samples lie on the original triangle tessellation. The selected hull has38,903 vertices, from30,242 original vertices.
- The independently owned `PitField` supplies inward offsets. Selected footprint radii are72% of the initial wide attempt; input depths0.16–0.21mm are ARTIST. Measured264 floor depths are0.1520–0.2095mm, median0.1856mm. Original vertices outside the field remain fixed;30,140 total refined samples have zero displacement.
- Triangle interpolation has a finite band outside the mathematical ellipsoids. A convex-distance bound measures at most0.4248mm for selected geometry, below the declared0.72mm budget. Do not claim zero displacement at every surface point outside the analytic kernel. Vertex-level zero and triangle-level interpolation are distinct checks.
- Seed seating starts at the actual floor hit plus19% of the original thickness. Smaller pits initially failed Achene026 exposure:38.76% versus the unchanged40% minimum. The builder now fits only a positive lift along the same saved normal, capped at0.04mm, targeting42% exposed vertices. Exactly37 seeds needed a lift, maximum0.02215mm. This is a seating adjustment, not a new lookdev shape or a lowered criterion. Explicit local transforms avoid stale dependency matrices during the fit.
- Final independent triangle-BVH checks show that all264 actual seed meshes intersect the body (79–140 triangle pairs each). Measured exposed vertex fractions are41.57–55.62%; exposed extents0.252–0.395mm, embedded extents0.113–0.195mm. Orientation, scale, IDs, saved anchors and normals remain unchanged. Translation is along the normal, with maximum measured tangential drift about0.00000104mm.
- The original material graphs, eight color ramps, attribute/image bindings, atlas, calyx and stalk remain unchanged. The original pit mask is resampled on the refined hull. Custom smooth normals follow the pit-field slope. Clay plates use uniform material and mute all Bump nodes; independent review of the initial geometry also removed custom normals and still observed real recesses.

## Verification and limits

`validation.json` checks correspondence/area coverage to the original hull, actual inward displacement, finite support, seed seating, retained solids, five native Fast and five opt-in Exact knife poses, one connected watertight positive-volume body, four native layers, deferred knife edits, tissue controls, error fallback and save/reopen. `render-validation.json` records both real cross-layer candidate/control pixel matches. `mesh-contacts.json` records all264 mesh intersections plus rejected detached-seed and ColorRamp mutations. All107 existing Python tests pass.

The material comparator now includes ColorRamp stops/interpolation and attribute/image bindings. Render comparisons bind source hashes and actual frame names, preventing whole/macro receipt swaps. The support metric now measures ellipsoids rather than their enclosing spheres. These fixes address the three independent Astra findings; the original delivered geometry and labels were genuine. Astra reviewed the initial wide attempt, not the final seating adjustment. The parent reran the selected candidate's full QA and independent mesh-contact checks.

The selected macro and clay show tighter contact than the wide craters, but some rims remain visibly angular and pale. No second visual correction or tolerance relaxation was used. The denser initial0.40mm refinement trial had a coincident center-cut seam and was rejected. The first narrow attempt failed exposure and is retained with its failure log. Earlier binaries and PNGs are immutable evidence under their separate build directories. No Frucht media or source is included.

## Reproduce

Blender5.2.2LTS and Python3.11+ with NumPy/Pillow. Outside the existing workspace: create `.venv`, install root `requirements.txt`, and set `PY=.venv/bin/python`.

```sh
B=/Applications/Blender.app/Contents/MacOS/Blender
PY=../strawberry-lab/.venv/bin/python
E=experiments/geometric-achene-pits-v1
O=build/pits-reproduction
BASE=build/inputs/pr33-tissue-zones.blend
SCENE="$O/strawberry-geometric-achene-pits.blend"
mkdir -p "$O/renders" "$O/cross-layer"
blend() { "$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$@"; }
blend "$E/build_pits.py" -- "$BASE" "$SCENE"
blend "$E/validate_pits.py" -- build/inputs/pr29-original.blend "$BASE" "$SCENE" "$O/validation.json"
for frame in whole macro clay; do
  blend "$E/render_pits.py" -- "$BASE" "$frame" "$O/renders/baseline-$frame.png"
  blend "$E/render_pits.py" -- "$SCENE" "$frame" "$O/renders/pitted-$frame.png"
done
for layer in MATCHED 'FLESH ONLY'; do
  slug=matched
  if [ "$layer" = 'FLESH ONLY' ]; then slug=flesh-only; fi
  for case in candidate control; do
    blend "$E/check_cross_layer.py" -- "$SCENE" "$layer" "$case" "$O/cross-layer/$slug-$case.png"
  done
done
blend "$E/check_mesh_contacts.py" -- "$SCENE" "$BASE" "$O/renders" "$O/mesh-contacts.json"
"$PY" "$E/compare_plates.py" "$O" "$BASE" "$SCENE"
PYTHONPATH=src "$PY" -m unittest discover -s tests
```

Every plate is a real1000×1000 Cycles render,12samples, denoise, seed1729, CPU4threads in a fresh process. Beauty whole/macro and uniform bump-off clay pairs have identical cameras and light settings. The six originals, receipts and labeled contact sheet are retained. Their RGB differences prove image changes, not a quantitative realism score.

[Selected owner-private artifacts](https://drive.google.com/drive/folders/1CITiby_t5TDXrqlaQHzk3j5H332RMDDl). The parent folder retains the superseded wide attempt. Public source/QA and the delivery manifest are in GitHub; binary scenes, PNGs and the reproducibility bundle remain private. Main, previous experiments and GUI Blender are untouched.
