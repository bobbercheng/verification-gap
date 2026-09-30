#!/usr/bin/env python3
"""Witness discovery on disputed texts (protocol: artifacts/witness_discovery/PROTOCOL.md).

Subcommands
  cases                       build cases.json (ids, paths, sha256, groups) from the closure corpora
  propose --proposer gpt|claude [--workers N] [--only ID,...]
                              one call per text asking for obligation verdicts with witnesses (Claude CLI without tools;
                              Codex CLI in a read-only sandbox with web search disabled)
  check   --checker gpt|claude|glm [--workers N]
                              check every lower/upper witness this checker is responsible for
  baseline --grader gpt|claude  ordinary 0-7 coordinator grade with error list (same budget: one call per text)
  analyze [--freeze] [--root DIR]
                              results.json, RESULTS.md, the tables and gen/witness_macros.tex; offline. --root is a repository
                              root (DIR/artifacts/witness_discovery/) or a flat supplement (DIR/witness_discovery/); the macro
                              file is written only where DIR/gen/ exists.

Transports: scripts/cli_transport.py (Claude Code CLI, Codex CLI) and the Z.ai Anthropic-compatible API
for GLM-5.3 (closure_annotate.call). No credentials are printed; the GLM key is read from --key-file.
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, hashlib, json, pathlib, re, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
WD = ART / "witness_discovery"
GEN = ROOT / "gen"
SCRATCH = pathlib.Path("[local-path]")
sys.path.insert(0, str(ROOT / "scripts"))
# closure_annotate (RUBRIC for P3, call() for the GLM transport) and cli_transport are imported by the subcommands that make
# calls, so `analyze` runs offline from a supplement that ships neither module.


def case_bytes(case):
    """The case's text, from its recorded path when present, else the digest-identical copy tracked in the release."""
    p = pathlib.Path(case["path"])
    if p.exists():
        return p.read_bytes()
    import text_store as TS  # noqa: E402
    return TS.read_bytes(case["path"], case.get("sha256"))

def set_root(root) -> None:
    """--root DIR: a repository root (DIR/artifacts/witness_discovery/) or a flat supplement (DIR/witness_discovery/). The analysis
    reads and writes beside the retained responses; gen/witness_macros.tex is written only if DIR/gen/ exists."""
    global ROOT, ART, WD, GEN
    root = pathlib.Path(root).resolve()
    if (root / "artifacts" / "witness_discovery").is_dir(): ROOT, ART = root, root / "artifacts"
    elif (root / "witness_discovery").is_dir(): ROOT, ART = root, root
    else: sys.exit(f"--root {root}: found neither artifacts/witness_discovery/ nor witness_discovery/")
    WD, GEN = ART / "witness_discovery", root / "gen"

PROPOSERS = {"gpt": ("codex-cli", "gpt-5.6-sol"), "claude": ("claude-cli", "claude-opus-5")}
CHECKERS = {"gpt": ("codex-cli", "gpt-5.6-sol"), "claude": ("claude-cli", "claude-opus-5"), "glm": ("anthropic", "glm-5.3")}
CHECKS_FOR = {"gpt": ("claude", "glm"), "claude": ("gpt", "glm")}   # proposer -> checkers
OBLIGATIONS = ("reduction", "lower_bound", "upper_bound")
CHECKED = ("lower_bound", "upper_bound")

# ---------------------------------------------------------------- case list (fixed in PROTOCOL.md)
CASES = [
    # id, problem, group, path
    ("p6-gpt-5.6-sol-main-t009", "6", "A", SCRATCH / "deedy_ckpts_p6/gpt-5.6-sol-main-t009-6990dbe90da7.md"),
    ("p6-deedy-gpt-5.6-sol-final", "6", "A", SCRATCH / "imo-2026-deedy/results/gpt-5.6-sol/problem-06/current.md"),
    ("p6-kimi-k3-round2-t007", "6", "A", SCRATCH / "deedy_ckpts_p6/kimi-k3-round2-t007-bd6057aef3ec.md"),
    ("deedy-gpt-5.6-sol-final", "3", "A", SCRATCH / "imo-2026-deedy/results/gpt-5.6-sol/problem-03/current.md"),
    ("deedy-grok-4.5-final", "3", "B", SCRATCH / "imo-2026-deedy/results/grok-4.5/problem-03/current.md"),
    ("deedy-muse-spark-1.1-final", "3", "B", SCRATCH / "imo-2026-deedy/results/muse-spark-1.1/problem-03/current.md"),
    ("deedy-deepseek-v4-pro-final", "3", "B", SCRATCH / "imo-2026-deedy/results/deepseek-v4-pro/problem-03/current.md"),
    ("kimi-k3-round3-t007", "3", "C", SCRATCH / "deedy_ckpts/kimi-k3-round3-t007-15413cb68d86.md"),
    ("kimi-k3-round4-t014", "3", "C", SCRATCH / "deedy_ckpts/kimi-k3-round4-t014-ea4551d94017.md"),
    ("p6-kimi-k3-round1-t021", "6", "C", SCRATCH / "deedy_ckpts_p6/kimi-k3-round1-t021-b041005367c7.md"),
    ("p1-glm52-2ede1c6b-v1", "1", "D", pathlib.Path("[local-path]/candidate_v1.md")),
    ("p5-deepseek-v4-pro-main-t033", "5", "D", SCRATCH / "deedy_ckpts_p5/deepseek-v4-pro-main-t033-cd94261ef509.md"),
    ("p5-deepseek-v4-pro-main-t038", "5", "D", SCRATCH / "deedy_ckpts_p5/deepseek-v4-pro-main-t038-98f919cec9ce.md"),
    ("p5-nemotron-2587b733-v2", "5", "D", pathlib.Path("[local-path]/candidate_v2.md")),
    ("deedy-claude-fable-5-final", "3", "E", SCRATCH / "imo-2026-deedy/results/claude-fable-5/problem-03/current.md"),
    ("deedy-gpt-5.6-sol-xhigh-final", "3", "E", SCRATCH / "imo-2026-deedy/results/gpt-5.6-sol-xhigh/problem-03/current.md"),
    ("p6-deedy-gpt-5.6-sol-pro-final", "6", "E", SCRATCH / "imo-2026-deedy/results/gpt-5.6-sol-pro/problem-06/current.md"),
    ("p1-deedy-kimi-k3-final", "1", "E", SCRATCH / "imo-2026-deedy/results/kimi-k3/problem-01/current.md"),
    ("p4-deedy-claude-fable-5-final", "4", "E", SCRATCH / "imo-2026-deedy/results/claude-fable-5/problem-04/current.md"),
    ("p6-deedy-grok-4.5-final", "6", "F", SCRATCH / "imo-2026-deedy/results/grok-4.5/problem-06/current.md"),
]
GROUP_NAMES = {"A": "credited-defective (alarm hit)", "B": "documented-defective, never credited", "C": "alarm flag without record",
               "D": "replication flip", "E": "control: public grade 7, all evaluators S=2", "F": "low control: grade 1, all S=0"}
AUTHOR_LAB = {"gpt": {"p6-gpt-5.6-sol-main-t009", "p6-deedy-gpt-5.6-sol-final", "deedy-gpt-5.6-sol-final", "deedy-gpt-5.6-sol-xhigh-final", "p6-deedy-gpt-5.6-sol-pro-final"},
              "claude": {"deedy-claude-fable-5-final", "p4-deedy-claude-fable-5-final"}}
# documented defects (recovery targets) and the obligation they sit on
RECORDS = {
    "p6-gpt-5.6-sol-main-t009": ("lower_bound", "false finite-transversal lemma (pairwise-intersecting family of finite sets has finitely many minimal finite transversals)"),
    "p6-deedy-gpt-5.6-sol-final": ("lower_bound", "false finite-transversal lemma (same; Konig-tree proof)"),
    "p6-kimi-k3-round2-t007": ("lower_bound", "self-duality theorem proved for finite minimal transversals applied to a Zorn-extracted minimal transversal not shown finite"),
    "deedy-gpt-5.6-sol-final": ("lower_bound|upper_bound", "refinement lemma's 'column sweep' proof is a sketch: (i) sweep/cancellation induction, (ii) strip survival asserted; both bounds rest on it"),
    "deedy-grok-4.5-final": ("lower_bound|upper_bound", "Theorem B's k>=1 induction step garbled (lower bound); Theorem C never completes (upper bound)"),
    "deedy-muse-spark-1.1-final": ("lower_bound", "wrong answer (n+1)/(2n+1); even-multiples construction's guarantee false (n=2: 0.4,0.4,0.2 -> Xiang holds Liu to 0.505); no upper bound"),
    "deedy-deepseek-v4-pro-final": ("lower_bound", "wrong answer (n+1)/(2n+1); equally spaced construction's guarantee false (n=2: 0.2,0.2,0.6 -> 53/105); no proof of either direction"),
}
MAX_CHARS = 120000

