# BIMRI for Claude Code

**Brief Interaction Memory and Retrieval Intelligence — v2.0-cc**

A structured, self-maintaining memory protocol for Claude Code that gives your agent persistent project intelligence across sessions.

---

## What This Is

Every Claude Code session starts with a fresh context window. Claude Code has two built-in mechanisms to carry knowledge forward: CLAUDE.md files (instructions you write) and auto memory (notes Claude writes itself via MEMORY.md).

Auto memory is good at capturing technical details — build commands, debugging fixes, code style preferences. What it doesn't do is score information by importance, decay stale context over time, recognize behavioral patterns, or self-maintain within a token budget.

BIMRI adds that layer. It's a structured memory file that lives in your project and tracks three types of intelligence:

- **Tier 1 — Core Intelligence:** Permanent foundational knowledge about the project. What it is, who it's for, hard constraints, strategic context. Never decays.
- **Tier 2 — Active Context:** Session summaries scored by importance and weighted by freshness. Recent, important work surfaces first. Old, low-value entries decay and get pruned automatically.
- **Tier 3 — Pattern Recognition:** Behavioral insights derived from accumulated sessions. Things like "user always refactors before adding features" or "test coverage is a priority on this project." Confidence-scored by observation count.

The result is an agent that starts every session already knowing what matters, what's current, and how you work.

---

## How It Works With Auto Memory

BIMRI and auto memory serve different purposes. Leave auto memory enabled.

| | Auto Memory | BIMRI |
|---|---|---|
| **What it captures** | Technical notes, build commands, debugging insights, code style | Project purpose, strategic decisions, work patterns, behavioral insights |
| **Who writes it** | Claude decides automatically | Claude follows the BIMRI protocol |
| **Structure** | Flat notes in MEMORY.md + topic files | Three-tier scored system with decay and maintenance |
| **Scoring** | None | Importance × Freshness composite weight |
| **Self-maintenance** | Claude manages MEMORY.md length | Pruning, compression, and deep maintenance every 10 sessions |
| **Where it lives** | `~/.claude/projects/<project>/memory/` | `bimri.md` in the project root |

Think of auto memory as short-term technical recall. BIMRI is long-term project intelligence.

---

## Setup

You need Claude Code installed and working. The setup takes about two minutes.

### Option A: Project-Level (Recommended)

This gives BIMRI to a single project. Best for most users.

1. Open your project in Claude Code.
2. Open or create the `CLAUDE.md` file in your project root.
3. Copy the contents of `BIMRI-PROTOCOL.md` from this repo.
4. Paste it into your `CLAUDE.md` file. If you already have content in CLAUDE.md, add BIMRI below your existing instructions.
5. Start a new Claude Code session. The agent will check for `bimri.md`, create one if it doesn't exist, and run a brief intake to seed the memory.

After your first session, your project will have:

```
your-project/
├── CLAUDE.md              ← Your instructions + BIMRI protocol
├── bimri.md               ← Memory file (created and maintained by Claude)
├── bimri-backup.md        ← Rolling backup (created before each write)
└── ...your project files
```

### Option B: Global (All Projects)

This gives BIMRI to every project you open in Claude Code.

1. Open or create `~/.claude/CLAUDE.md` (your user-level instructions file).
2. Paste the contents of `BIMRI-PROTOCOL.md` into it.
3. Every project you open from this point forward gets BIMRI automatically.

**Note:** Global deployment means every project generates its own `bimri.md` file. If you don't want BIMRI in a specific project, add a line to that project's CLAUDE.md: `Do not use BIMRI in this project.`

### Option C: Modular Rule

If you prefer to keep your CLAUDE.md clean:

1. Create `.claude/rules/bimri.md` in your project.
2. Paste the BIMRI protocol contents into that file.
3. Claude Code loads it automatically alongside your other rules.

---

## Adjusting Memory Size

The default BIMRI token budgets are tuned for typical projects:

| Tier | Default Budget | Purpose |
|------|---------------|---------|
| Tier 1 — Core Intelligence | ~1,500 tokens | Permanent project foundations |
| Tier 2 — Active Context | ~3,000 tokens | Session summaries with decay |
| Tier 3 — Pattern Recognition | ~1,500 tokens | Behavioral insights |
| **Total** | **~6,000 tokens** | Full memory file |

These budgets control how much context Claude reads at the start of every session. Bigger budgets mean more memory but more token cost per session. Smaller budgets mean leaner context but faster pruning.

### When to Go Smaller

If you're working on a simple, focused project — a single CLI tool, a small library, a personal script — the default budgets are probably too generous. Shrink them:

```
Tier 1: ~800 tokens
Tier 2: ~1,500 tokens
Tier 3: ~700 tokens
Total: ~3,000 tokens
```

To change: open `BIMRI-PROTOCOL.md` (or wherever you pasted the protocol) and edit the budget comments in the template structure section. Also update the budget check threshold in Step 6 of the session end protocol to match your new total.

### When to Go Bigger

If you're running a large monorepo, a multi-service architecture, or a project with complex domain context that Claude needs to understand deeply — you can expand:

```
Tier 1: ~2,500 tokens
Tier 2: ~5,000 tokens
Tier 3: ~2,500 tokens
Total: ~10,000 tokens
```

