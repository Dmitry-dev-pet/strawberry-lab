# Actual nonlinear profiles — FAST ONLY partial integration

Two editable Blender scenes now contain genuinely non-affine physical hulls, seed meshes, baked pits, crown, original diagnostic paths and the existing artist 264-terminal graph. Native moving Boolean cuts use an analytic inverse shader to sample the original owned 150³ atlas in reference space. **Exact geometric cap relief is explicitly disabled.** This is a bounded Fast-only result, not the requested completed nonlinear Exact generator.

[Owner-private artifacts](https://drive.google.com/drive/folders/1mSinN57YDNCcLZGACZ9ykMbWspn9dNNT). Baseline PR36 source SHA256 is pinned in `build.py`; neither that scene nor main nor GUI Blender was modified.

## Method

The existing PR35 FruitContext remains provenance in each scene. One `Nonlinear parameters` scene record identifies the actual profile, parameters, authenticated source and FAST_ONLY status. `profile_probe.PROFILES` is now used to derive actual meshes rather than only numerical plots:

`F(x,y,z)=(s(z)x,s(z)y,hz)`, with `s(z)=1+a exp(-((z-.5)/.36)^2)+b exp(-((z+.3)/.4)^2)`.

Shouldered uses (.23,-.12,1.08), waisted (-.12,.18,.96). Inverse is z=Z/h, x=X/s(z), y=Y/s(z). Positive s and h make this mapping invertible. Native shader Math/Separate/Combine nodes implement that same inverse between the existing rest Object-coordinate output and its existing consumers, including the flesh atlas. Cap points come from a physical Boolean plane in the deformed object's frame; the knife is not virtually warped.

Physical source vertices/curve points are transformed through F, then object matrices reset. Each mesh is copied before deformation to avoid shared seed-mesh writes. The first candidate failed Achene001 contact; it was rejected, retained under build/nonlinear-cut-v1, and corrected by copying mesh datablocks. Final assets are build/nonlinear-final. Original canonical positions are retained in the `nonlinear_source_rest` point attribute and `nonlinear_source_points` curve property; source files remain immutable. Curve counts, point radii and stable seed IDs are retained. Radii are **not** Jacobian-deformed; tubes are an artist approximation. Saved normal metadata remains reference-space metadata; actual shading normals derive from the deformed mesh. No anatomical or pit-footprint regeneration is claimed.

The existing new artist graph's terminals follow the same vertex map and are checked against actual deformed seed vertices. Original 28+539 diagnostic paths/539 markers remain distinct from this new graph. No 539→264 mapping was invented. Deformation changes their physical coordinates; immutable canonical source buffers and digest metadata are retained instead of asserting unchanged physical coordinates.

## Verification

`qa.py` reopens scenes, verifies F on actual hull vertices, residual against best-fit affine >0.01 model units, inverse error <1e-6,264 actual seed/hull mesh intersections,264 terminal endpoints within1e-4mm of real seed vertices, four native layers, two translated/rotated physical Fast cuts with connected/manifold/positive-volume hulls. Existing120 Python tests were rerun. These Blender validations are additional integration checks, not a new unit-test count.

`check_field.py` evaluates the ACTUAL saved shader inverse subgraphs at four rest/physical probes per material and checks every deformed curve point against its canonical source. This is not an independent Cycles RGB emission calibration. Six real Cycles renders use750px,12CPU samples, denoise, fixed camera/lights/seed: whole, longitudinal and oblique per profile. Source/PNG hashes are in receipts. Downloaded scenes undergo the same reopen QA.

## Exact blocker and remaining limits

The previous Exact runtime derives `body_to_rest` and strand coordinates through matrices and stores that field on newly refined cap vertices. A z-dependent inverse is not representable by those matrices. Keeping that runtime active would sample and displace the wrong rest positions. Its embedded Exact/Tissue activation texts now raise a clear RuntimeError; native Fast stays available without scripts. No nonlinear Exact mesh, relief quality, Exact callback/cache correctness or new Exact cross-layer validation is claimed.

The shader inverse is working for Fast's newly generated cap positions. Next implementation must make Exact's generated cap/rest sampling and strand field consume the same inverse function, with deformation parameters in its cache key; then independently validate plane seams and relief. This adapter is not implemented here. Current geometry is baked editable output; changing profile parameters requires rebuilding from the immutable source, not editing a scene slider. Known skin/pit visual defects are unchanged. Scientific measurements are not inferred from these artistic profiles.

## Reproduce

```sh
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/nonlinear-cut-v1/build.py
python experiments/nonlinear-cut-v1/run.py
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/nonlinear-cut-v1/check_field.py -- build/nonlinear-final/shouldered.blend build/nonlinear-final/shouldered-field.json
```

Builder expects the owned PR36 round source at the sibling worktree path documented in its code and refuses existing output scenes. ZIP contains the required owned input. See evidence.json/readback.json for actual hashes and measured results.