def sha256(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def lj(p): return json.load(open(p))
def dj(p, o): pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True); pathlib.Path(p).write_text(json.dumps(o, indent=1, ensure_ascii=False))

CHECKER_FIELDS = ("quote_faithful", "verdict", "evidence_kind", "fatal")

def extract_checker_lenient(text: str):
    """Fallback for checker replies that are almost JSON (e.g. an unquoted explanation value): pull the four enum fields by
    regex and take the remainder after "explanation": as the explanation. Only used when extract_json fails; marked lenient_parse."""
    out = {}
    for k in CHECKER_FIELDS:
        m = re.search(r'"%s"\s*:\s*"([a-z_]+)"' % k, text)
        if not m: return None
        out[k] = m.group(1)
    m = re.search(r'"explanation"\s*:\s*"?(.*)', text, re.S)
    out["explanation"] = (m.group(1).strip().rstrip("}").rstrip().rstrip('"') if m else "")
    out["lenient_parse"] = True
    return out

def extract_json(text: str):
    m = re.search(r"\{.*\}", text, re.S)
    if not m: return None
    s = m.group(0)
    for cand in (s, s.replace("\n", " ")):
        try: return json.loads(cand)
        except json.JSONDecodeError: pass
    # code fence inside? try the largest balanced object
    depth, start = 0, None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0: start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try: return json.loads(text[start:i + 1])
                except json.JSONDecodeError: continue
    return None

# ---------------------------------------------------------------- rubric handling
def rubric_core(problem: str) -> str:
    if problem == "3":
        import closure_annotate  # noqa: E402  (RUBRIC for P3; generation-time dependency)
        txt = closure_annotate.RUBRIC
    else: txt = (ART / f"closure_rubric_p{problem}.txt").read_text()
    out, skip = [], False
    for ln in txt.splitlines():
        if ln.startswith("Return ONLY a JSON object"): skip = True
        if skip:
            if '"notes"' in ln: skip = False
            continue
        out.append(ln)
    return "\n".join(out).strip()

WITNESS_INSTRUCTIONS = """
TASK: obligation audit with witnesses. Audit the write-up obligation by obligation. The three obligations are the rubric fields "reduction", "lower_bound" and "upper_bound" (use the field mapping above for this problem). For each obligation return exactly one status:
- "written_and_valid": the text contains an argument covering all cases and you found no error in it.
- "written_but_invalid": the text presents an argument intended to cover all cases, but a specific step is false or does not follow.
- "not_written": the text does not present an all-cases argument for this obligation (absent, named or sketched only, checked only on examples, proved only under an unproved extra assumption, or deferred).
For every obligation whose status is not "written_and_valid" you must give a WITNESS with three parts:
- "quote": a verbatim excerpt of the write-up, 40 to 400 characters, copied exactly (same characters, no paraphrase, no ellipsis), containing the false claim or the inference that does not follow (written_but_invalid), or the closest the text comes to the obligation / the place where it defers it (not_written). The quote is matched mechanically against the text.
- "witness": for written_but_invalid, either an explicit COUNTEREXAMPLE (concrete objects that satisfy the hypotheses of the quoted claim and violate its conclusion, with the verification spelled out) or an explicit NON-SEQUITUR (the premises the text has established, the conclusion it draws, and why the conclusion does not follow); for not_written, the precise missing statement (what would have to be proved, for all cases) and why the quoted passage does not prove it.
- "load_bearing": one or two sentences on why the obligation depends on this step as the text is written.
For "written_and_valid" set quote, witness and load_bearing to null.
Judge only what is written. Do not use the length of the text, its confidence, or claims of completeness. Do not repair the argument for the author: if a step could be fixed but is not proved in the text, the status is not_written (or written_but_invalid if what is written is false).
Return ONLY a JSON object:
{"obligations": {"reduction": {"status": "...", "quote": ..., "witness": ..., "load_bearing": ...},
                 "lower_bound": {"status": "...", "quote": ..., "witness": ..., "load_bearing": ...},
                 "upper_bound": {"status": "...", "quote": ..., "witness": ..., "load_bearing": ...}},
 "S_valid": <number of lower_bound and upper_bound obligations with status written_and_valid>,
 "wrong_answer_stated": true|false, "notes": "<=60 words"}
"""

def proposer_system(problem: str) -> str:
    return rubric_core(problem) + "\n" + WITNESS_INSTRUCTIONS

CHECKER_INSTRUCTIONS = """
TASK: referee one objection. An objection has been raised against a specific step of the write-up below, concerning one obligation of the rubric above. Decide whether the objection is correct, using only mathematics and the text.

You receive: the full write-up; the obligation the objection concerns (or "unspecified" when the objector did not name one); a quote the objector says is verbatim from the write-up (possibly absent); the objector's claimed status and its witness (the objection proper).

Return:
- "quote_faithful": "yes" if the quoted passage, read in its context in the write-up, means what the objection takes it to mean; "no" if the objection misreads it (for example the text's claim carries a hypothesis the objection ignores, or the quote is not in the text); "unclear".
- "verdict": "confirmed" if the witness is correct: for a counterexample, the objects satisfy the hypotheses of the quoted claim as the text states it and violate its conclusion; for a non-sequitur, the conclusion indeed does not follow from what the text has established at that point; for a missing step, the text indeed does not establish the stated statement for all cases anywhere (check the whole text, not only the quoted passage). "rejected" if the witness is wrong: say exactly why (the counterexample violates a hypothesis, the inference is valid, or the text proves the statement elsewhere, quoting where). "unclear" only if you cannot decide.
- "evidence_kind": what the objection actually supplies, judged by you: "counterexample" (concrete objects refuting the quoted claim), "invalid_inference" (an identified step whose conclusion does not follow from its stated premises), "missing_justification" (a specific statement the text needs and does not prove, without a refutation), or "none" (no specific step is identified).
- "fatal": if the objection is correct, would the proof (or the obligation named) remain incomplete or invalid as written ("yes"), or is the step inessential or repaired elsewhere in the text ("no")? "unclear" if you cannot decide.
- "explanation": at most 150 words, with the decisive check spelled out.
Return ONLY a JSON object: {"quote_faithful": "...", "verdict": "...", "evidence_kind": "...", "fatal": "...", "explanation": "..."}
"""

def checker_system(problem: str) -> str:
    return rubric_core(problem) + "\n" + CHECKER_INSTRUCTIONS

# ---------------------------------------------------------------- ordinary-review baseline (Amendment 1.2)
GRADER_RETURN = """Return ONLY a JSON object:
{"grade": 0|1|2|3|4|5|6|7, "complete": true|false, "main_gap": "<=40 words or 'none'",
 "errors": [{"description": "<=80 words: the step concerned and what is wrong or missing", "quote": "<verbatim excerpt of the write-up this concerns, or null>"}, ...],
 "notes": "<=60 words"}
List at most three errors, the most severe first; an empty list means you found none."""

def baseline_system(problem: str) -> str:
    txt = (ART / f"baseline_rubric_p{problem}.txt").read_text()
    head = txt.split("Return ONLY a JSON object:")[0].rstrip()
    return head + "\n\n" + GRADER_RETURN

def baseline_one(args, case):
    kind, model = PROPOSERS[args.grader]
    out = WD / "baseline" / args.grader / case["id"]
    if (out / "parsed.json").exists() and not args.redo: return "cached"
    text = case_bytes(case)
    assert sha256(text) == case["sha256"], case["id"]
    system = baseline_system(case["problem"])
    user = "## Write-up to grade\n\n" + text.decode(errors="replace")[:MAX_CHARS]
    t0 = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    status, resp = call_model(kind, model, system, user, "", args.timeout)
    txt = resp_text(resp) if status == 200 else ""
    parsed = extract_json(txt) if txt else None
    dj(out / "request.json", {"grader": args.grader, "transport": kind, "model": model, "case": case["id"], "problem": case["problem"], "text_sha256": case["sha256"],
                              "system_sha256": sha256(system.encode()), "system": system, "user_chars": len(user), "started_utc": t0})
    dj(out / "response.json", {"status": status, "response": resp})
    if parsed is not None:
        errs = parsed.get("errors") or []
        anchors = [anchored(e.get("quote"), text.decode(errors="replace")) if isinstance(e, dict) else {"anchored": False, "reason": "malformed"} for e in errs]
        dj(out / "parsed.json", {"grader": args.grader, "case": case["id"], "problem": case["problem"], "group": case["group"], "status": status,
                                 "usage": usage_of(resp), "parsed": parsed, "anchors": anchors})
        print(f"[grader {args.grader}] {case['id']}: grade={parsed.get('grade')} errors={len(errs)} {usage_of(resp).get('elapsed_seconds')}s", flush=True)
        return "ok"
    print(f"[grader {args.grader}] {case['id']}: FAILED status={status} {str(resp)[:200]}", flush=True)
    return "failed"

