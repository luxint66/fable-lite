---
name: fable-lite
description: Work like Fable on the cheap — tiered delegation for codebase-heavy or token-heavy work. Use before writing or changing code, config, docs, or tests, and when a task spans multiple files, sources, or steps that can be offloaded. Opus keeps judgment, synthesis, and verification-of-record; cheaper pre-configured subagents do bounded scans, edits, and checks. Do NOT trigger on ordinary one-shot requests a direct attempt handles fine.
---

# fable-lite — tiered work routing

Route less-intensive, bounded work to cheaper subagents; keep judgment local.
Effort ceiling is **high** — never xhigh, never max.

Note: on a subscription plan, cheaper models do not save dollars. The win is
preserving Opus rate-limit/quota and speed. Delegate for that, not for cost.

Assumes an Opus main session. On Sonnet the boss-tier judgment drops a tier and
`work-lite`/`verify-lite` are same-tier — you keep context isolation and
parallelism but lose the tier savings.

## Keep local (Opus, this session)
- Debugging with an unknown cause, and exploratory probes decided as you go
- Decomposing ambiguous work into parallel slices
- Architecture / product / safety tradeoffs
- Reading conflicting subagent reports and deciding what's true (truth-judgment)
- Integrating partial work into one coherent result
- Final review, risk assessment, user-facing synthesis, commits and pushes
- **Tiny tasks:** if you can do the change plus its check in 1–2 tool calls,
  with the files already in context, just do it

## Code, config, docs and test changes — route by task type
Pick exactly one type, then pass the listed model as the Agent call's `model`
(it overrides the agent's default, so the table is the single source of truth).

| Type | Example | Agent | Model |
|---|---|---|---|
| docs | README, STATUS, comments | `edit-lite` | haiku |
| single-file-edit | a decided, mechanical change in one file | `edit-lite` | haiku |
| config | settings, cron, env, infra files | `edit-lite` | haiku |
| rename | rename / mechanical refactor | `edit-lite` | haiku |
| new-script | a new standalone script or tool | `work-lite` | haiku |
| multi-file-edit | a coordinated change across files | `work-lite` | sonnet |
| known-bug-fix | the cause is already identified | `work-lite` | sonnet |
| single-file-feature | one file, small judgment calls | `work-lite` | sonnet |
| tests | write/extend tests for known behavior | `work-lite` | sonnet |
| debug | cause unknown | keep on Opus | — |
| anything else | design, ambiguity, decisions the user must make | keep on Opus | — |

Why these models: see "Evidence" in the README. Haiku is trusted only where it
held up; it failed on coordinated multi-file work, so that stays on Sonnet.

- **Split, don't keep.** If a delegable task holds one judgment call, make that
  call here, then delegate the now-fully-specified rest. Keeping the whole task
  is right only when it is judgment all the way through. "It's one command" or
  "delegating costs more than doing it" are not reasons.
- **Brief** each subagent with: the goal, the exact files, constraints, and a
  pass/fail check it must run.
- **Commits stay here.** Tell the agent not to commit. After reviewing, stage
  and commit yourself. Agents tend to rewrite exact commit messages and
  trailers, which was the most common failure.

## Lookups — delegate freely (parallel when slices are independent)
| Work | Agent | Model / effort |
|---|---|---|
| Find pages / sources on the open web | `websearch-lite` | haiku |
| Fetch & distill ONE known URL | `webfetch-lite` | haiku |
| Local codebase scan, inventory, grep-summary | `scan-lite` | haiku / low |
| Independent verification, run tests, skeptical review | `verify-lite` | sonnet / high |

Delegation is **one level deep** — a subagent runs its slices sequentially and
does not spawn its own subagents, unless a sub-part clearly needs its own fan-out.

Bad delegation: splitting a single coherent thought just to use subagents.

## Verify with a check that can fail
Before delivering, each result needs a pass condition on an EXTERNAL artifact:
- a test that runs and passes
- a file or output that provably exists in the expected shape
- a source actually fetched and read, not assumed
- output diffed against the stated spec

For every delegated change, **also read the full diff — every line**, docs and
config included. Small models' typical slips are formatting: lines merged,
blank lines lost, literal tabs, wrapped continuations collapsed. A spot-check of
the top and bottom misses them.

"I reviewed it and it looks right" is not a check — a model that would skip
verification also passes its own introspection. If no failable check exists,
say so and mark the output **unverified**. If a late fix invalidates an earlier
stage, re-run that stage's check before continuing.

## Replan budget
At most two full replans per run. If a third structural replan seems necessary,
stop — the task is ambiguous at the requirements level, not the execution level;
surface it to the user instead of burning steps. (Renumbering or splitting one
stage is not a replan.)

## Effort
- Ceiling is **high**. Never use xhigh or max.
- Main-session effort is set by `effortLevel` in settings.
  Raise a heavy judgment session with `/effort high` when warranted; drop back
  after. Effort does not auto-adjust per task — the adjustment comes from
  sending less-intensive work to the lower-effort agents above.
- Subagent effort is fixed in each agent's frontmatter: `edit-lite` and
  `scan-lite` are low, `work-lite` and `verify-lite` are high.
