# Strawberry Lab: direct owner Frucht video audit and two experiments (2026-11-22)

Status: Engineering PASS in tested poses; Frucht visual fidelity FAIL. Draft branch only, main unchanged.

## Verified private video and frame observations

- Owner-private original: https://drive.google.com/file/d/1Aj17g8cIVZ-enECJAHUIXrDektWmVA-b/view
- MP4 downloaded and decoded in this session: 1080 x 1350, 1139 frames at 30 fps (37.97 seconds). SHA-256 cbe17cfd0ffa0e7697462892a28bd339e0b9666418276287499c49ca6bae684e.
- 10.0 s: broad bright central spindle, thin radiating pale fibers, saturated red-orange and glistening exposed flesh.
- 18.2-19.0 s: ragged, locally scalloped/tearing bite, wet segmented tissue. NOT a perfectly smooth spherical interior.
- Comparison is qualitative only: lighting, angle and cutter pose differ. No claim of exact pixel-matched A/B or direct inspection of commercial Frucht source.
- Private comparison images are in the owner's Drive, not in public GitHub.

## v9: enlarged central pith, visually rejected

- [Build source](build_v9.py), [validator](validate_v9.py), [QA](validation-v9.json), [manifest](v9-build.json).
- Built independently from v8. Only Blue/pith channel of existing 192-cubed tissue atlas changed to an elongated 3D spindle, with a warmer pith shader color. R vascular field, G mottling, the original SDF cutter, cut-cell relief and seeds preserved.
- Planar Cycles cut gains a pale central core, more like 10-second author shot. Bite becomes an overlarge blurry white patch: visual FAIL, v9 not accepted.
- Reopened Blender 5.2.2 scene with script autoexecution off passed initial/moved plane & sphere, watertight positive-volume bodies and zero surviving seed vertices inside cutters.

## v10: scalloped bite, engineering PASS; still not photoreal

- [Build source](build_v10_ragged_bite.py), [validator](validate_v10.py), [render](render_v10.py), [QA](validation-v10.json), [manifest](v10-build.json).
- Separate derivative from original v8, not v9. Only sphere cutter source mesh replaced: 162 -> 6050 vertices, nine broad deterministic scallops and fine perturbations, radius variation -9.18% to +9.28% (at scale 12 mm approximately +/-1.1 mm). ARTIST parameters, not a scientifically measured bite.
- Native editable cutter is still shared by body SDF difference and live achene culling; engine and tissue shader untouched.
- Reopened with scripts disabled: five tested states including 2 sphere poses and plane poses, all 0 nonmanifold edges and positive signed volume; all remaining seeds have 0 vertices inside the cutter. Visible seeds for bite initial 226, moved/enlarged 211.
- Genuine Cycles output shows a less circular rim but still one bowl-like cavity without Frucht's exposed fibrous tears. Visual acceptance remains FAIL.

## Private artifact links

- [Owner-private folder with scenes, 3 PNGs and hashes](https://drive.google.com/drive/folders/15JLM2-bMdsNnjOhxKGeD31eUVBPq3sNx).
- [Original video 10 s vs v8/v9 cut — PRIVATE](https://drive.google.com/file/d/1C6bNaLdB_U5Nrv2I_Hes6YqRaXnzaeD6/view).
- [Original video 18.2 s vs v8/v10 bite — PRIVATE](https://drive.google.com/file/d/1UL-w1shHFJ2XjPlXiS-GdQiNc5son0c1/view).
- [Editable v10 Blender file](https://drive.google.com/file/d/1CF4MFbAjUc9bqlKI3tKqamvRysWtC3ZM/view).

## Decision and limitations

Preserve v8 as baseline. v9 is a negative visual control; v10 is a narrow working cutter-shape proof only. Do not merge into main. Next work must match an actual edge-exposing bite pose and inspect texture, torn fiber geometry and wet highlights against the original frames. Avoid increasing standalone 3D-cell objects or rewriting the SDF engine.

Environment note: Mac disk free temporarily dropped below about 150 MiB during work; new large binary builds should remain bounded. No unknown files were deleted, and no private frames were committed to GitHub.
