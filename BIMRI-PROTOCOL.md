# BIMRI Protocol v4

Brief Interaction Memory and Retrieval Intelligence.

This is the full BIMRI operating protocol. The short bootstrap lives in `AGENTS.md`. Keep this file in the repository root as `BIMRI-PROTOCOL.md`.

## Core Principles

`bimri.md` is not a diary. It is the current operating state.

Two rules sit underneath everything else in v4.

Write ahead. Journal decisions and outcomes into the run log at the moment they happen. A session that dies still leaves a complete record up to the point of death. Reconstructing memory at the end of a session is the failure mode this protocol exists to remove.

Headlines live in hot memory, bodies live on disk. Every entry in `bimri.md` is one line: identity, scoring metadata, a single-sentence headline, and a pointer to the full record in `.bimri/log/`. Depth is always one grep away, so hot memory stays permanently small.

## The Two Layers

BIMRI v4 is layered. The markdown protocol works standalone in any agent that reads repository instruction files. The engine, `bimri-engine.py`, is one optional dependency-free script that takes over every deterministic job when present: run counting, decay math, cap enforcement, orphan detection, archival, and index building.

With the engine installed, the agent receives a BIMRI BRIEF at session start and spends zero attention on bookkeeping. Without it, the agent follows the protocol-only fallback steps in this document. Judgment about what matters and how to compress it belongs to the agent in both modes. Arithmetic belongs to the engine whenever the engine exists.

## File Model

```text
AGENTS.md                    # cross-agent bootstrap
CLAUDE.md                    # Claude Code bridge that imports AGENTS.md
BIMRI-PROTOCOL.md            # this full protocol
bimri-engine.py              # optional deterministic engine
BIMRI-STATE.template.json    # template for .bimri/state.json
BIMRI-MEMORY.template.md     # template for bimri.md
bimri.md                     # hot memory: headlines and pointers only
.bimri/
  state.json                 # run count, cadence class, caps, thresholds
  index.tsv                  # machine-built map of every ID to its location
  log/                       # append-only run logs, one file per run
  inbox/                     # raw notes awaiting consolidation
  archive/                   # demoted memory with provenance, never deleted
  backups/                   # hot memory snapshots before any modification
```

## Hot Memory Format

`bimri.md` has three tiers. Every entry is exactly one line. The caps are the budget: line counts are enforceable by a script and by a model, while token estimates are enforceable by neither.

### Tier 1: Core Intelligence

Durable facts, decisions, constraints, preferences, and graduated operating rules. Cap: 12 lines. No decay applies here. Change a Tier 1 line only when a fact changes or the user corrects memory.

```text
[R001-E01] [decision] [arch] Run logs are append-only; hot memory is never reconstructed from scratch.
[R004-E02] [pref] [style] User wants briefs in plain prose with zero filler.
```

Kinds: `decision`, `fact`, `pref`, `rule`. A `rule` is a graduated pattern, see Pattern Graduation below.

### Tier 2: Active Context

Open loops, current work state, risks, and near-term actions. Cap: 20 lines soft, 26 hard.

```text
[R047-E02] [I:3] [active] [F:R047] [L:R051] [billing] Stripe retry design done; verify idempotency tests next. -> .bimri/log/R047.md
```

Fields in order: ID, importance 1 to 5, status, first run, last relevant run, tags, headline, pointer. Statuses: `active`, `watch`, `closed`, and `decision` as a transitional marker meaning promote this to Tier 1 at the next touch. The WEIGHT and TTL fields from v3 are gone. Weight is computed transiently by the engine from `[L:]` and never written to disk, which removes the rewrite-every-entry burden that made v3 maintenance unreliable.

When an entry materially matters again during a run, update its `[L:]` to the current run. That single field refresh is what keeps a live entry alive.

### Tier 3: Pattern Recognition

Evidence-backed hypotheses. Cap: 8 patterns. No evidence IDs, no pattern.

```text
[P003] [developing] [obs:4] [ev:R004-E02,R009-E01,R014-E03,R017-E01] User simplifies architecture before expanding features. | Falsify: user repeatedly ships speed over structure.
```

Confidence: `emerging` for 1 to 2 observations, `developing` for 3 to 5, `established` for 6 or more.

## Importance Scoring

- `I:5` foundational, changes how every future session should work
- `I:4` significant, a major deliverable or durable decision
- `I:3` notable, useful for upcoming sessions
- `I:2` minor, helpful but short-lived
- `I:1` transient, belongs in the inbox or nowhere

