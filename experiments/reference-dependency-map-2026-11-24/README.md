# Reference-first dependency map — Frucht Free 0.4.3, 24 November 2026

**Research only; no new Strawberry mesh/material or main merge.** The integrated control remains SHA-256 `790dc4adbd9025b56e7833c2cedb8ada83c0e9b738ac294f96889fbb52e0e215`. This maps the available ordinary live/non-video pipeline, the piece pipeline where relevant, and evidence limits. It is not a reconstruction of the absent paid Strawberry node graph. The exact original ZIP was reopened, SHA-256 `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877`; its free edition exposes only Kiwi. Source pointers below identify the owner-private archive without reproducing code, graph wiring, numerical presets or assets. Prior actual Kiwi execution in `../reference-first-runtime-2026-11-24/summary.json` was reread and cross-checked; **not rerun in this audit**. No new render. Retain earlier independent negative experiments.

## 1. End-to-end dependencies and evidence

Evidence notation: S = executable source inspected, K = previously observed actual Kiwi runtime/graph, E = strawberry-specific executable fragment, D = description or reference to unavailable commercial graph, P = our independent proposed contract. K does not imply an observation on strawberry. The exact paid template cannot be reconstructed from these fragments.

| Stage | Input -> output / dependency | Evidence and limits |
|---|---|---|
| Species template and instance | Species registry and authored package -> visible components, hidden source data, materials, groups, root object, initial state | S: `fruechte.py:12–124,332–356`, `neu.py:210–300`, `api.py:265–270`. K: previous create/placeholder receipt. E: strawberry initialization invokes shared distribution, edge, vascular/shader and cavity setup; D: `erdbeere.blend` unavailable. Author app selects an active species globally; do not copy global mutable state into our FruitContext. |
| Neutral silhouette / resolution | Reference profile and resolution -> source skin mesh; neutral shape state resets macro-form coefficients and seed | S/E: `aufloesung.py:42–71`, `spawn.py:583–599`, `form.py:184–223`. D: exact reference curve and full pit/skin graph absent. |
| One seed distribution | Profile + density/count -> surface positions/normals on one shared point mesh, used by both seed and form distribution | E: `form.py:164–223,680–692`. Area proxy along meridian and golden-angle spacing. Actual pit topology and placement subgraph unavailable. |
| Surface organs | Same seed anchors + organ controls -> pits, source skin, seeds, hairs, crown; separate foliage source | E: `form.py:69–123`; D: missing pit/contact/skin trees; `ordnen_texte.py:89–96,137–160,171–185` is descriptive evidence, not executed node wiring. K: packed whole-source cache and packed leaf cache; Kiwi organs are not anatomically interchangeable with strawberry. |
| Neutral geometry caches | Source mesh/instances + typed keys -> whole stock and foliage stock (`GeometryNodeBake`, packed); optional contact source for foliage | S: `fast.py:366–497`, `jobs.py:437–519`; K: prior two valid stocks at placeholder, no inside cache. |
| Common forward shape | Neutral mesh and instance positions + form controls -> transformed positions; optional organ-specific alignment and instance scale; inverse rest mapping for strawberry flesh | S/E: `formen.py:102–301,426–437,652–685,724–763`, `form.py:648–692`, `anlegen.py:123–190,193–260`. K: radius change altered bounds while counts unchanged. Not proof that all topology-changing settings avoid rebuilds; inverse map is numerical, not guaranteed globally bijective. |
| Vascular field | Evaluated full achene instance transforms in neutral state, inward-offset endpoints + vessel parameters -> tapered ring paths -> core/halo/ring-relative packed 3D atlas | E: `leitbuendel.py:35–144,301–336,346–420`. The shared shader/cell template samples this field. D: full commercial flesh shader absent. Important key limitation in section 2. |
| Medullary geometry | Cavity-size control + source objects -> irregular inner cavity/attached tissue | E: `leitbuendel.py:168–184,200–298,346–365`, `hoehlung.py:3–49`. Kiwi has no same cavity branch; no biological or visual parameter calibration. |
| Separate flesh form | Evaluated neutral outer source mesh + current forward shape and cavity mesh (if species has it) -> deformed flesh form + tagged cavity faces -> packed bake | S/E: `schnitte.py:922–967`, `jobs.py:505–508`. Cavity receives common form only if the species flag enables it; do not assert the strawberry cavity is universally warped. K: flesh-form bake appeared on Fast. This is not a single cache containing every tissue cell. |
| Reusable volume source | Tagged flesh form -> outer SDF minus cavity SDF if present; named grid `form` + outer remeshed surface and cavity geometry for proximity | S/E: `schnitte.py:970–1024,1202–1224`; K: distinct Flesh Source with MeshToSDFGrid, StoreNamedGrid and GridToMesh. Distinguish geometry bake from derived named grid. |
| Cutter / quality policy | Editable plane, bite, combined cutter geometry -> common transforms/masks; choose Placeholder / Fast / Exact | S: `api.py:284–302,441–475,1743–1787`, `schnitte.py:273–310,1257–1294`, `schnitt.py:30–56`. K: Fast plane and bite evaluated; Exact one plane evaluated; requested Exact rotation not geometrically confirmed; exact bite explicitly rejected for Kiwi. Source permits broader strawberry exact options (`HAT_Z1`/`echt_alle`), not executed. |
| Skin and exterior cut | Original exterior mesh + instances, transformed cutter -> sample cutter SDF, discard selected instances/faces; alternate border snapping/clean clipping per condition | S: `schnitte.py:607–649,652–714,721–796,1227–1254`; K: Kiwi Fast skin's Live group has cutter SDF, SampleGrid, two DeleteGeometry, no GridToMesh. Original outside is not reconstructed as a full SDF skin. **Not a guarantee of exact preservation at the edge or actual seed-solid intersection.** |
| Flesh cut and layer registration | Cached named flesh grid + cutter grid -> difference and remesh; compare distances to outer surface, cavity, cutter; set wall flag, edge distance, flesh material and recess non-cut outer flesh under skin | S/E: `schnitte.py:1027–1153,1170–1199`; K: distinct Fast cut surface has GetNamedGrid, SDFGridBoolean, GridToMesh. The source yields a flesh mesh, not only an open cap polygon. A small offset under skin explicitly manages overlap; independent closure/interface QA still needed. |
| Coordinate contract | Physical position -> stored inverse rest offset (`ruhe_versatz`); piece relocation -> `frucht_versatz`; proximity -> `schnitt_rand_abstand` | E: `formen.py:724–763`, `spawn.py:118–158,230–235`, `schnitte.py:1088–1097,1183–1188`; cut cell module adds both offsets to position. Use our original names/types, not a copied author graph. |
| Cut-face cells | Geometry with selected flesh material + vascular image + rest coordinates and edge distance -> smooth pre-relief position/normal, adaptive subdivision of separated cut faces, locally varied cell relief and vascular suppression/lift | E: `zellen.py:73–201,213–229`, private `daten/zellen_saft.json`. Actual source separates cut faces before subdivision and joins other geometry afterwards. Default attachment to cut strawberry pieces via `spawn.py:197–201,228–238,280`, `zellen.py:242–257`; not proof every live mode runs this module. Kiwi uses different specialized groups. |
| Liquid surface | Same exposed flesh, saved smooth position/normal (fallback current), thickness/amount/drop scale and edge margin -> separate selected geometry joined after existing surface; height-dependent tint and shadow handling | E: `saft.py:24–57,80–160,255–268`, `reissbrett.py:215–294`, private JSON template. Cell modifier ordered before juice; juice subdivision depends on presence of active cell modifier. No evidence of fluid simulation or measured liquid volume. |
| Edge and attached organs | Source skin / exposed flesh / cutter boundary -> seam band, local edge smoothing, strand/seed policy, normal alignment and foliage attachment | S/E: `form.py:237–334`, `schnitte.py:607–714`, `gliederung.py:165–356`, `zellen.py:265–377,386–525`, `anlegen.py:140–260`. These are alternate/context-specific paths, not a single universal seam algorithm. |
| Piece state / finalization | Shared stock/stand ID, independent cut list and shape state, piece transform -> fast piece, exact finalization / frozen result | S/E: `spawn.py:185–280,377–523`, `api.py:530–561`; no new piece runtime test; exact Kiwi quarters not supported according to API docs. Preserve rest coordinates under relocation. |
| Optical/material changes | Existing spatial fields + independent shader controls -> skin, cap, cavity, juice shading | S/E: `form.py:337–445,844–858`, `reissbrett.py:74–294`, `hoehlung.py:3–49`; complete commercial material missing. Preserve distinction between material-only parameter and geometry-dependent field. |

