# claude-dispatch

Make [Claude Code](https://claude.com/claude-code) **work like Fable** — without
changing which model you run.

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
