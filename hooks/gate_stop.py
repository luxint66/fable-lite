#!/usr/bin/env python3
"""fable-lite verification gate (Stop hook).

Makes the skill's "check that can fail" rule *binding* instead of advisory.
When the current turn produced work (an Edit/Write/NotebookEdit) but no failable
check ran afterward, this blocks the stop and sends the model back to verify.

Contract (Claude Code Stop hook):
  - stdin: JSON with `transcript_path` and `stop_hook_active`.
  - stdout: `{"decision":"block","reason":...}` sends `reason` back to the model.
            Anything else (or exit 0 with no output) lets the turn end.
  - Fail-open: on any error we allow the stop. The gate must never wedge a session.

Scope: fires on ANY session by content signal (work-without-check), not by a
skill marker. If that's too eager for you, gate it behind an env var — see the
FABLE_LITE_GATE check below.
"""
import json
import os
import re
import sys
from typing import NoReturn

# --- what counts as "produced work" (the thing that must be verified) ---
MUTATING_TOOLS = {"Edit", "Write", "NotebookEdit"}

# --- what counts as a failable check running AFTER the last edit ---
# Bash commands that exercise the code with a pass/fail outcome.
CHECK_CMD = re.compile(
    r"\b("
    r"pytest|unittest|nose|tox|"
    r"npm\s+(test|run)|yarn\s+(test|run)|pnpm\s+(test|run)|"
    r"jest|vitest|mocha|"
    r"go\s+test|cargo\s+(test|build|check|clippy)|"
    r"make\b|cmake|"
    r"tsc\b|eslint|ruff|flake8|mypy|pyright|pylint|"
    r"python[0-9.]*\s+-m\s+\w|"
    r"gradle|mvn\b|"
    r"\bbuild\b|\blint\b|\btypecheck\b|\bverify\b"
    r")",
    re.IGNORECASE,
)
# Subagent delegations that carry their own failable check.
CHECK_AGENT = re.compile(r"verify-lite|edit-lite", re.IGNORECASE)
# The skill's sanctioned escape hatch: model may ship if it says so out loud.
UNVERIFIED = re.compile(r"\bUNVERIFIED\b", re.IGNORECASE)

BLOCK_REASON = (
    "fable-lite gate: this turn edited files but no failable check ran afterward. "
    "Before finishing, do ONE of:\n"
    "  1. Run a check that can actually fail on the change you just made — a test, "
    "build, lint, or a real run of the affected path (e.g. pytest / npm test / tsc "
    "/ the app itself), and report the actual pass/fail output; or\n"
    "  2. Delegate that check to verify-lite; or\n"
    "  3. If no failable check is possible here, say so explicitly and mark the "
    "output UNVERIFIED, naming the check that was impossible and why.\n"
    "\"I reviewed it and it looks right\" is not a check."
)


def allow() -> NoReturn:
    """Let the turn end."""
    sys.exit(0)


def block(reason) -> NoReturn:
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def walk_blocks(content):
    """Yield content blocks from a message.content (str or list of dicts)."""
    if isinstance(content, list):
        for b in content:
            if isinstance(b, dict):
                yield b


def is_human_prompt(ev):
    """A real user turn boundary — not a tool_result carrier."""
    if ev.get("type") != "user":
        return False
    content = ev.get("message", {}).get("content")
    if isinstance(content, str):
        return True
    # list form: a human prompt has no tool_result blocks
    return not any(b.get("type") == "tool_result" for b in walk_blocks(content))


def main():
    # Optional opt-in: if FABLE_LITE_GATE is set and not "1"/"on"/"true", stay dormant.
    flag = os.environ.get("FABLE_LITE_GATE")
    if flag is not None and flag.lower() not in ("1", "on", "true", "yes"):
        allow()

    try:
        payload = json.load(sys.stdin)
    except Exception:
        allow()

    # Never loop: if we already sent the model back once, let it stop.
    if payload.get("stop_hook_active"):
        allow()

    path = payload.get("transcript_path")
    if not path or not os.path.exists(path):
        allow()

    try:
        events = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        allow()

    # Scope assessment to the current turn: everything after the last human prompt.
    boundary = 0
    for i, ev in enumerate(events):
        if is_human_prompt(ev):
            boundary = i
    turn = events[boundary:]

    # Walk the turn in order; track the last edit and any check that follows it.
    last_edit_at = -1
    check_after_edit = False
    idx = 0
    for ev in turn:
        if ev.get("type") != "assistant":
            # tool_result / user side carries no tool_use; skip for signal purposes
            # but still advance the index so ordering stays monotonic.
            idx += 1
            continue
        for b in walk_blocks(ev.get("message", {}).get("content")):
            btype = b.get("type")
            if btype == "tool_use":
                name = b.get("name", "")
                raw_input = json.dumps(b.get("input", {}))
                if name in MUTATING_TOOLS:
                    last_edit_at = idx
                    check_after_edit = False  # a new edit invalidates a prior check
                elif name == "Bash" and CHECK_CMD.search(raw_input):
                    if last_edit_at >= 0:
                        check_after_edit = True
                elif name in ("Task", "Agent") and CHECK_AGENT.search(raw_input):
                    if last_edit_at >= 0:
                        check_after_edit = True
            elif btype == "text":
                if last_edit_at >= 0 and UNVERIFIED.search(b.get("text", "")):
                    check_after_edit = True
            idx += 1

    if last_edit_at >= 0 and not check_after_edit:
        block(BLOCK_REASON)
    allow()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Absolute backstop: any unexpected failure must not wedge the session.
        sys.exit(0)
