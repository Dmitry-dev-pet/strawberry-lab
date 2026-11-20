# Fruit Engine M2a — explicit contexts + composable organ adapters

**Date:** 2026-11-20  · **Status:** working, source-verified *architectural* prototype in Blender 5.2.4 LTS. **Not** a complete histological fruit generator.

## Why refactor

The open Frucht Free Kiwi 0.4.3 add-on uses one shared runtime with per-fruit `.blend` bundles, recipes and special cases. Our goal is a reusable fruit *anatomical* construction engine with independent, evidence-linked organ topology, not a single enormous Geometry Nodes graph with numeric substitutions. The source audit is [docs/frucht-transition-reconstruction.md](frucht-transition-reconstruction.md); biological distinctions are [docs/fruit-anatomy-map.md](fruit-anatomy-map.md). We did **not** import the Frucht code, node trees or meshes.

## Actual implemented architecture

```text
primary scientific measurements (205 source-table observations)
    | [fruit_morphometry.py exact-context queries]
    v
M1f Specimen(taxon, cultivar, stage, treatment, measured extents)
    |
M2a FruitContext(instance_id, Specimen, seed, detail) — FROZEN
    |
FruitRegistry — instance-owned, immutable map of taxon -> adapter
    +-- StrawberryReceptacleAdapter
    |    +-- measured height/width receptacle + illustrative envelope
    |    +-- rounded study-mean count + illustrative achene markers
    |    +-- source-linked cortex/pith/vascular graph, geometry not yet rendered
    +-- KiwiLocularBerryAdapter
         +-- source-measured radial boundaries of core/inner/outer pericarp
         +-- source-measured cell mean diameters -> calibration gauges only
         +-- locules/placenta/seeds listed, NOT fabricated without data
         +-- green A. deliciosa vascular source remains cross-taxon reference only
    |
FruitPlan(tuple[OrganRecipe], EvidenceStatus, Provenance, VascularEvidence)
    |                      
    v
Blender typed emitter dispatch (NO global current-fruit switch)
    +-- shared 'FE | TissueRegionMaterials | shared' Geometry Nodes group
    +-- shared 'FE | ScatterSurfaceAttachmentMarkers | shared' GN group
    +-- 4 separately tagged Fruit collections in one .blend
    |
    +-- Render / Operations LAYER: Blender Cycles preview and physical gauges

Cuts, animation, GLB exports: separate operations, not biological organs;
NOT implemented in this M2a proof-of-architecture build.
```

**Source:** [src/fruit_platform.py](../src/fruit_platform.py), [Blender composer](../src/build_fruit_platform_blender.py), [saved-scene validator](../src/validate_fruit_platform_blender.py), [Cycles renderer](../src/render_fruit_platform_blender.py), [tests](../tests/test_fruit_platform.py). Existing M1f `src/fruit_engine.py`, `src/fe_geometry.py`, `src/fruit_engine_anatomy.py` are reused rather than copied into a second engine.

### Real independent contexts

| Instance | Taxon and cultivar | Body representation | Source-bound values | Independent seed |
| --- | --- | --- | --- | ---: |
| `cam-a` | Fragaria × ananassa — Camarosa | 3D schematic receptacle envelope + achene markers | 48 × 32.5 mm; 325.6 study-average achenes → 326 illustrative markers | 13 |
| `cam-b` | Same taxon/cultivar | Same measured extent, **different artist arrangement** | Same verified scientific data; independent per-instance state | 107 |
| `sweet` | Actinidia chinensis var. chinensis — Sweet Gold | 2D schematic radial cross-section, no seeds/locules | core, inner, outer radii **3.6 / 14.0 / 21.3 mm**; 4 measured mean cell diameters | 13 |
| `jecy` | Actinidia chinensis var. chinensis — Jecy Gold | 2D schematic radial cross-section, no seeds/locules | **3.0 / 11.6 / 20.7 mm**, four distinct mean cell diameters | 107 |

**Every Blender unit represents 1 mm** (`scene.unit_settings.scale_length ≈ 0.001`). The actual physical dimensions of the four rendered objects and eight micro-scale diameter gauges are measured by the reopened `.blend` validator. The diagram/colours are a schematic visualization of data; it is **not** a simulation of real cells, seed placement or vascular tissue.

