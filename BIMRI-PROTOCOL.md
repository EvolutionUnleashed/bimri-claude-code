# BIMRI Protocol v2.1-ca

Brief Interaction Memory and Retrieval Intelligence.

This is the full BIMRI operating protocol. Keep the short bootstrap in `AGENTS.md`. Keep this file in the repository root as:

```text
BIMRI-PROTOCOL.md
```

## Core principle

`bimri.md` is not a diary. It is the current operating state.

The agent should only promote information into active memory when it is likely to affect future work. Raw notes, uncertain memories, and low-confidence details belong in `.bimri/inbox/` until consolidated.

## File model

```text
AGENTS.md                    # cross-agent bootstrap
CLAUDE.md                    # Claude Code bridge that imports AGENTS.md
BIMRI-PROTOCOL.md            # this full protocol
BIMRI-STATE.template.json    # template for .bimri/state.json
BIMRI-MEMORY.template.md     # template for bimri.md
bimri.md                     # compact active project memory
.bimri/
  state.json                 # run count, maintenance state, budgets
  inbox/                     # raw notes awaiting consolidation
  archive/                   # stale or closed memory, never auto-deleted
  backups/                   # snapshots before maintenance
```

## Relationship to other memory systems

BIMRI does not replace agent auto memory, documentation, issue trackers, or code comments.

Use other systems for:

- build commands;
- package manager quirks;
- lint commands;
- local environment fixes;
- specific file paths;
- routine implementation details.

Use BIMRI for:

- project purpose;
- durable decisions;
- strategic context;
- user preferences;
- active risks;
- unresolved threads;
- current operating state;
- behavioral or project patterns backed by evidence.

## State file

BIMRI uses `.bimri/state.json` as the source of truth for run count and maintenance state. Do not infer the run number from prose.

Expected fields are defined in `BIMRI-STATE.template.json`.

Important fields:

```json
{
  "bimri_version": "2.1-ca",
  "run_count": 0,
  "current_run_id": "R000",
  "last_bimri_update_run": 0,
  "last_light_maintenance_run": 0,
  "last_deep_maintenance_run": 0,
  "light_maintenance_interval_runs": 3,
  "deep_maintenance_interval_runs": 10,
  "maintenance_mode": "warn",
  "prune_policy": "archive_only",
  "token_budget_soft": 3000,
  "token_budget_hard": 4000,
  "max_active_entries": 24,
  "max_patterns": 10,
  "max_inbox_files": 10
}
```

### Run counter rule

Increment `run_count` once per new agent startup. Do not increment for repeated stop checks, compaction, or minor internal retries.

If the agent cannot confidently distinguish a resumed session from a new run, it should warn the user and proceed conservatively.

## Session start protocol

At the start of every meaningful task:

1. Read `AGENTS.md`.
2. Read `bimri.md` if it exists.
3. If `bimri.md` is missing, create it from `BIMRI-MEMORY.template.md`.
4. Ensure `.bimri/inbox/`, `.bimri/archive/`, and `.bimri/backups/` exist.
5. Read `.bimri/state.json` if it exists.
6. If `.bimri/state.json` is missing, create it from `BIMRI-STATE.template.json`.
7. Increment `run_count` once for the new run and update `current_run_id`.
8. Check whether light or deep maintenance is due.
9. Use BIMRI context before planning or editing.

If the project is new and `bimri.md` has no Tier 1 entries, ask at most 3 orientation questions unless the user clearly wants to proceed immediately:

- What is this project for?
- What matters most right now?
- What constraints or preferences should future agents remember?

If the user skips intake, continue and populate BIMRI from observed context.

## Active memory structure

`bimri.md` has three tiers.

### Tier 1: Core Intelligence

Permanent project facts, durable decisions, hard constraints, and user preferences. Keep this small. Tier 1 should change only when facts change or the user explicitly corrects memory.

Example:

```text
[ID:R001-E01] [I:5] [STATUS:decision] [FIRST:R001] [LAST:R001] [TAGS:purpose]
This project is a cross-agent memory protocol for coding agents, designed to reduce cold-start loss across sessions.
```

### Tier 2: Active Context

Current work state, open loops, unresolved risks, near-term next actions, and recently important outcomes.

Entry format:

```text
[ID:R017-E01] [I:3] [STATUS:active] [TTL:5r/14d] [FIRST:R017] [LAST:R017] [TAGS:architecture,billing] [WEIGHT:2.4]
Implemented Stripe webhook retry design; next session should verify idempotency tests before deployment.
```

### Tier 3: Pattern Recognition

Evidence-backed hypotheses about project behavior, user preferences, or recurring workflow patterns.

Pattern format:

```text
[PATTERN:P003] [CONFIDENCE:developing] [OBS:4] [EVIDENCE:R004-E02,R009-E01,R014-E03,R017-E01]
User prefers architectural simplification before feature expansion.
Falsify if: user repeatedly prioritizes speed-to-ship over structural cleanup.
```

Pattern confidence:

- `emerging`: 1 to 2 observations;
- `developing`: 3 to 5 observations;
- `established`: 6 or more observations.

No evidence IDs means no pattern.

## Importance scoring

Use this scale:

- `I:5`: foundational, changes how every future session should work;
- `I:4`: significant, major deliverable or durable decision;
- `I:3`: notable, useful for upcoming sessions;
- `I:2`: minor, helpful but short-lived;
- `I:1`: transient, normally belongs in inbox or not at all.

When unsure, write to `.bimri/inbox/`, not core BIMRI.

## Freshness and weight

Use simple lookup tables. Do not do elaborate math.

### Days since last relevant use

