# Strawberry Generator v1 — Fast-only vertical slice

One Blender CLI now generates independent seed/pit/artist-graph populations from JSON recipes. Seeds101 and202 are newly scattered on the authenticated canonical hull; they are not renamed copies of the PR39 population. **This delivery is Fast-only and fixed264.** Exact on the newly refined pit mesh failed its existing seam gate, so the generated scenes explicitly disable it.

[Owner-private outputs](https://drive.google.com/drive/folders/1C88ftQyspZZHHDP8lKZyrzZ-WDl6YDkd). [Seed101 scene](https://drive.google.com/file/d/1mYrvao6nCSIbFguFCbhFgCyUjAl7IVgg/view) and [seed202 scene](https://drive.google.com/file/d/1OBpfUbYXIFbX4KyF_89rUEi7s_Lm0mzn/view).

## Generate a fruit

Use Blender5.2.2 and the owned PR39 input. ZIP contains that input under `inputs-pr39/live-profile.blend`. Its SHA256 must be `481f98534847c7d18d1c1fcc14b9f30403c16099c7b0928b0ecdee13ffde9d95`.

From the repository root, run the same entrypoint for either recipe:

```sh
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/generate.py -- --input inputs-pr39/live-profile.blend --recipe recipes/strawberry-101.json --out build/my-seed101 --render
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/generate.py -- --input inputs-pr39/live-profile.blend --recipe recipes/strawberry-202.json --out build/my-seed202 --render
```

Each invocation writes `strawberry.blend`, `receipt.json`, `anchors.json`, `qa.json` and, with `--render`, native750px Cycles `whole.png`/`cut.png` plus hash/settings receipts. Output directories must be new. A failed gate raises an error; it does not produce a passing receipt. Render failure can leave an already validated scene, so require both render receipts for a complete rendered output.

Recipe fields are `seed`, `achene_count`, `a`, `b`, `h`. Count must currently equal264; unsupported counts are rejected before Blender data is loaded. The existing immutable `fruit_platform.FruitContext` is created with the recipe seed and a unique instance ID. Registry provenance is retained; this does not import M2a's approximate organ counts or claim measured cultivar dimensions.

## What regenerates

1. Restore every canonical body vertex from `pit_base_position`, removing inherited depressions before sampling new pits.
2. Project the existing deterministic area-stratified seeded scatter onto the actual unpitted hull through `HullInMillimetres`.
3. Build a fresh compact `PitField`, refine locally, displace actual vertices, replace `achene_pit`, and clear inherited custom normal data.
4. Create264 fresh editable seed meshes from the repository's owned ovoid emitter. Seat each at the measured triangle floor and apply the existing bounded exposure fit.
5. Rebuild the existing artist graph object with28 trunks and264 branches ending at actual NEW seed-underside vertices. Seed IDs include the new FruitContext instance.
6. Replace canonical live-profile buffers with these newly generated populations. Apply the recipe's nonlinear profile through the existing in-scene operator.
7. Validate actual triangle contacts, endpoint matches, compact pit-field correspondence, three native Fast knife poses and live-profile roundtrip. Save native Fast; render only after validation.

New source anchors and pitted canonical meshes have different digests for seed101 and202. Rebuilding seed101 through the final CLI reproduces its anchor digest, canonical pitted-body digest and vertex count. Binary `.blend` hashes may differ because Blender file metadata is not a deterministic serialization contract.

## What stays template-based

The single PR29 unpitted hull, its inherited topology/refinement, crown, original28+539 diagnostic paths/539markers and packed150³ RGB tissue atlas come from the owned input. Old diagnostics retain their canonical buffers and radii, then follow the recipe's profile map. They remain separate from the newly rebuilt artist28+264 graph. Tissue histology is not regenerated. Seed shape prototypes and artistic graph routing are reused; their spatial population is new.

The nonlinear F/inverse and four native View Layers are preserved. After opening the scene, run `TISSUE_ZONES__RUN.py` to use N → Strawberry Cut → Live nonlinear profile → Apply Profile on the NEW seed population. Native Fast works with scripts disabled. The panel explicitly says Fast-only; Exact activation is rejected with the seam-validation reason.

## Verified limits

| Property | Seed101 | Seed202 |
| --- | ---: | ---: |
| Actual seed/body triangle contacts |264/264|264/264|
| Final body vertices |47,384|45,382|
| Measured canonical pit depth at anchors |0.154–0.208mm|0.153–0.209mm|
| Old-only pit vertices restored to unpitted positions |8,151|7,069|
| Artist terminal/actual seed-vertex error |0mm|0mm|

`verify.py` reopens the baseline and output independently, checks unchanged canonical old diagnostics/packed atlas, then repeats physical contacts, endpoint, field, Fast cuts, inverse shader and live-profile roundtrip checks. Old-only restoration is a **vertex-level** statement; fresh pit interpolation can extend beyond the analytic compact support between vertices. Uncut dimensions are measured from raw physical mesh vertices, not cached Boolean bounds. The original build-receipt dimension metric was corrected after that cache issue was observed; no geometry or PNG changed.

The attempted Exact run failed on seed101's center cap: `The triangulator merged distinct seam vertices`. No CDT tolerance or geometry criterion was relaxed. The failure log is archived. Both final generated populations use explicit Fast-only policy, even if a particular pose might happen to triangulate. A general seam-safe Exact refinement adapter remains unfinished.

All120 prior Python tests plus4 new recipe-boundary tests pass. Final saved scenes are fully downloaded and reopened for verification. Four original750×750/12sample Cycles frames use fixed camera/light. Visual inspection confirms different layouts and real new pits; highlights remain waxy and some pits are coarse/angular. This is not a finished realism claim or a fully general fruit generator.

## Verify a saved output

```sh
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/verify.py -- inputs-pr39/live-profile.blend build/my-seed101 build/my-seed101/reopened-qa.json
PYTHONPATH=src python -m unittest strawberry_generator.test_recipe
```

See `evidence.json` and `readback.json` for actual recipes, hashes, determinism and downloaded-scene QA. Main, previous scenes and the user's GUI Blender remain untouched. No Frucht media, node trees or meshes are included.
