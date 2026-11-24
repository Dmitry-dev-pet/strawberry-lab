# Exterior audit — Frucht Free and integrated Strawberry Lab, 24 Nov 2026

Read-only audit of existing owner-private archive and integrated scene; no changes to geometry, materials, source assets or main. Visual acceptance remains FAIL. Original Frucht commercial Strawberry scene and complete skin/pit node trees are not in the free archive. No reference code, node trees, numerical presets, assets or images copied into this repository.

## Reference evidence

Reopened exact `frucht-free-kiwi-0.4.3.zip` SHA256 `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877`. `fruechte.py:24–41` defines a commercial `erdbeere.blend` which is absent from the archive. Evidence levels below distinguish executable source, references to absent groups, and author-supplied node descriptions.

- **Executable anchor placement:** `form.py:164–223`. One shared point mesh is used for both achene/pit placement and the form distribution object. The default count is 470, configurable via a factor; placement samples a radius profile by cumulative surface-area proxy (radius times meridional arc length), with a golden-angle azimuth and calculated surface normals. This is not a direct area integral of every deformed, non-axisymmetric final fruit, nor a biological count. Actual commercial scene count not verified.
- **Pit and contact coupling:** `form.py:21–30,69–123` updates distinct depth, width, variation and crown-specific pit inputs in named groups. `ordnen_texte.py:89–96,155–160` documents skin conforming to real seed bodies, seed seat testing, common shoulder mask for smaller seeds and pits, hair exclusion in pits, and fine short hairs plus crown fluff. These descriptions and parameter references do NOT establish the missing exact pit shape, contact solver or full GN wiring. `anlegen.py:123–190,268–295` directly implements smoothed surface-normal sampling and alignment of seed instances. That code changes instance rotation, not translation or seed-solid intersection resolution.
- **Executable macro form:** `formen.py:102–190,652–679,730–749` builds a common forward map with shoulder, longitudinal redistribution, elliptical/wedge cross sections, twist, lobes, local dents, skew/bend and stalk protection; it also has an inverse-coordinate attribute path. `form.py:33–52,967–1001` defines 11 shape classes and seeded, bounded variation. `aufloesung.py:42–71` implements a cube-to-sphere surface generator; `fruechte.py:280–289` configures its resolution. Exact reference silhouette still depends on the absent commercial curve/template.
- **Skin optics:** `ordnen_texte.py:137–145,171–185` documents fine pigment speckles, normal-only microrelief, irregular gloss traces, separate dry crown, suppressed gloss in pit centres, grazing-angle fade, and subsurface scattering. `form.py:368–410` actually wires independently adjustable scattering weight and scale multipliers; `reissbrett.py:200–212` actually adjusts skin hue on whole/cut materials. Complete original material nodes not available; do not infer exact frequencies, amplitudes or physically calibrated values.

## Our current source and evaluated scene

Read `src/strawberry_generator/README.md`, `generate.py`, `recipe.py`, `sdf/build.py` on accepted main. Own generator already has a real compact pit field, area-stratified scatter, geometric seed seating and nonlinear common profile. It is not merely a textured sphere. Fixed count 264, existing recipe rejects other counts. Current profile is a Gaussian radial warp plus height scaling. Increasing count without rebuilding seed IDs, pits, ring vascular field and atlas invalidates current anchor correspondence.

Reopened `integrated.blend` (SHA256 `790dc4adbd9025b56e7833c2cedb8ada83c0e9b738ac294f96889fbb52e0e215`), Blender 5.2.4 LTS `cd5dc428cce1`, autoexec disabled. `audit_exterior.py` changes mode and voxel properties only in process, never saves the scene. Uses the existing forward profile map and Jacobian-transformed rest normals. At each of the 264 anchors, casts a ray along that direction toward the surface; signed depth is relative to transformed nominal anchor, not a complete geometric pit cross-section. Closed raw seed triangles are compared with raw/evaluated body via BVH overlap. All 264 seeds have reported overlaps in every state. Overlap alone is not proof of seating quality, exact surface contact without penetration, or arbitrary-cut clipping.

| State | Median depth mm | Minimum depth mm | Body vertices | Seed BVH overlaps |
|---|---:|---:|---:|---:|
| Original pitted source | 0.176586 | 0.130055 | 47,384 | 264/264 |
| Whole SDF 0.32 mm | 0.147167 | 0.080967 | 93,370 | 264/264 |
| Whole SDF 0.20 mm | 0.167740 | 0.116654 | 239,270 | 264/264 |

The median loss is 16.7% at 0.32 mm and 5.0% at 0.20 mm. All depths positive. Body vertex counts include internal lumen in evaluated states. These are whole-fruit exterior probes, not fresh manifold, cut, juice, arbitrary-cutter, or performance acceptance at 0.20 mm. Previous integrated internal QA remains separate.

Actual source skin has 40 nodes (including inherited/disconnected inverse nodes); traced active Principled links. `achene_pit` drives recess tint and the second bump, but the roughness branch uses the fine cuticle noise and no pit mask. Roughness ramp .30–.39; Coat Weight .13 and Coat Roughness .31 are unlinked constants. SSS weight and scale also constant. The original field already contains ripening patches, shoulder tones and two bump layers. A single uniform coat contribution is a concrete difference from the reference's described spatial gloss exclusions, not proof that it alone causes the visual mismatch.

## Next bounded work

1. Preserve integrated scene byte-for-byte. First independently test a skin-only material mask from existing pit and shoulder fields: suppress coat and modulate roughness at pit centres, with small-scale variation on intervening skin; isolate one hypothesis against existing material, identical whole-fruit macro camera/light, geometry and renderer. Verify all tissue/juice/skin mesh hashes unchanged. Do not imply this is the author's exact shader.
2. Then address pit resolution with an independent A/B of source and SDF meshes using per-anchor depth, seat shape/contact, true cross sections, and controlled exterior macro renders. A pit-aware reconstruction or separate fine skin route can be compared against globally reducing voxel size; no assumption that more triangles alone fixes realism. Preserve cutter and internal state. Reevaluate fine-resolution cut cost/QA before promoting.
3. Only after that, test macro silhouette variation via one shared transform for body, achenes, rest coordinates, vascular paths and lumen. Do not increase seed count or introduce new shape families until recipe and atlas contracts are regenerated together. Missing scientific dimensions and visual parameters remain ARTIST.

The checked original source/pinned scene and aggregate report are sufficient to reproduce this audit. No new render or visual improvement is claimed here.

```sh
/path/to/blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python audit_exterior.py -- /path/to/integrated.blend /path/to/fresh-exterior-qa.json
```
