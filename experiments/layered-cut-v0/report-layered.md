# Layered Cut v0 — experimental conclusion

**Date:** 21 November 2026. **Source:** owned Volume First V4 and v0. **Renders:** true Blender 5.2.4 Cycles, same camera and light.

## Hypothesis and intervention

Earlier V1–V4 attempts changed vascular morphology to imitate a Frucht promo still. After the frame-based video audit, we hypothesized that the rendered scene contains independently clipped components. We tested *exactly one controlled change*: whether the halfspace plane `Y=0` clips all vessel/marker geometry in addition to the red flesh, or clips only the red flesh.

**Controls:** unchanged complete 28 core tracks, 539 branches, 539 octahedral destination markers and original physical v0 78,626-vertex half-fruit mesh, same cut orientation, camera transform, orthographic scale, light transforms and materials. A mirrored copy of the complete paths is never moved. Derivative clipped curves are calculated from exact 3D segment intersections with `Y=0`.

| Component | A: matched clip | B: flesh-only clip |
|---|---:|---:|
| Physical opaque body | 78,626 vertices | same 78,626, identical coordinates/material |
| Main carriers | 15 retained curve pieces | 28 full tracks |
| Vascular branch paths | 283 retained curve pieces | 539 full tracks |
| Achene diagnostic markers | 270 markers | 539 markers |
| Camera / studio | same | same |

**Result:** side-by-side actual Cycles renders show dramatically more pale vascular curves and seed-like orange termini when the complete skeleton remains in front of the cut tissue. This supports the **display-state hypothesis** as a meaningful explanation of the large visual difference in the promo, independently of anatomy. It cannot establish the exact wiring of Frucht's unavailable paid scene, nor does it resolve insufficient botanical fidelity of our source curves.

## Independent toggles

Blender file has A/B scenes and eight independent named geometry collections each, with meaningful native Blender Outliner exclusions. An additional **embedded optional** sidebar script exposes per-layer `Off / Clipped / Full`, plus flesh/transparent context; an automated headless callback test confirms the controls change real collection flags without modifying source geometry.

## What failed / not claimed

- No movable knife; the flesh cut is a saved *static* half-fruit at `Y=0`. This proves differential clipping only at one fixed plane.
- The normal body is the original static v0 tissue substrate; it is **not** volume-integrated with V4 vascular geometry. The pale lines on its cut do not automatically correspond to V4 paths.
- Orange points are diagnostic octahedra from our V2, not anatomical achene meshes.
- Cell microgeometry, juice, independent central parenchyma/pith and physical seed geometry are absent as separate modules. Do not claim they can be switched until they exist.
- A promotional frame with different camera, angle and animation state is not an image-quality benchmark or proof of the vendor's specific implementation.

## Decision

Retain layered cut model as a **successful, independently reproducible display-layer experiment**. It is a better explanation for the exposed strands than increasing branch count or tip curvature alone, but does not demonstrate Frucht parity. Next step only after choosing the target product workflow: make the cut plane movable with a shared signed-distance control for each layer, implement real pith/cells/juice as actual objects/fields, and test one credible static macro appearance before attempting full live animation.
