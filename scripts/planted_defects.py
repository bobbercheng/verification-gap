#!/usr/bin/env python3
"""Planted defects: mutation testing of verification gates on proofs everyone agrees are correct.

Every base text (original, type O) has three mutants written by the author (artifacts/planted_defects/plantings.json and
texts/<base_id>/{original,F,H,G}.md): F = fatal (a false statement used downstream), H = harmless (a false display nothing uses),
G = gap (a load-bearing proof removed, the claim kept). Truth by construction: O accept/accept, F and G reject/reject, H accept
under the repair-tolerant convention (RT) and reject under the as-written convention (AW).

Subcommands
  manifest [--root DIR]         artifacts/planted_defects/manifest.json: one row per text (originals + mutants), sha256 verified
  run --gate grade|witness|closure|refadj --model gpt|claude|glm [--workers N] [--only ID,...] [--types F,G] [--redo]
      grade    ordinary 0-7 coordinator grade with error list (witness_discovery.baseline_system; the v6 baseline prompt)
      witness  obligation audit with witnesses (witness_discovery.proposer_system; per-obligation status, quote, witness, S_valid)
      closure  closure rubric rating exactly as scripts/closure_annotate.py (P3: its RUBRIC; P1/P5/P6: closure_rubric_pN.txt;
               S = number of lower/upper fields scored 2); transports codex-cli / claude-cli / Z.ai API for GLM-5.3 with the
               retry-without-thinking fallback
      refadj   reference check (reference_adjudication.system_for(problem, "check"), ledger v1 as used in v7, no procedure
               label) of every objection of the witness gate (lower/upper obligations not written_and_valid) and of the first
               two errors of the grade gate, by checkers gpt and claude
      Calls are stored under artifacts/planted_defects/runs/<gate>/<model>/<text_id>[/<objection_key>]/{request,response,parsed}.json
      (system prompt, sha256 of the text, usage, elapsed), cached results are skipped.
  analyze [--freeze] [--root DIR]
      results.json, RESULTS.md, table_planted.tex and gen/planted_macros.tex (only where DIR/gen/ exists); offline; missing
      results are "pending" everywhere. --freeze: decide combined gates from the models/checkers that returned.

Pre-specified accept rules (per text)
  grade    accept iff grade >= 5 (per model; "both": accept iff both accept, reject if either rejects)
  closure  accept iff S = 2 (per rater; "gc": GPT and Claude; "all": GPT, Claude and GLM)
  witness  accept iff S_valid = 2, S_valid recomputed as the number of lower/upper obligations with status written_and_valid
           (per model; "both": both models)
  refadj   accept iff no scored obligation (lower_bound, upper_bound: the ledger statements of OBLIGATION_MAP, or the
           obligation the witness objection names) carries an objection with consensus status not_established, and no such
           objection is unresolved (the two checkers split); RT (repair-tolerant): consensus false_display does not reject;
           AW (as-written): consensus false_display also rejects. Objections from both witness models and both graders are
           pooled ("all"); "witness" and "grade" variants use one source gate. Problems without ledger statements (P4): n/a.
  Combined gates without --freeze are pending while any of their components is pending.
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, difflib, hashlib, json, pathlib, re, statistics, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
PD = ART / "planted_defects"
WD = ART / "witness_discovery"
GEN = ROOT / "gen"
sys.path.insert(0, str(ROOT / "scripts"))
# witness_discovery, closure_annotate, cli_transport and reference_adjudication are imported by `run` only; `manifest` and
# `analyze` run offline from a supplement that ships none of them.

def set_root(root) -> None:
    """--root DIR: a repository root (DIR/artifacts/planted_defects/) or a flat supplement (DIR/planted_defects/)."""
    global ROOT, ART, PD, WD, GEN
    root = pathlib.Path(root).resolve()
    if (root / "artifacts" / "planted_defects").is_dir(): ROOT, ART = root, root / "artifacts"
    elif (root / "planted_defects").is_dir(): ROOT, ART = root, root
    else: sys.exit(f"--root {root}: found neither artifacts/planted_defects/ nor planted_defects/")
    PD, WD, GEN = ART / "planted_defects", ART / "witness_discovery", root / "gen"

MODELS = {"gpt": ("codex-cli", "gpt-5.6-sol"), "claude": ("claude-cli", "claude-opus-5"), "glm": ("anthropic", "glm-5.3")}
GATES = ("grade", "witness", "closure", "refadj")
GATE_MODELS = {"grade": ("gpt", "claude"), "witness": ("gpt", "claude"), "closure": ("gpt", "claude", "glm"), "refadj": ("gpt", "claude")}
REFADJ_SOURCES = (("witness", "gpt"), ("witness", "claude"), ("grade", "gpt"), ("grade", "claude"))
TYPES = ("O", "F", "H", "G")
TYPE_NAMES = {"O": "original", "F": "fatal", "H": "harmless display", "G": "gap"}
TRUTH_BY_TYPE = {"O": {"AW": "accept", "RT": "accept"}, "F": {"AW": "reject", "RT": "reject"}, "G": {"AW": "reject", "RT": "reject"}, "H": {"AW": "reject", "RT": "accept"}}
OBLIGATIONS = ("reduction", "lower_bound", "upper_bound")
CHECKED = ("lower_bound", "upper_bound")
MAX_CHARS = 120000       # as in the closure instrument and witness_discovery
GRADE_MIN = 5            # grade gate threshold
LOCUS_WINDOW = 200       # characters around the planted hunk that count as "near"
QUOTE_MIN, QUOTE_MAX = 40, 400
LEDGER_VERSION = "v1 (reference_adjudication.LEDGER as used in v7, unedited)"
# ledger ids per scored obligation, per problem: must equal reference_adjudication.OBLIGATION_MAP (asserted when that module loads)
OBLIGATION_MAP = {
    "5": {"lower_bound": ["L5.1"], "upper_bound": ["L5.2", "L5.3", "L5.4", "L5.5"]},
    "3": {"lower_bound": ["L3.3"], "upper_bound": ["L3.2"]},
    "6": {"lower_bound": ["L6.2"], "upper_bound": ["L6.3"]},
    "1": {"lower_bound": ["L1.1"], "upper_bound": ["L1.2"]},
    "4": {"lower_bound": [], "upper_bound": []},
}
RULES = {
    "grade": f"accept iff grade >= {GRADE_MIN}; combined 'both' = accept iff both models accept (reject if either rejects)",
    "grade7": "accept iff grade = 7; 'both' = both models. Read post hoc from the stage-1 grade responses; no additional calls",
    "gradec": "accept iff the same grading call returned complete = true; 'both' = both models. Read post hoc from the stage-1 grade responses; no additional calls were made",
    "closure": "accept iff S = 2 with S = [lower_bound == 2] + [upper_bound == 2]; 'gc' = GPT and Claude, 'all' = GPT, Claude and GLM",
    "witness": "accept iff S_valid = 2, S_valid = number of lower_bound/upper_bound obligations with status written_and_valid (recomputed from the statuses); 'both' = both models",
    "refadj": "objections: witness-gate lower/upper obligations with status != written_and_valid (both models) and the first two errors of each grader; each checked by GPT and Claude with the v1 ledger; "
              "consensus = both checkers' status_as_written equal, else split; scored = the objection's obligation is lower/upper or a checker's affected_statement lies in OBLIGATION_MAP[lower/upper]; "
              "accept iff no scored objection has consensus not_established and no scored objection is split (RT); AW additionally rejects on consensus false_display; pending while a source gate or a checker is missing (unless --freeze); n/a where the ledger has no statements (P4)",
    "truth": "O accept/accept; F, G reject/reject; H accept under RT and reject under AW",
    "locus": f"in_hunk: the objection's quote (matched as in witness_discovery.anchored, position-preserving) overlaps a changed span of the mutant text (line diff against original.md, refined to characters; plus the hunk strings of plantings.json where given); near_hunk: within {LOCUS_WINDOW} characters",
    "certificate": "characters of quote + witness (grade gate: quote + description) per objection; medians over objections on mutant texts, against the median length of those texts",
}

def sha256(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def lj(p):
    try: return json.load(open(p))
    except (OSError, ValueError): return None
def dj(p, o): pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True); pathlib.Path(p).write_text(json.dumps(o, indent=1, ensure_ascii=False))
def now() -> str: return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
def runs_dir() -> pathlib.Path: return PD / "runs"

# ---------------------------------------------------------------- anchoring (same normalization as witness_discovery, position-preserving)
NORM_DROP = set("*_$\\")

def norm_map(text: str):
    """Normalized text (markup characters dropped, whitespace runs collapsed, stripped) and, per normalized character, its index in text."""
    out, idx, prev_space = [], [], False
    for i, ch in enumerate(text):
        if ch in NORM_DROP: continue
        if ch.isspace():
            if prev_space: continue
            out.append(" "); idx.append(i); prev_space = True
        else: out.append(ch); idx.append(i); prev_space = False
    s, e = 0, len(out)
    while s < e and out[s] == " ": s += 1
    while e > s and out[e - 1] == " ": e -= 1
    return "".join(out[s:e]), idx[s:e]

def find_span(quote, text):
    """(start, end, how) of the quote in text under the anchoring normalization, or None."""
    if not quote or not isinstance(quote, str) or not text: return None
    q, _ = norm_map(quote); t, tm = norm_map(text)
    if q:
        p = t.find(q)
        if p >= 0: return (tm[p], tm[p + len(q) - 1] + 1, "normalized")
    q2 = re.sub(r"\s", "", q)
    pairs = [(c, i) for c, i in zip(t, tm) if not c.isspace()]
    t2 = "".join(c for c, _ in pairs)
    if q2:
        p = t2.find(q2)
        if p >= 0: return (pairs[p][1], pairs[p + len(q2) - 1][1] + 1, "matched without spaces")
    return None

def anchored(quote, text) -> dict:
    if not quote or not isinstance(quote, str): return {"anchored": False, "reason": "no quote"}
    reason = "short" if len(quote) < QUOTE_MIN else ("long" if len(quote) > QUOTE_MAX else None)
    sp = find_span(quote, text)
    if sp: return {"anchored": True, "length": len(quote), "length_ok": reason is None, "reason": reason if sp[2] == "normalized" else sp[2], "span": [sp[0], sp[1]]}
    return {"anchored": False, "length": len(quote), "length_ok": reason is None, "reason": "not found"}

# ---------------------------------------------------------------- manifest
def problem_of(base_id: str, hint, cases: dict) -> str:
    if hint: return str(hint)
    if base_id in cases: return str(cases[base_id]["problem"])
    m = re.match(r"p(\d)-", base_id)
    return m.group(1) if m else "3"

def author_of(base_id: str, hint, cases: dict):
    if hint: return hint
    if cases.get(base_id, {}).get("author_lab"): return cases[base_id]["author_lab"]
    s = base_id.lower()
    for key, lab in (("gpt-5.6", "gpt"), ("gpt56", "gpt"), ("claude", "claude"), ("kimi", "kimi"), ("deepseek", "deepseek"), ("grok", "grok"), ("nemotron", "nemotron"), ("glm", "glm"), ("muse", "muse")):
        if key in s: return lab
    return None

def load_plantings():
    p = PD / "plantings.json"
    d = lj(p) if p.exists() else None
    if d is None: return None
    if isinstance(d, list): return {"entries": [e for e in d if isinstance(e, dict)], "meta": {}}
    for k in ("plantings", "entries", "mutants", "texts", "items"):
        if isinstance(d.get(k), list): return {"entries": [e for e in d[k] if isinstance(e, dict)], "meta": {kk: vv for kk, vv in d.items() if kk != k}}
    return {"entries": [dict(v, id=v.get("id", k)) for k, v in d.items() if isinstance(v, dict)], "meta": {}}

def hunk_strings(entry) -> dict:
    """Strings that locate the planting (schema-tolerant): mutant-side text (present in the mutant) and original-side text (removed)."""
    mut, orig = [], []
    def walk(obj, key=""):
        if isinstance(obj, dict):
            for k, v in obj.items(): walk(v, k)
        elif isinstance(obj, list):
            for v in obj: walk(v, key)
        elif isinstance(obj, str) and obj.strip():
            k = key.lower()
            if "diff" in k or "patch" in k:
                for ln in obj.splitlines():
                    if ln.startswith("+") and not ln.startswith("+++") and ln[1:].strip(): mut.append(ln[1:])
                    elif ln.startswith("-") and not ln.startswith("---") and ln[1:].strip(): orig.append(ln[1:])
            elif any(t in k for t in ("hunk", "snippet", "replacement", "inserted", "after", "new_text", "mutant_text", "mutated_text")):
                (orig if any(t in k for t in ("orig", "old", "before", "removed", "deleted")) else mut).append(obj)
    walk(entry)
    return {"mutant": mut, "original": orig}

def text_path(row) -> pathlib.Path:
    p = pathlib.Path(row["text"])
    return p if p.is_absolute() else PD / p

def row_for(tid, base, typ, problem, author, path, expected_sha, entry) -> dict:
    path = pathlib.Path(path) if path is not None else None
    exists = path is not None and path.exists()
    b = path.read_bytes() if exists else None
    sha = sha256(b) if b is not None else None
    try: rel = str(path.resolve().relative_to(PD.resolve())) if path is not None else None
    except ValueError: rel = str(path)
    truth = dict(TRUTH_BY_TYPE[typ])
    for k, v in ((entry or {}).get("truth") or {}).items():
        if k.upper() in truth and isinstance(v, str): truth[k.upper()] = v
    keep = {k: v for k, v in (entry or {}).items() if k not in ("id", "base_id", "base", "type", "problem", "truth", "sha256_mutant", "sha256")}
    return {"id": tid, "base_id": base, "type": typ, "type_name": TYPE_NAMES[typ], "problem": problem, "author": author, "text": rel, "exists": exists,
            "bytes": len(b) if b is not None else None, "sha256": sha, "sha256_expected": expected_sha,
            "sha256_ok": None if (expected_sha is None or sha is None) else sha == expected_sha, "truth": truth,
            "obligation": (entry or {}).get("obligation"), "ledger_statement": (entry or {}).get("ledger_statement"),
            "hunk": hunk_strings(entry) if entry else None, "planting": keep or None}

def build_manifest() -> dict:
    cases = {c["id"]: c for c in ((lj(WD / "cases.json") or {}).get("cases") or [])}
    pl = load_plantings(); entries = pl["entries"] if pl else []
    def base_of(e): return e.get("base_id") or e.get("base")
    bases = []
    for e in entries:
        if base_of(e) and base_of(e) not in bases: bases.append(base_of(e))
    if (PD / "texts").is_dir():
        for d in sorted((PD / "texts").iterdir()):
            if (d / "original.md").exists() and d.name not in bases: bases.append(d.name)
    source = "plantings.json" if entries else ("texts/" if bases else "cases.json (group E controls; plantings.json absent)")
    if not bases: bases = [cid for cid, c in cases.items() if c.get("group") == "E"]
    rows = []
    for b in bases:
        ents = [e for e in entries if base_of(e) == b]
        problem = problem_of(b, next((e.get("problem") for e in ents if e.get("problem")), None), cases)
        author = author_of(b, next((e.get("author") or e.get("author_lab") for e in ents if e.get("author") or e.get("author_lab")), None), cases)
        opath = PD / "texts" / b / "original.md"
        if not opath.exists() and b in cases: opath = pathlib.Path(cases[b]["path"])
        exp = next((e.get(k) for e in ents for k in ("sha256_original", "sha256_base", "original_sha256", "base_sha256") if e.get(k)), None) or cases.get(b, {}).get("sha256")
        rows.append(row_for(b, b, "O", problem, author, opath, exp, None))
        for e in sorted(ents, key=lambda e: TYPES.index(e["type"]) if e.get("type") in TYPES else 9):
            t = e.get("type")
            if t not in ("F", "H", "G"): print(f"manifest: skipping entry {e.get('id')} with type {t!r}"); continue
            mpath = PD / "texts" / b / f"{t}.md"
            given = e.get("path") or e.get("text")
            if given and not mpath.exists():
                gp = pathlib.Path(given); mpath = gp if gp.is_absolute() else ((PD / gp) if (PD / gp).exists() else ROOT / gp)
            rows.append(row_for(e.get("id") or f"{b}__{t}", b, t, problem, author, mpath, e.get("sha256_mutant") or e.get("sha256"), e))
    return {"built_utc": now(), "plantings_present": bool(pl), "plantings_meta": (pl or {}).get("meta"), "base_source": source,
            "n_texts": len(rows), "n_base": len(bases), "n_mutants": sum(1 for r in rows if r["type"] != "O"), "rows": rows}

def cmd_manifest(args):
    m = build_manifest(); dj(PD / "manifest.json", m)
    for r in m["rows"]:
        st = "ok" if r["sha256_ok"] else ("MISMATCH" if r["sha256_ok"] is False else ("unverified" if r["exists"] else "MISSING"))
        print(f"{r['type']} {r['id']:44s} P{r['problem']} {str(r['author']):8s} {str(r['bytes']):>6s}B {(r['sha256'] or '')[:12]:12s} {st}")
    print(f"{m['n_texts']} texts ({m['n_base']} base, {m['n_mutants']} mutants) from {m['base_source']}; written {PD / 'manifest.json'}")
    return 0

def rows_for_run(args):
    rows = build_manifest()["rows"]
    if args.only:
        sel = set(args.only.split(",")); rows = [r for r in rows if r["id"] in sel or r["base_id"] in sel]
    if getattr(args, "types", None): rows = [r for r in rows if r["type"] in set(args.types.split(","))]
    return rows

# ---------------------------------------------------------------- transports and prompts (generation time only)
def closure_rubric(problem: str) -> str:
    if problem == "3":
        import closure_annotate  # noqa: E402
        return closure_annotate.RUBRIC
    return (ART / f"closure_rubric_p{problem}.txt").read_text()

def closure_call(kind: str, mname: str, system: str, user: str, key: str, timeout: int):
    """The closure instrument's call, as scripts/closure_annotate.py annotate() makes it: CLI transports through closure_annotate.call
    (Claude CLI / Codex CLI, timeout capped at 1800 s); GLM-5.3 through the Z.ai API with thinking (max_tokens 30000, budget 16000,
    the settings of the paper's re-rating passes) and one retry without thinking when no JSON came back; 429 backoff 0/20/40/80/160/320 s."""
    import closure_annotate as CA  # noqa: E402
    import witness_discovery as W  # noqa: E402
    attempts, earlier = [], []
    if kind in ("claude-cli", "codex-cli"):
        body = {"model": mname, "max_tokens": 12000, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        rounds = ((0, body),)
    else:
        b0 = {"model": mname, "max_tokens": 30000, "system": system, "messages": [{"role": "user", "content": user}], "thinking": {"type": "enabled", "budget_tokens": 16000}}
        b1 = dict(b0, thinking={"type": "disabled"})
        rounds = ((0, b0), (1, b1))
    status, resp, parsed, lenient = None, {}, None, False
    t_all = time.time()
    for attempt, body in rounds:
        t0 = time.time()
        for backoff in (0, 20, 40, 80, 160, 320):
            if backoff: time.sleep(backoff)
            status, resp = CA.call("https://api.z.ai/api/anthropic", key, body, timeout, kind if kind != "anthropic" else "anthropic")
            if status != 429 and "rate_limit" not in json.dumps(resp)[:400]: break
        txt = W.resp_text(resp) if (status == 200 and isinstance(resp, dict)) else ""
        parsed = CA.extract_json(txt) if txt else None
        if parsed is None and txt:
            parsed = W.extract_json(txt); lenient = parsed is not None
        attempts.append({"attempt": attempt, "status": status, "stop": resp.get("stop_reason") if isinstance(resp, dict) else None,
                         "usage": resp.get("usage") if isinstance(resp, dict) else None, "sec": round(time.time() - t0, 1), "parsed": parsed is not None})
        if parsed is not None: break
        earlier.append(resp)
    if isinstance(resp, dict):
        resp["elapsed_seconds"] = round(time.time() - t_all, 1); resp["attempts"] = attempts
        if earlier: resp["earlier_attempt_responses"] = earlier
    return status, resp, parsed, {"attempts": attempts, "lenient_parse": lenient}

def objection_pool(text_id: str):
    """Objections of one text for the reference check: witness-gate lower/upper obligations not written_and_valid (both models) and
    the first two errors of each grader. Returns (objections, missing source gates)."""
    pool, missing = [], []
    for gate, m in REFADJ_SOURCES:
        pj = lj(runs_dir() / gate / m / text_id / "parsed.json")
        if pj is None: missing.append(f"{gate}-{m}"); continue
        parsed = pj.get("parsed") or {}
        if gate == "witness":
            obls = parsed.get("obligations") or {}
            for ob in CHECKED:
                o = obls.get(ob)
                if isinstance(o, dict) and o.get("status") != "written_and_valid" and (o.get("quote") or o.get("witness")):
                    pool.append({"key": f"witness-{m}__{ob}", "source_gate": "witness", "source_model": m, "tag": ob, "obligation": ob, "status": o.get("status"),
                                 "quote": o.get("quote"), "objection": o.get("witness"), "load_bearing": o.get("load_bearing")})
        else:
            errs = [x for x in (parsed.get("errors") or []) if isinstance(x, dict)][:2]
            for i, x in enumerate(errs):
                pool.append({"key": f"grade-{m}__e{i}", "source_gate": "grade", "source_model": m, "tag": f"e{i}", "obligation": "unspecified",
                             "status": "error reported by an ordinary grader", "quote": x.get("quote"), "objection": x.get("description"), "load_bearing": None})
    return pool, missing

def run_text(args, row, key):
    import witness_discovery as W  # noqa: E402
    gate, model = args.gate, args.model; kind, mname = MODELS[model]
    out = runs_dir() / (gate + getattr(args, "tag", "") or gate) / model / row["id"]
    if (out / "parsed.json").exists() and not args.redo: return "cached"
    if not row["exists"]: print(f"[{gate} {model}] {row['id']}: text missing ({row['text']})", flush=True); return "missing"
    if row["sha256_ok"] is False: print(f"[{gate} {model}] {row['id']}: sha256 differs from plantings.json; not run", flush=True); return "sha_mismatch"
    raw = text_path(row).read_bytes(); assert sha256(raw) == row["sha256"], row["id"]
    text = raw.decode(errors="replace")
    if gate == "grade": system, user, src = W.baseline_system(row["problem"]), "## Write-up to grade\n\n" + text[:MAX_CHARS], "witness_discovery.baseline_system"
    elif gate == "witness": system, user, src = W.proposer_system(row["problem"]), "## Write-up to audit\n\n" + text[:MAX_CHARS], "witness_discovery.proposer_system"
    else: system, user, src = closure_rubric(row["problem"]), "## Write-up to grade\n\n" + text[:MAX_CHARS], ("closure_annotate.RUBRIC" if row["problem"] == "3" else f"closure_rubric_p{row['problem']}.txt")
    t0 = now(); extra = {}
    if gate == "closure": status, resp, parsed, extra = closure_call(kind, mname, system, user, key, args.timeout)
    else:
        status, resp = W.call_model(kind, mname, system, user, key, args.timeout)
        txt = W.resp_text(resp) if (status == 200 and isinstance(resp, dict)) else ""
        parsed = W.extract_json(txt) if txt else None
    base = {"gate": gate, "model": model, "transport": kind, "model_name": mname, "text_id": row["id"], "base_id": row["base_id"], "type": row["type"], "problem": row["problem"]}
    dj(out / "request.json", {**base, "text_sha256": row["sha256"], "text_path": row["text"], "system_sha256": sha256(system.encode()), "system": system, "prompt_source": src,
                              "user_chars": len(user), "started_utc": t0})
    dj(out / "response.json", {"status": status, "response": resp})
    if parsed is None:
        print(f"[{gate} {model}] {row['id']}: FAILED status={status} {str(resp)[:200]}", flush=True); return "failed"
    rec = {**base, "status": status, "usage": W.usage_of(resp) if isinstance(resp, dict) else {}, "parsed": parsed, **extra}
    if gate == "grade":
        errs = parsed.get("errors") or []
        rec["anchors"] = [anchored(e.get("quote"), text) if isinstance(e, dict) else {"anchored": False, "reason": "malformed"} for e in errs]
        msg = f"grade={parsed.get('grade')} errors={len(errs)}"
    elif gate == "witness":
        obls = parsed.get("obligations") or {}
        rec["anchors"] = {ob: anchored((obls.get(ob) or {}).get("quote"), text) for ob in OBLIGATIONS if isinstance(obls.get(ob), dict) and obls[ob].get("status") != "written_and_valid"}
        msg = f"{ {ob: (obls.get(ob) or {}).get('status') for ob in OBLIGATIONS} } S_valid={parsed.get('S_valid')}"
    else:
        try: S = int(parsed.get("lower_bound", 0) == 2) + int(parsed.get("upper_bound", 0) == 2)
        except Exception: S = None
        rec["S"] = S; rec["rubric_sha256"] = sha256(system.encode())
        msg = f"S={S} grades={ {k: parsed.get(k) for k in ('answer', 'reduction', 'lower_bound', 'upper_bound')} }"
    dj(out / "parsed.json", rec)
    print(f"[{gate} {model}] {row['id']}: {msg} {rec['usage'].get('elapsed_seconds')}s", flush=True)
    return "ok"

def run_refadj(args, row, o, key):
    import witness_discovery as W  # noqa: E402
    import reference_adjudication as RA  # noqa: E402
    chk = args.model; kind, mname = MODELS[chk]
    out = runs_dir() / "refadj" / chk / row["id"] / o["key"]
    if (out / "parsed.json").exists() and not args.redo: return "cached"
    if not row["exists"] or row["sha256_ok"] is False: return "missing" if not row["exists"] else "sha_mismatch"
    raw = text_path(row).read_bytes(); assert sha256(raw) == row["sha256"], row["id"]
    text = raw.decode(errors="replace")
    system = RA.system_for(row["problem"], "check")
    user = ("## Write-up\n\n" + text[:MAX_CHARS] + "\n\n## Objection\n\nQuote (claimed verbatim from the write-up): "
            + json.dumps(o["quote"], ensure_ascii=False) + "\nObjection: " + str(o["objection"]) + "\n")
    t0 = now()
    status, resp = W.call_model(kind, mname, system, user, key, args.timeout)
    txt = W.resp_text(resp) if (status == 200 and isinstance(resp, dict)) else ""
    parsed = W.extract_json(txt) if txt else None
    base = {"gate": "refadj", "checker": chk, "model": chk, "transport": kind, "model_name": mname, "text_id": row["id"], "base_id": row["base_id"], "type": row["type"], "problem": row["problem"], "objection_key": o["key"]}
    dj(out / "request.json", {**base, "text_sha256": row["sha256"], "text_path": row["text"], "system_sha256": sha256(system.encode()), "system": system,
                              "ledger_version": LEDGER_VERSION, "ledger_sha256": sha256(json.dumps(RA.LEDGER[row["problem"]]).encode()), "objection": o, "user_chars": len(user), "started_utc": t0})
    dj(out / "response.json", {"status": status, "response": resp})
    if parsed is None:
        print(f"[refadj {chk}] {row['id']}/{o['key']}: FAILED status={status} {str(resp)[:200]}", flush=True); return "failed"
    anchor = anchored(parsed.get("elsewhere_quote"), text) if parsed.get("elsewhere_quote") else None
    dj(out / "parsed.json", {**base, "status": status, "usage": W.usage_of(resp) if isinstance(resp, dict) else {}, "parsed": parsed, "elsewhere_anchor": anchor,
                             "source_gate": o["source_gate"], "source_model": o["source_model"], "tag": o["tag"]})
    print(f"[refadj {chk}] {row['id']}/{o['key']}: {parsed.get('affected_statement')} correct={parsed.get('objection_correct')} elsewhere={parsed.get('established_elsewhere')} "
          f"status={parsed.get('status_as_written')} repair={parsed.get('repair_distance')} {(W.usage_of(resp) if isinstance(resp, dict) else {}).get('elapsed_seconds')}s", flush=True)
    return "ok"

def cmd_run(args):
    import reference_adjudication as RA  # noqa: E402  (also asserts the copied obligation map)
    assert RA.OBLIGATION_MAP == OBLIGATION_MAP, "OBLIGATION_MAP differs from reference_adjudication.OBLIGATION_MAP"
    key = pathlib.Path(args.key_file).expanduser().read_text().strip() if args.model == "glm" else ""
    rows = rows_for_run(args)
    if args.gate == "refadj":
        jobs = []
        for r in rows:
            pool, missing = objection_pool(r["id"])
            if missing: print(f"[refadj] {r['id']}: source gates not yet run: {missing}", flush=True)
            jobs += [(r, o) for o in pool]
        print(f"{len(jobs)} objections on {len(rows)} texts for checker {args.model}", flush=True)
        with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
            res = list(ex.map(lambda j: run_refadj(args, j[0], j[1], key), jobs))
    else:
        print(f"{len(rows)} texts for gate {args.gate}, model {args.model}", flush=True)
        with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
            res = list(ex.map(lambda r: run_text(args, r, key), rows))
    print({r: res.count(r) for r in set(res)}); return 0

# ---------------------------------------------------------------- analysis
def changed_spans(orig: str, mut: str):
    """Character spans of the mutant text that differ from the original: a line diff, each changed block refined to characters
    (a pure deletion gives a zero-width span at the deletion point)."""
    if orig is None or mut is None or orig == mut: return []
    ol, ml = orig.splitlines(keepends=True), mut.splitlines(keepends=True)
    offs = [0]
    for ln in ml: offs.append(offs[-1] + len(ln))
    spans = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ol, ml, autojunk=False).get_opcodes():
        if tag == "equal": continue
        a, b = "".join(ol[i1:i2]), "".join(ml[j1:j2]); base = offs[j1]
        if not b: spans.append([base, base]); continue
        refined = None
        if a and len(a) <= 8000 and len(b) <= 8000:
            ops = difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
            same = sum(a2 - a1 for t2, a1, a2, _, _ in ops if t2 == "equal")
            if same >= 0.5 * max(len(a), len(b)):   # an edit inside the block: keep only the changed characters
                refined = [[base + b1, base + b2] for t2, _, _, b1, b2 in ops if t2 != "equal"]
        spans += refined if refined else [[base, offs[j2]]]
    return merge_spans(spans)

def merge_spans(spans):
    merged = []
    for s in sorted(spans):
        if merged and s[0] <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], s[1])
        else: merged.append(list(s))
    return merged

