# v17 — original v12 vascular field intensity and anti-alias A/B (22 Nov 2026)

**ENGINEERING PASS · VISUAL FAIL. Research only, keep draft PR #43 open; do not merge or promote to main.**

## Motivation and exact scope

Independent v16 cap-only measurement showed strong vascular field R≥0.30 covering only 1.84% of the planar and 1.22% of the bite cap, although the original 3D source field was mostly volume-connected. The goal was to distinguish insufficient field intensity from insufficient spatial/physical structure, without changing the existing strawberry generator, cutter, achenes, leaves, shaders, skin, tissue G/B/A channels, or camera.

The verified source is the **unchanged owner-private v12** editable Blender scene, SHA-256 300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410cbb405b7. Its source image is a packed 16×12 tile atlas representing 192³ continuous rest-space R/G/B field. Both original Geometry Nodes samplers and the cut-face material use this same image. All proposed field values are ARTIST, not measured strawberry vessels. No third-party Frucht node trees, textures, images or proprietary code were imported.

Reproduction source (Blender 5.2.4 + NumPy; external Python + SciPy for smoothing): v17_restfield_repro.py in this same directory. The script was independently exercised: extract, candidate calculation and saved-scene application. Both generated red arrays are byte-identical to the independently analyzed v17 trial arrays. The source file explicitly refuses to overwrite an existing variant scene.

### Controlled alternatives

- v17A: Rnew = 1 − exp(−3 × Rold), clipped to [0,1], no new vessel geometry or topology.
- v17B: Gaussian smooth Rold with physically scaled sigma 0.22 mm along all rest-space axes (z pitch 51/191 mm; y/x pitch 36/191 mm), then identical transfer.
- Both: re-pack ONLY vascular R, leave G/B/A exactly unchanged. Original source v12 remains unmodified.

## Measured field coverage

Area fraction of exposed cap with the **mean quad R≥0.30**, before any physical remesh:

| Mode | Original v12 | v17A | v17B |
| --- | ---: | ---: | ---: |
| Plane | 1.84% | 13.11% | 6.23% |
| Bite | 1.22% | 9.98% | 4.09% |

This preliminary calculation samples source rest coordinates from genuine v12 Blender evaluated caps, not arbitrary 2D hand-painted maps. The original independent trilinear sample and native GN evaluated vertex attribute agree to approximately 1–1.5e−6 mean absolute difference.

**Actual reopened v17 evaluated cap area**, after native GN field-driven microdeformation:

| Mode | v17A | v17B |
| --- | ---: | ---: |
| Plane | 13.04% | 6.21% |
| Bite | 9.91% | 4.06% |

These are separate measurements on saved rendered geometry; do not conflate with the fixed v12 cap predictors. The Blender image red arrays have max error below 1e−6 on independent readback. Unchanged G/B/A fields are exact; both native GN field image inputs and material image textures reference the same newly packed image. All source tissue positions remain unmeasured ARTIST values.

## Real independent geometry QA

Official Blender 5.2.4 LTS Linux restored from 17 owner-private Drive parts, SHA verified. Independently reopened baseline v12 / v17A / v17B with script autoexecution disabled. For **each variant, five evaluated states**:

1. Whole solid
2. Planar cutter at original position
3. Scalloped spherical bite at original position
4. Moved + rotated planar cutter (Y +3 scene-mm, X rotation +10°)
5. Moved + scaled spherical cutter (X −4 scene-mm, scale ×1.13)

All **15/15** real evaluated bodies have **0 nonmanifold edges, strictly positive signed volume, and positive non-degenerate faces**. Both R variants retain original body/cutter topology in matched poses, and GN uses the newly saved shared rest-space red image, not a separate preview graphic.

Saved scene SHA-256:
- v17A: bd19ee7871b40e60fc19d5c11fb6cde85e4d3959b9c137d4af475bc916afd09d
- v17B: 80bfe8820a4f03de9b33cfa1f9a0457df96720ed1175a02511ac7188faf4a53d

Caveat: v17 did not independently rerun exact triangle-triangle cutter intersections for every retained achene/calyx; source GN seed/cutter policy is unchanged and no claim of a repaired seed-clipping contract is made.

## Genuine matched Cycles A/B and final result

Six real Blender Cycles CPU PNGs, all **640×640 and 24 samples**, fixed studio camera/lights: planar and spherical bite for v12, v17A and v17B. The seven-channel image original/exposure were not altered between cases; a separate contact sheet crops native bite render pixels for visual inspection (no generative image). All private binary assets and original Frucht reference frames remain outside public GitHub.

Full-frame pixels with max absolute RGB channel difference >0.01 versus original v12 (a change measurement, **not** a perceptual-realism score):

| Shot | v17A changed | v17B changed |
| --- | ---: | ---: |
| Plane | 7.773% | 10.682% |
| Bite | 4.603% | 6.288% |

**VISUAL FAIL:** v17A exposes stronger but too regular bright white streaks; v17B creates softer fuzzy halos; neither looks like naturally torn juicy parenchyma. The scalloped sphere bite **remains a smooth glossy scooped bowl**, not the irregular physically torn lip seen in the owner-provided Frucht promo. Stronger connected-looking source intensity alone does not solve physical cut-cell topology or torn flesh. This is not approved Frucht fidelity, despite engineering PASS.

## Decision and storage

Leave v12 unchanged, preserve v17A/B as **negative controls** for future experiments. Neither replaces v8/v12 or enters main. Next narrow hypothesis should test physically meaningful 3D fibrous/torn structures intersecting BOTH arbitrary cap poses, with cut-local geometry and a matched visual comparison; **do not** repeat global R gain, Voronoi amplitude, gloss or separate detached white tube proxies.

Source code and this numeric research report are stored in existing draft PR #43. Editable scenes, packed arrays, all six true Cycles PNGs and their SHA manifests, independent pose QA and enlarged A/B comparison are **owner-private conversation artifacts**, not public GitHub assets. No Google Drive upload is claimed for v17. Original commercial Frucht strawberry graph was not available and was not reproduced verbatim.
