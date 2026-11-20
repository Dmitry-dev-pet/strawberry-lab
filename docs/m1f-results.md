# M1f — physical-scale Fruit Engine, first two species / three evidence profiles

**Built and verified 20 November 2026 with Blender 5.2.4 LTS and Python 3.**

This is the **first implemented, source-calibrated dimensional prototype**, **NOT** a complete anatomical reconstruction or Frucht-quality rendering. The old M1a–M1d files were not modified.

## Input: exact primary measurements and experimental contexts

[Experimental morphometry registry](../data/morphometry/measurements-v1.json) (205 observations) and [source notes](morphometry-data-v1.md). No mixed-cultivar averages or substitute estimates have been used.

| Real measured quantity | Profile | Source rows | Value in the actual Blender geometry |
| --- | --- | --- | --- |
| Fruit longitudinal height | *Fragaria × ananassa*, **Camarosa**, field harvest, well-formed | R0015, Ariza et al. 2011, Table 2 | 4.80 cm = **48.0 mm** |
| Maximum fruit width | Same Camarosa cohort | R0016 | 3.25 cm = **32.5 mm** |
| External achene number per fruit | Same Camarosa cohort | R0017 | observed mean **325.6 ± 17.8 (SEM)**; **326 schematic markers** using explicit rounding, *not a measured individual fruit* |
| Central / inner / outer widths | *Actinidia chinensis* **Sweet Gold**, untreated, harvest 180 DAA | R0110–R0113, Jeon et al. 2024, Table 3 | **3.6 / 10.4 / 7.3 mm**, boundaries at radial **3.6 / 14.0 / 21.3 mm** |
| Central / inner / outer widths | *Actinidia chinensis* **Jecy Gold**, untreated, harvest 180 DAA | R0126–R0129, same source | **3.0 / 8.6 / 9.1 mm**, boundaries at radial **3.0 / 11.6 / 20.7 mm** |
| Mean cell diameters: core / inner / small outer / large outer | *A. chinensis* Sweet Gold, control | R0174–R0177, Jeon et al., Table 5 | **47.3 / 95.9 / 51.4 / 164.6 µm**, converted to **0.0473 / 0.0959 / 0.0514 / 0.1646 mm** |
| Same four cell diameters | *A. chinensis* Jecy Gold, control | R0190–R0193 | **47.4 / 85.5 / 65.3 / 181.5 µm** |

**Physical coordinates:** one Blender unit represents **1 mm**. Both Blender scenes have `scene.unit_settings.system='METRIC'`, `scale_length=0.001`, and `length_unit='MILLIMETERS'`. `cm` and `µm` are converted to `mm` without interpreting weights/counts as lengths.

## One algorithm library, biologically different species profiles

Code modules (independently authored, no Frucht node copies):

- [`src/fruit_engine.py`](../src/fruit_engine.py): typed, source-identified `Specimen`, `Measured`, strict exact-context retrieval and true unit conversions. Unknown fruit length / seed count of yellow kiwi remains `None`, and the cell diameters of ripe Camarosa remain **unknown**.
- [`src/fe_geometry.py`](../src/fe_geometry.py): reusable millimetre-based surface and annular region primitives. Parametric strawberry silhouette and quasi-uniform achene positions are **ARTIST / schematic**, only overall measured fruit extents and rounded achene count are empirical.
- [`src/fruit_engine_anatomy.py`](../src/fruit_engine_anatomy.py): typed organ/vascular graph API. Two distinct reference graphs: **Strawberry**, from Darrow (1966), figs 19-38/39; **green kiwi *Actinidia deliciosa***, from Guo et al. (2013), figs 1–5. **IMPORTANT:** the latter is a qualitative reference for a **different species** than measured yellow *A. chinensis*, and is **NOT** silently applied to either yellow-kiwi geometry.
- [`src/build_fruit_engine_blender.py`](../src/build_fruit_engine_blender.py): first common Blender integration. Creates two reusable *real* Geometry Nodes groups, shared across fruit profiles: `FE | TissueRegionMaterials | shared` (one actual material-index mapping reused in Camarosa, Sweet Gold and Jecy Gold) and `FE | ScatterSurfaceAttachmentMarkers | shared` (schematic outer achenes of strawberry). Other anatomical modules remain in Python; the full modular GN engine **has not been implemented**.
- [`src/validate_blender_profiles.py`](../src/validate_blender_profiles.py): opens the saved `.blend` and tests numerical dimensions, actual GN group links, evaluated material indexes, seed instance geometry, and actual physical size of 8 cell-diameter circles.
- [`tests/test_fruit_engine.py`](../tests/test_fruit_engine.py) and [`tests/test_anatomy.py`](../tests/test_anatomy.py): **22/22 unit tests**, including source exclusion, correct taxon, data absence, mm scale, two graph topologies, achene count, ring boundaries and physical cross-section limits.