def locus_of(quote, text, spans):
    a = anchored(quote, text)
    if not spans: return {**a, "in_hunk": None, "near_hunk": None, "distance": None}
    if not a.get("anchored"): return {**a, "in_hunk": False, "near_hunk": False, "distance": None}
    s, e = a["span"]
    def dist(sp):
        lo, hi = sp
        if hi <= lo: return max(lo - e, s - lo, 0) if not (s <= lo <= e) else 0   # zero-width span
        return 0 if (s < hi and e > lo) else (lo - e if lo >= e else s - hi)
    d = min(dist(sp) for sp in spans)
    return {**a, "in_hunk": d == 0, "near_hunk": d <= LOCUS_WINDOW, "distance": d}

def combine(decs: list, freeze: bool) -> str:
    if any(d == "reject" for d in decs): return "reject"
    if any(d == "na" for d in decs) and all(d in ("na", "pending") for d in decs): return "na"
    avail = [d for d in decs if d == "accept"]
    if not avail: return "pending"
    if len(avail) < len(decs) and not freeze: return "pending"
    return "accept"

def read_run(gate, model, text_id, key=None):
    d = runs_dir() / gate / model / text_id / (key or "")
    pj = lj(d / "parsed.json"); rq = lj(d / "request.json")
    return pj, rq, (pj is None and (d / "response.json").exists())

