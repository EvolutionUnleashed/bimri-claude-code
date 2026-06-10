# BIMRI: Memory Infrastructure For Coding Agents

**Brief Interaction Memory And Retrieval Intelligence - v4**

BIMRI gives coding agents memory that compounds. It keeps a small, permanently bounded memory file in context, stores full detail on disk behind pointers, and grows more valuable over time through evidence-backed pattern recognition.

The core rules:

> `bimri.md` is not a diary. It is the current operating state.

> Write ahead. Journal at the moment of decision, never reconstruct at the end.

> Headlines live in hot memory. Bodies live on disk, one grep away.

## Two Modes, One Infrastructure

BIMRI is one core product that runs in two modes. Both modes share the same engine, the same protocol, the same memory format, and the same files. The difference is who supervises the run.

**BIMRI Session** is for interactive work. You open a project, the agent orients from memory of every past session, you work, and the record updates so the next session inherits everything. Continuity is the product: cold-start orientation, durable decisions, and patterns that compound across weeks.

**BIMRI Loop** is for scheduled agents. It is Session plus the unattended-operation layer: orphan recovery for runs that die mid-flight, outcome telemetry that turns failure modes into percentages, and cap enforcement that holds while nobody watches.

Choosing takes one question. A human is in the chair: Session. The agent runs on a cron or schedule: Loop. Switching later is one config field, so nothing about the choice is permanent.

## Quick Start: BIMRI Session

1. Copy all nine BIMRI files into your project root.
2. For Claude Code, merge `hooks-example.json` into `.claude/settings.json` and verify with `/hooks`. The engine now briefs the agent automatically at session start and closes the run at session end. Without hooks, `AGENTS.md` instructs the agent to run `python3 bimri-engine.py start` as its first action, so it works either way.
3. Start a session and work normally.

Session write timing: the agent gets its brief at start and writes durable memory before the session closes. Short sessions may write their full detail once at the end. Sessions that run long escalate to journaling at milestones, because auto-compaction summarizes detail away mid-session and an end-of-session write can only record what survived. Journaling ahead of compaction is what preserves fidelity.

Minimal install: if you want zero scripts, copy only `AGENTS.md`, `CLAUDE.md`, `BIMRI-PROTOCOL.md`, and the two templates. The agent handles its own bookkeeping using the fallback rules in the protocol. Functional, lighter, less reliable, and Session-only.

## Quick Start: BIMRI Loop

1. Copy all nine BIMRI files into your project root. The engine is required in Loop mode, since deterministic maintenance with nobody watching is the whole point.
2. Open `.bimri/state.json` after the first run and set `cadence_class` to `daily_cron` or `hourly_cron`. This selects a decay curve scaled to your run frequency.
3. Wire the cron entry. The semicolon matters: closure must run even when the agent dies.

```text
cd /path/to/project && python3 bimri-engine.py start && <agent command> ; python3 bimri-engine.py close
```

Loop write timing: journal every decision the moment it happens, no exceptions. Unattended runs die without warning, and write-ahead journaling is why a run that overflows at the turn limit still loses nothing. The next start detects the orphaned run, recovers anything durable, and stamps it closed with an `[OUTCOME:overflow]` line. Run `python3 bimri-engine.py status` anytime to see outcome statistics across all runs, including your overflow rate.

## What Changed In v4

Every prior version had one root cause of drift: the model was its own maintenance engine. Run counting, decay math, budget checks, and archival all landed on the model at the end of a session, when context is fullest and attention is thinnest. Models are unreliable at deterministic bookkeeping, so pruning fired sometimes and memory bloated the rest of the time.

v4 splits the work. Arithmetic moves into `bimri-engine.py`, a single dependency-free Python script. Judgment stays with the agent. Specifically:

- **Hot memory becomes headlines and pointers.** Every entry in `bimri.md` is one line pointing at its full record in `.bimri/log/`. The file stabilizes around 1 to 1.5k tokens permanently.
- **Caps replace token budgets.** Tier 1 holds 12 lines, Tier 2 holds 20, Tier 3 holds 8 patterns. Line counts are enforceable by a script and by a model; token estimates are enforceable by neither.
- **Run logs are append-only and write-ahead.** Decisions are journaled as they happen in 30-token appends, so a dying run still leaves a complete record.
- **The index makes pruning safe.** `.bimri/index.tsv` maps every ID to its location, so archived memory stays one grep away. Agents stop hoarding context once nothing is ever truly lost.
- **Decay is cadence-aware.** Session work and hourly loops select different freshness curves through one config field.
- **Outcomes become data.** Every run log closes with an `[OUTCOME:]` line the engine aggregates across runs.
- **Patterns graduate.** Established patterns with surviving evidence promote into Tier 1 as operating rules. Observation becomes pattern becomes rule becomes changed behavior.

## How Memory Flows

1. **Start.** The engine counts the run, archives the unambiguous (closed entries, fully decayed minor ones), flags decayed entries for judgment, detects orphaned runs, opens this run's log, and prints a brief.
2. **Work.** The agent journals `[ID:]` entries into the run log and refreshes `[L:]` on hot entries that recur.
3. **Close.** The agent writes an `[OUTCOME:]` line and durable headlines, then the engine stamps closure, enforces caps, and rebuilds the index.
4. **Compound.** Evidence accumulates, patterns strengthen, established patterns graduate into Tier 1 rules that change behavior in every future session.

## The Files

| File | Purpose |
| --- | --- |
| `AGENTS.md` | Cross-agent bootstrap, the first file many agents read. |
| `CLAUDE.md` | Claude Code bridge that imports `AGENTS.md`. |
| `BIMRI-PROTOCOL.md` | Full protocol: formats, decay tables, lifecycle, recovery. |
| `bimri-engine.py` | Deterministic engine. Stdlib only, no dependencies. Optional in Session, required in Loop. |
| `hooks-example.json` | Claude Code hook wiring for automatic start and close. |
| `BIMRI-MEMORY.template.md` | Template for `bimri.md` hot memory. |
| `BIMRI-STATE.template.json` | Template for `.bimri/state.json`. |
| `MIGRATION.md` | Guided path from v3. |
| `bimri.md` | Created in each project. Hot memory, headlines and pointers only. |

## Token Math

An hourly Loop agent under v3 read a 3 to 4k token memory file at start, read it again before updating, then rewrote the whole thing: roughly 10k tokens of memory overhead per run, 240k per day, with corruption risk on every rewrite. Under v4 the same agent reads a 1.5k hot file and appends under 200 tokens: roughly 2k per run, under 50k per day. Better recall at a fifth of the cost, and the rewrite step that corrupted files is gone entirely.

## Manual Commands

```text
python3 bimri-engine.py status     # sizes, caps, run outcome statistics
python3 bimri-engine.py maintain   # force a safe archival pass plus judgment brief
python3 bimri-engine.py index      # rebuild the index from all memory files
```

The engine never hard-deletes memory in any mode. Archival moves lines to `.bimri/archive/` with provenance stamps, and hot memory is backed up before every modification.

## Privacy

For teams, decide whether memory ships in git. If it may contain private context:

```gitignore
bimri.md
.bimri/
```

## Migrating From v3

See `MIGRATION.md` for the guided one-session path. IDs and pattern evidence carry over intact. Migration lands you in Session mode by default; Loop users then set `cadence_class` per the quick start above.

## Author

**Stu Jordan** - Agent Orchestrator
[evolutionunleashed.com](https://evolutionunleashed.com)

## License

MIT - see `LICENSE` for details.
