# v22A — Different bite silhouette (research-only, 2026-11-23)

User correctly identified an architectural mismatch in the visual comparisons: the Frucht film frames at 18.0–19.5 seconds visibly show a large open missing chunk and ragged lower/side contour, whereas our v21B had a near-circular scooped hole on the front of the fruit. The film does not disclose the exact proprietary cutter graph.

**One controlled ARTIST change:** reposition and nonuniformly scale the existing native closed 6,050-vertex scalloped SDF cutter, leaving our own source geometry, all materials, seeds and rest-space fields unchanged.

| Variant | Location XYZ (mm) | Scale XYZ |
| --- | --- | --- |
| v21B | 4.072440, -13.537471, 26.380232 | 12, 12, 12 |
| v22A | 1, -9, 6.5 | 23, 22, 21.5 |

Original owned editable v21B SHA-256: 92e7e288f7851ec8c5e68897d5f7f19b5b5f73310a6d7d9084836f854c258a13. v22A scene from original executed script SHA-256: 7447470b1fdd21cb7391d8b038ebfcbdc4993d54d03db614e23507abc3c22b11. A portable independent builder was also smoke-tested with identical cutter transform; binary scene SHA may differ with Blender serialization.

**Observed real Blender 5.2.4 QA:** in the main candidate and translated candidate, evaluated body was one component, zero nonmanifold edges and positive signed volume: 271362 vertices/14188.29 mm3 and 271018 vertices/13647.55 mm3 respectively. The *third planned scale-pose check timed out*, so no 3/3 claim. Cutter/achene triangle intersections, calyx clipping and arbitrary poses were not newly proven.

**Actual 640x640 / 24-sample Blender Cycles** with unchanged studio camera/material shows a lower missing edge rather than an interior round bowl. Visually the missing-volume category is closer to Frucht, but the exposed tissue is dark and near-horizontal, the ragged strands and wet look are missing. **This experiment does not meet Frucht visual fidelity.**

Reproduce with Blender 5.2.4 and the verified original v21B: `blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python build_v22.py -- --source /private/strawberry-v21b-soft-cell-outline.blend --out /private/v22a.blend`.

The user-private film, extracted author frames and comparison montage are only in the conversation, not committed to this public branch. No paid Frucht or GPL source trees copied. Do not merge into main. Next hypothesis: a multi-lobed irregular open-side cutter plus cut-local 3D tissue detail, tested with a valid cut-face camera.
