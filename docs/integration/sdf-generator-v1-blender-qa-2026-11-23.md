# PR #47 — Independent native Blender SDF verification (23 Nov 2026)

**Result: engineering PASS for tested poses, visual acceptance FAIL.** This report documents a new in-chat native Blender run from exact PR47 code, not legacy PR42 receipts. No `main` merge.

## Environment and sources

- Blender **5.2.4 LTS** (`cd5dc428cce1`), CPU/headless, launched on Linux x86_64.
- Official Blender archive rebuilt from all **17** parts in owner-restricted [Drive folder](https://drive.google.com/drive/folders/1LuHr6wXiNMy-3BQ_lVTzIKsqM2T3T7Io). Every part and full 385,047,680-byte archive passed SHA256: `2fd14c50987426897ba60237ee996edf2b4151f4b1a72a460ca20be58c1d2d86`. No Mac runner was required.
- PR40 owner-private original [seed101 scene](https://drive.google.com/file/d/1mYrvao6nCSIbFguFCbhFgCyUjAl7IVgg/view) SHA256: `156908ee46fd6be4cb7624d63d3f668f772abab2323d8c65ba3619dc45f63017`.
- Local script blobs were verified against PR47 exact Git blobs: `sdf/build.py` `e6759ef06861f938a8af977d8f06f20422e44c62`; `sdf/test_contract.py` `8153065855444d1873f53c194a0beca17c1267a3`; `sdf/qa.py` `036f1d67470c93de3aaaa1392186361b3e58d8c8`; `sdf/qa_inputs.py` `37b87d0651f95c99bb5650a86381b50eb734f876`; `sdf/render.py` `1e5079c8989c99bcc3d0263de323a85557cacdfc`.
- Newly built editable `.blend` from PR47 `sdf/build.py`: SHA256 `c27ebc88e17e5172c80b3d4dbc3882a78be690fcc7a8f0af68d697d18addbc4f`, Blender build elapsed **2.32s**, max RSS ~538 MB.

## Independent test results

1. Reopen original scene with `--disable-autoexec` and run SDF contract: **4/4 PASS**.
2. Reopen newly rebuilt scene likewise: **4/4 PASS**.
3. Execute full `sdf/qa.py --source <pinned PR40 input>`: **PASS_NATIVE_SDF_TESTED_STATES**; final JSON receipt SHA256 `ca7af48ef51ed878629d2457d45e1d1804b9d75e06368f0c201885a8998dd8e6`. Wall time 80.72s, peak RSS ~1.193GB, with CPU process and scene data included.
4. Independent Python tests: `PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -q` **112/112 PASS**.

| SDF voxel (mm) | State | Body vertices | Visible achenes | Evaluated body time (s) |
|---|---|---:|---:|---:|
| 0.32 | whole | 91,046 | 264 | 1.97 |
| 0.32 | plane-center | 59,400 | 133 | 3.54 |
| 0.32 | plane-oblique | 65,888 | 118 | 3.99 |
| 0.32 | sphere | 90,964 | 233 | 2.59 |
| 0.20 | whole | 233,258 | 264 | 2.93 |
| 0.20 | plane-center | 152,500 | 133 | 6.25 |
| 0.20 | plane-oblique | 168,948 | 118 | 7.90 |
| 0.20 | sphere | 233,204 | 233 | 4.62 |

All eight evaluated bodies were **one connected component, zero nonmanifold edges, zero zero-length edges, zero zero-area render triangles, positive signed volume**. Exact source geometry and packed tissue atlas were preserved. At fine whole, 264/264 real achene meshes intersected the evaluated hull (52–84 triangle pairs). Native center-culling counts matched; changing the sphere location changed the evaluated mesh. Tested shader rest-position probes match inverseF; this does not prove biological authenticity.

## Four genuine Cycles frames, independent from legacy archives

`render.py` was run fresh on the new scene for `whole, plane, sphere, macro`, each at **900×900, 16 samples, seed 1729, denoised**. All four rendered successfully (approx. 16–24s Cycles per frame; actual process wall approx. 20–27s).

- `whole.png` SHA256 `8b34740ba184965bc6da08c9542a26c602c0a4c3ac24a06a6060ce197226309a`
- `plane.png` SHA256 `eba313e30b40a85879eff51119066f8d49e0d214b74d8fb32d07580fab1e7cfd`
- `sphere.png` SHA256 `f32120db315f088096215ac2e661650b264b2ff05c25e409d82be66e570e8246`
- `macro.png` SHA256 `93ac8dc2bfeac99684ce3af7a8602d0ac32a5a3507dbaa6a64b9c047b15c8df6`

**Visual FAIL**: intact skin is noticeably waxy, cut-center pith is broad and blurred, local microstructure is not convincingly wet/fibrous, and bite is a circular smooth cavity rather than rough open-sided torn tissue. The earlier PR46 v20/v21 improvements were *not* integrated into this run. This is not a new matched-angle Frucht A/B and should not be portrayed as parity.

## Artifact integrity and retention

Full local reproduction bundle (new `.blend`, 4 authentic PNGs, image receipts, QA JSON, Python/Blender logs, side-by-side sheet and SHA manifest) was packed as `pr47-sdf-blender-verified.zip` with SHA256 `bdd4c1d7f2269b874724c3a1b7533f7ac0331180431fcb065880a73a1ec30cb3` (~17.1 MB) and returned in the owner chat. **Durable owner-private Drive upload completed 23 Nov 2026; original files not overwritten.** [PR47 SDF Blender QA folder](https://drive.google.com/drive/folders/1geMz9gMgm5ze6BV8WoiPg_tADWRNx1-z). Provider metadata confirms folder and files are **not shared**. Each of the following was separately downloaded back from Drive and SHA-256 checked **4/4 byte-identical** against the local generated source:
- [Full verified ZIP](https://drive.google.com/file/d/1h67kthZVWHZuC3QNCEHnL5CYAeHF5xOg/view?usp=drivesdk), 17,085,815 bytes, SHA256 `bdd4c1d7f2269b874724c3a1b7533f7ac0331180431fcb065880a73a1ec30cb3`.
- [Editable `rebuilt-sdf.blend`](https://drive.google.com/file/d/1AI7HKnSo0_VBLCWZl-a6vIgMc5swZUhF/view?usp=drivesdk), 11,565,008 bytes, SHA256 `c27ebc88e17e5172c80b3d4dbc3882a78be690fcc7a8f0af68d697d18addbc4f`.
- [Cycles contact sheet](https://drive.google.com/file/d/1f9lqSUIM2dft7E0V4vbY2B0nSBsR6b1w/view?usp=drivesdk), 1,903,340 bytes, SHA256 `933e3be092f61e05fbc20d8d9a2a83d8864658b48902b376865fea1e89e3ca61`.
- [JSON integrity manifest](https://drive.google.com/file/d/10v7M_lFXZSBpQw8yVTsdY-SLH9O55Hyu/view?usp=drivesdk), 3,080 bytes, SHA256 `53314a2c37b0a5b05e744f1ef66d93aa0d15ec7b1bcac52c1881f9852913a036`.

The ZIP retains all four original individual Cycles PNGs, QA receipts and execution logs. The Drive readback validates bytes and visibility; it does not upgrade the visual QA verdict or expand the set of tested cutter poses.

**Decision:** Technical SDF slice is now independently reproduced from PR47 at Blender 5.2.4. Keep PR47 **Draft**: owner visual QA, arbitrary-angle/calyx/partial-achene clipping, and v20/v21 transfer remain unaccepted. Do not merge/close old PRs based on numeric geometry PASS alone.
