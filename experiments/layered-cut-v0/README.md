# Strawberry Lab — Layered Cut v0 (independent tissue / vascular clipping)

**Status:** reproducible Blender 5.2.4 diagnostic experiment. **Not** a finished Strawberry generator or a verified implementation of the commercial Frucht UI. The original 539 seed-linked spatial curves are unchanged. The report and code are independently authored for Strawberry Lab.

## Question

Can the dramatic exposed vascular network in a Frucht promo shot be explained at least partly by independently controlling *what gets clipped*, rather than by making new fibers? This experiment deliberately holds the physical volume-first half-cut flesh and the same vascular network, camera, lighting and materials constant.

## Actual result

| Blender scene | Red flesh | 28 central carriers | 539 branches | 539 achene markers |
|---|---|---|---|---|
| `LAYER A \| common cut y=0` | Physically retained `Y≥0` | Clip to `Y≥0` | Clip to `Y≥0` | Keep only `Y≥0` markers |
| `LAYER B \| flesh-only cut y=0` | **Same** physically retained `Y≥0` | **Whole original** | **Whole original** | **All original markers** |

Cutting only the flesh reveals a dramatic exposed pale network in front of the red cut face **without changing original spline coordinates or any seeds**. This demonstrates that display/clipping policy can have a large effect. It does **not** prove that Frucht uses this exact policy or has our 539 branch count.

- Whole-curve data is copied from our V4 `V3 | 28-sag0.25 | CARRIERS` and `V4 | hook0.85 | BRANCHES` objects.
- Physical half-fruit is reused, unchanged, from the prior Volume First v0 `CUT_000_deg | SAME 3D SUBSTRATE` mesh. We use its **original opaque v0 material**, not the unrelated V1 494-fiber appearance.
- Full seed endpoints are diagnostic octahedra already in V2/V4, *not* anatomically correct achene geometry. On the positive-Y side there are **270** markers; all markers total **539**.
- Intersections of polyline segments with the cut plane are computed exactly by linear interpolation, including radii. This yields **15 core segments** and **283 branch segments** retained for common clip, versus **28 + 539** original spatial paths for flesh-only clip.
- Existing base material still includes coarse synthetic tissue colors; **new V4 fibers have not been baked into the flesh**, and the v0 cut mesh is static rather than a live knife.
- Pith, microscopic cell mesh, wet droplets and real achene meshes are **not independent physical objects in the V4 source**. They are *not* silently simulated here; those layers can be added when actually implemented.

## Open and interact in Blender

1. Open `outputs/strawberry-independent-layers-v0.blend` with Blender 5.2.4 or newer. The active scene is **`LAYER B | flesh-only cut y=0`**. In the Scene selector, switch between it and **`LAYER A | common cut y=0`** to compare the two cutting policies.
2. In the **Outliner**, expand the active `LAYER ...` scene's named collections. Toggle collection exclusions/visibility (not just material colors) independently:
    - `10 | FLESH` — actual cut flesh / skin
    - `20 | CORE FULL` or `21 | CORE CLIPPED` — the same 28 carriers with independent clipping
    - `30 | VASCULAR FULL` or `31 | VASCULAR CLIPPED` — 539 independent spatial branches
    - `40 | SEED END MARKERS FULL` or `41 | SEED END MARKERS CLIPPED` — actual V2 diagnostic positions
    - `50 | OUTLINE` — optional transparent outer context, disabled by default
3. **Optional easier sidebar controls, no plugin installation:** switch to Blender **Scripting**, choose embedded text `LAYER_LAB_UI__RUN_IN_BLENDER.py` and press **Run Script** once. Then in 3D viewport press **N**, open **Strawberry Layers**. Each layer has `Off`, `Clipped`, `Full` switches; flesh and transparent outline each have a separate checkbox. Switch A and B scenes independently. These **work**, not decorative mockups: they change actual View Layer exclusion flags. The controls are loaded for the session; repeat Run Script after reopening Blender, or just use the native Outliner without it.
4. The physical flesh cut plane **is fixed at Y=0**; switching fiber clipping does *not* animate or change its location. A movable common knife is a separate next task.

## Command-line reproduction

From the directory containing `build_layered_display.py`:

```bash
blender -b input-v4-terminal-hooks.blend --python build_layered_display.py
blender -b outputs/strawberry-independent-layers-v0.blend --python validate_layered.py
blender -b outputs/strawberry-independent-layers-v0.blend --python test_ui.py
blender -b outputs/strawberry-independent-layers-v0.blend --python render_layered.py -- --mode matched --size 620 --samples 14 --output outputs/matched.png
blender -b outputs/strawberry-independent-layers-v0.blend --python render_layered.py -- --mode flesh-only --size 620 --samples 14 --output outputs/flesh-only.png
blender -b outputs/strawberry-independent-layers-v0.blend --python render_layered.py -- --mode fibers-only --size 620 --samples 14 --output outputs/fibers-only.png
python make_layer_comparisons.py
```

`test_ui.py` is the automated test, while `layer_controls_ui.py` is included in the `.blend` as text for direct Run Script use.

## Validation

`outputs/validation.json` checks original source SHA-256 on 28+539 curves, exact per-scene full-curve identity, cropped halfspace and seed marker positions, equal body meshes and materials, equal camera/light transforms, and independent actual layer inclusion. `ui-test.log` shows UI callbacks really alter View Layer exclusions. `outputs/render-difference.json` measures image differences (not perceived fidelity). The native renders `outputs/real-ab-layer-clipping.jpg` and `outputs/real-layer-toggle-grid.jpg` are composed solely from genuine Blender Cycles renders, no AI-generated imagery.

## Source ownership & limitations

Original comparison material from Frucht Free Kiwi 0.4.3 and private video is **not** redistributed here or in GitHub. This experiment consumes *our own* V4 scene and v0 cut object. Because the commercial strawberry `.blend` is not available, the exact mapping of the Frucht `Core Fibers`, `Core Cut Angle`, and `Cut Oblique` controls remains unknown. This experiment tests a plausible **effect** of independent layer visibility, **not the commercial implementation**.
