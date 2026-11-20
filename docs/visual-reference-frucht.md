# Visual reference: Frucht author's introductory film (2026-11-13)

**Статус: исходный видеопоток ещё не извлечён, покадровый просмотр ещё НЕ сделан.**

Source-of-truth: [Who Made the Strawberry? — original film, 0:38](https://strawberry-methodology.pages.dev/#kopfclip). The author's public page describes an intro film made with the procedural Frucht add-on. Date Nov 13, 2026 and length 0:38 are stated on the indexed original page; they are not inferred from our own downloaded file.

Our reference is a **visual target, not source code**: do not copy the Frucht model, node trees, commercial files, video or textures into public Strawberry Lab. Original footage, raw frames and contact sheets can only go into access-controlled research space with appropriate usage rights. Public GitHub may hold **text-only observations, timestamps, link to the original, our own code and our own Blender renders**.

Private storage destination: [Drive / Strawberry Lab / author-reference](https://drive.google.com/drive/folders/1uR3R1YWsUQ98FAOAXmRRaaHCs3NAwmsG).

## Procedure (once the original MP4 is actually accessible)

```bash
python3 -m pip install Pillow
python3 scripts/extract_reference_frames.py \
   /path/to/original/author-intro.mp4 \
   --out /path/to/private/author-reference/frames-1s --interval 1
# denser samples for cuts/transitions (private):
python3 scripts/extract_reference_frames.py \
   /path/to/original/author-intro.mp4 \
   --out /path/to/private/author-reference/frames-250ms --interval 0.25
```

Requires `ffmpeg` + `ffprobe` installed on the same machine. Uses the video from a local path, never pretends to download a missing source. Emits a labeled contact sheet, individual timestamped JPEG frames and `reference-manifest.json` with original SHA-256, resolution, fps and duration. **Extractor was tested on a synthetic 2-second clip (4 frames at 0.5s); not on the author's film.**

## Frame-analysis notebook schema

Record one observation per feature/shot; no invented timecodes.

| Field | Meaning |
|---|---|
| `t_start` / `t_end` | Actual seconds in verified original |
| `shot_kind` | `whole` / `macro-achene` / `skin` / `calyx` / `slice` / `internal` / `fluid` / `physics` |
| `camera` | Estimate of angle, crop, focal length perspective; mark uncertain |
| `observation` | Visible detail, not speculation about code |
| `reference_frame` | Private storage index (never public binary URL if copyright restricted) |
| `our_baseline` | Corresponding locally reproduced Blender frame using camera/lighting matched as closely as possible |
| `gap` | Evidence-backed difference |
| `change_hypothesis` | Independent algorithm/design change to test |
| `confidence` | `observed` / `inferred` / `unknown` |
| `issue` | GH issue / PR implementing and verifying |

**Seven checkpoints**: silhouette and lobe irregularity; spatial density/distribution of surface achenes; actual achene depressions and skin deformation; epidermis and subsurface sheen; calyx topology; cut-edge continuity; inner fibers connected to tissue/achene anchors. Animation: frozen pieces and realistic collisions, if those shots occur in the film.

For every feature, compare physical properties at equivalent framing, not raw pixel similarity across different lights. Keep **camera and render style** as a separate layer from **geometry, anatomy and material**, so a more cinematic shot is not mistaken for a better model.

## Frame-derived acceptance tests (pending observation)

| Metric | How measured | Target |
|---|---|---|
| Silhouette (front / 3/4) | Matched-camera outline overlay, shape ratio, asymmetry | Set *after* reference inspection |
| Achene placement | Count per visible area, neighbor distance CV, row phase, depth of pit in profile | Set *after* reference inspection |
| Achene-to-fiber anatomy | Track strand attachments on cut macro views | Set *after* reference inspection |
| Cut geometry | Compare skin and tissue seam at multiple orientations | Set *after* reference inspection |
| Skin look | Cross-polarized if available; specular/roughness subjective side-by-side | Set *after* reference inspection |
| Motion | Object motion vs camera movement; collision/interpenetration | Set *after* reference inspection |

A Reddit discussion raised legitimate-looking *hypotheses*, not independently confirmed defects: overly regular spirals, disconnected pale filaments, implausible white speckles, and physics slices falling off an edge. Do not report those as facts about the original until actual reference frames support them. [Reddit original discussion](https://www.reddit.com/r/ClaudeAI/comments/1xz0jhy/the_89_billion_token_strawberry/).

Our v0.1 binary baseline is recorded at [assets/manifest-v0.1.json](../assets/manifest-v0.1.json); it is not the author film.

## Current blocker

The page has an interactive `#kopfclip` player target but in our available read-only extracts **no stable direct MP4/WebM URL was exposed**; our runtime also cannot fetch the rendered page as a binary video source. Thus **no genuine author frames have been generated or reviewed in this task**. Do not generate fake frames and do not imply otherwise. First supply a legitimate local video file or source URL to the extractor. See [Issue #5](https://github.com/Dmitry-dev-pet/strawberry-lab/issues/5).
