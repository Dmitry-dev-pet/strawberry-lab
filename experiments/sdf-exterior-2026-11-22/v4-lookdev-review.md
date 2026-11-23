# Strawberry Lab SDF exterior — v4 lookdev review (22 November 2026)

**Outcome: engineering PASS, partial visual improvement, Frucht-level visual acceptance FAIL.**
V4 is not a new fruit engine and is not accepted into `main`. It refines the editable v3 sculpted-exterior proof without changing seed/cutter architecture.

## Specific changes

- 192³ original-coordinate volumetric RGB field (packed 3072×2304 PNG) rather than the v3 128³/2048×1024 field. The same packed atlas is sampled on plane and spherical-bite cut surfaces.
- 264 original seed anchors supply independent 3D Bézier curves. Every third curve uses a stronger, narrow main filament; the rest are faint twigs. The packed field uses maximum blending to reduce broad overbright clusters. Additional low-opacity 3D wisps improve continuity under different cutter orientations.
- Cut-only shader: adjusted fruit-pulp colors, softer subsurface, varied roughness, 3 Voronoi layers for cell and wet-film normals, faint cell-edge tint. Geometry-only displacement reduced from 0.27 to 0.16 mm on the cut.
- Source skin, physical pits, 264 seeds, crown/stem and the working SDF cutters are unchanged. Seed center threshold remains 0.95 mm, proven larger than 0.813 mm original seed-solid radius.

## Blender re-open and motion tests

- Blender 5.2.2 LTS, saved v4 `.blend` reopened with script autoexecution disabled.
- Whole 157,250, plane 48,590, bite 86,160 **evaluated vertices**; nonmanifold edges **0/0/0**.
- Packed 192³ image in Blender; `fruit_rest` attribute on both cut surfaces.
- Two independent cutter poses each: plane initial/moved+rotated, sphere initial/moved+enlarged. Four distinct computed surfaces; **0 nonmanifold edges** and **0 retained-achene vertices inside any cutter**.
- Remaining whole seeds: plane initial **93**, moved **66**; sphere initial **227**, moved **215**. This conservative hide-entire-achene policy can leave holes around the cut rim.

## Real visual A/B, not ImageGen

Three Blender Cycles v4 renders: `sdf-v4-plane.png`, `sdf-v4-bite.png`, `sdf-v4-macro.png` at 860×860 px, 36 samples, same original studio and cutter poses as v3. The macro camera is closer. Source binaries and images remain owner-local under `build/sdf-vertical-slice`; the public repository contains source and numeric receipts only, per existing policy.

Compared qualitatively with the earlier v3 renders:

| Area | V3 | V4 | Acceptance |
| --- | --- | --- | --- |
| Planar vessel texture | Broad repeated pale spots | Narrower longitudinal streaks plus scattered short pale points | Better but still artificial |
| Bite texture | Blurry, mostly wide radial blotches | Clearer wisps, but central blown-out/glossy patch and unnaturally smooth sphere | **Fail** |
| Macro cells | Thick cloudlike vessel marks, smooth pulp | Thin veining and faint cellular hexagonal network | Better texture; too uniform, insufficient wet 3D relief |
| Live geometry, seed culling | Passed | Still passes | **Engineering pass** |
| Crown | Not clipped | Still not clipped | **Fail** |

### Next (not part of v4)

Do not further tweak cut geometry. Improve the **independently exposed cut face** and its light transport: visible individual moist cells/pores at plausible scales, physically restrained thin fiber highlights (not sheet-like streaks), less concentrated specular patch on bites, and outer-edge tearing. Match lighting and camera with the owner's Frucht reference and test a second non-collinear cut. Distinguish render aesthetics from independently measured fruit anatomy (still **ARTIST**, not scientific data).

**Dependency:** stacked on draft PR #43; both PR #43 and v4 remain unmerged until visual acceptance.