def cmd_baseline(args):
    cases = load_cases()
    if args.only: cases = [c for c in cases if c["id"] in set(args.only.split(","))]
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        res = list(ex.map(lambda c: baseline_one(args, c), cases))
    print({r: res.count(r) for r in set(res)})
    return 0

# ---------------------------------------------------------------- transport
def call_model(kind: str, model: str, system: str, user: str, key: str, timeout: int):
    from cli_transport import call_claude_cli, call_codex_cli  # noqa: E402  (generation-time dependencies)
    import closure_annotate  # noqa: E402
    if kind == "claude-cli": return call_claude_cli(model, system, user, timeout)
    if kind == "codex-cli": return call_codex_cli(model, system, user, timeout, effort="high")
    # GLM-5.3 (Z.ai): thinking first; if the reply carries no parseable text (thinking exhausted the cap), one retry without thinking,
    # as in the closure instrument (closure_annotate.py); both attempts are kept in the response object.
    t0 = time.time(); attempts = []
    for attempt, body in enumerate((
            {"model": model, "max_tokens": 32000, "system": system, "messages": [{"role": "user", "content": user}], "thinking": {"type": "enabled", "budget_tokens": 12000}},
            {"model": model, "max_tokens": 16000, "system": system, "messages": [{"role": "user", "content": user}], "thinking": {"type": "disabled"}})):
        for backoff in (0, 30, 60, 120, 240):
            if backoff: time.sleep(backoff)
            status, resp = closure_annotate.call("https://api.z.ai/api/anthropic", key, body, timeout, "anthropic")
            if status != 429 and "rate_limit" not in json.dumps(resp)[:400]: break
        attempts.append({"attempt": attempt, "status": status, "stop_reason": resp.get("stop_reason") if isinstance(resp, dict) else None, "usage": resp.get("usage") if isinstance(resp, dict) else None})
        if status == 200 and extract_json(resp_text(resp)) is not None: break
    if isinstance(resp, dict): resp["elapsed_seconds"] = round(time.time() - t0, 1); resp["attempts"] = attempts
    return status, resp

def resp_text(resp) -> str:
    return "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")

def usage_of(resp) -> dict:
    u = resp.get("usage") or {}
    out = {"elapsed_seconds": resp.get("elapsed_seconds")}
    for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "total_tokens", "reasoning_output_tokens", "cached_input_tokens"):
        if k in u: out[k] = u[k]
    if resp.get("cli_model_usage"): out["cli_model_usage"] = resp["cli_model_usage"]
    return out

# ---------------------------------------------------------------- anchoring
def norm(s: str) -> str:
    s = re.sub(r"[*_$\\]", "", s)
    return re.sub(r"\s+", " ", s).strip()

def anchored(quote, text) -> dict:
    if not quote or not isinstance(quote, str): return {"anchored": False, "reason": "no quote"}
    q, t = norm(quote), norm(text)
    if len(quote) < 40: reason = "short"
    elif len(quote) > 400: reason = "long"
    else: reason = None
    if q and q in t: return {"anchored": True, "length": len(quote), "length_ok": reason is None, "reason": reason}
    q2, t2 = re.sub(r"\s", "", q), re.sub(r"\s", "", t)
    if q2 and q2 in t2: return {"anchored": True, "length": len(quote), "length_ok": reason is None, "reason": "matched without spaces"}
    return {"anchored": False, "length": len(quote), "length_ok": reason is None, "reason": "not found"}

