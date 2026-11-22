# Nonlinear Exact restored

The two physical nonlinear PR37 profiles now support opt-in geometric Exact cuts. Their native Fast appearance and source geometry remain unchanged. The adapter changes CPU coordinate sampling, not morphology, vessels, pit geometry or the Boolean triangulator.

[Owner-private scenes and renders](https://drive.google.com/drive/folders/1Q1UnAAtpxo2a9GBVtb2dfc9excUMHJ5T). [Shouldered scene](https://drive.google.com/file/d/11caA1A4CooQmEVfcHieZ57j3m6vYyeK8/view) and [waisted scene](https://drive.google.com/file/d/1Dwoy58HMux2SSNQfNl8eTZjhKMMaw9PZ/view) open in native Fast with scripts disabled.

## Run Exact

1. Open either scene.
2. Run embedded `TISSUE_ZONES__RUN.py` in Blender's Text Editor.
3. Choose N → Strawberry Cut → Exact.
4. Move or rotate the existing shared knife. Use the three existing Cortex/Pith/Vascular controls.

All four native View Layers remain available. Saving or a reconstruction error restores Fast. No external Python module is required after opening the scene. Source PR37 build receipts retain their historical Fast-only status; `Nonlinear Exact status` records this adapter's availability. Shape parameters still require rebuilding, as in PR37.

## Coordinate contract

`build.py` derives the embedded runtime from the existing tissue-zones runtime. Each substitution requires exactly one source anchor. The embedded helper uses the same PR37 a,b,h and inverse radial field.

- Cap refinement and displacement occur in the physical Boolean plane/frame.
- `strawberry_exact_rest` retains the **undisplaced physical source position**, despite its inherited name.
- CPU tissue noise, cortex/pith classification and atlas lookup receive inverse-F(physical).
- The Exact material substitutes that physical attribute for the original Object coordinate. The existing PR37 inverse shader then applies inverse-F **once**.
- Old 28+539 physical curve points receive inverse-F before constructing the CPU strand-distance field. Their counts and material/display behavior remain unchanged.
- The deformation tuple is included in the strand/cache key. Native knife matrices and control values still invalidate the cache.

The separate artist 28+264 graph remains display geometry. It is not silently substituted for the original diagnostic strand field. Both networks, 539 markers, 264 physical achenes, hull/pits/crown and packed atlas are preserved from PR37.

## Validation

`qa.py` compares every source mesh/curve geometry digest and original material snapshot against PR37. It checks scripts-disabled Fast, repeated embedded activation, source skin/seam/pit equality, three physical cuts per profile (center, longitudinal, oblique), manifold connected positive-volume meshes, and real cap displacement. It tests the actual queued callback after knife translation and rotation.

For each pose, three samples compare analytic inverse-F, CPU atlas coordinates and the actual derived shader subgraph. Seven additional cap samples compare measured displacement with the tissue components and seam fade predicted independently from inverse-F. Tolerance is1e-5mm for displacement and1e-6model units for rest position. All-zero controls produce a flat cap. An injected reconstruction failure restores Fast. Saving from Exact and reopening with scripts disabled also restores native Fast.

`check_layers.py` runs the existing stale-cap regression on both scenes. MATCHED and FLESH ONLY candidate renders from an edited WHOLE state must match refreshed controls pixel-for-pixel. Existing120 Python tests were rerun. New Blender checks are integration tests, not additional Python unit-test counts.

Six final Cycles comparison frames use750×750,12CPU samples, denoise and the same camera/light/knife within each pair: Fast/Exact beauty for each profile, plus oblique uniform-clay Fast/Exact. Clay contains no bump and hides all curves, because a material override otherwise removes diagnostic shader clipping. Earlier graph-visible clay diagnostics remain in the private archive; the montage uses isolated clay frames. Visual inspection confirms geometric cap relief and aligned pith/cortex. Skin/pit defects and the regular artist graph appearance remain unchanged.

`evidence.json` records downloaded-scene validation, actual source/image hashes and cross-layer results. `readback.json` authenticates complete Drive downloads. The source geometry and material equality checks preserve PR37's validated264seed contacts and264graph endpoints; they are not presented as a fresh independent biological validation.

## Reproduce

The builder authenticates the owned PR37 scenes at the sibling worktree path in `build.py` and refuses existing output scenes.

```sh
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/nonlinear-exact-v1/build.py
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/nonlinear-exact-v1/qa.py -- build/nonlinear-exact-v1/shouldered.blend build/nonlinear-exact-v1/shouldered-qa.json
python experiments/nonlinear-exact-v1/render_all.py
python experiments/nonlinear-exact-v1/check_layers.py
```

QA produces an additional saved/reopened Fast scene beside its JSON. Main, prior scenes and GUI Blender are untouched. Relief and curve radii remain artist-controlled; this does not establish biological histology or a fully regenerated anatomical model. Viewport refresh is CPU work rather than a guaranteed real-time interaction. Source shape records are immutable build metadata, not live deformation sliders.
