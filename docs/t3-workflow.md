# Strawberry Lab: pstack + Beads in T3

Owner approved OpenAI-only roles on 20 November 2026. Exact models/options are in [role configuration](../config/t3-agent-roles.json); the executable agent entrypoint is [strawberry-t3](../.agents/skills/strawberry-t3/SKILL.md). Original pstack remains installed unchanged in the user's Codex skills. This is a project adapter, not a claim of native upstream T3 support.

The parent discusses goals, owns Beads and exclusively controls live Blender. One Sol implementation worker writes assigned source files and builds headlessly. A fresh Astra reviewer reads actual evidence. Small accepted findings can be fixed by the parent; substantive changes need their relevant verification. Visual acceptance belongs to the owner.

## Authority and recovery

GitHub Issues define milestones (exterior: Issue #2); Git stores source and reports. Beads is the operational dependency graph and local task history, not another anatomical specification. Working database lives in this checkout's .beads/ and must not be deleted or assumed to exist in another clone. Use the canonical path of this checkout for all bd commands. Run bd prime and bd ready --json, then read active tasks before assigning work. The current exterior epic is straw-k43.

Dolt database is not committed into Git. A full Dolt-native local backup was initialized and synced to `~/.local/share/strawberry-lab/beads-backup` on this Mac. This is same-machine recovery, not an off-machine backup. Run `bd backup sync` after queue changes. No remote database push has been verified or performed. Tracked configuration does not back up task state. For another machine/checkout, first establish an explicit Dolt backup/remote restoration route; never infer recovery from a JSON task listing. Beads may derive an origin remote, but this setup does not enable automatic sync. No Git hooks, harness hooks, observer or recurring LLM heartbeat were installed.

## Surface verification

Build new versions under build/, never overwrite archived M1/M2 artifacts. Open the saved scene in a fresh Blender process and validate geometry/instances/materials before presenting. Inspect an authentic Blender render. Preserve the GUI file before switching; only parent may use Flue. Do not claim measured anatomy for artist-designed shape, pit depth, seed arrangement, or shading.

## Local runtime

Blender installed here is 5.2.2 LTS; historical reports used 5.2.4, so every fresh build records its actual version. Use a project environment rather than system Python:

```sh
uv venv .venv --python python3.13
uv pip install --python .venv/bin/python -r requirements.txt
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
bd ready --json
```

New review runs use T3 delegate_task and exactly the provider, model and options from role configuration. Provider catalog presence alone is not proof that the model executed; preserve the task result's executed-model evidence where available. Do not change models silently.
