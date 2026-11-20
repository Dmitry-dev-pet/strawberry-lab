# Strawberry Lab — рабочие правила для агентов

## Mission / source of truth
GitHub `main` и Issues — источник истины. История чата не считается документацией или доказательством готовности. Цель: собственный процедурный генератор клубники с качеством, сравнимым с Frucht, но без копирования чужой коммерческой модели.

## Legal / attribution
- Можно изучать опубликованные технические принципы и бесплатное дополнение в рамках его лицензии, но **не переносить** оригинальные Frucht-нодовые деревья, меши, текстуры или закрытые материалы в наш генератор.
- Генератор и рендеры должны иметь явное независимое происхождение. Не выдавать картинки ImageGen за Blender-рендеры.
- Не добавлять лицензию третьих сторон или сторонние ассеты без проверки источника и условий.
- Публичный репозиторий — никаких токенов, ключей, персональных файлов или закрытых исходников.

## Development workflow
1. Читать `README.md`, `docs/quality-plan.md` и текущие Issues перед разработкой.
2. Одно изменение — одна конкретная гипотеза о качестве, геометрии или производительности. Делать ветку и PR, не объявлять MVP «эталоном».
3. Использовать Blender 5.2+ через Python/Geometry Nodes. Сохранять исходный скрипт и параметры воспроизведения. Фиксировать deterministic seed.
4. Проверять на реальном объекте: форма целиком, три четверти, продольный срез, поперечный срез, детали семянок и кожи. Приложить оригинальные рендеры из Blender и журналы исполнения.
5. Сохранять `.blend` как редактируемую исходную сцену для принятых milestones; тяжёлые артефакты — в GitHub Release/Actions artifacts либо документированном внешнем хранилище с SHA-256, не в случайной папке.
6. Измерять как минимум время создания сетки, время рендера, количество объектов/вершин, размер GLB и максимальную память при тяжёлых разрезах. Сравнивать с предыдущим вариантом на одинаковых настройках.
7. Не объявлять успешным этап, если тест не выполнялся. Различать доступность файла, проверку GLB и фактическое изображение в браузере.
8. Не внедрять лишнюю инфраструктуру и не расходовать облачные GPU/кредиты без согласования.

## Architecture target
`shape field -> tissue fields -> feature generators -> true arbitrary cut -> materials -> render/export`. Переиспользовать собственные алгоритмы между фруктами, отделять Blender-зависимые ноды от чистых математических модулей. Разрез должен иметь геометрическую, а не только шейдерную глубину.

## Morphometry v1 — primary numerical tables (20 Nov 2026)

