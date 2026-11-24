# Exact juice geometry — 24 November 2026

Continuation of PR #50 from `43668075a366637311517e33a95e17cf29cf6b72`. Independent ARTIST optical interfaces, not copied Frucht graphs or fluid simulation. Source exact-refine.blend SHA256 `0868e656bc1d4c68c1a0f2b555bb5443f5f2527e34ca8bab0e55a1ae9d656e67`. Output exact-juice.blend SHA256 `250732d06c5c2cfbc24f531612cda2672755ba8cad50afddd0a2a894553954fb`. Blender 5.2.4 LTS cd5dc428cce1.

The native separate object (89 geometry nodes) consumes actual evaluated Exact cap mesh. Three independent rest-space smooth-centre envelopes and protected-surface/axis falloff select connected patches on cap-interior faces. The original pre-relief position and normal define a liquid height independent of the actual cell relief. Its signed normal gap is stored, and open rims are tucked at least 0.018 mm below source points along those normals. The shader is a thin Fresnel-reflective/straight-through transparent interface, with transparent shadow rays. This is an open intersecting optical surface, not a closed fluid, measured liquid thickness or proof of all-point contact. `juice_gain` defaults to 0. No output in Fast, whole or disabled cell relief. No copied author code, parameters, assets or templates. Original geometry, material assignment and tissue fields unchanged.

## Evaluated saved-scene gates

All six cases pass against the pinned exact-refine source. The initially killed parallel .20 plane process (exit -9) was rerun individually and completed PASS. Other negative/interrupted render logs remain evidence, not accepted results.

| Pose | Voxel mm | Juice vertices | Components | Open boundary vertices | Gate |
|---|---:|---:|---:|---:|---|
| Whole | .20 | 0 | 0 | 0 | PASS |
| Plane | .32 | 11832 | 165 | 6132 | PASS |
| Plane | .20 | 26890 | 345 | 11109 | PASS |
| Tilted/deformed | .20 | 31347 | 313 | 12190 | PASS |
| Bite | .32 | 12017 | 129 | 5555 | PASS |
| Bite | .20 | 18868 | 212 | 7908 | PASS |

Body, seed mesh and Fast snapshots (coordinates, triangles, material indices and selected attributes) equal baseline. Gain 0->1->0->1 geometry deterministic, source cap-interior point membership verified, no >2-face or wire edges, inconsistent edges or degenerate triangles in juice. Open edges intentional; all sampled rim vertices have <= -0.0179 mm signed normal clearance. Positive clearance and buried points both present. Geometry checks do not prove physical wetting or full self-intersection-free topology. No photographic parity or visual acceptance.

## Reproduce

Use exact-refine.blend with verified hash. Put prior owned build_split.py and qa_split.py in deps/ (included in evidence archive). Each output must not exist. Run sequentially to bound RAM.

```
blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_juice.py -- exact-refine.blend exact-juice.blend
for spec in 'whole .20' 'plane .32' 'plane .20' 'tilted .20' 'bite .32' 'bite .20'; do
  set -- $spec
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_juice.py -- exact-refine.blend exact-juice.blend "$1" "$2" "qa-$1-$2.json"
done
```

The dry plane diagnostic was rendered in Cycles at 600x600 / 24 samples; original wet render was interrupted and is not claimed completed. The follow-up matched optical study uses its own render settings and frozen juice geometry.
