# v16 — independent Blender-restored v12 cap-only vascular field diagnostic (2026-11-22)

**Status: measured diagnostic PASS; no new generator/render version, no photoreal quality acceptance.** This addresses the next research question left by [v15 field-to-Voronoi A/B](v15-field-to-voronoi-coupling-audit.md): precisely how strong and continuous is the original 192³ rest-space vascular field on **actual evaluated cut surfaces**, not across the entire strawberry body?

## Environment and provenance

- Recovered owner-stored **official Blender 5.2.4 LTS Linux x86-64** from the **17 parts** in private Drive folder [Blender-5.2.4-linux-x64](https://drive.google.com/drive/folders/1LuHr6wXiNMy-3BQ_lVTzIKsqM2T3T7Io). Ran the provided offline restoration procedure `restore_blender_drive.py`; all 17 part SHA-256 digests matched the storage manifest, total archive **385,047,680 bytes**, verified whole-archive SHA-256 `2fd14c50987426897ba60237ee996edf2b4151f4b1a72a460ca20be58c1d2d86`. Executed actual `blender -b --factory-startup` successfully.
- Recovered exact owner-private **v12** editable Blender file from [Drive v11/v12 research](https://drive.google.com/file/d/1J1Zi93Ewbt0AkbYc8-e17dgydjPL7Mrw/view). Input SHA-256 `300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410cbb405b7`, matching previous validated Mac source.
- Opened the file read-only with `--disable-autoexec` and `bpy.ops.wm.open_mainfile(...,use_scripts=False)`. Evaluated saved native SDF Geometry Nodes output at **frame 20 planar** and **frame 40 bite** via `evaluated_get(depsgraph).to_mesh()`. No scene/asset was modified.
- Blender 5.2.4 is not the original Mac renderer's 5.2.2. This is independent geometric field analysis, **not a new Cycles visual-quality A/B**.

## Cap face selection (important correction to the v15 whole-body percentages)

The evaluated material slots are `0:None`, `1:Skin • strawberry red`, `2:SDF v12 | continuous vascular fibers, restrained wetness (ARTIST)`. Selection uses **material_index=2** (actual flesh cap quads) and excludes skin=1. Each cap's evaluated vertex attribute `v8_vascular_intensity` and `fruit_rest` is sampled in the exact saved scene. Quad areas are computed as a sum of two triangle areas; area-coverage thresholds use the **average of four endpoint R samples**, a documented numerical approximation.

| Exact cut measure | Planar, frame 20 | Scalloped bite, frame 40 |
| --- | ---: | ---: |
| Cap-only quads | **75,128** | **61,704** |
| Unique cap vertices | **75,747** | **62,165** |
| Cap area (scene mm²) | 1,092.651 | 748.661 |
| Median cap R | 0.01031 | 0.00322 |
| Mean cap R | 0.04632 | 0.03677 |
| Cap vertices R ≥ 0.10 | **18.61%** | **14.57%** |
| Cap vertices R ≥ 0.30 | **1.90%** | **1.18%** |
| **Cap quad area where mean R ≥ 0.30** | **1.84%** | **1.22%** |
| Cap area where mean R ≥ 0.50 | **0.213%** | **0.272%** |

Older v15 numbers (1,582 / 194,354 and 1,994 / 350,314) counted strong-source vertices over the **whole evaluated body**, including skin, so are not the correct *cap-area* statistics. This audit supersedes those denominator choices; it does not invalidate the v15 A/B mechanics.

## Spatial connectedness — source 3D field versus its slice

The saved 192³ packed `SDF proof v4 | 192^3 sparse volume and continuous branches` atlas is read back from the Blender image datablock (`Non-Color`), then Z tiles are unpacked in order from its 16×12 layout. Source rest-space bounds X,Y ±18 mm, Z −1…50 mm; voxel pitch **0.1885 mm in X/Y and 0.2670 mm in Z**.

- In the full **3D** atlas at **R≥0.30**, high-strength voxels are **0.871%** of volume and form **2 components** under 26-neighbor voxel connectivity; the largest has **98.94%** of all high-strength voxels. *The field is therefore largely connected in volume* at that threshold.
- On **evaluated planar cap mesh**, at R≥0.30, high-strength vertices form **34 quad-edge-connected patches**; largest only **68 vertices**, with a bounding-box diagonal **≈0.961 mm** (this is **not** strand path length). At R≥0.10 there are 55 patches, with the largest spanning a 16.95 mm bounding-box diagonal.
- On **evaluated bite cap mesh**, at R≥0.30, **13 patches**; largest **218 vertices**, bbox diagonal **≈3.884 mm**. At R≥0.10 there are 48 patches; the largest bbox diagonal 25.48 mm.

**Interpretation:** high-intensity fibers mostly connect *inside* the 3D field but only intersect the current exposed caps in isolated local bright spots. Much longer low-intensity halos/strands exist at R~0.1; high-R contrast is concentrated into small islands. This is a strong mechanistic explanation for previously observed bright dots/fuzzy stripes when coupling 3D R to cut-cell displacement, not evidence of measured plant anatomy.

## Field-width resolution test (not botanical vessel diameters)

A 3D Euclidean distance transform on R≥0.30 at the measured voxel spacing returns a **median 2× local-core distance estimate of ≈0.654 mm**, and 90th percentile ≈0.755 mm. These are *threshold-dependent voxelized field widths*, not a physical measured xylem/phloem bundle diameter. The sampling pitch makes subvoxel strand detail unreliable; improving appearance by changing 3D field threshold/antialiasing may be more important than increasing all Voronoi cell amplitudes.

## Diagnostic image and reproducible evidence

Two data visualizations (kept **private with owner in the chat**, not committed publicly) show the actual evaluated cap vertex R field projected into source X–Z coordinates, with cyan marks at R>0.3. They are **not Cycles renders** and are not images copied from Frucht. All newly created read-only scripts and raw metrics/quad-cap NPZ files were packed in a 13-member verified local diagnostic archive `strawberry_v12_field_diagnostics.zip` (6,183,546 bytes, SHA-256 `6e308b42a7355309a8de09b543bbb97671a9b8a73c23a4fe7c0df68b8922658e`); no new material, model or production assets were uploaded or merged.

To reproduce, use the verified Blender Linux runtime and SHA-pinned v12 `.blend`; evaluate the two SDF bodies by frame, select `material_index==2` quad faces, use `v8_vascular_intensity` POINT data, calculate face area and quad-edge adjacency; unpack R from the packed atlas as 16×12 Z tiles, measure 26-connected 3D threshold components. Scripts in the local diagnostic bundle specify complete computation, exact cut poses and numerical tests.

## Decision

No changes to the SDF engine, node tree, materials, seed network or archived v12. **Keep PR #43 research-only, not merged.** The next bounded hypothesis, if approved, should modify **how the 3D source R field is constructed and antialiased** so meaningful continuous medium/high-amplitude strand structure intersects *both* planar and curved cuts, while preserving one rest-space source for visual shading **and** Voronoi displacement. Test **cap-only field coverage, connected patch lengths and matched Cycles closeups** before claiming improvement. Do not return to coarse cell-height tuning, extra detached tube objects, or cosmetic rim repair. All unmeasured vascular data remain ARTIST.
