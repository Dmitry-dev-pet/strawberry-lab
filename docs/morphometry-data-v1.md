# Morphometry data v1 — measured fruit anatomy (20 Nov 2026)

**This is an evidence registry, NOT a ready-to-render Blender fruit model.** It tracks individual measurements from four primary published works. No commercial Frucht geometry, nodes or source assets appear here.

- `measurements-v1.json`: **205 original numerical observations**, each with taxon, cultivar, tissue, metric, unit, experimental stage/treatment, numeric mean, uncertainty type/value when legible, sample size when known, exact original table, and full source URL in the `sources` mapping.
- `measurements-v1.csv`: the same measurements in tabular form, for manual review.
- `src/fruit_morphometry.py`: retrieval code requiring **exact source, species, cultivar, stage and treatment** so a parameter is never silently taken from a different species or an experimental intervention.
- `presets/`: **evidence snapshots**, *not universal defaults*: `strawberry_camarosa_well_formed.json`, `kiwi_chinensis_sweet_gold_control.json` and `kiwi_chinensis_jecy_gold_control.json`.
- `tests/test_fruit_morphometry.py`: ten source-count, matching, exclusion and unit-conversion tests.

## Four source tables, with direct evidence

### James (1974) — Cambridge Vigour strawberry cortex

Printed p.107, **Table IV.3**, mean cell dimensions in µm (mean ± standard error, 10 observations, 1972). **These are max. length and width of cortical parenchyma cells at maximal fruit girth, not ripe fruit cell diameters**:

| Stage | Length µm | Width µm |
|--|--:|--:|
| A | 41.1 ± 1.7 | 30.7 ± 1.4 |
| B | 59.9 ± 5.3 | 38.2 ± 1.7 |
| C | 109.5 ± 6.9 | 73.6 ± 3.6 |

Stages D and E have **no** measurements in Table IV.3 (the tissue disintegrated during preparation). Table IV.1 (printed p.104, season 1969) contains nominal selection sizes A (2.5 × 1.7 mm), B (5.0 × 3.2 mm) and measured fresh-weight means for C (5.70 ± 0.37 g, n=94), D (8.37 ± 0.26 g, n=72), E (10.84 ± 0.23 g, n=83). The source is the author’s [1974 thesis](https://gala.gre.ac.uk/id/eprint/9233/1/David_John_James_1974.pdf). PDF page-image screenshot attempts failed (cache miss): numbers verified from indexed full extracted text, not independently against the page bitmaps.

### Ariza et al. (2011) — strawberry achene count and fruit dimensions

[Article and Table 2 (p.134)](https://www.researchgate.net/publication/229735697_Fruit_misshapen_in_strawberry_cultivars_Fragariaananassa_is_related_to_achenes_functionality), [publisher DOI](https://doi.org/10.1111/j.1744-7348.2010.00451.x). Means ±SE (n=3 means of field plot replicates; 50 or 30 fruit/plot depending on metric):

| Cultivar, *well-formed fruit* | Length cm | Width cm | Achenes per fruit |
|--|--:|--:|--:|
| Camarosa | 4.80 ± 0.07 | 3.25 ± 0.03 | 325.6 ± 17.8 |
| Medina | 4.99 ± 0.05 | 3.55 ± 0.02 | 335.7 ± 10.3 |
| Ventana | 4.25 ± 0.02 | 3.28 ± 0.01 | 265.3 ± 14.2 |

Misshapen fruit and separate achene size-category counts also included. The paper classifies small achenes **<0.4 mm** and big achenes **>0.6 mm**. These are *size-class thresholds*, **not** the mean dimensions of all achenes. Other achenes can fall between the classes; do not require big+small=total. Source table numbers checked in accessible article text hosted via ResearchGate, not directly against the publisher PDF.

### Currie (1997) — green kiwifruit tissue cell size, experimental treatments

[Massey thesis PDF](https://mro.massey.ac.nz/server/api/core/bitstreams/c524d403-4e01-4d2e-8c09-e0d4057b09b3/content), Chapter 3, **Tables 3.4 and 3.5**. `A. deliciosa`, 150 days after full bloom, girdled shoots at 7/28/56 days and leaf:fruit ratio 1 or 4. Table 3.4 has separate **direction-specific** cell diameters (maximum/minimum equatorial axes); Table 3.5 separates large and small cells in outer pericarp. E.g. 7-day girdling, leaf:fruit ratio **1**: core Dmax 100 µm; core Dmin 55 µm; inner pericarp Dmin 217 µm; outer pericarp Dmin 89 µm; large outer cells 231 µm and small 62 µm. These are *population marginal means*, not untouched controls. The particular chapter 3 cultivar is not confirmed from adjacent extracted methods and is deliberately labelled `cultivar_unverified_ch3` until confirmed. No original PDF pages/plates republished; direct page screenshot failed (web cache miss).

### Jeon et al. (2024) — yellow kiwifruit tissue regions, cell sizes and sampled counts

[Publisher original HTML](https://www.hst-j.org/articles/xml/G2NO/) ([DOI](https://doi.org/10.7235/HORT.20240020)), *Actinidia chinensis var. chinensis*, `Sweet Gold` and `Jecy Gold`, control and 1/2/3 growth-regulator treatments. **Table 3** contains one-sided radial region widths (mm), **Table 4** sampled cell counts, **Table 5** mean cell sizes (µm). Mean ±SE, n=3 for widths; n=10 for sampled cells.

| Untreated (control), 2024 | Core cell | Inner pericarp cell | Outer small | Outer large |
|--|--:|--:|--:|--:|
| Sweet Gold, µm | 47.3 ± 0.2 | 95.9 ± 0.8 | 51.4 ± 1.4 | 164.6 ± 4.7 |
| Jecy Gold, µm | 47.4 ± 0.2 | 85.5 ± 0.9 | 65.3 ± 0.6 | 181.5 ± 4.4 |

Control radial tissue widths (core/inner/outer): Sweet Gold **3.6/10.4/7.3 mm**; Jecy Gold **3.0/8.6/9.1 mm**. These are different cultivars of *A. chinensis*, not the *A. deliciosa* specimens of Currie. The Table 4 typo `35.8 ± .1.5` in Jecy Gold at three sprays/large outer cells is retained as **35.8 with missing uncertainty** (not guessed). The counts refer to the sampled tissue, NOT the total number of cells in an intact fruit.

## Biologically honest engineering use

1. Set real-world coordinate units (`mm` or `m`) before calibrating any Blender scene. Transform lengths only. Old M1a uses arbitrary Blender units and cannot be assumed 1 BU = 1 mm.
2. Seed distributions are *per cultivar and fruit state*; the 539 seeds in M1d are an illustrative implementation value, not a measured Camarosa or Medina average.
3. The available data constrain cell-size distributions and layer-width ratios, but **do not constrain exact intercellular spacing, vascular bundle diameters, achene pit depths, fruit water refraction or calyx thickness** in the sampled cultivar. Those remain uncalibrated until direct numerical tables are found.
4. A single average cell diameter cannot fully define a tissue: anisotropic cell types, variability, area/volume packing and intercellular gaps need additional histomorphometric measurements.
5. Keep **reproducible evidence snapshots** separate from rendering-ready presets: source treatment conditions and uncertainty are non-optional, and no values may leak across taxa or experimental stages.

**Next research:** original ripe strawberry tissue cell-size table in 2023 An et al. (currently abstract only); actual vessel dimensions from matched fruit histology; comparative tissue/vascular cross-sections with scale bars. Do not invent these values or substitute leaves/stems for the fruit.