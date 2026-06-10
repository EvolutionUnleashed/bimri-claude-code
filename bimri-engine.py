#!/usr/bin/env python3
"""
BIMRI Engine v4
The deterministic layer of the BIMRI memory protocol.

The engine owns arithmetic: run counting, decay math, cap enforcement,
orphan detection, index building, and safe archival. Judgment about what
matters and how to compress it stays with the agent. The protocol works
without this engine in degraded mode; with it, memory maintenance becomes
machinery instead of model discipline.

Stdlib only. No dependencies. Python 3.8+.

Commands:
  start     Begin a run. Counts it, scans for orphans and decay, performs
            safe mechanical archival, opens the run log, prints a brief.
  close     End a run. Stamps closure, enforces hard caps, rebuilds index.
  status    Report sizes, cap usage, and run outcome statistics.
  index     Rebuild .bimri/index.tsv from hot memory, logs, and archive.
  maintain  Print a maintenance brief and perform safe mechanical archival.

Wiring:
  Claude Code hooks:  SessionStart -> start, SessionEnd -> close
  Cron:               python3 bimri-engine.py start && <agent command> ; \
                      python3 bimri-engine.py close
  Use ';' before close, never '&&', so closure runs even when the agent dies.

Safety: the engine never hard-deletes memory. Archival moves lines to
.bimri/archive/YYYY-MM.md with provenance stamps. Hot memory is backed up
to .bimri/backups/ before any modification.
"""

import json
import re
import shutil
import sys
import datetime as dt
from pathlib import Path

ROOT = Path.cwd()
BDIR = ROOT / ".bimri"
HOT = ROOT / "bimri.md"
STATE_F = BDIR / "state.json"
LOG_D = BDIR / "log"
ARC_D = BDIR / "archive"
INB_D = BDIR / "inbox"
BAK_D = BDIR / "backups"
INDEX_F = BDIR / "index.tsv"

DEFAULT_STATE = {
    "bimri_version": "4.0",
    "project_id": "unset",
    "cadence_class": "interactive",  # interactive | daily_cron | hourly_cron
    "run_count": 0,
    "current_run_id": "R000",
    "last_started_at": None,
    "last_closed_at": None,
    "last_maintenance_run": 0,
    "maintenance_mode": "warn",      # ask | warn | auto
    "prune_policy": "archive_only",
    "tier1_max": 12,
    "tier2_max": 20,
    "tier2_hard": 26,
    "tier3_max": 8,
    "flag_threshold": 0.5,           # below this: judgment brief
    "auto_archive_threshold": 0.2,   # below this AND I<=2: mechanical archive
    "run_dates": {},                 # run_id -> ISO date, trimmed
    "orphans_stamped": [],
}

# Freshness multipliers. The lower of the two applicable multipliers wins.
# Cadence class selects which table dominates: interactive projects decay
# by wall-clock days, cron agents decay by runs at a rate scaled to their
# run frequency.
DECAY_DAYS = [
    (1, 1.0), (3, 0.8), (5, 0.5), (10, 0.35), (15, 0.2), (20, 0.15), (10**9, 0.1)
]
DECAY_RUNS = {
    "interactive": [(1, 1.0), (3, 0.8), (5, 0.5), (10, 0.35), (10**9, 0.2)],
    "daily_cron":  [(2, 1.0), (6, 0.8), (12, 0.5), (24, 0.35), (10**9, 0.2)],
    "hourly_cron": [(24, 1.0), (72, 0.8), (168, 0.5), (336, 0.35), (10**9, 0.2)],
}

TIER2_RE = re.compile(
    r'^\[(?P<id>R\d+-E\d+)\]\s+\[I:(?P<imp>[1-5])\]\s+\[(?P<status>active|watch|closed|decision)\]'
    r'\s+\[F:(?P<first>R\d+)\]\s+\[L:(?P<last>R\d+)\]\s+\[(?P<tags>[^\]]*)\]'
    r'\s+(?P<text>.+?)(?:\s+->\s+(?P<ptr>\S+))?\s*$'
)
TIER1_RE = re.compile(
    r'^\[(?P<id>R\d+-E\d+)\]\s+\[(?P<kind>decision|fact|pref|rule)\]\s+\[(?P<tags>[^\]]*)\]'
    r'\s+(?P<text>.+?)(?:\s+->\s+(?P<ptr>\S+))?\s*$'
)
PATTERN_RE = re.compile(
    r'^\[(?P<id>P\d+)\]\s+\[(?P<conf>emerging|developing|established)\]\s+\[obs:(?P<obs>\d+)\]'
    r'\s+\[ev:(?P<ev>[^\]]*)\]\s+(?P<text>.+?)\s*$'
)

