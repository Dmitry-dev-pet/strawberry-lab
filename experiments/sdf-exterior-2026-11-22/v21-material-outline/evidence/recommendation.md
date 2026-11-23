# v21 — isolate the cell-color outline gain

## Cause found in the owned v20B material

The saved `strawberry-v20b-halo-suppression.blend` matches SHA-256
`35fd1d81c51aea1cc8f4cd71c39a2815da87a1137056d32c3f78d4ab1cf649e4`.
Its actual material node graph contains an explicit pale polygon-outline overlay:

`fruit_rest → Voronoi Texture (3D DISTANCE_TO_EDGE, scale 2.7) → Map Range → Math.039 → Mix (Legacy).004 → Principled Base Color`.

The clamped linear Map Range maps edge distance `[0.006, 0.07]` to
`[0.55, 0.02]`. `Math.039` multiplies that by `0.10`, giving a pale-color
overlay weight from `0.055` near edges to `0.002` farther inside cells.
`Mix (Legacy).004` mixes the existing tissue color toward `(0.98, 0.64, 0.54)`.
That is a direct mechanism for a pale many-sided network in the color macro.
Whether it is the visually dominant contribution must still be established by
the matched render; the same Voronoi also feeds unchanged bump and roughness.

## One proposed candidate

In material `SDF v12 | continuous vascular fibers, restrained wetness (ARTIST)`,
set **`nodes['Math.039'].inputs[1].default_value` from `0.10` to `0.02`**.

This is an **ARTIST** choice: an 80% reduction in the explicit cell-color
outline weight. The overlay range becomes `[0.011, 0.0004]`. The node's
downstream path reaches only the Principled `Base Color` input. Keep all
node links, all other defaults and all nonmaterial data unchanged.

The original atlas B→pith mix, R→vascular color mix and G→mottling multiply
remain upstream and untouched. Their coordinates and transfer functions do not
change. Final rendered colors will change wherever the attenuated overlay
previously acted, including overlap with those regions; that is the intended
effect, not a claim of pixelwise invariant tissue colors.

## Exact invariants for the controlled comparison

- Source and candidate material graphs differ at exactly that one socket
  default; all links, colors, Voronoi parameters, bump/roughness paths,
  Principled settings and other materials remain identical.
- Packed original and core/halo image bytes remain identical.
- Geometry Nodes, core/halo controls, evaluated body vertices/topology and
  diagnostic attributes remain identical for the compared poses.
- Seed/calyx/source meshes, transforms, camera, lights, world, render settings
  and frame remain identical.
- Compare the actual existing macro and one fruit-wide cut/bite view at the
  same camera/light/sample settings. A flatter overall result is a possible
  tradeoff to record, not an automatic improvement.

No new wet layer, altered scattering, geometry displacement, vessel/pith map,
foreign source, or asset is part of this candidate. Some polygonal highlights
may persist through the deliberately unchanged normal and roughness branches.

## Preserved normal and roughness paths

The coarse `Voronoi Texture` is also the largest of three weighted
Distance-to-Edge height sources:

| Source | Scale | Weight node | Weight |
| --- | ---: | --- | ---: |
| `Voronoi Texture` | 2.7 | `Math.034` | 0.58 |
| `Voronoi Texture.001` | 8.5 | `Math.035` | 0.31 |
| `Voronoi Texture.002` | 24 | `Math.036` | 0.10 |

`Math.037` and `Math.038` add those sources into `Bump.Height`. The first
`Bump` has **Strength 0.19, Distance 0.017**. Its normal feeds the second
`Bump.001.Normal`, which adds the existing anisotropic noise height at
**Strength 0.075, Distance 0.007**, then feeds `Principled BSDF.Normal`.
The noise uses `fruit_rest × (1.25, 1.25, 0.18)` with Noise Scale 4.2.
These are shader bump settings, not verified geometric displacement depths.

The same coarse Voronoi distance goes through `Map Range.001`:
`[0, 0.5] → [0.33, 0.49]`. The existing noise-derived smoothstep term,
bounded by 0.045, is subtracted in `Math.040`; `Math.041` floors roughness
at 0.16 before the Principled Roughness input. Consequently, polygon-edge
regions can still have normal and reflection contrast after the color overlay
is attenuated. Do not change these paths during the first color-only A/B.

The tissue color branch is also preserved: atlas B mixes cortex
`(0.62, 0.045, 0.058)` toward pith `(0.89, 0.36, 0.30)`; atlas R multiplied
by 0.56 mixes toward the vascular color `(0.87, 0.57, 0.48)`; atlas G adds
the existing multiply modulation at factor 0.22. The proposed gain acts only
on the final pale outline overlay after those mappings.
