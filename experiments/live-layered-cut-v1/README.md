# Strawberry Lab — Live Layered Cut v1

**Status:** independently authored functional Blender 5.2.4 LTS prototype, not a commercial Frucht reconstruction. Based on our Layered Cut v0, our Volume First v0 `150³` RGB tissue field, and the unchanged 28 core carriers + 539 3D achene-connected branch splines from our V3/V4 source.

## What now works

A **single movable Empty** named **`LIVE CUT | move or rotate this Empty`** drives **both**:

1. A **real evaluated Boolean** on a newly reconstructed, closed full-berry mesh. The Boolean produces an actual fresh-cut cap, whose material continuously samples the *same original Volume First v0 150³ RGB source field* through a packed atlas. The source full berry is reconstructed from our original v0 analytic shape function; it is not the earlier saved half-mesh.
2. Per-layer **world-space clip masks** (referencing the same Empty) on copies of our ORIGINAL V3/V4 tubes and diagnostic V2 orange achene markers. `Off / Clipped / Full` is independent for core, branches, and markers. **No source spline coordinates, radii, endpoints or seed marker positions change.**

Blender contains **two comparison scenes sharing the same one controller**:

- `LIVE MATCHED | shared movable plane` — cut tissue and clip core/branches/markers by that same plane.
- `LIVE FLESH ONLY | shared movable plane` — same cut tissue; show all 28 carriers, all 539 branches, and all 539 markers uncut.

The shared Empty's **local positive Y halfspace remains**. The cutter is a finite, oversize halfspace cube parented to the Empty; it subtracts the local negative-Y side. Blender Boolean is evaluated automatically when the Empty moves or rotates. The mask materials use the same Empty as an object-space reference, and respond automatically too. This is not a series of pre-rendered static cut angles.

## How to use in Blender

1. Open **`strawberry-live-layered-cut-v1.blend`** in Blender 5.2.4 or newer. The image data are packed; no external texture dependency for viewing.
2. Switch to the `LIVE FLESH ONLY` scene in the Scene selector. The camera and lighting are the same in `LIVE MATCHED`.
3. Find the Empty **`LIVE CUT | move or rotate this Empty`** in the Outliner and **move it along Y**, e.g. `0.34` or `-0.26`; or rotate it about Z, e.g. `32°`. The flesh's cut geometry and any clip-enabled layers move together. The cutter cube itself is hidden from final renders.
4. For a practical panel, switch to Blender **Scripting**, select the embedded Text block **`LIVE_CUT_CONTROLS__RUN.py`**, then click **Run Script** once. In 3D View press **N → Strawberry Live**. You can edit **Plane Y offset** and **Plane rotation Z**, set **Flesh = Off / Cut / Whole**, and set core, branches and seed markers independently to **Off / Clipped / Full**. The optional ghost outline is a separate toggle. The UI is a real Python properties panel, not a picture.
5. Optionally use native Blender View Layer collection checkboxes without running the script. The scene also contains the original v0 cut evidence and V4 source data, which were not modified.

For reasonable Cycles rendering, saved scenes have `transparent_max_bounces=192` because otherwise many shader-hidden tube intersections can cause black marks on the fresh cut. This is a display workaround, not a biological feature.

## Proof / reproduction

`build_live_cut.py` starts from our own `input-layered-v0.blend`. It reads the exact original source `tissue_3d.npz` and the atlas written by `make_atlas.py`.

```bash
python make_atlas.py
blender -b input-layered-v0.blend -t 4 --python build_live_cut.py
blender -b strawberry-live-layered-cut-v1.blend -t 4 --python validate_live_cut.py
blender -b strawberry-live-layered-cut-v1.blend -t 4 --python test_ui.py
blender -b strawberry-live-layered-cut-v1.blend -t 4 --python render_live_cut.py -- --mode flesh-only --pose oblique --resolution 520 --samples 12 --out outputs/oblique-flesh-only.png
python make_comparisons.py
```

`validate_live_cut.py` checks source curve SHA256 invariance, identical A/B cameras, exact branch and seed marker arrays in every full/clipped layer, two packed z-slice image sampler nodes and real Boolean *cap face* material. Tests at **Y=0**, **Y=+0.34**, **Y=-0.26**, **angle Z=32°** all PASS. The newly cut cap vertices lie on the current plane within **2.55e-8 model units** in the most oblique pose. There are 30,242 vertices in the complete source body (before cutting). `test_ui.py` asserts live property callbacks and independent scene layer flags.

`outputs/real-live-cut-four-poses.jpg` and `outputs/real-live-layer-modes.jpg` are contact sheets composed only from authentic Blender Cycles renders. No generative imagery was used.

## Limits and honest interpretation

- The whole red skin is regenerated from **our v0 analytic hull** because v0/v1 only saved a physical **half** berry; moving a cutter through a half-mesh would be invalid.
- The cut RGB material does **sample our actual stored 3D field**, but the **physical relief of microscopic cells is NOT regenerated** on every cut. The source field was artist-defined, not botanical histology.
- The 539 orange endpoints remain our **diagnostic octahedra**, not real achene meshes. Real pith, juice, cell geometry and leaf/stem layers are not added as independent geometry.
- The clipping of tubes and markers is a **shader opacity mask**, rather than an exact geometrical Boolean cap on every tube. It is correct for comparing visibility and source coordinates; it is not final exportable watertight clipped geometry.
- A single shared plane is actually movable in Blender; **render speed and viewport FPS on the user's own machine are unmeasured**.
- No commercial Frucht `.blend` is available; neither this experiment nor its independent controls prove how Frucht wires its on-video sliders.

All third-party Frucht source, original video, and paid graphics remain private. Only our own code, reports and QA results may be put in GitHub; `.blend`, field data, atlas PNG and Cycles renders stay in owner-private Drive.
