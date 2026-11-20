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
- **Still NOT true anatomical validation:** capsule/cut cell-scale structure and actual vascular sizes are uncalibrated; two fixed cut planes rather than arbitrary cut. No deceptive claims of Frucht quality. Source of anatomy: [docs/strawberry-biology-spec.md](docs/strawberry-biology-spec.md).

**Canonical binary storage**: `Google Drive / Strawberry Lab / v0.2-m1a-anatomy`, restricted to owner. Do not overwrite the previous `v0.1-baseline` or release private reference footage. Publish SHA-256 manifest with verified readback after every Drive upload.
