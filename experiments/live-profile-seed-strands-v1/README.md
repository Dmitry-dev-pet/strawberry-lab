# Live profile controls and seed-linked Exact

Both requested controls now work in one open Blender scene: Apply Profile recomputes the existing fruit from canonical buffers, and Exact uses the existing artist28+264 graph for Vascular relief. No new anatomy or replacement fruit was created.

[Private scenes and renders](https://drive.google.com/drive/folders/1TLoe9-9Pusr9SWRKRHHWXBFO6MQPENeX). [State A scene](https://drive.google.com/file/d/19Yj1Tbv2GNZ1EwzsynIv37oyxJxepc0r/view) and [state B scene](https://drive.google.com/file/d/1ymom_COuEpqil5qCzhTXah9Mfo4h38Sv/view) share the same embedded runtime and support changing either way.

## Use in Blender

1. Open either scene with scripts disabled. Native Fast and four View Layers work.
2. Run embedded `TISSUE_ZONES__RUN.py` once.
3. Open N → Strawberry Cut → Live nonlinear profile.
4. Edit Shoulder a, Waist b and Height h. Press **Apply Profile**.
5. Choose Exact in the existing Strawberry Cut panel. Move the shared knife or adjust Cortex/Pith/Vascular.

Tested states are A=(.23,-.12,1.08) and B=(-.12,.18,.96). The numeric controls permit bounded artistic interpolation; arbitrary combinations have not received the full contact/cut validation run. Applying uses the stored canonical geometry, so manual vertex edits are replaced. Keep source topology and canonical attributes intact.

## Implementation

`build.py` authenticates PR38 shouldered input using its committed readback receipt. It names the actual inverse shader coefficient nodes, switches Exact's CURVES input to the existing292-spline artist graph, and appends `profile_runtime.py` to the self-contained embedded runtime. Source PR38 scenes, main and GUI Blender stay unchanged.

Apply Profile disables the transient Exact cache, maps mesh vertices from `nonlinear_source_rest`, maps curve points from `nonlinear_source_points`, and maps seed anchors from `nonlinear_original_anchor`. It updates the artist graph manifest's physical coordinates, actual shader a/b/h constants and the scene's `Nonlinear parameters` JSON. It then clears the rest/strand/cache keys and refreshes Exact if it was active. All changes occur in memory; applying requires no disk save or external Python module.

The nonlinear map and inverse remain those verified in PR37/38. CPU sampling uses inverse-F(physical). The cap attribute stores undisplaced physical positions and the shader applies inverse-F once. Existing FruitContext provenance remains in the scene; no second platform/context type was introduced.

Exact's default strand-distance field now uses only `ARTIST | 28 trunks + 264 seed-linked terminals`, count292. The old28+539 diagnostics and539 markers remain distinct, keep their canonical source buffers and follow the same live profile mapping. They no longer drive the Vascular field. The new graph is an artistic routing model, not validated botanical anatomy.

## Verification

`qa.py` runs A→B→A through the registered UI operator in ONE Blender process without disk rebuilds. At each state it checks264 actual seed/hull mesh intersections,264 terminal-to-actual-seed-vertex errors below1e-4mm, unchanged canonical rest buffers, four layers and center/oblique Fast+Exact closed connected positive-volume cuts. Skin/seam/pit data match Fast. Three cap samples per pose compare the actual shader and CPU inverse against the independent reference inverse within1e-6model units, including atlas lookup agreement.

The same pose is evaluated with Vascular0 and0.12mm. The resulting physical displacement changes by more than0.01mm. Changed vertices are checked within1mm of the NEW graph's rest-space distance field. Thus the result is not just a changed UI number. Both complete Drive-downloaded scenes repeat the same A/B/A tests after reopening with scripts disabled.

`cross_frame.py` extends the existing stale-cap regression with an Apply Profile A→B operation. Candidate applies while Exact is active in WHOLE; control applies before building Exact. MATCHED and FLESH ONLY candidate/control renders must match decoded RGB pixels exactly. The old validator is not modified. Embedded script execution twice must remove the first handler and register the replacement without duplicate panel classes.

The first QA attempt incorrectly included transient derived Exact-cache attributes in its canonical-rest digest. The new QA now explicitly excludes tagged transient objects, matching the original-object comparison scope. No geometry gate was weakened. Existing120 Python tests were rerun; the new tests above are Blender integration checks.

`render_all.py` produces six genuine750px/12sample Cycles PNGs in the SAME open scene process: A/B whole and Exact cut, plus B oblique Vascular0/0.12 clay. Cortex/Pith are zero only for that isolated vascular diagnostic, and curves are hidden to avoid material-override clipping artifacts. Camera/light are fixed. State B is optionally saved for delivery; that save is not part of Apply Profile's operation.

Visual inspection shows distinct in-memory profiles and actual radial vascular relief in neutral clay. The relief remains visibly regular, as expected from the existing artist graph. Waxy skin/pale pit rims and reference-space radius/normal approximations remain inherited limitations. This does not establish biological histology or regenerate seed distribution.

## Reproduce

```sh
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/live-profile-seed-strands-v1/build.py
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/live-profile-seed-strands-v1/qa.py -- build/live-profile-v1/live-profile.blend build/live-profile-v1/qa.json
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/live-profile-seed-strands-v1/render_all.py
python experiments/live-profile-seed-strands-v1/cross_all.py
python experiments/live-profile-seed-strands-v1/gallery.py
```

Builder expects the owned PR38 input at the sibling path in its code and refuses existing outputs. ZIP includes that input. `evidence.json` and `readback.json` hold actual results, source/image hashes and full-download verification. Old assets are not overwritten. CPU updates are explicit Apply operations, not promised frame-rate animation.
