# Strawberry Lab — Volume First v2 / seed-anchored vascular proof

A **fully independent Strawberry Lab** comparison of 494 free-ended spatial fibers (v1) against a new network with actual seed-centroid targets. This is not the paid Frucht model and no third-party node graphs or source code are redistributed.

## Key facts

- Source: 539 achene mesh components in the owned M1e5/M1a GN scene, and 539 previously authored vascular splines with matching endpoints. Pairing is one-to-one (max source endpoint-to-seed center distance <0.005 Blender units).
- Reprojected these **existing seed centers** into the unrelated, owned Volume First v1 fruit silhouette. This second-stage shape mapping is deliberately approximate; it is not the original M1a fruit skin mesh.
- Independent core-and-branch generator: 28 main longitudinal carriers, 539 branches terminating 0.019 BU below the corresponding remapped seed marker.
- Controls modeled after author-declared names: `--strands`, `--strand-width`, `--fiber-width`, `--fiber-sag`, `--pattern`. Tested 14/28/40: achene endpoint coordinates stay invariant; only internal trunk network/paths change.
- Three actual Blender 5.2.4 Cycles views and editable `.blend` with the original v1 paths present but hidden.
- **Limit:** this is a *structural/diagnostic* demonstration. The existing cut/skin geometry, colors, and cellular tissue were NOT rebuilt from the new vascular network. The fruit shell and seed markers are artistic, not biological calibration.

## Reproduction

For source extraction, run Blender 5.2+ on `input-m1e5-live-exact.blend`:

```bash
blender -b input-m1e5-live-exact.blend --python extract_original_achene_centers.py
python generate_seed_linked_network.py
python generate_seed_linked_network.py --strands 14 --out v2-control-14-strands.npz
python generate_seed_linked_network.py --strands 40 --out v2-control-40-strands.npz
blender -b input-v1-494-fibers-inspection.blend --python build_blender_seedlinked.py
blender -b v2-seed-linked-539-diagnostic.blend --python validate_v2.py
blender -b v2-seed-linked-539-diagnostic.blend --python render_v2.py -- --view only --out v2-only-539-anchored.png
blender -b v2-seed-linked-539-diagnostic.blend --python render_v2.py -- --view ghost --out v2-translucent-fruit.png
blender -b v2-seed-linked-539-diagnostic.blend --python render_v2.py -- --view cut --out v2-actual-cut-overlay.png
python make_comparisons.py
```

`make_comparisons.py` reads `private-frucht-video-ref15.jpg` from the owner-provided source and **must not be run for a public publish of its montage**. The original commercial `.blend` is not available.

## Reading source evidence

See `report.md` for the distinction between visible author **Core Fibers** UI (not identified with any one code field), the code-declared **Vessel Strands** and related settings, and the source algorithm connecting to achene instances. This report describes the Frucht archive; it copies none of its code.