When unsure, write to `.bimri/inbox/`, never to hot memory.

## Run Logs And Write-Ahead Journaling

Every run gets one append-only file: `.bimri/log/R047.md`. The engine creates the stub at start; in protocol-only mode the agent creates it from the same shape.

```text
# Run R047 | 2026-06-10T09:00Z | hourly_cron

## Journal

[ID:R047-E01] [I:3] Full detail of a decision, written the moment it was made. Reasoning, alternatives rejected, anything a future session might need.
[ID:R047-E02] [I:4] Another decision with its complete context.

## Outcome

[OUTCOME:success] Webhook retry verified, all tests green.
[CLOSED:R047 2026-06-10T09:14Z]
```

Journal rhythm: append an `[ID:]` entry at every decision, milestone, or risk the moment it occurs. Appends cost 30 to 50 tokens and never require reading the file back. Run logs are immutable history. Nothing edits them after the fact, which makes them crash-safe and corruption-proof.

Write timing differs by mode. BIMRI Loop journals at every decision without exception, because unattended runs die without warning. BIMRI Session sets that same behavior as its ceiling and allows a softer floor: a short supervised session may write its bodies once before closing, and any session that runs long or approaches auto-compaction escalates to milestone journaling, since compaction summarizes detail away and an end-of-session write can only record what survived.

The `[OUTCOME:]` line is mandatory vocabulary: `success`, `partial`, `overflow`, `fail`, plus one line of why. The engine aggregates these across runs, so an agent that overflows one run in five shows up as data instead of a feeling.

Anything promoted into hot memory is a one-line headline pointing back at its log entry. The log entry holds the body forever.

## The Index And Retrieval

`.bimri/index.tsv` maps every ID to its location: hot memory, run log detail, or archive. The engine rebuilds it at every start and close, so it is a cache, never a source of truth, and corruption costs nothing.

Retrieval is grep. When depth is needed on any headline, pattern evidence, or archived entry:

```text
grep R047-E02 .bimri/index.tsv
grep -r "billing" bimri.md .bimri/index.tsv
```

Read only the file the index points to. This is what makes aggressive pruning safe: archived memory stays one grep away, so demoting a line from hot memory loses nothing. The v3 archive was write-only and made agents hoard out of justified fear. The index removes the fear, which removes the hoarding, which is what keeps `bimri.md` small in practice instead of in theory.

## Decay, Cadence Classes, And Weight

Freshness multiplies importance: `weight = importance x min(day_multiplier, run_multiplier)`. The day table is universal. The run table is selected by `cadence_class` in `state.json`, because a project touched three times a week and an agent running 24 times a day cannot share one freshness curve.

- `interactive` runs decay: 0-1 runs 1.0, 2-3 runs 0.8, 4-5 runs 0.5, 6-10 runs 0.35, 11+ runs 0.2
- `daily_cron` runs decay: 0-2 runs 1.0, 3-6 runs 0.8, 7-12 runs 0.5, 13-24 runs 0.35, 25+ runs 0.2
- `hourly_cron` runs decay: 0-24 runs 1.0, 25-72 runs 0.8, 73-168 runs 0.5, 169-336 runs 0.35, 337+ runs 0.2
- Days, all classes: 0-1 days 1.0, 2-3 days 0.8, 4-5 days 0.5, 6-10 days 0.35, 11-15 days 0.2, 16-20 days 0.15, 21+ days 0.1

Thresholds drive action. Below 0.5, an entry is flagged in the brief for agent judgment: refresh `[L:]` or close it. At or below 0.2 with importance 2 or lower, the engine archives it mechanically. Closed entries are archived mechanically at the next start. The engine never mechanically archives a healthy `I:4` or `I:5` entry; high-importance entries leave hot memory only through agent judgment, promotion to Tier 1, or decay below the flag threshold.

Protocol-only mode uses the simplified rule: archive any Tier 2 entry whose `[L:]` is older than 10 runs or 15 days for interactive work, or older than 150 runs for hourly cron work, unless it carries `I:4` or higher.

## Session Start

With the engine, via hooks or as the first command of a cron run:

```text
python3 bimri-engine.py start
```

The engine counts the run, performs safe mechanical archival, detects orphans, opens the run log, rebuilds the index, and prints a BIMRI BRIEF directly into context. The agent then reads `bimri.md`, resolves every JUDGMENT NEEDED item in the brief, and begins work.

