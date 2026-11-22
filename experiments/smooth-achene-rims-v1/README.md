# Smooth-rim bounded experiment — visual FAIL

No candidate is promoted. PR34 and its saved scene remain unchanged. This branch records two engineering alternatives and exactly one material calibration. There is no new generator, vascular/cell model or accepted replacement scene.

Baseline: PR34 commit `8dcf8282f448c215f300461cc2e78c77da73b934`, scene SHA `24a3f7a2b9b157aac3b5a8aa30aa1b84d2404be64df67f74705665de3dbf74b4`. `build_rims.py` authenticates that file and compares its immutable anchor/normal/ID/rotation/scale, material, network and runtime contract to the exact owned PR33 pre-pit hull. It applies the same pit depth, footprint and seating rules on that canonical object. PR34 source files are unmodified.

## Bounded alternatives

1. **Padded shoulder, half-edge subdivision:** target0.28mm, support padding1.25, three passes,79,085vertices. Rejected: Exact reports `The triangulator merged distinct seam vertices`. No epsilon/tolerance or fallback gate was changed. A real clay render is retained as negative evidence.
2. **Padded shoulder, thirds subdivision:** same target/padding, one pass with two cuts per selected edge,72,694vertices. Five Fast and five Exact poses, positive volume/connectivity, four layers, callbacks/tissue controls/save/reopen, original source diagnostics/materials,264 mesh intersections and both cross-layer render pixel controls pass. Nevertheless the real macro and uniform clay still show angular shoulders. **Visual FAIL.** No further shape or lookdev iteration was attempted.

The wrapper reuses PR34's builder; its inherited `builder_sha256` in the build receipt identifies that base module, not the wrapper. The complete reproduction recipe is this checked-in wrapper, alternative number and original inputs. No method transfer from Frucht is involved.

## Forensic material calibration

On an independent copy of PR34, `forensic_bump.py` sets only the strength of the Bump whose Height is fed by `achene_pit` from0.25 to0. The original microtexture remains connected. This diagnostic copy is not a proposed fix. All geometry stays at PR34.

The actual1000px Cycles beauty difference has mean absolute RGB difference0.3505/255;1.52% of pixels change by more than8levels in any channel. This is an image-difference statistic, not a physical attribution percentage. The independently rendered uniform clay is pixel-identical to baseline clay, and the angular shoulders persist. Legacy bump can contribute to the appearance but removing it does not solve the geometric defect.

## Geometry measurements and interpretation

All264 seed neighborhoods were sampled. Raw mesh shoulder dihedral P95: PR34 **22.653°**, alt1 **19.547°**, alt2 **20.500°**. Max:43.590°,48.287°,37.091°. Shoulder edge-length P95:0.435/0.264/0.287mm. More edges mechanically reduce neighboring face angles, so these are diagnostic geometric measures, not a realism score. Images override a merely improving metric: neither alternative establishes a sufficiently organic rim.

Depth inputs/analytic profile and footprint are unchanged. Alt2 measured anchor floors0.1581–0.2095mm, median0.1884mm. Smaller interpolation error changes measured floor values and normal seating slightly. Saved anchors/scales/rotations remain fixed. The parent inspected the actual beauty, clay and whole PNGs; the failure is not inferred solely from numbers.

115 baseline tests passed (107 existing plus8 tissue-zone tests). Full alt2 validator and mesh-contact reports are retained. Alt1 has an explicit failed log, not a PASS receipt. The transient forensic material change is intentional and is not labelled immutable-material QA PASS. Denoised12sample images limit extremely fine texture judgments, but the angular shoulders remain visible across multiple seeds.

## Reproduce and artifacts

Use Blender5.2.2 headless,4CPUthreads, and NumPy/Pillow in a separate Python environment for the sheet. The original `render_pits.py` produces actual1000×1000,12sample, seed1729 matched-camera/light beauty, clay and whole images. Existing PNGs and scenes are protected; choose fresh output paths.

```
Blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/smooth-achene-rims-v1/build_rims.py -- 2 build/inputs/pr34-pits.blend build/inputs/pr33-tissue-zones.blend FRESH/smooth-rims.blend
Blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/geometric-achene-pits-v1/validate_pits.py -- build/inputs/pr29-original.blend build/inputs/pr33-tissue-zones.blend FRESH/smooth-rims.blend FRESH/validation.json
Blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/geometric-achene-pits-v1/render_pits.py -- FRESH/smooth-rims.blend clay FRESH/clay.png
```

Private bundle includes source, unchanged authenticated owned inputs, experimental editable scenes, original PNG/receipts, geometric probes and failure logs. No Frucht media. No main merge, previous-scene overwrite or live GUI change. Stop at this negative result; a successful rim fix is not claimed.
