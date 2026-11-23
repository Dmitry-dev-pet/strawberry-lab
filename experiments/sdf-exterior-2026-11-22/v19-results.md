# Strawberry Lab v19 — central pith separated from the vascular bundle zone

**Research date:** 23 November 2026. **Decision: ENGINEERING PASS, VISUAL TARGET NOT ACCEPTED.** Independent experiment; original v12 remains intact, and neither variation is a main-branch candidate.

## Reason for experiment

The owner's question — “Я думал белое в центре это и есть сосуды?” — revealed that we were often conflating two anatomical regions in visual discussion. Published strawberry descriptions put the **pith** at the centre, a **vascular cylinder or ring** around it, followed by the fleshy **cortex**, with radial connections to external achenes. Primary qualitative references: Darrow, *The Strawberry* (1966), figs 19-38/39; Hurtado & Knoche (2026), Fig. 1B and section 3, DOI 10.3389/fhort.2026.1779354. None of these establishes our actual Blender radii/brightness numerically.

Our private owner-provided Frucht film frame at ~10 seconds appears to have pale longitudinal streaks around a more red centre. However a movie frame cannot establish which tissue/channel or node group the commercial generator uses. The author publicly described a NumPy precomputed vascular fibre field and a SDF cut; **we have not inspected the closed source**. Previous v9 experiments made the entire pith broad/pale and were visually rejected, especially on spherical bite. Cutter placement changed the apparent form of the centre.

## One tissue-layout hypothesis, two A/B controls

Starting from exact owner-v12 `strawberry-sdf-vertical-slice-v12-continuous-wet.blend` SHA-256 `300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410cbb405b7`:

- **v19A**: replace only the existing **B/pith** 3D field by a tapered, slightly bent central core, peak artist radius **2.8 mm** near Z=25 mm, fading at ends. Original R/vascular and G/mottling retained.
- **v19B**: same B/pith field plus a **discrete, curved longitudinal bundle collar** in the original **R/vascular** 3D field, outside the pith boundary. The source seed-connected R curves are preserved using a max operation. A ring of separate bundle signals is meant to avoid a completely uniform bright white annulus.
- Both use the **same 192³ rest-space RGB packed atlas** sampled by 2 Geometry Nodes and 2 Cycles image nodes, with unchanged SDF cutters, original achenes, cut material and Voronoi configuration. Neither variant introduces detached tube geometry, explicitly modeled individual cell membranes, or a new material shader.
- The model's radial pith/collar dimensions, axial falloff, colour interpretation and number of signal lobes are deliberately **ARTIST**, not empirical morphometry, and should not be identified as true xylem/phloem measurements.

## Independent saved-scene Blender QA

Blender **5.2.4 LTS Linux x86-64** read each saved `.blend` with script autoexecution disabled. The evaluated final GN mesh was checked for signed positive volume, manifold edges, and cut-only material assignment, on five actual source states per variant: whole, original oblique planar cut, centered axial planar cut, spherical bite, and moved/scaled spherical bite. **10/10 tested mesh states: 0 nonmanifold edges and positive signed volume.** The centered axial plane requires a **−1.745602 mm cutter-face translation** to pass through world original rest `(0,0,25)`; this translation is applied to render/QA processes only, not saved permanently in v12 or variants.

| Cut-only field coverage, evaluated cap quads | v19A | v19B |
| --- | ---: | ---: |
| Centered axial plane — R≥0.30 area | 2.83% | **4.98%** |
| Centered axial plane — B≥0.50 area | 5.42% | **5.42%** |
| Original oblique plane — B≥0.50 area | 0.00% | 0.00% |
| Original bite — R≥0.30 area | 1.23% | 2.18% |
| Original bite — B≥0.50 area | 0.34% | 0.34% |
| Moved bite — B≥0.50 area | 8.41% | 8.41% |

Thus the normal front-facing bite does not expose much central pith, while a moved bite can expose it substantially. Do **not** generalize the small default-bite area into a promise for arbitrary cutter positions. Cap-area percentages use mean per-quad sampled attributes at threshold and are not microscopically measured tissue area. The original rest-space R field sampled from the packed atlas matches GN `v8_vascular_intensity` on evaluated cap vertices within maximum **7.3×10⁻⁵** for these runs.

## Genuine Cycles visual review

CPU Cycles 640×640 / 16 samples, fixed camera, lighting and native frames; six new renders from v12 / v19A / v19B centered plane, v19A/B original spherical bite and v19B macro. The unchanged v12 spherical bite was previously rendered at the same settings and reused for the A/B sheet. All are original Blender output — no ImageGen.

- Centered axial slice: the added vascular collar in v19B contributes extra, somewhat more continuous longitudinal pale streaks. But these still appear as softened thin stripes, not the complex glistening mass visible in the owner Frucht film. The visual difference is **small** and does **not** pass the accepted quality target.
- Bite: both variants look almost identical to v12 and remain a smooth scooped bowl. A 3D organ mask does not itself create torn flesh geometry.
- Macro: persistent soft vascular stroking, no convincing real cut cell/vascular texture from the new anatomy alone.

The matched original **v19A versus v19B** rendered difference exceeds 0.01 in at least one RGB channel on only **1.971% of centered-plane pixels** and **0.756% of default-bite pixels**. This is an objective delta test, NOT a perceptual-quality score. The comparison to the author's promotional video remains qualitative, because the cutter pose, lighting, specimen and camera are not pixel matched.

## Assets and restoration

Owner-only private Drive folder: [Strawberry Lab — research-sdf-v19-pith-vascular-20261123](https://drive.google.com/drive/folders/1A7dVhA8fMp82vthchXO7Ix8xS6tjr7gd).

Verified archive: `strawberry-v19-pith-vascular-study.zip`, **68,655,257 bytes**, SHA-256 `9cfbfb9734122393b69b3c8941227edb9df656eb418dea7cd11569a4bac9e2a0`. Uploaded to the owner-private Drive folder then downloaded back. Complete byte-for-byte SHA-256 matches; **all 32 ZIP members** independently rehashed PASS. The package contains both editable `.blend`, both atlases, original render PNGs, visualization, original Python source, QA JSON and log receipts. The protected author-film frame is NOT included. Original v12 is NOT bundled and remains in its previous owner-private Drive location.

Local source scripts inside the artifact: `build_v19_pith_ring.py`, `qa_v19.py`, `render_v19.py`, `run_render_batch.py`, `plot_v19_fields.py`, `analyze_v19_renders.py`. Analysis is based on the existing v12 research SDF source and cannot be applied as a scientifically measured model to arbitrary cultivars.

## Next sensible hypothesis (NOT implemented)

To increase Frucht-like fidelity, do **not** further widen the pith or simply whiten the bundle collar. First study why the shared shader fails to show fine *longitudinal vessel structure and parenchyma* at similar local detail, especially across both vascular collar and radial peripheral paths. Keep a diagnostic anatomy-color toggle separate from normal photoreal rendering; validate the field along the centered plane before altering global wetness or mesh density. The current work proves a cleaner separation of fields, **not** product-quality strawberry flesh.
