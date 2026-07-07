# claude-dispatch

Tiered delegation for [Claude Code](https://claude.com/claude-code): keep judgment
on the expensive model, offload bounded work to cheaper pre-configured subagents.

A `dispatch` skill (the routing brain) plus three lightweight agents. The
orchestrator (Opus) keeps decomposition, tradeoffs, synthesis, and
verification-of-record; it hands scans, mechanical edits, and independent checks
to lower-tier agents whose model and effort are fixed in frontmatter.

> On a subscription plan, cheaper models don't save dollars — the win is
> preserving Opus rate-limit/quota and speed.

## What's here

| Path | Role | Model / effort |
|---|---|---|
| `skills/dispatch/SKILL.md` | Routing brain: partition table, "check that can fail" rule, replan budget, effort ceiling | main session |
| `agents/scan-lite.md` | Local codebase scan / inventory / grep-summary | haiku, no effort |
| `agents/edit-lite.md` | Bounded, well-specified code edits | sonnet, effort: medium |
| `agents/verify-lite.md` | Independent verification with a failable check | sonnet, effort: high |

## Design notes

- **Effort is structural, not dynamic.** Claude Code can't self-select its own
  main-session effort per task — that dial is set by `effortLevel` in settings,
  `/effort <level>`, or `--effort`. The "adjustment" here comes from routing work
  to a pre-configured agent whose effort is baked in.
- **Effort ceiling is `high`** by convention — the skill forbids `xhigh`/`max`.
- **Haiku ignores effort**, so `scan-lite` omits the field. Only sonnet/opus
  honor it.
- Frontmatter key is `effort` (agents/skills); the settings.json key is the
  differently-named `effortLevel`.

## Install (global)

```sh
cp -r skills/dispatch  ~/.claude/skills/
cp    agents/*.md      ~/.claude/agents/
```

Skills hot-load; **agents only register at Claude Code startup** — restart the
session after copying, then the `scan-lite` / `edit-lite` / `verify-lite` agent
types become available.
