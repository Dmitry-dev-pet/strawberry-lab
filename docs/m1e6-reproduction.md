# Strawberry Lab M1e6 — native Geometry Nodes live cut, Blender 5.2.4

**Independent experimental milestone.** The main deliverable is `m1e6-nativeGN-production.blend`: one fruit with a genuine hollow cavity, a moveable cutter, 3D-space filament signal and local selected-edge topology refinement, driven by Blender Geometry Nodes **without a Python runtime callback**. It contains no Frucht assets, code or licensed node graphs.

## Open and edit

Open `m1e6-nativeGN-production.blend` in Blender **5.2+**. Select the body object `M1c | SDF cutter + rest-space tissue` and open its Geometry Nodes modifier. Its six native parameters are:

- `Cut edge width` and `Cut edge segments` — selective Mesh Bevel *inside* the fresh cut, not full-face subdivision.
- `Fiber reach` and `Fiber intensity` — source-rest-space 3D nearest-distance field from our own persistent filament spline mesh.
- `Cell relief` and `Cavity relief` — geometric displacement strengths on the visible faces.

Move or rotate `M1e | independently moving knife (cube half space)`, or scrub frames 1–30. The cut and fiber field update natively, with no `Run Script` action. Blender may still take more than one second per pose on CPU because source SDF is not cached.

**Do not use M1e6 as the visual-quality replacement for M1e5 Exact yet.** Bevel creates fewer samples, but the original BMesh Exact has stronger microgeometry; comparison renders are provided. All cell/filament structures are artist-designed, not botanical tissue measurements.

## Reproduce from source

Use the included, owner-authored `m1e5-source.blend` as source material (not Frucht). Commands assume working directory containing this README:

```bash
blender -b m1e5-source.blend --python build_m1e6.py -- --out /tmp/m1e6-before-controls.blend --segments 3 --width 0.008 --material original
blender -b /tmp/m1e6-before-controls.blend --python expose_controls.py -- /tmp/m1e6-built.blend
blender -b /tmp/m1e6-built.blend --python validate_m1e6.py -- /tmp/validation.json
blender -b /tmp/m1e6-built.blend --python test_controls.py
blender -b /tmp/m1e6-built.blend --python render_m1e6.py -- --frame 15 --out /tmp/cycles-frame15.png
```

## Test boundaries

- Good: frames 1/15/21/30, moving knife by +0.3 Y, rotation 18°, filament source movement +0.5 X, 2500 untouched skin samples, connected components, six modifier inputs and zero non-manifold edges on standard poses.
- Known **failure**: moving the cavity 0.18 X at frame 21 produces six tiny extra *closed* islands (7 components total), despite zero non-manifold edges. Production cavity geometry is therefore not certified to animate or edit arbitrarily.
- A separate two-modifier island-cleaner cured that specific cavity edit (one component), but changing the `Fiber intensity` GN control sometimes hung Blender; it is **deliberately excluded from the distributed working .blend**.
- Cut-local Mesh Bevel is NOT selected-face Subdivide Mesh. The true source-volume SDF remains live, unbaked and the visual quality still lags the author's Frucht. Topology checks do not prove no self-intersections.

See `report-m1e6.md`, `validation.json`, `benchmark.json` and `manifest-m1e6.json` for verified measurements, experiments and hashes.
