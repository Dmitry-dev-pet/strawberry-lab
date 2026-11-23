# Strawberry Lab v19 — rooted 3D fiber graph + cutter-dependent solid retention

**Date:** 23 November 2026. **Result:** independently verified 3D topology/field and true Blender SDF effects; **VISUAL FAIL**, **STRICT CUT-CONNECTIVITY FAIL**. Research-only, not a release or merge candidate.

## Hypothesis

Test whether a persistent, rooted spatial fiber scaffold with one terminal route to **each of the 264 actual strawberry achene anchors** can make cut flesh more convincing than the noise-deformed surface of v18. Make the scaffold affect physical SDF geometry, not just a 2D image, and compare identical materials and native cutter configurations. Scope deliberately excludes new taxa, morphometry, GLB, Blender UI refactors, renderer changes and proprietary Frucht code.

## Inputs, provenance and limits

- **Original owner v12** editable scene SHA-256 `300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410cbb405b7`, restricted Google Drive. All visual A/B comes from original Blender Cycles, not ImageGen.
- **Immediate input v18A** saved scene SHA-256 `a2e387a13fb12a3d023f6c9d65b23755b6889ade9ad3dc4d4cbfa45c5d96cea0`, which derives from v12. Original v12/v18A and all previous v18 experiments untouched.
- Official **Blender 5.2.4 LTS Linux x86-64**, locally restored from SHA-verified owner-provided 17-part archive. Python NumPy + SciPy for offline graph/field checks, Blender Geometry Nodes for editable SDF. Random seed **19011**.
- All widths, segment controls, material transfer and tube-retention limits are **ARTIST**, not primary-source biological measurements or micro-CT reconstructions. The graph is not proof of true vascular anatomy. No paid Frucht files, GPL Kiwi nodes or reference frames were published.

## Explicit connected graph, not free-floating curves

Input: `achene_center` sampled from the same source mesh (264 authentic *model* achene instances, 178 vertices per instance). Deterministically generated **557 interconnected polylines**:

| Role | Count | Exact relation |
|---|---:|---|
| Central root | 1 | Shared axial stem |
| Carriers | 28 | Begin on an actual sampled root point |
| Terminals | 264 | Begin on an actual sampled carrier point, end at their own original achene center |
| Twigs | 264 | Begin on an actual sampled terminal point |

Algorithmically verified **1/1 rooted graph component**, zero positional error at every parent-child joint, exactly **264/264 achene links**. `v19_graph.py` builds the graph as pure NumPy data; `test_graph.py` has **4/4 independent Python tests passing**, including deterministic regeneration, point-coincident graph joints and finite spatial voxel output. A hidden-but-editable Blender diagnostic curve contains **557 splines**.

The same graph is rasterized as overlapping continuous Gaussian tubular cross-sections in **one fixed rest-space 192³ 3D R field**, 35,003 applied samples and **0 out-of-bounds**. Field SHA-256 `ffe30f3ac3dd75824afb69ca37aa500ab028b0730a40138b9df65af5e95d2eaf`; original atlas G/B/A channels remain **byte-identical in float pixel readback**, including after closing/reopening the Blender .blend. There are **2 material image users and 2 Geometry Nodes sample users of the same packed image**. Original G/B/A readback SHA-256 `ea047ec4df54725a77810d258c436683aa2b78ba5ffab74ca46350d7f3c2550d`.

**Volumetric connectedness:** a 26-neighbor connected-component check of the full 192³ R volume gives **one component** at each R≥0.10, R≥0.25 and R≥0.40. At R≥0.25 it occupies 363,052 voxels (5.13% of grid), all in one component. This tests continuity of the field, **not** connectivity of subsequent cutter output.

## One controlled SDF A/B

Both editable files use identical source mesh, cutter poses, seed masks, source tissue G/B/A, new graph R atlas, materials and SDF grid. The only A→B change is the `V19_SCAFFOLD_SOLID_GAIN` value (both native GN cut groups).

- **v19A (`gain=0`)**: the graph affects rest-space tissue material and cut-cell attenuation but is **not** retained as extra solid when cutting.
- **v19B (`gain=1`)**: the same graph R is interpreted as a tubular implicit 3D solid. `SDF union` retains portions **inside the original fruit body** and at most **0.90 mm beyond the current cutter surface**. This creates **actual physical relief and protrusions** on the cut. Not separate curve tubes pasted on top of a rendered image.

The whole body is unmodified; changing either native plane or spherical cutter recalculates the volume. No autoexecuting scripts are required after reopening. The per-cutter grid is ~140×140×214, approximately 0.27 mm pitch. The analytic graph and volume field are sampled in consistent rest-space coordinates, not repainted for each pose.

**Reproducibility:** the portable builder requires `STRAWBERRY_V19_BASE` to identify the verified v18A .blend and can set `STRAWBERRY_V19_OUT`; a separate run regenerated **the same graph field SHA, R array SHA and unchanged G/B/A SHA**. The saved binary .blend hashes differ across output locations, so do not require byte-identical Blender scenes after relocation; inspect semantic values and evaluated geometry instead.

Saved editable .blend SHA-256:
- v19A: `d89dd750f6f97bd7e85bce55eae0fb58af7d2a1dee9d07dc503932258a8b8110`
- v19B: `ed60ec1b21fdeb98184907391738f31278846c2a04b6176d428127ae3a43d69e`

