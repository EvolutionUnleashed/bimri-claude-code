# BIMRI for Claude Code and Coding Agents

**Brief Interaction Memory and Retrieval Intelligence - v3**

BIMRI is a lightweight project memory protocol for coding agents. It gives the agent a small, useful memory file that survives across sessions without turning into a bloated session diary.

The core rule:

> `bimri.md` is not a diary. It is the current operating state.

This release upgrades the original Claude Code focused version into a cross-agent version. The main startup trigger is now `AGENTS.md`, while Claude Code is supported through a small `CLAUDE.md` bridge.

## What changed in v3-ca

- `AGENTS.md` becomes the universal startup trigger for agents that read repository instruction files.
- `CLAUDE.md` imports `AGENTS.md`, because Claude Code reads `CLAUDE.md` rather than `AGENTS.md` directly.
- `BIMRI-PROTOCOL.md` is the full protocol. Keep the bootstrap short and the full protocol separate.
- Run counting moves into `.bimri/state.json` instead of being inferred from prose.
- Pruning becomes archive-only. BIMRI should move stale memory to archive, not silently delete it.
- Low-confidence notes go to `.bimri/inbox/` instead of bloating `bimri.md`.
- Patterns must include evidence IDs. No evidence, no pattern.

## The files

| File | Purpose |
|---|---|
| `AGENTS.md` | Small cross-agent bootstrap. This is the first file many coding agents read. |
| `CLAUDE.md` | Claude Code bridge. It imports `AGENTS.md`. |
| `BIMRI-PROTOCOL.md` | Full BIMRI protocol and maintenance rules. |
| `BIMRI-STATE.template.json` | Template for `.bimri/state.json`, used for run count and maintenance state. |
| `BIMRI-MEMORY.template.md` | Template for the active `bimri.md` memory file. |
| `bimri.md` | Created inside each working project. This is active memory, not part of this repo by default. |

## Quick install into a project

Copy these files into the root of any project where you want BIMRI enabled:

```text
AGENTS.md
CLAUDE.md
BIMRI-PROTOCOL.md
BIMRI-STATE.template.json
BIMRI-MEMORY.template.md
```

Then start a new agent session in that project.

For Claude Code, `CLAUDE.md` imports `AGENTS.md`, so the BIMRI bootstrap is loaded at startup. The agent should then create or update:

```text
bimri.md
.bimri/state.json
.bimri/inbox/
.bimri/archive/
.bimri/backups/
```

## How BIMRI behaves

At the start of meaningful work, the agent should:

1. Read `AGENTS.md`.
2. Read `bimri.md` if it exists.
3. If `bimri.md` is missing, create it from `BIMRI-MEMORY.template.md`.
4. If `.bimri/state.json` is missing, create it from `BIMRI-STATE.template.json`.
5. Increment the run counter once per new agent run.
6. Check whether maintenance is due.

Before finishing meaningful work, the agent should:

1. Update `bimri.md` only with durable context.
2. Write uncertain or low-value notes to `.bimri/inbox/` instead.
3. Warn before maintenance.
4. Archive stale entries to `.bimri/archive/`.
5. Never hard-delete memory unless explicitly told to do so.

## Memory structure

`bimri.md` has three tiers.

### Tier 1: Core Intelligence

Durable project facts, hard constraints, user preferences, and decisions. Keep this small.

### Tier 2: Active Context

Current work state, open loops, recent decisions, unresolved risks, and near-term next actions.

### Tier 3: Pattern Recognition

Evidence-backed patterns. Every pattern must include evidence IDs from actual memory entries.

## Maintenance policy

Default mode is **warn and archive**.

Safe maintenance can run after warning the user. It may compress wording, close resolved entries, merge duplicates, and move stale items to archive.

Hard deletion is never automatic.

Suggested warning:

```text
BIMRI maintenance is due: run R020, active memory over soft budget. I am compacting Tier 2 and moving stale items to `.bimri/archive/2026-05.md`. Nothing will be deleted.
```

## Why this is better than the original v2.0-cc

The original version told the agent to update, prune, and maintain memory at the end of every session. That worked sometimes, but it relied on the model remembering to do too much at the worst possible moment.

This version reduces the load:

- short startup instruction in `AGENTS.md`;
- full protocol in one separate file;
- run counter in JSON;
- safe archival instead of deletion;
- active memory capped by purpose, not by endless session summaries.

## Usage notes

- Leave Claude Code auto memory enabled. BIMRI is not a replacement for technical notes.
- BIMRI is for project intelligence: purpose, strategy, decisions, preferences, risks, and open loops.
- Routine technical details belong in normal docs, issues, code comments, or agent auto memory.
- For teams, decide whether `bimri.md` should be shared in git or kept local. If it may contain private project context, add it to `.gitignore`.

Suggested `.gitignore` entries for private memory:

```gitignore
bimri.md
.bimri/state.json
.bimri/inbox/
.bimri/archive/
.bimri/backups/
```

## Manual command

To force cleanup, tell the agent:

```text
Run BIMRI maintenance. Warn me first, archive stale entries, and do not delete anything.
```

## Author

**Stu Jordan** - Agent Orchestrator  
[evolutionunleashed.com](https://evolutionunleashed.com)

## License

MIT - see `LICENSE` for details.
