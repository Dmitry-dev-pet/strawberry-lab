# Reference-first Fast → Exact / Finalize audit — 24 November 2026

Research continuation of draft PR50 at `1efca4315dc6b4802626a3478682da68340cd0bb`. **Source and original free Kiwi runtime checks completed; no new Strawberry implementation or visual acceptance.** Keep prior integrated and split scenes unchanged. No main merge. Do not copy the unavailable commercial template, GPL node trees, source, meshes, assets or parameter presets. All conclusions about strawberry are explicitly fragment-level evidence, not commercial runtime observations.

## Primary source and architecture

Exact owner-provided Frucht Free Kiwi 0.4.3 ZIP SHA-256 `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877`. All 71 files in the extracted original package were checked against archive bytes before execution. The add-on declares GPL-3.0-or-later and the free package contains Kiwi, not the commercial Strawberry blend. The original add-on ran privately, without source modification or paid-feature bypass. The archived Linux Blender runtime SHA-256 `2fd14c50987426897ba60237ee996edf2b4151f4b1a72a460ca20be58c1d2d86` verified. Blender 5.2.4 LTS build `cd5dc428cce1`. Source pointers refer to that exact private ZIP.

| Operation | Direct source evidence | Meaning |
|---|---|---|
| Placeholder/Fast/Exact | `schnitt.py:8–56`, `api.py:284–302` | Explicit display modes for a whole fruit. Exact has a species/cutter capability check, ensures missing vascular data, enables true-cell control where applicable, turns off Fast and re-enables original cuts. It does NOT subdivide, weld or locally correct the prior Fast output. |
| Preview routing/cache | `jobs.py:419–434,437–574`, `fast.py:145–183,776–784,1212–1218` | Valid neutral exterior and leaf bakes can be reused; interior stock is lazy. Fast reads cached preview sources. Exact routes display back to ORIGINAL source objects and hides separate Fast flesh. Preview resolution is independently set/restored (`aufloesung.py:14–31`, `jobs.py:512–526`, `api.py:486–493`). |
| Automatic policy | `automatik.py:70–76,89–147` | During motion use lightweight view; while quiet in rendered view request Exact if supported. This is source evidence; our test pins modes and pauses auto switching. |
| Kiwi live Exact | `schnitte.py:277–292,572–592`, `fast.py:280–325` | Kiwi permits one plane or no cutter. Plane transform is synchronized with its internal controller; `Echte Zellen` enables real cut cells on original graph. Prior directly inspected Kiwi root uses Mesh Boolean. This is not the commercial strawberry cut route. |
| Strawberry live Exact | `fruechte.py:24–45` (`HAT_Z1=True`), `schnitte.py:217–251,277–282,294–310,585–591,1257–1294` | Shared code inserts cutter collection → realized mesh → SDF → difference before the existing original body's GridToMesh; species condition allows multiple cuts/bites. True-cell toggle from Kiwi is bypassed for this route. The paid original body graph is missing, so its full surface construction, voxel strategy and quality remain unverified. |
| Shared boundary then display separation | `gliederung.py:19–25,299–344,357–390,540–551` | Strawberry Skin and Flesh ORIGINAL routes both read KORPER. `_filter` computes the material ring and smooths a common mesh before deleting faces of the other display part. It is not a weld of independently generated Fast meshes. The earlier synthetic probe independently demonstrated this distinction. |
| Split | `api.py:530–542`, `teile.py:295–371`, `spawn.py:185–238` | Each piece stores stand/shape state and cut transforms; preview is generated from stock, with a separate flesh path. |
| Finalize | `api.py:546–561`, `teile.py:445–553`, `spawn.py:377–441,444–500,503–523` | For each chosen piece, temporarily restore source shape and its saved cutters, compute original geometry, pack a GeometryNodeBake, restore whole-fruit state, attach new source and mark piece exact. Grouped strawberry piece display filters the common baked body by material. Finalize is distinct from live Exact mode. |

## Fresh runtime experiment (not a library-only inspection)

Independent `probe_exact.py` in an isolated Xvfb GUI, factory startup, scripts disabled, explicitly imported original private add-on, CPU 4 requested threads, resolution 40%, automatic quality switching paused. No Strawberry file opened by the probe. `runtime.json` and logs private; `summary.json` records observed aggregate mesh counts, coordinate/triangle hashes and material adjacency, not actual meshes or graph wiring. A first harness attempt failed because the temporary evaluated GeometrySet was released before its mesh was read; held a reference on retry. Original source and model unchanged. Final run completed after 121.150 seconds (includes entire test, polling and evaluations, not an interactive benchmark).

