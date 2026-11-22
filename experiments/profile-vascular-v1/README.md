# Partial milestone: artist graph linked to 264 existing seed meshes

This implements the **vascular vertical slice only**, on PR35's two affine presets. Nonlinear morphology is NOT integrated into either delivered Blender scene. The original PR35 pipeline, body/pits, physical seeds, tissue atlas, Fast/Exact and four native modes are retained.

[Private artifacts](https://drive.google.com/drive/folders/1DTunNNJoMj38WIizyvo-q2rt54gHcc8l): two editable scenes, six native 750px/12-sample Cycles frames, QA and ZIP. No Frucht content or GUI Blender changes.

`build_graph.py` authenticates both PR35 inputs and reuses their existing FruitContext. It creates a separate ARTIST graph: one root, 28 linear trunks and 264 terminal polylines. Each terminal has a stable ID derived from an existing seed's object ID; its endpoint is the deepest actual seed-mesh vertex along the saved anchor normal, expressed in the same rest space. Parent selection is rounded azimuth onto 28 trunks—an explicit artistic routing rule, not botanical evidence. Each terminal starts at its exact interpolation position on its parent trunk. Branches are straight radial paths, not measured geodesics. Centerlines are tested against the actual pitted hull; no volumetric lumen/tube-union or watertight vascular export is claimed.

The original 28+539 paths and 539 markers remain untouched, in their original separate diagnostics collections. Their render visibility is disabled to isolate the new graph; viewport geometry is retained. The new object uses the existing shared-knife diagnostic material and collection/View Layer visibility contract. WHOLE hides it, MATCHED shader-clips it, FLESH ONLY and FIBERS ONLY show it fully. Full curves remain in exports. Existing Exact tissue strand influence still uses the ORIGINAL diagnostic network, not this new graph; that coupling remains incomplete.

## Validation and negative run

`validate_graph.py` reopens saved scenes, checks actual spline coordinates against the graph manifest, all 264 unique seed identities, actual seed-vertex endpoints, exact parent attachment, and ray-tests every centerline segment against the body. This does not establish biological vessel anatomy or guarantee the entire bevel tube is interior. The reported exposed fraction in inherited QA is a fraction of seed mesh vertices, not surface area.

`check_source.py` independently compares EVERY original PR35 mesh/curve object's reference coordinates, mesh faces, spline radii/tilts, parent, basis and world matrices, plus material snapshots including color ramps. Exactly one additional graph object is allowed. The unchanged inherited `validate_unified.py` then checks 264 body contacts, original diagnostics, atlas, material graphs, live dimensions, all four layers and two Fast/Exact knife poses per scene.

An initial candidate failed inherited QA with world-map error 0.1848 model units after original diagnostics had `hide_viewport=True`. The final build disables their **render visibility only**, preserving evaluated source transforms. The old validator was not modified or bypassed. The failed candidate is retained locally under `build/profile-vascular-v1`; final artifacts are under `build/profile-vascular-final`.

## Nonlinear blocker, not a completed feature

`profile_probe.py` implements two genuine smooth z-dependent radial maps with analytic inverse and measures residual against a best-fit affine map. This is a numerical probe only. Current Exact (`experiments/integration-exact-cut-v1/exact_runtime.py:129–140`) constructs rest coordinates using `world_to_rest @ body.matrix_world`; its cache key is matrix-based. The inherited cap shader likewise uses an Object-coordinate matrix. Those contracts cannot represent the probe's z-dependent inverse. Merely deforming body/seed meshes would leave cap atlas positions and Exact rest-space distances inconsistent. No nonlinear scene or successful nonlinear cutter is claimed, and no anatomy was substituted.

Visual inspection: whole/cut appearance is inherited. The new isolated graph is visible and correctly connected by IDs, but reads as a regular radial scaffold, not a convincing organic vascular network. Artistic realism remains FAIL; this draft provides an editable engineering slice.

## Reproduce

From this checkout, obtain the authenticated PR35 inputs at `../strawberry-unified-context/build/unified-context-v1/{elongated,round}.blend`. The builder requires absent output scenes and never overwrites earlier assets.

```sh
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/profile-vascular-v1/build_graph.py
python experiments/profile-vascular-v1/run_checks.py
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/profile-vascular-v1/check_source.py -- ../strawberry-unified-context/build/unified-context-v1/round.blend build/profile-vascular-final/round.blend build/profile-vascular-final/round-source-qa.json
python experiments/profile-vascular-v1/profile_probe.py
```

`run_checks.py` runs fresh graph QA, inherited cut QA, whole/cut/FIBERS ONLY renders for each preset. The independent source-preservation check is separate. Existing 107 repository, 8 atlas/receipt and 5 PR35 context tests were rerun. Saved/downloaded graph validation and source-preservation checks are integration tests, not additional unit-test counts. No new full cross-layer pixel regression is claimed in this milestone.