Protocol-only fallback, in order: read `bimri.md`, create it from the template if missing, create `.bimri/` directories if missing, increment `run_count` in `state.json`, check the previous run log for a missing `[CLOSED:]` line and run orphan recovery if found, create this run's log stub, apply the simplified decay rule, then begin work.

On a brand-new project with an empty Tier 1, ask at most three orientation questions: what this project is for, what matters most right now, and what constraints future agents should remember. If the user skips intake, populate from observed context.

## During Work

Work normally. Journal into the run log at decision moments. Touch `[L:]` on hot entries that materially recur. Promote a new headline into Tier 2 only when it will affect future sessions. Resist storing anything that code, docs, issues, or agent auto memory already hold.

## Closing A Run

Append the `[OUTCOME:]` line to the run log, add or refresh hot memory headlines for anything durable from this run, then close:

```text
python3 bimri-engine.py close
```

The engine stamps closure, stamps any orphans, enforces hard caps, and rebuilds the index. In protocol-only mode, the agent writes the `[OUTCOME:]` and `[CLOSED:]` lines itself and trims Tier 2 to its cap by archiving the weakest lines to `.bimri/archive/YYYY-MM.md` with an `[ARCHIVED:run date]` prefix.

Cron wiring, with a semicolon so closure runs even when the agent dies:

```text
cd /path/to/project && python3 bimri-engine.py start && <agent command> ; python3 bimri-engine.py close
```

## Orphan Recovery

A run log without a `[CLOSED:]` line means the run died before finishing: turn overflow, crash, closed laptop, context compaction. The next start brief names the orphan. The agent reads the tail of that log, promotes anything durable into hot memory as headlines, and continues. The close command then stamps the orphan with `[OUTCOME:overflow]` and an auto-closure line. Dead runs lose nothing that was journaled, which under write-ahead journaling means dead runs lose nothing.

## Maintenance

The engine performs safe mechanical archival at every start, so maintenance debt never accumulates. `python3 bimri-engine.py maintain` forces a pass on demand and prints any judgment items. `maintenance_mode` in `state.json` keeps its v3 meanings: `ask` before acting, `warn` then act, `auto` act and report. Hard deletion is never automatic in any mode. The archive grows monthly files forever; the index keeps all of it retrievable, and disk is cheap where context is expensive.

## Pattern Graduation

Patterns are the compounding layer. Evidence IDs stay permanently resolvable through the index, so observations accumulate across hundreds of runs instead of dying with the archive.

The lifecycle runs: observation, pattern, rule. An `established` pattern that has survived 10 or more runs without a falsifying observation is a graduation candidate. Graduation writes a one-line `[rule]` entry into Tier 1 and archives the pattern with its evidence trail intact. Under `ask` or `warn` mode, propose graduation to the user first. A graduated rule changes agent behavior in every future session, which is the loop the whole protocol exists to close.

Outcome lines feed patterns about the agent itself. Recurring `overflow` or `fail` outcomes with a shared cause are pattern evidence like anything else, so the system surfaces its own failure modes from data.

## Inbox Policy

`.bimri/inbox/` holds short raw notes that are not yet memory, named `R047-note.md`. The start brief reports the inbox count. Consolidate during any run with spare attention: promote, merge into an existing entry, or archive. The inbox is a buffer, never a destination.

## Rules

- Hot memory is headlines and pointers. Bodies live in run logs.
- Write ahead. Journal at the moment of decision.
- The caps are the budget. One line per entry, no exceptions.
- Run logs are append-only and never edited after the fact.
- Never hard-delete memory automatically. Archive with provenance.
- Preserve IDs everywhere so the index can always resolve them.
- No evidence IDs, no pattern. No falsifier, no pattern.
- Established patterns graduate into Tier 1 rules.
- When unsure, write to the inbox.
- Arithmetic belongs to the engine. Judgment belongs to the agent.

## Corruption Recovery

If `bimri.md` is corrupted, restore the newest snapshot from `.bimri/backups/`. If no backup exists, recreate from the template, rebuild the index with `python3 bimri-engine.py index`, and reconstruct Tier 2 headlines from the most recent run logs. Run logs are the durable record; hot memory is always rebuildable from them. Never invent lost context.

<!-- END BIMRI PROTOCOL v4 -->
