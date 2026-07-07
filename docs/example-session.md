# Example session

A real run of `fable-lite` on a small multi-file task, showing how the main model
keeps the judgment and offloads the legwork to cheaper agents — and how nothing
is called "done" until a check that can fail has passed.

## The test project

A tiny `wordcount` toolkit where any new metric has to be threaded through several
files, so a change is genuinely multi-file and testable:

```
wordcount/
  reader.py     # read a file
  metrics.py    # one function per metric
  report.py     # assemble + format the metrics dict
  cli.py        # command-line entry point
tests/
  test_metrics.py
  test_report.py
```

## The kick-off prompt

> Add three new metrics to this project — average word length, unique word count,
> and longest-line length — each wired through metrics/report/CLI with its own
> tests. Also scan the whole project for any places a metric is referenced but not
> tested, and fix the gaps. All tests must pass.

No mention of the skill — this task is big enough (independent slices + a
project-wide scan) that `fable-lite` auto-triggered on its own.

## What fable-lite did

1. **Kept the one real design decision local (Opus).** The longest-line metric
   needs line structure that the words list throws away. Rather than hack around
   it, the main model settled the architecture itself: add `read_text(path)` to the
   reader and have `build_report(text)` derive both words and lines from the raw
   text — one file read, one source of truth, `read_words` kept as a thin
   backward-compatible wrapper.

2. **Delegated the legwork to cheaper agents:**

   | Stage | Agent | Job | Cost |
   |---|---|---|---|
   | 1 | `scan-lite` (haiku) | Inventory metric test-coverage gaps project-wide | 9.8k tokens · 19s |
   | 2 | `edit-lite` (sonnet) | Apply the exact metric spec + rewiring | 14.8k tokens · 30s |
   | 3 | `verify-lite` (sonnet) | Run pytest and drive the CLI end-to-end | 13.3k tokens · 32s |

   ~38k tokens of grunt work ran on haiku/sonnet — off the expensive model's
   budget. The two tasks in this demo together used ~1% of a weekly Opus
   allowance.

3. **Verified with checks that can fail.** `scan-lite` reported no pre-existing
   gaps (all original metrics were already tested) instead of manufacturing work;
   `verify-lite` ran the suite to `11/11 pass` and hand-checked the CLI arithmetic.

## The result (independently re-verified)

`11 passed`. On a known 3-line input:

```
$ printf 'the quick brown\nfox the\nlazy dog\n' > known.txt
$ python -m wordcount.cli known.txt
words: 7
chars: 26
longest: quick
avg_word_length: 3.7
unique_words: 6        # "the" deduped: 7 tokens -> 6 distinct
longest_line: 15       # "the quick brown"
```

Every value matches a by-hand calculation. Empty input returns all zeros with no
crash.

## What to notice

- The **breaking change was handled**: changing `build_report`'s signature rippled
  to two call sites (`cli.py`, `test_report.py`); both were updated, and the strict
  key-set test was *tightened* to the new keys rather than weakened to stay green.
- The **division of labor is the point**: Opus spent its expensive budget on the
  design decision and orchestration; the mechanical scanning, editing, and
  verification ran on cheaper models.
- Nothing was declared done on "looks right" — only on a test that actually ran.
