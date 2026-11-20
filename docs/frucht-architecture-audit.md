# Frucht architecture audit — what we know, and what we do NOT (20 Nov 2026)

**Correction to earlier chat descriptions:** We thoroughly inspected the **free Kiwi add-on 0.4.3**, *not the commercial Frucht strawberry source graph*. We cannot claim our M1a/M1b algorithm reproduces the author's strawberry. This document preserves the difference between directly inspected software, the author's published account, and our own inventions.

## Evidence A — original author's strawberry (public explanations, not code audit)

- The original author publicly showed [64 node trees / roughly 7,700 nodes for the strawberry](https://www.reddit.com/r/geometrynodes/comments/1xvpnbt/the_node_trees_behind_the_procedural_strawberry/) grouped into shape, skin, flesh, achenes/seeds, and calyx. The exact full strawberry `.blend`/nodes are not available in the free demo.
- In the [Reddit discussion of the original Frucht video](https://www.reddit.com/r/blender/comments/1xvmtp6/) a technical explanation states the following implementation:
  1. Fruit body mesh and arbitrary closed cutters/knife/bites -> `Mesh to SDF Grid`, `SDF Grid Boolean` set to difference, `Grid to Mesh`; generates an actual closed cut/bite surface.
  2. Pale inner strands: one precomputed **256³ field** in Python/NumPy, packed into a **16×16 slice atlas** read in the flesh shader using *rest-space* coordinates, so fragmented pieces sample consistent internal detail.
  3. Cut face: local subdivision and displacement with **Voronoi cell** pattern, flatter over strands; on top, **three soft Voronoi layers** emulate juicy surface film.
- This is an **author-published technical description**, not an independently decompiled strawberry implementation. We have the film, but **a video proves appearance only, not how nodes are wired**. The author did not provide a free editable strawberry.
- The [methodology study](https://strawberry-methodology.pages.dev/) says coding agents consulted scientific papers on fruit anatomy and measured cut-fruit photos. The user judged anatomy and visual quality; neither was independently scientifically validated. Do not conflate anatomical plausibility with histologically verified morphology. The study also documents `Off/Fast/Exact` options to avoid costly exact cut regeneration.
- **Source does not say** the strawberry uses one explicit vessel curve per achene, nor our particular 3D Voronoi nearest-centre algorithm. Never attribute these algorithms to Frucht.

## Evidence B — exact free Frucht Kiwi 0.4.3 (verified in Blender 5.2.4)

Archive: `frucht-free-kiwi-0.4.3.zip`, manifest `version=0.4.3`, `FRUECHTE=('KIWI',)`, file `daten/kiwi.blend` **only**. A strawberry .blend is NOT in this zip; `formbeere.py` explicitly says the shape berry is full-edition only.

Direct inspection of linked Blender node groups:
- **17 GeometryNodeTree groups, ~2,290 total nodes** (counting each group once); main group `KIWI • Frucht komplett` has 38 nodes, and routes to shape, seeds, half-space cut, seam, cells-at-cut, hairs, calyx.
- `KIWI • Gewebe` 301 nodes: 19 scalar outputs describing inner regions (e.g. `Core`, `Kammer`, `Gel`, `Schale`, `Plazenta`). This is a *spatial field*, not a 3D collection of individual cell membrane meshes.
- `KIWI • Zellen am Schnitt` 244 nodes includes mesh grids, multiple volume cubes/named grids and sampling, `KIWI • Zelltypen`, `KIWI • Zellfarbe`, `KIWI • Leitbündel`. `Zelltypen` uses **five Voronoi Texture nodes**: **three 3D + two 4D**, all `SMOOTH_F1`, plus noise/math layers.
- `KIWI • Leitbündel` 408 nodes: parametric curves, sampled positions, instances and several material-defined strand geometries.
- In the main **Kiwi** tree the visible top-level cut uses `GeometryNodeMeshBoolean` (DIFFERENCE) and `Schnitthalbraum`; this should **not** be mistaken for the exact strawberry SDF technique. However shared add-on Python `schnitte.py` *does* construct `GeometryNodeMeshToSDFGrid`, `GeometryNodeSDFGridBoolean`, and `GeometryNodeGridToMesh` for cut pathways.
- The local Kiwi source documents *a modular procedural node strategy*, **not** the exact shape/seed anatomy of the commercial strawberry.

## Evidence C — our current M1b (direct source audit, not Frucht)

- `src/strawberry_biology.py`: 539 explicit achene anchors + 539 computed curves to a central vascular cylinder; botanically *motivated but uncalibrated numerical parameters*.
- `src/strawberry_cells.py`: **our own Python scalar 3D jittered Voronoi** (nearest two cell centres per sample), and `micro_tissue_color`. It changes cut-mesh vertex position and color; these are **not watertight individual cells**.
- `src/generate_cellular_strawberry.py`: Python generates visible fruit and **fixed longitudinal/transverse slices**; Geometry Nodes used for **achene instancing**. No general-purpose arbitrary SDF cutters, no 256³ precomputed strand field, no 16×16 atlas, and no three-layer procedural juice-film shader copied from Frucht.
- Thus our model is **not** 'Frucht recreated'; it is an independent research design with certain conceptual similarities. Current visual quality is far below Frucht.

## Recommendation — adjust engineering priorities

The biological-atlas-first decision remains useful **for our own goal of anatomical credibility**, but it does **not** faithfully describe the author's rendering pipeline.

Do not try to increase the number of modeled real cell volumes or explicit vascular curves as the first route to Frucht-quality visuals. Instead, investigate these **separate architectural layers**:
1. **Reusable true cutting engine (SDF)**: arbitrary closed cutter mesh → SDF difference → closed cut geometry; test closed surface and different cutter orientations.
2. **Rest-space 3D tissue fields with cache**: give every piece the same original coordinates; benchmark on-the-fly sampling versus one-time NumPy voxel bake (the author's 256³ + atlas is a reference design, not a mandated exact resolution).
3. **Cut-surface detail in Geometry Nodes**: multi-scale Voronoi and measured region masks, displaced geometry only where needed; separate a subtle wetness layer from physical cells.
4. **Separate biological explanation from photoreal mode**: explicit connected vessels may remain as diagnostic geometry; for normal photorealism use plausible volume fields/shader, avoid exaggerated white spines.
5. **Test loop**: compare both projected whole and sliced fruit in equivalent camera/light. Renderer quality before architectural complexity; preserve actual Blender files and versioned Drive SHA manifests.

**Do not claim** these changes have been implemented; treat as a roadmap. No proprietary Frucht code has been transferred into Strawberry Lab.
