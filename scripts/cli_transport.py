#!/usr/bin/env python3
"""Tool-free grader calls through subscription CLIs, returned in the Anthropic-message shape used by closure_annotate.py.
claude-cli: `claude -p` (Claude Code CLI) with no tools, no settings, no session persistence, system prompt via flag, user text on stdin.
codex-cli:  `codex exec` (Codex CLI) in a read-only sandbox with web search disabled; system+user text on stdin; last agent message returned.
Both record the CLI's own metadata (model, usage/cost where exposed) in the response object. No credentials are handled here."""
from __future__ import annotations
import json, subprocess, time

def call_claude_cli(model: str, system: str, user: str, timeout: int = 1800) -> tuple[int, dict]:
    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--tools", "", "--setting-sources", "", "--no-session-persistence",
           "--disable-slash-commands", "--system-prompt", system]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, input=user, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 599, {"error": f"claude-cli timeout after {timeout}s"}
    if r.returncode != 0:
        return 500, {"error": (r.stderr or r.stdout)[:2000]}
    try: d = json.loads(r.stdout)
    except json.JSONDecodeError: return 502, {"error": "claude-cli returned non-JSON: " + r.stdout[:500]}
    text = d.get("result") or ""
    return 200, {"model": model, "cli": "claude", "cli_model_usage": d.get("modelUsage"), "usage": d.get("usage"), "stop_reason": d.get("stop_reason") or ("end_turn" if text else "empty"),
                 "num_turns": d.get("num_turns"), "duration_ms": d.get("duration_ms"), "is_error": d.get("is_error"), "elapsed_seconds": round(time.time() - t0, 1),
                 "content": [{"type": "text", "text": text}]}

def call_codex_cli(model: str, system: str, user: str, timeout: int = 1800, effort: str = "high") -> tuple[int, dict]:
    cmd = ["codex", "exec", "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only", "--model", model,
           "-c", f'model_reasoning_effort="{effort}"', "-c", "tools.web_search=false", "--json", "-"]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, input=system + "\n\n" + user, capture_output=True, text=True, timeout=timeout, cwd="/tmp")
    except subprocess.TimeoutExpired:
        return 599, {"error": f"codex-cli timeout after {timeout}s"}
    text, events, usage = "", [], None
    for line in r.stdout.splitlines():
        try: e = json.loads(line)
        except json.JSONDecodeError: continue
        events.append(e.get("type"))
        if e.get("type") == "item.completed" and (e.get("item") or {}).get("type") == "agent_message": text = e["item"].get("text") or text
        if e.get("type") == "turn.completed": usage = e.get("usage")
    if r.returncode != 0 and not text:
        return 500, {"error": (r.stderr or r.stdout)[:2000]}
    return 200, {"model": model, "cli": "codex", "reasoning_effort": effort, "usage": usage, "events": sorted(set(events)), "stop_reason": "end_turn" if text else "empty",
                 "elapsed_seconds": round(time.time() - t0, 1), "content": [{"type": "text", "text": text}]}
