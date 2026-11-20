# How Frucht evolved from Strawberry into a multi-fruit Blender add-on

**Evidence-backed architectural reconstruction, 20 Nov 2026.** This is an analysis of the authentic **Frucht Free Kiwi 0.4.3** Python archive / `kiwi.blend` and the author's [Who Made the Strawberry? case study](https://strawberry-methodology.pages.dev/), **not** access to the paid strawberry `.blend` or the complete history of every commit.

## 1. What is directly verified in the free source

- **Fruit registry and adapters:** `fruechte.py` defines a single class `Frucht` and six fruit descriptors: `ERDBEERE` (strawberry), `KIWI`, `BANANE`, `ANANAS`, `GRANATAPFEL` and `KIRSCHE` (cherry). Each specifies `paket` = different per-fruit `.blend` file, controls, `form_eingaenge`, `form_felder`, named object and group aliases, cut/spawn/partition parameter dictionaries, node-resolution targets and per-fruit attributes.
- **Free vs full gating:** `edition.py` explicitly sets `FRUECHTE = ('KIWI',)`. `neu.py` lists the six main kinds as `FERTIG` and a separate `IN_ARBEIT` list for banana, pineapple, pomegranate and cherry. In free distribution `daten/kiwi.blend` is the **only** Blender fruit source, even though common Python code still has many other fruit recipes/branches. Thus the code reveals the architecture and some strawberry-specific algorithms without supplying the full paid strawberry Geometry Nodes tree.
- **Common runtime and life cycle:** `api.py` exports functions such as `create(fruit='strawberry')`, `set_form`, `set_mode`, `cut_add`, `cut_move`, `split`, `spawn_copy`, `physics`, `look`. Generic `neu.erzeugen(frucht)` invokes `fruechte.setze(fruechte.ALLE[frucht])`, retrieves the matching `f.paket` and loads collections, node groups and worlds through `bpy.data.libraries.load(paket, link=False)`.
- **Implementation mechanism of dispatch:** `fruechte.setze(f)` writes the chosen fruit's name/configuration aliases into module variables used by `fast`, `schnitte`, `teile`, `spawn`, `form` and `jobs`; updates each module's parameter `P` dictionary. `fruechte.mit(f)` temporarily switches the active fruit within a context manager. This is a functional adaptation layer but relies on **mutable global module state**; Strawberry Lab should prefer an explicit immutable `FruitContext`/dependency injection to avoid multi-fruit concurrency bugs.
- **Special cases remain:** `neu.erzeugen` explicitly branches on `if F.key == 'ERDBEERE'` to assemble strawberry seed dispersal, surface edges, vessels and cavity. `formen.py` contains extensive strawberry-specific mathematical shape code; `leitbuendel.py` and `zellen.py` supply dedicated operations. The free Kiwi `.blend` has its own dedicated groups `KIWI • Frucht komplett`, `KIWI • Gewebe`, `KIWI • Zellen am Schnitt`, `KIWI • Leitbündel`, `KIWI • Samen`, `KIWI • Griffel und Kelch`; it is **not** an instantiation of the strawberry node graph with different numbers.
- **More differences:** `schnitte.py` and `fast.py` share cut/live-preview logic but have species-specific branches and explicit capabilities, including Kiwi-specific cut planes. The generic API docstring says real Kiwi cell geometry is available for one planar cut and bites are only in fast quality; interface compatibility does **not** mean identical feature parity across fruits.
- **Node evidence:** audited free Kiwi `.blend` contains 17 stored GN groups / 2,290 GN nodes and 5 shader groups / 760 nodes. Strawberry M1d has only 3 GN groups / 41 grouped nodes (not comparable performance metrics because M1d relies on Python-generated shapes and ungrouped materials). See [independent node group audit](kiwi-architecture-audit.md).

## 2. What is directly documented about the creation chronology