## Scientific uncertainty explicitly captured

- **Measured:** Camarosa fruit length/width and study mean achene count (Ariza 2011 Table 2); Sweet/Jecy Gold radial tissue widths and regional mean cell diameters (Jeon et al. 2024 Tables 3/5). Data are selected with exact `source_id/taxon/cultivar/stage/treatment` from [morphometry v1](../data/morphometry/measurements-v1.json).
- **Schematic:** shape curve for Camarosa, marker scattering and size, kiwi circular symmetry and colour. Source tables do not provide exact geometry or fruit-specific seed coordinates.
- **Not constructed (intentionally):** kiwi seed chambers, ovules/locules, vascular route mesh, measured cuticle and vessel diameters, ripe Camarosa 3D parenchyma cell morphology, stem/calyx forms.
- **Vascular reference:** same-taxon strawberry schematic organ graph `S02` may be kept **qualitatively**. Guo et al. K04 measured **A. deliciosa**, not yellow **A. chinensis**; plan marks `CROSS_TAXON_REFERENCE_ONLY` and does **not** attach this graph to kiwi geometry.

## Reproducing / validating

Pure Python, no Blender dependency for core:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
# 45/45 tests PASS (M1f 22 + M2a 23)
```

Blender 5.2.4 LTS:

```bash
blender -b -t 8 --python src/build_fruit_platform_blender.py -- \
  --catalog data/morphometry/measurements-v1.json \
  --out build/m2a --samples 10 --no-render
blender -b build/m2a/fruit-platform-m2a.blend -t 8 \
  --python src/validate_fruit_platform_blender.py -- \
  --out build/m2a/saved-blend-validation.json
blender -b build/m2a/fruit-platform-m2a.blend -t 8 \
  --python src/render_fruit_platform_blender.py -- \
  --out build/m2a --samples 12
```

Actual recorded results: **45 unit tests PASS**, after reopening actual `.blend` **four measured body meshes** (two Camarosa, two kiwi) PASS, **two achene marker GN objects each with 326 markers** PASS, **eight physically scaled cell-gauge meshes** PASS. Two shared Geometry Nodes groups verified, material group applied to 4 bodies, marker group to 2 separate Camarosa contexts. Order-independent plan digest and deep-frozen profile mappings checked. Two Cycles PNG (one overview, one micrometer gauge) are rendered from this file; not ImageGen pictures.

See the generated source-linked `fruit-platform-m2a-plans.json` file for all separate source row IDs, missing data flags, and plan SHA256 fingerprints. The numerical equality of measured bounds/diameters is checked; **there is no assertion that visual appearance is anatomically perfect**.

## Binary storage and reproducibility

Versioned owner-only Google Drive folder: [Strawberry Lab / v0.7-m2a-modular-fruit-engine](https://drive.google.com/drive/folders/1W2tKQx6d6dqxV5ALU-cEAK5TYAWK_aNz). Editable `.blend` and genuine Cycles PNG stay on Drive. Public GitHub contains source, tests, report and `assets/manifest-m2a.json` with final Drive IDs and SHA256, verified after readback. No overwrite of existing M1f/M1a–M1d assets.

## What must be built next

1. Separate **real organ geometry** from schematic render emitters: field-based tissue volumetrics, seed/ovule/locule geometry only when source supports topology; explicit fallback `UNMEASURED` rather than invented shape.
2. General **typed vascular graph engine** with site, geometry, vessel type and anatomical source; avoid transferring A. deliciosa anatomy to A. chinensis as measured truth.
3. Shared Blender GN subgroups with proper **inputs/outputs for each organ and field**, not just two shared material/scatter helpers. Technical Kiwi free design is an inspiration, **not an imported GN tree**.
4. Cross-cutting CUT/LOD/export operations applied **after** anatomy is assembled; can reuse existing independently written SDF code with tests.
5. A fifth fruit should be supported by **registering a new adapter** without modifying the platform or reworking existing species; validate two simultaneous Camarosa contexts and two Kiwi profiles under the same execution.

**Do not close Issues #9, #10 or #11 on this result alone**: the architecture kernel is implemented; the biological model still has major unknown structures and calibration gaps.