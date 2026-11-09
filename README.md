# fable-lite

Make [Claude Code](https://claude.com/claude-code) **work like Fable** — without
changing which model you run.

> **Requirements:** [Claude Code](https://claude.com/claude-code). The core skill
> and four agents have no other dependencies; the optional web agents need extra
> tools, and the optional verification gate needs Python 3 (see below).

## What is this, in plain language

"Fable mode" isn't a smarter model or a magic switch. It's a **working style**:
plan first, split the job up, hand the boring parts to cheaper helpers, and always
check your work with a test that can actually fail. Opus can follow that same
style — that's all this does. (You can't turn Opus *into* Fable; they're different
models. You can only make it *work like* Fable.)

This toolkit is that working style, packaged as five small files:

- **`fable-lite`** — a rulebook for the main model. It says: break the task into
  steps, give the grunt work to cheap helpers, prove each result with a real
  check, and don't spin in circles (stop and ask after two failed re-plans).
- **`scan-lite`** — a cheap helper that *looks things up* in your code (searches
  files, maps where things live).
- **`edit-lite`** — a cheap helper that *makes small, exact edits* you've already
  decided on.
- **`work-lite`** — a mid-price helper for *bounded jobs that need small
  decisions*: multi-file changes, new scripts, bugs whose cause is known.
- **`verify-lite`** — a cheap helper that *runs the tests* and reports pass/fail
  honestly.

So the expensive model stays the "boss" doing the thinking, and the four helpers
do the legwork on cheaper, faster models (on a subscription this conserves your
Opus limits and answers faster rather than lowering a fixed bill). That division
of labor plus the "check that can fail" habit **is** the Fable-like behavior.

## Why this exists

Fable had me excited — the discipline, the depth, the quality of the results.
What I wasn't excited about was paying a frontier price for every keystroke. So I
went looking for the halfway point, and this is where I landed: keep a capable
model as the decision-maker, and let cheaper models do the legwork it hands them.
Most of the quality, a fraction of the spend. Not a replacement for Fable — a
pragmatic middle ground for the rest of us.

## How to install

Copy the files into your Claude Code config, then restart:

```sh
cp -r skills/fable-lite  ~/.claude/skills/
cp    agents/*.md      ~/.claude/agents/
```

The skill works right away. The four helper agents **only load when Claude Code
starts**, so restart your session after copying. After that, `scan-lite`,
`edit-lite`, `work-lite` and `verify-lite` are available.

**Upgrading from an earlier version?** Copy the agents again: `edit-lite` now
runs on Haiku instead of Sonnet, and `work-lite` is new. Nothing else changes;
there are still no hooks, scripts or settings to install.

## How to use it

You don't flip a switch. It kicks in two ways:

- **Automatically** — on a big, multi-file or multi-step job, the main model
  reaches for `fable-lite` on its own.
- **On demand** — just say *"use fable-lite"* or *"delegate this"* and it follows
  the rulebook.

## Example

> **You:** In `src/`, find every file that still calls the old `fetch_prices`
> API and update it to the new `get_prices` signature.

With `fable-lite` active, the main model doesn't do all of that itself — it
orchestrates:

1. **Plans** the steps.
2. Sends **`scan-lite`** (cheap) to find every file that calls `fetch_prices`.
3. Sends **`edit-lite`** (cheap) to apply the signature change in each file.
4. Sends **`verify-lite`** to run the test suite and report **PASS/FAIL** — a
   check that can actually fail.
5. The main model reviews the results, fixes anything the tests caught, and
   reports back.

You get the same outcome, but the boring legwork ran on cheaper, faster helpers
instead of burning your Opus usage — and nothing is called "done" until a real
test passed.

For a full worked run on a real project — the actual delegation, token costs, and
verified output — see [`docs/example-session.md`](docs/example-session.md).

## Install on another machine

It's just five text files, so it copies anywhere:

```sh
git clone https://github.com/luxint66/fable-lite.git
cd fable-lite
cp -r skills/fable-lite  ~/.claude/skills/
cp    agents/*.md      ~/.claude/agents/
# then restart Claude Code so the agents load
```

(A public repo clones over HTTPS with no credentials. If you keep the repo
private, the box needs an SSH key or token to clone.)

## Optional: web agents

The `fable-lite` rulebook also mentions two web helpers — **`websearch-lite`** (find
pages) and **`webfetch-lite`** (fetch one URL). They're kept separate in
`optional-web-agents/` because, unlike the core four, they need external tools:
`webfetch-lite` needs the `agent-browser` CLI, and `websearch-lite` also needs the
included `exa_search.py` script plus your own `EXA_API_KEY`.

If you skip them, **nothing breaks** — Claude Code just doesn't have those two
agents and falls back to its built-in web tools. The core delegation
(`scan-lite` / `edit-lite` / `work-lite` / `verify-lite`) works fully without them.

### Activating the web agents on a box

```sh
# 1. Install agent-browser (needed by both web agents)
npm install -g agent-browser

# 2. Put the two agent files in place
cp optional-web-agents/websearch-lite.md \
   optional-web-agents/webfetch-lite.md   ~/.claude/agents/

# 3. websearch-lite only: install the Exa helper + your API key
mkdir -p ~/.config/agent-browser-lite
cp optional-web-agents/exa_search.py  ~/.config/agent-browser-lite/
cp optional-web-agents/env.example    ~/.config/agent-browser-lite/env
#   then edit ~/.config/agent-browser-lite/env and set your real key
#   (get one at https://exa.ai)

# 4. Restart Claude Code so the agents register
```

`webfetch-lite` works after steps 1, 2, and 4 (no Exa key needed).
`websearch-lite` needs all four steps.

**If agent-browser won't launch:** put `"--no-sandbox"` under the **top-level
`args`** in `~/.agent-browser/config.json` (it's ignored under `launchOptions`).
If it hangs on a stale daemon, `pkill -f hermes` and retry.

## Optional: the verification gate (Stop hook)

The rulebook's **"check that can fail"** rule is, on its own, *advice* — and the
skill itself admits a model will skip verification and pass its own introspection
("I reviewed it and it looks right"). The gate makes that rule **binding**.

`hooks/gate_stop.py` is a Claude Code **Stop hook**. At the end of each turn it
reads the transcript, and if the turn **edited files** (`Edit`/`Write`/
`NotebookEdit`) but **no failable check ran afterward** — a test/build/lint/run,
a `verify-lite`/`edit-lite` delegation, or an explicit `UNVERIFIED` note — it
**blocks the turn from ending** and sends the model back to verify. Read-only and
exploratory turns are exempt. It honors `stop_hook_active` (blocks at most once,
never loops) and fails open on any error, so it can never wedge a session.

It's kept separate from the core four because it needs **Python 3** (stdlib
only) and it's the one component that actively gates the session rather than just
advising. If you skip it, nothing breaks — the "check that can fail" rule simply
stays advisory. Enable it:

```sh
mkdir -p ~/.claude/hooks
cp hooks/gate_stop.py ~/.claude/hooks/
```

Then add a `Stop` hook to `~/.claude/settings.json` (merge into any existing
`hooks` block) and restart Claude Code:

```json
{
  "hooks": {
    "Stop": [
      { "hooks": [
        { "type": "command",
          "command": "python3 ~/.claude/hooks/gate_stop.py",
          "timeout": 10 }
      ] }
    ]
  }
}
```

The gate fires on a content signal (work-without-check) on **any** session, not
only when fable-lite is "active." To keep it dormant, set `FABLE_LITE_GATE=0` in
the environment; set `1`/`on`/`true` (or leave unset) to run. Full details,
tuning, and the check/work regexes are in [`hooks/README.md`](hooks/README.md).

---

## Evidence: which model gets which job

The routing table in the skill isn't a guess. It comes from about 1,100 real
coding tasks logged over six weeks across several machines and projects, with
an Opus main session judging each delegated result pass or fail (any Opus
rework counted as a fail):

| Task type | Haiku pass | Sonnet pass | Verdict |
|---|---|---|---|
| docs | 138 / 143 | 123 / 125 | Haiku |
| single-file-edit | 48 / 48 | 42 / 43 | Haiku |
| new-script | 39 / 40 | 66 / 68 | Haiku |
| config | 13 / 13 | 6 / 7 | Haiku |
| rename | 5 / 5 | 2 / 2 | Haiku (small sample, low risk) |
| multi-file-edit | 6 / 8 | 258 / 268 | Sonnet: Haiku failed 2 of 8 |
| known-bug-fix | — | 37 / 39 | Sonnet |
| single-file-feature | — | 46 / 47 | Sonnet |
| tests | 1 / 1 | 1 / 1 | Sonnet by default: too few runs to decide |
| debug (cause unknown) | — | — | Opus: almost always needs live judgment |

Results are for Haiku 5.5 and Sonnet 5.5. Two caveats:

- The pass/fail grades come from the same Opus session that wrote the brief. An
  independent check, whether a delegated commit was reverted or fixed within
  48 hours, found 4 reworked out of 186 commits it could see.
- Of the delegated failures, about a quarter were agents rewriting the exact
  commit message they were given and a third were formatting slips. Both are
  why the skill keeps commits on the main model and asks for a full diff read.

## Reference (technical details)

| Path | Role | Model / effort |
|---|---|---|
| `skills/fable-lite/SKILL.md` | Routing rulebook: partition table, "check that can fail" rule, replan budget, effort ceiling | main session |
| `agents/scan-lite.md` | Local codebase scan / inventory / grep-summary | haiku, effort: low |
| `agents/edit-lite.md` | Decided, mechanical edits (docs, one-file edits, config, renames) | haiku, effort: low |
| `agents/work-lite.md` | Bounded jobs with small judgment calls (multi-file edits, new scripts, known-cause fixes) | sonnet, effort: high (the skill passes haiku for new scripts) |
| `agents/verify-lite.md` | Independent verification with a failable check | sonnet, effort: high |
| `hooks/gate_stop.py` | Optional Stop-hook gate: blocks turn-end when a turn edited files but ran no failable check | Stop hook, Python 3 |

### Design notes

- **Effort is structural, not dynamic.** Claude Code can't self-select its own
  main-session effort per task — that dial is set by `effortLevel` in settings,
  `/effort <level>`, or `--effort`. The "adjustment" here comes from routing work
  to a pre-configured agent whose effort is baked in.
- **Effort ceiling is `high`** by convention — the skill forbids `xhigh`/`max`.
- **Per-task model.** The skill's routing table passes `model` on each Agent
  call, which overrides the agent's frontmatter default. So one `work-lite`
  agent serves both the Haiku and the Sonnet rows.
- The frontmatter key is `effort` (agents/skills); the settings.json key is the
  differently-named `effortLevel`.

## License

[MIT](LICENSE) © luxint66
