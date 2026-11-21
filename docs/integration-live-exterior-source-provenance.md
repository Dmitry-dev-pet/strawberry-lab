# Integration slice 1: owned source provenance

This integration branch starts from `experiments/live-layered-cut-v1` commit `0aa85fa57eec5d67a6b8eba6f71fa35edcb08ba4` (PR #29, stacked on #28). It does not merge the experiment into main.

## Verified inputs

- Original owned live scene: `strawberry-live-layered-cut-v1.blend`, 48,048,054 bytes, SHA-256 `56b6d516e8794fb855512978e90e37cd754374a594fb4c5103e672c960a031cf`.
- Authorised download: private [Drive source](https://drive.google.com/file/d/1FSf6o2fIZ5oSw4H77MhY-uM6Q2HWTWgI/view), materialised as `build/inputs/live-source.blend`. Sharing was not changed. Hash checked against `assets/manifest-live-layered-cut-v1.json`.
- Exterior helpers: `src/build_strawberry_exterior.py` and `src/exterior_shape.py` restored from owned PR #13 commit `2e8f3bbda10f47371689c5e4eb1d6d924844a756`. Reuse does not imply using its berry surface as the integration hull.
- Existing `FruitContext` and measurement registry in this branch provide specimen identity and millimetre reference metadata. Kiwi cell means must not be transferred into strawberry.

## Parent source check, 21 November 2026

An independent headless Blender **5.2.2 LTS** process reopened the downloaded source and ran an unchanged copy of the PR29 `validate_live_cut.py` under `build/baseline-qa/`. All four poses passed: Y=0, Y=+0.34, Y=-0.26, and Z rotation=32 degrees. Original 28+539 spline data matched their source digests. Retained evaluated body vertex counts were 15,646 / 8,374 / 21,552 / 15,603. Maximum cap-plane error was 2.55e-8 original model units. These are baseline measurements, not integration results.

## Slice constraints

Use exactly one canonical live-cut hull and one control. New exterior seeds are artist-rendered attachments projected to that hull. The 264 PR13 achenes and 539 PR29 diagnostic marker locations are different populations; the first slice may preserve the diagnostic network as a separate warning-labelled layer without claiming correspondence. No new vascular model, measured histology or Frucht parity is implied. Native cap geometry and shader-hidden diagnostic tube surfaces have different export guarantees.

All old scenes and generated assets remain unchanged. New binaries belong under a fresh local build directory and private Drive version folder, never in public Git. User's live Blender scene remains under parent control.

## First assembled output

The editable scene and paired 650 px / 16 sample Cycles PNGs are saved in the fresh owner-private [integration folder](https://drive.google.com/drive/folders/1xSyKtxwMMPvYeY90kYMOseCRZTMlKq8K). Four files were downloaded through the authenticated connector and verified byte-identical. The downloaded .blend reopened and passed the same actual-geometry QA; source digests and cut geometry counts agree. See [manifest](../assets/manifest-integration-live-exterior-v1.json) and [build/edit/limitations](../experiments/integration-live-exterior-v1/README.md).

The body remains the original PR29 hull with a new exterior material, not the PR13 silhouette. 48 mm nominal height maps from FruitContext to 2.16 original model units; the resulting width is about 40.76 × 39.90 mm and is explicitly artistic. Skin pits are bump relief, not the PR13 mesh depressions. No additional cell solid geometry, unified biological seed-to-vessel mapping, whole-fruit GN rewrite or export parity is claimed. Four knife poses produce closed evaluated bodies and capped cut surfaces, while the original spline coordinates/radii and marker meshes remain unchanged.

Four legacy test fixture paths were repaired to the committed data/morphometry/measurements-v1.json. The full 107-test suite now runs directly from this checkout without temporary fixture copies. Independent Astra review is tracked separately in the working task.

## Review result and corrected build

Independent Astra review found an actual crown topology defect and two validator false passes. Parent changed crown Boolean solver to Manifold, required closed positive-volume meshes for every retained exterior part, preserved the source cap-node graph after its explicit coordinate substitution, and checked diagnostic transforms relative to the hull. The corrected saved scene passes all five poses and rejects the two deliberately damaged scenes. The first uploaded draft remains immutable but is superseded; the asset manifest points to corrected private files.
