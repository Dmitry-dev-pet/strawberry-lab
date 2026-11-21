# Volume-first strawberry prototype — engineering and visual audit

**21 Nov 2026 · Blender 5.2.4 LTS · independent static experiment**

## Why this is a new line of work

M1e1–M1e6 were useful demonstrations of Boolean/SDF geometry, editable cutters, BMesh subdivision and GN-only topology, but each used a simplified source fruit. Most of the subsequent changes optimized geometry and responsiveness without creating convincing internal tissue. This trial begins **from a single precomputed 3D tissue substrate**, not from a cut face.

## Original reference observations

Based on the owner-supplied private Frucht demonstration, frame ~00:10.5:

- Large saturated red-orange cortex surrounds an **elongated pale central pith**. A large spherical void is **not** the dominant feature in that frame.
- Pale fibrous bands radiate outward, and the cut surface contains microscopic light granules and varied specularity.
- At ~00:15 the author exposes numerous discrete curved white fiber-like 3D elements in a demonstration view. This supports the importance of spatial strands, but does **not** reveal their full paid node graph or prove their biological nature.
- Our previous giant round cavity / near-uniform pink cut did not match this reference.

The reference crop appears only in **owner-private** image comparisons, not in the public GitHub repository.

## The independently implemented 3D substrate

- Source domain: 150 × 150 × 150 voxels, x/y [-1.30,1.30], z [-1.23,1.05]. Deterministic RNG 20261121.
- **146 spatial paths:** 122 outward branching curve paths and 24 elongated central core paths; all stored explicitly as 3D polylines.
- Rasterized 3D distance-to-fiber field, a radially varying 3D pale pith region, a localized 3D amber center, spatially continuous radial sheets, anisotropic cellular microstructure and physically displaced surface-height field.
- Precomputed `tissue_3d.npz` supplies color/height/pith/filament signal to every cut; no per-angle authored 2D texture. Fine shader noise reads saved original 3D rest coordinates, not generated UV/camera position.
- Each 0°, 32°, 82° center-plane section is built as a closed physical half-fruit: rear red skin + sampled flesh plane with shared seam vertices. All three objects live in one `.blend`; only one is rendered at a time for fair comparison.

## Geometry and invariants

| Cut angle | Vertices | Faces | Non-manifold edges | Connected components | Degenerate faces |
|---:|---:|---:|---:|---:|---:|
| 0° | 78,626 | 78,960 | 0 | 1 | 0 |
| 32° | 78,626 | 78,960 | 0 | 1 | 0 |
| 82° | 78,626 | 78,960 | 0 | 1 | 0 |

All 32 tested central-axis coordinates yield identical sampled color across the three orientations because they refer to the same exact 3D points. The three full images differ because the physical 3D color/height/filament fields are not rotationally symmetric.

## Controlled visual evidence

- CPU Cycles, 840 × 960, 20 samples, same orthographic camera and identical lights, without retouching actual pixels.
- `three-cuts-one-volume.jpg` compares the three genuine renders.
- `frucht-versus-new-poc.jpg` is a private two-way juxtaposition of an authorized 00:10.5 video frame with our 0° frame. It is not proof of parity.

**Visual assessment:** silhouette and central red-vs-pale anatomy are closer to the chosen reference than the former spherical-cavity prototype, and spatial patterns remain coherent under azimuth changes. But the result is **still far below Frucht** in precisely localized thin vessels, porous tissue geometry, realistic light transmission, fruit skin/seeds and leaf shape. Our large core is still smooth, and many bundles are diffuse because the 150³ sampling resolution is too small for true sub-millimeter fibers.

## What this does NOT prove

1. This is not a general moving Boolean cutter — the three section angles are prebuilt via an independent analytic 3D fruit silhouette and sampled volume.
2. A closed mesh proves topological closure, **not** lack of every self-intersection or botanical correctness.
3. Our curve shapes and region mixing coefficients are artistic. Do not present them as real strawberry histological measurements.
4. We have not reproduced the author's commercial `.blend`, node graph, fine 256³ fiber atlas or photographic look.
5. The sequential viewport or live performance of any earlier Strawberry Lab engine is not improved by this prototype.

## Decision gate for next experiment

Instead of returning to M1e7 performance development, refine one static macro section toward the Frucht target. Next discriminating experiment: **represent central vascular bundles as thin explicit coherent 3D geometry / higher-resolution distance fields** (and compare close-ups under the same studio light), then test whether the gain survives the 82° section. If it does, only then integrate that substrate into a live knife.
