"""Behavioural tests for the fable-lite Stop-hook gate.

Runs the hook as a subprocess exactly as Claude Code does (JSON on stdin), and
asserts the block/allow decision across the cases the gate is meant to cover.
Stdlib + pytest only; each test builds its own transcript fixture in a tmp dir.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "gate_stop.py"

# --- transcript building blocks (JSONL lines) ---
HUMAN = {"type": "user", "message": {"content": "fix the bug in prices.py"}}
EDIT = {"type": "assistant", "message": {"content": [
    {"type": "text", "text": "editing"},
    {"type": "tool_use", "name": "Edit",
     "input": {"file_path": "prices.py", "old_string": "a", "new_string": "b"}},
]}}
TOOLRES = {"type": "user", "message": {"content": [
    {"type": "tool_result", "content": "ok"}]}}
BASH_TEST = {"type": "assistant", "message": {"content": [
    {"type": "tool_use", "name": "Bash", "input": {"command": "pytest tests/ -q"}}]}}
BASH_READ = {"type": "assistant", "message": {"content": [
    {"type": "tool_use", "name": "Bash", "input": {"command": "cat prices.py"}}]}}
UNVERIFIED_TXT = {"type": "assistant", "message": {"content": [
    {"type": "text", "text": "No harness here; marking UNVERIFIED (no tests)."}]}}
VERIFY_TASK = {"type": "assistant", "message": {"content": [
    {"type": "tool_use", "name": "Task",
     "input": {"subagent_type": "verify-lite", "prompt": "run the suite"}}]}}


def run_hook(tmp_path, events, stop_active=False, env=None):
    """Write a transcript, invoke the hook, return 'block' or 'allow'."""
    t = tmp_path / "transcript.jsonl"
    t.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    payload = json.dumps(
        {"transcript_path": str(t), "stop_hook_active": stop_active})
    proc = subprocess.run(
        [sys.executable, str(HOOK)], input=payload,
        capture_output=True, text=True, env=env)
    out = proc.stdout.strip()
    if out and json.loads(out).get("decision") == "block":
        return "block"
    return "allow"


@pytest.mark.parametrize("events, expected", [
    ([HUMAN, EDIT, TOOLRES], "block"),                       # edit, no check
    ([HUMAN, EDIT, TOOLRES, BASH_TEST], "allow"),            # edit then test
    ([HUMAN, EDIT, BASH_TEST, EDIT, TOOLRES], "block"),      # check invalidated by later edit
    ([HUMAN, BASH_READ], "allow"),                           # read-only, exempt
    ([HUMAN, EDIT, UNVERIFIED_TXT], "allow"),                # explicit UNVERIFIED escape
    ([HUMAN, EDIT, VERIFY_TASK], "allow"),                   # verify-lite delegation
])
def test_gate_decisions(tmp_path, events, expected):
    assert run_hook(tmp_path, events) == expected


def test_loopguard_allows_when_stop_hook_active(tmp_path):
    # Same unverified-edit transcript that blocks, but we already re-prompted once.
    assert run_hook(tmp_path, [HUMAN, EDIT, TOOLRES], stop_active=True) == "allow"


def test_fails_open_on_missing_transcript():
    payload = json.dumps(
        {"transcript_path": "/no/such/file.jsonl", "stop_hook_active": False})
    proc = subprocess.run(
        [sys.executable, str(HOOK)], input=payload, capture_output=True, text=True)
    assert proc.stdout.strip() == ""  # allow (no decision emitted)


def test_fails_open_on_malformed_transcript(tmp_path):
    t = tmp_path / "bad.jsonl"
    t.write_text('not json\n{"type":"user"\n')
    payload = json.dumps(
        {"transcript_path": str(t), "stop_hook_active": False})
    proc = subprocess.run(
        [sys.executable, str(HOOK)], input=payload, capture_output=True, text=True)
    assert proc.stdout.strip() == ""


def test_env_optout_stays_dormant(tmp_path):
    import os
    env = dict(os.environ, FABLE_LITE_GATE="0")
    # Would normally block (edit, no check); opt-out must allow.
    assert run_hook(tmp_path, [HUMAN, EDIT, TOOLRES], env=env) == "allow"