The *measured-data registry* is [data/morphometry/measurements-v1.json](data/morphometry/measurements-v1.json), 205 observations across James 1974 (strawberry tissue), Ariza 2011 (fruit shape/achenes), Currie 1997 (kiwifruit tissue), Jeon et al. 2024 (yellow kiwi tissues under growth regulator). Cross-source authority and limits: [docs/morphometry-data-v1.md](docs/morphometry-data-v1.md). Exact-context API `src/fruit_morphometry.py`, 10 tests in `tests/test_fruit_morphometry.py`, strict evidence snapshots under `data/morphometry/presets/`. [M1f Issue #11](https://github.com/Dmitry-dev-pet/strawberry-lab/issues/11) tracks application to Blender.

**Do not quietly promote samples into global defaults.** Source, taxon, cultivar, organ, tissue, growth stage, treatment, measurement axis, unit and uncertainty must match; missing source values stay missing (e.g. James ripe strawberry D/E cortical cell sizes; typo in Jecy Gold SE). `Currie1997` chapter 3 cultivar remains UNVERIFIED. Define mm→Blender-unit physical scale before sampling cell widths. These values are observations, **not** Blender-calibrated source defaults. Vessel thicknesses and achene pit depth still need matched primary measurements. Datasets + JSON presets are not a finished Geometry Nodes fruit engine; no Blender geometry was modified in this milestone.

## Fruit Engine scientific evidence gate — adopted 20 Nov 2026

**Before refactoring M1d into a fruit-general model, READ:**
- [docs/botanical-source-library.md](docs/botanical-source-library.md) for real scientific books/atlases/histological papers, exact figures/printed pages, specimen limitations and whether a whole chapter was actually available.
- [docs/fruit-anatomy-map.md](docs/fruit-anatomy-map.md) for organ identity, biological origin, tissue regionalization, vascular graph and reproductive topology of strawberry vs kiwi.
- [Issue #10](https://github.com/Dmitry-dev-pet/strawberry-lab/issues/10) — biological evidence prerequisites for [M1e Issue #9](https://github.com/Dmitry-dev-pet/strawberry-lab/issues/9).

**Non-negotiable design rules:**
1. Generic Geometry Nodes = reusable algorithms. Each fruit provides its own *developmental organ origin*, named tissue regions, vascular edge-types and reproductive attachment scheme. Strawberry's swollen floral receptacle and surface achenes are NOT Kiwi's multicarpellate ovary/pericarp with internal locular seeds.
2. Vascular topology comes from specimen-based illustrations (Darrow 1966 Fig 19-38/39; Guo et al. 2013 Fig 5 + microscopy), NOT decorative straight white lines. Preserve edge types, source/sink, and local tissue destinations.
3. Cell morphometry depends on **species/cultivar/maturity and region**. All M1a–M1d numbers (539 achenes, distances, thicknesses) are **ARTIST parameters until calibrated**, never established botanical facts. Do not generalize one 3D Voronoi over every tissue type.
4. Tag every biological claim with source id, exact figure/table/page, taxon and access confidence (FULL, EXCERPT, ABSTRACT, BIBLIOGRAPHIC); never cite a bibliographic-only book as if the inaccessible chapter had been inspected.
5. `Cut`, `Fast/Exact`, rendering and GLB export are **operations after anatomical construction**, not biological organs or modules that define the fruit's identity.
6. Original Frucht Kiwi Free 0.4.3 is an architecture reference only. No copying of its GPL source/meshes into our public code without a deliberate licensing decision.

**State:** this evidence-backed organ map has been written; shared GN fruit-engine implementation and biological validation of numerical values have NOT been completed. Do not report those stages as done.

## State of prototype
- **v0.1 frozen baseline:** `src/generate_strawberry.py` + `src/make_tissue_textures.py`; фиксированный разрез и декоративная 2D карта тканей.
- **M1a live prototype (20 Nov 2026):** `src/strawberry_biology.py` (continuous 3D pith/cortex/epidermis/bundle-zone fields, 539 achene anchors, 539 center-to-achene vessel routes) and `src/generate_anatomical_strawberry.py` (Blender 5.2+; full fruit, longitudinal and transverse cuts, real local pits, GN achene instancing); diagnostic `anatomy.blend` and Workbench view. Code, scene tests and 12 validated Drive assets are indexed in [docs/m1a-results.md](docs/m1a-results.md) and [assets/manifest-m1a.json](assets/manifest-m1a.json).
- **Still NOT true anatomical validation:** capsule/cut cell-scale structure and actual vascular sizes are uncalibrated; two fixed cut planes rather than arbitrary cut. No deceptive claims of Frucht quality.
- **M1b experimental (20 Nov 2026):** `src/strawberry_cells.py` (independent deterministic 3D Voronoi tissue field) + `src/generate_cellular_strawberry.py` (photoreal/anatomy presets; 3 Blender scenes; 2 GLBs). [docs/m1b-results.md](docs/m1b-results.md) + [assets/manifest-m1b.json](assets/manifest-m1b.json). All nine Drive artifacts passed SHA-256 readback, Python tests 15/15. **Cells are implicit 3D fields that modulate cut-mesh geometry and vertex colors, not individually watertight cell volumes, histological ground truth, or photoreal production-ready tissue.** Current data has not established credible macro-scale microstructure. Arbitrary plane cuts are not implemented. Source of anatomy: [docs/strawberry-biology-spec.md](docs/strawberry-biology-spec.md).

**Canonical binary storage**: `Google Drive / Strawberry Lab / v0.2-m1a-anatomy`, restricted to owner. Do not overwrite the previous `v0.1-baseline` or release private reference footage. Publish SHA-256 manifest with verified readback after every Drive upload.


## M1c current (20 November 2026) — SDF + rest-space tissue cache
- Source: `src/bake_rest_atlas.py`, `src/sdf_cut_strawberry.py`, `src/validate_sdf_scene.py`, `tests/test_atlas.py`.
- [M1c results](docs/m1c-results.md) / [Drive asset manifest](assets/manifest-m1c.json) / [Issue #8](https://github.com/Dmitry-dev-pet/strawberry-lab/issues/8).
- Verified: 2/2 true SDF evaluated Blender meshes are watertight, two arbitrary cutter shapes, 64³ rest-coordinate voxel atlas with trilinear shader interpolation, 3 Voronoi wet-surface normal layers, 6 pure Python atlas tests PASS, two scene validators PASS, 11/11 Drive SHA-256 verification PASS.
- Key limitation: achene positions are masked at **scene generation time** based on cutter pose, **not dynamically** when the cutter object is moved later. The live SDF body modifier updates, but GN seeds may then become incorrect.
- Another limit: web-exported GLB has neither Blender's full rest-space sampling shader nor its Cycles normal detail. Do not claim screenshot parity with browser.
- The full strawberry Frucht source remains unavailable; our code is independent and uncalibrated scientifically, not a clone. Next priority after SDF is live seed masking and realistic cut structure, not more node count for its own sake.


## M1d (20 November 2026) — verified dynamic achene mask

Implemented and tested in Blender 5.2.4:
- `src/live_achene_mask.py`: loads existing M1c `.blend` and unfiltered M1a `whole.blend`, restores **539 anchors** (including original rotation/size attrs), inserts live SDF sample + point-domain Delete Geometry **before** GN Instance on Points, using the same editable cutter as the M1c body.
- `src/validate_live_cut.py`: reopen actual M1d `.blend` and validate frames **1/15/30**, GN point counts, instance mesh vertex count and watertight SDF output. Half seed counts **273/176/84**, bite **481/453/539**. All six SDF states have 0 non-manifold edges.
- `src/export_pose_glb.py`: **explicitly bake evaluated meshes per frame before glTF export**. Never rely on `export_apply` for frame-specific Geometry Nodes — tested bug produced identical GLB for frame 1/30. GLB snapshots do NOT preserve Blender's animation, Geometry Nodes or full Cycles material.
- `src/render_pose.py`: one genuine Cycles render per Blender process; avoids headless memory issues with many successive high-quality frames.
- [M1d results](docs/m1d-results.md) / [manifest](assets/manifest-m1d.json): two editable .blend, four GLB snapshots, four Cycles PNG, one comparison sheet and six JSON reports; all **17/17 SHA-256 readback PASS** from restricted owner Google Drive [v0.5-m1d-live-achenes](https://drive.google.com/drive/folders/1x4TCZEZM8LEzsK8BFBB0TtHBXTGnWj1m).

Limitations NOT yet implemented: per-achene solid/cutter intersection (currently centre-point mask), live cutting of calyx/stem, credible wet internal tissue, photoreal PBR GLB. Keep [Issue #8](https://github.com/Dmitry-dev-pet/strawberry-lab/issues/8) open for the remaining visual work. Do not claim author-grade Frucht fidelity.


## M1e architecture reference — Frucht Free Kiwi 0.4.3 (audited 20 Nov 2026)
- REQUIRED before further M1e design: [docs/kiwi-architecture-audit.md](docs/kiwi-architecture-audit.md) and [Issue #9](https://github.com/Dmitry-dev-pet/strawberry-lab/issues/9).
- Directly opened free `daten/kiwi.blend` in Blender 5.2.4. Source is only **KIWI**, not paid strawberry. All source ZIP / Blender / graph metadata live in private Drive reference folder (linked in audit). The `blender_manifest.toml` declares **GPL-3.0-or-later**.
- Kiwi root group uses `Mesh Boolean DIFFERENCE` and delegates shape, seeds, cut-cap cells, edge repair, hairs and calyx; shared addon `schnitte.py` separately implements SDF workflows. No false claim that free Kiwi root uses SDF.
- Kiwi `Zellen am Schnitt` includes five volume cubes and four each named-grid store/get; `Zelltypen` has 3×3D+2×4D Voronoi; `Gewebe` yields 19 tissue fields. This is **engineering reference only**; strawberry must have its own anatomy.
- M1d currently has 3 GN groups / 41 group nodes but extensive Python-built geometry/materials (counts are NOT directly comparable as performance/fidelity metrics).
- Priority: (1) all parts respond to the same cutter, radius-aware seed intersection and calyx/stem mask; (2) independently testable `CutSurface` with tissue fields and 3D volume grids; (3) Fast/Exact + benchmark. **M1e refactor not yet implemented**. Do not claim that a docs audit builds a new 3D model.
- The generic read-only audit tool [scripts/audit_node_architecture.py](scripts/audit_node_architecture.py) may be run on reference and own scenes. It writes aggregate summaries only; DO NOT check proprietary/free GPL source node exports into this repo without a licensing review.

## Fruit Engine M1f — first physical-scale Blender source-of-truth (20 Nov 2026)

Implemented real independent source modules: [src/fruit_engine.py](src/fruit_engine.py), [src/fe_geometry.py](src/fe_geometry.py), [src/fruit_engine_anatomy.py](src/fruit_engine_anatomy.py), [src/build_fruit_engine_blender.py](src/build_fruit_engine_blender.py), [src/validate_blender_profiles.py](src/validate_blender_profiles.py) and two new Python unit test files. [Technical report](docs/m1f-results.md). Actual saved editable [Blender scene and two Cycles renders on Drive](https://drive.google.com/drive/folders/1DCNnvFh7de0qx8Hdj5PefVBn3j5rmQW6); verified [8/8 full SHA-256 readback](assets/manifest-m1f.json).

**REAL scale:** 1 Blender unit represents 1 mm, Blender scene length scale = 0.001. Verified geometry: Camarosa 48 × 32.5 mm with 326 schematic markers rounded from 325.6 observed mean; Sweet Gold one-sided tissue bounds 3.6/14.0/21.3 mm; Jecy Gold 3.0/11.6/20.7 mm; eight mean-cell-diameter gauges physically exact. 22/22 pure Python tests and reopening of two-scene Blender .blend PASS. Shared GN region-material group instantiated across all three fruit objects; second GN group scatters schematic strawberry surface markers.

**DO NOT OVERCLAIM:** The profile establishes only **source-measured extents**. Not yet measured: fruit silhouette, true achene size/distribution, locule arrangement, vascular diameters, complete ripe strawberry tissue morphology. Kiwi discs are radial cross-section schematics; microdiameter circles are NOT real cell membranes. Organ graph reference for *Actinidia deliciosa* from Guo et al 2013 is NOT silently attached to yellow-kiwi measured *A. chinensis* profile. Full common GN engine not yet implemented; two shared groups are only the first working kernel. Old M1a–M1d remain immutable. [Issue #11](https://github.com/Dmitry-dev-pet/strawberry-lab/issues/11) remains OPEN for real biological calibration.


## M2a shared Fruit Platform — verified 20 Nov 2026

**New source of truth:** [fruit_platform.py](src/fruit_platform.py) contains immutable, independent `FruitContext` with nested maps frozen via MappingProxyType, an instance-owned `FruitRegistry`, strawberry/kiwi anatomy adapters and `FruitPlan` of typed `OrganRecipe` records. The Blender composer [build_fruit_platform_blender.py](src/build_fruit_platform_blender.py) accepts individual recipes and emits Blender objects via stateless geometry emitters. **There is no per-process global active fruit.** Cuts/renders are operations, not anatomical organs.

**Evidence-bound output:** four simultaneous fruit instances in one saved .blend (Camarosa twice with different artist arrangements, Sweet Gold, Jecy Gold); two GN groups reused across contexts; strict 1 BU = 1 mm; original primary table IDs stored per organ. Tissue domains, vascular topology and reproductive organs have explicit `MEASURED_EXTENT`, `QUALITATIVE_ONLY` or `UNMEASURED_ONLY` annotations; unmeasured kiwi seed/locular/vascular geometry is **not generated**. Guo 2013 green A. deliciosa vascular graph is marked CROSS_TAXON_REFERENCE_ONLY for A. chinensis, never asserted as the actual measured yellow cultivar graph.

**QA:** `PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v` returned **45/45 PASS**. Reopened saved .blend in Blender 5.2.4 verified 4 body meshes, 2 seed marker point groups with 326 each, 8 micro gauge circles, 2 shared GN groups, correct measured physical sizes; Drive-readback copy independently reopened and yielded identical validator JSON. Two authentic Cycles PNG rendered. All 9 artifacts SHA-256 checked after fetching from owner-restricted Google Drive [v0.7-m2a](https://drive.google.com/drive/folders/1W2tKQx6d6dqxV5ALU-cEAK5TYAWK_aNz), see [asset manifest](assets/manifest-m2a.json) and [technical report](docs/m2a-results.md).

**Still NOT ready:** real 3D parenchyma and vascular Geometry Nodes, locule placement, cut-scene integration and browser glTF output; current M2a is a *platform kernel with schematic geometry*, not anatomically accurate photorealistic fruit. Next priority: implementing real reusable organ/tissue/vascular GN subgroups respecting each specimen's source evidence. Old M1f/M1d archives must not be overwritten. Do not copy original Frucht Kiwi GPL-licensed node trees.

## T3 visual-first workflow (owner approved 20 Nov 2026)

For T3 work read [project adapter](.agents/skills/strawberry-t3/SKILL.md), [role configuration](config/t3-agent-roles.json), and [workflow/recovery](docs/t3-workflow.md). Use Beads for operational subtasks, GitHub Issues for milestone acceptance. Exterior quality is the current user priority; do not expand it into another universal-engine refactor. Parent exclusively controls live Blender; workers build headlessly and reviewer reads independent evidence. Never mark owner visual acceptance complete from technical tests alone.
