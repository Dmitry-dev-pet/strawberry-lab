# Strawberry Lab 🍓

**Open research project: procedural, anatomically structured strawberries in Blender.**

Русский — основной язык проекта. Задача: построить самостоятельный, воспроизводимый генератор клубники, а не только статическую 3D-модель. Итог должен поддерживать изменяемую форму, внешние семянки, ткани мякоти, произвольные разрезы и качественный рендер, а также экспорт в GLB/Three.js.

**Current status: v0.1 baseline (proof of concept), NOT author-grade.** Текущие рендеры уступают Frucht по анатомической подробности, реалистичности материалов и производительности при разрезании. Это открытый список технических проблем, а не скрытый недостаток.

## Что сейчас в репозитории

- `src/generate_strawberry.py` — воспроизводимая сцена Blender 5.2+: форма по математической функции, чашелистики, сетка продольного разреза, инстансинг наружных семянок через Geometry Nodes, рендер и экспорт GLB.
- `src/make_tissue_textures.py` — независимое построение процедурных текстур кожуры и среза. Никаких фотографий и сгенерированных нейросетью изображений.
- `docs/quality-plan.md` — цели, объективные критерии качества и следующий этап.
- `AGENTS.md` — рабочий процесс для агентов и правила публикации/проверок.

Текущие исходники создают **гибрид Python + Geometry Nodes**, ещё не полностью нодовый генератор. Плоскость разреза зафиксирована при `y=0`. Большие `.blend`, `.glb`, изображения и самодостаточный HTML-просмотрщик пока не версионированы в GitHub; их можно воспроизвести из исходников (GLB) или получить из предыдущего тестового комплекта. Не считать их наличие в чате публикацией в этом репозитории.

## Быстрый старт

Нужен Blender **5.2+**, Python 3 с `numpy` и `Pillow` для генерации PNG.

```bash
python3 -m pip install -r requirements.txt
python3 src/make_tissue_textures.py

blender --background --python src/generate_strawberry.py -- \
  --mode whole --preview --samples 24 --resolution 900
blender --background --python src/generate_strawberry.py -- \
  --mode cut --preview --samples 24 --resolution 900
```

Результаты записываются рядом с `src/generate_strawberry.py` (в `src/`). Для сравнения результатов нужно фиксировать версию Blender, ракурс, освещение, количество сэмплов и семя случайности.

## Цель качества

Переход от плоской текстуры среза к **подлинному трёхмерному анатомическому полю**; отдельные семянки с углублениями в кожуре; геометрически корректная кромка произвольного разреза; процедурные материалы с тонкой структурой; измеряемая производительность; повторяемые рендеры. Все визуальные утверждения должны сопровождаться настоящим Blender-рендером и сохранённой сценой.

## Происхождение и права

Проект создан независимо по мотивам публичного исследования [Who Made the Strawberry?](https://strawberry-methodology.pages.dev/) и анализа архитектурных идей в бесплатном Frucht Kiwi. **Не** копируем коммерческую модель клубники автора, его нодовые деревья, изображения или закрытые материалы. Frucht — отдельный проект его автора. Публичный репозиторий пока **без явно выбранной лицензии**: открытая видимость сама по себе не даёт автоматического разрешения на повторное использование кода. Решение о лицензии принимается отдельно.

## План работы

См. [Quality Plan](docs/quality-plan.md) и GitHub Issues. Каждый этап завершается сравнимым рендером, логом характеристик сцены и проверенным исходным файлом Blender.

## Blender, textures and 3D files on Google Drive

Heavy v0.1 baseline assets are saved in **[Strawberry Lab / v0.1-baseline on Google Drive](https://drive.google.com/drive/folders/1-W4FaqIQAgR6jdaVIYqriLfBuK8UjLJa)**: two editable Blender files, `skin.png`, `flesh.png`, two GLB models, two authentic Cycles renders and one standalone Three.js HTML build (9 files).

Every file was downloaded back from Drive and verified byte-for-byte with SHA-256. The authoritative [asset manifest](assets/manifest-v0.1.json) contains sizes, digests and Drive links. [Storage and restoration rules](docs/storage.md) explain the split between GitHub and Drive and the local verification command:

```bash
python3 scripts/verify_assets.py assets/manifest-v0.1.json /path/to/downloaded/v0.1-baseline
```

**Access:** The GitHub repository is public; the current Google Drive folder is restricted (authorized users only). This does not prevent rebuilding assets from public source, but external visitors cannot download the exact reference binaries until Drive sharing is explicitly enabled.

**Build verification:** a clean-directory build from GitHub-matched source produced textures and both GLB files with SHA-256 hashes identical to the Drive baseline. Newly saved Blender scenes work but are not binary-identical; see [rebuild verification report](docs/rebuild-verification.md).