The author's [methodology/case study](https://strawberry-methodology.pages.dev/) reports:
- **Nov 5 at 10:19–10:47** — discussion of two buttons (create strawberry / randomize), lazy inside computation and user decision at ~10:24 to turn scripts into a Blender add-on. The user and agent considered off/fast/exact cut computation.
- **Nov 6 at 15:06** — the user requested a *short manifesto/recipe for how an agent builds a new fruit*. An agent wrote an **approximately 90-line checklist**.
- **Nov 6 from 15:57** — fresh agent sessions followed that checklist for cherry, pineapple and pomegranate. The user inspected screenshots and requested improvements. The same study says strawberry project sessions also included integration of **Kiwi and banana into the add-on**.
- The November 13 shipped add-on had six fruit variants at different stages of development: strawberry the most developed; Kiwi working/nearly complete; four others marked WIP. These are author's retrospective descriptions, not independent functionality tests.

**These facts do not prove** the exact sequence of every refactor, the contents of the 90-line manifesto, or which particular GN group was copied/reused in a paid fruit source. Source code at version 0.4.3 shows an **end-state architecture**, not a historical diff.

## 3. Best-supported reconstruction (INFERENCE — not directly logged)

```text
Phase A: Strawberry-specific Blender scripts / Geometry Nodes
     ↓ (Nov 5: user explicitly chooses add-on)
Phase B: Generic Blender add-on runtime:
         fruit registry, common API, create/remove, cut, preview,
         copying, physics, asset import, presets
     ↓ (Nov 6: ~90-line recipe + parallel agent fruit sessions)
Phase C: Per-fruit adapters + self-contained blend/node bundles:
         strawberry.blend, kiwi.blend, banana.blend, etc.
     ↓
Phase D: Unified end-user interface presenting separate fruit generators,
         with feature capabilities and quality differing by fruit
```

This was apparently a **platform / adapter architecture**, not an `all fruit = same GN tree plus presets` design. Biological/geometry modules still differ by fruit. The reusable layer is mainly the infrastructure and some low-level operations.

## 4. Practical conclusion for our Fruit Engine

We should adopt the strengths of Frucht's approach while improving its weaknesses:

1. **Common, explicit data contract** (`FruitSpec`): taxon, cultivar, developmental organ identity, tissue domains, cell populations, typed vascular graph, reproduction/seed placement, attachments, physical scale and provenance. A fruit has **several topology plugins**, not merely scalar presets.
2. **Reusable GN / procedural primitives**: field sampling, mesh/volume conversion, typed vascular curves, cell generators, region material application, attachments, cut/LOD/export; preserve independent anatomical profiles.
3. **Per-fruit graph composition**: `StrawberryReceptacleAndAchenes` and `KiwiPericarpLoculesAndInternalSeeds` are separate assemblies that can reuse primitives but are not interchangeable algorithms. Every biology-dependent value must cite specific atlas/table scope (not arbitrary 539 achenes).
4. **Common runtime and API** similar in intent to `Frucht` registry, but **no mutable-module-global dispatch**: pass `FruitContext(spec, state, resources)` explicitly to build/rebuild/update functions, making multi-fruit projects testable.
5. **Shared operations**, not organs: `Cut`, `Off/Fast/Exact`, animation, preview, render/export are applied after anatomical structures are defined.
6. **Test two complete fruits first** (minimal Strawberry + Kiwi) under one public Blender add-on/entry point; only later add banana/cherry. Reuse confirmed by tests, not by count of identical node names.

Our M1f already has **physically scaled, source-linked profiles and 2 shared GN groups**, but not this fully modular runtime. This document is a **confirmed research outcome**, not a claim that the next refactor was implemented.

## Access / copyright

Free `Frucht Free - Kiwi 0.4.3` manifest declares `SPDX:GPL-3.0-or-later`. This audit contains **only high-level independently written analysis**, no verbatim imported source, no proprietary asset or node tree. Original ZIP and `kiwi.blend` remain in the owner's restricted [Drive reference](https://drive.google.com/drive/folders/1nmOaAsu06breNDKJxCBTYH8JByEcRRFP). A downstream derivative must separately satisfy applicable licensing.
