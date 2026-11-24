# Reference-first reset: original Frucht runtime, 24 Nov 2026

Owner-approved methodological reset after the integrated PR50 scene and skin-only negative control. Freeze the integrated scene as the technical control, not as a visually accepted product: SHA-256 `790dc4adbd9025b56e7833c2cedb8ada83c0e9b738ac294f96889fbb52e0e215`, owner Drive file `1EHj1K923RxqkgMVJFTBof1mhUMHLgh9K`; local original hash independently rechecked. No new Strawberry geometry, shaders, parameter sweep, merge, or commercial Frucht reconstruction in this experiment.

## Evidence boundaries

The exact owner-provided Frucht Free Kiwi 0.4.3 ZIP (`aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877`) was re-extracted; original `daten/kiwi.blend` SHA-256 `217cd347b593763cad075804da3b4916231c133fae482981a9fbc4714a325791`. Manifest: GPL-3.0-or-later. The full commercial strawberry blend is absent. Only the available Kiwi runtime was executed. No protected/paid feature bypass, source/tree export, copied assets or borrowed presets in Strawberry Lab. The two included probe scripts are our original inspection harnesses, not a fruit implementation. Reference snapshots and logs stay private. See the earlier `docs/kiwi-architecture-audit.md` (library-only inventory), `experiments/sdf-vascular-topology-audit-2026-11-23/README.md` and `experiments/sdf-exterior-audit-2026-11-24/README.md` for narrower source findings. Do not generalize Kiwi-specific tissue anatomy or exact Boolean path to the missing strawberry scene.

## Source-backed build sequence, not a speculative node reconstruction

1. `neu.py:210–301`: load species package collections, groups and worlds; assemble instance root and display sources. Important: author starts from a real authored parametric template, not a Python script creating every mesh/node from nothing. Strawberry-specific initialization references a missing commercial template; Python fragments alone cannot recover all its geometry.
2. `form.py:164–223`: in the strawberry path one shared point mesh carries achene positions and normals sampled along a meridional area proxy; pit placement and shape share it. `formen.py:102–190,426–440,652–685,730–765` separates common forward transformations of meshes and instances and a strawberry-specific inverse-coordinate path. Kiwi deformation is simpler; its dimensions are not strawberry presets.
3. `jobs.py:437–574`, `spawn.py:583–600`: neutral source geometry, separate packed geometry bakes for whole fruit and leaves, and invalidation keys that distinguish exterior, foliage and interior. Source geometry can remain cached while the live shape map changes. Interior cache is produced when needed; there is no requirement to compute it in initial placeholder mode.
4. `schnitte.py:721–797,922–1025,1027–1130,1170–1255`: **Fast pathway is hybrid**. Original exterior mesh and instances use a cutter field and deletion/edge handling; independent flesh source stores a named SDF grid; flesh surface uses grid difference and remeshing. In the available runtime the exterior modifier has one MeshToSDFGrid (the cutter), one SampleGrid, two DeleteGeometry nodes and no GridToMesh. The independent flesh surface modifier has MeshToSDFGrid, GetNamedGrid, SDFGridBoolean and GridToMesh. Skin and flesh are not merely differently assigned materials on a single globally remeshed mesh. Kiwi exact root contains MeshBoolean; do not call the entire reference SDF-only. A separate exterior/flesh architecture may remove our pit-erasure problem, but needs independent edge/overlap/cutter QA. It does not guarantee the same behavior in every Frucht mode.
5. `schnitt.py:30–56`, `schnitte.py:273–285,572–592`, `api.py:284–304`: display policy (placeholder, fast, exact) explicitly depends on fruit and cutter; exact Kiwi only supports one plane, not a bite. Shared add-on `leitbuendel.py`, `zellen.py`, `saft.py` and available `daten/zellen_saft.json` provide partial evidence for the strawberry cut-surface/optical mechanisms (previous audits). The complete commercial skin/pit, tissue, color and material graphs remain unavailable; no claim to have reconstructed them.

## Executed original add-on, not just a library read

