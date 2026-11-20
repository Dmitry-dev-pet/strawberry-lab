# Whole strawberry exterior v1

First visual-first implementation under the owner-approved OpenAI T3 workflow. Generated locally in Blender 5.2.2 LTS from independent source. This version does not replace frozen M1/M2 artifacts and has not been accepted by the owner as the final look.

## Output and limits

One whole fruit with artist-designed asymmetric silhouette, geometric seed depressions, 264 seated oval achenes sharing five meshes, eight curled sepals and a curved stem. Nominal body extents are 48 × 32.5 mm, referenced to Ariza 2011 Table 2 rows R0015/R0016 in the existing repository registry. Achene count, dimensions, distribution, pit depth, calyx, colour and silhouette are artist parameters, not measured specimen anatomy. No Frucht source, node trees or textures were imported. Internal anatomy and arbitrary cuts are outside this change.

Actual saved scene bounds: 32.49997 × 29.95192 × 48.0 mm in local coordinates; 1 Blender unit represents 1 mm. Body has 157,250 vertices. Cycles output is 900 × 900 at 28 samples, deterministic seed 1729. The shoulder still looks waxy under the softboxes and the achene distribution has visible diagonals; photorealistic parity with Frucht is not established.

## Reproduce

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
/Applications/Blender.app/Contents/MacOS/Blender -b -t 6 --python-exit-code 1 \
  --python src/build_strawberry_exterior.py -- \
  --out build/exterior-v1 --resolution 900 --samples 28 --seed 1729
/Applications/Blender.app/Contents/MacOS/Blender -b \
  build/exterior-v1/strawberry-exterior.blend --python-exit-code 1 \
  --python src/validate_strawberry_exterior.py
```

Implementation run and parent verification: 81 Python tests pass. Saved scene validator reports closed body, eight closed evaluated sepals, closed pedicel and skin contact for every achene. A separate no-render rebuild with the same seed reproduced the body and achene-transform digest `9485877dc83f20690621c675e536fe58218c41f3ac16e0ca7b66b7613d03bfe1`. Validation checks technical geometry and does not assert biological or aesthetic accuracy.

## Evidence state

Local working scene, PNG and logs are in build/exterior-v1/. [Local evidence manifest](../assets/manifest-exterior-v1-local.json) records hashes and sizes; it is not a download link or a canonical Drive release. Generated binaries have not yet been archived to Drive. Independent Astra review and owner visual assessment are separate from implementation completion; see Beads straw-k43.3 and straw-k43.4 for live status.
