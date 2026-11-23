# Cell Surface — smooth centre field, first bounded study

23 November 2026. Original independent research, based on the owner-approved SDF baseline PR47 (main 61b403eb1fbdc2cff72afdaf95504f4fe7e46b17). Technical PASS for the tested states, visual acceptance pending / Frucht parity not reached. No commercial scene, GPL source nodes or preset values copied. All numeric geometry parameters ARTIST.

## Hypothesis and mechanism
Unlike PR49's distance-to-edge on the existing SDF mesh, use a smooth nearest-centre 3D field, continuous radial frequency warp, low-frequency spatial deformation and fixed stored smooth position/normal. Apply a bounded positive dome displacement to cut material only, fading by distance to the original skin. One full connected mesh subdivision level while enabled, rather than splitting cap and skin into a T-junction. This is deliberately global conforming subdivision, not yet cap-local or automatic adaptive refinement. The skin topology changes in cut mode, but skin-only and seam positions are unchanged relative to the refined reference positions. Same original 150^3 atlas, materials, seeds and SDF engine, no wet-film or vascular changes. PR47 centre-only seed masking limitation remains. Gain=0/whole bypasses the module. A new shared scalar `sl_cell_dome` and `sl_cell_reference_position`/`sl_cell_reference_normal` are stored for subsequent study. The colour of the core is not fixed here.

## Reproduce
Verified official Blender 5.2.4 Linux x64 runtime restored from 17 private Drive parts and manifest: archive SHA256 2fd14c50987426897ba60237ee996edf2b4151f4b1a72a460ca20be58c1d2d86. Input: owner-private rebuilt-sdf.blend, SHA256 c27ebc88e17e5172c80b3d4dbc3882a78be690fcc7a8f0af68d697d18addbc4f, PR47 evidence folder https://drive.google.com/drive/folders/1geMz9gMgm5ze6BV8WoiPg_tADWRNx1-z. No private reference footage or third-party assets included.

```
B=/path/to/blender
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_cell_surface.py -- rebuilt-sdf.blend cell-surface-ab.blend
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_cell_surface.py -- cell-surface-ab.blend qa-032.json .32 whole plane oblique bite
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_cell_surface.py -- cell-surface-ab.blend qa-020.json .20 plane
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_cell_surface.py -- cell-surface-ab.blend plane 0 plane-A.png .32
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_cell_surface.py -- cell-surface-ab.blend plane 1 plane-B.png .32
```

Use absolute paths for saved scenes and render outputs. For macro and bite substitute shot names. Open the saved scene with autoexec disabled, select Receptacle | canonical PR29 hull and set `sdf_mode` 1 or 2, `sdf_voxel_mm` 0.32, `cell_surface_gain` 0 or 1, `cell_surface_detail` 1 (UI range 0–1). The saved default is whole and gain zero.

## Actual QA
5 A/B pose/voxel comparisons (10 evaluated body states): 0.32 mm whole, plane, oblique plane, sphere bite; 0.20 mm plane. All zero nonmanifold edges and degenerate render triangles, positive volume. Whole A/B exact vertex-coordinate SHA. All four cut B states: 0 observed skin-only and seam displacement from the stored refined reference, max relief ~0.145 mm. Coarse plane 59,400 -> 237,594 vertices; fine plane 152,500 -> 609,994. Peak process RSS 1,042,540 / 1,376,232 KiB (not isolated modifier memory); fine plane full evaluation + QA 4.87 s A / 17.64 s B. 45 native nodes. Not exhaustive self-intersection/seed/calyx validation; arbitrary poses beyond these not verified. Subdivision may slightly alter original nonplanar quad surfaces; the reference is the subdivided surface, not an exact continuous-surface equivalence test. 

Six actual matched CPU Cycles 480x480 /8 samples, seed 1729; plane, closer plane, sphere bite. A/B render times (after scene state setup): 4.62/7.21, 4.80/7.53, 4.56/6.63 s. Per-image receipts include SHA. Visual result: more real relief but uniform granular/pitted appearance, too broad pale pith, smooth rounded bite and glossy artificial highlight. Visual target remains FAIL; do not merge solely based on numeric QA. Next bounded work: test cap-local conforming refinement, regional heterogeneity and separate common-field vascular relief suppression; no additional droplet parameter sweep or switch away from SDF. Original author source reviewed statically only; full commercial tree not available.
