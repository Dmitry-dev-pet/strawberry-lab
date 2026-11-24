# Lumen protrusions and ring-relative pigment — two independent experiments

23–24 November 2026. Research continuation of Draft PR50. Both candidates are independent: the prior lumen-only scene is the input for tissue protrusions; the prior ring-only scene is the input for pigment. Neither is combined with the other. Original ARTIST geometry and optical parameters, not histological measurements. No commercial Frucht code, node trees, assets or numerical presets are copied.

## Reference clarification
The exact private Frucht Free Kiwi 0.4.3 archive was reopened (SHA256 `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877`). In `leitbuendel.py:250–298`, the 32 tissue structures start slightly outside a cavity-wall sample and taper inward over a short curved trajectory. They are one-ended wall attachments, not fibers spanning the complete lumen. This confirms the intended source geometry in the accessible fragment, not the complete commercial scene's evaluated behavior. The third atlas channel represents ring-relative radial position in `leitbuendel.py:131–142`. The complete commercial flesh shader is unavailable. Our pigment palette and transfer functions are independent hypotheses.

## A/B: tissue protrusions
Source `lumen-B.blend` SHA256 `ccd9d4b5e93d000bdaee27a83afa95581fe19a69533493a0f96ce12917574b45`. Build 18 sparse attachments by raycasting from the axis to the actual lumen mesh, reject crowded roots, embed roots in tissue, generate tapered closed swept solids. The 18 source solids have 3,456 vertices and total source volume 13.695 mm³, including buried roots. The effective lumen is the original lumen SDF **minus** protrusion solids; tissue is cut by that effective lumen before the editable user cutter. Four added native nodes, including a grid-to-mesh output for classification of the true inner wall. The source wall material is unchanged. No loose visible tube objects are joined to the fruit. An initial saved candidate had two links into the multi-input Grid 2 socket of the tissue difference, so the original lumen unioned with the modified one and all protrusions disappeared. The initial diagnostic correctly failed (0/18 midline probes, exact baseline geometry). Fixed by explicitly removing all obsolete Grid 2 links before connecting the sole effective cavity; retained failure logs and rejected-build receipt. A preceding source-build Vector/NumPy error was also corrected.

Independent saved-scene evaluations (scripts disabled) at 0.32 mm: whole, longitudinal plane, side bite. All three have zero nonmanifold and inconsistent orientation edges, zero degenerate triangles, exactly one positive-volume body component, no liquid on whole, juice boundary tests pass and wall excluded from cap interior. Whole exterior coordinate set exactly equals the prior lumen scene. Internal negative boundary volume changes from -102.67119 to -98.36586 mm³; retained tissue volume approximately 4.30533 mm³. 17 of 18 sampled points (60% of each anchor-to-tip path) are inside tissue based on nearest oriented inner-wall normal; one is not. This is not exhaustive per-protrusion survival or continuity proof. Plane opens the cavity (one connected boundary, 4,096 wall faces). Bite misses cavity (two boundary components, one negative). Fine voxel, arbitrary poses, self-intersection and seed/calyx QA remain untested here.

## A/B: ring-relative pigment
Source `ring-B.blend` SHA256 `0498a4bb9daf0fbdb15630a052539283e89f117bbe074c2b8762868ba0deb1b0`. Independent prior field NPZ SHA256 `65cdd1b27fa6569ced1da7dde1c10f921f9933a1aadee963c7cc6c73330e193f`. Extend the existing native trilinear R/G sampler to also interpolate blue from the same two slice samples and existing z weights. Store `sl_ring_relative` on the same point geometry, prior to cell displacement. No new atlas. Eighteen added cap shader nodes, only outgoing link to old Base Color. A soft ring-relative transition blends warm inner tissue and red outer tissue with the actual suppressed cell-dome field and restrained R/H tints. Existing atlas contributes 20% to preserve context. The material has A/B gain, and geometry is unchanged. No unmeasured color value is called botanical fact.

Independent saved-scene QA: all 3 states at 0.32 mm (whole, plane, bite) match prior ring-B body coordinate and triangle topology SHA and juice receipt exactly. 512 sampled cap positions in each cut match independent NumPy trilinear values for B, max error 3.387e-6 (plane), 3.047e-6 (bite). Plane ring-relative range 0.11435–1; 26.10% of cap vertices lie inside nominal ring. No fresh fine-resolution, exhaustive self-intersection or separate seed regression. Only designated cap color input is driven by new shader nodes; no fresh complete inventory comparison is claimed.

## Visual comparison and decision
Two fresh 480² CPU Cycles renders, 8 samples, seed 1729, fixed camera, gain and voxel settings. Compared each candidate against its own archived SHA-verified previous plane render (not rerendered); `compare.py` verifies matching receipts. Ring pigment changes 28.4123% of pixels >2/255; lumen protrusions 0.4288%. These are image differences, not fidelity scores. New ring color looks overly salmon and has a conspicuously bounded pale central band; no convincing new realism. The small protrusions are visible but appear rounded and sparse, and one probe fails at coarse voxel. Technical research gates passed for sampled cases; **visual target not accepted**. Do not merge these experiments or claim a combined scene. No main mutation.

## Reproduction
Blender 5.2.4 LTS, hash cd5dc428cce1, 4 CPU threads, autoexec disabled. Use exact private input scenes/field from prior ring-lumen experiment and exact earlier QA helpers. Set `R` to an absolute directory containing `ring-lab`, `lumen-lab`, `juice-lab`, `vascular-lab`, `optical-lab` populated from the previous PR50 source and artifacts; `L` is this experiment directory. Use fresh output paths.

```
B=/absolute/path/to/blender
R=/absolute/path/to/ROOT
L=/absolute/path/to/this-experiment
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/build_lumen_protrusions.py" -- "$R/lumen-lab/lumen-B.blend" "$L/lumen-protrusions.blend"
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/build_ring_pigment.py" -- "$R/ring-lab/ring-B.blend" "$L/ring-pigment.blend"
for pose in whole plane bite; do
  $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/qa_lumen_protrusions.py" -- "$R/lumen-lab/lumen-B.blend" "$L/lumen-protrusions.blend" "$pose" "$R" "$L/lumen-qa-$pose.json"
  $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/qa_ring_pigment.py" -- "$L/ring-pigment.blend" "$R/ring-lab/qa-$pose.json" "$R/ring-lab/ring-field.npz" "$pose" "$R" "$L/pigment-qa-$pose.json"
done
for candidate in ring-pigment lumen-protrusions; do
  $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$R/optical-lab/render_optical.py" -- "$L/$candidate.blend" "$R/juice-lab/qa_juice_surface.py" plane B "$L/$candidate-plane.png"
done
python "$L/compare.py" "$R" "$L"
```
Saved scene hashes can vary with serialization path; numerical and visual evidence is tied to the saved artifacts. Private scenes and PNGs are stored on owner Drive. Public GitHub contains original source and compact evidence, not author material.
