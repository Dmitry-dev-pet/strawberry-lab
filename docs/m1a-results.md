# M1a — первый реализованный анатомический генератор (20 ноября 2026)

**Статус: рабочий исследовательский прототип, не готовая реалистичная клубника.**

## Что действительно реализовано и проверено

Предыдущая версия v0.1 сохраняется без изменения. M1a — отдельные Python-скрипты и 4 новые редактируемые сцены Blender 5.2.4 LTS (Cycles CPU для трёх обычных видов и Workbench для диагностической схемы).

| Компонент | Факт реализации | Проверка |
|---|---|---|
| Геометрия цветоложа | Радиальная форма и **настоящие локальные углубления под семянками**, рассчитанные на поверхности | Blender `.blend` открывается, видны реальные неровности |
| Семянки | 539 индивидуальных якорей, реальная 3D-геометрия, Blender Geometry Nodes instancing | 539 whole, 270 в продольной половине, 221 в поперечной половине |
| Сосудистые пути | 539 параметрических кривых, каждая от центра/цилиндра до своего achene | 8 unit tests; полная сеть сохранена в каждом `.blend`, в натуральных рендерах скрыта |
| Тканевые поля | Одна математическая функция `fields(x,y,z)` для pith, cortex, bundle zone, epidermis | Продольный срез y=0 и поперечный z=0 из одной модели |
| Цвет и текстура | Внешняя процедурная кожа, tissue color attribute на поверхности среза, процедурная микрошероховатость | Подтверждены рендерами Blender, **без ImageGen** |
| Экспорт | Три GLB: whole, longitudinal, transverse | Все три открыты библиотекой `trimesh`, содержат 241896 / 174412 / 158948 треугольников |
| Диагностика сосудов | Отдельная сцена `anatomy.blend` и Workbench PNG; без кожуры | 539 ветвей видны в 3D |

**Test status:** чистый Python — 8/8, Blender scene validation — 4/4, GLB parser — 3/3, полная проверка файлов после скачивания из Drive — 12/12 совпадений SHA-256.

## Файлы и воспроизведение

- [Хранилище версий (Drive / v0.2-m1a-anatomy)](https://drive.google.com/drive/folders/1MErno0Y_C-ctG_dw8YvM8Abdje5ODEDh) — закрытая папка владельца, **12 финальных артефактов**, 42,3 МБ (не включая промежуточный предварительный сравнительный JPG и копию исходников).
- [Список 12 файлов с SHA-256, точными Drive ID и статусами](../assets/manifest-m1a.json).
- Исходники: [strawberry_biology.py](../src/strawberry_biology.py), [generate_anatomical_strawberry.py](../src/generate_anatomical_strawberry.py), [validate_scene.py](../src/validate_scene.py), [render_anatomy_workbench.py](../src/render_anatomy_workbench.py), [8 тестов](../tests/test_biology.py).

### Локальный запуск

```bash
python3 -m unittest discover -s tests -p 'test_biology.py' -v
mkdir -p build/m1a
blender -b --python src/generate_anatomical_strawberry.py -- \
  --mode whole --out build/m1a --samples 18 --resolution 860
blender -b --python src/generate_anatomical_strawberry.py -- \
  --mode longitudinal --out build/m1a --samples 18 --resolution 860
blender -b --python src/generate_anatomical_strawberry.py -- \
  --mode transverse --out build/m1a --samples 18 --resolution 860

blender -b --python src/generate_anatomical_strawberry.py -- \
  --mode anatomy --out build/m1a --no-render --no-glb
blender -b build/m1a/strawberry-m1a-anatomy.blend --python src/render_anatomy_workbench.py -- \
  --output build/m1a/strawberry-m1a-anatomy-workbench.png --resolution 720
```

Чтобы отдельно проверить сохранённую геометрию:

```bash
blender -b build/m1a/strawberry-m1a-longitudinal.blend --python src/validate_scene.py
```

## Ограничения, которые нужно исправлять далее

1. **Биология не откалибрована численно.** 539 семянок, радиусы, толщина пучков, параметры кожи и форма ветвления — параметры моделирования, не измерения из атласов. Источники задают топологию и типы тканей, но не говорят, что эта визуализация анатомически точна.
2. **Клеточная структура среза выглядит слишком гладкой.** В M1a имеется непрерывное 3D-поле ткани, но ещё нет отдельных объёмных клеток, интерцеллюлярных промежутков и убедительного влажного рельефа; это визуально даже уступает старому декоративному эффекту волокон v0.1.
3. **Сосудистая система топологически связана моделью**, но ветви в натуральном рендере скрыты внутри непрозрачной ткани; диагностический режим показывает их отдельно. Утолщённые белые «нити» Frucht не копируются.
4. **Разрезы пока фиксированы** — y=0 и z=0, а не свободная плоскость. Проверка пересечений и герметичности также не закончена.
5. **GLB не содержит полный скрытый граф сосудов** — этот граф хранится в редактируемой сцене Blender; браузерный GLB содержит видимую геометрию и материалы.

Итог: M1a — реальный переход от плоской карты к пространственной тканевой модели, улучшенная внешняя кожура и исходный граф сосудов. **M2 — пространственная клеточная микроструктура, научная калибровка, физически корректные срезы.** Уровень Frucht пока не достигнут.

## Научные ориентиры

- [Hurtado & Knoche, Frontiers in Horticulture (2026)](https://doi.org/10.3389/fhort.2026.1779354): receptacle, epidermis, cortex, vascular cylinder, pith, achene depressions.
- [Darrow, *The Strawberry*, USDA, figs 19-38 / 19-39](https://content-calpoly-edu.s3.amazonaws.com/strawberry/1/documents/Darrow_The%20Strawberry.pdf): сосудистая зона, связи к семянкам, продольный и поперечный срез.
- [Полная спецификация биологии](strawberry-biology-spec.md). Видео Frucht — независимый [визуальный ориентир](visual-reference-frucht.md), а не источник размеров.
