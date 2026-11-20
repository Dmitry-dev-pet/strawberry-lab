# Fruit Engine M2b — reusable biological GN components (20 November 2026)

**State:** reproducible, editable **Blender 5.2.4 LTS** exploratory implementation, but **NOT microscopic tissue reconstruction, NOT accurate vascular geometry, and NOT Frucht-quality photorealism**. Built from the independently verified M2a scene; the prior v0.7-M2a and M1d source/binaries were not modified.

## Implemented: three *real* reusable Geometry Nodes modules

| Group | Real GN role | Real per-instance source data | Scientific limitations |
| --- | --- | --- | --- |
| **FE M2b · TissueRegionField** | Reads spatial Position and 4 named FACE attrs; computes radial distance; classifies every face via shared comparison/switch chain; stores a new integer FACE attr `fe_m2b_tissue_region` | Yellow *A. chinensis* Sweet Gold + Jecy Gold core/inner/outer bounds, **Jeon et al. 2024 Table 3**. Identical GN group used by all **four** main fruit bodies. | Camarosa **has no measured internal radial boundaries** in this dataset: faces remain unclassified tissue-domain 0. For Kiwi, exactly three **concentric** schematic zones represent only the *radial transect means*, not real locules. |
| **FE M2b · CellPopulation3D** | Geometry Nodes instances an actual UV-sphere mesh at every supplied cell-centre point. A `fe_m2b_cell_diameter_mm` POINT attr independently controls sphere scale (1 Blender Unit=1 mm). Shared GN group used by **eight** sample objects. | Original **MEAN diameters** of 4 tissue classes, Sweet Gold and Jecy Gold untreated, **Jeon et al. 2024 Table 5**, source rows retained on each Blender object. | The input 3-D point lattice, 1.10 × spacing, spherical proxy shape, counts and packing are **artist diagnostic choices, NOT histological data**. These are small (0.63 mm) diagnostic samples, not real reconstructed total cells. No Camarosa spheres (no matching ripe cortical sizes). |
| **FE M2b · VascularGraph** | A reusable Curve→Mesh tube subgraph applied to two separate Strawberry schematic curve graphs, source relationships stored as typed edges | **Darrow 1966, Figs. 19-38 and 19-39 (S02)** support qualitative central-bundle→surface-achene connectivity; the two instances reuse the exact same GN group. | All curve point positions and **0.16 mm visible radius** are **ARTIST rendering aids, NOT measured vessel topology/diameter**. The available Guo 2013 vascular work concerns *A. deliciosa*, not the two yellow *A. chinensis* cultivars. **No yellow-kiwi vessel geometry created.** |

Important technical detail: in the supplied Blender 5.2.4 runtime, modifier dynamic IDProperties cannot be written using `modifier[socket_id]`. To avoid per-species duplicated groups, TissueRegionField consumes **FACE named attributes** on the fruit mesh and CellPopulation3D consumes **POINT named attributes** on the input point cloud. The exact same `NodeTree` datablock can therefore be used with different cultivar measurements. This design also prevents process-global active-fruit state.

## Direct Blender evidence

The generated `.blend` has **4 scenes** and **5 Geometry Nodes groups**: the two M2a reusable groups plus the three new M2b groups.

| Saved scene | Content | Verification |
| --- | --- | --- |
| `01 | Fruit Platform | 4 independent contexts` | original two Camarosa + two measured yellow kiwi profiles, with new tissue classification modifier on each body | **4/4 PASS**. Sweet Gold and Jecy Gold each produce **180 + 180 + 180** classified faces (core, inner, outer), identical to the measured-band input mesh; Camarosa remains **7800 faces** all in region 0, without invented pith widths. |
| `02 | Cell size calibration, not histology` | M2a source size gauges | Preserved unchanged. |
| `04 | M2b | 3D cell diameter proxies NOT histology` | 8 real 3-D cell-population GN objects, 4 per measured kiwi cultivar | **8/8 PASS**: every evaluated mesh's X-axis extent equals the predicted physical sample span to less than 0.0025 µm, within floating-point precision; each population source measured mean is precisely linked to the Blender point attribute and a source row. |
| `05 | M2b | vascular graph QUALITATIVE` | two illustrated Camarosa central axis + 12 branches, same shared Curve→Mesh group | **2/2 PASS**, each with sourced qualitative edge metadata; no fabricated *A. chinensis* vascular mesh. |

**Source values encoded in Blender objects** (micrometres, **mean ± SE** from the source table, only the mean controls geometry):

| Control cultivar | Core | Inner pericarp | Outer pericarp SMALL | Outer pericarp LARGE |
| --- | ---: | ---: | ---: | ---: |
| *Sweet Gold* | 47.3 | 95.9 | 51.4 | 164.6 |
| *Jecy Gold* | 47.4 | 85.5 | 65.3 | 181.5 |

