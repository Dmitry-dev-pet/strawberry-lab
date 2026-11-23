# Four live display modes on the PR30 strawberry

Open `strawberry-layer-modes.blend` in Blender 5.2.2 and use the View Layer selector at the top right. The file opens in MATCHED. Use **Z → Rendered** to see the shader mask, or **F12** to render the active layer. Solid shading shows the full paths in any layer that includes diagnostics.

| View Layer | Flesh and exterior | Original diagnostic network |
| --- | --- | --- |
| WHOLE | Full body, 264 exterior achenes, 8 sepals and pedicel | Hidden |
| MATCHED | Live solid cut | 28 core splines, 539 branches and 539 markers clipped by the same knife |
| FLESH ONLY | Same live solid cut | Full network, including paths and markers beyond the cut face |
| FIBERS ONLY | Hidden | Full network |

Select **LIVE CUT | move or rotate this Empty** in **One shared knife**. Translate or rotate it in either cut layer. Its local positive Y side remains. WHOLE uses two native constraints to park the evaluated knife at Y = −1.6 model units (−35.56 mm), with zero rotation. The editable transform retains the current cut and takes effect again when switching back. FIBERS ONLY leaves the knife transform alone and hides the solid collections. The starting cut is Y = −0.10 model units (−2.22 mm) and Z rotation = −23°.

The View Layers work with scripts disabled. To add the optional panel, open **Scripting**, select **LAYER_MODES_CONTROLS__RUN.py** in the Text Editor, and click **Run Script**. In the 3D View open **N → Strawberry Layers**. The panel switches the native View Layer and exposes the shared knife’s Y, X rotation and Z rotation. The nested Markers collection checkbox controls diagnostic markers independently in each layer. The file also carries the **START HERE | Strawberry layer modes.txt** guide.

