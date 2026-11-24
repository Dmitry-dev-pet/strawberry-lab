# Strawberry Lab — Frucht promotional video: display-state investigation

**21 November 2026.** Investigation, not an assertion about the unavailable commercial `erdbeere.blend`. Owner-supplied promotional video (duration **37.98 s**, **1080×1350**, **30 fps**), verified SHA-256 `cbe17cfd0ffa0e7697462892a28bd339e0b9666418276287499c49ca6bae684e`. Compared with owner-supplied Frucht Free Kiwi **0.4.3** source ZIP SHA-256 `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877` (46 Python modules). Frames are extracted directly from the original MP4 with OpenCV at exact 30-fps frame indices; NO synthetic imagery, image-generation, repainting, or interpolation used.

## Decision in brief

The visual gulf between our V4 network and Frucht at ~00:15 is *not established to be solely an anatomical/branch-shape difference*. At ~13–16 s the promotional scene shows an **exposed cutaway state**: orange achene-like terminals and white tubes occupy the region **beyond the red flesh that is currently visible**. This strongly suggests a **difference in clipping/visibility between tissue and at least some of the vascular/terminal geometry**, or another equivalent visualization effect. The full paid GN scene is missing; this **remains an interpretation**, not confirmation of specific node wiring.

The UI label `Core Fibers` displays **1.00** at **16.30 s**, when the vascular network is *not visible*. Accordingly, the presence of a high `Core Fibers` setting is **not sufficient to make fibers visible from every angle/cut state**. At 16.50 s, `Core Fibers` becomes **0.00** at the same time as **Bites=1** and a mode switch to `Cut · Bite`; the video cannot isolate the direct causal effect of the control.

## Evidence-by-time — visual observations, not parameter attribution

| Video time | Readable onscreen state | Observed on pixels | Inference limit |
|---|---|---|---|
| **13.10** | `Height=+1.3`, `Camera Orbit=646°`, `Cut · Oblique=0.25`, `Core Fibers=1.00` | Red exposed upper surface with pale branches and orange terminals; stem/leaves still visible | Many controls animate together; do not assign this appearance to a single slider |
| **13.30** | `Height=+1.0`, `Camera Orbit=648°`, `Cut · Oblique=0.64`, `Core Fibers=1.00` | Upper red flesh disappears; pale network and many orange endpoints remain where red body is absent | Visual evidence of non-identical *visible* masks (or a special display effect), not proof of implementation |
| **13.40** | `Height≈+0.8`, `Camera Orbit≈649°`, `Cut · Oblique≈0.83`, `Core Fibers=1.00` | Vascular network dominates above the remaining lower red flesh | A real cutaway, not an intact whole-berry comparison |
| **14.30** | `Height=−1.4`, `Distance≈0.48`, `Camera Orbit=653°`, `Core Cut Angle=0°`, `Core Fibers=1.00` | Extreme close-up of long opaque white trunks and side tubes with orange endpoints; red flesh only behind/below | Camera distance and cut setup change substantially; not a calibrated anatomical view |
| **15.10** | `Height=−1.5`, `Camera Orbit=653°`, `Core Cut Angle=10°`, `Core Fibers=1.00` | Central white cut-end structures and outer branches are prominent | Central-cut-angle slider appears to be in motion |
| **15.50** | `Height=−1.6`, `Camera Orbit=653°`, `Core Cut Angle=40°`, `Core Fibers=1.00` | Central white cylindrical cut-ends have different arrangement, while orange terminal fibers remain | Compatible with a local *core-cut* orientation change, **not proof** of bending all seed-linked fiber paths |
| **16.10** | `Height=−5.6`, `Camera Orbit=673°`, `Cut · Oblique=0.28`, `Core Fibers=1.00` | External skin dominates, with no comparable visible white network | Visibility depends on camera/cut, not only Core Fibers |
| **16.30** | `Height=−6.2`, `Camera Orbit=687°`, `Cut · Oblique=0.00`, `Core Fibers=1.00` | Skin-covered fruit; internal white network not visible | The strongest counterexample to treating `Core Fibers=1` as an automatic exposed-network mode |
| **16.50** | `Height=−6.5`, `Camera Orbit=700°`, `Core Cut Angle=0°`, `Bites=1`, `Core Fibers=0.00`, `Cut · Bite=0.00` | Biting/exterior geometry and camera are different | **Confounded intervention**: cannot isolate whether `Core Fibers 1→0` removes any geometry by itself |

