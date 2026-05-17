# AGENTS.md

## BIMRI Memory Protocol

This repository uses BIMRI: Brief Interaction Memory and Retrieval Intelligence.

BIMRI is project memory for coding agents. Treat `bimri.md` as active operating state, not as a diary and not as immutable truth.

## Start of every meaningful task

1. Check for `bimri.md` in the repository root.
2. If present, read it before planning, coding, or editing.
3. If absent and `BIMRI-MEMORY.template.md` exists, create `bimri.md` from that template.
4. If `.bimri/state.json` is absent and `BIMRI-STATE.template.json` exists, create `.bimri/state.json` from that template.
5. Read `BIMRI-PROTOCOL.md` when you need the full operating protocol.
6. Increment the run counter once per new agent run if `.bimri/state.json` exists.
7. Check whether maintenance is due before planning large work.

## During work

Capture only durable context:

- project purpose;
- strategic decisions;
- user preferences;
- constraints;
- active risks;
- unresolved questions;
- meaningful outcomes;
- recurring patterns with evidence.

Do not put routine technical minutiae in core BIMRI if normal docs, build files, issue notes, or agent auto memory cover it better.

When uncertain, write a short note to `.bimri/inbox/` instead of expanding `bimri.md`.

## Before finishing meaningful work

1. Update `bimri.md` with concise active memory or record why no BIMRI update was needed.
2. Update `.bimri/state.json` if available.
3. If maintenance is due, warn the user before compaction or archival.
4. Archive stale entries to `.bimri/archive/`; never hard-delete memory automatically.

## Maintenance safety

- Warn before safe maintenance.
- Ask before deleting anything permanently.
- Ask before rewriting Tier 1 core facts.
- Preserve evidence IDs for patterns.
- Prefer compression and archival over removal.

## File map

- Full protocol: `BIMRI-PROTOCOL.md`
- Active memory: `bimri.md`
- State file: `.bimri/state.json`
- State template: `BIMRI-STATE.template.json`
- Memory template: `BIMRI-MEMORY.template.md`
- Inbox: `.bimri/inbox/`
- Archive: `.bimri/archive/`
