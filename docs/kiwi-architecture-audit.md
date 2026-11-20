# M1e research — Frucht Free Kiwi 0.4.3 as an architectural reference

**Status: real source inspected in Blender; M1e architecture redesign NOT yet implemented.** This is a technical, not biological, comparison with our saved M1d model.

## Evidence, version and licensing

- **Original owner-provided source:** `frucht-free-kiwi-0.4.3.zip`, SHA-256 `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877`, size 1,100,729 bytes.
- **Actual Blender node file from that archive:** `daten/kiwi.blend`, SHA-256 `217cd347b593763cad075804da3b4916231c133fae482981a9fbc4714a325791`, size 655,382 bytes.
- **The extension manifest says:** `id = "frucht_free"`, `version = "0.4.3"`, `blender_version_min = "5.2.0"`, **`license = ["SPDX:GPL-3.0-or-later"]`**.
- **Free version includes only Kiwi** (`edition.py: FRUECHTE = ('KIWI',)`; `formbeere.py` reports strawberry full-edition only). The full strawberry Geometry Nodes cannot be inferred by direct inspection of this file.
- **Blender 5.2.4 LTS** was used to load `kiwi.blend` and the saved `strawberry-m1d-half.blend`.
- Exact reference ZIP and Blender asset are preserved in the **private** owner [Drive / reference-kiwi-free-0.4.3](https://drive.google.com/drive/folders/1nmOaAsu06breNDKJxCBTYH8JByEcRRFP), alongside two machine-generated inventories. ZIP and `.blend` were downloaded back; both SHA-256 hashes matched.
- Public code contains only our independent [generic node-audit script](../scripts/audit_node_architecture.py) and these factual observations. No Frucht source code, full graphs, artwork, meshes or binary assets have been copied into this public repository.

## Method

Run on any owned/legitimately inspected `.blend`:

```bash
blender -b --factory-startup --python scripts/audit_node_architecture.py -- \
  --blend /path/to/kiwi.blend --output /tmp/kiwi-inventory.json
blender -b --factory-startup --python scripts/audit_node_architecture.py -- \
  --blend /path/to/strawberry-m1d-half.blend --output /tmp/m1d-inventory.json
```

The script counts stored groups/nodes and descriptive interfaces, and checks which nodes are upstream of each active group output. A reachable node **may still be disabled by selection/conditional fields**; neither node count nor the script measures render time or correctness. Meshes, node link topology, proprietary node settings and embedded textures are **never exported**. The Kiwi file is loaded as a Blender library; even if the host displays “loading empty scene”, its node groups are directly accessible and inventoried.

Direct results:

| Stored groups | Frucht Free Kiwi | Strawberry Lab M1d |
| --- | ---: | ---: |
| Geometry Nodes groups | **17** | **3** |
| Shader group trees | **5** | **0** |
| Nodes in Geometry Nodes groups | **2,290** | **41** |
| Nodes in separate shader group trees | **760** | **0** |
| Total nodes inside stored groups | **3,050** | **41** |

**Do not compare quality from these counts:** M1d uses extensive Python-generated meshes and material-node trees not counted as stored node groups, while Kiwi puts far more work into groups. Material node trees on objects are excluded from both inventories.

## Verified Kiwi structure, from the real Blender groups

| Kiwi node group | Nodes / links | Directly inspected implementation | Relevance for strawberry |
| --- | --- | --- | --- |
| `KIWI • Frucht komplett` | 38 / 68 | **Orchestrator** linked to eight dedicated groups: fruit shape, seed generation, cut half-space, seam/edge fix, cut-cell geometry, coordinate field, hairs and calyx/stem. Inputs include `Schnittebene`, `Schnitt`, `Echte Zellen` and separate fineness controls. The visible root cut uses **Mesh Boolean DIFFERENCE**, NOT SDF. | Build a consistent high-level cut/LOD contract rather than one-off scripts controlling unrelated objects. |
| `KIWI • Gewebe` | 301 / 412 | Spatial tissue function from `Ort` → **19 numeric fields**, e.g. `Core`, `Kammer`, `Gel`, `Schale`, `Plazenta`. Also a separate `KIWI • Gewebe (Shader)` group with 301 nodes. | Keep anatomical tissues as *reusable continuous fields*, separate from their shader appearance. Different strawberry anatomy, not Kiwi-specific fields. |
| `KIWI • Zelltypen` | 154 / 223 | Five connected Voronoi texture nodes: **three 3D, two 4D**, all `SMOOTH_F1`, mixed with noise/math. | Multi-scale/orientation-aware cellular appearance; our isolated nearest-centre Python Voronoi is not the same method. |
| `KIWI • Zellen am Schnitt` | 244 / 371 | **5 Volume Cube**, **4 Store Named Grid**, **4 Get Named Grid**, **3 Mesh Grid** nodes, all reachable from the active group output. Internally calls cell-type/color, coordinate fields and the vascular-bundle group. | Most important gap: dedicated cut-face geometry + per-region volumetric sampling, not only a Cycles cut shader. |
| `KIWI • Leitbündel` | 408 / 555 | **3 curve→mesh pipelines**, with resampling, instancing and realize-instances, controlled separately. Used by the cut-cell group. | Keep vessel paths tied to anatomy but present via a dedicated reusable subgraph. Do not copy Kiwi vascular topology, which is biologically different. |
| `KIWI • Samen` | 257 / 347 | Dedicated seed generator returns **`Samen`, `Huelle`, `Straenge`**; the two latter outputs feed cut geometry (half-space and cells at cut). | Surface attachments and internal cut context should share explicit interfaces; currently our seed mask only filters anchor centres. |
| `KIWI • Griffel und Kelch` | 121 / 145 | Calyx/stem subsystem receives `Schnitt` and a cutting transform alongside the skin. | M1d calyx/stem is static and can appear detached after a strong cut. Make it respond to same cutter. |
| `KIWI • Schnittkante aus einem Guss` | 16 / 18 | Separate modifier section directly after the main Mesh Boolean; includes position/attribute processing. | Treat cut seam/edge as a first-class geometry and test target, not merely a material transition. |

**Additional distinction:** Shared add-on module `schnitte.py` constructs `Mesh to SDF Grid → SDF Grid Boolean → Grid to Mesh` for some cut pathways. **The loaded Kiwi root graph uses ordinary Mesh Boolean**, while our M1d already uses live SDF. Do not claim that this particular Kiwi root graph uses SDF simply because the common Python source contains it. Shared `fast.py` has code for precomputed Geometry Nodes bakes, but these functions were **not shown to be invoked by this exact Kiwi file**.

## What the current M1d scene actually contains

Verified directly from `strawberry-m1d-half.blend`, SHA-256 `8a0a2e945d089bb639ce6aa8e65f42bcdd7f41d45a9256e8f043d3eed08d520d` ([M1d Drive folder](https://drive.google.com/drive/folders/1x4TCZEZM8LEzsK8BFBB0TtHBXTGnWj1m)):

- `M1c | arbitrary-cutter SDF Boolean & material classification` — **19 nodes**, two `Mesh to SDF Grid`, one `SDF Grid Boolean`, one `Grid to Mesh`. This already covers the *basic* SDF cutting idea.
- `M1d | LIVE SDF achene culling` — **14 nodes**, one cutter SDF and one `Sample Grid`. Verified seed count updates with cutter movement.
- `M1d | live anchor diagnostic` — **8 nodes**, independent checking path rather than a production feature.
- Source-code-built tissue rest-space sampling already exists (`64³` PNG atlas), but not a dedicated *Geometry Nodes volumetric tissue/cut-cell subsystem*.
- Calyx/stem are separate mesh objects without a shared live cutting interface. Seed culling uses a **centre-point** signed-distance threshold; the visible achene solid may protrude into the cutter near the boundary. No separate generic cut-edge repair subsystem.

## Gap analysis and proposed M1e work, ordered by benefit

**P0 — same cutter must control all pieces.** Extend one well-defined cutter contract to the actual **body, achene solids, calyx and stem**. Test six poses (3 poses × plane/sphere) using reopened scenes; no floating parts, exact seed-solid crossing policy, watertight main fruit. This is a targeted improvement to [Issue #8](https://github.com/Dmitry-dev-pet/strawberry-lab/issues/8), not a request to recreate all 3,050 Kiwi nodes.

**P1 — a dedicated cut-surface pipeline.** Separate `CutSurface` geometry from the `Body` and `Cutter`, with a clean interface for `rest_position`, `tissue_region`, mesh resolution, boundaries, vein field and `Fast/Exact`. Use one continuous strawberry-specific tissue field, shared between shader and geometry. Validate geometry on 2 nonparallel cuts.

**P2 — reusable named grids and anatomical region fields.** Prototype one or two 3D named grids and sample them at the actual cut face. Measure whether this improves tissue realism and speed compared with our existing 64³ PNG atlas; do **not** assume five grids are needed just because Kiwi uses five.

**P3 — modular rendering/detail controls.** Isolate achene/pit, skin, pith/cortex, vascular strands, calyx and seam into independent testable groups, with *user-facing* Off/Fast/Exact cut quality and a single set of coordinate transforms.

**P4 — independent visual and performance validation.** For each major step: matched-camera Cycles whole/cut PNG, non-manifold scan, 3D tissue consistency, real cutter-motion test, update latency and memory. Keep binary images/.blend in Drive and hashes/evidence in GitHub.

## Boundary of inference

Kiwi is a **technical example of modular Geometry Nodes**, not a biological template for Strawberry. We cannot infer the closed commercial Frucht strawberry uses exactly these 17 groups or this cut method. Its public author-described `256³` precomputed field and multi-layer juice shader have a different evidence basis. [Previous Frucht architecture audit](frucht-architecture-audit.md). The engineering proposals above are **our own inferences** from verifiable source characteristics. The M1e changes listed are **not yet implemented**.

For explicit GPL compliance: the Free add-on declares GPL-3.0-or-later. If we later copy or modify its source/node trees in a distributed derivative, the applicable license obligations must be followed; this audit does not copy them. Our current Strawberry Lab code and the generic audit script are independently written.
