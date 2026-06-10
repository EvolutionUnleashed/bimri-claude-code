# AGENTS.md

## BIMRI Memory Protocol v4

This repository uses BIMRI: Brief Interaction Memory and Retrieval Intelligence.

`bimri.md` is hot memory: one-line headlines with pointers into `.bimri/log/`. Treat it as active operating state, not as a diary and not as immutable truth. Full detail always lives in the run logs and is retrievable by grepping `.bimri/index.tsv`.

## Start Of Every Meaningful Task

1. If a `=== BIMRI BRIEF ===` block is already in your context, the engine ran at session start. Read `bimri.md`, resolve every JUDGMENT NEEDED item in the brief, then begin work.
2. Otherwise, if `bimri-engine.py` exists in the repository root, run `python3 bimri-engine.py start` as your first action and follow step 1 with its output.
3. Otherwise run protocol-only mode: read `bimri.md` (create from `BIMRI-MEMORY.template.md` if missing), ensure `.bimri/log/`, `.bimri/inbox/`, `.bimri/archive/`, and `.bimri/backups/` exist, increment `run_count` in `.bimri/state.json`, check the previous run log for a missing `[CLOSED:]` line and recover it if found, then create this run's log stub per `BIMRI-PROTOCOL.md`.

## During Work

Write ahead. Append an `[ID:Rnnn-Enn]` entry to this run's log in `.bimri/log/` the moment a decision, milestone, or risk occurs. Appends are cheap; reconstruction at the end is the failure mode.

Capture only durable context: purpose, decisions, preferences, constraints, risks, open loops, outcomes, and evidence-backed patterns. Routine technical minutiae belongs in code, docs, issues, or agent auto memory. When uncertain, write a short note to `.bimri/inbox/`.

When a hot memory entry materially matters again, refresh its `[L:]` field to the current run. That is what keeps live entries alive under decay.

## Before Finishing Meaningful Work

1. Append an `[OUTCOME:success|partial|overflow|fail]` line plus one line of why to this run's log.
2. Add or refresh one-line headlines in `bimri.md` for anything durable, each pointing to its log entry.
3. If the engine exists, run `python3 bimri-engine.py close`. Otherwise write the `[CLOSED:]` line yourself and trim Tier 2 to its 20-line cap by archiving the weakest lines.

## Retrieval

Depth on any headline, pattern evidence, or archived entry is one grep away:

```text
grep R047-E02 .bimri/index.tsv
```

Read only the file the index points to.

## Safety

- Never hard-delete memory. Archive to `.bimri/archive/` with provenance.
- Never edit a run log after the fact. They are append-only history.
- Ask before rewriting Tier 1 facts.
- Preserve IDs everywhere.

## File Map

- Full protocol: `BIMRI-PROTOCOL.md`
- Hot memory: `bimri.md`
- Engine: `bimri-engine.py`
- State: `.bimri/state.json`
- Index: `.bimri/index.tsv`
- Run logs: `.bimri/log/`
- Inbox: `.bimri/inbox/`
- Archive: `.bimri/archive/`
