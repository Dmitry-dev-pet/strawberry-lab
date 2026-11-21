# Live exterior on the PR29 strawberry

This experiment uses the single saved PR29 receptacle as the body for the PR13 exterior. The PR13 linked achene meshes, materials, sepals and pedicel are editable. One Empty controls the original body Boolean and the exterior Booleans. The original packed PR29 RGB atlas still supplies the body cap.

## Edit the saved scene

Open `strawberry-integration.blend` in Blender 5.2. The scene opens on the cut pose. Select **LIVE CUT | move or rotate this Empty** in **One shared knife**. Translate or rotate the Empty. The local positive Y half-space stays. Example transforms use the Empty’s Location Y and Rotation fields.

| Pose | Location Y | Rotation XYZ |
| --- | ---: | --- |
| Whole | −35.56 mm (−1.6 model units) | 0°, 0°, 0° |
| Cut render | −2.22 mm (−0.10 model units) | 0°, 0°, −23° |

Enable **Diagnostics | original paths and 539 markers** with its View Layer collection checkbox to see the original 28 core splines, 539 branch splines and 539 diagnostic markers. Material Preview and Cycles evaluate the knife opacity mask for these paths and markers. **539 diagnostic anchors != 264 exterior achenes. They are not biologically matched.** The instructions and warning are also in the embedded **START HERE | Live exterior.txt**.

## Geometry and shading

- The original 30,242-vertex hull, cutter, splines and diagnostic marker mesh retain native PR29 coordinates. The editable fruit and knife share an identity rest-space parent. The cap shader reads position through that parent, preserving the original two-slice interpolation and packed 150³ RGB image. The guide and original diagnostic clipping require no add-on.
- The millimetre adapter takes the 48 mm nominal height from the Camarosa `FruitContext` (R0015) and maps it to the 2.16-unit PR29 hull with a uniform factor of 22.2222 mm per model unit. The Blender scene unit display uses that conversion. The resulting native width is about 40.76 × 39.90 mm. The width, silhouette, achene count and crown are artist choices.
- The achene emitter places its phyllotaxis on the canonical hull through radial BVH intersection at each meridian and azimuth. The achene axes follow the local tangent and normal. The same surface adapter feeds the calyx and pedicel emitter. The skin uses PR13’s ripening, cuticle and pit-tint logic, with shallow bump relief from an interpolated pit mask. The skin pits are shading relief on the unchanged hull.
- The shared knife’s solid subtraction volume drives a Manifold Boolean on the body and Exact Booleans on the exterior. The Manifold solver closes the center cut where Exact left a seam on nearly coplanar hull edges. Sepal Booleans enable self-intersection handling for the folded, solidified tips. The diagnostic layers use opacity clipping, which displays the original paths without generating caps.
- The tissue volume and exterior arrangement are artist studies. This experiment adds no histological calibration or new tissue geometry. The finite cutter block covers the tested poses. Very distant or tangent poses and interactive viewport latency are outside the verification.

## Reproduce the build and checks

Run from the repository root with Blender 5.2.2. The immutable input is the verified owner-provided PR29 file, 48,048,054 bytes with SHA-256 `56b6d516e8794fb855512978e90e37cd754374a594fb4c5103e672c960a031cf`. The build and validator reject a different input digest. Use a fresh output directory on each build.

```bash
BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
EXPERIMENT=experiments/integration-live-exterior-v1
SOURCE=build/inputs/live-source.blend
OUT=build/integration-v1/reproduction

export PYTHONDONTWRITEBYTECODE=1
"$BLENDER" -b --factory-startup -t 4 --python-exit-code 1 \
  --python "$EXPERIMENT/build_integration.py" -- --source "$SOURCE" --out "$OUT"
"$BLENDER" -b --factory-startup -t 4 --python-exit-code 1 \
  --python "$EXPERIMENT/validate_integration.py" -- \
  --source "$SOURCE" --scene "$OUT/strawberry-integration.blend" --out "$OUT/validation.json"
for POSE in whole cut; do
  "$BLENDER" -b --factory-startup "$OUT/strawberry-integration.blend" -t 4 --python-exit-code 1 \
    --python "$EXPERIMENT/render_integration.py" -- --pose "$POSE" --out "$OUT/$POSE.png"
done
```

The validator opens both files independently. It compares the original hull, cutter, packed atlas bytes and diagnostic geometry including spline radii. It checks each of the 264 achenes against the hull, checks the saved scene mesh inventory, and moves the shared Empty through the whole pose and four distinct cutting poses. It measures the closed evaluated body and cap plane alignment, and verifies the exterior solids respond to the same knife. Each PNG has a JSON receipt with the saved scene digest, render settings, time and image digest. Both images use the same camera, lights and render settings.