### Live transition

| State | Displayed body vertices | Separate visible flesh vertices | Body boundary edges | Shared skin/flesh material edges |
|---|---:|---:|---:|---:|
| Placeholder whole | 25879 | 0 | 0 | 0 |
| Fast plane | 13283 | 42814 | 229 | 0 |
| Exact same plane | 117889 | 0 | 8704 | 1904 |
| Exact after confirmed plane rotation | 108434 | 0 | 8818 | 2048 |
| Fast rotated | 13509 | present | see receipt | 0 |
| Fast original plane restored | 13283 | 42814 | 229 | 0 |

Fast plane reads `SCHNELL KIWI | Körper`, material skin only; separate flesh has zero boundary edges. Exact switches routing to `KIWI | Körper`, separate flesh hidden, actual `Echte Zellen` input true. On the Exact mesh, material indices 1 and 2 are skin and flesh, and 1904 edges have one face of each material. Additional materials include cells, seed strands and vascular bundles. Boundary counts include all evaluated mesh components; no global watertightness claim. Over-two-face edges zero at these snapshots; that is not a full manifold/self-intersection test.

A requested 65-degree plane rotation returned success before the internal controller updated. Initial snapshot still had the old geometry hash and needed plane sync. At the subsequent observed snapshot (62.009 s since start), controller aligned and geometry hash changed, with 108434 vertices and 2048 shared material edges. The original explicit sync function then returned false (already aligned). Thus actual movement is now confirmed, resolving the previous audit's premature observation. When reset to original plane in Fast, both skin and flesh position/triangle hashes matched original Fast exactly. An immediate subsequent Exact snapshot still showed rotated geometry and pending plane sync; do not claim Exact roundtrip equality or treat API success as settled geometry. No fault injected or automatic-policy performance inference.

### Finalize

Removed live cut, used original blade/split API. Two pieces created in preview (`schnell`), 53470 and 51806 body vertices. Finalized only piece 1 through original API. It became `echt`, 112313 vertices, 1916 skin/flesh shared material edges, own packed bake with 10 data blocks. Piece 2 remained `schnell`, position and triangle hashes unchanged. Applying a translation of one model unit to finalized piece preserved its local evaluated position and triangle hashes; the other piece also stayed unchanged. This is a local mesh observation after translation, not a separately measured world-transform or disk-reopen test. The packed result was observed in the running original app, not a new exported reference scene. One finalized half took approximately 24 s from request to observed receipt, including polling/evaluation. No new render or commercial strawberry runtime claim.

## Decision / next bounded hypothesis (not implemented)

Stop optimizing the disconnected preview seam as if it must be the final surface. Preserve current neutral stock and split Fast experiment (including negative controls). Design **an independent separate Exact path** based on the same `NeutralStock`, `AnchorSet`, common shape map and actual cutter geometry. Begin with one planar and one spherical cut, using a single connected material-labelled source-body result, before splitting for display. Reuse owned prior full-body SDF technical control and the verified inverse rest-coordinate contract as comparative inputs, not as a mandate to blindly restore the old mesh. Check shared skin/cap edge incidence, cutter provenance, pit-depth loss, rest coordinates, seed completeness, and original stock/Fast hash stability when switching. Keep resolution and quality policy explicit; a preview may retain exact original skin while final surface requires independent high-resolution generation. Do not assume a globally welded or watertight final fruit merely because the original Kiwi calls its mode Exact. Introduce no new vascular, cell, liquid or pigment tuning until this branch's common-boundary contract is verified. Finalize/baked piece state is a later separate operation. This proposal does not replace the adopted main ADR without review.

## Reproduce

Use an owner-authorized exact reference ZIP extracted to `/private/frucht_free`. Fresh output directory; no protected-feature changes. The private logs include the initial harness failure. Actual test ended at stage 15; `summary.json` records 11 independent aggregate comparisons passed and the stated limitations. Frozen Strawberry files were checked against the previous SHA-256 values after the probe.

```sh
export FRUCHT_PRIVATE_PARENT=/private
export FRUCHT_PROBE_OUT=/private/fresh-exact-probe
export LIBGL_ALWAYS_SOFTWARE=1
mkdir -p "$FRUCHT_PROBE_OUT"
timeout 195s xvfb-run -a -s '-screen 0 1024x768x24' /path/to/blender --factory-startup --disable-autoexec -t 4 --python probe_exact.py
```
