# Frucht seed-linked vascular network — source & Blender comparison (2026-11-21)

## 1. Source-derived finding (owner-provided Frucht Free Kiwi 0.4.3)

A substantial strawberry-specific implementation is present in the **Python** files of the free archive even though the commercial strawberry `.blend` Geometry Nodes scene is absent.

- In `leitbuendel.py::_enden()` around lines 301–336, the author evaluates `INNEN | vollständige Achänen` as real GN instance pointcloud transforms; each position is offset slightly inside the fruit.
- In `leitbuendel.py::fasern()` around lines 56–81, a set of axial ring carriers is created, then **one curved branch is constructed for each returned achene endpoint**. Branching is core-to-achene rather than free-floating.
- `leitbuendel.py::rechnen()` at lines 120–144 rasterizes the spatial vascular geometry/halos into a 256³ atlas (`16 × 16` tiles in a 4096×4096 image), used as precomputed 3D data by the shader/node logic.
- `fruechte.py::ERDBEERE_EXTRA` around lines 65–74 declares `Vessel Strength` default 1 (0–2; shader); `Vessel Strands` default 28 (6–48); `Strand Width` default 1 (0.3–2.5); `Fiber Width` default 1 (0.3–2.5); `Fiber Sag` default 1 (0–2); `Halo Width` default 1 (0.3–2.5); `Fiber Pattern` default 0 (0–99).
- The UI screenshot at ~00:15 shows orange endpoints on long pale curves. `Core Fibers` is separately visible at ~00:16–00:17; **do not assert its on-screen slider is identical to `Vessel Strands` or any other source control** without the paid UI wiring.

**Answer to “maybe it is just a parameter”:** yes, *quantities, curvature, intensity, seed/pattern* are exposed controls, but **connecting branches to the achene instances is a fixed part of the generator**, not a toggle that magically turns unrelated 3D strands into meaningful fibers. The code computes the network and bakes an atlas from geometry.

## 2. Independent botanical sanity check (not Frucht source)

Strawberry receptacle pith/central vascular cylinder and fibrovascular strands supplying the achenes are established in academic work: [Fait et al. 2008](https://pmc.ncbi.nlm.nih.gov/articles/PMC2556830/) and [Frontiers in Horticulture 2026](https://www.frontiersin.org/journals/horticulture/articles/10.3389/fhort.2026.1779354/full). These do not establish the *exact shapes* of our artist models or of Frucht.

## 3. Grounded comparison to **our** geometry

The baseline Volume First v1 `fine_fibers_3d.npz` contains 494 curves/45,928 spatial samples, but endpoints are independent of the seed positions. The **older** owned M1a → M1e5 file has an explicit `Vascular network | branches to every achene`: 539 17-point splines and a companion `GN live achenes` mesh with 539 separate achene components of 168 vertices each, measured in the uncut frame 1. A one-to-one nearest-center test gives 539 unique matches; source point-to-center distance median **0.00398**, max **0.00497** BU.

Volume First v2 restores a link using this source, while acknowledging different geometry: the 539 M1a seed positions are reprojected into the independent Volume First v1 berry silhouette. The V2 spatial network uses **28 main trunks + 539 branches = 567 curves**, 29,456 sampled 3D points. Every independent branch ends exactly 0.019 BU beneath the corresponding remapped achene marker. All old V1 paths and baseline cut meshes remain in the saved Blender file, hidden in new diagnostic contexts.

Controlled parameter gate: with 14, 28, and 40 main strands, the matched 539 seed endpoints and achene positions are bitwise identical; only carrier count/shape changes. Zero endpoint mismatch in the reopened `.blend`.

## 4. Real visual evidence and limits

- `author-vs-v1-v2-real.jpg`: source Frucht promotional still ~00:15, real v1 494 curve Cycles, real v2 539 seed-linked Cycles. The author frame has a **different camera/zoom and may show a cut animation**; this is morphology comparison, not image-quality A/B.
- `v2-three-blender-views.jpg`: actual v2 only/ghost/cut modes under the saved Blender scene lighting.
- V2 corrects the destination/topology, but looks **too radially uniform and spoke-like**, unlike the author's more independent strongly curved protruding branches. This is not visual parity, not actual tissue histology, not a new volumetric tissue atlas, and not a full cut-surface reconstruction.

## 5. Proposed next experiment

Preserve these 539 anchors while (a) introducing local branching/taper and variable curvature, (b) building 3D tissue fields around the *connected* carrier network, and (c) testing two oriented cuts of the exact same source at fixed lighting. Only then improve SDF performance and runtime cut interaction.

No vendor GPL source, paid model or private reference frame belongs in public GitHub; only report, independent source, metrics, checksums.