## Real evaluated Blender geometry — strict result

**Each of five tested poses for A and B** has zero non-manifold edges, positive signed volume, and retained rest-space tissue attributes. Evaluated outputs were read from saved and reopened files, scripts disabled. Moving the plane and sphere changes evaluated mesh geometry. But component-based analysis reveals **severe failure** that a manifold test alone misses:

| Pose | A: vertices | B: vertices | A: components | B: components |
|---|---:|---:|---:|---:|
| Whole | 157,250 | 157,250 | 1 | 1 |
| Plane (initial) | 189,804 | 229,002 | **2** | **24** |
| Bite (initial) | 341,932 | 360,198 | **2** | **11** |
| Plane moved + rotated | 151,000 | 176,206 | **4** | **18** |
| Bite moved + scaled | 352,718 | 385,238 | **3** | **46** |

Physical retained fiber volumes increase signed volume by **170.6194 mm³** (initial plane) and **75.0524 mm³** (initial bite), proving nonzero genuine geometry. However many thin retained islands are not actually connected to the visible intact receptacle. The largest components still contain ~99.3% of B's planar vertices and ~99.9% of B's bite vertices; strict accepted condition is nevertheless **zero detached components**, so **FAIL**. Some min face areas are extremely small (e.g. B plane 5.82e−11 mm²). No production milestone can be accepted on this basis.

Crucial cross-check: the original **v12** evaluated plane and bite each have **1 component**. The intermediate v18A resampling itself introduced a tiny **26-vertex** cap island; v19B's implicit retained solids introduced many more. The detached components are not a property of the source owner scene.

A bounded native Blender GN island-size filter (`Mesh Island` + `Accumulate Field` + `Delete Geometry` for components with fewer than 1000 vertices) reduced A to one connected component in the two original cuts. But **B's filtered evaluation exceeded the experiment's execution limit**; it is not a validated solution, and deleting all short components could also remove legitimate future fragments. No filtered variant is proposed for merging.

## Achene intersection guard

Against the original physical cutter mesh (including the actual ~6,050-vertex scalloped sphere), the existing live retained-seed geometry was checked with a signed nearest-triangle normal test. Across initial/moved planar and initial/moved spherical cutter states, **106,088 evaluated seed vertices checked, zero strictly inside the original cutter**. This is not an exhaustive triangle–triangle intersection proof; the fiber-retention SDF may remain near the original cutter and is a separate surface.

## Genuine matched Cycles A/B — visual result

Four original Blender Cycles CPU frames, fixed **640×640 px, 24 samples**, same camera, light, material and original scene frame for the plane and bite. No AI illustration or postprocessing of source pixels; contact sheet only adds row/column headings. Original source full images and comparison remain in user-private conversation artifacts.

| A vs B actual Cycles pixel change (max RGB difference >0.01) | % |
|---|---:|
| Plane | 13.5203% |
| Bite | 6.6189% |

This is an image-change statistic, **not** a realism metric. On the genuine rendered planar cut, solid-scaffold B looks like **red thorns/caviar** protruding from dense tissue; on the bite, solid projections look like red worms inside a scooped bowl. Both are visually much less realistic than the Frucht reference. **VISUAL FAIL**. A's surface is less physically torn but its cut is flatter and also below the reference.

## Decision and next required mechanism

**Do not merge v19, promote its `.blend`, or present it as Frucht fidelity.** Preserve v12 and v18 controls, and keep the ongoing research draft PR open. The experiment establishes a negative but important engineering fact: **a globally connected root graph AND a globally connected 3D field do not imply a connected cut mesh after a movable knife removes sections of the graph**. A physically plausible tear model must distinguish scaffold segments that remain attached to surviving receptacle from those isolated by the specific cut, and must couple the *cells/tissue surface* to those surviving segments without turning tubes into red spikes. This poses a graph-cut/geometry-connectivity problem, not simply a shader, noise gain or brightness issue. A further test should first enforce pose-dependent attachment and cut topology; only then attempt convincing wet tissue materials.

## Reproduce using documented source

```bash
export STRAWBERRY_V19_BASE=/path/to/verified/strawberry-v18a-source-rest-torn-sdf.blend
export STRAWBERRY_V19_OUT=/path/to/private/output
B=/path/to/Blender-5.2.4-linux-x64/blender
python -m unittest -v test_graph.py
"$B" -b "$STRAWBERRY_V19_BASE" --disable-autoexec --python build_v19.py
for variant in a b; do
  case "$variant" in a) suffix=graph-only;; b) suffix=solid-scaffold;; esac
  scene="$STRAWBERRY_V19_OUT/strawberry-v19${variant}-${suffix}.blend"
  for pose in whole plane bite plane_moved bite_moved; do
    "$B" -b "$scene" --disable-autoexec --python validate_v19_pose.py -- "$variant" "$pose"
  done
  for shot in planar bite; do
    "$B" -b "$scene" --disable-autoexec --python render_v19.py -- "$variant" "$shot"
  done
done
python make_comparison.py
```

Use one fresh Blender process per evaluated pose; combined B run hit an execution timeout after two states, but all five **individual-process** B checks completed. The ignored private artifact package includes `.blend`, original Cycles, field array, graph endpoints, QA JSON, SHA-256 manifest and exact source. No commercial Frucht media or material is in the package. Heavy binaries are **not published in GitHub**; no claim of Google Drive upload is made.