def analyze_text(row, freeze: bool) -> dict:
    text = text_path(row).read_bytes().decode(errors="replace") if row["exists"] else None
    orig_row_path = PD / "texts" / row["base_id"] / "original.md"
    spans, span_source = [], []
    if row["type"] != "O" and text is not None:
        if orig_row_path.exists():
            spans = changed_spans(orig_row_path.read_bytes().decode(errors="replace"), text); span_source.append("diff against original.md")
        for h in ((row.get("hunk") or {}).get("mutant") or []):
            sp = find_span(h, text)
            if sp: spans.append([sp[0], sp[1]]); span_source.append("plantings.json hunk string")
        spans = merge_spans(spans)
    e = {"id": row["id"], "base_id": row["base_id"], "type": row["type"], "problem": row["problem"], "author": row["author"], "truth": row["truth"], "exists": row["exists"],
         "sha256_ok": row["sha256_ok"], "text_chars": len(text) if text is not None else None, "obligation": row.get("obligation"), "ledger_statement": row.get("ledger_statement"),
         "hunk_spans": spans, "hunk_span_source": sorted(set(span_source)), "gates": {"grade": {}, "witness": {}, "closure": {}, "refadj": {}}, "decisions": {}}
    def stale(rq): return bool(rq and row["sha256"] and rq.get("text_sha256") != row["sha256"])
    # grade gate
    for m in GATE_MODELS["grade"]:
        pj, rq, failed = read_run("grade", m, row["id"])
        if pj is None: e["gates"]["grade"][m] = {"decision": "pending", "delivery_failure": failed}; continue
        p = pj.get("parsed") or {}; g = p.get("grade")
        try: g = int(g)
        except (TypeError, ValueError): g = None
        errs = [x for x in (p.get("errors") or []) if isinstance(x, dict)]
        objs = [{"tag": f"e{i}", "quote": x.get("quote"), "objection": x.get("description"), "locus": locus_of(x.get("quote"), text, spans),
                 "cert_chars": len(x.get("quote") or "") + len(x.get("description") or ""), "in_pool": i < 2} for i, x in enumerate(errs)]
        dec = "pending" if (g is None or stale(rq)) else ("accept" if g >= GRADE_MIN else "reject")
        e["gates"]["grade"][m] = {"decision": dec, "grade": g, "complete": p.get("complete"), "main_gap": p.get("main_gap"), "n_errors": len(errs), "objections": objs,
                                  "stale": stale(rq), "usage": pj.get("usage")}
    e["gates"]["grade"]["both"] = {"decision": combine([e["gates"]["grade"][m]["decision"] for m in GATE_MODELS["grade"]], freeze)}
    # strict score rule (both graders at 7), from the same responses
    e["gates"]["grade7"] = {}
    for m in GATE_MODELS["grade"]:
        gm = e["gates"]["grade"][m]; g = gm.get("grade")
        e["gates"]["grade7"][m] = {"decision": "pending" if gm["decision"] == "pending" or g is None else ("accept" if g >= 7 else "reject"), "grade": g}
    e["gates"]["grade7"]["both"] = {"decision": combine([e["gates"]["grade7"][m]["decision"] for m in GATE_MODELS["grade"]], freeze)}
    # completeness verdict of the SAME grading call, read as an acceptance rule (post-hoc baseline; no additional model calls)
    e["gates"]["gradec"] = {}
    for m in GATE_MODELS["grade"]:
        gm = e["gates"]["grade"][m]; c = gm.get("complete")
        d = "pending" if gm["decision"] == "pending" or c is None else ("accept" if c is True else "reject")
        e["gates"]["gradec"][m] = {"decision": d, "complete": c, "grade": gm.get("grade"), "main_gap": gm.get("main_gap")}
    e["gates"]["gradec"]["both"] = {"decision": combine([e["gates"]["gradec"][m]["decision"] for m in GATE_MODELS["grade"]], freeze)}
    # witness gate
    for m in GATE_MODELS["witness"]:
        pj, rq, failed = read_run("witness", m, row["id"])
        if pj is None: e["gates"]["witness"][m] = {"decision": "pending", "delivery_failure": failed}; continue
        p = pj.get("parsed") or {}; obls = p.get("obligations") or {}
        statuses = {ob: (obls.get(ob) or {}).get("status") if isinstance(obls.get(ob), dict) else None for ob in OBLIGATIONS}
        S_derived = sum(1 for ob in CHECKED if statuses[ob] == "written_and_valid")
        objs = []
        for ob in CHECKED:
            o = obls.get(ob)
            if isinstance(o, dict) and o.get("status") != "written_and_valid" and (o.get("quote") or o.get("witness")):
                objs.append({"tag": ob, "status": o.get("status"), "quote": o.get("quote"), "objection": o.get("witness"), "load_bearing": o.get("load_bearing"),
                             "locus": locus_of(o.get("quote"), text, spans), "cert_chars": len(o.get("quote") or "") + len(str(o.get("witness") or "")), "in_pool": True})
        dec = "pending" if stale(rq) else ("accept" if S_derived == 2 else "reject")
        e["gates"]["witness"][m] = {"decision": dec, "statuses": statuses, "S_valid": S_derived, "S_valid_reported": p.get("S_valid"), "S_valid_mismatch": p.get("S_valid") != S_derived,
                                    "wrong_answer_stated": p.get("wrong_answer_stated"), "notes": p.get("notes"), "objections": objs, "stale": stale(rq), "usage": pj.get("usage")}
    e["gates"]["witness"]["both"] = {"decision": combine([e["gates"]["witness"][m]["decision"] for m in GATE_MODELS["witness"]], freeze)}
    # closure gate
    for m in GATE_MODELS["closure"]:
        pj, rq, failed = read_run("closure", m, row["id"])
        if pj is None: e["gates"]["closure"][m] = {"decision": "pending", "delivery_failure": failed}; continue
        p = pj.get("parsed") or {}
        try: S = int(p.get("lower_bound", 0) == 2) + int(p.get("upper_bound", 0) == 2)
        except Exception: S = None
        dec = "pending" if (S is None or stale(rq)) else ("accept" if S == 2 else "reject")
        e["gates"]["closure"][m] = {"decision": dec, "S": S, "fields": {k: p.get(k) for k in ("answer", "reduction", "lower_bound", "upper_bound")}, "notes": p.get("notes"),
                                    "attempts": len(pj.get("attempts") or []) or None, "lenient_parse": pj.get("lenient_parse"), "stale": stale(rq), "usage": pj.get("usage")}
    e["gates"]["closure"]["gc"] = {"decision": combine([e["gates"]["closure"][m]["decision"] for m in ("gpt", "claude")], freeze)}
    e["gates"]["closure"]["all"] = {"decision": combine([e["gates"]["closure"][m]["decision"] for m in GATE_MODELS["closure"]], freeze)}
    # reference adjudication gate
    pool, missing = objection_pool(row["id"])
    scored_ids = {i for ob in CHECKED for i in OBLIGATION_MAP.get(row["problem"], {}).get(ob, [])}
    ledger_ok = bool(scored_ids)
    objs = []
    for o in pool:
        checks = {}
        for chk in GATE_MODELS["refadj"]:
            pj, rq, failed = read_run("refadj", chk, row["id"], o["key"])
            if pj is None: checks[chk] = None; continue
            p = pj.get("parsed") or {}
            checks[chk] = {**{f: p.get(f) for f in ("affected_statement", "objection_correct", "established_elsewhere", "elsewhere_quote", "status_as_written", "repair_distance", "explanation")},
                           "elsewhere_anchor": pj.get("elsewhere_anchor"), "stale": stale(rq), "usage": pj.get("usage")}
        ret = {c: v for c, v in checks.items() if v and not v.get("stale")}
        st = [v.get("status_as_written") for v in ret.values()]
        if len(ret) == len(GATE_MODELS["refadj"]): cons, single = (st[0] if len(set(st)) == 1 else "split"), False
        elif ret and freeze: cons, single = st[0], True
        else: cons, single = "pending", False
        touched = set()
        if o["obligation"] in CHECKED: touched.add(o["obligation"])
        for v in ret.values():
            for ob in CHECKED:
                if v.get("affected_statement") in OBLIGATION_MAP.get(row["problem"], {}).get(ob, []): touched.add(ob)
        aff = sorted({str(v.get("affected_statement")) for v in ret.values()})
        objs.append({**o, "checks": checks, "consensus": cons, "single_checker": single, "affected": aff, "obligations_touched": sorted(touched), "scored": bool(touched),
                     "locus": locus_of(o.get("quote"), text, spans)})
    def decide(sub, sources, conv):
        if not ledger_ok: return "na"
        trig = ("not_established", "split") + (("false_display",) if conv == "AW" else ())
        if any(x["consensus"] in trig and x["scored"] for x in sub): return "reject"
        if any(s in missing for s in sources) and not freeze: return "pending"
        if any(x["consensus"] == "pending" for x in sub): return "pending"
        return "accept"
    variants = {"all": [f"{g}-{m}" for g, m in REFADJ_SOURCES], "witness": ["witness-gpt", "witness-claude"], "grade": ["grade-gpt", "grade-claude"],
                "witness_gpt": ["witness-gpt"], "witness_claude": ["witness-claude"]}
    e["gates"]["refadj"] = {"ledger_applicable": ledger_ok, "missing_sources": missing, "objections": objs, "variants": {}}
    for name, sources in variants.items():
        sub = [x for x in objs if f"{x['source_gate']}-{x['source_model']}" in sources]
        e["gates"]["refadj"]["variants"][name] = {"RT": decide(sub, sources, "RT"), "AW": decide(sub, sources, "AW"), "n_objections": len(sub)}
    # flat decisions
    D = e["decisions"]
    for m in list(GATE_MODELS["grade"]) + ["both"]: D[f"grade:{m}"] = e["gates"]["grade"][m]["decision"]
    for m in list(GATE_MODELS["grade"]) + ["both"]: D[f"gradec:{m}"] = e["gates"]["gradec"][m]["decision"]
    for m in list(GATE_MODELS["grade"]) + ["both"]: D[f"grade7:{m}"] = e["gates"]["grade7"][m]["decision"]
    for m in list(GATE_MODELS["witness"]) + ["both"]: D[f"witness:{m}"] = e["gates"]["witness"][m]["decision"]
    for m in list(GATE_MODELS["closure"]) + ["gc", "all"]: D[f"closure:{m}"] = e["gates"]["closure"][m]["decision"]
    for name, v in e["gates"]["refadj"]["variants"].items():
        D[f"refadj_{name}:RT"] = v["RT"]; D[f"refadj_{name}:AW"] = v["AW"]
    return e

