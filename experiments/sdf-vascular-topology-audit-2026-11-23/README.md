# Vascular topology and lumen — reference audit, 2026-11-23

Read-only source/scene investigation following the PR50 pigment negative control. No new Blender geometry, shader, author code or assets transferred. No commercial Strawberry scene access or biological validation claimed.

## Primary evidence

Owner-private Frucht Free Kiwi 0.4.3 ZIP (SHA256 aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877). Exact local archive reopened and source inspected. The shared package contains strawberry-specific code but does not contain erdbeere.blend.

- leitbuendel.py:13,19–81: shape-preserving cubic-interpolated ring radius profile, curved axial centre, azimuthally varying elliptical ring, longitudinal carrier paths (default 28), variable radii along carriers and terminal branches. Terminal branch joins the ring at a higher z than its target (subject to top clamp), picks a carrier by angular sector, curves with axial sag and tapers. No single axial trunk and no per-achene secondary twig in this generator.
- leitbuendel.py:301–336: terminal targets are extracted from the evaluated full achene instance transforms in neutral shape state, then slightly displaced inward toward the origin. This is not a claim that their unmodified centres are exact endpoints.
- leitbuendel.py:84–144: maximum-combined Gaussian stamps; full-resolution 256³ core, halo carriers at 64³, halo terminals at 128³, interpolated and combined. Atlas third channel is a signed radial offset relative to the local elliptical ring (bounded remap), not a generic pith mask or independent noise field. No physical dimensions inferred from these normalized coordinates.
- leitbuendel.py:200–298, fruechte.py:33–34, schnitte.py:943–957, 985–1022, 1040–1086,1114–1128: distinct irregular closed medullary-lumen geometry and 32 attached tissue bridge shapes are constructed when the required objects exist. The flesh-source builder subtracts the cavity SDF before the user cutter and assigns a separate wall material in the cut pathway. This is a real geometric cavity in the accessible implementation, not proof of the runtime configuration of every commercial fruit.
- hoehlung.py:3–49 separately adjusts cavity wall and tissue-fragment appearance.

## Our actual baseline

PR50 shadow-transparent scene SHA256 361696819fd44733d560e3f59b101cd11f59862e7ebd7b7f83ce94fd07909963 reopened with Blender 5.2.4 build cd5dc428cce1, scripts disabled. Raw receptacle mesh has one connected component (47,384 vertices), zero nonmanifold edges. Its only body Boolean is the user plane/sphere SDF difference; no named cavity object or cavity SDF input. In particular the existing one-component closed-surface geometry checks do not implement a separate enclosed lumen. Current source anchors: 264, canonical z range 1.677–47.298 mm with the existing +27 mm shift. Raw body z range -1.320–50.520 mm.

PR49 original graph and fields were read from the saved research archive; Git blob hashes verified equal to the GitHub source at 3a09a524f56328752a4d36b79a0afe1805996127 (v19_graph.py 2db048cbfae5be46009bcac196bb517cb360ece1; fields.py 64b75c9e30d13a97c12e7b89af77da55b8abe489). Our graph has one straight axial root, 28 carriers beginning at a common point and widening monotonically toward high z, 264 terminals attached to a sampled carrier point approximately below the target, 264 additional twigs; constant sigma per segment. Our 192³ core and halo use the same resolution, max-combined Gaussian rasterization, halo width x1.8, separate atlas with B unused. Existing 150³ material atlas remains independent. Our previous pigment-coherence diagnostic adds an artistic axial spindle, not the ring-relative coordinate or a geometric lumen.

## Quantitative profile comparison

Direct evaluation of only the inspected numerical reference radius interpolation (not the Blender add-on or commercial scene). Normalize each carrier's longitudinal parameter from its own first to last z, and each radius by its own maximum. This compares **shape of the carrier radius profile**, not physical dimensions or measured histology. Reference azimuth modulation and axis offset are excluded from this base radius comparison.

| Relative longitudinal position | Reference | Ours |
|---|---:|---:|
| 0% | 0.045 | 0.000 |
| 10% | 0.163 | 0.138 |
| 25% | 0.434 | 0.304 |
| 50% | 0.845 | 0.551 |
| 65% | 0.998 | 0.690 |
| 75% | 0.936 | 0.781 |
| 90% | 0.426 | 0.913 |
| 100% | 0.108 | 1.000 |

Reference base profile peaks near 63.3% of carrier height. Ours peaks at its high endpoint. The topological difference is substantial even though both have 28 carriers. Do not claim this observation alone proves the cause of the visual artifacts.

## Next independently authored hypotheses

1. Replace the current single-root artificial graph with an independent ring-oriented rest-space architecture fitted to our actual fruit envelope, curved centreline, variable carrier radius and smooth tapered terminals to inward-offset achene anchors. Preserve seed IDs and verify endpoint association, continuous paths, inside-fruit containment and reproducibility. Introduce a separately named ring-relative scalar field. Do not copy the author's source, profile table, node trees or numeric presets.
2. Controlled A/B first: old versus independently generated fields, same accepted SDF body, cell/juice algorithms, original shadow-corrected materials, cameras and render settings. Visual and field QA separately. A graph connected to one central root is no longer the acceptance criterion for the new architecture; verify branch-to-carrier connections instead. This is still ARTIST morphology, not a measured vascular reconstruction.
3. Separately test a small irregular medullary cavity cut from the body before the editable cutter, with a distinct cavity-wall material. Check exterior unchanged, orientation and positive tissue volume, watertight cavity walls, consistent cutter behavior and juice/cell exclusion on uncut cavity walls. A sealed internal cavity creates an additional boundary component; distinguish this from detached tissue or nonmanifold defects in QA. Do not mix this hypothesis with the ring-graph A/B.

No change to main, no visual acceptance, no new renders in this audit. Preserve the shadow correction and all prior negative controls.
