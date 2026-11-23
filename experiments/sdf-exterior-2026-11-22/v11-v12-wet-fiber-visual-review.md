# Strawberry Lab v11–v12 — directional wet cut-field lookdev (22 November 2026)

**Status: technical geometry PASS on the tested cutter poses; Frucht visual fidelity FAIL.** This is an independent bounded research continuation of [v8 + v10](owner-video-v9-v10-audit.md); it is **not** the previous v9 filled-spindle or annular-sheath experiment. Preserve all earlier scenes and do not merge these variants into `main`.

## Hypothesis and implementation

Starting from the independent editable **v10 ragged-bite SDF** scene, test whether cut-local **anisotropic 3D Voronoi microdisplacement** and a fine rest-space **wet-film normal/roughness field** make the internal tissue more naturally fibrous *without changing the cutter, achene graph, anatomical tissue atlas or fruit exterior*.

- **v11:** [Build script](build_v11_wet_fibers.py): scale cut-cell Voronoi sampling anisotropically (XYZ multiplier 1.55, 1.55, 0.48), sharpen the visible white strands with a nonlinear vascular-intensity response, and add 3D aligned material microbump + variable wet-film roughness. Original physically displaced cap (via native GN, after SDF) remains; the added film normals are shader-only.
- **v12:** [Refinement script](refine_v12_continuous_fibers.py): restore the original continuous R-channel vessel response (v11 had fragmented pale strands into isolated dots), use milder 3D cut microdisplacement anisotropy (1.24, 1.24, 0.67), and attenuate the sheen. **v12 is a derivative of v11**, not a redefinition of the older `build_v9.py` experiment.
- Both retain **the exact same packed 192³ rest-coordinate tissue image** as v10. SHA-256 of all three independently reopened image datablocks: `38c8f94099425d634d09607a46c160bbcf54ff350b94d9439a3c9868985c6317`. All anatomical parameters and the graphic fiber paths remain **ARTIST**; no specimen histology or Frucht proprietary nodes were incorporated.

## What actual Blender renders show

Matched scene, camera, lighting, Blender **5.2.2 LTS**, Cycles **860×860 / 36 samples**. Unedited original Cycles PNGs; no ImageGen. In every comparison, **v10 is LEFT** and experimental variant RIGHT:

| A/B | Owner-private original renders | Observation |
|---|---|---|
| v11 planar + bite | In the [research folder](https://drive.google.com/drive/folders/1Ylc-G_V1HftUiTOpA2EjOZtN9aHqpwI5) | Hard threshold broke continuous white strands into detached white specks and created excessively separated specular patches: visual regression |
| v12 planar | [A/B plane](https://drive.google.com/file/d/1TmaaBQFYUQnMVegc51PHna4o6FzRLG7O/view) | Restores long wispy original strands; a small local wet textural difference, not strong improvement |
| v12 scalloped spherical bite | [A/B bite](https://drive.google.com/file/d/1jRGgKnTu0zt7fqqptEl87dF-vysxqU1f/view) | Wetness somewhat softer, but still a smooth bowl of tissue; unlike actual torn strawberry flesh in Frucht |
| v12 cut macro | [A/B macro](https://drive.google.com/file/d/1r7KZ8SzYcKPYlEFiGjS3iaOKY-D5ITrb/view) | Elongated microstructure visible only at close range; source vascular strokes remain broad/blurry |

**Do not mark v11 or v12 visually accepted.** v12's minor improvement is insufficient to justify additional cosmetic shader tweaking. The current bottleneck is the underlying spatial microfibrous appearance and local torn-flesh geometry.

## Native QA from saved editable .blend

[Validator](validate_wet_fiber_variants.py) adapts existing v10 QA and independently reopens each version **with Blender script autoexecution disabled**. Tested whole, original planar, original ragged bite, translated+rotated planar, moved+scaled bite. **Each version passed all five states**: 0 nonmanifold edges, positive signed volumes, and **zero retained achene vertices inside** either cutter. Physical rather than shader-only displacement verified by disabling the native `V8_CELL_STRENGTH` field, and vessel-dependent flattening is still active.

| Evaluated state | v11 & v12 vertices | Nonmanifold edges |
|---|---:|---:|
| Whole | 157,250 | 0 |
| Planar | 194,354 | 0 |
| Ragged bite | 350,314 | 0 |
| Moved/rotated planar | 154,762 | 0 |
| Moved/enlarged ragged bite | 361,858 | 0 |

For example, v12 cut-face displacement vs zero-strength: planar **0.01847 mm max** with 55,500 vertices moving >0.005 mm; bite **0.01840 mm max**. Both are tiny local geometric changes, not 3D modeled biological cells. Routine renders took about 10–20 s per image on the observed Mac; isolated peak RAM/VRAM and glTF performance were **not measured** in this experiment.

## Reproduction and provenance

Requires independent v10 `.blend` from the previously verified [owner-private v9/v10 folder](https://drive.google.com/drive/folders/15JLM2-bMdsNnjOhxKGeD31eUVBPq3sNx), placed in `build/sdf-vertical-slice/`. From the project root:

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/build_v11_wet_fibers.py
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/refine_v12_continuous_fibers.py
STRAWBERRY_QA_VARIANT=v11 $B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/validate_wet_fiber_variants.py
STRAWBERRY_QA_VARIANT=v12 $B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/validate_wet_fiber_variants.py
$B -b build/sdf-vertical-slice/strawberry-sdf-vertical-slice-v12-continuous-wet.blend --disable-autoexec --python experiments/sdf-exterior-2026-11-22/render_v11_v12_variant.py -- v12 bite
```

All original scenes, test receipts, reproducible scripts and 860px Cycles A/B PNGs are in the [owner-private Drive folder](https://drive.google.com/drive/folders/1Ylc-G_V1HftUiTOpA2EjOZtN9aHqpwI5), **33 files (~66 MB) with local SHA-256 readback**. Independently downloaded back through Google Drive and full SHA-256 verified: [v11 editable .blend](https://drive.google.com/file/d/1OXb5Mt_IlK4dMRuJM0v-JtNxhFlUqj3j/view) `839f5a6b493d6dfe98c09f79f68ca5a8c1ac46d16c1f4197e3ff33a345e7ffd3`, [v12 editable .blend](https://drive.google.com/file/d/1J1Zi93Ewbt0AkbYc8-e17dgydjPL7Mrw/view) `300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410cbb405b7`, [macro comparison](https://drive.google.com/file/d/1r7KZ8SzYcKPYlEFiGjS3iaOKY-D5ITrb/view) `3e1b398ad7a261da96df289db0e5a09d21930b3dbdc9c2b2416ff96525a90e8b`. Other 30 files had local hash-matched copy verification and provider list metadata, not independent byte download.

## Decision

Archive **v11 as a negative lookdev control**, v12 as an **engineering-validated but visually unaccepted** artifact. Keep v8, v9, v10 and the independently tested annular sheath; don't transfer experimental versions into `main` without human review. A next genuinely new hypothesis must target a **spatially detailed fibrous tissue field and torn exposed tissue geometry** with matched close-up shots of the owner-authorized 10s / 18s Frucht frames; avoid another isolated shader-tweak sequence.
