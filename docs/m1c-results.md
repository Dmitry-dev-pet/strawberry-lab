# M1c — SDF cutting and rest-space tissue cache (2026-11-20)

**Статус:** проверенный инженерный прототип в Blender 5.2.4 LTS. **Не** готовый фотореалистичный генератор, **не** копия закрытого Frucht.

## Что реализовано

1. **Настоящий SDF-разрез, не заранее нарисованная плоскость:** исходная M1a кожура с углублениями под семянками сначала замыкается (удаляются совпадающие вершины, заполняются торцы), затем внутри live Geometry Nodes `Mesh to SDF Grid` (плод и cutter) → `SDF Grid Boolean: DIFFERENCE` → `Grid to Mesh`. Извлечённый mesh замкнут; материал контактирующей с режущим объёмом поверхности определяется через `Geometry Proximity`, `Set Material`.
2. **Два разных резака из одной реализации:** `--mode half --angle 26` — наклонённый прямоугольный cutter, и `--mode bite` — сферический вырез. Blender сохраняет объекты cutters в сценах; дальнейшее редактирование cutter перестраивает SDF-геометрию.
3. **Кэш 3D-полей:** `bake_rest_atlas.py` создаёт детерминированное синтетическое поле RGB, `64³`, упакованное в PNG 512×512 с 8×8 тайлами Z-срезов. Это proof of concept, **не** размер 256³ автора и **не** измеренное биологическое поле. Синтезируются интенсивность сосудистой зоны, цветовая неоднородность и маска сердцевины.
4. **Rest-space sampling:** после получения SDF геометрии в `Store Named Attribute` записывается `fruit_rest`, а Cut Shader читает это поле. Программно построены две последовательные выборки 2D-атласа с биллинейной XY-интерполяцией внутри тайла и смешением соседних Z-срезов. Встроенные PNG и шейдер Blender сохранены внутри `.blend`, **никакой внешней текстуры не требуется после открытия сцены**.
5. **Многослойная мокрая фактура:** три независимых 3D Voronoi `DISTANCE_TO_EDGE` (разные пространственные масштабы) формируют Bump для среза; дополнительный Voronoi создаёт очень небольшой реальный mesh displacement на выделенной SDF кромке. Эффект остаётся **слишком гладким**; это не подтверждение подлинной клеточной структуры Frucht.

## Числовые результаты настоящего Blender-теста

| Режим | Voxel | Вершин SDF | Треугольников SDF | Неманифолдных рёбер | Семянок в видимой части | Cycles |
|---|---:|---:|---:|---:|---:|---|
| half, tilt 26° | 0.034 | 28 976 | 57 948 | **0** | 266 | 860×860, 24 samples |
| spherical bite | 0.038 | 30 892 | 61 780 | **0** | 478 | 860×860, 24 samples |

Python tests `test_atlas.py`: **6/6 PASS** (детерминизм, многоканальность, 3D-слои, ориентация упаковки, полное соответствие вычисляемому полю). Blender-сцены открыты и проверены скриптом `validate_sdf_scene.py`: **2/2 PASS** (реальное выполнение SDF-модификатора, атрибут rest-space, 3 Voronoi, 2 sample в packed atlas, замкнутость и два материала). GLB парсинг `trimesh`: **2/2 PASS**; glTF экспорт не воспроизводит нодовый Cycles-шейдер 1:1.

**Владелец Drive:** [v0.4-m1c-sdf-restspace](https://drive.google.com/drive/folders/1eV8D_tZ1dGbwmNevGHoC91EFU7_LhugX) — 2×`.blend`, 2×`.glb`, 2× реальный Cycles PNG, PNG 3D-атласа, сравнительный JPG, 3 JSON-файла с параметрами. **11/11 файлов скачаны обратно с Drive и проверены SHA-256 по полному содержимому**. [Манифест](../assets/manifest-m1c.json). Предыдущие версии не перезаписывались.

## Локальное воспроизведение из GitHub

```bash
python -m pip install numpy Pillow trimesh
python -m unittest discover -s tests -p 'test_atlas.py' -v
mkdir -p build/m1c

python src/bake_rest_atlas.py --out build/m1c/tissue-atlas-64.png

# Базовая M1a-сцена строится из открытых исходников или скачивается с Drive
blender -b --python src/generate_anatomical_strawberry.py -- \
  --mode whole --out build/m1c --no-render --no-glb

blender -b --python src/sdf_cut_strawberry.py -- \
  --base build/m1c/strawberry-m1a-whole.blend \
  --atlas build/m1c/tissue-atlas-64.png \
  --mode half --angle 26 --voxel 0.034 \
  --out build/m1c --resolution 860 --samples 24

blender -b --python src/sdf_cut_strawberry.py -- \
  --base build/m1c/strawberry-m1a-whole.blend \
  --atlas build/m1c/tissue-atlas-64.png \
  --mode bite --voxel 0.038 \
  --out build/m1c --resolution 860 --samples 24

blender -b build/m1c/strawberry-m1c-half.blend \
  --python src/validate_sdf_scene.py
blender -b build/m1c/strawberry-m1c-bite.blend \
  --python src/validate_sdf_scene.py
```

Воспроизводимость **именно этих бинарных BLEND SHA** через новый clean Git clone ещё не проверялась (сцены Blender часто не воспроизводимы побайтно). Исходный M1a whole snapshot закреплён в манифесте hash `333ac3f48df28cf2776efa492a15434c4c808a017ff0a48b1944e4fbeaf2493a`.

## Ограничения и важный следующий шаг

- **Семянки НЕ обновляются динамически при ручном перемещении резака:** текущая версия фильтрует GN-исходные achene-якоря **в момент генерации**, сохраняя их как live Geometry Nodes-инстансы. Перемещение cutter в Blender обновляет SDF поверхность плода, но не переназначает/удаляет семянки автоматически — нужен отдельный GN узел динамической маски.
- Калибровка полей по настоящим анатомическим данным не выполнена, 64³ cache грубый.
- Cut face внешне всё ещё слишком гладкий. Кромка SDF слегка сглажена; детализированные клетки, внутриклетники, жидкость и волокна не воспроизведены на уровне Frucht.
- Сосудистый граф M1a остаётся диагностическим: новая SDF выборка не рассчитывает реалистичное сечение всех 539 сосудов.
- GLB содержит геометрию с Material ID, но **веб-рендер не полностью воспроизводит процедурную Cycles-модель**; требуется отдельная UV/texture bake для GLB.

Следующий шаг: **динамическое удаление семянок тем же cutter полем**, затем более качественная вычисляемая ткань, параметрический SDF с разными cutter формами и экспорт тех же шейдеров через bake.

## Provenance

Это самостоятельный открытый код; Frucht служит публичным источником общей идеи и визуальным эталоном, но коммерческое дерево клубники недоступно. Техническая проверка [Frucht Kiwi vs strawberry claims](frucht-architecture-audit.md). Атлас не переносит авторские изображения и ноды, тканевые величины не являются биологически измеренными. [Биологические источники](strawberry-biology-spec.md).
