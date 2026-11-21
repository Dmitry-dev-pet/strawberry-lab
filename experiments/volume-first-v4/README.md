# Strawberry Lab — Volume First V4: terminal tangent test

**Status: independently authored, reproducible diagnostic; NOT a photorealistic Frucht replication.**

The experiment changes **only the final 21 of 64 points** of each of 539 curves in our owned V3 `sag=0.25` model. It preserves all seed markers and branch endpoints bit-for-bit, **28 central carriers**, all branch roots and the first **43** points of each branch, curve radii, camera, lighting and materials. Three independently controlled strengths are `0.35`, `0.85`, `1.5`.

This directly tests the previous hypothesis that local exit/arrival tangents, as opposed to total global sag, explain the shape difference vs Frucht. Every curve is an actual spatial polyline in the saved Blender scene. The last segment follows a cubic Hermite interpolation with individual terminal directions and an analytically smooth local tangential bend. No Frucht GPL code or node group is copied.

## Actual result

- 539/539 fixed branch endpoints; no change to first 43/64 points, main carriers or radii; deterministic NPZ regeneration and saved Blender readback PASS.
- Median change in terminal direction vs V3: 9.4°, 25.0°, 46.0° at strengths .35, .85, 1.5.
- One view, same 840×942 camera and 12 CPU Cycles samples for all four variants. V4 still looks **much too uniformly radial and compact** compared with Frucht's promo frame ~00:15. The prototype remains an engineering negative result, not a visual breakthrough.
- The Frucht reference may show a different scale, angle, cut/exploded or animated pose with visible fibers extending beyond the fruit tissue. We **do not** know the precise promo UI-to-node state and cannot conclude that simple terminal bending is the missing mechanism. Since our endpoints are constrained immediately under a static skin, our whole-fruit views could not reproduce an outward-exposed pose without a distinct visualization mode.

## Reproduce

Use Python 3, NumPy, Blender 5.2.4 LTS (any installation with comparable Cycles support).

```bash
python generate_v4_network.py --hook 0.35 --out v4-hook0.35.npz
python generate_v4_network.py --hook 0.85 --out v4-hook0.85.npz
python generate_v4_network.py --hook 1.5  --out v4-hook1.5.npz
python qa_v4_data.py
blender -b input-v3-scene.blend -t 4 --python build_v4_blender.py -- v4-terminal-hooks.blend
blender -b v4-terminal-hooks.blend -t 4 --python validate_v4_blender.py
blender -b v4-terminal-hooks.blend -t 4 --python render_v4_blender.py -- --variant v3 --view only --resolution 840 --samples 12 --out outputs/only-v3.png
blender -b v4-terminal-hooks.blend -t 4 --python render_v4_blender.py -- --variant 1.5 --view only --resolution 840 --samples 12 --out outputs/only-1.5.png
python make_comparisons.py
```

The Blender scene holds V3 and three new V4 variants; the render script selects the active branch curves while sharing V3's unchanged 28 carriers. `private-frucht-video-ref15.jpg` is an **owner-provided copyright reference** stored only in restricted Drive/ZIP and intentionally excluded from public GitHub. `make_comparisons.py` expects this private frame for the private montage (other montages can be generated without it after commenting that section). One multi-render launch was interrupted/stalled; isolated rendering processes succeeded. We do not claim runtime animation stability.

Next meaningful diagnostic: understand Frucht video **geometry display state** and distinguish exposed/exploded fibers from internal seed-anchored anatomy. Do not continue tuning tangents or increasing curve counts blindly. The `main` branch contains the Frucht code audit; V4 remains a stacked experimental PR until a visual criterion is achieved.