**Underlying source:** Jeon, Oh & Song (2024), *Response of Fruit Growth and Quality to the Spray of Plant Growth Regulator in Yellow-fleshed Kiwifruits*, *Horticultural Science & Technology*, **Tables 3 and 5** — [original publisher page](https://www.hst-j.org/articles/xml/G2NO/). Controls were untreated; do **not** mix with regulator-sprayed measurements or with *A. deliciosa*. Strawberry connection reference: George Darrow (1966), *The Strawberry*, Figs. 19-38/19-39 — [USDA PDF](https://www.nal.usda.gov/sites/default/files/speccoll_guides/Darrow_TheStrawberry.pdf). Our source-local annotations: [fruit anatomy map](fruit-anatomy-map.md) and [measurement registry](../data/morphometry/measurements-v1.json).

## Actual tests and rendering

- **58/58 full Python tests passed:** previously verified M2a module suites (45), plus **13** tests for tissue evidence isolation, exact Sweet/Jecy means, missing ripe strawberry cells, no cross-taxon vessels, numerical bounding boxes and typed vascular source contracts.
- A fresh Blender process reopened the saved M2b `.blend` and executed [src/validate_m2b_blender.py](../src/validate_m2b_blender.py): **4/4 tissues**, **8/8 real 3D cell proxy meshes**, **2/2 vascular meshes**, **5/5 shared GN node groups**. Check uses evaluated depsgraph geometry, not screenshot guesswork.
- Actual Blender Cycles CPU renders (not ImageGen):
  - `fruit-platform-m2b-cells.png`: 1820×920, 14 samples, ~13.3 sec, peak RSS ~1.99 GB;
  - `fruit-platform-m2b-vascular.png`: 1500×740, 14 samples, ~8.2 sec, peak RSS ~1.35 GB.
- The earlier M2a overview and gauge scenes were retained within the new editable `.blend`, but their old PNG files are not duplicated in M2b.

## Rebuild in a clean workspace

The scripts depend on **existing public M2a source files**; do not copy them back under new filenames:

```bash
# Starting from the Strawberry Lab GitHub source tree
export BLENDER=/path/to/blender-5.2.4/blender
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v

# Build the M2a base from source and the source-linked 205-row measurement JSON
"$BLENDER" -b --python src/build_fruit_platform_blender.py -- \
  --catalog data/morphometry/measurements-v1.json --out /tmp/m2a --samples 10 --no-render

"$BLENDER" -b --python src/build_m2b_blender.py -- \
  --base /tmp/m2a/fruit-platform-m2a.blend \
  --catalog data/morphometry/measurements-v1.json --out /tmp/m2b

"$BLENDER" -b /tmp/m2b/fruit-platform-m2b.blend --python src/validate_m2b_blender.py -- \
  --out /tmp/m2b/validation-m2b.json
"$BLENDER" -b /tmp/m2b/fruit-platform-m2b.blend --python src/render_m2b_scene.py -- \
  --name cells --out /tmp/m2b/fruit-platform-m2b-cells.png --samples 14
"$BLENDER" -b /tmp/m2b/fruit-platform-m2b.blend --python src/render_m2b_scene.py -- \
  --name vascular --out /tmp/m2b/fruit-platform-m2b-vascular.png --samples 14
```

The ZIP-free source code is written independently. No Frucht Kiwi/paid-strawberry node tree, meshes, textures or addon code is included. No claim that `.blend` byte-for-byte hashing after rebuilding is stable.

## Remaining work — keep Issue #12 OPEN

1. Source-grounded **real 3D** tissue domains beyond radial annular schematics (actual locules, placenta, septa, vascular ring, volume cell populations), calibrated to matching histological figures and tables; no default guessing for missing measurements.
2. Cell packing, anisotropy, wall thickness and air spaces backed by species/cultivar/stage evidence. **Currently source mean diameters are exact but the packing itself is only an arranged 3-D demonstration**.
3. Vessel axes/path radii and real segmented network positions from matched specimens, or explicitly disable anatomical tube geometry. Current illustrated golden paths are **not true anatomical estimates**.
4. The complete per-fruit GN-composed anatomy, reproducible shader/GLB export and true generic cutter operation remain separate integration tasks. Do not celebrate one shared node group as a full biological model.

[Source architecture and limits](kiwi-architecture-audit.md) · [scientific source library](botanical-source-library.md) · [M2a baseline](m2a-results.md) · [Issue #12](https://github.com/Dmitry-dev-pet/strawberry-lab/issues/12).