GATE_KEYS = [("grade:gpt", "ordinary grade, GPT-5.6-Sol"), ("grade:claude", "ordinary grade, Claude Opus 5"), ("grade:both", "ordinary grade, both models"),
             ("grade7:gpt", "score = 7, GPT-5.6-Sol"), ("grade7:claude", "score = 7, Claude Opus 5"), ("grade7:both", "score = 7, both models"),
             ("gradec:gpt", "completeness verdict, GPT-5.6-Sol"), ("gradec:claude", "completeness verdict, Claude Opus 5"), ("gradec:both", "completeness verdict, both models"),
             ("closure:gpt", "closure S, GPT-5.6-Sol"), ("closure:claude", "closure S, Claude Opus 5"), ("closure:glm", "closure S, GLM-5.3"),
             ("closure:gc", "closure S, GPT and Claude"), ("closure:all", "closure S, all three raters"),
             ("witness:gpt", "witness S_valid, GPT-5.6-Sol"), ("witness:claude", "witness S_valid, Claude Opus 5"), ("witness:both", "witness S_valid, both models"),
             ("refadj_witness:RT", "witness objections + reference (RT)"), ("refadj_witness:AW", "witness objections + reference (AW)"),
             ("refadj_grade:RT", "grader errors + reference (RT)"), ("refadj_grade:AW", "grader errors + reference (AW)"),
             ("refadj_all:RT", "all objections + reference (RT)"), ("refadj_all:AW", "all objections + reference (AW)"),
             ("refadj_witness_gpt:RT", "GPT witness objections + reference (RT)"), ("refadj_witness_claude:RT", "Claude witness objections + reference (RT)")]
CLASSES = {"FG": ("F", "G"), "O": ("O",), "H": ("H",), "F": ("F",), "G": ("G",)}

def tally(per: list, key: str) -> dict:
    out = {}
    for cls, types in CLASSES.items():
        sub = [e for e in per if e["type"] in types]; decs = [e["decisions"].get(key, "pending") for e in sub]
        out[cls] = {"n": len(sub), "accepted": decs.count("accept"), "rejected": decs.count("reject"), "pending": decs.count("pending"), "na": decs.count("na"),
                    "decided": decs.count("accept") + decs.count("reject")}
    return {"classes": out, "false_accepts": {"k": out["FG"]["accepted"], **{k: out["FG"][k] for k in ("n", "pending", "na", "decided")}},
            "false_rejects": {"k": out["O"]["rejected"], **{k: out["O"][k] for k in ("n", "pending", "na", "decided")}},
            "H_accepted": {"k": out["H"]["accepted"], **{k: out["H"][k] for k in ("n", "pending", "na", "decided")}}}

def frac(t: dict) -> str:
    if t["n"] == 0: return "--"
    if t["n"] == t.get("na", 0): return "n/a"
    if t["decided"] == 0: return "pending"
    s = f"{t['k']}/{t['n'] - t.get('na', 0)}"
    if t["pending"]: s += f" ({t['pending']} pending)"
    return s

