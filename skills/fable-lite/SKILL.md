---
name: fable-lite
description: Work like Fable on the cheap — tiered delegation for codebase-heavy or token-heavy work. Use when a task spans multiple files, sources, or steps and independent slices can be offloaded. Opus keeps judgment, synthesis, and verification-of-record; cheaper pre-configured subagents do bounded scans, edits, and checks. Do NOT trigger on ordinary one-shot requests a direct attempt handles fine.
---

# fable-lite — tiered work routing

Route less-intensive, bounded work to cheaper subagents; keep judgment local.
Effort ceiling is **high** — never xhigh, never max.

Note: on a subscription plan, cheaper models do not save dollars. The win is
preserving Opus rate-limit/quota and speed. Delegate for that, not for cost.

## Keep local (Opus, this session)
- Decomposing ambiguous work into parallel slices
- Architecture / product / safety tradeoffs
- Reading conflicting subagent reports and deciding what's true (truth-judgment)
- Integrating partial work into one coherent result
- Final review, risk assessment, user-facing synthesis
- Anything tiny, or where the validation itself needs delicate judgment

## Delegate to cheaper subagents (parallel when slices are independent)
| Work | Agent | Model / effort |
|---|---|---|
| Find pages / sources on the open web | `websearch-lite` | haiku |
| Fetch & distill ONE known URL | `webfetch-lite` | haiku |
| Local codebase scan, inventory, grep-summary | `scan-lite` | haiku |
| Bounded, well-specified code edits | `edit-lite` | sonnet / medium |
| Independent verification, run tests, skeptical review | `verify-lite` | sonnet / high |

Brief each subagent with: its specific task, what to produce, where to save
output, and the minimum prior context it needs. Delegation is **one level
deep** — a subagent runs its slices sequentially and does not spawn its own
subagents, unless a sub-part clearly needs its own fan-out.

Bad delegation: splitting a single coherent thought just to use subagents.

## Verify with a check that can fail
Before delivering, each result needs a pass condition on an EXTERNAL artifact:
- a test that runs and passes
- a file or output that provably exists in the expected shape
- a source actually fetched and read, not assumed
- output diffed against the stated spec

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
- Main-session effort is set by `effortLevel` in settings (currently medium).
  Raise a heavy judgment session with `/effort high` when warranted; drop back
  after. Effort does not auto-adjust per task — the adjustment comes from
  sending less-intensive work to the lower-effort agents above.
- Subagent effort is fixed in each agent's frontmatter: haiku takes none;
  `edit-lite` is medium; `verify-lite` is high.
