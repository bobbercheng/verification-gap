#!/usr/bin/env python3
"""Reference-anchored adjudication of the v6 witness objections (protocol: artifacts/reference_adjudication/PROTOCOL.md).

Subcommands
  jobs                          list the 96 objections (sanity)
  check --checker gpt|claude    stage 1: ledger-guided adjudication of every objection
  rate  --rater gpt|claude|glm  stage 2: ledger-guided closure rating of the 20 case texts
  analyze [--root DIR] [--freeze]   analysis and reports only (no calls): results.json, RESULTS.md, table_refadj.tex,
                                  table_refadj_disputes.tex, gen/refadj_macros.tex (or <root>/reference_adjudication/refadj_macros.tex in a flat layout)
Transports reuse scripts/witness_discovery.py (which reuses cli_transport.py and closure_annotate.call).
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, hashlib, json, pathlib, re, sys, time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import witness_discovery as W  # noqa: E402

ROOT = HERE.parent
ART = ROOT / "artifacts"
RA = ART / "reference_adjudication"
WD = ART / "witness_discovery"

MODELS = {"gpt": ("codex-cli", "gpt-5.6-sol"), "claude": ("claude-cli", "claude-opus-5"), "glm": ("anthropic", "glm-5.3")}

# Ledger statements (author-written from Chen's notes; see LEDGER.md for citations and the cross-check status)
LEDGER = {
    "5": [("L5.1", "Sufficiency: for every c >= 0 and all x, y > 0 the chain sqrt((x^2+(y+c)^2)/2) >= (x+y+c)/2 >= sqrt(x(y+c)) holds (QM-AM-GM on x and y+c); the middle term is (f(x)+y)/2 = (x+c+y)/2."),
          ("L5.2", "Structural identity: f(f(t)) = 2 f(t) - t for every t > 0 (from the two inequalities at (x,y) = (f(t),t)); hence t, f(t), f(f(t)), ... is an arithmetic progression."),
          ("L5.3", "Nonnegative difference: the common difference f(t) - t is nonnegative for every t > 0, because all terms of the progression are positive."),
          ("L5.4", "Equal positive differences: if the differences of the progressions from x and from y are both positive, they are equal (iterate comparison using the right-hand inequality)."),
          ("L5.5", "Fixed points: if f is not the identity, there is D > 0 with f(x) in {x, x+D} for all x, and f(x) = x+D together with f(y) = y forces |x-y| > D, hence f(t) = t + D everywhere. (A calculus route needs f(y) = f(x) + (y-x) + O(|y-x|^2) for every x, hence f' = 1.)")],
    "3": [("L3.1", "Reduction: under optimal play Liu's score is the sum of the odd-ranked piece lengths; the gap G = x1 - x2 + x3 - ... + x_{2n+1}."),
          ("L3.2", "Upper bound, universal over Liu's division: for any two disjoint subsets S, T of Liu's n+1 segments Xiang can guarantee G <= |Sigma(S) - Sigma(T)| (mirrored cuts pairing S against T, bisect the rest); pigeonhole on the 2^{n+1} subset sums gives S != T with 0 <= Sigma(S) - Sigma(T) <= 1/(2^{n+1}-1)."),
          ("L3.3", "Lower bound, universal over Xiang's replies: for any division G >= Delta = min over nonzero sign vectors of |sum eps_i a_i| (tree component of the multigraph on segments; a bipartition S, T gives |Sigma(S) - Sigma(T)| as a signed sum of the d_i, at most G); for the division 1:2:...:2^n, Delta = 1/(2^{n+1}-1). Alternative for that division: induction on k with x2 + x4 + ... + x_{2k} <= 2^{n-1} + ... + 2^{n-k}.")],
    "6": [("L6.1", "Characterization: x appears in the sequence iff gcd(x, a_i) > 1 for every i (equivalently for every earlier term, or every minimal term under a_m < a_n with rad a_m | rad a_n)."),
          ("L6.2", "Large-prime erasure, for all terms: if a_n is divisible by a prime larger than a_1^2 then a_n is not minimal (some q^k c with q | gcd(a_1, a_n) lies in [a_1, a_n) and is a term); hence membership depends only on the small primes (at most a_1^2). Pairwise intersection of the prime supports alone does not imply this: the family F_k = {x_1..x_k, y_k} is pairwise intersecting and has infinitely many minimal finite transversals."),
          ("L6.3", "Periodicity from n = 1: the sequence is exactly the integers a >= a_1 whose small-prime support lies in the set of supports that occur; membership depends only on a mod L with L the product of the small primes; T is the number of residues that appear; a_{n+T} = a_n + L for every n >= 1.")],
    "1": [("L1.1", "Termination and exactly one survivor, for every sequence of moves: a move with gcd = 1 permanently increases the number of 1s and a move with gcd > 1 decreases the product, so moves end; at the end at most one integer exceeds 1 (two would allow a move) and at least one does (a move never outputs two 1s)."),
          ("L1.2", "Invariance, for every move and every prime p: gcd of the p-adic valuations over the board is unchanged, since (x, y) -> (min(x,y), |x-y|) and gcd(x, y-x) = gcd(x, y); hence v_p(M) = gcd_i v_p(a_i) and M is determined by the initial board (note gcd(1, 0) = 1: a positive valuation somewhere gives a positive gcd).")],
    "4": [("L4.x", "P4 is not in the disputed set; no ledger statements were written (the P4 control text is rated under its closure rubric only).")],
}

def ledger_text(problem: str) -> str:
    return "\n".join(f"- {k}: {v}" for k, v in LEDGER[problem])

CHECK_INSTRUCTIONS = """
TASK: reference-anchored adjudication of one objection. Below is a reference ledger: statements that every complete proof of this problem establishes (from the published solutions; a text may follow a different route, but each ledger statement, or an equivalent covering the same cases, must be established somewhere in it). An objection has been raised against a step of the write-up (a quote and an objection text). The objection's own opinion of severity, if it states one, is not evidence: decide from the write-up and the ledger only.

Return ONLY a JSON object with these fields:
- "affected_statement": the ledger id the objection bears on (e.g. "L5.3"), or "none" if the objection does not concern any required statement.
- "objection_correct": "yes" | "no" | "unclear": is the objection's local claim correct (the counterexample valid, the inference invalid as written, or the statement indeed missing at the quoted place)?
- "established_elsewhere": "yes" | "no": does the write-up establish the affected statement, for all cases and as written (no repair by you), somewhere other than the quoted place? If "yes", give "elsewhere_quote": a verbatim excerpt (40-400 characters) of that passage; else null.
- "status_as_written": "established" (the affected statement is established as written, the objection notwithstanding) | "not_established" (the write-up does not establish it as written) | "false_display" (a false line or misprint stands beside an argument in the text that does establish the statement; the argument is present, the line is wrong) | "not_applicable" (affected_statement is "none").
- "repair_distance": "symbol" | "sentence" | "lemma" | "none": the smallest edit that would make the write-up establish the statement ("none" if no local edit does, or not applicable).
- "explanation": at most 120 words with the decisive check.
"""

RATE_INSTRUCTIONS = """
TASK: ledger-guided rating. For each ledger statement below decide whether the write-up establishes it as written for all cases (an equivalent statement on a different route counts if it covers the same cases). Return ONLY a JSON object:
{"statements": {"<ledger id>": {"established": "yes"|"no"|"partial", "quote": "<verbatim excerpt of 40-400 characters where it is established, or null>", "note": "<=30 words"}, ...},
 "S_ref": <number of the two obligations lower_bound and upper_bound (see the field mapping) all of whose ledger statements are established>,
 "notes": "<=60 words"}