def median(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return round(statistics.median(xs)) if xs else None

def cmd_analyze(args):
    freeze = bool(args.freeze)
    man = build_manifest(); rows = man["rows"]
    per = [analyze_text(r, freeze) for r in rows]
    gates = {}
    for key, label in GATE_KEYS:
        t = tally(per, key)
        t["label"] = label
        t["by_problem"] = {p: tally([e for e in per if e["problem"] == p], key) for p in sorted({e["problem"] for e in per})}
        t["by_author"] = {a: None for a in sorted({("gpt" if e["author"] == "gpt" else "other") for e in per})}   # sorted: the report must not depend on set iteration order
        for a in list(t["by_author"]): t["by_author"][a] = tally([e for e in per if (("gpt" if e["author"] == "gpt" else "other") == a)], key)
        gates[key] = t
    # locus and certificate size over objections on mutant texts
    locus, cert = {}, {}
    for gate in ("witness", "grade"):
        for m in GATE_MODELS[gate]:
            L = {"objections": 0, "anchored": 0, "in_hunk": 0, "near_hunk": 0, "by_type": {t: {"objections": 0, "in_hunk": 0} for t in ("F", "H", "G")}}
            sizes, tlens = [], []
            for e in per:
                if e["type"] == "O": continue
                for o in (e["gates"][gate].get(m) or {}).get("objections", []):
                    if not o.get("in_pool"): continue
                    L["objections"] += 1; L["by_type"][e["type"]]["objections"] += 1
                    lc = o["locus"]
                    if lc.get("anchored"): L["anchored"] += 1
                    if lc.get("in_hunk"): L["in_hunk"] += 1; L["by_type"][e["type"]]["in_hunk"] += 1
                    if lc.get("near_hunk"): L["near_hunk"] += 1
                    sizes.append(o["cert_chars"]); tlens.append(e["text_chars"])
            locus[f"{gate}-{m}"] = L
            cert[f"{gate}-{m}"] = {"n": len(sizes), "median_cert_chars": median(sizes), "median_text_chars": median(tlens),
                                   "ratio": (round(median(sizes) / median(tlens), 4) if sizes and median(tlens) else None)}
    def pool_(prefix):
        ks = [k for k in locus if k.startswith(prefix)]
        return {f: sum(locus[k][f] for k in ks) for f in ("objections", "anchored", "in_hunk", "near_hunk")}
    locus["witness"] = pool_("witness-"); locus["grade"] = pool_("grade-"); locus["all"] = {f: locus["witness"][f] + locus["grade"][f] for f in locus["witness"]}
    def pool_cert(prefix):
        ks = [k for k in cert if k.startswith(prefix)]
        sizes, tlens = [], []
        for e in per:
            if e["type"] == "O": continue
            for k in ks:
                gate, m = k.split("-")
                for o in (e["gates"][gate].get(m) or {}).get("objections", []):
                    if o.get("in_pool"): sizes.append(o["cert_chars"]); tlens.append(e["text_chars"])
        return {"n": len(sizes), "median_cert_chars": median(sizes), "median_text_chars": median(tlens)}
    cert["witness"] = pool_cert("witness-"); cert["grade"] = pool_cert("grade-")
    cert["all_texts_median_chars"] = median([e["text_chars"] for e in per]); cert["mutant_texts_median_chars"] = median([e["text_chars"] for e in per if e["type"] != "O"])
    # refadj objection-level summary
    ra = {"objections": 0, "both_checked": 0, "by_consensus": {}, "scored": 0, "single_checker": 0}
    for e in per:
        for o in e["gates"]["refadj"]["objections"]:
            ra["objections"] += 1; ra["scored"] += int(o["scored"]); ra["single_checker"] += int(o["single_checker"])
            ra["both_checked"] += int(all(o["checks"].get(c) for c in GATE_MODELS["refadj"]))
            ra["by_consensus"][o["consensus"]] = ra["by_consensus"].get(o["consensus"], 0) + 1
    # delivery / usage
    usage = {}
    for gate in ("grade", "witness", "closure"):
        for m in GATE_MODELS[gate]:
            secs = [((e["gates"][gate].get(m) or {}).get("usage") or {}).get("elapsed_seconds") for e in per]
            secs = [s for s in secs if isinstance(s, (int, float))]
            usage[f"{gate}-{m}"] = {"delivered": sum(1 for e in per if (e["gates"][gate].get(m) or {}).get("decision") not in (None, "pending") or (e["gates"][gate].get(m) or {}).get("usage")),
                                    "failures": sum(1 for e in per if (e["gates"][gate].get(m) or {}).get("delivery_failure")), "timed": len(secs), "mean_s": round(sum(secs) / len(secs), 1) if secs else None, "max_s": max(secs) if secs else None}
    for chk in GATE_MODELS["refadj"]:
        secs = [((o["checks"].get(chk) or {}).get("usage") or {}).get("elapsed_seconds") for e in per for o in e["gates"]["refadj"]["objections"]]
        secs = [s for s in secs if isinstance(s, (int, float))]
        usage[f"refadj-{chk}"] = {"delivered": sum(1 for e in per for o in e["gates"]["refadj"]["objections"] if o["checks"].get(chk)), "timed": len(secs), "mean_s": round(sum(secs) / len(secs), 1) if secs else None, "max_s": max(secs) if secs else None}
    pending_primary = {k: gates[k]["classes"]["FG"]["pending"] + gates[k]["classes"]["O"]["pending"] + gates[k]["classes"]["H"]["pending"] for k in ("grade:both", "closure:all", "witness:both", "refadj_all:RT")}
    results = {"protocol": "artifacts/planted_defects/PROTOCOL_PLANTINGS.md", "analyzed_utc": now(), "frozen": freeze, "rules": RULES, "manifest": {k: v for k, v in man.items() if k != "rows"},
               "n_texts": len(rows), "n_base": man["n_base"], "n_mutants": man["n_mutants"], "n_by_type": {t: sum(1 for r in rows if r["type"] == t) for t in TYPES},
               "texts_missing": [r["id"] for r in rows if not r["exists"]], "sha_mismatch": [r["id"] for r in rows if r["sha256_ok"] is False],
               "gates": gates, "locus": locus, "certificate": cert, "refadj_objections": ra, "usage": usage, "pending_primary": pending_primary, "per_text": per}
    dj(PD / "results.json", results)
    write_reports(results, rows)
    brief = {"n_texts": len(rows), "n_mutants": man["n_mutants"], "missing": len(results["texts_missing"]), "pending_primary": pending_primary,
             **{k: {"false_accepts": frac(gates[k]["false_accepts"]), "false_rejects": frac(gates[k]["false_rejects"]), "H_accepted": frac(gates[k]["H_accepted"])} for k in ("grade:both", "closure:all", "witness:both", "refadj_all:RT", "refadj_all:AW")},
             "locus": locus["all"], "refadj_objections": ra}
    print(json.dumps(brief, indent=1)); return 0

def tex_escape(x):
    return str(x).replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#").replace("$", r"\$")

def short(s, n=160):
    s = str(s) if s is not None else ""
    return (s[:n] + "...") if len(s) > n else s

def write_reports(results, rows):
    per = {e["id"]: e for e in results["per_text"]}; G = results["gates"]; L = results["locus"]; C = results["certificate"]
    md = ["# Planted defects: results\n", f"Analyzed {results['analyzed_utc']} (frozen: {results['frozen']}). Texts: {results['n_texts']} ({results['n_base']} base, {results['n_mutants']} mutants; by type {results['n_by_type']}); "
          f"missing texts: {results['texts_missing'] or 'none'}; sha256 mismatches: {results['sha_mismatch'] or 'none'}.\n", "\nRules (pre-specified):\n"]
    for k, v in results["rules"].items(): md.append(f"- {k}: {v}\n")
    md.append("\n## Summary\n\n| gate | false accepts (F+G) | false rejects (O) | H accepted | pending |\n|---|---|---|---|---|\n")
    for key, label in GATE_KEYS:
        t = G[key]; pend = sum(t["classes"][c]["pending"] for c in ("FG", "O", "H"))
        md.append(f"| {label} (`{key}`) | {frac(t['false_accepts'])} | {frac(t['false_rejects'])} | {frac(t['H_accepted'])} | {pend} |\n")
    md.append(f"\nLocus (objections on mutants; quote inside / within {LOCUS_WINDOW} chars of the planted hunk): witness {L['witness']['in_hunk']}/{L['witness']['objections']} (near {L['witness']['near_hunk']}), "
              f"grader {L['grade']['in_hunk']}/{L['grade']['objections']} (near {L['grade']['near_hunk']}); per model {json.dumps({k: {f: v[f] for f in ('objections', 'anchored', 'in_hunk', 'near_hunk')} for k, v in L.items() if '-' in k})}.\n")
    md.append(f"\nCertificate size (median characters of quote + witness on mutants vs median mutant text length): witness {C['witness']['median_cert_chars']} vs {C['witness']['median_text_chars']} (n={C['witness']['n']}), "
              f"grader {C['grade']['median_cert_chars']} vs {C['grade']['median_text_chars']} (n={C['grade']['n']}).\n")
    md.append(f"\nReference checks: {results['refadj_objections']}. Usage: {json.dumps(results['usage'])}.\n")
    for key in ("grade:both", "closure:all", "witness:both", "refadj_all:RT", "refadj_all:AW"):
        t = G[key]
        md.append(f"\nBy problem, {key}: " + "; ".join(f"P{p}: FA {frac(v['false_accepts'])}, FR {frac(v['false_rejects'])}, H {frac(v['H_accepted'])}" for p, v in t["by_problem"].items())
                  + ". By base author: " + "; ".join(f"{a}: FA {frac(v['false_accepts'])}, FR {frac(v['false_rejects'])}, H {frac(v['H_accepted'])}" for a, v in t["by_author"].items()) + ".\n")
    md.append("\n## Per text\n")
    for r in rows:
        e = per[r["id"]]
        md.append(f"\n### {r['id']} (P{r['problem']}, type {r['type']} = {r['type_name']}, base {r['base_id']}, author {r['author']}); truth AW={r['truth']['AW']} RT={r['truth']['RT']}"
                  + (f"; planted on {r['obligation']} ({r['ledger_statement']})" if r.get("obligation") else "") + (f"; hunk spans {e['hunk_spans']}" if e["hunk_spans"] else "")
                  + ("" if r["exists"] else "; TEXT MISSING") + (f"; sha256 MISMATCH" if r["sha256_ok"] is False else "") + "\n")
        def verdict(dec, conv="RT"):
            truth = r["truth"][conv]
            if dec in ("pending", "na"): return dec
            return dec + (" (correct)" if dec == truth else (" (FALSE ACCEPT)" if dec == "accept" else " (FALSE REJECT)"))
        for m in GATE_MODELS["grade"]:
            g = e["gates"]["grade"][m]
            if g["decision"] == "pending" and "grade" not in g: md.append(f"- grade {m}: pending" + (" (delivery failure)" if g.get("delivery_failure") else "") + "\n"); continue
            md.append(f"- grade {m}: grade={g['grade']} complete={g['complete']} errors={g['n_errors']} -> {verdict(g['decision'])}" + (" [stale]" if g.get("stale") else "") + f"; main gap: {short(g['main_gap'], 200)}\n")
            for o in g["objections"]:
                lc = o["locus"]; md.append(f"  - {o['tag']}: quote {json.dumps(short(o['quote'], 300), ensure_ascii=False)} (anchored {lc.get('anchored')}, in hunk {lc.get('in_hunk')}, near {lc.get('near_hunk')}); objection: {short(o['objection'], 300)}\n")
        md.append(f"- grade both: {verdict(e['decisions']['grade:both'])}\n")
        for m in GATE_MODELS["closure"]:
            c = e["gates"]["closure"][m]
            if c["decision"] == "pending" and "S" not in c: md.append(f"- closure {m}: pending" + (" (delivery failure)" if c.get("delivery_failure") else "") + "\n"); continue
            md.append(f"- closure {m}: S={c['S']} fields={c['fields']} -> {verdict(c['decision'])}" + (" [stale]" if c.get("stale") else "") + f"; notes: {short(c['notes'], 200)}\n")
        md.append(f"- closure gpt+claude: {verdict(e['decisions']['closure:gc'])}; all raters: {verdict(e['decisions']['closure:all'])}\n")
        for m in GATE_MODELS["witness"]:
            w = e["gates"]["witness"][m]
            if w["decision"] == "pending" and "statuses" not in w: md.append(f"- witness {m}: pending" + (" (delivery failure)" if w.get("delivery_failure") else "") + "\n"); continue
            md.append(f"- witness {m}: statuses {w['statuses']} S_valid={w['S_valid']}" + (f" (reported {w['S_valid_reported']})" if w["S_valid_mismatch"] else "") + f" -> {verdict(w['decision'])}" + (" [stale]" if w.get("stale") else "") + "\n")
            for o in w["objections"]:
                lc = o["locus"]; md.append(f"  - {o['tag']} ({o['status']}): quote {json.dumps(short(o['quote'], 300), ensure_ascii=False)} (anchored {lc.get('anchored')}, in hunk {lc.get('in_hunk')}, near {lc.get('near_hunk')}); witness: {short(o['objection'], 300)}\n")
        md.append(f"- witness both: {verdict(e['decisions']['witness:both'])}\n")
        ra = e["gates"]["refadj"]; v = ra["variants"]
        md.append(f"- reference adjudication (ledger applicable: {ra['ledger_applicable']}; sources missing: {ra['missing_sources'] or 'none'}; objections {len(ra['objections'])}): "
                  f"all RT {verdict(v['all']['RT'], 'RT')}, AW {verdict(v['all']['AW'], 'AW')}; witness-only RT {verdict(v['witness']['RT'], 'RT')}, AW {verdict(v['witness']['AW'], 'AW')}; grader-only RT {verdict(v['grade']['RT'], 'RT')}\n")
        for o in ra["objections"]:
            md.append(f"  - {o['key']}: consensus **{o['consensus']}**" + (" [single checker]" if o["single_checker"] else "") + f", affected {o['affected']}, obligations {o['obligations_touched']}, scored {o['scored']}, in hunk {o['locus'].get('in_hunk')}\n")
            for chk, ck in o["checks"].items():
                md.append(f"    - {chk}: " + ("not returned" if not ck else f"{ck['status_as_written']} / {ck['affected_statement']} / correct={ck['objection_correct']} / elsewhere={ck['established_elsewhere']} / repair={ck['repair_distance']}: {short(ck['explanation'], 300)}") + "\n")
    (PD / "RESULTS.md").write_text("".join(md))
    # LaTeX table: gates x {false accepts F+G, false rejects O, H accepted, locus hits}
    nFG, nO, nH = G["grade:both"]["classes"]["FG"]["n"], G["grade:both"]["classes"]["O"]["n"], G["grade:both"]["classes"]["H"]["n"]
    T = [r"\begin{tabular}{@{}lcccc@{}}", r"\toprule", f"Gate & false accepts (F+G, $n{{=}}{nFG}$) & false rejects (O, $n{{=}}{nO}$) & H accepted ($n{{=}}{nH}$) & quotes in hunk \\\\", r"\midrule"]
    def loc_cell(key):
        gate, m = key.split(":")
        if gate not in ("grade", "witness"): return "--"
        l = L.get(f"{gate}-{m}") if m in GATE_MODELS[gate] else L.get(gate)
        return f"{l['in_hunk']}/{l['objections']}" if l and l["objections"] else "--"
    last = None
    for key, label in GATE_KEYS:
        if key.startswith("refadj_witness_"): continue
        fam = key.split(":")[0].split("_")[0]
        if last and fam != last: T.append(r"\addlinespace[2pt]")
        last = fam; t = G[key]
        T.append(f"{tex_escape(label)} & {tex_escape(frac(t['false_accepts']))} & {tex_escape(frac(t['false_rejects']))} & {tex_escape(frac(t['H_accepted']))} & {loc_cell(key)} \\\\")
    T += [r"\bottomrule", r"\end{tabular}"]
    (PD / "table_planted.tex").write_text("\n".join(T) + "\n")
    # macros (no digits in names)
    m = [r"% generated by scripts/planted_defects.py analyze; do not edit; loaded by main.tex via \InputIfFileExists{gen/planted_macros}",
         r"\newcommand{\PLANTN}{%d}" % results["n_mutants"], r"\newcommand{\PLANTBASE}{%d}" % results["n_base"], r"\newcommand{\PLANTTEXTS}{%d}" % results["n_texts"],
         r"\newcommand{\PLANTNFG}{%d}" % nFG, r"\newcommand{\PLANTNO}{%d}" % nO, r"\newcommand{\PLANTNH}{%d}" % nH]
    prim = {"GRADE": "grade:both", "CLOSURE": "closure:all", "WITNESS": "witness:both", "REFADJ": "refadj_all:RT"}
    for name, key in prim.items():
        m.append(r"\newcommand{\PLANTFA%s}{%s}" % (name, frac(G[key]["false_accepts"]))); m.append(r"\newcommand{\PLANTFR%s}{%s}" % (name, frac(G[key]["false_rejects"])))
        m.append(r"\newcommand{\PLANTH%s}{%s}" % (name, frac(G[key]["H_accepted"])))
    variants = {"GRADEC": "gradec:both", "GRADECGPT": "gradec:gpt", "GRADECCLAUDE": "gradec:claude", "GRADEGPT": "grade:gpt", "GRADECLAUDE": "grade:claude", "CLOSUREGPT": "closure:gpt", "CLOSURECLAUDE": "closure:claude", "CLOSUREGLM": "closure:glm", "CLOSUREGC": "closure:gc",
                "WITNESSGPT": "witness:gpt", "WITNESSCLAUDE": "witness:claude", "REFADJAW": "refadj_all:AW", "REFADJWIT": "refadj_witness:RT", "REFADJWITAW": "refadj_witness:AW",
                "REFADJGRD": "refadj_grade:RT", "REFADJGRDAW": "refadj_grade:AW", "REFADJWITGPT": "refadj_witness_gpt:RT", "REFADJWITCLAUDE": "refadj_witness_claude:RT"}
    for name, key in variants.items():
        m.append(r"\newcommand{\PLANTFA%s}{%s}" % (name, frac(G[key]["false_accepts"]))); m.append(r"\newcommand{\PLANTFR%s}{%s}" % (name, frac(G[key]["false_rejects"])))
        m.append(r"\newcommand{\PLANTH%s}{%s}" % (name, frac(G[key]["H_accepted"])))
    # per base author (GPT-5.6-Sol wrote six of the eight bases): OTHER = bases not written by GPT, GPTAUTH = GPT-written bases
    for name, key in {"GRADE": "grade:both", "WITNESS": "witness:both", "CLOSUREGC": "closure:gc", "REFADJWIT": "refadj_witness:RT", "REFADJWITAW": "refadj_witness:AW"}.items():
        for a, suffix in (("other", "OTHER"), ("gpt", "GPTAUTH")):
            ba = (G[key].get("by_author") or {}).get(a)
            m.append(r"\newcommand{\PLANTFA%s%s}{%s}" % (name, suffix, frac(ba["false_accepts"]) if ba else "--"))
            m.append(r"\newcommand{\PLANTFR%s%s}{%s}" % (name, suffix, frac(ba["false_rejects"]) if ba else "--"))
    # false accepts split by F and G for the primary gates
    for name, key in prim.items():
        c = G[key]["classes"]
        m.append(r"\newcommand{\PLANTFAF%s}{%s}" % (name, frac({"k": c["F"]["accepted"], **{k: c["F"][k] for k in ("n", "pending", "na", "decided")}})))
        m.append(r"\newcommand{\PLANTFAG%s}{%s}" % (name, frac({"k": c["G"]["accepted"], **{k: c["G"][k] for k in ("n", "pending", "na", "decided")}})))
    la = L["all"]; lw = L["witness"]; lg = L["grade"]
    m.append(r"\newcommand{\PLANTLOCUS}{%s}" % (f"{la['in_hunk']}/{la['objections']}" if la["objections"] else "pending"))
    m.append(r"\newcommand{\PLANTLOCUSNEAR}{%s}" % (f"{la['near_hunk']}/{la['objections']}" if la["objections"] else "pending"))
    m.append(r"\newcommand{\PLANTLOCUSWITNESS}{%s}" % (f"{lw['in_hunk']}/{lw['objections']}" if lw["objections"] else "pending"))
    m.append(r"\newcommand{\PLANTLOCUSGRADE}{%s}" % (f"{lg['in_hunk']}/{lg['objections']}" if lg["objections"] else "pending"))
    cw, cg = C["witness"], C["grade"]
    if cw["n"] or cg["n"]:
        parts = []
        if cw["n"]: parts.append(f"{cw['median_cert_chars']:,} characters for the witness gate")
        if cg["n"]: parts.append(f"{cg['median_cert_chars']:,} for the grader")
        tl = cw["median_text_chars"] if cw["n"] else cg["median_text_chars"]
        m.append(r"\newcommand{\PLANTCERT}{a median objection of %s against a median text of %s characters (medians over objections, so a text with several objections weighs more than once)}" % (" and ".join(parts), f"{tl:,}"))
    else: m.append(r"\newcommand{\PLANTCERT}{pending}")
    m.append(r"\newcommand{\PLANTTABLE}{\input{artifacts/planted_defects/table_planted.tex}}")
    # compact body table: one row per acceptance policy, every column an accepted-count so the ideal row is (0, 0, 8, 8 repair-tolerant)
    body_rows = [("grade:both", "score $\\ge 5$"), ("grade7:both", "score $=7$"), ("gradec:both", "\\textbf{completeness verdict, same call}"),
                 ("witness:both", "witness $S_{\\mathrm{valid}}{=}2$"), ("refadj_witness:RT", "witness + reference, repair-tolerant"),
                 ("refadj_witness:AW", "witness + reference, as written")]
    B = [r"\begin{tabular}{@{}lcccc@{}}", r"\toprule",
         r"Acceptance rule (both models) & fatal & gap & originals & harmless \\", r"\midrule"]
    for key, label in body_rows:
        t_ = G.get(key)
        if not t_: B.append(f"{label} & -- & -- & -- & -- \\\\"); continue
        c = t_["classes"]
        def cell(cls):
            x = c[cls]; return f"{x['accepted']}/{x['n']}" + (f" ({x['pending']} pending)" if x.get("pending") else "")
        B.append(f"{label} & {cell('F')} & {cell('G')} & {cell('O')} & {cell('H')} \\\\")
    B += [r"\bottomrule", r"\end{tabular}"]
    (PD / "table_planted_body.tex").write_text("\n".join(B) + "\n")
    m.append(r"\newcommand{\PLANTBODYTABLE}{\input{artifacts/planted_defects/table_planted_body.tex}}")
    Fa = {k: frac(G[v]["false_accepts"]) for k, v in prim.items()}; Fr = {k: frac(G[v]["false_rejects"]) for k, v in prim.items()}; Ha = {k: frac(G[v]["H_accepted"]) for k, v in prim.items()}
    m.append(r"\newcommand{\PLANTTXT}{On the %d mutants of %d base texts, the ordinary grade gate (both models) accepted %s of the fatal-or-gap texts, the closure gate (all raters) %s, the witness gate (both models) %s and the reference-adjudication gate %s, while rejecting %s, %s, %s and %s of the %d originals. The %d harmless-display texts were accepted by %s, %s, %s and %s of the gates respectively, and %s of the objections raised on mutants quoted the planted passage.}" % (
        results["n_mutants"], results["n_base"], Fa["GRADE"], Fa["CLOSURE"], Fa["WITNESS"], Fa["REFADJ"], Fr["GRADE"], Fr["CLOSURE"], Fr["WITNESS"], Fr["REFADJ"], nO, nH,
        Ha["GRADE"], Ha["CLOSURE"], Ha["WITNESS"], Ha["REFADJ"], (f"{la['in_hunk']} of {la['objections']}" if la["objections"] else "a pending number")))
    m.append(r"\newcommand{\PLANTPENDING}{%d}" % sum(results["pending_primary"].values()))
    # named-text detail, grade range on fatal texts, hunk-quoting graders, GLM coverage (all recomputed from per-text decisions)
    def ids(pred): return [e["id"] for e in per.values() if pred(e)]
    def dec(e, k): return e["decisions"].get(k)
    grade_rej_FG = ids(lambda e: e["type"] in ("F", "G") and dec(e, "grade:both") == "reject")
    gc_acc_FG = ids(lambda e: e["type"] in ("F", "G") and dec(e, "closure:gc") == "accept")
    rt_acc_FG = ids(lambda e: e["type"] in ("F", "G") and dec(e, "refadj_witness:RT") == "accept")
    wit_rej_H = [(e["id"], [md for md in ("gpt", "claude") if dec(e, f"witness:{md}") == "reject"]) for e in per.values() if e["type"] == "H" and dec(e, "witness:both") == "reject"]
    pooled_fr = ids(lambda e: e["type"] == "O" and dec(e, "refadj_all:AW") == "reject")
    glm_acc_FG = ids(lambda e: e["type"] in ("F", "G") and dec(e, "closure:glm") == "accept"); glm_pending = ids(lambda e: dec(e, "closure:glm") == "pending")
    def lst(xs): return ", ".join(xs) if xs else "none"
    detail = (f"The grade rejected {lst(grade_rej_FG)} (gap texts whose deleted proof left a visible hole); the GPT-and-Claude closure rating accepted {lst(gc_acc_FG)}; "
              f"the repair-tolerant reference gate re-admitted {lst(rt_acc_FG)}; the witness gate rejected the harmless displays "
              + (", ".join(f"{i} ({' and '.join(ms)})" for i, ms in wit_rej_H) if wit_rej_H else "none")
              + f"; the pooled as-written reference variant rejected the original {lst(pooled_fr)} on a grader's remark about a closing formula, judged a false display by both checkers"
              + f"; GLM-5.3's closure rating alone accepted {lst(glm_acc_FG)}" + (f" (pending: {lst(glm_pending)})" if glm_pending else "") + ".")
    m.append(r"\newcommand{\PLANTDETAIL}{%s}" % detail.replace("_", r"\_"))
    fg = [e["gates"]["grade"][md].get("grade") for e in per.values() if e["type"] == "F" for md in ("gpt", "claude") if isinstance(e["gates"]["grade"][md].get("grade"), int)]
    m.append(r"\newcommand{\PLANTFGRADERANGE}{%s}" % (f"{min(fg)} to {max(fg)}" if fg else "pending"))
    acc_FG = [e for e in per.values() if e["type"] in ("F", "G") and dec(e, "grade:both") == "accept"]
    named = sum(1 for e in acc_FG if any((o.get("locus") or {}).get("in_hunk") for md in ("gpt", "claude") for o in e["gates"]["grade"][md].get("objections", [])))
    m.append(r"\newcommand{\PLANTNAMEDGRADE}{%d/%d}" % (named, len(acc_FG)))
    for md in GATE_MODELS["grade"]:
        n_ = sum(1 for e in acc_FG if any((o.get("locus") or {}).get("in_hunk") for o in e["gates"]["grade"][md].get("objections", [])))
        m.append(r"\newcommand{\PLANTNAMED%s}{%d/%d}" % (md.upper(), n_, len(acc_FG)))
    # disputed labels (post-hoc, after the reviewer audit; the pre-registered counts above are unchanged)
    DISPUTED_G = "p1-gpt56-5aca5e52-v1-G"   # deletes the derivation of a standard gcd identity the published reference also invokes without deriving
    DISPUTED_G2 = "p1-deedy-kimi-k3-final-G"   # second P1 gcd omission, raised in the v12 fresh review
    DISPUTED_F = ["p1-deedy-kimi-k3-final-F", "p5-gpt56-7324ef70-v1-F"]   # false as written; a one-line repair restores the argument, so "unrepairable" is not defensible
    def acc_excl(key, cls, excl):
        sub = [e for e in per.values() if e["type"] in cls and e["id"] not in excl]
        return sum(1 for e in sub if dec(e, key) == "accept"), len(sub)
    EXCL = {DISPUTED_G, *DISPUTED_F}   # all three disputed labels, matching the sentence in the body
    ge = acc_excl("grade:both", ("F", "G"), EXCL); ce = acc_excl("gradec:both", ("F", "G"), EXCL); we = acc_excl("witness:both", ("F", "G"), EXCL)
    m.append(r"\newcommand{\PLANTEXCLG}{%d/%d}" % ge); m.append(r"\newcommand{\PLANTEXCLGC}{%d/%d}" % ce); m.append(r"\newcommand{\PLANTEXCLW}{%d/%d}" % we)
    m.append(r"\newcommand{\PLANTDISPUTEDG}{%s}" % DISPUTED_G.replace("_", r"\_"))
    m.append(r"\newcommand{\PLANTDISPUTEDGTWO}{%s}" % DISPUTED_G2.replace("_", r"\_"))
    m.append(r"\newcommand{\PLANTDISPUTEDF}{%s}" % ", ".join(x.replace("_", r"\_") for x in DISPUTED_F))
    # rule-disagreement (label-free), per-grader disagreement, refusal counts, lab dependence, and the out-of-sample alarm
    P = list(per.values())
    ndiff = sum(1 for e in P if dec(e, "grade:both") != dec(e, "gradec:both"))
    ndiff_fg = sum(1 for e in P if e["type"] in ("F", "G") and dec(e, "grade:both") != dec(e, "gradec:both"))
    m.append(r"\newcommand{\PLANTDIFF}{%d of %d}" % (ndiff, len(P)))
    m.append(r"\newcommand{\PLANTDIFFFG}{%d of %d}" % (ndiff_fg, sum(1 for e in P if e["type"] in ("F", "G"))))
    pg = [sum(1 for e in P if e["type"] in ("F", "G") and dec(e, f"grade:{md}") != dec(e, f"gradec:{md}")) for md in ("gpt", "claude")]
    m.append(r"\newcommand{\PLANTDIFFPERGRADER}{%s of %d}" % ("/".join(str(x) for x in pg) if len(set(pg)) > 1 else str(pg[0]), sum(1 for e in P if e["type"] in ("F", "G"))))
    labc = sum(1 for e in P if dec(e, "gradec:gpt") != dec(e, "gradec:claude")); labs = sum(1 for e in P if dec(e, "grade:gpt") != dec(e, "grade:claude"))
    m.append(r"\newcommand{\PLANTLABCOMPLETE}{%d of %d}" % (labc, len(P))); m.append(r"\newcommand{\PLANTLABSCORE}{%d of %d}" % (labs, len(P)))
    for name, key in (("GRADEC", "gradec:both"), ("WITNESS", "witness:both"), ("GRADE", "grade:both"), ("GRADESEVEN", "grade7:both")):
        h = G[key]["classes"]["H"]; m.append(r"\newcommand{\PLANTHREFUSE%s}{%d/%d}" % (name, h["n"] - h["accepted"], h["n"]))
    for name, key in (("GRADESEVEN", "grade7:both"),):
        m.append(r"\newcommand{\PLANTFA%s}{%s}" % (name, frac(G[key]["false_accepts"]))); m.append(r"\newcommand{\PLANTFR%s}{%s}" % (name, frac(G[key]["false_rejects"])))
        m.append(r"\newcommand{\PLANTH%s}{%s}" % (name, frac(G[key]["H_accepted"])))
    def alarm(e):   # the S-disagreement alarm of the closure section, applied to these texts; the rule predates them
        vals = [(e["gates"]["closure"].get(x) or {}).get("S") for x in ("gpt", "claude", "glm")]
        vals = [v for v in vals if v is not None]
        return len(vals) >= 2 and len(set(vals)) > 1
    for cls, name in ((("F",), "F"), (("G",), "G"), (("H",), "H"), (("O",), "O"), (("F", "G"), "FG")):
        sub = [e for e in P if e["type"] in cls]
        m.append(r"\newcommand{\PLANTALARM%s}{%d/%d}" % (name, sum(1 for e in sub if alarm(e)), len(sub)))
    rem = [e for e in P if e["type"] in ("F", "G") and e["id"] not in {DISPUTED_G, *DISPUTED_F}]   # exclusion sensitivity for the disputed labels
    ge4 = acc_excl("grade:both", ("F", "G"), EXCL | {DISPUTED_G2}); ce4 = acc_excl("gradec:both", ("F", "G"), EXCL | {DISPUTED_G2})
    m.append(r"\newcommand{\PLANTEXCLFOURG}{%d/%d}" % ge4); m.append(r"\newcommand{\PLANTEXCLFOURGC}{%d/%d}" % ce4)
    DISPUTED_F2 = "p1-gpt56-5aca5e52-v1-F"   # fifth case, raised in the v15 fresh review: same one-line repair as the Kimi P1 fatal edit
    EXCL5 = EXCL | {DISPUTED_G2, DISPUTED_F2}
    ge5 = acc_excl("grade:both", ("F", "G"), EXCL5); ce5 = acc_excl("gradec:both", ("F", "G"), EXCL5); we5 = acc_excl("witness:both", ("F", "G"), EXCL5)
    m.append(r"\newcommand{\PLANTEXCLFIVEG}{%d/%d}" % ge5); m.append(r"\newcommand{\PLANTEXCLFIVEGC}{%d/%d}" % ce5); m.append(r"\newcommand{\PLANTEXCLFIVEW}{%d/%d}" % we5)
    m.append(r"\newcommand{\PLANTEXCLRT}{%d/%d}" % (sum(1 for e in rem if dec(e, "refadj_witness:RT") == "accept"), len(rem)))
    m.append(r"\newcommand{\PLANTEXCLRTH}{%s}" % frac(G["refadj_witness:RT"]["H_accepted"]))
    repeat_flips = {}   # per-threshold replicate decision flips; filled by the repeat block below, read by the policy object
    # --- repeat-query stability of the two fields (runs/grade_rep2, one extra call per text and model; absent -> macros omitted)
    rep = runs_dir() / "grade_rep2"
    if rep.is_dir():
        pairs = []
        for e in P:
            for md in GATE_MODELS["grade"]:
                b = lj(rep / md / e["id"] / "parsed.json")
                if not b: continue
                bp = b.get("parsed") or {}
                try: g2 = int(bp.get("grade"))
                except (TypeError, ValueError): g2 = None
                a = e["gates"]["grade"][md]
                if a.get("grade") is None or g2 is None: continue
                pairs.append({"id": e["id"], "m": md, "g1": a["grade"], "g2": g2, "c1": a.get("complete"), "c2": bp.get("complete")})
        if pairs:
            n = len(pairs)
            m.append(r"\newcommand{\PLANTREPN}{%d}" % n)
            m.append(r"\newcommand{\PLANTREPSAME}{%d/%d}" % (sum(1 for p in pairs if p["g1"] == p["g2"]), n))
            m.append(r"\newcommand{\PLANTREPFLIPPASS}{%d/%d}" % (sum(1 for p in pairs if (p["g1"] >= GRADE_MIN) != (p["g2"] >= GRADE_MIN)), n))
            m.append(r"\newcommand{\PLANTREPFLIPC}{%d/%d}" % (sum(1 for p in pairs if bool(p["c1"]) != bool(p["c2"])), n))
            by = {}
            for p in pairs: by.setdefault(p["id"], []).append(p)
            full = {i: v for i, v in by.items() if len(v) == len(GATE_MODELS["grade"])}
            def joint(v, a, b): return (all(x[a] >= GRADE_MIN for x in v), all(bool(x[b]) for x in v))
            d2 = sum(1 for v in full.values() if joint(v, "g1", "c1") != (None,) and joint(v, "g2", "c2")[0] != joint(v, "g2", "c2")[1])
            m.append(r"\newcommand{\PLANTREPDIFF}{%d of %d}" % (d2, len(full)))
            m.append(r"\newcommand{\PLANTREPJOINT}{%d/%d}" % (sum(1 for v in full.values() if joint(v, "g1", "c1") == joint(v, "g2", "c2")), len(full)))
            def rep_pair(kind):
                bad_, good_ = ("F", "G"), ("O", "H")
                by_id = {}
                for x in pairs: by_id.setdefault(x["id"], []).append(x)
                wa = wr = 0
                for e in P:
                    vs = by_id.get(e["id"], [])
                    if len(vs) < len(GATE_MODELS["grade"]): continue
                    ok = all(x["g2"] >= 7 for x in vs) if kind == "seven" else all(bool(x["c2"]) for x in vs)
                    if ok and e["type"] in bad_: wa += 1
                    if (not ok) and e["type"] in good_: wr += 1
                return wa, wr

            byk = {}
            for k in range(0, 8):
                fl = 0
                for p in pairs:
                    fl += ((p["g1"] >= k) != (p["g2"] >= k))
                byk[k] = fl
            repeat_flips.update(byk)
            m.append(r"\newcommand{\REPFLIPZERO}{%s}" % ", ".join(str(k) for k, v in byk.items() if v == 0))
            for kind, nm in (("seven", "SEVEN"), ("complete", "COMPLETE")):
                wa, wr = rep_pair(kind)
                m.append(r"\newcommand{\REPPAIR%s}{(%d,\,%d)}" % (nm, wa, wr))
    # ---- decision-rule analysis added after the v12 reviews: all offline, from the same stored responses ----
    BAD, GOOD = ("F", "G"), ("O", "H")   # repair-tolerant truth: a false line the next step corrects is acceptable
    def wrong(fn):
        return (sum(1 for e in P if e["type"] in BAD and fn(e) == "accept"),
                sum(1 for e in P if e["type"] in GOOD and fn(e) == "reject"))
    def at_threshold(e, k):
        gs = [e["gates"]["grade"][md].get("grade") for md in GATE_MODELS["grade"]]
        return "accept" if all(g is not None and g >= k for g in gs) else "reject"
    sweep = [(k, *wrong(lambda e, k=k: at_threshold(e, k))) for k in range(1, 8)]
    m.append(r"\newcommand{\SWEEPFIVE}{%d}" % sweep[4][1]); m.append(r"\newcommand{\SWEEPSIX}{%d}" % sweep[5][1])
    m.append(r"\newcommand{\SWEEPSEVEN}{%d}" % sweep[6][1]); m.append(r"\newcommand{\SWEEPSEVENFR}{%d}" % sweep[6][2])
    cw = wrong(lambda e: dec(e, "gradec:both"))
    m.append(r"\newcommand{\SWEEPCOMPLETE}{%d}" % cw[0]); m.append(r"\newcommand{\SWEEPCOMPLETEFR}{%d}" % cw[1])
    m.append(r"\newcommand{\SWEEPN}{%d}" % sum(1 for e in P if e["type"] in BAD))
    m.append(r"\newcommand{\SWEEPNGOOD}{%d}" % sum(1 for e in P if e["type"] in GOOD))
    # escalation: two graders, agree decides, disagree goes to a person
    def escalate(prefix, texts=None):
        texts = P if texts is None else texts
        n = w = s = 0
        for e in texts:
            a, b = dec(e, f"{prefix}:gpt"), dec(e, f"{prefix}:claude")
            if a != b: n += 1
            elif a == "accept" and e["type"] in BAD: w += 1
            elif a == "reject" and e["type"] in GOOD: s += 1
        return n, w, s
    ESC = {"GRADE": "grade", "GRADESEVEN": "grade7", "COMPLETE": "gradec", "CLOSURE": "closure", "WITNESS": "witness"}
    esc = {k: escalate(v) for k, v in ESC.items()}
    nbad = sum(1 for e in P if e["type"] in BAD); ngood = sum(1 for e in P if e["type"] in GOOD)
    for k, (n_, w_, s_) in esc.items():
        m.append(r"\newcommand{\ESC%s}{%d/%d}" % (k, n_, len(P)))
        m.append(r"\newcommand{\ESCBAD%s}{%d/%d}" % (k, w_, nbad))
        m.append(r"\newcommand{\ESCSOUND%s}{%d/%d}" % (k, s_, ngood))
    # the same routing with the four disputed labels set aside
    kept = [e for e in P if e["id"] not in (EXCL | {DISPUTED_G2})]
    nbad4 = sum(1 for e in kept if e["type"] in BAD)
    for k, v in (("COMPLETE", "gradec"), ("WITNESS", "witness")):
        n_, w_, s_ = escalate(v, kept)
        m.append(r"\newcommand{\ESCFOUR%s}{%d/%d}" % (k, n_, len(kept)))
        m.append(r"\newcommand{\ESCFOURBAD%s}{%d/%d}" % (k, w_, nbad4))
    # the completeness flag is largely a recode of the top score: report it ourselves
    rec = tot = 0
    for e in P:
        for md in GATE_MODELS["grade"]:
            g = e["gates"]["grade"][md]
            if g.get("grade") is None or g.get("complete") is None: continue
            tot += 1; rec += (bool(g["complete"]) == (g["grade"] == 7))
    m.append(r"\newcommand{\PLANTRECODE}{%d/%d}" % (rec, tot))
    # does a lab's score separate a fatal edit from a cosmetic one?
    for md in GATE_MODELS["grade"]:
        Fg = [e["gates"]["grade"][md].get("grade") for e in P if e["type"] == "F"]
        Hg = [e["gates"]["grade"][md].get("grade") for e in P if e["type"] == "H"]
        Fg = [x for x in Fg if x is not None]; Hg = [x for x in Hg if x is not None]
        auc = sum((1 if h > f_ else 0.5 if h == f_ else 0) for f_ in Fg for h in Hg) / (len(Fg) * len(Hg)) if Fg and Hg else None
        nm = md.upper()
        m.append(r"\newcommand{\AUC%s}{%s}" % (nm, ("%.2f" % auc) if auc is not None else "--"))
        flat = len(set(Fg + Hg)) == 1
        m.append(r"\newcommand{\SPREAD%s}{%s}" % (nm, ("the same score, %d" % Fg[0]) if flat else ("scores of %d--%d" % (min(Fg + Hg), max(Fg + Hg)))))
    # which lab looks better depends on the convention
    def lab_errors(gate, md, conv):
        return sum(1 for e in P if (e["gates"].get(gate, {}).get(md) or {}).get("decision") in ("accept", "reject")
                   and e["gates"][gate][md]["decision"] != e["truth"][conv])
    flip = []
    for gate, label in (("grade7", "score $=7$"), ("gradec", "completeness"), ("witness", "witness")):
        row = [lab_errors(gate, md, cv) for cv in ("RT", "AW") for md in GATE_MODELS["grade"]]
        flip.append((label, row))
    import itertools as _it
    agr = [sum(1 for e in P if dec(e, a) == dec(e, b)) for a, b in _it.combinations(("grade7:both", "gradec:both", "witness:both"), 2)]
    m.append(r"\newcommand{\FLIPAGREE}{%d--%d}" % (min(agr), max(agr)))
    m.append(r"\newcommand{\FLIPRULES}{%d}" % sum(1 for _, r_ in flip if (r_[1] < r_[0]) != (r_[3] < r_[2])))
    m.append(r"\newcommand{\FLIPTOTAL}{%d}" % len(flip))
    # cross-lab disagreement by planted type, for the two alarm candidates
    for gate, nm in (("closure", "CLOSURE"), ("grade", "GRADE")):
        for ty in ("F", "H", "O"):
            sub = [e for e in P if e["type"] == ty]
            n_ = sum(1 for e in sub if (e["gates"][gate].get("gpt") or {}).get("decision") != (e["gates"][gate].get("claude") or {}).get("decision"))
            m.append(r"\newcommand{\ALARM%s%s}{%d/%d}" % (nm, ty, n_, len(sub)))
    # how often a grader calls the planted defect minor or repairable
    import re as _re
    pat = _re.compile(r"repairab|readily repaired|easily (?:fixed|repaired)|does not affect|\bminor\b|cosmetic", _re.I)
    hits = tot2 = 0; tx = set()
    for e in P:
        if e["type"] not in BAD: continue
        for md in GATE_MODELS["grade"]:
            g = e["gates"]["grade"][md]; tot2 += 1
            blob = " ".join([str(g.get("main_gap") or "")] + [str(o.get("objection") or "") for o in g.get("objections", [])])
            if pat.search(blob): hits += 1; tx.add(e["id"])
    m.append(r"\newcommand{\PLANTREPAIRCLAIM}{%d/%d}" % (hits, tot2)); m.append(r"\newcommand{\PLANTREPAIRTEXTS}{%d/%d}" % (len(tx), sum(1 for e in P if e["type"] in BAD)))
    on = offt = unanch = 0
    for e in P:
        if e["type"] not in BAD: continue
        for md in GATE_MODELS["grade"]:
            g = e["gates"]["grade"][md]
            objs = [o for o in g.get("objections", []) if pat.search(str(o.get("objection") or ""))]
            if objs:
                if any((o.get("locus") or {}).get("in_hunk") for o in objs): on += 1
                else: offt += 1
            elif pat.search(str(g.get("main_gap") or "")): unanch += 1
    m.append(r"\newcommand{\PLANTREPAIRON}{%d}" % on); m.append(r"\newcommand{\PLANTREPAIROFF}{%d}" % offt)
    m.append(r"\newcommand{\PLANTREPAIRUNANCH}{%d}" % unanch)
    # body table: accuracy and escalation cost side by side
    B2 = [r"\begin{tabular}{@{}lcccccc@{}}", r"\toprule",
          r" & \multicolumn{2}{c}{as a binary gate} & \multicolumn{3}{c}{as accept/reject/refer} \\",
          r"\cmidrule(lr){2-3}\cmidrule(lr){4-6}",
          r"Rule & broken accepted & sound rejected & referred & broken accepted & sound rejected \\", r"\midrule"]
    ROWS = [("score $\\ge 5$", lambda e: at_threshold(e, 5), "GRADE"),
            ("score $=7$", lambda e: at_threshold(e, 7), "GRADESEVEN"), ("completeness verdict", lambda e: dec(e, "gradec:both"), "COMPLETE"),
            ("closure rating $S{=}2$", lambda e: dec(e, "closure:gc"), "CLOSURE"), ("witness $S_{\\mathrm{valid}}{=}2$", lambda e: dec(e, "witness:both"), "WITNESS")]
    for label, fn, ek in ROWS:
        wa, wr = wrong(fn)
        if ek:
            n_, w_, s_ = esc[ek]
            B2.append(f"{label} & {wa}/{nbad} & {wr}/{ngood} & {n_}/{len(P)} & {w_}/{nbad} & {s_}/{ngood} \\\\")
        else:
            B2.append(f"{label} & {wa}/{nbad} & {wr}/{ngood} & -- & -- & -- \\\\")
    B2 += [r"\bottomrule", r"\end{tabular}"]
    (PD / "table_rules.tex").write_text("\n".join(B2) + "\n")
    results["policy"] = {
        "convention": "repair-tolerant: originals and harmless displays are acceptable",
        "threshold_sweep": [{"pass_mark": k, "bad_accepted": a, "sound_rejected": b} for k, a, b in sweep],
        "completeness": {"bad_accepted": cw[0], "sound_rejected": cw[1]},
        "routing": {k: {"escalated": v[0], "bad_auto_accepted": v[1], "sound_auto_rejected": v[2], "of_texts": len(P)} for k, v in esc.items()},
        "routing_excluding_four_disputed": {k: dict(zip(("escalated", "bad_auto_accepted", "sound_auto_rejected"), escalate(v, kept))) for k, v in (("COMPLETE", "gradec"), ("WITNESS", "witness"))},
        "discrimination_fatal_vs_harmless": {md: {"scores_fatal": sorted({e["gates"]["grade"][md].get("grade") for e in P if e["type"] == "F"}),
                                                 "scores_harmless": sorted({e["gates"]["grade"][md].get("grade") for e in P if e["type"] == "H"})} for md in GATE_MODELS["grade"]},
        "strict_rule_agreement_pairs": agr,
        "strict_rules": ["grade7:both", "gradec:both", "witness:both"],
        "strict_rule_agreement_note": "pairwise agreement between combined two-model gates over the 32 texts",
        "discrimination_auc_fatal_vs_harmless": {md: (None if not (Fs := [e["gates"]["grade"][md].get("grade") for e in P if e["type"] == "F"]) or not (Hs := [e["gates"]["grade"][md].get("grade") for e in P if e["type"] == "H"]) else round(sum((1 if h > f_ else 0.5 if h == f_ else 0) for f_ in Fs for h in Hs) / (len(Fs) * len(Hs)), 4)) for md in GATE_MODELS["grade"]},
        "convention_errors_by_lab": {gate: {conv: {md: lab_errors(gate, md, conv) for md in GATE_MODELS["grade"]} for conv in ("RT", "AW")} for gate in ("grade", "grade7", "gradec", "witness", "closure")},
        "routing_excluding_five_disputed": {k: dict(zip(("escalated", "bad_auto_accepted", "sound_auto_rejected"), escalate(v, [e for e in P if e["id"] not in EXCL5]))) for k, v in (("GRADE", "grade"), ("COMPLETE", "gradec"), ("WITNESS", "witness"))},
        "repeat_decision_flips_by_threshold": dict(repeat_flips),
        "repair_language": {"responses_matching": hits, "of": tot2, "quote_in_hunk": on, "quote_elsewhere": offt, "unanchored_main_gap": unanch,
                            "note": "keyword match anywhere in the response; the split is by whether the matching objection's quote lies in the planted hunk"},
        "completeness_is_top_score": rec,
    }
    m.append(r"\newcommand{\RULESTABLE}{\input{artifacts/planted_defects/table_rules.tex}}")
    m.append(r"\newcommand{\RULESROWS}{%s}" % {1:"One",2:"Two",3:"Three",4:"Four",5:"Five",6:"Six",7:"Seven"}.get(len(ROWS), str(len(ROWS))))
    glm_n = sum(1 for e in per.values() if dec(e, "closure:glm") in ("accept", "reject")); m.append(r"\newcommand{\PLANTGLMCOV}{%d/%d}" % (glm_n, len(per)))
    (PD / "results.json").write_text(json.dumps(results, indent=1))   # rewritten so the policy block above is persisted alongside the gates
    if results.get("frozen"): m = [x.replace(" pending)", " not returned)").replace("(pending: ", "(not returned: ") for x in m]   # frozen analysis: missing ratings are reported as not returned, per the protocol
    if GEN.is_dir(): (GEN / "planted_macros.tex").write_text("\n".join(m) + "\n")
    else: (PD / "planted_macros.tex").write_text("\n".join(m) + "\n"); print(f"note: {GEN} does not exist; macros written to {PD / 'planted_macros.tex'}")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sub = ap.add_subparsers(dest="cmd", required=True)
    mf = sub.add_parser("manifest", help="write artifacts/planted_defects/manifest.json (originals + mutants, sha256 verified)"); mf.add_argument("--root", default=None)
    r = sub.add_parser("run", help="run one gate with one model on every text (cached results skipped)")
    r.add_argument("--gate", choices=list(GATES), required=True); r.add_argument("--model", choices=list(MODELS), required=True)
    r.add_argument("--workers", type=int, default=5); r.add_argument("--timeout", type=int, default=2400); r.add_argument("--only", default=None, help="comma-separated text or base ids")
    r.add_argument("--types", default=None, help="comma-separated subset of O,F,H,G"); r.add_argument("--redo", action="store_true")
    r.add_argument("--tag", default="", help="suffix appended to the gate's run directory, e.g. --tag _rep2 writes runs/grade_rep2/ and leaves the frozen runs untouched")
    r.add_argument("--key-file", default="~/.config/vexorium/glm_api_key", help="GLM-5.3 key file (model glm only)"); r.add_argument("--root", default=None)
    an = sub.add_parser("analyze", help="results.json, RESULTS.md, table_planted.tex, gen/planted_macros.tex (offline)")
    an.add_argument("--freeze", action="store_true", help="decide combined gates and consensus from the models/checkers that returned")
    an.add_argument("--root", default=None, help="repository root (with artifacts/planted_defects/) or a flat supplement (with planted_defects/ at the top level)")
    args = ap.parse_args()
    if getattr(args, "root", None): set_root(args.root)
    return {"manifest": cmd_manifest, "run": cmd_run, "analyze": cmd_analyze}[args.cmd](args)

if __name__ == "__main__": sys.exit(main())