### Explicit sequencing and feedback

Creation calls `neu.erzeugen` -> source setup -> `jobs.fast_starten(platz=True)`. `jobs._frei_starten` checks missing inside/vessel dependencies when requested, compares three cache keys, bakes only missing/stale source parts. It temporarily sets neutral state for source bakes, then restores actual shape state. Flesh form is produced from the outer stock and the current state. `schnitte.quelle_bauen` reconstructs the derived flesh source when the flesh-form key changes. `schnitte.live_bauen` sets up skin/instance removal and independent flesh display from the same cutter collection. Parameter changes use `form.anwenden` / deferred `_schlange` to update current shape, attachment and shader state, then check caches. Cut movement uses `schnitte.anpassen`, potentially promoting Placeholder to real Fast if penetration occurs and automatic mode allows it. These are dependency edges, not a claim every step runs on each edit.

## 2. Reproduced invalidation-key behavior

`audit_dependencies.py` parses the exact private archive, obtains the original parameter classes and executes only the three pure key/class functions in an isolated minimal species/resolution context (no author code exported). It probes **64** distinct parameters/state fields, varying one at a time. Result in `dependency-keys.json`. This is a **key-function probe**, not a GUI rebuild test of commercial Strawberry. Seven explicit expectations passed. Source: `fruechte.py:12–88,336–337`, `spawn.py:583–599`, `leitbuendel.py:157–189`, `jobs.py:451–458`.