Blender 5.2.4 LTS `cd5dc428cce1`, four requested CPU threads, separate Xvfb GUI session because the original packed geometry bake uses modal operators; autoexec disabled. Explicitly imported the exact original add-on locally and used its own API. Set resolution to 40% for bounded runtime, paused automatic viewport quality switching, otherwise no changes to reference code or node graphs. Start with empty scene. All times are observations of this test harness (including polling and updates), not benchmark comparisons to Strawberry Lab.

| Observation | Body verts | Body faces | Outside cache valid | Inside cache valid |
|---|---:|---:|---|---|
| Whole Placeholder | 25879 | 26106 | yes | no |
| Radius 2.55 -> 3.0 | 25879 | 26106 | yes | no |
| Radius reset | 25879 | 26106 | yes | no |
| Whole Fast | 25879 | 26106 | yes | yes |
| Plane Fast | 13283 | 13282 | yes | yes |
| Plane Exact | 117889 | 147227 | yes | yes |
| Requested plane rotation Exact | 117889 | 147227 | yes | yes |
| Bite Fast | 25432 | 25602 | yes | yes |

Original evaluated whole size changes from [5.19471,4.89443,6.86249] to [6.11142,5.75815,6.86249] and back after radius reset (model units). The 7473 instances counted by the reference API include hairs and other instances, **not 7473 seeds**. Whole Placeholder shows packed exterior bakes and no inside source. Fast creates separate flesh form and source; plane Fast separately exposes 42814-vertex flesh surface and bite Fast 66234-vertex flesh surface. Exact mode on the initial plane yielded a much denser evaluated original root. The requested subsequent rotation was accepted by API but mesh counts/dimensions stayed unchanged at the next tick: **geometric rotation NOT confirmed**, despite successful return code. Exact bite rejected with explicit expected unsupported-mode message. End receipt at 62.471 s. No exhaustive QA of the original model, no performance/visual parity claim, no new Cycles renders in this audit. Some hidden original objects are not evaluable in Fast and the probe records those exceptions as unavailable, not passed mesh tests.

Independently reopened saved original bite scene with autoexec disabled and inventoried actual runtime modifiers (see `summary.json`). This validates the two different skin/flesh paths rather than inferring them merely from shared Python code.

## Next gate: reconstruct architecture before more lookdev

Do not resume isolated pigment/coat/pit adjustments or tune the integrated scene's numerical constants by default. First map **all** known dependencies between the strawberry template, source anchors, common shape/rest-space map, source organ caches, separate skin/flesh cutter paths, cut-face cell/juice stages and materials. For each mark `SOURCE_EXECUTABLE`, `KIWI_RUNTIME_CONFIRMED`, `STRAWBERRY_FRAGMENT`, `MISSING_TEMPLATE`, or independent `PROPOSED`. Build no substitute for a missing node graph merely because it has a similar label. Keep current integrated scene unchanged and keep all negative controls.

The next independently authored test should be a minimal neutral-shape/exterior and separate interior path that uses a common transform and a single cutter, compared against the frozen integrated control. Design the interfaces before generating more surface detail. Only proceed to cut cells, materials, and quantitative visual comparisons after the independent shape/skin/seed contract and separate flesh/skin edge contract have passed. Keep biological anatomy fruit-specific; do not copy Kiwi's tissues or declare the commercial strawberry architecture fully known. This is a proposed research order, not a new adopted `main` ADR or implementation. Existing Issue #9 (modular architecture) and #8 (cut quality) remain relevant; no duplicate implementation or new PR required.

## Reproduce

Unzip the original authorized package privately into `/private/frucht_free/`. Run the independent probe with a fresh output directory:

```sh
export FRUCHT_PRIVATE_PARENT=/private
export FRUCHT_PROBE_OUT=/private/probe-output
export LIBGL_ALWAYS_SOFTWARE=1
mkdir -p "$FRUCHT_PROBE_OUT"
timeout 165s xvfb-run -a -s '-screen 0 1024x768x24' /path/to/blender --factory-startup --disable-autoexec -t 4 --python probe.py
/path/to/blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python graph_probe.py -- "$FRUCHT_PROBE_OUT/original-kiwi-bite-fast.blend" "$FRUCHT_PROBE_OUT/runtime-graphs.json"
```

Probe emits aggregate receipts and private reference snapshots; do not publish snapshots or full node trees. Exact motion remains a separate unresolved probe. No actual original commercial strawberry run was performed.
