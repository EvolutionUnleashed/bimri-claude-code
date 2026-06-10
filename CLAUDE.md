@AGENTS.md

## Claude Code

Use `BIMRI-PROTOCOL.md` as the full BIMRI operating protocol.

If hooks are configured (see `hooks-example.json`), the engine briefs you automatically at session start and closes the run at session end; your only memory jobs are journaling into the run log as you work and resolving JUDGMENT NEEDED items. Without hooks, run `python3 bimri-engine.py start` as your first action.
