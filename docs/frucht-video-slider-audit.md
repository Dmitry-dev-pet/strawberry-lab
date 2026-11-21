# Frucht strawberry video sliders — visual audit (2026-11-21)

**Sources:** Original 38-second video [private reference](https://drive.google.com/file/d/1Aj17g8cIVZ-enECJAHUIXrDektWmVA-b/view), and owner-supplied [Frucht Free Kiwi 0.4.3 ZIP](https://drive.google.com/file/d/10yqWZY0hhrtACwLAEMHZPvJBdlfEjplv/view). The Free archive contains the strawberry-specific parameter registry and portions of independent shape code, **not** the closed strawberry `.blend` node tree. No screenshots or third-party code are checked into this repository.

## Sliders actually legible in the video

| Time | On-screen controls | Sample value |
|---|---|---|
| 00:01–00:03 | Height, Distance, Look Height, Light Spin, Camera Orbit, Hip, Tip, Notch, Oval, Lean X/Y, Furrows, Notch Balance, Belly, Bend, Bumps | At 00:02: Hip 0.40, Tip -0.50, Furrows 0.40 |
| 00:05 | Leaf Style, Leaf Count, Seed Spread, Twist, Focal Length | Leaf Style 7; Leaf Count 6; Twist 0.50 |
| 00:10–00:11 | Cut · Plane, Fill Light | Cut · Plane 0.61 → 0.90 |
| 00:16 | Cut · Oblique, Core Cut Angle, Core Fibers, Macro Lens, Wobble | Cut Oblique 0.49; Core Cut Angle 40°; Core Fibers 1.00 |
| 00:17–00:18 | Bites, Shake, Core Fibers | Bites 1 → 2; Core Fibers 0.00 |
| 00:22 | Hue, Leaf Hue, Seed Hue, Refill | Hue -230°; Leaf Hue -75°; Seed Hue -130° |
| 00:24 | Slices, Shake | Slices 1.00 |

**Caveat:** Different controls, camera, light and animation change simultaneously. These are observed UI labels and snapshots, **not controlled parameter-response experiments**. Promotional overlay scaling may differ from the add-on's Python API.

## Author-declared strawberry shape parameters in the free source

In `fruechte.py`, the `ERDBEERE_FORM` registry provides exact English control names and declared limits. These are source-code ranges, **not bounds inferred from the video**:

| English label | Internal key | Min | Max |
|---|---|---:|---:|
| Tip | spitze | -1.00 | 0.25 |
| Hip | huefte | -0.20 | 1.00 |
| Belly | bauch | -0.15 | 0.80 |
| Notch | kerbe | 0.00 | 0.25 |
| Furrows | furchen | 0.00 | 0.40 |
| Oval | oval | 0.00 | 0.12 |
| Bumps | beulen | 0.00 | 0.10 |
| Twist | drall | -0.80 | 0.80 |
| Bend | krumm | 0.00 | 0.10 |

Video **Notch Balance** likely resembles source `kerbe_ungleich` / `Notch Skew` (-1..1), but wording differs. Video **Lean X/Y** may correspond to `schief_x/y` / `Skew X/Y` (-0.3..0.3), **not proved identical**, especially since a video frame shows -0.4. Video **Height** is not demonstrably the same quantity or scale as source `laenge` / `Length` (-0.3..0.4).

In `formen.py`, author functions associated with the notch and furrows implement *separate spatial shape deformations* (localized bell-shaped weighting; circumferential wave modulation). There is also inverse-coordinate mapping that is architecturally relevant to stable rest-space sampling after deformation. This audit reports engineering principles only; no GPL code or node graphs are copied.

## Critical author-declared visual controls not all shown in the promotional overlay

The same registry's `ERDBEERE_EXTRA` includes, with declared ranges:

- **Seeds/skin:** Pit Depth 0..3; Pit Width 0.5..2; Pit Noise 0..4; Seed Count/Size 0.4..2; Gloss 0..1; Scatter 0..2; Scatter Depth 0..4; Edge Width 0.03..2; Edge Gloss Position/Fade 0..0.5.
- **Cut flesh/interior:** Cavity 0.2..2; Vessel Strength 0..2; Zone Strength 0..2; Flesh Saturation 0..2; Flesh Brightness 0.3..2; Vessel Strands 6..48; Strand Width and Fiber Width 0.3..2.5.
- **Presentation:** The video separately exposes cut modes, bites, slices, color hues, light/camera and macro lens. Those should not be mistaken for all being fruit-mesh parameters.

## Consequences for our own next A/B experiments

1. **Silhouette presets:** independent Hip, Tip, Notch, Furrows, Belly, Oval and Bumps, identical camera/lighting; do not port Frucht GPL implementation.
2. **Seed contact and skin material:** pit geometry + edge gloss + scattering. Render fixed seed counts and controlled slider differences.
3. **Cut fidelity:** separate controls for Cavity, pulp zones, pale fibers and genuine inner wall material; compare two orientations of a single retained 3D cavity.
4. **Action/rendering:** treat Cut Plane/Oblique, Bites, Slices and Camera/Light as independent operations, not internal tissue parameters.
5. **Evidence:** authentic Blender renders + measured voxel/cut performance + watertightness separate from aesthetic evaluation.

**Not claimed:** possession of paid strawberry asset, exact shader graphs, exact UI internal mapping, literal reproduction of author implementation, or scientific histology.