**Be aware:** Claude Code's CLAUDE.md files and memory are all loaded at session start. A 10,000-token BIMRI file on top of your CLAUDE.md instructions and auto memory means a larger baseline context before Claude does any work. For most users, the 6,000-token default is the right balance. Go bigger only if you're consistently losing important context to pruning.

### How to Change It

1. Open the BIMRI protocol in your CLAUDE.md (or `.claude/rules/bimri.md`).
2. Find the template structure section. Update the budget comments:
   ```
   <!-- Permanent foundational knowledge. Budget: ~1,500 tokens. No decay. -->
   ```
   Change `~1,500` to your desired budget.
3. Find **Step 6 — Budget check** in the session end protocol. Update the threshold:
   ```
   If it exceeds ~6,000 tokens, compress...
   ```
   Change `~6,000` to your new total.
4. Next session, tell Claude: "The BIMRI token budgets have changed. Run a maintenance pass to realign." Claude will rebalance the file to fit the new limits.

### Quick Reference

| Project Type | Suggested Total Budget |
|---|---|
| Small script or utility | ~3,000 tokens |
| Standard project (default) | ~6,000 tokens |
| Large or complex codebase | ~8,000–10,000 tokens |
| Monorepo with multiple services | ~10,000 tokens (consider per-directory bimri.md files) |

---

## Usage

Once BIMRI is set up, you don't need to do anything. The protocol runs automatically:

- **Session start:** Claude reads `bimri.md` and picks up where you left off.
- **During session:** Claude tracks tasks, decisions, and context internally.
- **Session end:** Claude writes a scored entry to `bimri.md`, recalculates weights, prunes stale entries, and confirms with "BIMRI updated."
- **Every 10th session:** Claude runs a deep maintenance pass — reviewing accuracy, merging redundant entries, updating pattern confidence, and compressing the file.

### Verifying It Works

After your second session in a project, ask Claude: "What do you know about this project so far?" It should summarize the contents of `bimri.md` including entries from previous sessions.

### Manual Maintenance

If the memory file feels bloated or stale, tell Claude:

```
Run BIMRI maintenance and compress aggressively.
```

Claude will execute the deep maintenance protocol regardless of the session counter.

### Editing the Memory File Directly

`bimri.md` is plain markdown. Open it in any editor and change whatever you want. Claude reads it fresh at the start of every session, so your edits take effect immediately.

### Adding BIMRI to .gitignore

The memory file contains project-specific context that may not be relevant to collaborators. Add these lines to your `.gitignore`:

```
bimri.md
bimri-backup.md
```

If you're working on a team and want shared project memory, commit `bimri.md` instead. Every team member's Claude Code sessions will read and contribute to the same memory file.

---

## Freshness Lookup Table

BIMRI uses a static lookup table instead of computed decay. This eliminates inconsistent math between sessions.

| Days Since Entry | Freshness Multiplier |
|-----------------|---------------------|
| 0–1             | 1.0                 |
| 2–3             | 0.8                 |
| 4–5             | 0.5                 |
| 6–10            | 0.35                |
| 11–15           | 0.2                 |
| 16–20           | 0.15                |
| 21+             | 0.1                 |

**Composite weight** = Importance Score × Freshness Multiplier

**Floor rule:** Any entry scored IMPORTANCE:4 or IMPORTANCE:5 has a minimum composite weight of 4.0, regardless of age. This prevents critical project context from decaying into irrelevance.

**Archive threshold:** Any entry with composite weight below 1.5 gets removed at the next maintenance cycle. Before removal, the agent checks whether the entry contributes to a Tier 3 pattern.

---

## Known Limitations

These are real and worth understanding before you deploy.

- **Agent compliance is probabilistic.** The protocol tells Claude what to do, but Claude interprets instructions, it doesn't execute them deterministically. The "BIMRI updated" confirmation exists so you can verify the write happened. If you don't see it, the session end protocol may have been skipped.
- **Importance scoring varies between sessions.** Each session is a fresh Claude instance reading the same instructions. What one session scores as importance 3, another might score as importance 4. The concrete examples in the protocol reduce this variance but don't eliminate it.
- **Token counting is estimated.** Claude doesn't have a precise token counter. Budget thresholds are approximate. The maintenance cycle catches drift over time.
- **Pattern recognition can hallucinate.** Tier 3 patterns are derived from written summaries, not from the actual sessions. Ambiguous entries can produce false patterns. The confidence scoring system mitigates this.
- **No cross-project intelligence.** Each project maintains independent memory. If you want to share context between projects, you'd need to manually copy relevant entries.
- **Session end can be missed.** If a session ends abruptly (crash, timeout, user closes terminal), the write may not happen. The backup file provides a rollback point for the previous good state.

---

## File Reference

| File | Purpose | Where It Goes |
|------|---------|---------------|
| `BIMRI-PROTOCOL.md` | The protocol — paste into your CLAUDE.md | Your CLAUDE.md or `.claude/rules/bimri.md` |
| `LICENSE` | MIT license | Repo root |
| `README.md` | This file | Repo root |

---

## Contributing

This is an active experiment. If you run into edge cases, inconsistent behavior, or have improvements, open an issue or submit a PR.

---

## Author

**Stu Jordan** — Agent Orchestrator
[evolutionunleashed.com](https://evolutionunleashed.com)

---

## License

MIT — see [LICENSE](LICENSE) for details.