# ---------------------------------------------------------------- subcommands
def cmd_cases(args):
    cases = []
    for cid, problem, group, path in CASES:
        b = pathlib.Path(path).read_bytes()
        rec = RECORDS.get(cid)
        cases.append({"id": cid, "problem": problem, "group": group, "group_name": GROUP_NAMES[group], "path": str(path), "bytes": len(b),
                      "sha256": sha256(b), "author_lab": next((lab for lab, s in AUTHOR_LAB.items() if cid in s), None),
                      "record_obligation": rec[0] if rec else None, "record_defect": rec[1] if rec else None})
    dj(WD / "cases.json", {"protocol": "PROTOCOL.md", "built_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), "cases": cases})
    for c in cases: print(f"{c['group']} {c['id']:34s} P{c['problem']} {c['bytes']:6d}B {c['sha256'][:12]}")
    return 0

def load_cases():
    return lj(WD / "cases.json")["cases"]

def propose_one(args, case):
    kind, model = PROPOSERS[args.proposer]
    out = WD / "propose" / args.proposer / case["id"]
    if (out / "parsed.json").exists() and not args.redo: return "cached"
    text = case_bytes(case)
    assert sha256(text) == case["sha256"], case["id"]
    system = proposer_system(case["problem"])
    user = "## Write-up to audit\n\n" + text.decode(errors="replace")[:MAX_CHARS]
    t0 = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    status, resp = call_model(kind, model, system, user, "", args.timeout)
    txt = resp_text(resp) if status == 200 else ""
    parsed = extract_json(txt) if txt else None
    dj(out / "request.json", {"proposer": args.proposer, "transport": kind, "model": model, "case": case["id"], "problem": case["problem"], "text_sha256": case["sha256"],
                              "system_sha256": sha256(system.encode()), "system": system, "user_chars": len(user), "started_utc": t0})
    dj(out / "response.json", {"status": status, "response": resp})
    if parsed is not None:
        # anchoring for every non-valid obligation
        obls = parsed.get("obligations") or {}
        anchors = {}
        for ob in OBLIGATIONS:
            o = obls.get(ob) or {}
            if isinstance(o, dict) and o.get("status") != "written_and_valid":
                anchors[ob] = anchored(o.get("quote"), text.decode(errors="replace"))
        dj(out / "parsed.json", {"proposer": args.proposer, "case": case["id"], "problem": case["problem"], "group": case["group"], "status": status,
                                 "usage": usage_of(resp), "parsed": parsed, "anchors": anchors})
        stat = {ob: (obls.get(ob) or {}).get("status") for ob in OBLIGATIONS}
        print(f"[{args.proposer}] {case['id']}: {stat} anchors={ {k: v['anchored'] for k, v in anchors.items()} } {usage_of(resp).get('elapsed_seconds')}s", flush=True)
        return "ok"
    print(f"[{args.proposer}] {case['id']}: FAILED status={status} {str(resp)[:200]}", flush=True)
    return "failed"

def cmd_propose(args):
    cases = load_cases()
    if args.only: cases = [c for c in cases if c["id"] in set(args.only.split(","))]
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        res = list(ex.map(lambda c: propose_one(args, c), cases))
    print({r: res.count(r) for r in set(res)})
    return 0

def witness_jobs():
    """All objections to check: (procedure, source model, case, tag, objection dict).
    procedure 'witness': proposer's lower/upper witnesses; procedure 'grader': the ordinary grader's two most severe errors."""
    jobs = []
    for c in load_cases():
        for prop in PROPOSERS:
            p = WD / "propose" / prop / c["id"] / "parsed.json"
            if p.exists():
                parsed = lj(p)["parsed"]
                for ob in CHECKED:
                    o = (parsed.get("obligations") or {}).get(ob) or {}
                    if isinstance(o, dict) and o.get("status") in ("written_but_invalid", "not_written"):
                        jobs.append(("witness", prop, c, ob, {"obligation": ob, "status": o.get("status"), "quote": o.get("quote"), "witness": o.get("witness"), "load_bearing": o.get("load_bearing")}))
            b = WD / "baseline" / prop / c["id"] / "parsed.json"
            if b.exists():
                errs = [e for e in (lj(b)["parsed"].get("errors") or []) if isinstance(e, dict)][:2]
                for i, e in enumerate(errs):
                    jobs.append(("grader", prop, c, f"e{i}", {"obligation": "unspecified", "status": "error reported by an ordinary grader", "quote": e.get("quote"), "witness": e.get("description"), "load_bearing": None}))
    return jobs

def job_key(job):
    proc, src, case, tag, _ = job
    return f"{proc}-{src}__{case['id']}__{tag}"

def check_one(args, key, job):
    proc, src, case, tag, o = job
    if args.checker not in CHECKS_FOR[src]: return "skip"
    kind, model = CHECKERS[args.checker]
    out = WD / "check" / args.checker / job_key(job)
    if (out / "parsed.json").exists() and not args.redo: return "cached"
    text = case_bytes(case)
    assert sha256(text) == case["sha256"]
    system = checker_system(case["problem"])
    user = ("## Write-up\n\n" + text.decode(errors="replace")[:MAX_CHARS] +
            f"\n\n## Objection\n\nObligation: {o.get('obligation')}\nClaimed status: {o.get('status')}\n"
            f"Quote (claimed verbatim): {json.dumps(o.get('quote'), ensure_ascii=False)}\nObjection / witness: {o.get('witness')}\n"
            + (f"Load-bearing: {o.get('load_bearing')}\n" if o.get("load_bearing") else ""))
    t0 = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    status, resp = call_model(kind, model, system, user, key, args.timeout)
    txt = resp_text(resp) if status == 200 else ""
    parsed = extract_json(txt) if txt else None
    if parsed is None and txt: parsed = extract_checker_lenient(txt)
    dj(out / "request.json", {"checker": args.checker, "transport": kind, "model": model, "procedure": proc, "source": src, "case": case["id"], "tag": tag,
                              "text_sha256": case["sha256"], "system_sha256": sha256(system.encode()), "objection": o, "started_utc": t0})
    dj(out / "response.json", {"status": status, "response": resp})
    if parsed is not None:
        dj(out / "parsed.json", {"checker": args.checker, "procedure": proc, "source": src, "case": case["id"], "tag": tag, "status": status, "usage": usage_of(resp), "parsed": parsed})
        print(f"[{args.checker}] {job_key(job)}: {parsed.get('verdict')} kind={parsed.get('evidence_kind')} faithful={parsed.get('quote_faithful')} fatal={parsed.get('fatal')} {usage_of(resp).get('elapsed_seconds')}s", flush=True)
        return "ok"
    print(f"[{args.checker}] {job_key(job)}: FAILED status={status} {str(resp)[:200]}", flush=True)
    return "failed"

def cmd_check(args):
    key = pathlib.Path(args.key_file).expanduser().read_text().strip() if args.checker == "glm" else ""
    jobs = [j for j in witness_jobs() if args.checker in CHECKS_FOR[j[1]]]
    if args.only: jobs = [j for j in jobs if j[2]["id"] in set(args.only.split(","))]
    if args.procedure: jobs = [j for j in jobs if j[0] == args.procedure]
    print(f"{len(jobs)} objections for checker {args.checker}")
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        res = list(ex.map(lambda j: check_one(args, key, j), jobs))
    print({r: res.count(r) for r in set(res)})
    return 0

# ---------------------------------------------------------------- analysis (classes fixed in PROTOCOL.md Amendment 1)
CLASS_ORDER = {"substantiated": 4, "localized": 3, "unresolved": 2, "unsupported": 1, "pending": 0}
SYM = {"substantiated": r"\textbf{S}", "localized": "L", "unresolved": "?", "unsupported": "U", "pending": r"$\cdot$", None: "--"}
DECISIVE = {"counterexample", "invalid_inference"}

def classify(checks: dict, freeze: bool) -> tuple[str, bool]:
    """checks: checker -> parsed dict or None. Returns (class, single_checker)."""
    ret = [v for v in checks.values() if v]
    if not ret: return "pending", False
    if len(ret) < len(checks) and not freeze: return "pending", False
    single = len(ret) < len(checks)
    conf = [v.get("verdict") == "confirmed" and v.get("quote_faithful") != "no" for v in ret]
    if all(conf):
        kinds = {v.get("evidence_kind") for v in ret}
        return ("substantiated" if kinds and kinds <= DECISIVE else "localized"), single
    if all(v.get("verdict") == "rejected" for v in ret): return "unsupported", single
    return "unresolved", single

def both_fatal_yes(checks: dict) -> bool:
    """Severity layer, reported beside the classes and not part of the classification rule (PROTOCOL.md declares that `fatal` is
    reported alongside, not used): every checker that returned answered fatal = yes."""
    ret = [v for v in checks.values() if v]
    return bool(ret) and all(v.get("fatal") == "yes" for v in ret)

def read_checks(proc, src, case_id, tag):
    out = {}
    for chk in CHECKS_FOR[src]:
        cp = WD / "check" / chk / f"{proc}-{src}__{case_id}__{tag}" / "parsed.json"
        if cp.exists():
            cj = lj(cp); out[chk] = {k: cj["parsed"].get(k) for k in ("quote_faithful", "verdict", "evidence_kind", "fatal", "explanation")}; out[chk]["usage"] = cj.get("usage")
        else: out[chk] = None
    return out

def best_class(objs):
    cls = [o["class"] for o in objs]
    return max(cls, key=lambda c: CLASS_ORDER[c]) if cls else None

# ---- cost accounting over retained responses: input, output, cache-read and cache-creation tokens kept apart; timed and untimed
# records counted separately; helper-model and earlier-attempt usage reported where the response stored it.
TOKEN_KINDS = (("input", "input_tokens"), ("output", "output_tokens"), ("cache_read", "cache_read_input_tokens"), ("cache_creation", "cache_creation_input_tokens"))
TOKEN_FIELDS = tuple(k for k, _ in TOKEN_KINDS) + ("total", "cached_input_memo", "reasoning_output_memo")

def token_breakdown(u) -> dict:
    """Primary-model tokens of one retained response by kind, and their sum. Codex reports input_tokens inclusive of
    cached_input_tokens and output_tokens inclusive of reasoning_output_tokens (kept as memo fields, not added again); the Claude
    CLI and the Anthropic-style GLM API report cache reads and cache creation as separate input kinds, so all four are added."""
    u = u or {}
    b = {k: int(u.get(src) or 0) for k, src in TOKEN_KINDS}
    b["total"] = sum(b[k] for k, _ in TOKEN_KINDS)
    b["cached_input_memo"] = int(u.get("cached_input_tokens") or 0)
    b["reasoning_output_memo"] = int(u.get("reasoning_output_tokens") or 0)
    return b

def helper_tokens(u, model: str) -> int:
    """Claude CLI: tokens of models the CLI invoked besides the requested one (cli_model_usage), e.g. a Haiku helper call per invocation."""
    tot = 0
    for name, mu in ((u or {}).get("cli_model_usage") or {}).items():
        if not isinstance(mu, dict) or name == model or mu.get("canonicalModel") == model: continue
        tot += sum(int(mu.get(k) or 0) for k in ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens"))
    return tot

def earlier_attempts(resp_path) -> dict:
    """Attempt summaries stored with a response (the GLM transport keeps status, stop reason and usage of every attempt): the usage
    of the attempts before the retained reply, where it was stored. A response file replaced by a rerun is not recoverable."""
    out = {"attempts": None, "earlier_tokens": 0}
    try: r = lj(resp_path).get("response") if resp_path.exists() else None
    except (ValueError, OSError, AttributeError): r = None
    if isinstance(r, dict) and isinstance(r.get("attempts"), list):
        out["attempts"] = len(r["attempts"])
        for a in r["attempts"][:-1]:
            if isinstance(a, dict) and a.get("usage"): out["earlier_tokens"] += token_breakdown(a["usage"])["total"]
    return out

def usage_record(rid: str, u, resp_path, model: str) -> dict:
    el = (u or {}).get("elapsed_seconds")
    return {"id": rid, "elapsed": el if isinstance(el, (int, float)) else None, "tokens": token_breakdown(u), "helper_tokens": helper_tokens(u, model), **earlier_attempts(resp_path)}

def summarize_usage(recs: list) -> dict:
    timed = [r["elapsed"] for r in recs if r["elapsed"] is not None]
    att = {}
    for r in recs: att[r["attempts"]] = att.get(r["attempts"], 0) + 1
    return {"delivered": len(recs), "timed": len(timed), "untimed_ids": [r["id"] for r in recs if r["elapsed"] is None],
            "mean_s": round(sum(timed) / len(timed), 1) if timed else None, "max_s": max(timed) if timed else None, "sum_s": round(sum(timed), 1),
            "tokens": {k: sum(r["tokens"][k] for r in recs) for k in TOKEN_FIELDS},
            "helper_tokens": sum(r["helper_tokens"] for r in recs), "earlier_attempt_tokens": sum(r["earlier_tokens"] for r in recs),
            "attempt_summaries": {("none_stored" if k is None else f"{k}_attempts"): v for k, v in sorted(att.items(), key=lambda kv: (kv[0] is not None, kv[0] or 0))}}

def cmd_analyze(args):
    cases = load_cases(); freeze = bool(args.freeze)
    per_case = {}
    usage_first = {}                                                       # "witness-gpt" -> usage records of retained first-stage responses
    usage_check = {chk: {"witness": [], "grader": []} for chk in CHECKERS}  # checker -> procedure -> usage records of retained checks
    for c in cases:
        e = {"id": c["id"], "problem": c["problem"], "group": c["group"], "record_obligation": c["record_obligation"], "record_defect": c["record_defect"],
             "author_lab": c["author_lab"], "witness": {}, "grader": {}}
        for src in PROPOSERS:
            # witness procedure
            pp = WD / "propose" / src / c["id"] / "parsed.json"
            if pp.exists():
                pj = lj(pp); parsed = pj["parsed"]; obls = parsed.get("obligations") or {}
                pe = {"usage": pj.get("usage"), "S_valid": parsed.get("S_valid"), "wrong_answer_stated": parsed.get("wrong_answer_stated"), "notes": parsed.get("notes"),
                      "statuses": {ob: (obls.get(ob) or {}).get("status") for ob in OBLIGATIONS}, "objections": []}
                for ob in CHECKED:
                    o = obls.get(ob) or {}
                    if isinstance(o, dict) and o.get("status") in ("written_but_invalid", "not_written"):
                        checks = read_checks("witness", src, c["id"], ob); cls, single = classify(checks, freeze); fatal = both_fatal_yes(checks)
                        pe["objections"].append({"tag": ob, "status": o.get("status"), "quote": o.get("quote"), "witness": o.get("witness"), "load_bearing": o.get("load_bearing"),
                                                 "anchor": (pj.get("anchors") or {}).get(ob), "checks": checks, "class": cls, "single_checker": single,
                                                 "both_fatal_yes": fatal, "substantiated_fatal": cls == "substantiated" and fatal})
                pe["class"] = best_class(pe["objections"]); pe["substantiated_fatal"] = any(o["substantiated_fatal"] for o in pe["objections"])
                e["witness"][src] = pe
                usage_first.setdefault(f"witness-{src}", []).append(usage_record(c["id"], pj.get("usage"), pp.parent / "response.json", PROPOSERS[src][1]))
            else:
                e["witness"][src] = None if not (WD / "propose" / src / c["id"] / "response.json").exists() else {"delivery_failure": True, "objections": [], "class": None}
            # grader baseline
            bp = WD / "baseline" / src / c["id"] / "parsed.json"
            if bp.exists():
                bj = lj(bp); parsed = bj["parsed"]
                ge = {"usage": bj.get("usage"), "grade": parsed.get("grade"), "complete": parsed.get("complete"), "main_gap": parsed.get("main_gap"), "notes": parsed.get("notes"),
                      "n_errors_listed": len(parsed.get("errors") or []), "objections": []}
                errs = [x for x in (parsed.get("errors") or []) if isinstance(x, dict)][:2]
                for i, x in enumerate(errs):
                    checks = read_checks("grader", src, c["id"], f"e{i}"); cls, single = classify(checks, freeze); fatal = both_fatal_yes(checks)
                    ge["objections"].append({"tag": f"e{i}", "quote": x.get("quote"), "witness": x.get("description"), "anchor": (bj.get("anchors") or [None] * 3)[i] if i < len(bj.get("anchors") or []) else None,
                                             "checks": checks, "class": cls, "single_checker": single, "both_fatal_yes": fatal, "substantiated_fatal": cls == "substantiated" and fatal})
                ge["class"] = best_class(ge["objections"]); ge["substantiated_fatal"] = any(o["substantiated_fatal"] for o in ge["objections"])
                e["grader"][src] = ge
                usage_first.setdefault(f"grader-{src}", []).append(usage_record(c["id"], bj.get("usage"), bp.parent / "response.json", PROPOSERS[src][1]))
            else:
                e["grader"][src] = None if not (WD / "baseline" / src / c["id"] / "response.json").exists() else {"delivery_failure": True, "objections": [], "class": None}
        per_case[c["id"]] = e
    # usage of every retained check, by checker and by the procedure whose objection it judged
    for cid, e in per_case.items():
        for proc in ("witness", "grader"):
            for src in PROPOSERS:
                for o in (e[proc].get(src) or {}).get("objections", []):
                    for chk, ck in (o.get("checks") or {}).items():
                        if ck:
                            key = f"{proc}-{src}__{cid}__{o['tag']}"
                            usage_check[chk][proc].append(usage_record(key, ck.get("usage"), WD / "check" / chk / key / "response.json", CHECKERS[chk][1]))

    # ---- endpoint counts per group x procedure x source (+ union)
    def texts(g): return [c["id"] for c in cases if c["group"] == g]
    def ent(e, proc, src): return e[proc].get(src) or {}
    def cls_of(e, proc, src): return ent(e, proc, src).get("class")
    def has(e, proc, src, pred): return pred(ent(e, proc, src))
    def union(e, proc, pred): return any(has(e, proc, src, pred) for src in PROPOSERS)
    preds = {"substantiated": lambda pe: pe.get("class") == "substantiated", "localized_or_better": lambda pe: pe.get("class") in ("substantiated", "localized"),
             "unsupported": lambda pe: pe.get("class") == "unsupported", "unresolved": lambda pe: pe.get("class") == "unresolved",
             "any_objection": lambda pe: pe.get("class") is not None, "pending": lambda pe: pe.get("class") == "pending",
             "substantiated_fatal": lambda pe: bool(pe.get("substantiated_fatal"))}   # severity layer: substantiated and both checkers fatal = yes
    counts = {}
    for g in "ABCDEF":
        counts[g] = {"n": len(texts(g))}
        for proc in ("witness", "grader"):
            for src in list(PROPOSERS) + ["union"]:
                for k, pr in preds.items():
                    ids = texts(g)
                    n = sum(1 for i in ids if (union(per_case[i], proc, pr) if src == "union" else has(per_case[i], proc, src, pr)))
                    counts[g].setdefault(proc, {}).setdefault(src, {})[k] = n
    # objection-level totals
    obj_tot = {}
    for proc in ("witness", "grader"):
        for src in PROPOSERS:
            t = {"objections": 0, "anchored": 0, "substantiated": 0, "localized": 0, "unresolved": 0, "unsupported": 0, "pending": 0, "single_checker": 0, "substantiated_fatal": 0}
            for e in per_case.values():
                pe = e[proc].get(src) or {}
                for o in pe.get("objections", []):
                    t["objections"] += 1; t[o["class"]] += 1
                    if (o.get("anchor") or {}).get("anchored"): t["anchored"] += 1
                    if o.get("single_checker"): t["single_checker"] += 1
                    if o.get("substantiated_fatal"): t["substantiated_fatal"] += 1
            obj_tot[f"{proc}-{src}"] = t
    # proposer status agreement (witness procedure)
    agree = {"n": 0, "same_status": 0}
    for e in per_case.values():
        if all((e["witness"].get(s) or {}).get("statuses") for s in PROPOSERS):
            for ob in OBLIGATIONS:
                agree["n"] += 1; agree["same_status"] += int(e["witness"]["gpt"]["statuses"][ob] == e["witness"]["claude"]["statuses"][ob])
    # ---- severity layer: the same quoted passage checked under both procedures by the same checker, and whether `fatal` differs
    same_quote = []
    for cid, e in per_case.items():
        W = [(src, o) for src in PROPOSERS for o in ent(e, "witness", src).get("objections", [])]
        G = [(src, o) for src in PROPOSERS for o in ent(e, "grader", src).get("objections", [])]
        for ws, w in W:
            for gs, g in G:
                qw, qg = norm(w.get("quote") or ""), norm(g.get("quote") or "")
                if not qw or qw != qg: continue
                for chk in CHECKERS:
                    cw, cg = (w.get("checks") or {}).get(chk), (g.get("checks") or {}).get(chk)
                    if cw and cg:
                        same_quote.append({"case": cid, "checker": chk, "witness_objection": f"{ws}/{w['tag']}", "grader_objection": f"{gs}/{g['tag']}",
                                           "verdict": {"witness": cw.get("verdict"), "grader": cg.get("verdict")}, "fatal": {"witness": cw.get("fatal"), "grader": cg.get("fatal")},
                                           "fatal_differs": cw.get("fatal") != cg.get("fatal")})
    compared = {(r["case"], r["checker"]) for r in same_quote}; differing = {(r["case"], r["checker"]) for r in same_quote if r["fatal_differs"]}
    def gsum_(proc, groups, k): return sum(counts[g][proc]["union"][k] for g in groups)
    fatal_layer = {"rule": "substantiated_fatal: classified substantiated (Amendment 1.1 rule, unchanged) and every returned checker answered fatal = yes; "
                           "a post hoc severity layer reported beside the classes, not a replacement endpoint",
                   "open_disputes": {"n": counts["C"]["n"] + counts["D"]["n"],
                                     **{proc: {"substantiated": gsum_(proc, "CD", "substantiated"), "substantiated_fatal": gsum_(proc, "CD", "substantiated_fatal")} for proc in ("witness", "grader")}},
                   "known_defects": {"n": counts["A"]["n"] + counts["B"]["n"],
                                     **{proc: {"substantiated": gsum_(proc, "AB", "substantiated"), "substantiated_fatal": gsum_(proc, "AB", "substantiated_fatal")} for proc in ("witness", "grader")}},
                   "same_quote_pairs": same_quote, "pairs_compared": len(compared), "pairs_fatal_differs": len(differing), "cases_fatal_differs": sorted({c for c, _ in differing})}
    # ---- costs and delivery failures (retained responses only)
    costs = {}
    for proc in ("witness", "grader"):
        for src in PROPOSERS:
            key = f"{proc}-{src}"; s = summarize_usage(usage_first.get(key, []))
            fails = sum(1 for e in per_case.values() if (e[proc].get(src) or {}).get("delivery_failure"))
            costs[key] = {"calls": s["delivered"] + fails, "delivered": s["delivered"], "delivery_failures": fails, "mean_s": s["mean_s"], "max_s": s["max_s"],
                          "tokens_reported": s["tokens"]["total"], **{k: v for k, v in s.items() if k not in ("delivered", "mean_s", "max_s")}}
    chk_cost = {}
    for chk in CHECKERS:
        s = summarize_usage(usage_check[chk]["witness"] + usage_check[chk]["grader"])
        chk_cost[chk] = {"calls": s["delivered"], "mean_s": s["mean_s"], "max_s": s["max_s"], **{k: v for k, v in s.items() if k not in ("delivered", "mean_s", "max_s")},
                         "per_procedure": {proc: summarize_usage(usage_check[chk][proc]) for proc in ("witness", "grader")}}
    arms = {}
    for proc in ("witness", "grader"):
        first = [r for src in PROPOSERS for r in usage_first.get(f"{proc}-{src}", [])]
        checks = [r for chk in CHECKERS for r in usage_check[chk][proc]]
        sf, sc, sa = summarize_usage(first), summarize_usage(checks), summarize_usage(first + checks)
        arms[proc] = {"first_stage_calls": sf["delivered"], "checks": sc["delivered"], "tokens": sa["tokens"], "helper_tokens": sa["helper_tokens"],
                      "earlier_attempt_tokens": sa["earlier_attempt_tokens"], "timed": sa["timed"], "untimed_ids": sa["untimed_ids"], "sum_s": sa["sum_s"],
                      "first_stage": sf, "check_stage": sc}
    cost = {"note": "Retained responses only. tokens_reported and tokens.total count input + output + cache-read + cache-creation tokens of the requested model; "
                    "helper_tokens are auxiliary models the Claude CLI reports beside it; earlier_attempt_tokens are stored usage of attempts before the retained "
                    "reply (GLM transport). calls/delivered count every retained response; mean_s is over timed records (untimed_ids lack elapsed_seconds). "
                    "Response files replaced by a rerun are not recoverable, so these are not totals of everything spent.",
            "first_stage": costs, "checkers": chk_cost, "arms": arms}
    results = {"protocol": "PROTOCOL.md (with Amendment 1)", "analyzed_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), "frozen": freeze, "n_cases": len(cases),
               "counts": counts, "objection_totals": obj_tot, "proposer_status_agreement": agree, "cost": cost, "fatal_layer": fatal_layer, "per_case": per_case}
    rec_path = WD / "recovery.json"
    if rec_path.exists():
        # recovery.json (post hoc, author): {case: {"distinct_defect": str, "target_match": {"witness-gpt": bool, ...}, "note": str, "conclusion_change": str}}
        rec = lj(rec_path); results["recovery"] = rec
        keys = ("witness-gpt", "witness-claude", "grader-gpt", "grader-claude")
        def recovered(cid, key):
            proc, src = key.split("-")
            cls = cls_of(per_case[cid], proc, src)
            return bool((rec.get(cid) or {}).get("target_match", {}).get(key)) and cls in ("substantiated", "localized")
        def distinct_count(ids, ks):
            return len({(rec.get(i) or {}).get("distinct_defect") for i in ids if any(recovered(i, k) for k in ks) and (rec.get(i) or {}).get("distinct_defect")})
        results["recovered"] = {}
        for g in "AB":
            ids = texts(g); r = {"n": len(ids)}
            for key in keys: r[key] = sum(1 for i in ids if recovered(i, key))
            r["witness-union"] = sum(1 for i in ids if any(recovered(i, k) for k in keys[:2]))
            r["grader-union"] = sum(1 for i in ids if any(recovered(i, k) for k in keys[2:]))
            r["distinct_defects_witness"] = distinct_count(ids, keys[:2]); r["distinct_defects_grader"] = distinct_count(ids, keys[2:])
            r["distinct_defects_total"] = len({(rec.get(i) or {}).get("distinct_defect") for i in ids if (rec.get(i) or {}).get("distinct_defect")})
            results["recovered"][g] = r
    dj(WD / "results.json", results)
    write_reports(results, cases)
    brief = {k: results[k] for k in ("counts", "objection_totals", "proposer_status_agreement")}
    brief["fatal_layer"] = {k: v for k, v in fatal_layer.items() if k != "same_quote_pairs"}
    brief["cost"] = {"arms": {p: {k: v for k, v in a.items() if k not in ("first_stage", "check_stage")} for p, a in arms.items()},
                     "checkers": {c: {k: v for k, v in s.items() if k != "per_procedure"} for c, s in chk_cost.items()}}
    print(json.dumps(brief, indent=1)[:8000])
    return 0

def tex_escape(x):
    return str(x).replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#").replace("$", r"\$")

def write_reports(results, cases):
    pc = results["per_case"]
    md = ["# Witness discovery: results\n", f"Analyzed {results['analyzed_utc']} (frozen: {results['frozen']}). Protocol: PROTOCOL.md with Amendment 1. Classes: substantiated defect / localized concern / unsupported allegation / unresolved (see Amendment 1.1). The severity layer (both checkers fatal = yes) is reported beside the classes, not part of the rule.\n"]
    for g in "ABCDEF":
        md.append(f"\n## Group {g}: {GROUP_NAMES[g]}\n")
        for c in cases:
            if c["group"] != g: continue
            e = pc[c["id"]]
            md.append(f"\n### {c['id']} (P{c['problem']})\n")
            if e["record_defect"]: md.append(f"Documented defect ({e['record_obligation']}): {e['record_defect']}\n")
            for proc in ("witness", "grader"):
                for src, pe in e[proc].items():
                    label = f"{proc} procedure, {src}"
                    if pe is None: md.append(f"- **{label}**: not run\n"); continue
                    if pe.get("delivery_failure"): md.append(f"- **{label}**: delivery failure (no parseable output)\n"); continue
                    if proc == "witness": md.append(f"- **{label}**: statuses {pe['statuses']}, S_valid={pe['S_valid']}, class={pe['class']}; notes: {pe['notes']}\n")
                    else: md.append(f"- **{label}**: grade={pe['grade']} complete={pe['complete']} errors listed={pe['n_errors_listed']}, class={pe['class']}; main gap: {pe['main_gap']}\n")
                    for o in pe["objections"]:
                        anch = "" if (o.get("anchor") or {}).get("anchored") else " (quote unanchored)"
                        md.append(f"  - objection {o['tag']}: **{o['class']}**{anch}" + (" [single checker]" if o.get("single_checker") else "")
                                  + (" [both checkers fatal]" if o.get("both_fatal_yes") else "") + "\n")
                        md.append(f"    - quote: {json.dumps(o.get('quote'), ensure_ascii=False)}\n    - objection: {o.get('witness')}\n")
                        for chk, ck in (o.get("checks") or {}).items():
                            if ck: md.append(f"    - checker {chk}: {ck['verdict']} (kind {ck['evidence_kind']}, faithful {ck['quote_faithful']}, fatal {ck['fatal']}): {ck['explanation']}\n")
                            else: md.append(f"    - checker {chk}: not returned\n")
    if results.get("recovery"):
        md.append("\n## Recovery and conclusion-change judgments (post hoc, by the author, from the quotes above)\n")
        for cid, r in results["recovery"].items():
            if not isinstance(r, dict): continue
            md.append(f"- {cid}: defect '{r.get('distinct_defect')}'; target match {r.get('target_match')}; {r.get('note','')}" + (f" Conclusion change: {r['conclusion_change']}" if r.get("conclusion_change") else "") + "\n")
    fl = results.get("fatal_layer") or {}
    if fl:
        cnt = results["counts"]
        md.append("\n## Severity layer (post hoc): substantiated objections that both checkers call fatal\n")
        md.append(f"{fl['rule']}.\n\nTexts per group with a substantiated defect / with one both checkers call fatal (witness procedure; grader):\n")
        for g in "ABCDEF":
            w, r_ = cnt[g]["witness"]["union"], cnt[g]["grader"]["union"]
            md.append(f"- {g} (n={cnt[g]['n']}): witness {w['substantiated']} / {w['substantiated_fatal']}; grader {r_['substantiated']} / {r_['substantiated_fatal']}\n")
        od = fl["open_disputes"]
        md.append(f"\nOpen disputes (C, D; n={od['n']}): witness {od['witness']['substantiated']} -> {od['witness']['substantiated_fatal']}, grader {od['grader']['substantiated']} -> {od['grader']['substantiated_fatal']}.\n")
        md.append(f"\nSame quoted passage checked under both procedures by the same checker: {fl['pairs_compared']} (text, checker) pairs, fatal differs in {fl['pairs_fatal_differs']} ({', '.join(fl['cases_fatal_differs']) or 'none'}).\n")
        for r in fl["same_quote_pairs"]:
            md.append(f"- {r['case']} / {r['checker']}: witness {r['witness_objection']} verdict {r['verdict']['witness']} fatal {r['fatal']['witness']}; grader {r['grader_objection']} verdict {r['verdict']['grader']} fatal {r['fatal']['grader']}" + (" **differs**" if r["fatal_differs"] else "") + "\n")
    cost = results.get("cost") or {}
    if cost.get("arms"):
        md.append("\n## Cost over retained responses\n")
        md.append(cost.get("note", "") + "\n\n```json\n" + json.dumps({"arms": {p: {k: v for k, v in a.items() if k not in ("first_stage", "check_stage")} for p, a in cost["arms"].items()},
                                                                       "first_stage": cost["first_stage"], "checkers": {c: {k: v for k, v in s.items() if k != "per_procedure"} for c, s in cost["checkers"].items()}}, indent=1) + "\n```\n")
    (WD / "RESULTS.md").write_text("".join(md))
    # per-case table
    L = [r"\begin{tabular}{@{}clcccc@{}}", r"\toprule",
         r"Grp & Text & \multicolumn{2}{c}{Witness procedure} & \multicolumn{2}{c}{Ordinary grader} \\",
         r" & & GPT & Claude & GPT & Claude \\", r"\midrule"]
    lastg = None
    for c in cases:
        e = pc[c["id"]]
        if lastg is not None and c["group"] != lastg: L.append(r"\addlinespace[1pt]")
        lastg = c["group"]; cells = []
        for src in PROPOSERS:
            pe = e["witness"].get(src)
            cells.append("--" if pe is None else ("fail" if pe.get("delivery_failure") else f"{pe['S_valid']}/{SYM[pe['class']]}"))
        for src in PROPOSERS:
            ge = e["grader"].get(src)
            cells.append("--" if ge is None else ("fail" if ge.get("delivery_failure") else f"{ge['grade']}/{SYM[ge['class']]}"))
        L.append(f"{c['group']} & {tex_escape(c['id'])} & " + " & ".join(cells) + r" \\")
    L += [r"\bottomrule", r"\end{tabular}"]
    (WD / "table_witness.tex").write_text("\n".join(L) + "\n")
    # summary table (transposed, compact): rows = outcome classes, columns = groups; cell = witness / grader (union of the two models)
    cnt = results["counts"]
    S = [r"\begin{tabular}{@{}l" + "c" * 6 + "@{}}", r"\toprule",
         " & " + " & ".join(f"{g} ($n{{=}}{cnt[g]['n']}$)" for g in "ABCDEF") + r" \\", r"\midrule"]
    for label, key in (("substantiated defect", "substantiated"), ("\\quad both checkers fatal", "substantiated_fatal"), ("localized concern or better", "localized_or_better")):
        S.append(f"{label} & " + " & ".join(f"{cnt[g]['witness']['union'][key]} / {cnt[g]['grader']['union'][key]}" for g in "ABCDEF") + r" \\")
    S += [r"\bottomrule", r"\end{tabular}"]
    (WD / "table_witness_summary.tex").write_text("\n".join(S) + "\n")
    # macros
    m = [r"% generated by scripts/witness_discovery.py analyze; do not edit", r"\newcommand{\WITNESSN}{%d}" % results["n_cases"]]
    for g in "ABCDEF":
        w = cnt[g]["witness"]["union"]; r_ = cnt[g]["grader"]["union"]
        m.append(r"\newcommand{\WITNESSRES%s}{%d/%d}" % (g, w["localized_or_better"], cnt[g]["n"]))
        m.append(r"\newcommand{\WITNESSSUB%s}{%d/%d}" % (g, w["substantiated"], cnt[g]["n"]))
        m.append(r"\newcommand{\GRADERSUB%s}{%d/%d}" % (g, r_["substantiated"], cnt[g]["n"]))
        m.append(r"\newcommand{\GRADERRES%s}{%d/%d}" % (g, r_["localized_or_better"], cnt[g]["n"]))
        m.append(r"\newcommand{\WITNESSUNS%s}{%d}" % (g, w["unsupported"]))
        m.append(r"\newcommand{\GRADERUNS%s}{%d}" % (g, r_["unsupported"]))
        m.append(r"\newcommand{\WITNESSSUBFAT%s}{%d/%d}" % (g, w["substantiated_fatal"], cnt[g]["n"]))
        m.append(r"\newcommand{\GRADERSUBFAT%s}{%d/%d}" % (g, r_["substantiated_fatal"], cnt[g]["n"]))
    m.append(r"\newcommand{\WITNESSRESAGPT}{%d/%d}" % (cnt["A"]["witness"]["gpt"]["localized_or_better"], cnt["A"]["n"]))
    m.append(r"\newcommand{\WITNESSRESACLAUDE}{%d/%d}" % (cnt["A"]["witness"]["claude"]["localized_or_better"], cnt["A"]["n"]))
    rec = results.get("recovered", {})
    m.append(r"\newcommand{\WITNESSRECA}{%s}" % (f"{rec['A']['witness-union']}/{rec['A']['n']}" if "A" in rec else "--"))
    m.append(r"\newcommand{\WITNESSRECB}{%s}" % (f"{rec['B']['witness-union']}/{rec['B']['n']}" if "B" in rec else "--"))
    m.append(r"\newcommand{\GRADERRECA}{%s}" % (f"{rec['A']['grader-union']}/{rec['A']['n']}" if "A" in rec else "--"))
    m.append(r"\newcommand{\GRADERRECB}{%s}" % (f"{rec['B']['grader-union']}/{rec['B']['n']}" if "B" in rec else "--"))
    ot = results["objection_totals"]
    tot = lambda proc, k: sum(ot[f"{proc}-{s}"][k] for s in PROPOSERS)
    m.append(r"\newcommand{\WITNESSTOTAL}{%d}" % tot("witness", "objections")); m.append(r"\newcommand{\WITNESSCONF}{%d}" % (tot("witness", "substantiated") + tot("witness", "localized")))
    m.append(r"\newcommand{\WITNESSSUBST}{%d}" % tot("witness", "substantiated")); m.append(r"\newcommand{\WITNESSLOCAL}{%d}" % tot("witness", "localized"))
    m.append(r"\newcommand{\WITNESSCONTESTED}{%d}" % tot("witness", "unresolved")); m.append(r"\newcommand{\WITNESSREJECTED}{%d}" % tot("witness", "unsupported"))
    m.append(r"\newcommand{\WITNESSANCHORED}{%d}" % tot("witness", "anchored"))
    m.append(r"\newcommand{\GRADERTOTAL}{%d}" % tot("grader", "objections")); m.append(r"\newcommand{\GRADERSUBST}{%d}" % tot("grader", "substantiated"))
    m.append(r"\newcommand{\GRADERLOCAL}{%d}" % tot("grader", "localized")); m.append(r"\newcommand{\GRADERREJECTED}{%d}" % tot("grader", "unsupported"))
    m.append(r"\newcommand{\GRADERANCHORED}{%d}" % tot("grader", "anchored")); m.append(r"\newcommand{\GRADERCONTESTED}{%d}" % tot("grader", "unresolved"))
    m.append(r"\newcommand{\WITNESSSUBSTFAT}{%d}" % tot("witness", "substantiated_fatal")); m.append(r"\newcommand{\GRADERSUBSTFAT}{%d}" % tot("grader", "substantiated_fatal"))
    ag = results["proposer_status_agreement"]; m.append(r"\newcommand{\WITNESSAGREE}{%d/%d}" % (ag["same_status"], ag["n"]))
    fs = results["cost"]["first_stage"]
    for src in PROPOSERS:
        m.append(r"\newcommand{\WITNESSSEC%s}{%s}" % (src.upper(), fs[f"witness-{src}"]["mean_s"] if fs[f"witness-{src}"]["mean_s"] is not None else "--"))
        m.append(r"\newcommand{\GRADERSEC%s}{%s}" % (src.upper(), fs[f"grader-{src}"]["mean_s"] if fs[f"grader-{src}"]["mean_s"] is not None else "--"))
    m.append(r"\newcommand{\WITNESSFAILS}{%d}" % sum(fs[k]["delivery_failures"] for k in fs))
    # baseline comparison sentences (numbers only; the sets of C/D texts are compared, not asserted equal)
    def gsum(proc, groups, k): return sum(cnt[g][proc]["union"][k] for g in groups)
    def subst_set(proc, groups):
        return {cid for cid, e in pc.items() if e["group"] in groups and any(((e[proc].get(src) or {}).get("class") == "substantiated") for src in PROPOSERS)}
    nAB = cnt["A"]["n"] + cnt["B"]["n"]; nCD = cnt["C"]["n"] + cnt["D"]["n"]
    recAB = (rec["A"]["witness-union"] + rec["B"]["witness-union"]) if rec else None
    grecAB = (rec["A"]["grader-union"] + rec["B"]["grader-union"]) if rec else None
    ddAB = (rec["A"]["distinct_defects_total"] + rec["B"]["distinct_defects_total"]) if rec else None
    wS, gS = subst_set("witness", "CD"), subst_set("grader", "CD")
    same = "the same texts" if wS == gS else "different texts"
    def anch(proc): return sum(ot[f"{proc}-{s}"]["anchored"] for s in PROPOSERS)
    recov = (f"both procedures recovered every documented defect ({recAB} and {grecAB} of {nAB} texts, {ddAB} distinct defects)" if rec and recAB == nAB and grecAB == nAB
             else (f"the witness procedure recovered the documented defect on {recAB} of {nAB} texts and the grader on {grecAB}" if rec else "recovery is reported in Appendix~\\ref{app:witness}"))
    m.append(r"\newcommand{\WITNESSBASETXT}{On the %d known-defect texts (A, B) %s; substantiated defects on %d (witness procedure) and %d (grader) of them. On the %d open disputes (C, D) both produced substantiated defects on %d and %d texts (%s). Of the %d witness-procedure objections, %d were anchored to a verbatim quote, %d unsupported and %d unresolved; of the %d grader objections, %d, %d and %d.}" % (
        nAB, recov, gsum("witness", "AB", "substantiated"), gsum("grader", "AB", "substantiated"), nCD, gsum("witness", "CD", "substantiated"), gsum("grader", "CD", "substantiated"), same,
        tot("witness", "objections"), anch("witness"), tot("witness", "unsupported"), tot("witness", "unresolved"), tot("grader", "objections"), anch("grader"), tot("grader", "unsupported"), tot("grader", "unresolved")))
    # pooled counts on the known-defect and open-dispute texts, with and without the severity condition
    for proc, name in (("witness", "WITNESS"), ("grader", "GRADER")):
        m.append(r"\newcommand{\%sSUBAB}{%d/%d}" % (name, gsum(proc, "AB", "substantiated"), nAB)); m.append(r"\newcommand{\%sSUBCD}{%d/%d}" % (name, gsum(proc, "CD", "substantiated"), nCD))
        m.append(r"\newcommand{\%sSUBFATAB}{%d/%d}" % (name, gsum(proc, "AB", "substantiated_fatal"), nAB)); m.append(r"\newcommand{\%sSUBFATCD}{%d/%d}" % (name, gsum(proc, "CD", "substantiated_fatal"), nCD))
    # severity sentence: the fatal-conditional open-dispute counts and the same-passage fatal reversals, computed, not assumed
    fl = results.get("fatal_layer") or {}
    NAMED = {"p5-nemotron-2587b733-v2": "the P5 Nemotron display"}
    cd = fl.get("cases_fatal_differs") or []
    where = ("all on " + NAMED[cd[0]]) if len(cd) == 1 and cd[0] in NAMED else ("none" if not cd else "on " + ", ".join(tex_escape(c) for c in cd))
    m.append(r"\newcommand{\WITNESSFATALPAIRS}{%d}" % fl.get("pairs_fatal_differs", 0))
    m.append(r"\newcommand{\WITNESSFATALTXT}{Requiring both checkers to call the error fatal changes the open-dispute counts from %d/%d versus %d/%d to %d/%d versus %d/%d; the fatal judgments that differ between procedures on the same quoted passage are %d of the %d (text, checker) pairs compared (%s).}" % (
        gsum("witness", "CD", "substantiated"), nCD, gsum("grader", "CD", "substantiated"), nCD, gsum("witness", "CD", "substantiated_fatal"), nCD, gsum("grader", "CD", "substantiated_fatal"), nCD,
        fl.get("pairs_fatal_differs", 0), fl.get("pairs_compared", 0), where))
    # cost macros: first-stage calls per arm, checks per arm, timed checker means, and a sentence with the token breakdown
    arms = results["cost"]["arms"]; ck = results["cost"]["checkers"]; aw, ag_ = arms["witness"], arms["grader"]
    K = lambda n: f"{n:,}"
    m.append(r"\newcommand{\WITNESSFIRSTCALLS}{%d}" % aw["first_stage_calls"]); m.append(r"\newcommand{\GRADERFIRSTCALLS}{%d}" % ag_["first_stage_calls"])
    m.append(r"\newcommand{\WITNESSCHECKSW}{%d}" % aw["checks"]); m.append(r"\newcommand{\WITNESSCHECKSG}{%d}" % ag_["checks"])
    m.append(r"\newcommand{\WITNESSGLMSEC}{%s}" % (ck["glm"]["mean_s"] if ck["glm"]["mean_s"] is not None else "--"))
    m.append(r"\newcommand{\WITNESSGLMTIMED}{%d of %d}" % (ck["glm"]["timed"], ck["glm"]["calls"]))
    m.append(r"\newcommand{\CHECKSECGPT}{%s}" % (ck["gpt"]["mean_s"] if ck["gpt"]["mean_s"] is not None else "--"))
    m.append(r"\newcommand{\CHECKSECCLAUDE}{%s}" % (ck["claude"]["mean_s"] if ck["claude"]["mean_s"] is not None else "--"))
    untimed = sorted(set(aw["untimed_ids"] + ag_["untimed_ids"])); ucases = sorted({i.split("__")[1] if "__" in i else i for i in untimed})
    untimed_txt = ("every record carries a timing" if not untimed else
                   f"{len(untimed)} records, all on \\texttt{{{tex_escape(ucases[0])}}}, carry no timing metadata" if len(ucases) == 1 else
                   f"{len(untimed)} records on {len(ucases)} texts carry no timing metadata")
    def tk(a): t = a["tokens"]; return f"{K(t['total'])} ({K(t['input'])} input, {K(t['output'])} output, {K(t['cache_read'])} cache read, {K(t['cache_creation'])} cache creation)"
    m.append(r"\newcommand{\WITNESSCOSTTXT}{Each arm made %d first-stage calls (%d texts, two models; mean %s\,s for GPT-5.6-Sol and %s\,s for Claude Opus~5 in the witness procedure, %s and %s\,s in the grader), followed by %d checks in the witness arm and %d in the grader arm (two checkers per objection). Retained primary-model usage in tokens: witness arm %s, grader arm %s. Helper-model usage the Claude CLI records beside the requested model adds %s and %s tokens; GLM-5.3 attempts retried before the retained reply, where their usage was stored, add %s and %s. Mean checker call time: GPT-5.6-Sol %s\,s, Claude Opus~5 %s\,s, GLM-5.3 %s\,s over %d of %d timed checks (%s). Response files replaced by a rerun are not retained, so these are retained-response totals, not total spend.}" % (
        aw["first_stage_calls"], results["n_cases"], fs["witness-gpt"]["mean_s"], fs["witness-claude"]["mean_s"], fs["grader-gpt"]["mean_s"], fs["grader-claude"]["mean_s"],
        aw["checks"], ag_["checks"], tk(aw), tk(ag_), K(aw["helper_tokens"]), K(ag_["helper_tokens"]), K(aw["earlier_attempt_tokens"]), K(ag_["earlier_attempt_tokens"]),
        ck["gpt"]["mean_s"], ck["claude"]["mean_s"], ck["glm"]["mean_s"], ck["glm"]["timed"], ck["glm"]["calls"], untimed_txt))
    m.append(r"\newcommand{\WITNESSTABLE}{\input{artifacts/witness_discovery/table_witness.tex}}")
    m.append(r"\newcommand{\WITNESSSUMMARYTABLE}{\input{artifacts/witness_discovery/table_witness_summary.tex}}")
    if GEN.is_dir(): (GEN / "witness_macros.tex").write_text("\n".join(m) + "\n")
    else: print(f"note: {GEN} does not exist; gen/witness_macros.tex not written (results.json, RESULTS.md and the tables are in {WD})")

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("cases")
    p = sub.add_parser("propose"); p.add_argument("--proposer", choices=list(PROPOSERS), required=True); p.add_argument("--workers", type=int, default=4)
    p.add_argument("--timeout", type=int, default=2400); p.add_argument("--only", default=None); p.add_argument("--redo", action="store_true")
    c = sub.add_parser("check"); c.add_argument("--checker", choices=list(CHECKERS), required=True); c.add_argument("--workers", type=int, default=4)
    c.add_argument("--timeout", type=int, default=2400); c.add_argument("--only", default=None); c.add_argument("--redo", action="store_true")
    c.add_argument("--key-file", default="~/.config/vexorium/glm_api_key"); c.add_argument("--procedure", choices=["witness", "grader"], default=None)
    b = sub.add_parser("baseline"); b.add_argument("--grader", choices=list(PROPOSERS), required=True); b.add_argument("--workers", type=int, default=3)
    b.add_argument("--timeout", type=int, default=2400); b.add_argument("--only", default=None); b.add_argument("--redo", action="store_true")
    an = sub.add_parser("analyze"); an.add_argument("--freeze", action="store_true", help="classify single-checker objections from the returned checker (Amendment 1.5)")
    an.add_argument("--root", default=None, help="repository root (with artifacts/witness_discovery/) or a flat supplement (with witness_discovery/ at the top level)")
    args = ap.parse_args()
    if getattr(args, "root", None): set_root(args.root)
    return {"cases": cmd_cases, "propose": cmd_propose, "baseline": cmd_baseline, "check": cmd_check, "analyze": cmd_analyze}[args.cmd](args)

if __name__ == "__main__": sys.exit(main())