HOT_TEMPLATE = """# BIMRI Memory

<!-- BIMRI v4 | Headlines and pointers only. Full detail lives in .bimri/log/ -->
<!-- Engine: bimri-engine.py | Protocol: BIMRI-PROTOCOL.md | State: .bimri/state.json -->

## Tier 1: Core Intelligence

<!-- Durable facts, decisions, constraints, preferences. One line each. Cap: 12. -->
<!-- Format: [Rnnn-Enn] [decision|fact|pref|rule] [tags] text -->

## Tier 2: Active Context

<!-- Open loops, current state, risks, next actions. One line each. Cap: 20. -->
<!-- Format: [Rnnn-Enn] [I:n] [active|watch|closed] [F:Rnnn] [L:Rnnn] [tags] headline -> log/Rnnn.md -->

## Tier 3: Pattern Recognition

<!-- Evidence-backed patterns. Cap: 8. No evidence IDs, no pattern. -->
<!-- Format: [Pnnn] [emerging|developing|established] [obs:n] [ev:ID,ID] hypothesis | Falsify: condition -->

<!-- END BIMRI -->
"""


def now_iso():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today():
    return dt.date.today().isoformat()


def ensure_layout():
    for d in (BDIR, LOG_D, ARC_D, INB_D, BAK_D):
        d.mkdir(parents=True, exist_ok=True)
    if not HOT.exists():
        HOT.write_text(HOT_TEMPLATE, encoding="utf-8")


