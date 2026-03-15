# BIMRI Protocol for Claude Code

> Brief Interaction Memory and Retrieval Intelligence — v2.0-cc
> Persistent, scored, self-maintaining memory for Claude Code sessions.

## Relationship to Auto Memory

Claude Code has built-in auto memory (MEMORY.md + topic files). BIMRI does not replace it. Auto memory captures granular technical notes — build commands, debugging fixes, code style preferences. BIMRI captures higher-order intelligence — project purpose, strategic context, work patterns, and behavioral insights. They complement each other. Leave auto memory enabled.

## Session Start Protocol

1. Check for `bimri.md` in the project root.
2. If found, read it before doing any work. Use it as session context.
3. If not found, create `bimri.md` using the template structure below. Ask the user 3–5 quick orientation questions: what this project is for, primary focus, preferences for working together, and any constraints. If the user wants to skip and get to work, respect that and populate from what you learn during the session.
4. Seed Tier 1 with intake answers scored at IMPORTANCE:5.

### Template Structure for New bimri.md Files

```markdown
<!-- BIMRI v2.0-cc | Last Maintained: YYYY-MM-DD | Sessions: 0 | Token Est: ~200 -->
<!-- Maintenance Due: After 10 sessions or when token estimate exceeds 6,000 -->

# BIMRI Memory

## Tier 1: Core Intelligence
<!-- Permanent foundational knowledge. Budget: ~1,500 tokens. No decay. -->
<!-- Only IMPORTANCE:4 or IMPORTANCE:5 entries belong here. -->

## Tier 2: Active Context
<!-- Current work state. Budget: ~3,000 tokens. Freshness decays per lookup table. -->
<!-- Ordered by composite weight (highest first). Archive threshold: 1.5 -->

## Tier 3: Pattern Recognition
<!-- Derived behavioral insights. Budget: ~1,500 tokens. Confidence-scored. -->
<!-- EMERGING (1-2 obs) | DEVELOPING (3-5 obs) | ESTABLISHED (6+ obs) -->

<!-- END BIMRI -->
```

## Freshness Lookup Table

Do not calculate decay. Read this table.

| Days Since Entry | Freshness Multiplier |
|-----------------|---------------------|
| 0–1             | 1.0                 |
| 2–3             | 0.8                 |
| 4–5             | 0.5                 |
| 6–10            | 0.35                |
| 11–15           | 0.2                 |
| 16–20           | 0.15                |
| 21+             | 0.1                 |

**Composite weight** = Importance × Freshness Multiplier

**Floor rule:** Entries with IMPORTANCE:4 or IMPORTANCE:5 have a minimum composite weight of 4.0 regardless of age.

**Archive threshold:** Composite weight below 1.5 = flagged for removal at next maintenance.

## During the Session

Work normally. Track anything worth recording: tasks completed, decisions made, preferences revealed, new context learned, recurring behaviors observed.

## Session End Protocol

This is mandatory. Update bimri.md as your final action before the session ends.

**Step 0 — Backup.** Copy `bimri.md` to `bimri-backup.md` in the same directory. Overwrite any existing backup.

**Step 1 — Write new entry.** Append a summary to Tier 2 (Active Context) using this format:

```
[IMPORTANCE:X] [TIMESTAMP:YYYY-MM-DD] [TAGS:relevant,tags] [WEIGHT:X.X]
One-line summary of the task and its outcome.
```

**Importance scoring guide:**
- 5 = Foundational — changes how every future session should work. Example: "This project is a CLI tool for generating invoice PDFs."
- 4 = Significant — major deliverable completed, key architectural decision made. Example: "Migrated database layer from SQLite to PostgreSQL."
- 3 = Notable — useful context for upcoming sessions. Example: "Added unit tests for the auth module, 94% coverage."
- 2 = Minor — helpful but short-lived. Example: "Fixed a typo in the config loader."
- 1 = Transient — operational detail, likely irrelevant within days. Example: "Ran lint pass, no issues."

**Step 2 — Recalculate weights.** Update composite weights for all Tier 2 entries using the freshness lookup table.

**Step 3 — Reorder.** Sort Tier 2 entries by composite weight, highest first.

**Step 4 — Prune.** Remove any entry whose composite weight has dropped below 1.5. Before deleting, check if it contributes to a pattern in Tier 3. If so, update the pattern's observation count.

**Step 5 — Detect patterns.** Review Tier 2 for recurring behaviors, preferences, or outcomes. If a pattern is new, add it to Tier 3 as EMERGING. If it matches an existing pattern, increment the observation count and update confidence level.

**Step 6 — Budget check.** Estimate the total token count of bimri.md. If it exceeds ~6,000 tokens, compress Tier 2 entries (merge related items, tighten language) and prune aggressively.

**Step 7 — Update metadata.** Increment the session counter and update the "Last Maintained" date in the file header.

**Step 8 — Confirm.** Tell the user: "BIMRI updated." If any entries were pruned or patterns changed, mention it briefly.

## Deep Maintenance (Every 10th Session)

On every 10th session (check the session counter), perform a full maintenance pass:

- Review all Tier 1 entries for accuracy. Remove or update anything that has changed.
- Merge redundant Tier 2 entries.
- Recalibrate all composite weights.
- Review Tier 3 patterns: promote, merge, or remove based on current observation counts.
- Clean up orphaned or unused tags.
- Compress the entire file to stay within budget.
- Report a brief summary of changes to the user.

## Manual Maintenance Trigger

If the user says "run BIMRI maintenance" or "clean up the memory file," execute the deep maintenance protocol regardless of the session counter.

## Rules

- When in doubt, record it. A low-importance entry that decays naturally costs almost nothing. A missed insight is gone forever.
- Never skip the session end protocol. If the session is ending abruptly, write at minimum a one-line Tier 2 entry.
- Tier 1 entries do not decay. They persist until explicitly updated or removed during deep maintenance.
- Tier 3 patterns are hypotheses until they reach ESTABLISHED status (6+ observations). Treat EMERGING patterns as signals, not facts.
- If bimri.md is corrupted or unreadable, check for bimri-backup.md first. If no backup exists, create a fresh file and note that history was lost.
- Do not duplicate information that auto memory already tracks well (build commands, linting configs, file paths). BIMRI is for project intelligence, not technical minutiae.

<!-- END BIMRI PROTOCOL -->
