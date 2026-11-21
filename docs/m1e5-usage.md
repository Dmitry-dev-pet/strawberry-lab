# Strawberry Lab M1e5 — Live Exact adaptive CutSurface (Blender 5.2.4)

**Independent implementation based on our own M1e4.** No Frucht code, .blend files or Geometry Nodes trees are included.

## What is new

- Real-time *event-driven* cutter tracking: moving the existing knife in Object Mode, scrubbing a timeline or rotating a cut plane automatically rebuilds **only the currently visible locally refined CutSurface mesh**. No manual regeneration command is required after installation/activation.
- The source volume, hole, material classification, original rest-space fields and existing 135 3D filament splines are retained. Geometry remains watertight on tested poses. Original achenes remain controlled by the live knife.
- **Fast mode** (default on opening): the original M1e3 Geometry Nodes cutter and material/relief update even if the addon is not installed. The static Exact snapshot is hidden to prevent stale data.
- **Exact mode** (opt-in): a Blender event-handler invokes a synchronous Python+BMesh local edge refinement + existing Geometry Nodes surface displacement. It takes around **0.37–0.68 s** per tested CPU update, **not 60 fps**, and is *not purely GN*.

## Open the file and use the knife

1. Open `strawberry-m1e5-live-exact.blend` in Blender 5.2+.
2. To use only native Geometry Nodes, move `M1e | independently moving knife (cube half space)` or scrub frames 1–30. The default **Fast** model responds without any script.
3. To enable auto-updating **Exact**, open Blender's **Scripting** workspace, open Text datablock **`M1e5 - Enable Live Exact.py`**, and click **Run Script** once per Blender session. (Alternatively install the accompanying `m1e5_live_exact.py` as an addon via *Edit → Preferences → Get Extensions → Install from Disk*.) **There is no need to enable automatic script execution globally.**
4. The Viewport sidebar **N → Strawberry → Strawberry Lab — Live Exact** now has **Exact**, **Fast** and **Force Refresh** controls. `Force Refresh` also invalidates the cached spline KD-tree if you edit the cavity/filaments.
5. Drag/rotate the knife or scrub the timeline. Exact updates at the new pose automatically while the script/addon is active. If rebuild fails, the code falls back to the always-live native GN body so a stale snapshot is not displayed.

The embedded Text code is a copy of the standalone addon, saved inside the .blend for provenance. The .blend itself does not silently execute Python scripts when opened. Installing/enabling the addon allows load-time activation for this specifically tagged scene.

## Reproduction

From `source-m1e4-frame15-beauty.blend`:

```bash
blender -b source-m1e4-frame15-beauty.blend \
  --python build_m1e5.py -- \
  --out strawberry-m1e5-live-exact.blend --addon m1e5_live_exact.py

blender -b strawberry-m1e5-live-exact.blend --python validate_live_m1e5.py
blender -b strawberry-m1e5-live-exact.blend --python test_ui_rotation.py
blender -b strawberry-m1e5-live-exact.blend --python render_m1e5.py -- \
  --outdir . --frames 15 --samples 16 --resolution 720
```

The QA command automatically switches to Exact, checks 4 timeline poses, manual knife movement at fixed frame, restores the pose, tests zero open edges, checks no duplicate idle rebuild, and exercises Fast fallback. UI test checks double Run Script safety, an 18° rotated cut and addon handling after reloading the saved .blend.

## Limitations

- A **Python/BMesh hybrid**, **not** a pure Geometry Nodes adaptive topology generator. The registered handler runs synchronously and can pause dragging while computing; no 60fps performance claim.
- Changes to the source shape, cavity or fiber paths without moving the knife require **Force Refresh**. The rest of the scene is unchanged.
- Polygon edges are manifold on tested poses, which does not rule out every geometric self-intersection.
- Diagnostic 3D tubes are still clipped at sampled spline points, not exact intersections with tissue.
- The appearance remains stylized. This stage intentionally delivers functional live Exact editing **without changing the original material/render output**.
- Running sequential high-quality Cycles renders within one Blender process timed out on a subsequent frame in this environment; independent single-frame Blender processes completed and generated genuine frames. This is not a validated production animation pipeline.

## Provenance

Blender scenes and authentic Cycles PNGs are stored in the owner-private Google Drive folder; independently authored source, tests, technical notes and a SHA256 manifest are proposed via a stacked GitHub PR. No commercial Frucht assets, GPL source graphs or biological calibration are included. Prior milestone M1e4 remains unchanged.