## Blender outputs

One editable `fruit-engine-m1f.blend` contains **two scenes**:

1. `01 | Measured fruit organs overview`: three profiles side by side. Strawberry whole surface extent **48×32.5 mm** with 326 schematic external achene markers; two circular **transverse region diagrams** with radii **21.3 mm** and **20.7 mm**, and the original tabulated core/inner/outer widths. A round region is **not** a direct assertion that the living tissue has a perfect circle, and the kiwi's *unmeasured longitudinal length* is intentionally not modeled.
2. `02 | Measured cell diameters only`: 8 circular physical size standards at exact published **mean cell diameter**. **They are reference circles, not real cell membranes, packing or cell counts.** No false claim of reconstructed histology.

Two images are **actual Blender Cycles renders**, not ImageGen or fabricated previews. Color is for interpretation only; it is **not measured pigment/material output**.

### Verification

- Python 22/22 tests **PASS**.
- Actual `.blend` reopened in Blender 5.2.4: **PASS**, two scenes and two distinct Geometry Nodes groups.
- `TissueRegionMaterials` used by all **three** fruit objects, each evaluated material index (0/1/2) verified for both kiwi diagrams, **192 faces per region**.
- Camarosa geometry measured **48.0 mm** height and **32.5 mm** width; **326** source-rounded achene anchors, **3,912** vertices in evaluated marker output.
- Both kiwi radial boundaries verified against original source values; micro-diameter markers checked geometrically to **1 µm tolerance or better** (actual code tolerance 0.000001 mm).
- JSON source data read through published exact-context catalog, no fabricated numeric values for vascular diameters, ripe strawberry cell sizes or kiwi seed locations.

The asset manifest in [`assets/manifest-m1f.json`](../assets/manifest-m1f.json) will record SHA-256 hashes for source-preserved Drive files. Full reproducible build:

```bash
# In a clean checkout of Strawberry Lab, Python 3.10+ plus Blender 5.2.4
python -m unittest discover -s tests -p 'test_anatomy.py' -v
python -m unittest discover -s tests -p 'test_fruit_engine.py' -v

blender -b -t 8 --python src/build_fruit_engine_blender.py -- \
  --catalog data/morphometry/measurements-v1.json --out build/m1f --samples 20

blender -b build/m1f/fruit-engine-m1f.blend -t 8 \
  --python src/validate_blender_profiles.py -- \
  --out build/m1f/blender-validation.json
```

**The Blender file may not reproduce byte-for-byte** in a different environment. Validation is by geometry, source provenance, actual GN groups and saved artifact SHA-256, not binary-deterministic `.blend` builds.

## Boundaries / next scientific work

- **Not a histological reconstruction.** Full strawberry cell populations, vascular diameters, epidermis thickness, intercellular porosity and achene geometry are not calibrated. As before, we avoid “making it look scientific” using invented precision.
- **Not a full kiwi.** These are region-thickness diagrams from a cross-section; no arbitrary longitudinal shape, locule/seed geometry, sepals or vascular curves are claimed for *A. chinensis* based on unrelated studies.
- **Not yet fully GN-modular.** Only two shared Blender Geometry Nodes groups exist; organ taxonomy/vascular graphs are currently independent Python specifications, and Cut/Render are not built as one reusable graph hierarchy.
- **No tissue cell populations generated from a mean alone**: morphology/variance/packing must come from additional primary histology.
- **Vascular structures remain qualitative**, backed by Darrow and Guo; the *A. deliciosa* graph is a reference and must not be assumed identical for measured yellow *A. chinensis*.
- **Next priority:** obtain direct comparable histology for ripe Camarosa cortex and *A. chinensis* vascular/seed organization; validate actual cell shape and cut-face topologies, then implement one new shared `TissueDomain` GN group rather than duplicating species-specific pipelines.