Map ledger statements to obligations as follows: the statement(s) that the field mapping assigns to "lower_bound" and to "upper_bound"; statements about the reduction/answer do not count toward S_ref. Judge only what is written; do not repair the argument for the author.
"""

OBLIGATION_MAP = {  # ledger ids per S obligation, per problem (lower_bound, upper_bound as in the closure rubric field mapping)
    "5": {"lower_bound": ["L5.1"], "upper_bound": ["L5.2", "L5.3", "L5.4", "L5.5"]},
    "3": {"lower_bound": ["L3.3"], "upper_bound": ["L3.2"]},
    "6": {"lower_bound": ["L6.2"], "upper_bound": ["L6.3"]},
    "1": {"lower_bound": ["L1.1"], "upper_bound": ["L1.2"]},
    "4": {"lower_bound": [], "upper_bound": []},
}

def sha256(b): return hashlib.sha256(b).hexdigest()
def lj(p): return json.load(open(p))
def dj(p, o): pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True); pathlib.Path(p).write_text(json.dumps(o, indent=1, ensure_ascii=False))

def system_for(problem: str, stage: str) -> str:
    core = W.rubric_core(problem)
    return core + "\n\nREFERENCE LEDGER (published-solution statements; see LEDGER.md):\n" + ledger_text(problem) + "\n" + (CHECK_INSTRUCTIONS if stage == "check" else RATE_INSTRUCTIONS)

def objections():
    """The 96 v6 objections: one per (procedure, source, case, tag), taken from the stored checker requests (any checker's copy)."""
    cases = {c["id"]: c for c in lj(WD / "cases.json")["cases"]}
    seen, out = set(), []
    for req in sorted((WD / "check").glob("*/*/request.json")):
        r = lj(req); key = (r["procedure"], r["source"], r["case"], r["tag"])
        if key in seen: continue
        seen.add(key)
        out.append({"key": "-".join(key[:2]) + "__" + key[2] + "__" + key[3], "procedure": r["procedure"], "source": r["source"], "case": r["case"], "tag": r["tag"],
                    "problem": cases[r["case"]]["problem"], "quote": r["objection"].get("quote"), "objection": r["objection"].get("witness"), "path": cases[r["case"]]["path"], "sha256": cases[r["case"]]["sha256"]})
    return out

def call(kind, model, system, user, key, timeout):
    return W.call_model(kind, model, system, user, key, timeout)

def check_one(args, key, ob):
    kind, model = MODELS[args.checker]
    out = RA / "check" / args.checker / ob["key"]
    if (out / "parsed.json").exists() and not args.redo: return "cached"
    text = pathlib.Path(ob["path"]).read_bytes(); assert sha256(text) == ob["sha256"]
    system = system_for(ob["problem"], "check")
    user = ("## Write-up\n\n" + text.decode(errors="replace")[:W.MAX_CHARS] + "\n\n## Objection\n\nQuote (claimed verbatim from the write-up): "
            + json.dumps(ob["quote"], ensure_ascii=False) + "\nObjection: " + str(ob["objection"]) + "\n")
    t0 = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    status, resp = call(kind, model, system, user, key, args.timeout)
    txt = W.resp_text(resp) if status == 200 else ""
    parsed = W.extract_json(txt) if txt else None
    dj(out / "request.json", {"checker": args.checker, "model": model, "transport": kind, "objection_key": ob["key"], "case": ob["case"], "problem": ob["problem"], "text_sha256": ob["sha256"],
                              "system_sha256": sha256(system.encode()), "system": system, "quote": ob["quote"], "objection": ob["objection"], "started_utc": t0})
    dj(out / "response.json", {"status": status, "response": resp})
    if parsed is not None:
        anchor = W.anchored(parsed.get("elsewhere_quote"), text.decode(errors="replace")) if parsed.get("elsewhere_quote") else None
        dj(out / "parsed.json", {"checker": args.checker, "objection_key": ob["key"], "case": ob["case"], "procedure": ob["procedure"], "source": ob["source"], "status": status,
                                 "usage": W.usage_of(resp), "parsed": parsed, "elsewhere_anchor": anchor})
        print(f"[{args.checker}] {ob['key']}: {parsed.get('affected_statement')} correct={parsed.get('objection_correct')} elsewhere={parsed.get('established_elsewhere')} status={parsed.get('status_as_written')} repair={parsed.get('repair_distance')} {W.usage_of(resp).get('elapsed_seconds')}s", flush=True)
        return "ok"
    print(f"[{args.checker}] {ob['key']}: FAILED status={status} {str(resp)[:200]}", flush=True)
    return "failed"

def cmd_check(args):
    key = pathlib.Path(args.key_file).expanduser().read_text().strip() if args.checker == "glm" else ""
    obs = objections()
    if args.only: obs = [o for o in obs if o["case"] in set(args.only.split(","))]
    print(f"{len(obs)} objections for checker {args.checker}")
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        res = list(ex.map(lambda o: check_one(args, key, o), obs))
    print({r: res.count(r) for r in set(res)}); return 0

def rate_one(args, key, case):
    kind, model = MODELS[args.rater]
    out = RA / "rate" / args.rater / case["id"]
    if (out / "parsed.json").exists() and not args.redo: return "cached"
    text = pathlib.Path(case["path"]).read_bytes(); assert sha256(text) == case["sha256"]
    system = system_for(case["problem"], "rate")
    user = "## Write-up to rate\n\n" + text.decode(errors="replace")[:W.MAX_CHARS]
    t0 = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    status, resp = call(kind, model, system, user, key, args.timeout)
    txt = W.resp_text(resp) if status == 200 else ""
    parsed = W.extract_json(txt) if txt else None
    dj(out / "request.json", {"rater": args.rater, "model": model, "transport": kind, "case": case["id"], "problem": case["problem"], "text_sha256": case["sha256"], "system_sha256": sha256(system.encode()), "system": system, "started_utc": t0})
    dj(out / "response.json", {"status": status, "response": resp})
    if parsed is not None:
        anchors = {k: (W.anchored(v.get("quote"), text.decode(errors="replace")) if isinstance(v, dict) and v.get("quote") else None) for k, v in (parsed.get("statements") or {}).items()}
        dj(out / "parsed.json", {"rater": args.rater, "case": case["id"], "problem": case["problem"], "group": case["group"], "status": status, "usage": W.usage_of(resp), "parsed": parsed, "anchors": anchors})
        print(f"[{args.rater}] {case['id']}: S_ref={parsed.get('S_ref')} { {k: (v.get('established') if isinstance(v, dict) else v) for k, v in (parsed.get('statements') or {}).items()} } {W.usage_of(resp).get('elapsed_seconds')}s", flush=True)
        return "ok"
    print(f"[{args.rater}] {case['id']}: FAILED status={status} {str(resp)[:200]}", flush=True)
    return "failed"

def cmd_rate(args):
    key = pathlib.Path(args.key_file).expanduser().read_text().strip() if args.rater == "glm" else ""
    cases = lj(WD / "cases.json")["cases"]
    if args.only: cases = [c for c in cases if c["id"] in set(args.only.split(","))]
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        res = list(ex.map(lambda c: rate_one(args, key, c), cases))
    print({r: res.count(r) for r in set(res)}); return 0

# ---------------------------------------------------------------- analysis (v8: uncertainty-preserving aggregation; reporting only)
# Nothing below makes a model call or touches the retained check/rate returns; every number is recomputed from parsed.json.
STATUSES = ("not_established", "false_display", "established", "not_applicable")
STRICTNESS = {"not_established": 0, "false_display": 1, "established": 2, "not_applicable": 3}  # smaller = stricter
CONVENTIONS = {"AW": "as written: a consensus false display counts as not established",
               "RT": "repair-tolerant: a consensus false display counts as established"}
NEGATIVE = {"AW": {"not_established", "false_display"}, "RT": {"not_established"}}
CATEGORY_PRIORITY = ("not_established", "mixed", "unresolved", "established", "no_objection")
SCORED = ("lower_bound", "upper_bound")
NAMES = {"gpt": "GPT", "claude": "Claude", "glm": "GLM"}
TEXT_NAMES = {"kimi-k3-round3-t007": "Kimi P3 round 3", "kimi-k3-round4-t014": "Kimi P3 round 4", "p6-kimi-k3-round1-t021": "Kimi P6 round 1",
              "p1-glm52-2ede1c6b-v1": "GLM P1 candidate", "p5-deepseek-v4-pro-main-t033": "DeepSeek P5 t033",
              "p5-deepseek-v4-pro-main-t038": "DeepSeek P5 t038", "p5-nemotron-2587b733-v2": "Nemotron P5"}
WORDS = {0: "no", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
RULES = {
    "objection": "consensus = both checkers' status_as_written when equal; otherwise split, with the ordered pair (gpt, claude) recorded (split_type = gpt status/claude status). "
                 "Every ledger statement named by either checker is attributed (affected_all); when the two differ, both statements' obligations receive the objection.",
    "objection_class": "per convention: consensus_negative if both statuses are negative under the convention (AW: not_established or false_display; RT: not_established), "
                       "consensus_positive if the statuses are equal and not negative, otherwise unresolved. So a not_established/false_display split is a consensus "
                       "negative under AW and unresolved under RT; not_established/established and established/false_display splits are unresolved under both.",
    "statement_category": "mixed if the statement carries both a consensus_negative and a consensus_positive objection; else not_established if any consensus_negative; "
                          "else unresolved if any unresolved; else established if any consensus_positive; else no_objection.",
    "obligation_category": "the highest-priority category among the obligation's ledger statements (OBLIGATION_MAP), priority " + " > ".join(CATEGORY_PRIORITY) + ". "
                           "No obligation category merges no_objection with established.",
    "D": "D = number of the text's two scored obligations in category not_established; mixed and unresolved obligations are counted as unresolved, not in D. "
         "S_not_contradicted = 2 - D. P4 (no ledger statements) is excluded from every ledger-based count (19 texts, 38 scored obligations).",
    "dispute_partition": "fail = D > 0; unresolved = D == 0 and some scored obligation is unresolved or mixed; neither = no negative and no unresolved. "
                         "strict variant: fail also when a scored obligation is mixed.",
    "wording_sensitivity": "for each (checker, text, ledger statement named by that checker) judged under two or more objections: changed if the checker's "
                           "status_as_written differs across those objections (three-valued); also reported with the statuses collapsed to negative/positive under AW and under RT.",
    "anchoring": "mechanical (witness_discovery.anchored: whitespace/markup-normalized substring); stage 1: established_elsewhere == yes claims; stage 2: statement ratings established == yes.",
    "v7_compat": "reference_outcome / S_reference keep the v7 rule (splits ignored; no objection merged with established) for comparison only; they are superseded by categories/D/S_not_contradicted.",
}

def _side(status, conv): return "neg" if status in NEGATIVE[conv] else "pos"

def classify(o, conv):
    """consensus_negative | consensus_positive | unresolved | pending, for one objection under one convention (RULES['objection_class'])."""
    if o["n_checks"] < 2: return "pending"
    sg, sc = (o["checks"][c].get("status_as_written") for c in ("gpt", "claude"))
    if sg not in STATUSES or sc not in STATUSES: return "unresolved"
    if sg == sc: return "consensus_negative" if _side(sg, conv) == "neg" else "consensus_positive"
    if _side(sg, conv) == "neg" and _side(sc, conv) == "neg": return "consensus_negative"
    return "unresolved"

def stmt_category(neg, pos, unr):
    if neg and pos: return "mixed"
    if neg: return "not_established"
    if unr: return "unresolved"
    if pos: return "established"
    return "no_objection"

def load_stage1(ra, wd, cmap):
    """The 96 objections with both checkers' parsed returns and the per-objection consensus fields. Returns (obs, objection_texts)."""
    obs, texts = {}, {}
    for req in sorted((wd / "check").glob("*/*/request.json")):
        r = lj(req); key = "-".join((r["procedure"], r["source"])) + "__" + r["case"] + "__" + r["tag"]
        obs.setdefault(key, {"key": key, "procedure": r["procedure"], "source": r["source"], "case": r["case"], "tag": r["tag"], "problem": cmap[r["case"]]["problem"], "group": cmap[r["case"]]["group"], "checks": {}})
        texts.setdefault(key, str(r["objection"].get("witness")) + "\n" + str(r["objection"].get("quote")))
    for chk in ("gpt", "claude"):
        for p in (ra / "check" / chk).glob("*/parsed.json"):
            d = lj(p); k = d["objection_key"]
            if k in obs: obs[k]["checks"][chk] = {**{f: d["parsed"].get(f) for f in ("affected_statement", "objection_correct", "established_elsewhere", "elsewhere_quote", "status_as_written", "repair_distance", "explanation")}, "elsewhere_anchor": d.get("elsewhere_anchor"), "usage": d.get("usage")}
    for o in obs.values():
        chks = [c for c in ("gpt", "claude") if c in o["checks"]]
        st = [o["checks"][c]["status_as_written"] for c in chks]; aff = [o["checks"][c]["affected_statement"] for c in chks]
        o["n_checks"] = len(st)
        o["adjudicated"] = (st[0] if len(st) == 2 and st[0] == st[1] else ("split" if len(st) == 2 else ("single:" + st[0] if st else "pending")))
        o["affected_agree"] = (len(aff) == 2 and aff[0] == aff[1])
        o["affected"] = aff[0] if aff and (len(aff) == 1 or aff[0] == aff[1]) else ("/".join(aff) if aff else None)
        o["same_lab"] = {c: (c == o["source"]) for c in o["checks"]}
        # v8 fields
        o["affected_all"] = sorted({a for a in aff if a not in (None, "none")})
        o["same_statement"] = len(aff) == 2 and aff[0] == aff[1]
        o["endorsed"] = {c: o["checks"][c].get("objection_correct") == "yes" for c in chks}
        o["endorsed_both"] = len(chks) == 2 and all(o["endorsed"].values())
        if len(st) == 2 and st[0] != st[1]:
            o["split_pair"] = {"gpt": st[0], "claude": st[1]}
            o["split_type"] = st[0] + "/" + st[1]  # ordered pair (gpt, claude)
            o["stricter"] = "gpt" if STRICTNESS.get(st[0], 9) < STRICTNESS.get(st[1], 9) else "claude"
        else: o["split_pair"] = o["split_type"] = o["stricter"] = None
        o["class"] = {conv: classify(o, conv) for conv in CONVENTIONS}
    return obs, texts

def text_outcomes(c, ob_here, conv):
    """Per-statement and per-obligation categories of one text under one convention (RULES['statement_category'], ['obligation_category'], ['D'])."""
    problem = c["problem"]; omap = OBLIGATION_MAP[problem]; ids_all = [k for k, _ in LEDGER[problem]]
    scored_ids = [i for obl in SCORED for i in omap[obl]]
    stmts = {}
    for sid in ids_all:
        rel = [o for o in ob_here if o["n_checks"] == 2 and sid in o["affected_all"]]
        neg = [o["key"] for o in rel if o["class"][conv] == "consensus_negative"]
        pos = [o["key"] for o in rel if o["class"][conv] == "consensus_positive"]
        unr = [o["key"] for o in rel if o["class"][conv] == "unresolved"]
        stmts[sid] = {"category": stmt_category(neg, pos, unr), "scored": sid in scored_ids, "consensus_negative": neg, "consensus_positive": pos, "unresolved": unr}
    obl = {}
    for ob in SCORED:
        ids = omap[ob]
        obl[ob] = {"category": (min((stmts[i]["category"] for i in ids), key=CATEGORY_PRIORITY.index) if ids else "not_applicable"), "statements": {i: stmts[i]["category"] for i in ids}}
    cats = [obl[ob]["category"] for ob in SCORED]
    D = sum(1 for x in cats if x == "not_established") if scored_ids else None
    unscored = [{"key": o["key"], "statements": [s for s in o["affected_all"] if s not in scored_ids], "adjudicated": o["adjudicated"], "split_pair": o["split_pair"]}
                for o in ob_here if o["n_checks"] == 2 and o["class"][conv] == "consensus_negative" and any(s not in scored_ids for s in o["affected_all"])]
    return {"obligations": obl, "statements": stmts, "D": D, "S_not_contradicted": (2 - D) if D is not None else None,
            "n_unresolved": sum(1 for x in cats if x in ("unresolved", "mixed")), "n_mixed": sum(1 for x in cats if x == "mixed"),
            "unresolved": any(x in ("unresolved", "mixed") for x in cats), "unscored_consensus_negative": unscored}

def _empty_pair_mentions(text):
    """True if the text speaks of an empty subset/pair other than through 'nonempty'/'non-empty' (used for the L3.2 ledger-correction check)."""
    return re.search(r"(?<!non)(?<!non-)empty", text, re.I) is not None

def cmd_analyze(args):
    root = pathlib.Path(args.root).resolve() if args.root else ROOT
    art = root / "artifacts" if (root / "artifacts" / "reference_adjudication").exists() else root
    ra, wd = art / "reference_adjudication", art / "witness_discovery"
    cases = lj(wd / "cases.json")["cases"]; cmap = {c["id"]: c for c in cases}
    v6 = lj(wd / "results.json")
    obs, otexts = load_stage1(ra, wd, cmap)
    # ---- per-objection endpoints (v7 headline counts, unchanged rules)
    n = len(obs); done = [o for o in obs.values() if o["n_checks"] == 2]
    with_stmt = [o for o in done if all(o["checks"][c]["affected_statement"] not in (None, "none") for c in ("gpt", "claude"))]
    agree = [o for o in done if o["adjudicated"] not in ("split",)]
    counts = {"objections": n, "both_checked": len(done), "affected_statement_both": len(with_stmt), "status_agree": len(agree), "split": sum(1 for o in done if o["adjudicated"] == "split"),
              "by_status": {s: sum(1 for o in done if o["adjudicated"] == s) for s in ("established", "not_established", "false_display", "not_applicable", "split")},
              "by_procedure": {proc: {s: sum(1 for o in done if o["procedure"] == proc and o["adjudicated"] == s) for s in ("established", "not_established", "false_display", "not_applicable", "split")} for proc in ("witness", "grader")}}
    # same-lab vs other-lab: objection_correct counts are ENDORSEMENT of the local objection (not agreement with an adjudicated status)
    lab = {"same": {"n": 0, "objection_correct": 0, "established": 0, "not_established": 0}, "other": {"n": 0, "objection_correct": 0, "established": 0, "not_established": 0}}
    for o in done:
        for c in ("gpt", "claude"):
            b = "same" if c == o["source"] else "other"; v = o["checks"][c]; lab[b]["n"] += 1
            lab[b]["objection_correct"] += int(v.get("objection_correct") == "yes"); lab[b]["established"] += int(v.get("status_as_written") == "established"); lab[b]["not_established"] += int(v.get("status_as_written") == "not_established")
    lab["splits_by_source"] = {src: sum(1 for o in done if o["adjudicated"] == "split" and o["source"] == src) for src in ("gpt", "claude")}
    lab["note"] = "objection_correct counts are endorsement rates of the local objection (objection_correct == yes), not agreement with the adjudicated status; see objection_consensus."
    # ---- v8: consensus / split / identity / endorsement summary
    splits = [o for o in done if o["adjudicated"] == "split"]
    split_types = {}
    for o in splits: split_types[o["split_type"]] = split_types.get(o["split_type"], 0) + 1
    split_types = dict(sorted(split_types.items(), key=lambda kv: (-kv[1], kv[0])))
    stricter = {c: sum(1 for o in splits if o["stricter"] == c) for c in ("gpt", "claude")}
    consensus = {"same_statement": sum(1 for o in done if o["same_statement"]), "different_statement": [{"key": o["key"], "gpt": o["checks"]["gpt"]["affected_statement"], "claude": o["checks"]["claude"]["affected_statement"], "statuses": [o["checks"][c]["status_as_written"] for c in ("gpt", "claude")]} for o in done if not o["same_statement"]],
                 "endorsed_both": sum(1 for o in done if o["endorsed_both"]), "endorsed_by_checker": {c: sum(1 for o in done if o["endorsed"].get(c)) for c in ("gpt", "claude")},
                 "not_endorsed": [{"key": o["key"], c: o["checks"][c].get("objection_correct")} for o in done for c in ("gpt", "claude") if not o["endorsed"].get(c)],
                 "endorsement_by_lab": {b: f"{lab[b]['objection_correct']}/{lab[b]['n']}" for b in ("same", "other")},
                 "splits": [{"key": o["key"], "case": o["case"], "pair": o["split_pair"], "type": o["split_type"], "stricter": o["stricter"], "statements": o["affected_all"], "class": o["class"]} for o in splits],
                 "split_types": split_types, "split_texts": sorted({o["case"] for o in splits}), "stricter_on_splits": stricter,
                 "class_counts": {conv: {cl: sum(1 for o in done if o["class"][conv] == cl) for cl in ("consensus_negative", "consensus_positive", "unresolved")} for conv in CONVENTIONS}}
    # ---- stage 2 ratings
    rates = {}
    for rater in ("gpt", "claude", "glm"):
        for p in (ra / "rate" / rater).glob("*/parsed.json"):
            d = lj(p); rates.setdefault(d["case"], {})[rater] = {"S_ref": d["parsed"].get("S_ref"), "statements": {k: (v.get("established") if isinstance(v, dict) else v) for k, v in (d["parsed"].get("statements") or {}).items()}, "anchors": d.get("anchors"), "usage": d.get("usage")}
    # ---- per-text outcomes (v7 rule kept for comparison; v8 categories under both conventions)
    per_text = {}
    for c in cases:
        cid = c["id"]; e = v6["per_case"][cid]; ob_here = [o for o in obs.values() if o["case"] == cid]
        outcome = {}
        for obl in SCORED:
            ids = set(OBLIGATION_MAP[c["problem"]][obl])
            rel = [o for o in ob_here if o["adjudicated"] in ("not_established", "false_display") and (o["affected"] in ids or (o["affected"] or "").split("/")[0] in ids)]
            if any(o["adjudicated"] == "not_established" for o in rel): outcome[obl] = "not_established"
            elif rel: outcome[obl] = "false_display_only"
            else: outcome[obl] = "established_or_no_objection"
        S_ref_labs = {r: rates.get(cid, {}).get(r, {}).get("S_ref") for r in ("gpt", "claude", "glm")}
        conv_out = {conv: text_outcomes(c, ob_here, conv) for conv in CONVENTIONS}
        per_text[cid] = {"group": c["group"], "problem": c["problem"], "name": TEXT_NAMES.get(cid, cid), "ledger_scored": c["problem"] != "4",
                         "reference_outcome": outcome, "S_reference": sum(1 for obl in SCORED if outcome[obl] == "established_or_no_objection"), "S_reference_note": RULES["v7_compat"],
                         "categories": {conv: {obl: conv_out[conv]["obligations"][obl]["category"] for obl in SCORED} for conv in CONVENTIONS},
                         "D": {conv: conv_out[conv]["D"] for conv in CONVENTIONS}, "S_not_contradicted": {conv: conv_out[conv]["S_not_contradicted"] for conv in CONVENTIONS},
                         "n_unresolved": {conv: conv_out[conv]["n_unresolved"] for conv in CONVENTIONS}, "n_mixed": {conv: conv_out[conv]["n_mixed"] for conv in CONVENTIONS},
                         "unresolved": {conv: conv_out[conv]["unresolved"] for conv in CONVENTIONS},
                         "unscored_consensus_negative": {conv: conv_out[conv]["unscored_consensus_negative"] for conv in CONVENTIONS},
                         "statements": {conv: conv_out[conv]["statements"] for conv in CONVENTIONS},
                         "S_ref_ratings": S_ref_labs, "v6_S_valid": {s: (e["witness"].get(s) or {}).get("S_valid") for s in ("gpt", "claude")},
                         "v6_grade": {s: (e["grader"].get(s) or {}).get("grade") for s in ("gpt", "claude")}, "record_defect": c.get("record_defect"),
                         "objections": [{"key": o["key"], "adjudicated": o["adjudicated"], "split_pair": o["split_pair"], "affected": o["affected"], "affected_all": o["affected_all"], "class": o["class"], "repair": [o["checks"][ch].get("repair_distance") for ch in ("gpt", "claude") if ch in o["checks"]]} for o in ob_here]}
    scored_texts = [cid for cid in per_text if per_text[cid]["ledger_scored"]]
    obligations = {"n_texts": len(scored_texts), "n_obligations": 2 * len(scored_texts), "excluded": [cid for cid in per_text if not per_text[cid]["ledger_scored"]],
                   "by_category": {conv: {cat: sum(1 for cid in scored_texts for obl in SCORED if per_text[cid]["categories"][conv][obl] == cat) for cat in CATEGORY_PRIORITY} for conv in CONVENTIONS},
                   "texts_with_unresolved": {conv: [cid for cid in scored_texts if per_text[cid]["unresolved"][conv]] for conv in CONVENTIONS},
                   "texts_with_mixed": {conv: [cid for cid in scored_texts if per_text[cid]["n_mixed"][conv]] for conv in CONVENTIONS},
                   "D_distribution": {conv: {str(d): sum(1 for cid in scored_texts if per_text[cid]["D"][conv] == d) for d in (0, 1, 2)} for conv in CONVENTIONS}}
    # ---- disputes (groups C, D): partition under both conventions
    disputes = {cid: per_text[cid] for cid in per_text if per_text[cid]["group"] in "CD"}
    def partition(conv, strict=False):
        out = {"fail": [], "unresolved": [], "neither": []}
        for cid, t in disputes.items():
            if t["D"][conv] > 0 or (strict and t["n_mixed"][conv] > 0): out["fail"].append(cid)
            elif t["unresolved"][conv]: out["unresolved"].append(cid)
            else: out["neither"].append(cid)
        return out
    dispute_partition = {conv: partition(conv) for conv in CONVENTIONS}
    dispute_partition.update({conv + "_strict": partition(conv, True) for conv in CONVENTIONS})
    dispute_partition["rule"] = RULES["dispute_partition"]
    dispute_partition["unscored_consensus_negative"] = {cid: {conv: [(u["key"], u["statements"]) for u in t["unscored_consensus_negative"][conv]] for conv in CONVENTIONS} for cid, t in disputes.items()}
    false_display = [o["key"] for o in done if o["adjudicated"] == "false_display"]
    # ---- wording sensitivity: same checker, same text, same statement, different objection wording
    groups = {}
    for o in done:
        for c in ("gpt", "claude"):
            groups.setdefault((c, o["case"], o["checks"][c]["affected_statement"]), []).append((o["key"], o["checks"][c]["status_as_written"]))
    multi = {k: v for k, v in groups.items() if len(v) >= 2}
    def changed(v, conv=None): return len({(s if conv is None else _side(s, conv)) for _, s in v}) > 1
    wording = {"n": len(multi), "changed": sum(1 for v in multi.values() if changed(v)),
               "changed_collapsed": {conv: sum(1 for v in multi.values() if changed(v, conv)) for conv in CONVENTIONS},
               "by_checker": {c: {"n": sum(1 for k in multi if k[0] == c), "changed": sum(1 for k, v in multi.items() if k[0] == c and changed(v))} for c in ("gpt", "claude")},
               "changed_list": [{"checker": k[0], "case": k[1], "statement": k[2], "judgments": v} for k, v in sorted(multi.items()) if changed(v)],
               "rule": RULES["wording_sensitivity"]}
    # ---- anchoring
    elsewhere = [(o["key"], c, (o["checks"][c].get("elsewhere_anchor") or {})) for o in done for c in ("gpt", "claude") if o["checks"][c].get("established_elsewhere") == "yes"]
    anchoring = {"stage1_established_elsewhere": {"n": len(elsewhere), "anchored": sum(1 for _, _, a in elsewhere if a.get("anchored")),
                                                  "by_checker": {c: {"n": sum(1 for _, cc, _ in elsewhere if cc == c), "anchored": sum(1 for _, cc, a in elsewhere if cc == c and a.get("anchored"))} for c in ("gpt", "claude")},
                                                  "not_anchored": [{"key": k, "checker": c, "reason": a.get("reason")} for k, c, a in elsewhere if not a.get("anchored")]},
                 "stage2_positive_ratings": {}, "nonledger_rating_keys": []}
    s2 = anchoring["stage2_positive_ratings"]; tot_n = tot_a = 0
    for rater in ("gpt", "claude", "glm"):
        n_pos = n_anc = n_two = n_two_full = 0; partial = []
        for cid in sorted(rates):
            r = rates[cid].get(rater)
            if not r: continue
            pos = [k for k, v in r["statements"].items() if v == "yes"]
            anc = [k for k in pos if ((r.get("anchors") or {}).get(k) or {}).get("anchored")]
            n_pos += len(pos); n_anc += len(anc)
            for k in r["statements"]:
                if k not in {i for i, _ in LEDGER[per_text[cid]["problem"]]}: anchoring["nonledger_rating_keys"].append({"rater": rater, "case": cid, "key": k})
            if r["S_ref"] == 2:
                n_two += 1
                if len(anc) == len(pos): n_two_full += 1
                else: partial.append({"case": cid, "positive": pos, "anchored": anc, "unanchored": [k for k in pos if k not in anc]})
        s2[rater] = {"positive": n_pos, "anchored": n_anc, "S_ref_2": n_two, "S_ref_2_fully_anchored": n_two_full, "S_ref_2_not_fully_anchored": partial}
        tot_n += n_pos; tot_a += n_anc
    s2["total"] = {"positive": tot_n, "anchored": tot_a, "S_ref_2": sum(s2[r]["S_ref_2"] for r in NAMES), "S_ref_2_fully_anchored": sum(s2[r]["S_ref_2_fully_anchored"] for r in NAMES)}
    anchoring["rule"] = RULES["anchoring"]
    # ---- ratings vs outcome (19 ledger-scored texts)
    rvo = {}
    for r in ("gpt", "claude", "glm"):
        rvo[r] = {"n": len(scored_texts)}
        for conv in CONVENTIONS:
            res = [cid for cid in scored_texts if not per_text[cid]["unresolved"][conv]]
            rvo[r]["match_" + conv] = sum(1 for cid in scored_texts if per_text[cid]["S_ref_ratings"][r] is not None and per_text[cid]["S_ref_ratings"][r] == per_text[cid]["S_not_contradicted"][conv])
            # interval membership: the not-contradicted score is an interval [2 - D - U, 2 - D] where U counts unresolved and mixed scored obligations
            for cid in scored_texts:
                per_text[cid].setdefault("S_interval", {})[conv] = [2 - per_text[cid]["D"][conv] - per_text[cid]["n_unresolved"][conv], 2 - per_text[cid]["D"][conv]]
            rvo[r]["within_" + conv] = sum(1 for cid in scored_texts if per_text[cid]["S_ref_ratings"][r] is not None and per_text[cid]["S_interval"][conv][0] <= per_text[cid]["S_ref_ratings"][r] <= per_text[cid]["S_interval"][conv][1])
            rvo[r]["match_" + conv + "_resolved_only"] = {"n": len(res), "match": sum(1 for cid in res if per_text[cid]["S_ref_ratings"][r] is not None and per_text[cid]["S_ref_ratings"][r] == per_text[cid]["S_not_contradicted"][conv])}
            rvo[r]["mismatch_" + conv] = [{"case": cid, "S_ref": per_text[cid]["S_ref_ratings"][r], "S_not_contradicted": per_text[cid]["S_not_contradicted"][conv], "unresolved": per_text[cid]["unresolved"][conv]} for cid in scored_texts if per_text[cid]["S_ref_ratings"][r] != per_text[cid]["S_not_contradicted"][conv]]
        rvo[r]["match_v7_S_reference_20"] = sum(1 for cid, t in per_text.items() if t["S_ref_ratings"][r] is not None and t["S_ref_ratings"][r] == t["S_reference"])
        rvo[r]["anchoring"] = {k: s2[r][k] for k in ("positive", "anchored", "S_ref_2", "S_ref_2_fully_anchored")}
    # ---- ledger version check (LEDGER_v2.md corrections must not touch a scored outcome)
    scored_ids = {i for p in OBLIGATION_MAP for obl in SCORED for i in OBLIGATION_MAP[p][obl]}
    l61 = [{"key": o["key"], "case": o["case"], "statuses": [o["checks"][c]["status_as_written"] for c in ("gpt", "claude")], "adjudicated": o["adjudicated"]} for o in done if "L6.1" in o["affected_all"]]
    l32 = [o for o in done if "L3.2" in o["affected_all"]]
    l32_empty = [o["key"] for o in l32 if _empty_pair_mentions(otexts.get(o["key"], "") + "\n" + "\n".join(str(o["checks"][c].get("explanation")) for c in ("gpt", "claude")))]
    unknown_ids = [{"key": o["key"], "id": a} for o in done for a in o["affected_all"] if a not in {i for i, _ in LEDGER[o["problem"]]}]
    ledger_version = {"used_for_all_judgments": "LEDGER.md (v1); every request.json reproduces the ledger's statement list generated from it, not the file, which additionally records provenance and cross-checks", "corrected": "LEDGER_v2.md (analysis-time corrections; no judgment re-run)",
                      "L6.1_scored": "L6.1" in scored_ids, "L6.1_objections": l61, "L6.1_stage2_ratings": sum(1 for cid in rates for r in rates[cid] if "L6.1" in rates[cid][r]["statements"]),
                      "L3.2_objections": len(l32), "L3.2_checker_judgments": sum(1 for o in l32 for c in ("gpt", "claude") if o["checks"][c]["affected_statement"] == "L3.2"),
                      "L3.2_objections_mentioning_empty_pair": l32_empty, "L3.2_stage2_ratings": sum(1 for cid in rates for r in rates[cid] if "L3.2" in rates[cid][r]["statements"]),
                      "unknown_statement_ids": unknown_ids}
    ledger_version["no_scored_outcome_depends_on_corrections"] = (not ledger_version["L6.1_scored"]) and not l32_empty
    # ---- costs
    def secs(paths):
        v = [lj(p).get("usage", {}).get("elapsed_seconds") for p in paths]; v = [x for x in v if isinstance(x, (int, float))]
        return {"n": len(paths), "timed": len(v), "mean_s": round(sum(v) / len(v), 1) if v else None}
    cost = {f"check-{c}": secs(list((ra / "check" / c).glob("*/parsed.json"))) for c in ("gpt", "claude")}
    cost.update({f"rate-{r}": secs(list((ra / "rate" / r).glob("*/parsed.json"))) for r in ("gpt", "claude", "glm")})
    results = {"protocol": "PROTOCOL.md", "analyzed_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), "frozen": bool(args.freeze), "analysis_version": "v8 (uncertainty-preserving aggregation; check/rate returns unchanged)",
               "conventions": CONVENTIONS, "rules": RULES, "counts": counts, "lab_agreement": lab, "objection_consensus": consensus, "obligations": obligations,
               "false_display_objections": false_display, "per_text": per_text, "disputes": disputes, "dispute_partition": dispute_partition, "wording_sensitivity": wording,
               "anchoring": anchoring, "ratings_vs_outcome": rvo, "ledger_version": ledger_version, "ratings_coverage": {r: sum(1 for cid in rates if r in rates[cid]) for r in ("gpt", "claude", "glm")},
               "cost": cost, "objections": list(obs.values())}
    dj(ra / "results.json", results)
    write_reports(results, cases, ra, root)
    summary = {k: results[k] for k in ("counts", "ratings_coverage", "cost")}
    summary.update({"same_statement": consensus["same_statement"], "endorsed_both": consensus["endorsed_both"], "split_types": split_types, "stricter": stricter,
                    "obligations_by_category": obligations["by_category"], "dispute_partition": {k: dispute_partition[k] for k in ("AW", "RT", "AW_strict", "RT_strict")},
                    "wording": {k: wording[k] for k in ("n", "changed", "changed_collapsed")}, "anchoring_stage1": {k: anchoring["stage1_established_elsewhere"][k] for k in ("n", "anchored")},
                    "anchoring_stage2": s2["total"], "ratings_vs_outcome": {r: {k: rvo[r][k] for k in ("match_AW", "match_RT", "within_AW", "within_RT", "n")} for r in rvo},
                    "ledger_ok": ledger_version["no_scored_outcome_depends_on_corrections"]})
    print(json.dumps(summary, indent=1)); return 0

def tex(x): return str(x).replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#").replace("$", r"\$")

SYM = {"not_established": r"$\times$", "unresolved": "?", "mixed": "m", "established": r"\checkmark", "no_objection": "--", "not_applicable": "n/a"}
SHORT = {"not_established": "not est.", "false_display": "false disp.", "established": "est.", "not_applicable": "n/a", None: "--"}

def _one_line(s): return re.sub(r"\s+", " ", str(s or "")).strip()

def _names(cids, pt): return ", ".join(pt[c]["name"] for c in cids) if cids else "none"

def _join_and(items): return items[0] if len(items) == 1 else (", ".join(items[:-1]) + " and " + items[-1]) if items else "none"

def write_reports(results, cases, ra, root):
    pt = results["per_text"]; cn = results["counts"]; cons = results["objection_consensus"]; obl = results["obligations"]; dp = results["dispute_partition"]
    wo = results["wording_sensitivity"]; an = results["anchoring"]; rvo = results["ratings_vs_outcome"]; lv = results["ledger_version"]; full = {x["key"]: x for x in results["objections"]}
    convs = list(CONVENTIONS)
    # ---------------- RESULTS.md
    md = [f"# Reference-anchored adjudication: results\n\nAnalyzed {results['analyzed_utc']} (frozen: {results['frozen']}; {results['analysis_version']}). Rules: PROTOCOL.md and the `rules` block of results.json; ledger used for every judgment: LEDGER.md (v1); corrected ledger: LEDGER_v2.md (not used for any judgment).\n",
          "\n## 1. Headline counts (v7 rules, unchanged)\n",
          f"\nObjections: {cn['objections']}; both checkers returned: {cn['both_checked']}; some ledger statement named by both: {cn['affected_statement_both']}; the same statement named by both: {cons['same_statement']}; status agreement: {cn['status_agree']} (split {cn['split']}); by status: {cn['by_status']}; by procedure: {cn['by_procedure']}.\n",
          f"\nEndorsement (objection_correct == yes; this is not agreement with an adjudicated status): both checkers {cons['endorsed_both']}/{cn['both_checked']}; per checker {cons['endorsed_by_checker']}; same-lab {cons['endorsement_by_lab']['same']}, other-lab {cons['endorsement_by_lab']['other']}; not endorsed: {cons['not_endorsed']}.\n",
          f"\nStatement identity disagreements: {cons['different_statement']}. Ratings coverage: {results['ratings_coverage']}. False-display objections: {results['false_display_objections']}.\n",
          "\n## 2. Split objections\n", f"\nConventions: {CONVENTIONS}. Objection classes per convention: {cons['class_counts']}.\n",
          f"\nSplit types: {cons['split_types']}; texts carrying splits: {cons['split_texts']}; stricter checker on splits: {cons['stricter_on_splits']}.\n"]
    for s in cons["splits"]:
        md.append(f"- {s['key']}: gpt={s['pair']['gpt']}, claude={s['pair']['claude']} ({s['type']}; stricter: {s['stricter']}); statements {s['statements']}; class AW={s['class']['AW']}, RT={s['class']['RT']}\n")
    md += ["\n## 3. Scored obligations by category\n", f"\n{obl['n_texts']} ledger-scored texts (excluded: {obl['excluded']}), {obl['n_obligations']} scored obligations. Rule: {RULES['statement_category']} {RULES['obligation_category']} {RULES['D']}\n",
           "\n| category | AW | RT |\n|---|---:|---:|\n"]
    for cat in CATEGORY_PRIORITY: md.append(f"| {cat} | {obl['by_category']['AW'][cat]} | {obl['by_category']['RT'][cat]} |\n")
    md.append(f"| total | {sum(obl['by_category']['AW'].values())} | {sum(obl['by_category']['RT'].values())} |\n")
    md.append(f"\nD distribution (texts with D = 0/1/2): {obl['D_distribution']}. Texts with an unresolved or mixed scored obligation: {obl['texts_with_unresolved']}; with a mixed obligation: {obl['texts_with_mixed']}.\n")
    md += ["\n## 4. Wording sensitivity\n", f"\nRule: {wo['rule']}\n", f"\nTriples judged under two or more objections: {wo['n']}; status changed (three-valued): {wo['changed']}; changed after collapsing to negative/positive: AW {wo['changed_collapsed']['AW']}, RT {wo['changed_collapsed']['RT']}; by checker: {wo['by_checker']}.\n"]
    for w in wo["changed_list"]: md.append(f"- {w['checker']} / {w['case']} / {w['statement']}: {w['judgments']}\n")
    s1 = an["stage1_established_elsewhere"]; s2 = an["stage2_positive_ratings"]
    md += ["\n## 5. Anchoring\n", f"\nRule: {an['rule']}\n", f"\nStage 1 established-elsewhere claims: {s1['n']}, anchored {s1['anchored']}; by checker {s1['by_checker']}; not anchored: {s1['not_anchored']}.\n",
           f"\nStage 2 positive statement ratings: {s2['total']['positive']}, anchored {s2['total']['anchored']}; per rater: " + "; ".join(f"{NAMES[r]} {s2[r]['anchored']}/{s2[r]['positive']} (S_ref=2 ratings fully anchored {s2[r]['S_ref_2_fully_anchored']}/{s2[r]['S_ref_2']})" for r in NAMES) + f". Non-ledger rating keys: {an['nonledger_rating_keys']}.\n"]
    for r in NAMES:
        for p in s2[r]["S_ref_2_not_fully_anchored"]: md.append(f"- {NAMES[r]} S_ref=2 on {p['case']}: unanchored {p['unanchored']}\n")
    md += ["\n## 6. Disputed texts (groups C, D)\n", f"\nRule: {dp['rule']}\n"]
    for conv in convs:
        md.append(f"\n{conv}: fail {len(dp[conv]['fail'])}/{len(results['disputes'])} ({_names(dp[conv]['fail'], pt)}); unresolved only {len(dp[conv]['unresolved'])} ({_names(dp[conv]['unresolved'], pt)}); neither {len(dp[conv]['neither'])} ({_names(dp[conv]['neither'], pt)}). Strict variant (mixed counted as fail): fail {len(dp[conv + '_strict']['fail'])}.\n")
    md.append(f"\nConsensus-negative objections on statements outside the two scored obligations: {dp['unscored_consensus_negative']}.\n")
    md.append("\n### Per-dispute records (every objection; both checkers' status, statement, explanation)\n")
    for cid, t in results["disputes"].items():
        md.append(f"\n#### {t['name']} ({cid}, P{t['problem']}): categories AW {t['categories']['AW']} RT {t['categories']['RT']}; D AW={t['D']['AW']} RT={t['D']['RT']}; S_not_contradicted AW={t['S_not_contradicted']['AW']} RT={t['S_not_contradicted']['RT']}; ratings {t['S_ref_ratings']}; v6 S_valid {t['v6_S_valid']}; grades {t['v6_grade']}\n")
        for o in t["objections"]:
            x = full[o["key"]]
            head = f"**{o['adjudicated']}**" if o["adjudicated"] != "split" else f"**split** (gpt={o['split_pair']['gpt']}, claude={o['split_pair']['claude']})"
            md.append(f"- {o['key']}: {head}; statement(s) {o['affected_all']}; class AW={o['class']['AW']}, RT={o['class']['RT']}; repair {o['repair']}\n")
            for ch in ("gpt", "claude"):
                v = x["checks"].get(ch, {})
                md.append(f"  - {ch}: {v.get('status_as_written')} / {v.get('affected_statement')} / correct={v.get('objection_correct')} / elsewhere={v.get('established_elsewhere')}" + (f" (quote anchored: {(v.get('elsewhere_anchor') or {}).get('anchored')})" if v.get("elsewhere_quote") else "") + f": {_one_line(v.get('explanation'))}\n")
    md += ["\n## 7. Ledger-guided ratings vs adjudicated outcome\n", f"\nMatch = the rater's S_ref equals S_not_contradicted = 2 - D under the convention, over the {obl['n_texts']} ledger-scored texts (P4 excluded).\n",
           "\n| rater | AW | RT | AW (resolved texts only) | RT (resolved texts only) | v7 S_reference (/20) | positive ratings anchored | S_ref=2 fully anchored |\n|---|---:|---:|---:|---:|---:|---:|---:|\n"]
    for r in NAMES:
        v = rvo[r]; md.append(f"| {NAMES[r]} | {v['match_AW']}/{v['n']} | {v['match_RT']}/{v['n']} | {v['match_AW_resolved_only']['match']}/{v['match_AW_resolved_only']['n']} | {v['match_RT_resolved_only']['match']}/{v['match_RT_resolved_only']['n']} | {v['match_v7_S_reference_20']}/20 | {v['anchoring']['anchored']}/{v['anchoring']['positive']} | {v['anchoring']['S_ref_2_fully_anchored']}/{v['anchoring']['S_ref_2']} |\n")
    for r in NAMES:
        for conv in convs: md.append(f"- {NAMES[r]} mismatches under {conv}: {rvo[r]['mismatch_' + conv]}\n")
    md += ["\n## 8. Ledger version\n", f"\n{lv}\n", "\n## 9. Every text\n", "\nPer text: obligation categories under AW and RT (lower, upper), D, S_not_contradicted, the v7 outcome for comparison, ratings, v6 S_valid and grades; then every objection with both checkers.\n"]
    for g in "ABCDEF":
        md.append(f"\n### Group {g}\n")
        for c in cases:
            if c["group"] != g: continue
            t = pt[c["id"]]
            md.append(f"\n#### {c['id']} (P{c['problem']}): AW {t['categories']['AW']} D={t['D']['AW']}; RT {t['categories']['RT']} D={t['D']['RT']}; S_not_contradicted {t['S_not_contradicted']}; v7 outcome {t['reference_outcome']} (S_reference={t['S_reference']}); S_ref ratings {t['S_ref_ratings']}; v6 S_valid {t['v6_S_valid']}; grades {t['v6_grade']}\n")
            if t["record_defect"]: md.append(f"Documented defect: {t['record_defect']}\n")
            if t["unscored_consensus_negative"]["RT"]: md.append(f"Consensus not-established objections on unscored statements: {[(u['key'], u['statements']) for u in t['unscored_consensus_negative']['RT']]}\n")
            for o in t["objections"]:
                x = full[o["key"]]
                head = f"**{o['adjudicated']}**" if o["adjudicated"] != "split" else f"**split** (gpt={o['split_pair']['gpt']}, claude={o['split_pair']['claude']})"
                md.append(f"- {o['key']}: {head}, affected {o['affected']}, repair {o['repair']}\n")
                for ch, v in x["checks"].items():
                    md.append(f"  - {ch}{' (same lab)' if x['same_lab'].get(ch) else ''}: {v.get('status_as_written')} / {v.get('affected_statement')} / correct={v.get('objection_correct')} / elsewhere={v.get('established_elsewhere')}" + (f" (quote anchored: {(v.get('elsewhere_anchor') or {}).get('anchored')})" if v.get("elsewhere_quote") else "") + f": {v.get('explanation')}\n")
    (ra / "RESULTS.md").write_text("".join(md))
    # ---------------- per-text table
    L = [r"\begin{tabular}{@{}clcccccclcc@{}}", r"\toprule",
         r" & & \multicolumn{2}{c}{AW} & \multicolumn{2}{c}{RT} & \multicolumn{2}{c}{$D$} & ratings & v6 $S_{\mathrm{valid}}$ & grades \\",
         r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(lr){7-8}", r"Grp & Text & lo & up & lo & up & AW & RT & G/C/GLM & G/C & G/C \\", r"\midrule"]
    lastg = None
    for c in cases:
        t = pt[c["id"]]
        if lastg and c["group"] != lastg: L.append(r"\addlinespace[1pt]")
        lastg = c["group"]
        rr = "/".join("--" if t["S_ref_ratings"][r] is None else str(t["S_ref_ratings"][r]) for r in ("gpt", "claude", "glm"))
        cells = [SYM[t["categories"][conv][obl]] for conv in convs for obl in SCORED]
        dd = ["n/a" if t["D"][conv] is None else str(t["D"][conv]) for conv in convs]
        L.append(f"{c['group']} & {tex(c['id'])} & " + " & ".join(cells) + " & " + " & ".join(dd) + f" & {rr} & {t['v6_S_valid']['gpt']}/{t['v6_S_valid']['claude']} & {t['v6_grade']['gpt']}/{t['v6_grade']['claude']} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]
    (ra / "table_refadj.tex").write_text("\n".join(L) + "\n")
    # ---------------- disputes table: one row per objection on the disputed texts
    T = [r"\begin{tabular}{@{}llllll@{}}", r"\toprule", r"Text & Objection & Stmt & GPT & Claude & Repair G/C \\", r"\midrule"]
    first = True
    for cid, t in results["disputes"].items():
        if not first: T.append(r"\addlinespace[2pt]")
        first = False
        if not t["objections"]: T.append(f"{tex(t['name'])} & (no objection) & -- & -- & -- & -- \\\\"); continue
        for i, o in enumerate(t["objections"]):
            x = full[o["key"]]; proc_src, _, tag = o["key"].split("__")
            g, cl = x["checks"].get("gpt", {}), x["checks"].get("claude", {})
            sg, sc = SHORT.get(g.get("status_as_written"), str(g.get("status_as_written"))), SHORT.get(cl.get("status_as_written"), str(cl.get("status_as_written")))
            if o["adjudicated"] == "split": sg, sc = r"\textbf{" + sg + "}", r"\textbf{" + sc + "}"
            stmt = "/".join(o["affected_all"]) or "none"
            T.append(f"{tex(t['name']) if i == 0 else ''} & {tex(proc_src + '/' + tag.replace('_bound', ''))} & {tex(stmt)} & {sg} & {sc} & {tex((g.get('repair_distance') or '--') + '/' + (cl.get('repair_distance') or '--'))} \\\\")
    T += [r"\bottomrule", r"\end{tabular}"]
    (ra / "table_refadj_disputes.tex").write_text("\n".join(T) + "\n")
    # ---------------- macros (names carry no digits)
    bs = cn["by_status"]; bp = cn["by_procedure"]; lab = results["lab_agreement"]; cov = results["ratings_coverage"]
    m = [r"% generated by scripts/reference_adjudication.py analyze; do not edit",
         r"\newcommand{\REFADJN}{%d}" % cn["objections"], r"\newcommand{\REFADJDONE}{%d}" % cn["both_checked"],
         r"\newcommand{\REFADJSTMT}{%d}" % cn["affected_statement_both"], r"\newcommand{\REFADJSAMESTMT}{%d}" % cons["same_statement"],
         r"\newcommand{\REFADJAGREE}{%d}" % cn["status_agree"], r"\newcommand{\REFADJSPLIT}{%d}" % cn["split"],
         r"\newcommand{\REFADJNOTEST}{%d}" % bs["not_established"], r"\newcommand{\REFADJFALSEDISP}{%d}" % bs["false_display"], r"\newcommand{\REFADJEST}{%d}" % bs["established"], r"\newcommand{\REFADJNA}{%d}" % bs["not_applicable"],
         r"\newcommand{\REFADJWNOTEST}{%d}" % bp["witness"]["not_established"], r"\newcommand{\REFADJGNOTEST}{%d}" % bp["grader"]["not_established"],
         r"\newcommand{\REFADJWSPLIT}{%d}" % bp["witness"]["split"], r"\newcommand{\REFADJGSPLIT}{%d}" % bp["grader"]["split"],
         r"\newcommand{\REFADJENDORSE}{%d}" % cons["endorsed_both"],
         r"\newcommand{\REFADJENDORSESAME}{%d/%d}" % (lab["same"]["objection_correct"], lab["same"]["n"]), r"\newcommand{\REFADJENDORSEOTHER}{%d/%d}" % (lab["other"]["objection_correct"], lab["other"]["n"]),
         r"\newcommand{\REFADJSAMELABNE}{%d/%d}" % (lab["same"]["not_established"], lab["same"]["n"]), r"\newcommand{\REFADJOTHERLABNE}{%d/%d}" % (lab["other"]["not_established"], lab["other"]["n"]),
         r"\newcommand{\REFADJSPLITTYPES}{%s}" % ", ".join(f"{WORDS.get(k, str(k))} {typ.replace('_', '-')}" for typ, k in cons["split_types"].items()),
         r"\newcommand{\REFADJSPLITTEXTS}{%d}" % len(cons["split_texts"]),
         r"\newcommand{\REFADJSTRICTER}{%s}" % _stricter_phrase(cons["stricter_on_splits"], cn["split"]),
         r"\newcommand{\REFADJWORDINGN}{%d}" % wo["n"], r"\newcommand{\REFADJWORDINGCHANGED}{%d}" % wo["changed"],
         r"\newcommand{\REFADJWORDINGCHANGEDAW}{%d}" % wo["changed_collapsed"]["AW"], r"\newcommand{\REFADJWORDINGCHANGEDRT}{%d}" % wo["changed_collapsed"]["RT"],
         r"\newcommand{\REFADJOBLN}{%d}" % obl["n_obligations"], r"\newcommand{\REFADJOBLTEXTS}{%d}" % obl["n_texts"],
         r"\newcommand{\REFADJOBLNOTESTAW}{%d}" % obl["by_category"]["AW"]["not_established"], r"\newcommand{\REFADJOBLNOTESTRT}{%d}" % obl["by_category"]["RT"]["not_established"],
         r"\newcommand{\REFADJOBLUNRESAW}{%d}" % obl["by_category"]["AW"]["unresolved"], r"\newcommand{\REFADJOBLUNRESRT}{%d}" % obl["by_category"]["RT"]["unresolved"],
         r"\newcommand{\REFADJOBLMIXED}{%s}" % _same_or_both(obl["by_category"]["AW"]["mixed"], obl["by_category"]["RT"]["mixed"]),
         r"\newcommand{\REFADJOBLNOOBJ}{%s}" % _same_or_both(obl["by_category"]["AW"]["no_objection"], obl["by_category"]["RT"]["no_objection"]),
         r"\newcommand{\REFADJOBLEST}{%s}" % _same_or_both(obl["by_category"]["AW"]["established"], obl["by_category"]["RT"]["established"]),
         r"\newcommand{\REFADJANCHELSE}{%d/%d}" % (s1["anchored"], s1["n"]), r"\newcommand{\REFADJANCHRATE}{%d/%d}" % (s2["total"]["anchored"], s2["total"]["positive"]),
         r"\newcommand{\REFADJANCHRATER}{%s}" % ", ".join(f"{NAMES[r]} {s2[r]['anchored']}/{s2[r]['positive']}" for r in NAMES),
         r"\newcommand{\REFADJANCHFULLTOP}{%s}" % ", ".join(f"{NAMES[r]} {s2[r]['S_ref_2_fully_anchored']}/{s2[r]['S_ref_2']}" for r in NAMES),
         r"\newcommand{\REFADJDISPUTES}{%d}" % len(results["disputes"]),
         r"\newcommand{\REFADJDISPFAILAW}{%d/%d}" % (len(dp["AW"]["fail"]), len(results["disputes"])), r"\newcommand{\REFADJDISPFAILRT}{%d/%d}" % (len(dp["RT"]["fail"]), len(results["disputes"])),
         r"\newcommand{\REFADJDISPFAILRTSTRICT}{%d/%d}" % (len(dp["RT_strict"]["fail"]), len(results["disputes"])),
         r"\newcommand{\REFADJDISPUNRESAW}{%s}" % tex(_join_and([pt[c]["name"] for c in dp["AW"]["unresolved"]])), r"\newcommand{\REFADJDISPUNRESRT}{%s}" % tex(_join_and([pt[c]["name"] for c in dp["RT"]["unresolved"]])),
         r"\newcommand{\REFADJDISPMIXED}{%s}" % tex(_join_and([pt[c]["name"] for c in obl["texts_with_mixed"]["RT"]])),
         r"\newcommand{\REFADJRATINGS}{%s}" % ", ".join(f"{NAMES[r]} {cov[r]}/20" for r in NAMES),
         r"\newcommand{\REFADJRATEAGREEAW}{%s}" % ", ".join(f"{NAMES[r]} {rvo[r]['match_AW']}/{rvo[r]['n']}" for r in NAMES),
         r"\newcommand{\REFADJRATEAGREERT}{%s}" % ", ".join(f"{NAMES[r]} {rvo[r]['match_RT']}/{rvo[r]['n']}" for r in NAMES),
         r"\newcommand{\REFADJRATEWITHINAW}{%s}" % ", ".join(f"{NAMES[r]} {rvo[r]['within_AW']}/{rvo[r]['n']}" for r in NAMES),
         r"\newcommand{\REFADJRATEWITHINRT}{%s}" % ", ".join(f"{NAMES[r]} {rvo[r]['within_RT']}/{rvo[r]['n']}" for r in NAMES),
         r"\newcommand{\REFADJTABLE}{\input{artifacts/reference_adjudication/table_refadj.tex}}",
         r"\newcommand{\REFADJDISPUTETABLE}{\input{artifacts/reference_adjudication/table_refadj_disputes.tex}}",
         r"\newcommand{\REFADJLEDGERTXT}{%s}" % _ledger_sentence(lv)]
    gen = root / "gen"
    (gen / "refadj_macros.tex" if gen.exists() else ra / "refadj_macros.tex").write_text("\n".join(m) + "\n")

def _same_or_both(a, b): return str(a) if a == b else f"AW {a} / RT {b}"

def _stricter_phrase(stricter, n_split):
    order = sorted(stricter.items(), key=lambda kv: -kv[1])
    return f"{NAMES[order[0][0]]} on {WORDS.get(order[0][1], str(order[0][1]))} of the {WORDS.get(n_split, str(n_split))} splits and {NAMES[order[1][0]]} on {WORDS.get(order[1][1], str(order[1][1]))}"

def _ledger_sentence(lv):
    base = (r"All stage-1 and stage-2 judgments used ledger v1: every request reproduces the statement list generated from \texttt{LEDGER.md}, which itself also records provenance and cross-checks; \texttt{LEDGER\_v2.md} records two literal corrections "
            r"(L6.1 restricted to $x \geq a_1$; L3.2 requiring two distinct disjoint subsets) and tags each statement as a route-independent requirement or a mechanism of the reference route; "
            r"no judgment was re-run")
    one_l61 = len(lv["L6.1_objections"]) == 1 and lv["L6.1_objections"][0]["case"] == "p6-kimi-k3-round1-t021" and lv["L6.1_objections"][0]["adjudicated"] == "not_established"
    if lv["no_scored_outcome_depends_on_corrections"] and one_l61:
        return base + (r", and no scored outcome depends on either correction: L6.1 is outside the scored obligations and its only objection concerns a text that supplies no argument for it at all, "
                       r"and none of the %d L3.2 objections concerns an empty pair." % lv["L3.2_objections"])
    if lv["no_scored_outcome_depends_on_corrections"]: return base + r", and no scored outcome depends on either correction (L6.1 is outside the scored obligations; no L3.2 objection concerns an empty pair)."
    return base + r"; WARNING: the mechanical check that no scored outcome depends on the corrections did not pass, see results.json ledger\_version."

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("jobs")
    c = sub.add_parser("check"); c.add_argument("--checker", choices=["gpt", "claude"], required=True); c.add_argument("--workers", type=int, default=5); c.add_argument("--timeout", type=int, default=2400); c.add_argument("--only", default=None); c.add_argument("--redo", action="store_true"); c.add_argument("--key-file", default="~/.config/vexorium/glm_api_key")
    r = sub.add_parser("rate"); r.add_argument("--rater", choices=["gpt", "claude", "glm"], required=True); r.add_argument("--workers", type=int, default=5); r.add_argument("--timeout", type=int, default=2400); r.add_argument("--only", default=None); r.add_argument("--redo", action="store_true"); r.add_argument("--key-file", default="~/.config/vexorium/glm_api_key")
    a = sub.add_parser("analyze"); a.add_argument("--root", default=None); a.add_argument("--freeze", action="store_true")
    args = ap.parse_args()
    if args.cmd == "jobs":
        obs = objections(); print(len(obs)); [print(o["key"], o["problem"]) for o in obs[:5]]; return 0
    return {"check": cmd_check, "rate": cmd_rate, "analyze": cmd_analyze}[args.cmd](args)

if __name__ == "__main__": sys.exit(main())
