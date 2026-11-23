# Independent saved-scene pose validation

`validate_saved_pose.py` does not rebuild, repair, filter, save, or otherwise
change the input `.blend`. It opens that file with script execution disabled,
applies one documented in-memory cutter pose, evaluates the real Blender mesh,
and writes an engineering report. Use Blender 5.2.4 for the v19 comparison.

```bash
BLENDER=/absolute/path/to/blender
"$BLENDER" --background --factory-startup --disable-autoexec \
  --python-exit-code 1 --python validate_saved_pose.py -- \
  --scene /absolute/input.blend --pose plane --output /absolute/plane-qa.json \
  --surface-distance
```

A successful script run may have **exit code 2**: that means evaluation and
report writing completed but at least one engineering gate failed. Inspect
the JSON `status`, `checks`, and individual measurements. Errors before a
report is written are incomplete validation, never a pass.

## Poses

| CLI pose | Frame | Change from the saved pose, after setting its frame |
| --- | ---: | --- |
| `whole` | 1 | None |
| `plane` | 20 | None |
| `bite` | 40 | None |
| `plane_moved` | 20 | Plane world-independent object location Y +3 BU, Euler X +0.1745329252 rad; matches v19 |
| `bite_moved` | 40 | Sphere object location X −4 BU, scale ×1.13; matches v19 |
| `plane_rotated` | 20 | Plane Euler Y +20°, Z +30°; additional ARTIST test pose |

The saved original and tested world matrices are included. Parent transforms
would change the interpretation of object-local translation; these descriptions
therefore do not silently call the object offsets world-space offsets.

## Strict gates

The evaluated body must have one component, no nonmanifold edges or vertices,
consistent winding, positive signed volume, finite coordinates, and **every
actual loop triangle at least 1e−10 mm²**. The threshold is not reduced to
make a candidate pass. All component sizes and bounds are retained, including
very small islands. Unlike the previous validator, the minimum is a triangle
area, not a polygon area.

Scene scale is used to transform every evaluated coordinate to millimetres;
the expected physical scale is 1 BU = 1 mm. A non-unit object transform is
included in area and volume calculations. Cut poses must retain finite
`fruit_rest` and `v8_vascular_intensity` attributes by default. Repeat
`--required-attribute NAME` to supply the exact contract of a newer scene.
No v19 variant property or v19 control name is required.

The source `.blend`, raw source-body vertices, evaluated mesh and packed atlas
are hashed. Atlas R and GBA float arrays have separate SHA-256 digests, compatible
with v19's recorded NumPy hashing. Individual R/G/B/A and combined BA hashes
are also recorded for a split core/halo experiment. Optional
`--expect-scene-sha256`, `--expect-R-sha256`, `--expect-GBA-sha256`, and
`--expect-BA-sha256` add comparison gates.
Default atlas discovery selects the existing 3072×2304 atlas. For a different
atlas layout, pass its exact name with `--atlas-name` rather than silently
accepting no image.

## Material diagnostic

`--surface-distance` queries every evaluated triangle centroid against the
evaluated body's original raw source mesh, transformed into the same object
frame in world millimetres. The separate whole-display object is deliberately
not used because its presentation transform can differ from the cut body's.
The table
includes the **actual material names**, triangle counts, nearest-hull distance
range and counts farther than 0.5 mm from the original hull. It does not assume
that slot 0 or slot 2 means skin. The inward test uses the nearest triangle's
normal; it is a diagnostic approximation, not general volumetric containment.
This can reveal deep internal triangles assigned an actual skin material.

`--bulk-witness-mm X Y Z` optionally tests a chosen surviving bulk point using
three deterministic ray directions. It records all parities and rejects a
boundary-adjacent ambiguous witness. This is a numerical point-containment
check, not biological graph-root proof or universal attachment proof.

## Minimal useful comparison

1. Reopen historical v19B in `plane` and `bite` to confirm that the independent
   check detects the already known component failure. These are negative controls.
2. For the candidate, evaluate `whole`, `plane`, `bite`, `plane_moved`,
   `bite_moved`, and `plane_rotated` in fresh processes. Reuse the unchanged
   whole-body geometry hash to check accidental changes to the exterior.
3. Compare matched original Cycles plane/bite images and one macro separately.
   A connected manifold mesh alone cannot pass visual acceptance.

Elapsed time starts before file opening and includes frame/dependency-graph
updates, geometry measurement, and atlas checks. Individual phases are reported.
It excludes Blender process startup and final JSON writing, so use an external
process timer if that complete wall time is required. Two simultaneous jobs
may contend for CPU; report concurrency when using those timings.

This validator does **not** cover seed/cutter triangle intersection, calyx
cutting, field rebaking after diagnostic-curve edits, every possible cutter
pose, self-intersection, or biological realism. Use the existing seed guard
and explicit visual inspection as separate evidence when relevant.

## Independent core/halo A/B causality

`compare_halo_fields.py` exports one real saved pose per fresh Blender process,
then compares NumPy arrays outside Blender. For the first A export, supply the
original v19A scene to obtain an independent material-graph reference:

```bash
"$BLENDER" --background --factory-startup --threads 3 --disable-autoexec \
  --python-exit-code 1 --python compare_halo_fields.py -- export \
  --scene /absolute/strawberry-v20a-core-suppression.blend --pose plane \
  --npz /absolute/v20a-plane-fields.npz --report /absolute/v20a-plane-fields.json \
  --reference-scene /absolute/strawberry-v19a-graph-only.blend
```

Export B identically without `--reference-scene`, then compare:

```bash
python3 compare_halo_fields.py compare \
  /absolute/v20a-plane-fields.npz /absolute/v20b-plane-fields.npz \
  --report /absolute/v20-plane-causality.json
```

Repeat A/B export with `--pose bite`. Its comparison can reuse the reference
captured from the first export through
`--reference-report /absolute/v20a-plane-fields.json`.

The exporter observes the real final mesh, temporarily routes the group output
to the geometry feeding its final Set Position, evaluates that undisplaced mesh,
and restores the link. It never saves the source scene. Thus the base positions
and normals are measured separately from the builder's diagnostic attributes.

The comparison requires identical A/B topology, base positions/normals, rest
coordinates, core, halo, ridge and rim fields. It checks that the actual cell
amplitude control remains 1; the broader halo never increases absolute cell
height; the inherited suppression map produces the recorded values; both
variants share the same unsuppressed cell field and ridge formula; and the
measured A→B vertex displacement equals the normal times the cell-height change.
It also verifies the original packed atlas SHA, unchanged original material
graphs, and native SDF difference route with no reachable tube-union/resampling
nodes. The positional tolerance is 1e−5 mm to accommodate float32 coordinate
writeback at the approximately 48 mm scene extent; maximum errors are reported.

The result establishes field-to-geometry causality for the exported poses.
Mesh topology QA and visual acceptance remain separate checks.