def load_state():
    state = dict(DEFAULT_STATE)
    if STATE_F.exists():
        try:
            state.update(json.loads(STATE_F.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            print("BIMRI: state.json unreadable, rebuilding from defaults "
                  "(memory files untouched).")
    return state


def save_state(state):
    if len(state.get("run_dates", {})) > 200:
        keep = sorted(state["run_dates"], key=run_num)[-200:]
        state["run_dates"] = {k: state["run_dates"][k] for k in keep}
    STATE_F.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def run_num(run_id):
    m = re.search(r"\d+", run_id or "")
    return int(m.group()) if m else 0


def lookup(table, value):
    for limit, mult in table:
        if value <= limit:
            return mult
    return table[-1][1]


def parse_hot():
    """Return (lines, tier_of_line_index, entries) for the hot file."""
    lines = HOT.read_text(encoding="utf-8").splitlines()
    tier = 0
    tiers = {}
    entries = []
    for i, line in enumerate(lines):
        low = line.strip().lower()
        if low.startswith("## tier 1"):
            tier = 1
        elif low.startswith("## tier 2"):
            tier = 2
        elif low.startswith("## tier 3"):
            tier = 3
        tiers[i] = tier
        if tier == 2:
            m = TIER2_RE.match(line.strip())
            if m:
                entries.append({"tier": 2, "line": i, **m.groupdict()})
        elif tier == 1:
            m = TIER1_RE.match(line.strip())
            if m:
                entries.append({"tier": 1, "line": i, **m.groupdict()})
        elif tier == 3:
            m = PATTERN_RE.match(line.strip())
            if m:
                entries.append({"tier": 3, "line": i, **m.groupdict()})
    return lines, tiers, entries


def composite(entry, state):
    """importance x freshness, freshness = lower of day and run multipliers."""
    imp = int(entry.get("imp", 3))
    cur = run_num(state["current_run_id"])
    runs_since = max(0, cur - run_num(entry.get("last", "R0")))
    run_mult = lookup(DECAY_RUNS.get(state["cadence_class"],
                                     DECAY_RUNS["interactive"]), runs_since)
    last_date = state.get("run_dates", {}).get(entry.get("last", ""))
    if last_date:
        days = max(0, (dt.date.today() - dt.date.fromisoformat(last_date)).days)
        day_mult = lookup(DECAY_DAYS, days)
    else:
        day_mult = run_mult  # no date on record, lean on run distance alone
    return imp * min(day_mult, run_mult)


def backup_hot():
    if HOT.exists():
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(HOT, BAK_D / f"bimri-{stamp}.md")
        baks = sorted(BAK_D.glob("bimri-*.md"))
        for old in baks[:-20]:
            old.unlink()


def archive_lines(lines, idx_to_drop, reason, state):
    """Move selected hot-file lines into the monthly archive. Never deletes."""
    if not idx_to_drop:
        return lines
    backup_hot()
    arc = ARC_D / f"{dt.date.today():%Y-%m}.md"
    stamp = f"[ARCHIVED:{state['current_run_id']} {today()}]"
    with arc.open("a", encoding="utf-8") as f:
        for i in sorted(idx_to_drop):
            f.write(f"{stamp} [{reason.get(i, 'mechanical')}] {lines[i].strip()}\n")
    kept = [l for i, l in enumerate(lines) if i not in idx_to_drop]
    HOT.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return kept


def mechanical_pass(state):
    """Archive only the unambiguous: closed entries and deeply decayed minor
    ones. Anything debatable is flagged for the agent, never auto-moved."""
    lines, tiers, entries = parse_hot()
    drop, reason, flagged = set(), {}, []
    for e in entries:
        if e["tier"] != 2:
            continue
        w = composite(e, state)
        if e["status"] == "closed":
            drop.add(e["line"]); reason[e["line"]] = "status:closed"
        elif w <= state["auto_archive_threshold"] and int(e["imp"]) <= 2:
            drop.add(e["line"]); reason[e["line"]] = f"decayed w={w:.2f} I{e['imp']}"
        elif w < state["flag_threshold"] and e["status"] != "decision":
            flagged.append((e["id"], e["imp"], w, e["text"][:70]))
    archived = [reason[i] + " " + lines[i].strip()[:60] for i in sorted(drop)]
    if drop:
        archive_lines(lines, drop, reason, state)
    return archived, flagged


def cap_report(state):
    _, _, entries = parse_hot()
    c = {1: 0, 2: 0, 3: 0}
    for e in entries:
        c[e["tier"]] += 1
    return c


def enforce_hard_caps(state):
    """Past the hard cap, archive Tier 2 entries down to the soft cap.
    Mechanical removal only ever touches minor entries (I<=3) or entries
    already decayed below the flag threshold. A healthy I:4 or I:5 is never
    archived by arithmetic; if protected entries alone exceed the cap, the
    engine reports the overflow and leaves judgment to the agent."""
    lines, tiers, entries = parse_hot()
    t2 = [e for e in entries if e["tier"] == 2]
    if len(t2) <= state["tier2_hard"]:
        return []
    for e in t2:
        e["_w"] = composite(e, state)
    candidates = [e for e in t2
                  if int(e["imp"]) <= 3 or e["_w"] < state["flag_threshold"]]
    candidates.sort(key=lambda e: e["_w"])
    n_drop = min(len(candidates), len(t2) - state["tier2_max"])
    drop = {e["line"] for e in candidates[:n_drop]}
    reason = {e["line"]: f"hard-cap w={e['_w']:.2f}" for e in candidates[:n_drop]}
    archive_lines(lines, drop, reason, state)
    if len(t2) - n_drop > state["tier2_hard"]:
        print(f"BIMRI: Tier 2 still over hard cap after archiving candidates; "
              f"{len(t2) - n_drop} protected high-importance entries remain. "
              f"Promote durable ones to Tier 1 or close stale ones.")
    return [e["id"] for e in candidates[:n_drop]]


def open_run_log(state, mode):
    log = LOG_D / f"{state['current_run_id']}.md"
    if not log.exists():
        log.write_text(
            f"# Run {state['current_run_id']} | {now_iso()} | {mode}\n\n"
            f"## Journal\n\n"
            f"<!-- Append [ID:{state['current_run_id']}-Enn] entries as decisions "
            f"happen. Write ahead, never reconstruct. -->\n\n"
            f"## Outcome\n\n"
            f"<!-- Close with: [OUTCOME:success|partial|overflow|fail] one line why -->\n",
            encoding="utf-8")
    return log


def find_orphans(state):
    cur = state["current_run_id"]
    orphans = []
    for log in sorted(LOG_D.glob("R*.md")):
        rid = log.stem
        if rid == cur or rid in state.get("orphans_stamped", []):
            continue
        if "[CLOSED:" not in log.read_text(encoding="utf-8"):
            orphans.append(rid)
    return orphans[-3:]  # surface only the most recent few


def stamp_orphans(state):
    stamped = []
    for log in sorted(LOG_D.glob("R*.md")):
        rid = log.stem
        if rid == state["current_run_id"]:
            continue
        text = log.read_text(encoding="utf-8")
        if "[CLOSED:" not in text:
            with log.open("a", encoding="utf-8") as f:
                f.write(f"\n[OUTCOME:overflow] run ended without closure, "
                        f"stamped by {state['current_run_id']}\n"
                        f"[CLOSED:{state['current_run_id']} {now_iso()} auto]\n")
            stamped.append(rid)
    state["orphans_stamped"] = sorted(
        set(state.get("orphans_stamped", []) + stamped))[-50:]
    return stamped


def est_tokens(path):
    return len(path.read_text(encoding="utf-8")) // 4 if path.exists() else 0


# ---------------------------------------------------------------- commands

def cmd_start(mode="interactive"):
    ensure_layout()
    state = load_state()
    state["run_count"] += 1
    state["current_run_id"] = f"R{state['run_count']:03d}"
    state["last_started_at"] = now_iso()
    state.setdefault("run_dates", {})[state["current_run_id"]] = today()

    orphans = find_orphans(state)
    archived, flagged = mechanical_pass(state)
    caps = cap_report(state)
    log = open_run_log(state, state["cadence_class"])
    inbox = len(list(INB_D.glob("*")))
    save_state(state)
    build_index(state)

    rid = state["current_run_id"]
    print(f"=== BIMRI BRIEF {rid} | {today()} | {state['cadence_class']} ===")
    print(f"Hot memory: ~{est_tokens(HOT)} tokens | "
          f"T1 {caps[1]}/{state['tier1_max']} "
          f"T2 {caps[2]}/{state['tier2_max']} "
          f"T3 {caps[3]}/{state['tier3_max']}")
    if archived:
        print("Archived mechanically (recoverable in .bimri/archive/):")
        for a in archived:
            print(f"  - {a}")
    needs = []
    if flagged:
        ids = ", ".join(f"{i}(I{imp},w={w:.2f})" for i, imp, w, _ in flagged)
        needs.append(f"{len(flagged)} Tier 2 entr{'y' if len(flagged)==1 else 'ies'} decayed below threshold: {ids}. "
                     f"For each: refresh [L:{rid}] if still live, or mark closed.")
    for rid_o in orphans:
        needs.append(f"Orphaned run {rid_o}: read the tail of .bimri/log/{rid_o}.md, "
                     f"journal anything durable to bimri.md, engine stamps closure at close.")
    if inbox:
        needs.append(f"Inbox holds {inbox} note(s) awaiting consolidation.")
    if caps[2] > state["tier2_max"]:
        needs.append(f"Tier 2 over soft cap ({caps[2]}/{state['tier2_max']}): "
                     f"compress or close the weakest entries.")
    if needs:
        print("JUDGMENT NEEDED:")
        for n in needs:
            print(f"  - {n}")
    print(f"Run log open: {log.relative_to(ROOT)} "
          f"(journal decisions as they happen; end with an [OUTCOME:] line)")
    print("=== END BRIEF ===")


def cmd_close():
    ensure_layout()
    state = load_state()
    rid = state["current_run_id"]
    log = LOG_D / f"{rid}.md"
    if log.exists():
        text = log.read_text(encoding="utf-8")
        if "[CLOSED:" not in text:
            with log.open("a", encoding="utf-8") as f:
                if "[OUTCOME:" not in text:
                    f.write("\n[OUTCOME:unrecorded] closed without an outcome line\n")
                f.write(f"[CLOSED:{rid} {now_iso()}]\n")
    stamped = stamp_orphans(state)
    dropped = enforce_hard_caps(state)
    state["last_closed_at"] = now_iso()
    save_state(state)
    build_index(state)
    msg = f"BIMRI: run {rid} closed."
    if stamped:
        msg += f" Stamped orphans: {', '.join(stamped)}."
    if dropped:
        msg += f" Hard cap enforced, archived: {', '.join(dropped)}."
    print(msg)


def build_index(state=None):
    ensure_layout()
    rows = []
    if HOT.exists():
        _, _, entries = parse_hot()
        for e in entries:
            rows.append([e.get("id", ""), f"T{e['tier']}",
                         e.get("status") or e.get("kind") or e.get("conf", ""),
                         e.get("imp", ""), e.get("first", ""), e.get("last", ""),
                         e.get("tags", "") or e.get("ev", ""),
                         "bimri.md", e.get("text", "")[:120]])
    for arc in sorted(ARC_D.glob("*.md")):
        for line in arc.read_text(encoding="utf-8").splitlines():
            m = re.search(r'\[(R\d+-E\d+|P\d+)\]', line)
            if m and line.startswith("[ARCHIVED:"):
                rows.append([m.group(1), "arc", "archived", "", "", "", "",
                             str(arc.relative_to(ROOT)), line[:120]])
    for log in sorted(LOG_D.glob("R*.md")):
        for line in log.read_text(encoding="utf-8").splitlines():
            m = re.match(r'\[ID:(R\d+-E\d+)\]', line.strip())
            if m:
                rows.append([m.group(1), "log", "detail", "", "", "", "",
                             str(log.relative_to(ROOT)), line.strip()[:120]])
    header = "id\tloc\tstatus\timp\tfirst\tlast\ttags\tfile\theadline\n"
    INDEX_F.write_text(
        header + "\n".join("\t".join(map(str, r)) for r in rows) + "\n",
        encoding="utf-8")
    return len(rows)


def cmd_status():
    ensure_layout()
    state = load_state()
    caps = cap_report(state)
    outcomes = {}
    for log in LOG_D.glob("R*.md"):
        m = re.search(r'\[OUTCOME:(\w+)\]', log.read_text(encoding="utf-8"))
        if m:
            outcomes[m.group(1)] = outcomes.get(m.group(1), 0) + 1
    total = sum(outcomes.values()) or 1
    print(f"BIMRI v{state['bimri_version']} | project {state['project_id']} | "
          f"cadence {state['cadence_class']} | run {state['current_run_id']}")
    print(f"Hot: ~{est_tokens(HOT)} tokens | T1 {caps[1]}/{state['tier1_max']} "
          f"T2 {caps[2]}/{state['tier2_max']} T3 {caps[3]}/{state['tier3_max']}")
    print(f"Logs: {len(list(LOG_D.glob('R*.md')))} | "
          f"Archive files: {len(list(ARC_D.glob('*.md')))} | "
          f"Inbox: {len(list(INB_D.glob('*')))} | "
          f"Index rows: {build_index(state)}")
    if outcomes:
        line = ", ".join(f"{k}: {v} ({100*v//total}%)"
                         for k, v in sorted(outcomes.items()))
        print(f"Run outcomes: {line}")


def cmd_maintain():
    ensure_layout()
    state = load_state()
    archived, flagged = mechanical_pass(state)
    state["last_maintenance_run"] = state["run_count"]
    save_state(state)
    build_index(state)
    print(f"BIMRI maintenance pass complete ({state['maintenance_mode']} mode, "
          f"archive-only).")
    for a in archived:
        print(f"  archived: {a}")
    if flagged:
        print("JUDGMENT NEEDED:")
        for i, imp, w, txt in flagged:
            print(f"  - {i} (I{imp}, w={w:.2f}): {txt}")
    if not archived and not flagged:
        print("  hot memory is clean.")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "start":
        cmd_start()
    elif cmd == "close":
        cmd_close()
    elif cmd == "status":
        cmd_status()
    elif cmd == "index":
        ensure_layout()
        print(f"BIMRI: index rebuilt, {build_index(load_state())} rows.")
    elif cmd == "maintain":
        cmd_maintain()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