**539 diagnostic anchors ≠ 264 exterior achenes.** The original diagnostic geometry and its alignment to the body stay as authored. A View Layer scalar gates the existing knife-space transparency mask on the same three diagnostic objects. Flesh can occlude the retained network in MATCHED. Diagnostic clipping is display-only and exported paths retain their full geometry. PR30’s skin pits remain shader relief. The scene uses the original packed atlas and the PR30 scale of 48 mm for the 2.16-unit source hull. [Blender Attribute node documentation](https://docs.blender.org/manual/en/latest/render/shader_nodes/input/attribute.html)

## Reproduce

Run from the repository root with the two authenticated owner-provided inputs. Each command uses Blender's stock installation. Integer RGB pixel validation and the montage command also use ImageMagick.

| Input | SHA-256 |
| --- | --- |
| `build/inputs/pr30-corrected.blend` | `0b8af93c399d0077f51f864f7b9f55673b822a1755e2badcc626f5bfc6256bca` |
| `build/inputs/pr29-original.blend` | `56b6d516e8794fb855512978e90e37cd754374a594fb4c5103e672c960a031cf` |

```bash
BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
EXPERIMENT=experiments/integration-layer-modes-v1
OUT=build/layer-modes-v1
SCENE="$OUT/strawberry-layer-modes.blend"
export PYTHONDONTWRITEBYTECODE=1

"$BLENDER" -b --factory-startup -t 4 --python-exit-code 1 \
  --python "$EXPERIMENT/build_layer_modes.py" -- \
  --source build/inputs/pr30-corrected.blend --out "$OUT"
"$BLENDER" -b --factory-startup -t 4 --python-exit-code 1 \
  --python "$EXPERIMENT/validate_layer_modes.py" -- \
  --pr29 build/inputs/pr29-original.blend --pr30 build/inputs/pr30-corrected.blend \
  --scene "$SCENE" --out "$OUT/validation.json"
"$BLENDER" -b --factory-startup "$SCENE" -t 4 --python-exit-code 1 \
  --python "$EXPERIMENT/render_layer_modes.py" -- --out "$OUT/renders"
"$BLENDER" -b --factory-startup "$SCENE" -t 4 --python-exit-code 1 \
  --python "$EXPERIMENT/validate_renders.py" -- \
  --renders "$OUT/renders" --out "$OUT/render-validation.json"

magick montage -font /System/Library/Fonts/Supplemental/Arial.ttf -pointsize 23 \
  -fill '#e5e7eb' -background '#171c22' \
  -label WHOLE "$OUT/renders/whole.png" -label MATCHED "$OUT/renders/matched.png" \
  -label 'FLESH ONLY' "$OUT/renders/flesh-only.png" \
  -label 'FIBERS ONLY' "$OUT/renders/fibers-only.png" \
  -tile 2x2 -geometry 500x500+12+12 "$OUT/montage.png"
```

Use a fresh `OUT` per build. The renderer also accepts `--mode whole`, `matched`, `flesh-only` or `fibers-only` for an individual PNG and receipt. Render validation expects the complete set.

## Measured checks

The Blender 5.2.2 run saved one 5,041,033-byte scene in 1.49 s. It retained the PR30 inventory of 284 objects, including one 30,242-vertex body, one knife Empty and its one subtraction mesh, one camera and three lights. `validation.json` records source geometry digests, the unchanged cap graph, exact MATCHED/FLESH ONLY evaluated mesh equality and the embedded script’s registration and layer-switch tests after opening the scene with scripts disabled.

| Y offset, X and Z rotation | Evaluated body faces | Retained achenes / sepals / pedicel | Update and topology check |
| --- | ---: | ---: | ---: |
| −1.60, 0°, 0° | 30,400 | 264 / 8 / 1 | 0.665 s |
| −0.10, 0°, −23° | 17,826 | 148 / 8 / 1 | 0.713 s |
| 0, 0°, 0° | 15,201 | 135 / 6 / 1 | 0.714 s |
| −0.26, 0°, 0° | 21,388 | 174 / 8 / 1 | 0.711 s |
| +0.08, 29°, 32° | 12,344 | 127 / 8 / 1 | 0.716 s |

The evaluated body and every retained exterior solid were closed and had positive signed volume in all five poses. The largest body cap-plane error was 1.15 × 10⁻⁷ model units. The body and crown use Manifold. Achenes use Exact.

| View Layer | Cycles CPU render, 650 × 650, 16 samples, 4 threads |
| --- | ---: |
| WHOLE | 12.405 s |
| MATCHED | 12.879 s |
| FLESH ONLY | 12.689 s |
| FIBERS ONLY | 11.885 s |

At the shared cut pose, 19.9% of pixels differed by more than 15 RGB levels in at least one channel. FLESH ONLY restored 15,023 diagnostic pixels over the MATCHED backdrop. Rendering MATCHED again after the other layers produced identical decoded pixels. The pixel validator also rendered the isolated MATCHED diagnostics at two knife poses and confirmed that moving the knife changed the mask. These timings come from headless renders and evaluated topology checks.

## Independent review

Astra independently reopened the saved scene without scripts, rendered all four active layers through the default operator and matched their PNG pixels. It verified whole-mode parking/restoration of an independently edited knife transform, retained source edits across mode switches, identical MATCHED/FLESH ONLY solids and hidden solids in FIBERS ONLY. Parent corrected integer RGB threshold accounting; the scene and PNG bytes are unchanged. The Stage B inventory probe now verifies three input hashes before opening and creates a fresh output directory; swapped originals are rejected.

## Private delivery

[Owner-private scene, four renders, montage and macro comparison](https://drive.google.com/drive/folders/11lQeYVO13TbYgVPWUVHpCQhe7czpo0jY). Use **layer-modes-reproducible-reviewed.zip** and **render-validation-final.json**; earlier archive and pixel-count report are retained unchanged but superseded. Public manifest records canonical IDs, sizes and full download SHA256 checks. The downloaded scene was reopened and passed native layer/UI/geometry validation. No GUI scene was changed.

Stage B is deliberately **not enabled**. See [verified M1e5/M1e6 source inventory and adapter contract](../m1e5-integration-assessment/README.md). The provided macro A/B compares layer visibility only, not an Exact-relief improvement.
