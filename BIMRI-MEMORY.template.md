# BIMRI Memory

<!-- BIMRI v2.1-ca | Active memory only. Not a diary. -->
<!-- State file: .bimri/state.json -->
<!-- Full protocol: BIMRI-PROTOCOL.md -->

## Tier 1: Core Intelligence

Permanent project facts, durable decisions, hard constraints, and user preferences.

Use only when the memory should affect most future sessions.

## Tier 2: Active Context

Current work state, open loops, unresolved risks, near-term next actions, and recently important outcomes.

Entry format:

```text
[ID:R001-E01] [I:3] [STATUS:active] [TTL:5r/14d] [FIRST:R001] [LAST:R001] [TAGS:example] [WEIGHT:3.0]
One concise sentence describing useful active context.
```

## Tier 3: Pattern Recognition

Evidence-backed patterns about the project, user preferences, or workflow.

Pattern format:

```text
[PATTERN:P001] [CONFIDENCE:emerging] [OBS:1] [EVIDENCE:R001-E01]
Pattern hypothesis.
Falsify if: clear condition that would disprove or weaken the pattern.
```

<!-- END BIMRI -->