| Parameter/change | Exterior stock key | Leaf key | Flesh-form key | Vessel key |
|---|---|---|---|---|
| Macro length | — | — | changes | — |
| Seed count / size / pit depth | changes | — | changes | — |
| Crown hill size | changes | changes | changes | — |
| Cavity size | — | — | changes | — |
| Vessel strand count/width | — | — | — | changes |
| Skin gloss | — | — | — | — |
| Seed alignment | — | — | — | — |
| Shape seed | — | — | changes | — |
| Leaf seed | — | changes | — | — |
| Resolution | changes | changes | — | — |

Do not interpret blanks as proof of no actual work: `jobs._frei_starten` forces interior rebuild when the exterior cache changes, and may also rebuild foliage when a stand is referenced by other pieces. Cavity is separately checked by `leitbuendel._hoehle_fehlt`; vessel atlas has its own asynchronous calculation. Display and shader edits still update relevant state. The position of an editable cutter is separate from the four generation keys, but the first penetrating cut can trigger lazy inside creation. A key changing is not proof that a new baked result exists.

**Potential source-level cache dependency gap**: `_enden()` derives atlas endpoints from evaluated neutral achenes, but `leitbuendel.schluessel()` depends only on six vessel controls, not the actual anchor fingerprint. Changing `kern_anzahl` in the isolated probe changes exterior and flesh keys but not the vascular key. `_schlange` checks `leitbuendel.fehlt()` before scheduling, which compares the atlas key and cavity status. This is evidence of a *possible stale atlas* on count changes in the accessible source, NOT a demonstrated runtime bug in the missing commercial scene. Do not copy this contract blindly. Our own proposed vessel key must contain neutral-anchor digest and algorithm/coordinate version as well as its own controls.

## 3. Proposed independent implementation contract (not implemented)

Reuse `FruitContext` and original PR50 mechanisms only when they satisfy the explicit dependencies. No new universal engine or visual tuning yet.

| Record / module | Contract |
|---|---|
| NeutralShape | Versioned canonical shape and rest frame; deterministic normals and surface-area mapping. |
| AnchorSet | Stable seed IDs, rest positions, orientations, organ/pit dimensions; deterministic digest. One shared record for all exterior and vascular consumers. |
| ExteriorStock | Neutral skin mesh, seeds/hairs and optional attachment geometry. Key = shape source, anchor digest, surface controls, resolution/version. |
| LeafStock | Separate leaf inputs and skin contact signature only where needed. |
| ShapeMap | Common forward/inverse map, including normals and verified rest-coordinate transport; no per-organ unrelated deformation. |
| VascularField | Neutral anchor digest + ring settings + atlas resolution/bounds + algorithm version -> shared core/halo/ring coordinate. |
| FleshSource | Shape map + source envelope + cavity -> reusable closed volume and tagged walls. Separate from render skin. |
| CutState / SkinCut / FleshCut | One cutter and coordinate contract; skin clip preserves outside original geometry, flesh separate grid; actual solid intersection policy for seeds. Explicit interface/overlap and edge checks. |
| CutSurface | Uses cut face provenance, rest coordinates, edge distances, tissue fields, pre-relief position/normal; local refinement, cells, then juice. |
| Materials | Spatial inputs from same upstream fields; shader-only changes must not alter geometry hashes. |

**Next bounded experiment (proposed):** do not introduce new fruit appearance knobs. First create a small neutral-shape/exterior contract using the existing independent anchor generator and a common shape map, with shape-state roundtrip, seed/pit registration and deterministic cache hashes. Test exactly one shape change and one seed-count change. Preserve the previously frozen PR50 scene. Next test separate skin and flesh cuts at matched resolution, no cells/juice/material changes until exterior registration, edge integrity, cavity classification, and field continuity pass. Test unchanged outside original vertices, edge gap/overlap and actual seed solid crossing separately. Use matched renders and measured cost only at that stage. This does not override the adopted main ADR; it refines its independently authored experiment order and requires owner review before adopting a new baseline.

## 4. Reproduction of this audit

```sh
python audit_dependencies.py /private/frucht-free-kiwi-0.4.3.zip /path/to/reference-first-runtime-2026-11-24/summary.json /tmp/dependency-keys.json
```

Python standard library only. The private archive is a required local input; this report publishes neither its code nor nodes/assets. The runtime receipt is from the earlier actual Blender probe. Output is aggregate key-change names, old runtime counts and source/receipt hashes. This stage makes no new Blender geometry, visual fidelity, performance or commercial runtime claims.