**Important correction to previous reasoning:** The `Height` label sits next to `Distance`, `Look Height` and `Light Spin`, with `Camera Orbit` in the opposite camera-control column. It ranges from above +1 to below −6 in the video, markedly outside the public strawberry **form** range in the Free add-on. `Height` is **likely camera elevation**, not the `laenge/Length` strawberry morph parameter and not proven to be the knife-cut height. Therefore saying *"the clipping plane descended because Height changed"* is **not justified**. In the same period `Cut · Oblique` also changes, and the view rotates and zooms.

## Source-code cross-check — what can actually be verified

- Exact strings `Core Fibers`, `Core Cut Angle`, `Cut Oblique`, `Macro Lens`, `Look Height`, `Camera Orbit` occur **zero** times across the ZIP's 46 Python files. This establishes only that those **literal English labels** are not present in that source text, **not** that an equivalent paid control does not exist.
- `fruechte.py:65,69–74` does declare **different** strawberry properties: `Vessel Strength` (shader-class), `Vessel Strands` (default 28), `Strand Width`, `Fiber Width`, `Fiber Sag`, `Halo Width`, and `Fiber Pattern`. Their identification with onscreen `Core Fibers` is **unverified**. Do not map `Core Cut Angle` to `Fiber Sag` without the paid graph.
- The `leitbuendel.py` source computes a 3-D vascular network to the **original GN achene positions**, rasterizes core and halo, and precomputes a 256³ atlas. The author code establishes seed-linked source geometry but not how the promo scene **clips, hides, or displays** its seed/fiber/tissue objects.
- `schnitte.py` and `schnitt.py` include cutting logic and multiple states, but the paid `erdbeere.blend` and its shader/node connections are **absent** from Free 0.4.3. It is impossible to prove whether the promotional scene renders upper skeleton on purpose or uses a prepared/animated preview from these sources.

## Competing interpretations

1. **Differential visibility / clipping of distinct geometry classes (primary, unconfirmed).** Flesh is cut away, while the full/rest-position vascular network and achene-end markers remain visible. This explains orange terminals above the red cutaway. Equivalent camera-space overlays or an intentionally separate pass could create the same look.
2. **Deliberately expanded/exploded structure (possible, unconfirmed).** The author may temporarily move or scale a fiber subset for a didactic shot. Needs motion tracking of relative marker positions vs whole original berry silhouette, matched orbit and seed coordinates. The provided changing camera prevents confirming expansion.
3. **Completely different biological branching rules (also possible).** Real differences in original branching curvature and carrier radius were already established by source audit, but **one promotional exposure state cannot quantitatively isolate them**. Both causes can coexist.

## Controlled Strawberry Lab follow-up (no new anatomy yet)

**A/B experiment on the exact same existing 539 achene-connected 3-D paths**, preserving all source geometry and camera:

- **Matched clip:** hide red flesh above a chosen cut plane and clip/hide the fibers/terminals with exactly the same half-space.
- **Independent clip:** apply the exact same cut to red tissue **but do not clip the 3-D paths or the seed-marker positions**. Record whether apparent long exterior "arms" emerge without changing any spline coordinates.
- **Visibility gate:** only in the independent-clip scene, compare visible `Core Fibers` style scale 0 vs 1 **as an independently named diagnostic parameter, not a claim of vendor UI mapping**.
- **Camera control:** hold the same projection, focal length, elevation and orbit while comparing; vary height/orbit as separate tests to determine occlusion.
- **Acceptance:** count unchanged 539 destination points, unchanged polyline checksums, compare exact visible regions and time states; label the author's frame as camera-incomparable. Do not write a new procedural anatomy generator yet.

**Interpretation:** if independent clipping reproduces the *type* of exposed white tubes and orange terminal points seen in the promo, then the missing feature is likely a **display-state/clipping mechanism** (not another random fiber network). If it does not, investigate orientation and morphology on comparable views. This test is **proposed, not performed in this audit**.

## Evidence and privacy

- Private `six-real-frames-controls.jpg`: six video frames at 13.10,13.30,14.30,15.50,16.30,16.50, with text labels **outside** source frames.
- Private `visible-fibers-vs-cut.jpg`: original 13.30,15.50,16.30 frames cropped/rescaled, no scene manipulation.
- The owner's video is already in private Drive; do not re-publish it or its frames to GitHub. Source-author ZIP and Blender data remain owner-private. GitHub may contain this independently written source-method audit and the hash/timestamp manifest only.
