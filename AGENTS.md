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
