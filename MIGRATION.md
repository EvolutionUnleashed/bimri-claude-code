# Migrating From v3 To v4

One guided agent session migrates a project. IDs, pattern evidence, and archives carry over intact, so nothing in your memory history breaks.

## What Changes Shape

v3 entries were multi-line with `[WEIGHT:]` and `[TTL:]` fields and full detail inline. v4 entries are one line each: the detail moves into a synthetic run log, the hot file keeps a headline and a pointer, and weight becomes something the engine computes instead of something anyone writes.

## Steps

1. Copy the v4 files into the project root: `AGENTS.md`, `CLAUDE.md`, `BIMRI-PROTOCOL.md`, `bimri-engine.py`, both templates, and `hooks-example.json` if you use Claude Code hooks. These overwrite the v3 versions of the same names.
2. Run `python3 bimri-engine.py start` once. The engine creates `.bimri/log/`, `.bimri/index.tsv`, and a fresh `state.json` if needed. Your existing `bimri.md`, inbox, and archive are untouched.
3. Paste the migration prompt below into one agent session and let it run.
4. Run `python3 bimri-engine.py status` and confirm the caps and index rows look right.

## The Migration Prompt

```text
Migrate this project's BIMRI memory from v3 to v4 per BIMRI-PROTOCOL.md.

1. Create .bimri/log/R000-migrated.md with a "# Run R000-migrated" header and a "## Journal" section.
2. For every Tier 2 entry in bimri.md: append its full text to that log as an [ID:original-id] [I:n] line preserving the original ID, then replace the entry in bimri.md with one line in v4 grammar: [ID] [I:n] [status] [F:Rnnn] [L:Rnnn] [tags] one-sentence headline -> .bimri/log/R000-migrated.md. Drop WEIGHT and TTL fields entirely.
3. Rewrite Tier 1 entries into v4 grammar: [ID] [decision|fact|pref] [tags] text. Keep their IDs.
4. Rewrite Tier 3 patterns into v4 grammar: [Pnnn] [confidence] [obs:n] [ev:ID,ID] hypothesis | Falsify: condition. Keep all evidence IDs.
5. Enforce caps: Tier 1 max 12, Tier 2 max 20, Tier 3 max 8. Archive overflow lines to .bimri/archive/ with an [ARCHIVED:] prefix, weakest first.
6. Append [OUTCOME:success] migration complete and a [CLOSED:] line to the migrated log, then run: python3 bimri-engine.py index
7. Report what moved, what was archived, and the final line counts per tier.
```

## After Migration

Old archives stay valid; the index picks up any `[ID:]`-prefixed lines they contain. The state file resets cleanly: run numbering continues from wherever `run_count` sits, and `cadence_class` defaults to `interactive`, so set it to `daily_cron` or `hourly_cron` for scheduled agents before their next run.