| Days | Multiplier |
|---:|---:|
| 0 to 1 | 1.0 |
| 2 to 3 | 0.8 |
| 4 to 5 | 0.5 |
| 6 to 10 | 0.35 |
| 11 to 15 | 0.2 |
| 16 to 20 | 0.15 |
| 21+ | 0.1 |

### Runs since last relevant use

| Runs | Multiplier |
|---:|---:|
| 0 to 1 | 1.0 |
| 2 to 3 | 0.8 |
| 4 to 5 | 0.5 |
| 6 to 10 | 0.35 |
| 11+ | 0.2 |

Use the lower of the two multipliers.

```text
composite_weight = importance * freshness_multiplier
```

Important nuance: high-importance Tier 2 entries are not immortal. If an old `I:4` or `I:5` entry remains permanently relevant, promote it into Tier 1 as a decision or core fact. Otherwise it can still close and archive.

## Lifecycle statuses

Use statuses instead of deleting entries.

- `active`: affects current work;
- `watch`: monitor but not immediately actionable;
- `decision`: durable choice or project fact;
- `closed`: resolved or no longer active;
- `archived`: moved to archive;
- `promoted`: merged into Tier 1 or Tier 3.

Lifecycle flow:

```text
active -> closed -> archived
active -> decision -> Tier 1
active -> pattern evidence -> Tier 3 evidence -> archived
watch -> active or archived
```

## During work

Work normally. Do not interrupt useful work just to update memory.

Track durable items:

- decisions made;
- work completed that changes future context;
- open loops;
- risks;
- constraints;
- user preferences;
- repeated behaviors worth testing as patterns.

Avoid storing routine technical details that are already captured in code, docs, issues, build files, or auto memory.

## Before finishing meaningful work

Before the final response on meaningful work:

1. Create a backup of `bimri.md` in `.bimri/backups/` if possible.
2. Add or update concise active memory in `bimri.md`.
3. If no BIMRI update is needed, say why in one sentence.
4. Update `.bimri/state.json`, especially `last_bimri_update_run`.
5. If maintenance is due, warn the user and perform safe maintenance according to `maintenance_mode`.
6. Confirm briefly: `BIMRI updated.` or `No BIMRI update needed.`

If the session is ending abruptly, write at minimum one concise Tier 2 entry or an inbox note.

## Maintenance triggers

Maintenance is due when any condition is true:

- user says `run BIMRI maintenance` or similar;
- `run_count - last_light_maintenance_run >= light_maintenance_interval_runs`;
- `run_count - last_deep_maintenance_run >= deep_maintenance_interval_runs`;
- active entries exceed `max_active_entries`;
- estimated tokens exceed `token_budget_soft`;
- estimated tokens exceed `token_budget_hard`;
- inbox files exceed `max_inbox_files`;
- pattern count exceeds `max_patterns`.

## Maintenance modes

Read `maintenance_mode` from `.bimri/state.json`.

- `ask`: ask before compression, archival, or promotion.
- `warn`: announce safe maintenance before doing it. This is the default.
- `auto`: run safe maintenance without interrupting, but still never hard-delete.

Hard deletion is never automatic. It requires an explicit user command.

Safe warning language:

```text
BIMRI maintenance is due: run R020, active memory over soft budget. I am compacting Tier 2 and moving stale items to `.bimri/archive/2026-05.md`. Nothing will be deleted.
```

## Light maintenance

Light maintenance should run every 3 runs or when active memory is slightly over budget.

Steps:

1. Back up `bimri.md`.
2. Move closed or stale Tier 2 entries to `.bimri/archive/YYYY-MM.md`.
3. Consolidate related active entries.
4. Move uncertain or low-value details to `.bimri/inbox/`.
5. Recalculate weights.
6. Update `last_light_maintenance_run`.
7. Report briefly what changed.

## Deep maintenance

Deep maintenance should run every 10 runs or when the hard budget is exceeded.

Steps:

1. Back up `bimri.md`.
2. Review Tier 1 for accuracy. Ask before rewriting durable facts.
3. Compress Tier 2 into the smallest useful active state.
4. Archive closed, stale, duplicated, or low-value entries.
5. Review Tier 3 patterns. Merge, weaken, promote, or archive patterns based on evidence.
6. Ensure every pattern has evidence IDs.
7. Clean unused tags.
8. Update state fields.
9. Report briefly what changed.

## Archive policy

Automatic maintenance may archive. It may not hard-delete.

Archive format:

```text
.bimri/archive/YYYY-MM.md
```

Archived content should preserve original IDs so Tier 3 evidence remains traceable.

## Inbox policy

Use `.bimri/inbox/` for raw or uncertain notes.

Inbox notes should be short. They are not active memory until consolidated.

Suggested filename:

```text
.bimri/inbox/R017-note.md
```

## Rules

- `bimri.md` is active operating state, not a session diary.
- When in doubt, write to `.bimri/inbox/`, not core BIMRI.
- Never hard-delete memory automatically.
- Preserve IDs when archiving.
- Tier 1 should stay small and stable.
- Tier 2 should be aggressively compact.
- Tier 3 patterns require evidence IDs.
- High-importance Tier 2 entries are not immortal. Promote durable facts to Tier 1 or archive stale context.
- Do not duplicate information that auto memory, code, docs, or issue trackers already handle well.

## Corruption recovery

If `bimri.md` is corrupted or unreadable:

1. Check `.bimri/backups/` for the latest usable backup.
2. If no backup exists, create a fresh file from `BIMRI-MEMORY.template.md`.
3. Note in Tier 2 that memory history was lost or partially recovered.
4. Do not invent lost context.

<!-- END BIMRI PROTOCOL -->
