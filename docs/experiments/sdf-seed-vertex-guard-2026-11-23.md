# Strawberry SDF — native achene vertex intersection guard (23 Nov 2026)

**Scope:** one verified source change on the [PR #47 merged technical SDF baseline](https://github.com/Dmitry-dev-pet/strawberry-lab/pull/47) at `61b403eb1fbdc2cff72afdaf95504f4fe7e46b17`. This is a **research / corrective PR**, not an accepted Frucht-look generator. No changes to the organic hull, cutters, underlying SDF Boolean, tissue atlas, materials, original achene meshes, source recipes, or license status.

## Bug reproduced on the previous baseline

The old `SDF | same-cutter CENTER mask` tested only a whole object's mean position against the moving plane/sphere. A retained seed could visibly cross into the removed volume:
- Centre plane, voxel 0.20 mm: **135** evaluated achene vertices inside discarded half-space.
- Oblique plane, 0.20 mm: **233**.
- Default sphere: **74**.
- An artist edge-intersecting bite at location `(0.82,-0.70,-0.42)`, uniform scale `1.04` (Blender model units, not mm): **165** inside its sphere; 207 visible achenes.

Source scene: [owner-private PR47 editable scene](https://drive.google.com/file/d/1AI7HKnSo0_VBLCWZl-a6vIgMc5swZUhF/view) SHA-256 `c27ebc88e17e5172c80b3d4dbc3882a78be690fcc7a8f0af68d697d18addbc4f`.

## Hypothesis and bounded change

Within the **same native Geometry Nodes modifier**, compute the `GeometryNodeAttributeStatistic` minimum of **every original seed vertex** relative to the shared cutter:
- Plane: minimum local Y of seed vertices after inverse rotation; hide entire seed if any vertex falls behind the plane.
- Uniform sphere: minimum per-vertex distance from cutter origin; hide entire seed if any sampled vertex is within radius.
- Whole: retain 264/264 source seeds; no script executed on reopening or moving cutter.

The cut body still uses `Mesh → SDF Grid → SDF difference → Grid to Mesh`. This is conservative **whole-object removal**, not true partial achene/calyx mesh clipping or proof that triangles spanning the surface have no intersections. The previous centre-mask assertions were **replaced with independent Python checks of every source vertex and every retained evaluated vertex** rather than simply weakening the old test. Render materials, scientific numbers and atlas remain `ARTIST` or template-derived where previously marked.

## Original Blender 5.2.4 verification

Rebuilt from independently SHA-pinned PR40 `seed101.blend` in a fresh Linux Blender 5.2.4 LTS process; tested saved-scene reopening with `--disable-autoexec`.
- **112/112** pure Python tests PASS.
- **5/5** Blender saved SDF contract tests PASS (adds group Min-vs-Mean wiring).
- **8/8** full native SDF QA states PASS at 0.32/0.20 mm (whole, plane, oblique, sphere): one connected closed body, 0 nonmanifold edges, 0 zero-area render triangles, positive volume; 264/264 whole-seed contacts remain. Existing rest-space/packed-atlas checks pass.
- New seed counts at both voxel sizes: **264 whole, 130 centre plane, 114 oblique, 232 default sphere**. Independent Python whole-vertex guard agrees and reports **0 retained seed vertices inside cutters** at all tested non-whole poses.
- New base scene SHA-256 `bfecf691df67cafff020971368f1afc877f4bac1165e851520bdcc1773f85ce1`; native QA receipt `c3ce0d6cf7e334f48069fd7f897b9fb39e9a77294d814442c01c63ec0d2b70ec`.
- New side-edge cutter scene SHA-256 `ab22ec9c7b7f6d887f08113eff21cf6e8060608d35df4c10eac46e07d5486e54`: **202** retained seeds, **0** evaluated vertices inside sphere, body **233,234 vertices**, 0 nonmanifold edges; body geometry unchanged from the same pose using old centre mask. New scene and Cycles 640×640 /16 samples re-rendered.
- Fixed camera/light and Cycles seed 1729. Pixel difference in A/B side-edge images is only **0.208%** at RGB channel delta >2/255 (image alteration, **not an image-quality score**).

## Durable private artifacts and provenance

[Drive / Strawberry Lab / pr48-sdf-seed-guard-2026-11-23](https://drive.google.com/drive/folders/1kP4wbsqjXW0zOvISaCUB4EUTlmer4SUC):
- [Full evidence ZIP](https://drive.google.com/file/d/1pzeFM39rscGbobfebnLEtsZIWMdqb8I1/view) `6fc4a194390320c187624692496a23622eec540339495c2202c8671d9a3591d1`.
- [Editable base .blend](https://drive.google.com/file/d/1gBhr4NA5AB6UK_IHILfepU5t4O_iFQgU/view) `bfecf691df67cafff020971368f1afc877f4bac1165e851520bdcc1773f85ce1`.
- [Editable edge-pose .blend](https://drive.google.com/file/d/1oVGWL6Dv-FEc9rnZuTTrprt0MGsExkB1/view) `ab22ec9c7b7f6d887f08113eff21cf6e8060608d35df4c10eac46e07d5486e54`.
- [A/B contact sheet](https://drive.google.com/file/d/17z9lXO3KQEU3KfMH4tT129fvGZNJqErG/view) `40d2b23874ced638d6952a50fa51d548645e72ae82aad3f906b48f4627ad11d5`.
- [SHA manifest](https://drive.google.com/file/d/1MTWqJBYLuxnKAuuqZ8kGnPdgfKaFxyqH/view) `94e8552514bf1acabcd1ee4216b63ba963abe16a3fccd9e199c361143a21bc2f`.

Google Drive returned all five files, and **5/5 full downloaded SHA-256 readbacks matched locally**. The folder is private. Exact Python source files are also stored there and in this PR; Git blob SHAs of those files match the locally executed source.

## Remaining limitations

This fixes the measured **vertex intrusion bug for the tested poses**, but not all possible triangle intersections, seeds crossing a nonuniform/non-spherical cutter, physical partial slicing of a seed, or independent calyx/stem correctness. The edge cut is closer in silhouette category to the author's open missing volume, yet its surface remains overly smooth, waxy and unfibrous; **visual acceptance FAIL**. The v20/v21 core/halo/cell-outline lookdev is **not** transferred into this scene, and its similarly named material node sockets have different meanings. Do not blindly transplant the v21 `Math.039` value.

**Merge gate:** keep this change as a reviewable separate PR; owner review + continued visual A/B needed before another merge into `main`.
