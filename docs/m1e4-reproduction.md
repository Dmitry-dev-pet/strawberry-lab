# Strawberry Lab · M1e4: 3D filament field + selective CutSurface

Independent research prototype for Blender 5.2.4 LTS. Starts from Strawberry Lab's **own** M1e3 Fast `.blend` (included in this package). No code, node graphs, meshes, or commercial assets from Frucht are included.

## What the models show

- `m1e4-frame01-beauty.blend`: uncut skin with closed internal cavity.
- `m1e4-frame15-beauty.blend`: independently moving plane knife opens the cavity, with locally refined true cut geometry and a subtle pale filament field.
- `m1e4-frame30-beauty.blend`: deeper cut generated from the same original 3D curve network.
- `m1e4-frame15-diagnostic.blend`: same geometry, with actual 3D tubular curves exposed for inspection.
- `m1e4-frame*.png`: authentic Blender Cycles renders (not AI renders).
- `m1e4-ab-comparison.jpg`, `m1e4-three-poses.jpg`: layouts of original Cycles frames.
- `build_m1e4.py`, `validate_m1e4.py`, `render_m1e4.py`: source and independently reopening verifier.

## Rebuild without chat context

Blender 5.2+ is required. From this package's directory:

```bash
blender -b source-m1e3-fast.blend --python build_m1e4.py -- \
  --frame 15 --cuts 2 --mode beauty --out my-frame15.blend --report my-build15.json
blender -b my-frame15.blend --python validate_m1e4.py -- --out my-validation.json
blender -b my-frame15.blend --python render_m1e4.py -- \
  --out my-frame15.png --samples 16 --resolution 720
```

Repeat with `--frame 1` or `--frame 30`, or move the knife to a new pose in the source file and rebuild. `--mode diagnostic` enables the 3D tubes in the final render.

## Key limitations

**The original underlying Geometry Nodes cutter stays live, but the high-detail locally refined snapshot is baked per pose.** It must be regenerated when the cutter moves. This is *not* a real-time adaptive Geometry Nodes CutSurface. Curve ends are trimmed with SDF at 60 sampled points per spline, not exact Boolean intersections. Synthetic filaments are artistic, not measured biology. Zero non-manifold edges does not prove absence of geometric self-intersections. We do not claim visual fidelity to Frucht.

See `report.md` and `manifest.json` for measured results, SHA-256, and file provenance. Prior M1e3 is kept unchanged.
