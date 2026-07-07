# claude-dispatch

Make [Claude Code](https://claude.com/claude-code) **work like Fable** — without
changing which model you run.

> **Requirements:** [Claude Code](https://claude.com/claude-code). The core skill
> and three agents have no other dependencies; the optional web agents need extra
> tools (see below).

## What is this, in plain language

"Fable mode" isn't a smarter model or a magic switch. It's a **working style**:
plan first, split the job up, hand the boring parts to cheaper helpers, and always
check your work with a test that can actually fail. Opus can follow that same
style — that's all this does. (You can't turn Opus *into* Fable; they're different
models. You can only make it *work like* Fable.)

This toolkit is that working style, packaged as four small files:

- **`dispatch`** — a rulebook for the main model. It says: break the task into
  steps, give the grunt work to cheap helpers, prove each result with a real
  check, and don't spin in circles (stop and ask after two failed re-plans).
- **`scan-lite`** — a cheap helper that *looks things up* in your code (searches
  files, maps where things live).
- **`edit-lite`** — a cheap helper that *makes small, exact edits* you've already
  decided on.
- **`verify-lite`** — a cheap helper that *runs the tests* and reports pass/fail
  honestly.

So the expensive model stays the "boss" doing the thinking, and the three helpers
do the legwork on cheaper, faster models. That division of labor plus the
"check that can fail" habit **is** the Fable-like behavior.

> Note: if you're on a Claude subscription, using cheaper helpers doesn't save
> money — the win is preserving your Opus usage limits and getting faster answers.

## How to install

Copy the files into your Claude Code config, then restart:

```sh
cp -r skills/dispatch  ~/.claude/skills/
cp    agents/*.md      ~/.claude/agents/
```

The skill works right away. The three helper agents **only load when Claude Code
starts**, so restart your session after copying. After that, `scan-lite`,
`edit-lite`, and `verify-lite` are available.

## How to use it

You don't flip a switch. It kicks in two ways:

- **Automatically** — on a big, multi-file or multi-step job, the main model
  reaches for `dispatch` on its own.
- **On demand** — just say *"use dispatch"* or *"delegate this"* and it follows
  the rulebook.

## Example

> **You:** In `src/`, find every file that still calls the old `fetch_prices`
> API and update it to the new `get_prices` signature.

With `dispatch` active, the main model doesn't do all of that itself — it
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

It's just four text files, so it copies anywhere:

```sh
git clone https://github.com/luxint66/claude-dispatch.git
cd claude-dispatch
cp -r skills/dispatch  ~/.claude/skills/
cp    agents/*.md      ~/.claude/agents/
# then restart Claude Code so the agents load
```

(A public repo clones over HTTPS with no credentials. If you keep the repo
private, the box needs an SSH key or token to clone.)

## Optional: web agents

The `dispatch` rulebook also mentions two web helpers — **`websearch-lite`** (find
pages) and **`webfetch-lite`** (fetch one URL). They're kept separate in
`optional-web-agents/` because, unlike the core three, they need external tools:
`webfetch-lite` needs the `agent-browser` CLI, and `websearch-lite` also needs the
included `exa_search.py` script plus your own `EXA_API_KEY`.

If you skip them, **nothing breaks** — Claude Code just doesn't have those two
agents and falls back to its built-in web tools. The core delegation
(`scan-lite` / `edit-lite` / `verify-lite`) works fully without them.

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

---

## Reference (technical details)

| Path | Role | Model / effort |
|---|---|---|
| `skills/dispatch/SKILL.md` | Routing rulebook: partition table, "check that can fail" rule, replan budget, effort ceiling | main session |
| `agents/scan-lite.md` | Local codebase scan / inventory / grep-summary | haiku, no effort |
| `agents/edit-lite.md` | Bounded, well-specified code edits | sonnet, effort: medium |
| `agents/verify-lite.md` | Independent verification with a failable check | sonnet, effort: high |

### Design notes

- **Effort is structural, not dynamic.** Claude Code can't self-select its own
  main-session effort per task — that dial is set by `effortLevel` in settings,
  `/effort <level>`, or `--effort`. The "adjustment" here comes from routing work
  to a pre-configured agent whose effort is baked in.
- **Effort ceiling is `high`** by convention — the skill forbids `xhigh`/`max`.
- **Haiku ignores effort**, so `scan-lite` omits the field. Only sonnet/opus
  honor it.
- The frontmatter key is `effort` (agents/skills); the settings.json key is the
  differently-named `effortLevel`.

## License

[MIT](LICENSE) © luxint66
