# M2c — physically scaled 3D cellular solids and two orthogonal sections

**Date:** 20 November 2026. **Status:** independent Blender 5.2.4 LTS test of *3-D geometric cell solids* generated with cultivar-specific observed **mean diameter**; not an actual histological volume reconstruction.

## Why this is different from M2b

M2b placed isolated, strictly spherical cell-diameter gauges on artificial lattices. In **M2c**, cells are explicit closed 3D ellipsoid meshes with an individual 3D center and three semi-axes (mm). Realized by a **single reusable shared Geometry Nodes group** via named point radii. Mixed *outer pericarp* samples contain large and small cells together, not in separate exhibition boxes. Two **mathematically perpendicular** cut planes `Z=0` and `Y=0` intersect the **same saved 3D cells**. There are no independently painted 2D cross-section textures.

**Critically:** a fully closed 3D mesh is not necessarily a reconstructed living cell. Shapes, 3-D packing, air gaps, sample counts, and the translation of histological 2D diameters to 3D equivalent-volume diameters remain independently selected **ARTIST modelling assumptions**. We do NOT claim true measured 3D cell morphology or porosity.

## Primary scientific inputs and observational level

1. **Jeon, Oh & Song (2024)**, [published full text](https://www.hst-j.org/articles/xml/G2NO/), [DOI: 10.7235/HORT.20240020](https://doi.org/10.7235/HORT.20240020), **Table 5**. Exactly matched untreated 180 DAA *Actinidia chinensis var. chinensis* ‘Sweet Gold’ and ‘Jecy Gold’. These control mean diameters are the **ONLY measured cell geometry used**. [GitHub numerical catalogue](../data/morphometry/measurements-v1.json).
2. **White et al. (2018)**, [ISHS Acta Horticulturae 1218:185–190](https://ishs.org/ishs-article/1218_25/), **abstract**. Describes two coexisting populations in the A. chinensis outer pericarp: relatively large ellipsoidal cells and more isodiametric smaller cells. **Not used to assert any mean diameter for the above named cultivars, or 3-D density.**
3. **A rapid method of fruit cell isolation for cell size and shape measurements (2009)**, [PMC2685799](https://pmc.ncbi.nlm.nih.gov/articles/PMC2685799/), **Fig. 5D–F**. Micrographs distinguish core, inner and outer-pericarp cell morphology; useful qualitative cross-check only. Cells are extracted from fruit; not a preserved exact 3-D packing map.
4. **Hallett, MacRae & Wegrzyn (1992)**, [DOI: 10.1086/297006](https://doi.org/10.1086/297006), **abstract only**. Air-space volume and cell-wall morphology vary with ripening. No numeric void fraction copied, since full quantitative tables are not available here.

| Untreated specimen | Core mean (µm) | Inner pericarp (µm) | Outer small (µm) | Outer large (µm) |
| --- | ---: | ---: | ---: | ---: |
| *Sweet Gold* | 47.3 | 95.9 | 51.4 | 164.6 |
| *Jecy Gold* | 47.4 | 85.5 | 65.3 | 181.5 |

Those observations are 2D section measurements. **Treating their source mean diameter as a 3-D volume-equivalent ellipsoid diameter is an explicit modelling convention, not a biological measurement.** We select ellipsoid axis ratios separately and preserve equivalent volume using the product of the three multipliers. All numeric semi-axes and centers are stored for independent checking.

## Blender architecture and scenes

From source M2b `.blend` (existing M2b clinical reference and 5 generic GN groups unchanged), M2c adds:

- New shared group **`FE M2c | VolumetricCellSolids | shared`**: reads a `FLOAT_VECTOR` named attribute `fe_m2c_half_axes_mm` on points, instances one unit UV sphere scaled by the measured-equivalent semi-axes, realizes **closed 3D solids**, sets smooth shading and one shared object-color material. It is reused for every measured 3D cell population in the scenes below.
- **`06 | M2c | 3D CELL SOLIDS / source diameters`**: core, inner pericarp, mixed outer pericarp, both cultivars; 8 source-point objects, 6 physical sample blocks.
- **`07 | M2c | exact TWO ORTHOGONAL SECTIONS`**: two independent source-coordinate slice orientations for **each mixed 3D block** (4 slice objects). Each ellipse is derived analytically from one original 3D ellipsoid and then projected into XZ display panels solely for viewing. Individual face IDs make every ellipse traceable back to its source cell.
- **`08 | M2c | mixed outer pericarp 3D macro`**: two source-sized mixed volume blocks (4 GN objects), no changes to source cell positions or widths.

Each new Blender scene uses explicit metric units **`scale_length=0.001`**, so **1 Blender unit = 1 millimetre**. The 3-D data archive (`m2c-tissue-volumes.json`, with each cell ID, center and axes) is embedded as a Blender Text datablock and is also exported separately.

## Validation results (real saved .blend reopened)

**Python:** full project test suite **76/76 PASS**, including **18 new tests** for measured diameters, physical scale, non-overlap of large/small cell volumes, exact two-axis ellipsoid sections, source/taxon separation, unknown ripe-strawberry cell dimensions and reproducibility. The original 58 M2b tests are unchanged.

**Actual Blender evaluated geometry:** `validate_m2c_blender.py` reopens the scene; checks shared GN group, 12 evaluated 3D cell objects, per-point source radii, source rows, 4 actual slice meshes, closed cell meshes, **0 non-manifold edges**, and verifies **every vertex of every section ellipse** against its original ellipsoid equation (dimensionless max error < 8e-4; observed ~6.1e-6). Source records are embedded in saved .blend and compared with independent plan JSON.

**Measured output of our generated synthetic sample (NOT a natural cell-count claim):**

| Specimen | Core (3D solid instances) | Inner (3D solids) | Mixed outer (large + small) | Plane intersections (XY + XZ) |
| --- | ---: | ---: | ---: | ---: |
| *Sweet Gold* | 513 | 47 | 995 (11 + 984) | 62 + 62 |
| *Jecy Gold* | 520 | 48 | 308 (9 + 299) | 25 + 28 |
| **Total** | **1,033** | **95** | **1,303** | **177** |

**Six 3D sample blocks, 2,431 independent 3D cell solids, 4 orthogonal displays, 177 true cell-plane intersections**; old M2b diagnostic vessel diagrams and tissue maps remain in the Blender file, not regenerated or falsely calibrated. Independent validation wall ~1.33 s, max RSS ~434 MB on this environment. Three separate authentic Blender Cycles PNG renders: region volumes, mixed outer macro, two-view orthogonal sections.

### Reproduce

```bash
# Use Blender >= 5.2 and the previously published M2b source scene.
# In the checked project environment, use the same primary numeric catalogue.
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
blender -b --python src/build_m2c_blender.py -- \
  --base /path/to/fruit-platform-m2b.blend \
  --catalog data/morphometry/measurements-v1.json \
  --out /tmp/m2c
blender -b /tmp/m2c/fruit-platform-m2c.blend \
  --python src/validate_m2c_blender.py -- \
  --plan /tmp/m2c/m2c-tissue-volumes.json --out /tmp/m2c/validation.json
blender -b /tmp/m2c/fruit-platform-m2c.blend \
  --python src/render_m2c_scene.py -- \
  --mode sections --out /tmp/m2c/sections.png --samples 18
```

## Missing scientific steps — why this is NOT completed anatomy

1. **True tissue packing:** live parenchyma cells form complex polyhedra, cell walls and plasmodesmata; our ellipsoids leave model-chosen gaps. Need actual 3-D volume imaging/serial histological sections for accurate morphology and void fraction. The four source means alone cannot uniquely identify packing.
2. **Regional cell populations in whole fruit:** this is a 0.58–0.80 mm *local tissue sample*, not a 40+ mm full kiwi cellular reconstruction; whole fruit would be too costly at per-cell mesh resolution and require LOD/volume techniques.
3. **Vascular structure:** M2b's existing Camarosa routing is still qualitative, artistic curve geometry; no inferred yellow A. chinensis vascular diameter or pathways from cross-taxon A. deliciosa studies.
4. **Unmeasured tissue depths and species:** ripe Camarosa lacks matched cell diameter measurements. Its real 3-D parenchyma is NOT modelled here. Source measurements of A. chinensis are not generalized to A. deliciosa Hayward.
5. **Different cultivar samples:** the number of selected 3D cells and the implied big/small density ratio are algorithmically generated *artist* settings; they must not be reported as population counts observed in Jeon Table 4 or physiological statistics.

**Next development:** compare synthetic cut microgeometry with actual microscopy using explicit scale bars; research real 3D cell-wall/void statistics before refining packing, integrate a common `TissueVolume` GN field into whole-fruit LOD and then add scientifically justified vascular layers. Cutting remains a shared operation acting on the organ volumes, not a biological group.

## Provenance, files and licensing

- Independent implementation. **No imported proprietary Frucht source or KIWI node tree**; the free Frucht Kiwi 0.4.3 is only an architectural reference and has GPL-3.0-or-later obligations if redistributed.
- Exact project source: [GitHub Strawberry Lab](https://github.com/Dmitry-dev-pet/strawberry-lab).
- Binary `.blend`, Cycles PNG, source-position JSON, log and QA JSON under **owner-restricted Drive** in a new `v0.9-m2c-cell-volumes` version folder; SHA-256 manifest pinned in GitHub after full readback. Original M2b untouched.
- Parent work: [M2b report](m2b-results.md), [anatomy scientific registry](botanical-source-library.md), [morphometry numeric primary records](../data/morphometry/measurements-v1.json).