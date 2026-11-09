# fable-lite verification gate (Stop hook)

Makes the skill's **"check that can fail"** rule *binding* instead of advisory.

The skill already admits its own failure mode: a model will happily skip
verification and pass its own introspection ("I reviewed it and it looks right").
This hook closes that gap the way the `fablize` plugin does — with a `Stop` hook
that **refuses to end the turn** when work shipped without a real check.

## What it does

At the end of every turn, `gate_stop.py` reads the transcript and looks only at
the **current turn** (everything since your last prompt):

- If the turn **edited files** (`Edit` / `Write` / `NotebookEdit`) **and** a
  **failable check ran afterward** — a test/build/lint/run via `Bash`, a
  delegation to `verify-lite`/`edit-lite`, or the model explicitly writing
  `UNVERIFIED` — the turn ends normally.
- If it **edited files but no check followed** → the hook **blocks the stop** and
  sends the model back to run a real check (or mark the output `UNVERIFIED`).
- A check that ran *before* the last edit does **not** count — a late fix
  invalidates an earlier stage (the skill's own rule).
- **Read-only / exploratory turns are exempt** — no edit, no gate.

### Fail-safe by design

- Honors `stop_hook_active`: it blocks **at most once**, never loops.
- Any parse error, missing transcript, or unexpected exception → **allows the
  stop**. The gate can never wedge a session.

## Enable it

1. Copy the hook into your Claude Code config:

   ```sh
   mkdir -p ~/.claude/hooks
   cp hooks/gate_stop.py ~/.claude/hooks/
   ```

2. Add a `Stop` hook to `~/.claude/settings.json` (merge into existing `hooks`):

   ```json
   {
     "hooks": {
       "Stop": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "python3 ~/.claude/hooks/gate_stop.py",
               "timeout": 10
             }
           ]
         }
       ]
     }
   }
   ```

3. Restart Claude Code.

Requires **Python 3** (stdlib only — no packages). This is the only fable-lite
component that needs Python; the core skill + four agents remain zero-dependency.

## Tune / opt out

The gate fires on a **content signal** (work-without-check) on any session, not
on a skill marker. If that's too eager:

- **Opt-in switch:** set `FABLE_LITE_GATE=0` (or `off`/`false`) in the
  environment to keep the hook dormant; set `1`/`on`/`true` (or leave it unset)
  to run. Flip the default to opt-in by exporting `FABLE_LITE_GATE=0` globally
  and enabling per-project.
- **What counts as a check** lives in the `CHECK_CMD` / `CHECK_AGENT` regexes at
  the top of `gate_stop.py` — extend them for your stack (e.g. `phpunit`,
  `rspec`, a custom `./run-ci` script).
- **What counts as "work"** is `MUTATING_TOOLS`. Bash-only mutations (e.g. `sed`,
  `git commit`) are deliberately *not* gated to avoid false positives on
  data/exploratory turns.
