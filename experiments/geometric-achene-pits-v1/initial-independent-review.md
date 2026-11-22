# Independent review of geometric achene pits v1

Reviewed the saved scene with SHA-256 `fdbb62617682c43d7399bcf4f7d7fabf61458cfee51d1cee35f78a8d4281a6c4` in headless Blender 5.2.2 LTS with auto-execution disabled and four threads. The geometry and knife pass the requested functional checks. Three evidence checks need small changes before publishing their claims.

## Findings

| Severity | Reproduction | Minimal correction |
| --- | --- | --- |
| P2, interpolation bound | In the reviewed validator, lines 165–171 measure the maximum distance to a sphere with the longest pit radius. The stated 0.373145 mm understates distance past the ellipsoidal field. A point inside a moved triangle at Achene 103 lies 0.418557 mm outside the union of all 264 ellipsoids. The residual displacement there is only 6.24 × 10⁻⁹ mm. A conservative bound across all 41,720 affected triangles is 0.420095 mm. | Bound each triangle by the largest of its three base-corner distances to one support ellipsoid. Convexity covers the interior. Record it as an upper bound and refresh the receipt. The existing 0.72 mm budget passes. |
| P3, plate captions | Swapping the whole and macro PNGs **together with their receipts** on both sides produces a PASS sheet with the two captions reversed. The supplied originals have the correct captions. | Assert each receipt’s frame equals the requested frame and its resolution, layer and sampling settings equal the advertised values. |
| P3, material comparison | Changing a skin Color Ramp stop to green in memory leaves the validator’s immutable snapshot equal. Eight independently inspected saved ramps match PR33. | Include ramp element positions, colors and interpolation in the material signature. Include the attribute name and image identity of shader nodes that read those data. |

The three reproductions are in [probe.json](probe.json), [swap_frames.log](swap_frames.log) and [materials.json](materials.json).

## Saved geometry and contact

- The original PR29 and authenticated PR33 hulls share the same mesh digest. The candidate preserves all 30,242 original samples in its 45,123-point reference mesh. Every child triangle fits an oriented source triangle. The maximum per-source-triangle coverage error was 5.62 × 10⁻⁷ mm². All 28,231 out-of-field base vertices retain their coordinates exactly. At storage precision 16,787 vertices actually moved.
- Independent source-to-candidate rays through the 264 saved anchors gave floor depths of 0.18729–0.29948 mm, median 0.25216 mm. Every source anchor was within 0.00390 mm of the original skin. The smallest dot product between a saved normal and the nearest source face normal was 0.99948.
- Both body and seeds share the PR29 rest-space parent. Transforming each seed’s original triangles by the inverse body world matrix times the seed world matrix gave 75–142 intersecting seed/body triangle pairs for **every** seed. Maximum tangential center drift from the source was 0.00000293 mm. Embedded and exposed distances spanned 0.119–0.188 and 0.255–0.396 mm respectively.
- Name/ID, saved anchor and normal, rotation, scale and original seed mesh digest matched for all 264 objects. The single hull, calyx and pedicel meshes, 28 + 539 curve splines with radii, 539 endpoint markers, and packed 150-slice atlas passed the reopened source comparison. The validator allows the intended raw-body change and seed translations. Four in-memory challenges rejected a sideways seed move, normal-only seed move, out-of-support vertex deformation and altered saved anchor.
- Independently placed label, source, code and output checks matched all 5 input, 17 code and 26 artifact SHA-256 entries present at the time of review. Per-plate checks are in [plate-hashes.json](plate-hashes.json).

## Saved knife and view layers

A fresh [validator run](validation.json) completed in 88.65 seconds. The native Fast path opened with scripts disabled. Four layers used the existing cutter. The five cut poses yielded connected, watertight positive-volume body meshes in both modes. Fast volumes were 1.695209, 1.467008, 2.106083, 1.407146 and 1.702212 BU³. Exact gave 1.701502, 1.473241, 2.112543, 1.413411 and 1.708386 BU³. Native clipping checks also passed for the retained exterior solids.

The opt-in runtime passed translated and rotated knife updates, double registration, tissue controls, unload, injected failure fallback and save/reopen into Fast with the edited tissue control intact. Four fresh cross-layer renders reproduced the candidate/control pixel equality for MATCHED and FLESH ONLY, including agreement with the supplied rasters. See [decoded SHA-256](cross-raster-sha256.json).

## Appearance

Inspected all six 1,000 px, 12-sample original plates, their source hashes, paired cameras, lights, material treatment and frame settings. The whole fruit reads as having recessed seeds. The macro plates show a visible floor and steep sides around several achenes. The lower-center and lower-right recesses have angular shoulders in both the red and clay views. This matches the documented macro-scale limitation.

A fresh [full-size clay render](reproduced-clay.png) agreed with the original in every decoded RGBA channel of all 1,000,000 pixels. PNG container bytes differed. A separate [500 px clay control](geometric-only-500.png) removed the body’s stored custom normals in memory while preserving the same studio and geometry. Recesses and wall shading persist with ordinary mesh normals. The [native-resolution crops](native-crops.png) show the visible rim facets. The known baked-pit behavior on independent seed edits is documented.
