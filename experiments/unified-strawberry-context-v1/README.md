# Unified strawberry context v1 — affine integration slice

Changing one width/height control record now co-deforms the existing PR34 hull, its 264 physical achenes and baked geometric pits, calyx, original 28+539 curves, 539 diagnostic markers and shared knife. This is a **working affine template adapter**, not a complete morphology or anatomical generator. PR34 and main are unchanged.

Private scenes, six original PNGs, comparison and reproduction ZIP: [owner Drive folder](https://drive.google.com/drive/folders/1ELh4EIMLCPIictDQvd4wkvLlOwYuDsoX). [Elongated scene](https://drive.google.com/file/d/1f0HZAQGUORVFHXbrrIvTmhz_wbBbbMmL/view), [round scene](https://drive.google.com/file/d/1tHEFjKPhETqZLS0u1gWGpRS-Nk6lujB1/view), [comparison](https://drive.google.com/file/d/1q2D8y8AH6DJfvnT1qKYiCNAWOw4Nz9pM/view). Binaries and renders stay private; no Frucht assets are included.

## One control record, existing platform

`SharedDeformation` wraps the existing immutable `fruit_platform.FruitContext`; `make_context` and `standard_registry().plan` validate the existing specimen and research provenance. No second FruitContext or platform was introduced. A typed `OrganRecipe` records this display adapter. The existing research organ emitters are **not** producing the rendered organs in this slice: the authenticated PR34 scene is the template.

`F(x,y,z)=(width*x,width*y,height*z)` is an invertible rest-to-world mapping at the existing `Strawberry | PR29 rest space` Empty. Native scale drivers read its two custom properties. The body, seeds, pits, crown, network, markers and knife already share this parent. Raw template mesh and curve coordinates remain unchanged; evaluated **world geometry and anchor locations genuinely differ**. Source names, identities, radii and connections are retained in reference space. World radii and seed/pit proportions stretch with the same mapping.

| Artist preset | Width factor | Height factor | Actual body X × Y × Z, mm |
| --- | ---: | ---: | --- |
| Elongated | 0.80 | 1.15 | 32.612 × 31.923 × 55.200 |
| Round | 1.10 | 0.90 | 44.841 × 43.893 × 43.200 |

These dimensions are measured from the generated world mesh, **not cultivar measurements**. M2a's 48 × 32.5 mm specimen dimensions remain reference provenance only. The PR29/34 template is wider. Native scene scale remains 22.22222276 mm/model unit.

## Editing

Open either scene with scripts disabled: native Fast and WHOLE/MATCHED/FLESH ONLY/FIBERS ONLY work. Select the rest-space Empty and edit Object Properties → Custom Properties → `unified_width_factor` / `unified_height_factor` (0.65–1.35). The immutable context JSON in scene properties is a **build receipt**, not a live reflection of later UI edits. The two root properties are authoritative during editing; saving a new preset should generate a fresh receipt.

For live geometric tissue relief, run the embedded `TISSUE_ZONES__RUN.py`, then N → Strawberry Cut → Exact. Knife translation/rotation and the four native layers are inherited from PR34. Saving returns to native Fast. The GUI Blender scene was never touched during this build.

Atlas Object coordinates use the same rest Empty: `F^-1(world)` samples the original packed 150³ atlas. Exact uses `root.world^-1 @ body.world` and the same rest-space 3D curves. Thus cap colors, pith/cortex masks and relief stay attached through changes of shape and knife pose. **Relief depths/wavelengths and the labels “mm” in the inherited tissue controls are reference-space mm and stretch under F**. This is not physical-scale-invariant tissue regeneration. Knife pose values are reference-space coordinates; world plane orientation is the inverse-transpose transformation of the reference plane.

## Evidence and limits

- Both saved scenes and their full Drive downloads reopened in Blender 5.2.2 with auto-execution disabled.
- All 264 seed meshes intersect the actual world hull in each shape. Minimum exposed mesh-vertex fraction is 0.41573 (not exposed surface area); minimum buried vertex depth is 0.09928 / 0.10941 mm.
- All source mesh/curve points are identical in reference space; all actual world points match F within 1.63e-7 model units. Original 28 carrier and 539 branch splines/radii, 539 markers, packed atlas, material graphs, color ramps and bindings match PR34.
- Two translated/rotated cuts per shape pass both native Fast and Exact: connected, manifold, positive-volume body. The Exact cap has real displacement, preserved rest coordinates and zero tangential drift within the inherited tolerance. Four view layers and a live width-driver roundtrip pass.
- Six genuine Cycles renders: 750×750, 12 CPU samples, denoise, seed1729, same camera/light, whole + longitudinal + oblique for both shapes. Each gallery slot authenticates the source scene, frame and PNG hash.
- 107 repository tests + 8 existing atlas/receipt tests + 5 new context tests pass.

Visual inspection confirms distinct silhouettes and coherent pith/cortex placement on both cuts. Skin remains waxy and the inherited angular/pale pit rims remain visible; no realism improvement is claimed. Seed/calyx dimensions also stretch, which is a limitation of this affine slice.

**Vascular attachment constraint: FAIL / UNRESOLVED.** The 539 diagnostic endpoints are not the 264 real achenes. No nearest-neighbor correspondence was invented. The existing network co-deforms as a diagnostic graph; no new vascular geometry or cells were generated. Diagnostic MATCHED clipping remains shader-only; exported curves retain full paths.

Next architectural increment should replace this affine template adapter with one non-affine rest-space profile map and regenerated seed-aligned pits, while retaining the explicit inverse field and existing IDs. Anatomical endpoint generation is a separate unresolved contract. Neither is implemented here.

## Reproduce

Use Blender 5.2.2 headlessly; obtain `build/inputs/pr34-pits.blend` from the owned source and authenticate SHA256 `24a3f7a2b9b157aac3b5a8aa30aa1b84d2404be64df67f74705665de3dbf74b4`.

```sh
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/unified-strawberry-context-v1/build_unified.py -- build/inputs/pr34-pits.blend build/new-unified
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/unified-strawberry-context-v1/validate_unified.py -- build/inputs/pr34-pits.blend build/new-unified/elongated.blend build/new-unified/elongated-qa.json
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/unified-strawberry-context-v1/render_unified.py -- build/new-unified/elongated.blend cut build/new-unified/elongated-cut.png
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src:experiments/exact-tissue-zones-v1 python -m unittest discover -s experiments/exact-tissue-zones-v1 -p 'test_*.py'
PYTHONPATH=src python -m unittest discover -s experiments/unified-strawberry-context-v1 -p 'test_*.py'
```

Repeat validation/render with round; supported frames are `whole`, `cut`, `oblique`. Build and QA refuse to overwrite existing outputs. `check_layers.py` runs the original stale-cap render regression against both shapes. `make_gallery.py` authenticates and assembles the six frames at the default output path. `evidence.json` pins scenes, parameters, image hashes, readback and actual QA.
