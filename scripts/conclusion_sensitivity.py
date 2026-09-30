#!/usr/bin/env python3
"""Conclusion sensitivity under evaluator replay (offline, stdlib only, no model calls).

For every applicable lineage (P2: the two synthetic-route lineages only; route-N/A lineages are excluded from
every count) three trajectory conclusions are read off an S sequence: improved (last S > first S), regressed
(some adjacent decrease), first crossing (index of the first S=2, or none).  The REFERENCE layer is the
defect-corrected layer (key `valid` in labels.json: the written GLM-and-Kimi layer with the correction entries of
validity_overrides.json applied).  It is an author-maintained, partly model-derived corrected reference, so every
'survival' below is agreement with that reference, not out-of-sample accuracy.

The script asks (1) which conclusions survive a change of evaluator and a replay of the same evaluator, separates
(2) identical-text controls from different-text transitions, tests (3) whether more retained checkpoints create
more apparent progress under the replay null, compares (4) rating procedures and two no-model baselines on two
separate endpoints (improvement detection = strict S increase between the paired texts; endpoint acceptance =
later text rated S=2), states (5) the exact algebra of the same-defect control, tabulates (6) the sources of
instability, and (7) evaluates single-evaluator disagreement as an alarm.  The alarm's target is the CREDITED-DEFECTIVE text: a text
with a documented defect (a correction entry of validity_overrides.json, or a public final file whose released public verifier grade is a
failing grade <= 4/7, whatever the grader's model or wording) that at least one evaluator nevertheless rates S=2; a documented-defective
text every evaluator rates S<2 is visible to an operator without an alarm.  Item 7 reports the credited-defective coverage, the coverage
of every documented-defective text (misses named with their S profile), the flags on texts without any record (unexamined, not known
negatives), the distinct defects, and the sensitivity of the alarm to the evaluator pair, triple and full set.

Two same-model rating pools are replayed side by side.  GLM-5.3 = re-rating + completed repeats of the ADAPTIVE
thinking-then-fallback workflow (attempt 0 with thinking; attempt 1 without thinking when attempt 0 yields no
parsable output; the fallback is read from each annotation's `attempts`: attempt index 1 parsed).  Claude Opus 5 =
re-rating + three repeats at one fixed setting.  Same-text disagreement q is therefore reported separately for
fixed-setting pairs (both ratings under the same thinking mode) and for mixed-mode pairs; GLM's disagreement is
never described as fixed-setting stochastic variation.  Replay distributions are enumerated EXACTLY (each distinct
text's S is drawn from its pool; a text with fewer than two ratings in a pool is not 'covered' by that pool).  A
B-replay Monte Carlo cross-check is kept only to show that B controls Monte Carlo precision, not evidence.

Inputs (read only)
  artifacts/closure_matrix/matrix.json                            checkpoint order per lineage, route_na
  artifacts/closure{,_deedy,_p6,_p2}/*/annotation.json            layer 0: one GLM-5.3 rating per checkpoint
  artifacts/closure_glm_rerun/p*/, closure_kimi/p*/, closure_claude/p*/, closure_gpt/p*/   single evaluators, one rating per distinct text
  artifacts/closure_repeat/p{3,6}/rep{1,2,3}/                     GLM-5.3 repeats (same workflow as the re-rating)
  artifacts/closure_repeat_claude/p{3,6}/rep{1,2,3}/              Claude Opus 5 repeats (same setting as its re-rating)
  artifacts/closure_adjudicated/{labels,validity_overrides,reliability}.json   written/majority3/defect-corrected layers; correction entries; kappas
  artifacts/closure_analysis/grade_sources/public_problem03.json  released copy of the public grader's P3 receipt (per-model score and justification)
  artifacts/closure_matrix/public_grades.json                     released public grades (first pass and final) per problem and model; used where no receipt exists (P6)
  artifacts/baseline_{glm,claude}/p6/                             ordinary coordinator-style grades (same-defect note only)
  artifacts/pilot_critique/{p3-high-*/output.md,grades_*/p3,gate_glm53}       positive set (c)
Outputs (the only files written)
  artifacts/conclusion_sensitivity/{results.json,table_survival.tex,table_remedies.tex,table_sources.tex,table_evaluators.tex,table_alarm.tex,table_alarm_pairs.tex}
  gen/sensitivity_macros.tex   (newcommand definitions, no digits in macro names; main.tex loads the file with InputIfFileExists; written only when
                                <root>/gen exists or <root> is the repository, never created inside a flat bundle)
Usage: python3 scripts/conclusion_sensitivity.py [--root DIR] [--replays 1000] [--seed 20260906] [--evaluators raw,glm,kimi,claude,gpt,rep1,...]
  --root accepts the repository root (artifacts under <root>/artifacts) or a flat supplementary bundle (the artifact directories at the top level
  of <root>, as scripts/supplementary.py lays them out): the layout is detected from <root>/artifacts/closure_adjudicated.
Idempotent: outputs are fully regenerated on every run; re-run as repeats arrive.
"""
from __future__ import annotations
import argparse, hashlib, json, random, re, time
from collections import Counter, defaultdict
from itertools import combinations, product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBS = ("3", "6", "2")
RAW_DIRS = {"3": ("closure", "closure_deedy"), "6": ("closure_p6",), "2": ("closure_p2",)}
EVAL_DIRS = {"glm": "closure_glm_rerun", "kimi": "closure_kimi", "claude": "closure_claude", "gpt": "closure_gpt"}   # live, one rating per text
FOUR = ("glm", "kimi", "claude", "gpt")                     # the four single evaluators (gpt: P3/P6 only)
AGG = ("written", "majority3", "valid")                     # aggregation layers, from labels.json
REF, REF_NAME = "valid", "defect-corrected"                 # labels.json key of the reference layer, and its name in every table and macro
POOLS = {"glm": {"name": "GLM-5.3", "repeat_dir": "closure_repeat", "rep_layers": ("rep1", "rep2", "rep3"), "pilot_grades": "grades_glm",
                 "workflow": "adaptive thinking-then-fallback workflow (attempt 0 with thinking; attempt 1 without thinking when attempt 0 yields no parsable output)",
                 "modes": ("thinking", "no-thinking fallback")},
         "claude": {"name": "Claude Opus 5", "repeat_dir": "closure_repeat_claude", "rep_layers": ("crep1", "crep2", "crep3"), "pilot_grades": "grades_claude",
                    "workflow": "one fixed CLI setting, no fallback", "modes": ("fixed setting", "fixed setting")}}
REP_LAYERS = {L: (pn, i + 1) for pn, sp in POOLS.items() for i, L in enumerate(sp["rep_layers"])}
DEFAULT_EVALUATORS = ("raw",) + FOUR + tuple(REP_LAYERS)
CONCS = ("improved", "regressed", "crossing")
NO_MODEL = ("none", "constant2")                            # baselines that need no rating
PROCS = NO_MODEL + ("per_checkpoint", "cached", "majority3_text", "majority3_checkpoint")
PROC_LABEL = {"none": "no rating (abstain everywhere; no model)", "constant2": "constant S=2 everywhere (no model)", "per_checkpoint": "(i) one rating per checkpoint",
              "cached": "(ii) one rating per distinct text (caching)", "majority3_text": "(iii) majority of three per text",
              "majority3_checkpoint": "(iv) majority of three per checkpoint (cost comparator for (iii))"}
TABLE_LABEL = {"none": "no rating (abstain; no model)", "constant2": "constant $S{=}2$ (no model)", "per_checkpoint": "(i) one per checkpoint", "cached": "(ii) one per text (caching)",
               "majority3_text": "(iii) majority of three per text", "majority3_checkpoint": "(iv) majority of three per checkpoint"}
EVAL_SHORT = {"raw": "layer~0", "glm": "GLM", "kimi": "Kimi", "claude": "Claude", "gpt": "GPT", "written": "written", "majority3": "majority of three", "valid": REF_NAME,
              "rep1": "GLM repeat~1", "rep2": "GLM repeat~2", "rep3": "GLM repeat~3", "crep1": "Claude repeat~1", "crep2": "Claude repeat~2", "crep3": "Claude repeat~3"}
MIN_COVERED = 3          # a replay cell needs at least this many fully covered lineages / pairs, else "--"
ANN_PLAIN = {"glm-5.3": "GLM-5.3 re-rating", "kimi-k3": "Kimi K3", "claude-opus-5": "Claude Opus 5", "gpt-5.6-sol": "GPT-5.6-Sol"}   # annotator id -> plain name (results.json strings)
PILOT_ROUTES = ("p3-high-C-r1", "p3-high-C-r2", "p3-high-N-r1", "p3-high-N-r2")
# Independently supported improvements: (problem, before checkpoint id, after checkpoint id | pilot:<route>, note)
POSITIVE = [("3", "kimi-k3-round4-t014", "deedy-kimi-k3-final", "public Kimi P3: verifier first pass 5/7 -> re-grade 7/7"),
            ("6", "p6-kimi-k3-round3-t009", "p6-kimi-k3-main-t005", "public Kimi P6: 3/7 -> main session (finiteness crux closed)"),
            ("6", "p6-kimi-k3-round3-t009", "p6-deedy-kimi-k3-final", "public Kimi P6: 3/7 -> final file (re-grade 7/7)")]
POSITIVE += [("3", "kimi-r1-c3", f"pilot:{r}", f"our P3 repair: seed 6/7 -> gate-passed pilot output {r}") for r in PILOT_ROUTES]
DEFECT_PAIR = ("6", "p6-gpt-5.6-sol-main-t009", "p6-deedy-gpt-5.6-sol-final")   # same false lemma, verifier 1/7
SAME_DEFECT = (DEFECT_PAIR,)          # texts known to carry one and the same defect: counted once among the distinct defects of the alarm analysis
# Alarm analysis (item 7): systematic ascertainment of DOCUMENTED-DEFECTIVE texts = (a) every correction entry of validity_overrides.json plus
# (b) every public final file of an applicable lineage whose released public verifier grade is <= PUBLIC_FAIL_MAX (a failing grade), whatever
# the grader's model or wording.  The grade comes from the released receipt where one exists (P3), else from the released grade table.
PUBLIC_FAIL_MAX = 4
PUBLIC_RECEIPTS = {"3": "closure_analysis/grade_sources/public_problem03.json"}    # per-model entries {model, score, justification, ...}
PUBLIC_GRADES = "closure_matrix/public_grades.json"                                 # {"first_pass": {prob: {model: grade}}, "final": {prob: {model: grade}}}
ALARM_EVALS = FOUR + ("rep1",)        # the evaluators the alarm uses: the four single evaluators plus the GLM-5.3 repeat rep1 where present
ALARM_PAIRS = (("glm", "kimi"), ("glm", "claude"), ("glm", "gpt"), ("kimi", "claude"), ("kimi", "gpt"), ("claude", "gpt"), ("glm", "rep1"))
ALARM_TRIPLES = tuple(combinations(FOUR, 3))
BASELINE_DIRS = {"glm": "baseline_glm", "claude": "baseline_claude"}     # ordinary coordinator-style grades, read for the same-defect note only
KAPPA_KEYS = {"GLM-Kimi": "kappa_S_glm_rerun_vs_kimi", "GLM-Claude": "kappa_S_glm_vs_claude", "Kimi-Claude": "kappa_S_kimi_vs_claude", "GLM-GPT": "kappa_S_glm_vs_gpt"}
KAPPA_PAIRS = {"GLM-Kimi": ("glm", "kimi"), "GLM-Claude": ("glm", "claude"), "Kimi-Claude": ("kimi", "claude"), "GLM-GPT": ("glm", "gpt")}


# ----------------------------------------------------------------------------- helpers
def load(p):
    try: return json.loads(Path(p).read_text())
    except (OSError, ValueError): return None

def fields(a):
    if not a or a.get("S") is None: return None
    g = a.get("grades") or {}
    try: return (int(g["lower_bound"]), int(g["upper_bound"]))
    except (KeyError, TypeError, ValueError): return None

def S_of(f): return None if f is None else sum(x == 2 for x in f)
def is_fallback(a): return any(t.get("attempt") == 1 and t.get("parsed") for t in (a or {}).get("attempts", []))   # attempt 1 parsed => no-thinking fallback
def mode_of(pn, a): return POOLS[pn]["modes"][1 if is_fallback(a) else 0]
def cls(a, b): return None if a is None or b is None else ("up" if b > a else "down" if b < a else "flat")
def gt(a, b): return a is not None and b is not None and b > a
def ne(a, b): return a is not None and b is not None and a != b
def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None
def fmt(x, nd=2): return "--" if x is None else f"{x:.{nd}f}"
def fnum(x, nd=1): return "--" if x is None else (str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.{nd}f}")
def pct(x, nd=1): return "--" if x is None else f"{fnum(100 * x, nd)}\\%"
def nword(n): return {0: "no", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}.get(n, str(n))
def esc(s): return str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
def yn(v): return "?" if v is None else ("yes" if v else "no")
def cross_txt(v): return "?" if v is None else ("none" if v == "none" else f"checkpoint {v + 1}")
def conc_txt(c, v): return cross_txt(v) if c == "crossing" else yn(v)
def r3(x): return None if x is None else round(x, 4)
def join_and(xs): xs = list(xs); return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]
def plural(n, w="s"): return w if n != 1 else ""
def n_sentences(t):
    t = re.sub(r"\$[^$]*\$", " M ", t)
    return len(re.findall(r"[.!?](?=\s+[A-Z(\\]|\s*$)", t))

def conclusions(seq):
    """improved / regressed / crossing from an S sequence with possible unknowns (None = abstention)."""
    first, last = seq[0], seq[-1]
    improved = None if (first is None or last is None) else (last > first)
    dec = any(a is not None and b is not None and b < a for a, b in zip(seq, seq[1:]))
    regressed = True if dec else (None if any(s is None for s in seq) else False)
    crossing = "none"
    for i, s in enumerate(seq):
        if s is None: crossing = None; break
        if s == 2: crossing = i; break
    return {"improved": improved, "regressed": regressed, "crossing": crossing}

def kappa(pairs, classes=(0, 1, 2)):
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    n = len(pairs)
    if not n: return {"n": 0, "observed": None, "kappa": None}
    po = sum(a == b for a, b in pairs) / n
    pa, pb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(pa[c] * pb[c] for c in classes) / (n * n)
    return {"n": n, "observed": round(po, 3), "kappa": None if pe == 1 else round((po - pe) / (1 - pe), 3)}

def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0] * len(xs); i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]: j += 1
        for t in range(i, j + 1): r[order[t]] = (i + j) / 2 + 1
        i = j + 1
    return r

def pearson(x, y):
    n = len(x); mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x); syy = sum((b - my) ** 2 for b in y)
    return None if sxx == 0 or syy == 0 else sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sxx * syy) ** 0.5

def spearman_perm(x, y, rng, n_perm=10000):
    rx, ry = ranks(x), ranks(y); rho = pearson(rx, ry)
    if rho is None: return None, None
    cnt = 0; ry2 = list(ry)
    for _ in range(n_perm):
        rng.shuffle(ry2); r = pearson(rx, ry2)
        if r is not None and abs(r) >= abs(rho) - 1e-12: cnt += 1
    return round(rho, 3), round((cnt + 1) / (n_perm + 1), 4)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--replays", type=int, default=1000, help="Monte Carlo cross-check replays per lineage (0 = skip); every reported number is an exact enumeration")
    ap.add_argument("--seed", type=int, default=20260906)
    ap.add_argument("--root", type=Path, default=ROOT, help="repository root (artifacts under <root>/artifacts) or a flat supplementary bundle (artifact directories at the top level)")
    ap.add_argument("--evaluators", default=",".join(DEFAULT_EVALUATORS),
                    help="single-evaluator layers: raw (layer 0, per checkpoint), glm/kimi/claude/gpt (live directories), rep1-3 (GLM repeats), crep1-3 (Claude repeats)")
    args = ap.parse_args()
    B, root = args.replays, args.root.resolve()
    # layout detection: repository (<root>/artifacts/...) or flat bundle (<root>/closure_adjudicated/... as scripts/supplementary.py lays it out)
    art = root / "artifacts" if (root / "artifacts" / "closure_adjudicated").is_dir() else root
    if not (art / "closure_adjudicated").is_dir(): raise SystemExit(f"{root}: neither <root>/artifacts/closure_adjudicated nor <root>/closure_adjudicated exists")
    bundle = art == root
    out = art / "conclusion_sensitivity"
    gen = root / "gen" if (not bundle or (root / "gen").is_dir()) else None    # macros: repository always; a bundle only if it already has gen/
    rng = random.Random(args.seed)
    single = tuple(x for x in args.evaluators.split(",") if x)
    if "raw" not in single or "glm" not in single: raise SystemExit("--evaluators must include raw and glm")
    t0 = time.time(); problems = []     # data problems found (reported, never fixed)

    # ---- layer 0: one rating per checkpoint -------------------------------------------------------------
    ck, rubric0 = {}, {}
    for prob, dirs in RAW_DIRS.items():
        for d in dirs:
            for f in sorted((art / d).glob("*/annotation.json")):
                a = load(f)
                if not a: problems.append(f"unreadable layer-0 record {f.relative_to(root)}"); continue
                fl = fields(a)
                if fl is None: problems.append(f"layer-0 record without parsed grades: {a.get('id')}")
                elif a.get("S") != S_of(fl): problems.append(f"layer-0 stored S != fields for {a['id']}")
                ck[(prob, a["id"])] = {"sha": a["sha256"], "S": S_of(fl), "fields": fl, "lineage": a.get("lineage")}
                rubric0.setdefault(prob, set()).add(a.get("rubric_sha256"))
    for prob, rs in rubric0.items():
        if len(rs) > 1: problems.append(f"P{prob}: several layer-0 rubric hashes {sorted(rs)}")

    # ---- lineages (order and route policy from matrix.json) -----------------------------------------------
    M = load(art / "closure_matrix" / "matrix.json") or {"lineages": []}
    lins = []
    for l in M["lineages"]:
        ids = [c["id"] for c in l["S_sequence"]]
        miss = [i for i in ids if (l["problem"], i) not in ck]
        if miss: problems.append(f"P{l['problem']} {l['lineage']}: checkpoints without layer-0 record {miss}"); continue
        shas = [ck[(l["problem"], i)]["sha"] for i in ids]
        lins.append({"problem": l["problem"], "lineage": l["lineage"], "source": l["source"], "route_na": l.get("route_na"),
                     "applicable": l.get("route_na") is None, "ids": ids, "labels": [c.get("label") or c["id"] for c in l["S_sequence"]], "shas": shas,
                     "k": len(ids), "d": len(set(shas)), "S_matrix": [c["S"] for c in l["S_sequence"]], "grade_for_agreement": l.get("grade_for_agreement"),
                     "S_final_matrix": l.get("S_final")})
    app = [l for l in lins if l["applicable"]]

    # ---- labels (written / majority3 / defect-corrected), correction entries, reliability -------------------
    labels = load(art / "closure_adjudicated" / "labels.json") or []
    lab = {(r["problem"], r["sha256"]): r for r in labels}
    for l in lins:
        for i, s in zip(l["ids"], l["shas"]):
            if (l["problem"], s) not in lab: problems.append(f"P{l['problem']} {i}: text {s[:12]} has no labels.json record")
        if all((l["problem"], s) in lab for s in l["shas"]):
            v = [lab[(l["problem"], s)]["S"][REF] for s in l["shas"]]
            if v != l["S_matrix"]: problems.append(f"P{l['problem']} {l['lineage']}: matrix.json S != labels.json {REF_NAME} S")
    overrides = {k: v for k, v in (load(art / "closure_adjudicated" / "validity_overrides.json") or {}).items() if not k.startswith("_")}
    rel = load(art / "closure_adjudicated" / "reliability.json") or {}

    # ---- single evaluators (live) and same-model pools --------------------------------------------------------
    live_S, live_F, live_annot = {e: {} for e in FOUR}, {e: {} for e in FOUR}, {}
    pool = {pn: defaultdict(list) for pn in POOLS}; rerun_fb = {pn: Counter() for pn in POOLS}
    def add_rating(pn, key, fl, src, a): pool[pn][key].append({"S": S_of(fl), "f": list(fl), "src": src, "fallback": is_fallback(a), "mode": mode_of(pn, a)})
    for e, d in EVAL_DIRS.items():
        for prob in PROBS:
            for f in sorted((art / d / f"p{prob}").glob("*/annotation.json")):
                a = load(f); fl = fields(a)
                if fl is None: problems.append(f"{e} rating without parsed grades: {d}/p{prob}/{f.parent.name}"); continue
                key = (prob, a["sha256"]); live_S[e][key] = S_of(fl); live_F[e][key] = fl; live_annot.setdefault(e, a.get("annotator"))
                if a.get("rubric_sha256") not in rubric0.get(prob, set()): problems.append(f"{e} rubric differs from layer 0: {f.parent.name}")
                if e in POOLS: add_rating(e, key, fl, e, a); rerun_fb[e][prob] += is_fallback(a)
    for key, r in lab.items():
        for e in FOUR:
            if key in live_S[e] and r["S"].get(e) != live_S[e][key]: problems.append(f"labels.json {e} S ({r['S'].get(e)}) != live {e} record ({live_S[e][key]}) for P{key[0]} {key[1][:12]} -- labels.json stale?")
        if key not in live_S["glm"]: problems.append(f"P{key[0]} text {key[1][:12]}: no GLM re-rating")
    rep_S, rep_F, rep_files = {L: {} for L in REP_LAYERS}, {L: {} for L in REP_LAYERS}, {}
    for L, (pn, i) in REP_LAYERS.items():
        for prob in ("3", "6"):
            base = art / POOLS[pn]["repeat_dir"] / f"p{prob}" / f"rep{i}"; st = {"dirs": 0, "parsed": 0, "pending": 0, "unparsed": 0, "fallback": 0}
            for sub in sorted(base.iterdir()) if base.is_dir() else []:
                if not sub.is_dir(): continue
                st["dirs"] += 1
                if not (sub / "annotation.json").exists(): st["pending"] += 1; continue
                a = load(sub / "annotation.json"); fl = fields(a)
                if fl is None: st["unparsed"] += 1; problems.append(f"{L} P{prob} {sub.name}: unreadable or unparsed (in progress?)"); continue
                key = (prob, a["sha256"]); st["parsed"] += 1; st["fallback"] += is_fallback(a)
                if key in rep_S[L]: problems.append(f"{L} P{prob}: two records for text {key[1][:12]}"); continue
                if a.get("rubric_sha256") not in rubric0.get(prob, set()): problems.append(f"{L} P{prob} {sub.name}: rubric differs from layer 0")
                rep_S[L][key] = S_of(fl); rep_F[L][key] = fl; add_rating(pn, key, fl, L, a)
            rep_files[f"{pn}/p{prob}/rep{i}"] = st
    completion = {pn: {"name": POOLS[pn]["name"], "workflow": POOLS[pn]["workflow"],
                       "repeat_ratings_parsed": {f"P{prob}": {f"rep{i}": rep_files[f"{pn}/p{prob}/rep{i}"]["parsed"] for i in (1, 2, 3)} for prob in ("3", "6")}} for pn in POOLS}
    for pn in POOLS:
        completion[pn]["repeat_ratings_total"] = sum(v for p in completion[pn]["repeat_ratings_parsed"].values() for v in p.values())
        completion[pn]["repeat_passes_with_any_rating"] = sorted({k for p in completion[pn]["repeat_ratings_parsed"].values() for k, v in p.items() if v})
    # positive set (c): four pilot outputs; each pool uses the grade of its own model where one exists
    pilot = {}
    for route in PILOT_ROUTES:
        p = art / "pilot_critique" / route / "output.md"
        if not p.exists(): problems.append(f"pilot output missing: {route}"); continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        meta = load(art / "pilot_critique" / "gate_glm53" / f"{route}-p3" / "meta.json") or {}
        if meta.get("candidate_sha256") != h: problems.append(f"pilot gate meta sha mismatch for {route}")
        rec = {"sha256": h, "gate_pass": bool(meta.get("passes_gate")), "gate_verdict": meta.get("verdict"), "grades": {}}
        for pn, sp in POOLS.items():
            g = load(art / "pilot_critique" / sp["pilot_grades"] / "p3" / f"pilot-{h[:12]}" / "annotation.json"); gf = fields(g)
            if g and g.get("sha256") != h: problems.append(f"pilot grade sha mismatch for {route} ({pn})")
            rec["grades"][pn] = S_of(gf)
            if gf is not None: add_rating(pn, ("3", h), gf, "pilot grade", g)
        kk = load(art / "pilot_critique" / "grades_kimi" / "p3" / f"pilot-{h[:12]}" / "annotation.json"); rec["grades"]["kimi"] = S_of(fields(kk))
        pilot[f"pilot:{route}"] = rec
    def sha_of(prob, ident): return pilot[ident]["sha256"] if ident.startswith("pilot:") else ck[(prob, ident)]["sha"]
    def poolS(pn, prob, sha): return [r["S"] for r in pool[pn][(prob, sha)]]
    def covered(pn, prob, sha): return len(pool[pn][(prob, sha)]) >= 2
    def rids(prob, sha): return (lab.get((prob, sha)) or {}).get("record_ids") or [sha[:12]]

    # ---- coverage ------------------------------------------------------------------------------------------
    coverage = {}
    for prob in PROBS:
        appt = sorted({s for l in app if l["problem"] == prob for s in l["shas"]})
        coverage[prob] = {"lineages": sum(l["problem"] == prob for l in lins), "lineages_applicable": sum(l["problem"] == prob for l in app),
                          "checkpoints_applicable": sum(l["k"] for l in app if l["problem"] == prob), "distinct_texts_applicable": len(appt),
                          "single_evaluator_ratings": {e: sum((prob, s) in live_S[e] for s in appt) for e in FOUR},
                          "pools": {pn: {"texts_with_2plus_ratings": sum(covered(pn, prob, s) for s in appt), "texts_with_3plus_ratings": sum(len(pool[pn][(prob, s)]) >= 3 for s in appt),
                                         "texts_with_4_ratings": sum(len(pool[pn][(prob, s)]) >= 4 for s in appt), "rerun_fallbacks": rerun_fb[pn][prob],
                                         "repeat_files": {k: v for k, v in rep_files.items() if k.startswith(f"{pn}/p{prob}/")}} for pn in POOLS}}

    # ---- q per pool: same-text disagreement, split by thinking mode of the two ratings ------------------------
    def q_stats(pn, keys, min_ratings=2):
        st = Counter(); var = []; draw_dis = []
        for key in keys:
            p = pool[pn][key]
            if len(p) < min_ratings: continue
            st["texts"] += 1; st["texts_all_equal_S"] += len({r["S"] for r in p}) == 1
            n = len(p); draw_dis.append(1 - sum((v / n) ** 2 for v in Counter(r["S"] for r in p).values()))
            if len({r["S"] for r in p}) > 1:
                var.append({"problem": key[0], "sha": key[1][:12], "record_ids": rids(*key), "ratings": [{"src": r["src"], "S": r["S"], "mode": r["mode"]} for r in p],
                            "modes_differ": len({r["mode"] for r in p}) > 1})
            for a, b in combinations(p, 2):
                fixed = a["fallback"] == b["fallback"]; kind = "fixed_primary" if fixed and not a["fallback"] else "fixed_fallback" if fixed else "mixed"; dif = a["S"] != b["S"]
                st["pairs"] += 1; st["pairs_differ"] += dif; st[f"{kind}_pairs"] += 1; st[f"{kind}_differ"] += dif; st["fixed_pairs"] += fixed; st["fixed_differ"] += fixed and dif
                st["pairs_lower_differ"] += a["f"][0] != b["f"][0]; st["pairs_upper_differ"] += a["f"][1] != b["f"][1]
                if fixed: st["fixed_lower_differ"] += a["f"][0] != b["f"][0]; st["fixed_upper_differ"] += a["f"][1] != b["f"][1]
        o = {k: st[k] for k in ("texts", "texts_all_equal_S", "pairs", "pairs_differ", "fixed_pairs", "fixed_differ", "fixed_primary_pairs", "fixed_primary_differ", "fixed_fallback_pairs",
                                "fixed_fallback_differ", "mixed_pairs", "mixed_differ", "pairs_lower_differ", "pairs_upper_differ", "fixed_lower_differ", "fixed_upper_differ")}
        rat = lambda a, b: r3(o[a] / o[b]) if o[b] else None
        o.update({"q": rat("pairs_differ", "pairs"), "q_fixed": rat("fixed_differ", "fixed_pairs"), "q_fixed_primary": rat("fixed_primary_differ", "fixed_primary_pairs"),
                  "q_mixed": rat("mixed_differ", "mixed_pairs"), "q_lower": rat("pairs_lower_differ", "pairs"), "q_upper": rat("pairs_upper_differ", "pairs"),
                  "q_lower_fixed": rat("fixed_lower_differ", "fixed_pairs"), "q_upper_fixed": rat("fixed_upper_differ", "fixed_pairs"),
                  "draw_disagreement_mean": r3(mean(draw_dis)) if draw_dis else None, "variable_texts": var})
        return o
    text_keys = {prob: sorted({(prob, s) for l in app if l["problem"] == prob for s in l["shas"]}) for prob in PROBS}
    q = {pn: {"3": q_stats(pn, text_keys["3"]), "6": q_stats(pn, text_keys["6"]), "pooled": q_stats(pn, text_keys["3"] + text_keys["6"]),
              "pooled_3plus_ratings": q_stats(pn, text_keys["3"] + text_keys["6"], 3)} for pn in POOLS}
    q["definition"] = {"q": "pairwise disagreement of S between two same-model ratings of the same text (re-rating and repeats), every unordered pair counted once; for GLM-5.3 this is the "
                            "disagreement of the adaptive thinking-then-fallback workflow as run, NOT fixed-setting variation",
                       "q_fixed": "the same over fixed-setting pairs only (both ratings under the same thinking mode: thinking-thinking or fallback-fallback; every Claude pair is fixed-setting)",
                       "q_fixed_primary": "fixed-setting pairs whose two ratings are both primary (thinking) successes", "q_mixed": "pairs of one thinking success and one no-thinking fallback",
                       "draw_disagreement_mean": "mean over covered texts of 1 - sum_v p_v^2: the probability that two independent WITH-REPLACEMENT draws from the text's pool differ, "
                                                 "which is what the replay uses (a text with 2 ratings gives q/2 of its pairwise value, 4 ratings 3q/4)",
                       "scope": "texts of applicable lineages; texts with fewer than 2 ratings contribute nothing; P2 has no repeats by protocol"}
    Q = {pn: q[pn]["pooled"]["q"] for pn in POOLS}; QF = {pn: q[pn]["pooled"]["q_fixed"] for pn in POOLS}; QD = {pn: q[pn]["pooled"]["draw_disagreement_mean"] for pn in POOLS}

    # ---- exact replay machinery -------------------------------------------------------------------------------
    def dist_S(pn, prob, sha):
        p = poolS(pn, prob, sha)
        if not p: return {None: 1.0}
        return {v: k / len(p) for v, k in sorted(Counter(p).items())}
    def dist_maj3(d):
        o = defaultdict(float); items = list(d.items())
        for (a, pa), (b, pb), (c, pc) in product(items, repeat=3):
            cnt = Counter((a, b, c)).most_common(); o[cnt[0][0] if cnt[0][1] >= 2 else None] += pa * pb * pc
        return dict(o)
    def proc_dists(pn, proc, prob):
        """per-text single-draw distribution for a procedure, and whether one draw is shared by every checkpoint of a text (caching)."""
        if proc == "none": return (lambda s: {None: 1.0}), True
        if proc == "constant2": return (lambda s: {2: 1.0}), True
        if proc in ("per_checkpoint", "cached"): return (lambda s: dist_S(pn, prob, s)), proc == "cached"
        return (lambda s: dist_maj3(dist_S(pn, prob, s))), proc == "majority3_text"
    def enum_seqs(shas, dfn, cache):
        keys = list(dict.fromkeys(shas)) if cache else list(shas)
        for combo in product(*[list(dfn(s).items()) for s in keys]):
            w = 1.0
            for _, p in combo: w *= p
            vals = [v for v, _ in combo]
            if cache: m = dict(zip(keys, vals)); vals = [m[s] for s in shas]
            yield vals, w
    def conc_dist(shas, dfn, cache):
        o = {c: defaultdict(float) for c in CONCS}
        for sq, w in enum_seqs(shas, dfn, cache):
            cc = conclusions(sq)
            for c in CONCS: o[c][cc[c]] += w
        return o
    def stab(d): return sum(v * v for v in d.values())
    # Monte Carlo cross-check (B replays; adds precision, never evidence)
    def pick(p): return rng.choice(p)["S"] if p else None
    def maj3(p):
        if not p: return None
        c = Counter(rng.choice(p)["S"] for _ in range(3)).most_common()
        return c[0][0] if c[0][1] >= 2 else None
    def draw(pn, proc, prob, shas):
        if proc == "per_checkpoint": return [pick(pool[pn][(prob, s)]) for s in shas]
        if proc == "majority3_checkpoint": return [maj3(pool[pn][(prob, s)]) for s in shas]
        f = pick if proc == "cached" else maj3
        m = {s: f(pool[pn][(prob, s)]) for s in dict.fromkeys(shas)}
        return [m[s] for s in shas]

    # ---- 1. conclusions under each evaluator, and under exact replay -------------------------------------------
    def seq_layer(l, layer):
        if layer == "raw": return [ck[(l["problem"], i)]["S"] for i in l["ids"]]
        if layer in REP_LAYERS: return [rep_S[layer].get((l["problem"], s)) for s in l["shas"]]
        if layer in FOUR: return [live_S[layer].get((l["problem"], s)) for s in l["shas"]]
        return [lab[(l["problem"], s)]["S"].get(layer) if (l["problem"], s) in lab else None for s in l["shas"]]
    ALL_LAYERS = tuple(dict.fromkeys(single + AGG))
    mc = {"replays": B, "seed": args.seed, "max_abs_diff_survival_text_vs_ref": 0.0, "max_abs_diff_p_apparent_up": 0.0,
          "note": "every reported number is an exact enumeration of the replay distribution; the Monte Carlo replays only check that enumeration and add no evaluator evidence"}
    for l in app:
        per = {}
        for L in ALL_LAYERS:
            sq = seq_layer(l, L)
            if any(s is None for s in sq): continue
            per[L] = {"seq": sq, **conclusions(sq)}
        if REF not in per or "glm" not in per: raise SystemExit(f"P{l['problem']} {l['lineage']}: {REF_NAME} or glm layer incomplete")
        used = [L for L in single if L in per]; four = [L for L in FOUR if L in per]
        l["layers"], l["evaluators_used"], l["four_used"] = per, used, four
        for c in CONCS:
            l[f"identical_{c}"] = len({json.dumps(per[L][c]) for L in used}) == 1
            l[f"identical_four_{c}"] = len({json.dumps(per[L][c]) for L in four}) == 1
            l[f"all_match_valid_{c}"] = all(per[L][c] == per[REF][c] for L in used)
        l["covered"] = {pn: all(covered(pn, l["problem"], s) for s in set(l["shas"])) for pn in POOLS}
        l["texts_covered"] = {pn: f"{sum(covered(pn, l['problem'], s) for s in set(l['shas']))}/{l['d']}" for pn in POOLS}
        l["pool_deterministic"] = {pn: all(len({r["S"] for r in pool[pn][(l["problem"], s)]}) <= 1 for s in set(l["shas"])) for pn in POOLS}
        l["survival"] = {}
        for pn in POOLS:
            own = pn if pn in per else "glm"; ex = {}
            for proc, tag in (("cached", "text"), ("per_checkpoint", "checkpoint")):
                dfn, cache = proc_dists(pn, proc, l["problem"]); cd = conc_dist(l["shas"], dfn, cache)
                ex[f"{tag}_vs_valid"] = {c: r3(cd[c].get(per[REF][c], 0.0)) for c in CONCS}
                if tag == "text":
                    ex["text_vs_own_rerating"] = {c: r3(cd[c].get(per[own][c], 0.0)) for c in CONCS}
                    ex["text_distribution"] = {c: {str(k): r3(v) for k, v in cd[c].items()} for c in CONCS}
            if B and l["covered"][pn]:
                cnt = {c: Counter() for c in CONCS}
                for _ in range(B):
                    cc = conclusions(draw(pn, "cached", l["problem"], l["shas"]))
                    for c in CONCS: cnt[c][cc[c]] += 1
                ex["mc_text_vs_valid"] = {c: cnt[c][per[REF][c]] / B for c in CONCS}
                mc["max_abs_diff_survival_text_vs_ref"] = max(mc["max_abs_diff_survival_text_vs_ref"], max(abs(ex["mc_text_vs_valid"][c] - ex["text_vs_valid"][c]) for c in CONCS))
            l["survival"][pn] = ex

    def surv_agg(ls, pn, key="text_vs_valid"):
        cov = [l for l in ls if l["covered"][pn]]
        return {c: (r3(mean([l["survival"][pn][key][c] for l in cov])) if len(cov) >= MIN_COVERED else None) for c in CONCS}
    def surv_min(ls, pn):
        cov = [l for l in ls if l["covered"][pn]]
        return {c: (r3(min(l["survival"][pn]["text_vs_valid"][c] for l in cov)) if cov else None) for c in CONCS}
    def prevalence(ls):
        return {"improved": sum(l["layers"][REF]["improved"] is True for l in ls), "regressed": sum(l["layers"][REF]["regressed"] is True for l in ls),
                "crossing": sum(l["layers"][REF]["crossing"] not in ("none", None) for l in ls)}
    survival = {"reference": {"key": REF, "name": REF_NAME, "definition": f"labels.json layer '{REF}': the written layer (a field counts 2 only if both GLM-5.3 and Kimi K3 score it 2, else the lower score) "
                                                                             f"with the {len(overrides)} correction entries of validity_overrides.json applied; author-maintained and partly model-derived, so "
                                                                             "survival = agreement with this reference, not out-of-sample accuracy", "n_correction_entries": len(overrides)},
                "per_problem": {}, "flips": [], "agree_but_not_valid": [], "evaluator_choice": {}, "fragile_lineages": {}}
    for prob in PROBS + ("all",):
        ls = [l for l in app if prob == "all" or l["problem"] == prob]; n = len(ls)
        survival["per_problem"][prob] = {
            "n_lineages": n, "reference_prevalence": prevalence(ls),
            "identical_across_evaluators": {c: sum(l[f"identical_{c}"] for l in ls) for c in CONCS},
            "identical_across_four_single_evaluators": {c: sum(l[f"identical_four_{c}"] for l in ls) for c in CONCS},
            "identical_and_equal_valid": {c: sum(l[f"identical_{c}"] and l[f"all_match_valid_{c}"] for l in ls) for c in CONCS},
            "replay": {pn: {"n_covered": sum(l["covered"][pn] for l in ls), "n_covered_deterministic_pool": sum(l["covered"][pn] and l["pool_deterministic"][pn] for l in ls),
                            "survival_text_vs_valid": surv_agg(ls, pn), "survival_text_vs_own_rerating": surv_agg(ls, pn, "text_vs_own_rerating"),
                            "survival_checkpoint_vs_valid": surv_agg(ls, pn, "checkpoint_vs_valid"), "min_survival_text_vs_valid": surv_min(ls, pn),
                            "lineages_with_survival_below_1": sum(l["covered"][pn] and min(l["survival"][pn]["text_vs_valid"].values()) < 1 for l in ls)} for pn in POOLS},
            "evaluator_layers_used": sorted(Counter(tuple(l["evaluators_used"]) for l in ls).items(), key=lambda kv: -kv[1])[:6]}
        survival["evaluator_choice"][prob] = {L: {c: {"equal_valid": sum(l["layers"][L][c] == l["layers"][REF][c] for l in ls if L in l["layers"]),
                                                      "evaluable": sum(L in l["layers"] for l in ls)} for c in CONCS} for L in ALL_LAYERS if L != REF}
    for pn in POOLS:
        survival["fragile_lineages"][pn] = [{"problem": l["problem"], "lineage": l["lineage"], "k": l["k"], "survival_text_vs_valid": l["survival"][pn]["text_vs_valid"],
                                             "reference": {c: l["layers"][REF][c] for c in CONCS}, "own_layer": {c: l["layers"][pn][c] for c in CONCS} if pn in l["layers"] else None,
                                             "pool_deterministic": l["pool_deterministic"][pn],
                                             "texts_where_pool_differs_from_reference": [{"id": i, "label": lb, "pool_S": poolS(pn, l["problem"], s), "reference_S": lab[(l["problem"], s)]["S"][REF]}
                                                                                         for j, (i, lb, s) in enumerate(zip(l["ids"], l["labels"], l["shas"])) if s not in l["shas"][:j]
                                                                                         and set(poolS(pn, l["problem"], s)) - {lab[(l["problem"], s)]["S"][REF]}]}
                                            for l in app if l["covered"][pn] and min(l["survival"][pn]["text_vs_valid"].values()) < 1]
    def votes(prob, sha): return {e: live_S[e].get((prob, sha)) for e in FOUR}
    def split_txt(v):
        groups = defaultdict(list)
        for e in FOUR:
            if v.get(e) is not None: groups[v[e]].append(EVAL_SHORT[e])
        parts = sorted(groups.items(), key=lambda kv: (-len(kv[1]), -kv[0]))
        tag = "-vs-".join(str(len(es)) for _, es in parts)
        rem = ", so the rater-dependent $S{=}1$ is the majority reading" if len(parts) == 2 and parts[0][0] == 1 and len(parts[0][1]) >= 3 else ""
        body = " but ".join(f"$S{{=}}{val}$ by {join_and(es)}" for val, es in parts) if len(parts) == 2 else "; ".join(f"$S{{=}}{val}$ by {join_and(es)}" for val, es in parts)
        return f"{body}, {tag}{rem}"
    for l in app:
        pivots = []
        for i, s in enumerate(l["shas"]):
            v = votes(l["problem"], s)
            if len({x for x in v.values() if x is not None}) > 1 and (i == 0 or s != l["shas"][i - 1]):
                pivots.append({"position": i, "id": l["ids"][i], "label": l["labels"][i], "votes": v, "split": split_txt(v)})
        l["pivot_texts"] = pivots
        bad = [c for c in CONCS if not l[f"identical_{c}"]]
        if bad:
            survival["flips"].append({"problem": l["problem"], "lineage": l["lineage"], "conclusions": bad, "evaluators_used": l["evaluators_used"],
                                      "values": {c: {L: l["layers"][L][c] for L in l["evaluators_used"] + list(AGG)} for c in bad},
                                      "sequences": {L: l["layers"][L]["seq"] for L in l["evaluators_used"] + list(AGG)}, "pivot_texts": pivots})
        nv = [c for c in CONCS if l[f"identical_{c}"] and not l[f"all_match_valid_{c}"]]
        if nv:
            survival["agree_but_not_valid"].append({"problem": l["problem"], "lineage": l["lineage"], "conclusions": nv,
                                                    "values": {c: {"evaluators": l["layers"][l["evaluators_used"][0]][c], REF: l["layers"][REF][c]} for c in nv},
                                                    "sequences": {L: l["layers"][L]["seq"] for L in l["evaluators_used"] + list(AGG)}})
    survival["aggregation_vs_valid"] = {L: [{"problem": l["problem"], "lineage": l["lineage"], "conclusions": [c for c in CONCS if l["layers"][L][c] != l["layers"][REF][c]]}
                                            for l in app if L in l["layers"] and any(l["layers"][L][c] != l["layers"][REF][c] for c in CONCS)] for L in ("written", "majority3")}
    survival["nesting_note"] = ("units are nested: ratings within fixed texts (Claude's 504 same-text pairs are 6 dependent pairs on each of 84 texts; GLM's 73 pairs one per text), texts and "
                                "checkpoints within selected lineages, lineages within a few problems, operators and overlapping model families; exact enumeration over pools of 2 or 4 ratings "
                                "per text carries all the evidence there is, and the Monte Carlo replays only check it")
    survival["lineages"] = [{k: l[k] for k in ("problem", "lineage", "k", "d", "covered", "texts_covered", "pool_deterministic", "evaluators_used", "layers", "survival", "pivot_texts")} for l in app]

    # ---- 2. identical-text controls vs different-text transitions -----------------------------------------------
    ident, diff = [], []
    for l in app:
        for i in range(l["k"] - 1):
            prob, sa, sb = l["problem"], l["shas"][i], l["shas"][i + 1]
            rec = {"problem": prob, "lineage": l["lineage"], "from": l["ids"][i], "to": l["ids"][i + 1]}
            if sa == sb:
                rec["layer0_S"] = [ck[(prob, l["ids"][i])]["S"], ck[(prob, l["ids"][i + 1])]["S"]]; rec["layer0_change"] = rec["layer0_S"][0] != rec["layer0_S"][1]
                rec["pools"] = {}
                for pn in POOLS:
                    p = poolS(pn, prob, sa)
                    rec["pools"][pn] = {"ratings": p, "covered": covered(pn, prob, sa), "expected_change_per_checkpoint_replay": r3(1 - sum((v / len(p)) ** 2 for v in Counter(p).values())) if len(p) >= 2 else None}
                ident.append(rec)
            else:
                classes = {L: cls(l["layers"][L]["seq"][i], l["layers"][L]["seq"][i + 1]) for L in l["evaluators_used"]}
                cv = cls(l["layers"][REF]["seq"][i], l["layers"][REF]["seq"][i + 1])
                rec.update(classes=classes, class_valid=cv, changes_across_evaluators=len(set(classes.values())) > 1, all_match_valid=all(v == cv for v in classes.values()), pools={})
                for pn in POOLS:
                    pa, pb = poolS(pn, prob, sa), poolS(pn, prob, sb); cvd = covered(pn, prob, sa) and covered(pn, prob, sb)
                    own = classes.get(pn, classes["glm"])
                    rec["pools"][pn] = {"covered": cvd, "p_class_differs_from_valid": r3(sum(cls(x, y) != cv for x in pa for y in pb) / (len(pa) * len(pb))) if cvd else None,
                                        "p_class_differs_from_own_rerating": r3(sum(cls(x, y) != own for x in pa for y in pb) / (len(pa) * len(pb))) if cvd else None}
                diff.append(rec)
    ident_all = ident_all_change = 0
    for l in lins:      # supplementary: every lineage, including route-N/A (where the paper's two layer-0 conflicts live)
        for i in range(l["k"] - 1):
            if l["shas"][i] == l["shas"][i + 1]:
                ident_all += 1; ident_all_change += ck[(l["problem"], l["ids"][i])]["S"] != ck[(l["problem"], l["ids"][i + 1])]["S"]
    def by_prob(recs, f):
        return {prob: f([r for r in recs if prob == "all" or r["problem"] == prob]) for prob in PROBS + ("all",)}
    def ident_agg(rs):
        o = {"n": len(rs), "layer0_changes": sum(r["layer0_change"] for r in rs), "change_rate_per_text_replay": 0.0 if rs else None}
        for pn in POOLS:
            cv = [r["pools"][pn]["expected_change_per_checkpoint_replay"] for r in rs if r["pools"][pn]["covered"]]
            o[pn] = {"n_covered": len(cv), "expected_change_rate_per_checkpoint_replay": r3(mean(cv)) if len(cv) >= MIN_COVERED else None}
        return o
    def diff_agg(rs):
        o = {"n": len(rs), "class_changes_across_evaluators": sum(r["changes_across_evaluators"] for r in rs), "class_not_all_equal_valid": sum(not r["all_match_valid"] for r in rs)}
        for pn in POOLS:
            cv = [r["pools"][pn] for r in rs if r["pools"][pn]["covered"]]
            o[pn] = {"n_covered": len(cv), "p_class_differs_from_valid_per_text_replay": r3(mean([x["p_class_differs_from_valid"] for x in cv])) if len(cv) >= MIN_COVERED else None,
                     "p_class_differs_from_own_rerating_per_text_replay": r3(mean([x["p_class_differs_from_own_rerating"] for x in cv])) if len(cv) >= MIN_COVERED else None}
        return o
    controls = {"identical_adjacent_pairs": by_prob(ident, ident_agg), "different_text_adjacent_pairs": by_prob(diff, diff_agg),
                "identical_adjacent_pairs_all_lineages_incl_route_na": {"n": ident_all, "layer0_changes": ident_all_change},
                "note": ("identical-text pairs: a per-text replay (caching) cannot change S between them; the expected change rate under independent per-checkpoint draws is "
                         f"1 - sum_v p_v^2 over the text's same-model rating distribution (exact). different-text pairs: transition class up/flat/down against the {REF_NAME} layer."),
                "identical_pairs": ident, "different_pairs": diff}

    # ---- 3. more checkpoints => more apparent progress?  (replay null, texts fixed; exact) ---------------------
    effect = {"definition": ("apparent up-transition = adjacent increase in a replayed sequence at a position where the reference sequence (per-text majority of the same-model pool; "
                             "ties -> that pool's re-rating) has no increase; replay null = independent draw per checkpoint from its text's pool, texts fixed; exact enumeration"),
              "design_note": ("the comparison is BETWEEN lineages of different lengths, texts, models and pool distributions, not one lineage thinned to different k; it cannot "
                              "isolate a checkpoint-count effect, and the observed record contributes a single apparent-up event"),
              "heuristic_note": ("1-(1-q/2)^(k-1) assumes a constant up-probability q/2 at every adjacent pair, independent adjacent events (they share a rating) and no reference "
                                 "exclusion; it is a heuristic, not the probability under the replay null. Pairwise q counts each observed pair once; the replay draws with replacement, "
                                 "whose per-text disagreement is draw_disagreement_mean (1/2 of pairwise q with two ratings, 3/4 with four)"), "pools": {}}
    for l in app:
        raw, val = l["layers"]["raw"]["seq"], l["layers"][REF]["seq"]
        ups = [i for i in range(l["k"] - 1) if raw[i + 1] > raw[i] and not (val[i + 1] > val[i])]
        l["layer0_apparent_up"] = len(ups); l["layer0_apparent_up_where"] = [l["labels"][i + 1] for i in ups]
        l["layer0_identical_changes"] = sum(l["shas"][i] == l["shas"][i + 1] and raw[i] != raw[i + 1] for i in range(l["k"] - 1))
        l["null"] = {}
    for pn in POOLS:
        ref_S = {}
        for key, p in pool[pn].items():
            c = Counter(r["S"] for r in p).most_common(); ref_S[key] = c[0][0] if len(c) == 1 or c[0][1] > c[1][1] else p[0]["S"]
        dfn_by_prob = {prob: proc_dists(pn, "per_checkpoint", prob)[0] for prob in PROBS}
        for l in app:
            ref = [ref_S[(l["problem"], s)] for s in l["shas"]]
            ref_up = [b > a for a, b in zip(ref, ref[1:])]; ref_chg = [a != b for a, b in zip(ref, ref[1:])]
            up = chg = 0.0
            if l["k"] >= 2:
                for sq, w in enum_seqs(l["shas"], dfn_by_prob[l["problem"]], False):
                    if any(gt(sq[i], sq[i + 1]) and not ref_up[i] for i in range(l["k"] - 1)): up += w
                    if any(ne(sq[i], sq[i + 1]) and not ref_chg[i] for i in range(l["k"] - 1)): chg += w
            l["null"][pn] = {"p_apparent_up": r3(up), "p_apparent_change": r3(chg)}
            if B and l["covered"][pn] and l["k"] >= 2:
                hit = 0
                for _ in range(B):
                    sq = draw(pn, "per_checkpoint", l["problem"], l["shas"]); hit += any(gt(sq[i], sq[i + 1]) and not ref_up[i] for i in range(l["k"] - 1))
                l["null"][pn]["mc_p_apparent_up"] = hit / B; mc["max_abs_diff_p_apparent_up"] = max(mc["max_abs_diff_p_apparent_up"], abs(hit / B - up))
        cov = [l for l in app if l["covered"][pn] and l["k"] >= 2]
        by_k = {}
        for k in sorted({l["k"] for l in app}):
            ls = [l for l in cov if l["k"] == k]
            by_k[str(k)] = {"n_covered_lineages": len(ls), "n_lineages": sum(l["k"] == k for l in app),
                            "p_apparent_up": r3(mean([l["null"][pn]["p_apparent_up"] for l in ls])) if ls else None,
                            "p_apparent_up_max": r3(max(l["null"][pn]["p_apparent_up"] for l in ls)) if ls else None,
                            "p_apparent_change": r3(mean([l["null"][pn]["p_apparent_change"] for l in ls])) if ls else None,
                            "heuristic_up_pairwise_q_1-(1-q/2)^(k-1)": r3(1 - (1 - Q[pn] / 2) ** (k - 1)) if Q[pn] is not None else None,
                            "heuristic_up_draw_q_1-(1-q/2)^(k-1)": r3(1 - (1 - QD[pn] / 2) ** (k - 1)) if QD[pn] is not None else None}
        kc = [l["k"] for l in cov]; sm = None
        if len(cov) >= MIN_COVERED:
            k_hi = max(3, sorted(kc)[len(kc) // 2]); lo = [l for l in cov if l["k"] == min(kc)]; hi = [l for l in cov if l["k"] >= k_hi]; k3 = [l for l in cov if l["k"] >= 3]
            nz = [l for l in cov if l["null"][pn]["p_apparent_up"] > 0]
            sm = {"k_min": min(kc), "p_up_at_k_min": r3(mean([l["null"][pn]["p_apparent_up"] for l in lo])), "k_hi_threshold": k_hi,
                  "p_up_at_k_hi": r3(mean([l["null"][pn]["p_apparent_up"] for l in hi])) if hi else None, "n_hi": len(hi), "p_up_at_k_hi_is_a_mean_over_lineages_not_a_maximum": True,
                  "p_up_mean_k_ge3": r3(mean([l["null"][pn]["p_apparent_up"] for l in k3])) if k3 else None, "n_k_ge3": len(k3),
                  "p_up_max_lineage": r3(max(l["null"][pn]["p_apparent_up"] for l in cov)), "n_covered": len(cov), "n_covered_zero": len(cov) - len(nz),
                  "n_covered_deterministic_pool": sum(l["pool_deterministic"][pn] for l in cov),
                  "nonzero_lineages": [{"problem": l["problem"], "lineage": l["lineage"], "k": l["k"], "p_apparent_up": l["null"][pn]["p_apparent_up"], "p_apparent_change": l["null"][pn]["p_apparent_change"]} for l in nz],
                  "present_under_null": bool(nz),
                  "spearman_k_vs_p_apparent_up": (lambda r: None if r is None else round(r, 3))(pearson(ranks(kc), ranks([l["null"][pn]["p_apparent_up"] for l in cov])))}
        effect["pools"][pn] = {"by_k": by_k, "n_covered_lineages": len(cov), "summary": sm}
    x = [l["k"] for l in app]; y_up = [l["layer0_apparent_up"] for l in app]; y_id = [l["layer0_identical_changes"] for l in app]
    rho_up, p_up = spearman_perm(x, y_up, rng); rho_id, p_id = spearman_perm(x, y_id, rng)
    effect["observed_layer0"] = {"apparent_up_transitions_total": sum(y_up), "lineages_with_any": sum(v > 0 for v in y_up), "n_lineages": len(app),
                                 "events": [{"problem": l["problem"], "lineage": l["lineage"], "k": l["k"], "at": l["layer0_apparent_up_where"]} for l in app if l["layer0_apparent_up"]],
                                 "spearman_k_vs_apparent_up": {"rho": rho_up, "perm_p": p_up}, "identical_text_changes_total": sum(y_id),
                                 "spearman_k_vs_identical_changes": {"rho": rho_id, "perm_p": p_id},
                                 "per_lineage": [{"problem": l["problem"], "lineage": l["lineage"], "k": l["k"], "apparent_up": l["layer0_apparent_up"], "identical_changes": l["layer0_identical_changes"]} for l in app]}

    # ---- 4. rating procedures and no-model baselines: two endpoints, cost comparison (exact) ---------------------
    pos_pairs = []
    for prob, a, b, note in POSITIVE:
        if b.startswith("pilot:") and b not in pilot: problems.append(f"positive pair skipped (pilot output unavailable): {b}"); continue
        if (prob, a) not in ck or (not b.startswith("pilot:") and (prob, b) not in ck): problems.append(f"positive pair skipped (missing record): {a} -> {b}"); continue
        sa, sb = sha_of(prob, a), sha_of(prob, b)
        s_ref = [lab[(prob, sa)]["S"][REF], lab[(prob, sb)]["S"][REF] if (prob, sb) in lab else None]
        pos_pairs.append({"problem": prob, "lineage_before": ck[(prob, a)]["lineage"], "before": a, "after": b, "note": note, "before_sha": sa[:12], "after_sha": sb[:12],
                          "pools": {pn: {"before": poolS(pn, prob, sa), "after": poolS(pn, prob, sb), "evaluable": bool(poolS(pn, prob, sa) and poolS(pn, prob, sb)),
                                         "covered": covered(pn, prob, sa) and covered(pn, prob, sb)} for pn in POOLS},
                          "gate_pass_after": pilot[b]["gate_pass"] if b.startswith("pilot:") else None, "S_ref": s_ref,
                          "kind": ("S=2 -> S=2: repair of a text already closed in the reference; tests endpoint acceptance only, a strict increase is impossible" if s_ref[0] == 2
                                   else "S<2 -> S=2 in the reference: tests improvement detection")})
    n_closed = sum(pp["S_ref"][0] == 2 for pp in pos_pairs); det_lineages = sorted({f"P{pp['problem']} {pp['lineage_before']}" for pp in pos_pairs if pp["S_ref"][0] != 2})
    neg_pairs = []
    for l in app:
        for i, j in combinations(range(l["k"]), 2):
            if l["shas"][i] == l["shas"][j]:
                neg_pairs.append({"problem": l["problem"], "lineage": l["lineage"], "a": l["ids"][i], "b": l["ids"][j], "kind": "identical_text",
                                  "pools": {pn: {"ratings": poolS(pn, l["problem"], l["shas"][i]), "covered": covered(pn, l["problem"], l["shas"][i])} for pn in POOLS},
                                  "layer0_change": ck[(l["problem"], l["ids"][i])]["S"] != ck[(l["problem"], l["ids"][j])]["S"]})
    dp, da, db = DEFECT_PAIR
    if (dp, da) in ck and (dp, db) in ck:
        sA, sB = ck[(dp, da)]["sha"], ck[(dp, db)]["sha"]
        defect = {"problem": dp, "a": da, "b": db, "kind": "same_defect_different_text", "layer0_change": ck[(dp, da)]["S"] != ck[(dp, db)]["S"],
                  "valid_S": [lab[(dp, sA)]["S"][REF], lab[(dp, sB)]["S"][REF]], "single_evaluator_S": {e: [live_S[e].get((dp, sA)), live_S[e].get((dp, sB))] for e in FOUR},
                  "pools": {pn: {"a": poolS(pn, dp, sA), "b": poolS(pn, dp, sB), "a_modes": [r["mode"] for r in pool[pn][(dp, sA)]], "b_modes": [r["mode"] for r in pool[pn][(dp, sB)]],
                                 "covered": covered(pn, dp, sA) and covered(pn, dp, sB)} for pn in POOLS},
                  "target_note": (f"both texts rest on the same refuted finiteness lemma; the negative control fixes the {REF_NAME} target (S=1 and 1), not identical quality "
                                  "or identical written mechanisms of the two different texts")}
    else: defect = None; problems.append("same-defect negative pair not found")
    cost = {"none": 0, "constant2": 0, "per_checkpoint": mean([l["k"] for l in app]), "cached": mean([l["d"] for l in app]), "majority3_text": 3 * mean([l["d"] for l in app]), "majority3_checkpoint": 3 * mean([l["k"] for l in app])}
    total = {"none": 0, "constant2": 0, "per_checkpoint": sum(l["k"] for l in app), "cached": sum(l["d"] for l in app), "majority3_text": 3 * sum(l["d"] for l in app), "majority3_checkpoint": 3 * sum(l["k"] for l in app)}
    remedies = {"pools": {}, "baselines": {}, "positive_set": pos_pairs, "positive_set_summary": {"n": len(pos_pairs), "n_before_already_S2_in_reference": n_closed, "n_detection_possible": len(pos_pairs) - n_closed,
                                                                                                    "detection_possible_lineages": det_lineages},
                "negative_identical_pairs": neg_pairs, "negative_same_defect_pair": defect,
                "cost_ratings_per_lineage": {p: r3(cost[p]) for p in PROCS}, "cost_total_ratings": total,
                "definitions": {"stability": "probability that two independent runs of the procedure reach the same conclusion (sum of squared exact replay probabilities), mean over lineages fully "
                                             "covered by the pool; abstentions count as a value, which is why the no-rating baseline scores 1.00",
                                "detected": "improvement detection: P(S_after > S_before) between the two texts of a positive pair (an abstention on either text is not a detection); expected "
                                            "count over the pairs whose two texts both carry at least one rating in the pool (the pilot outputs carry a GLM-5.3 and a Kimi grade, no Claude grade)",
                                "accepted": "endpoint acceptance: P(S_after = 2) for the later text of a positive pair, same denominator; a constant S=2 without any rating accepts every pair, "
                                            "so acceptance alone is degenerate",
                                "false_change": "P(S differs, both known) between the two checkpoints of a negative-control pair; identical-text pairs restricted to texts with >=2 ratings in the pool",
                                "cost": "ratings per applicable lineage: k checkpoints for per-checkpoint procedures, d distinct texts for per-text procedures (x3 for majority of three)",
                                "cost_comparison": "(ii) costs d <= k ratings, (iii) 3d, (iv) 3k >= 3d without caching; these are rating-count comparisons, not matched budgets: the four "
                                                   "models' calls differ in thinking behaviour and token use, so equal rating counts are not equal compute"}}
    def proc_block(pn, proc):
        cov_l = [l for l in app if pn is None or l["covered"][pn]]
        st = {c: [] for c in CONCS}; det = {c: 0 for c in CONCS}; abst_ck = n_ck = abst_conc = n_conc = 0.0
        for l in app:
            dfn, cache = proc_dists(pn or "glm", proc, l["problem"]); cd = conc_dist(l["shas"], dfn, cache)
            for s in l["shas"]: n_ck += 1; abst_ck += dfn(s).get(None, 0.0)
            for c in CONCS: n_conc += 1; abst_conc += cd[c].get(None, 0.0)
            if pn is None or l["covered"][pn]:
                for c in CONCS: st[c].append(stab(cd[c])); det[c] += len([v for v in cd[c].values() if v > 1e-12]) == 1
        rec = []
        for pp in pos_pairs:
            if pn is not None and not pp["pools"][pn]["evaluable"]: rec.append({"pair": f"{pp['before']} -> {pp['after']}", "evaluable": False}); continue
            dfn, cache = proc_dists(pn or "glm", proc, pp["problem"]); d_ = a_ = ab = 0.0
            for sq, w in enum_seqs([sha_of(pp["problem"], pp["before"]), sha_of(pp["problem"], pp["after"])], dfn, cache):
                d_ += w * gt(sq[0], sq[1]); a_ += w * (sq[1] == 2); ab += w * (sq[1] is None)
            rec.append({"pair": f"{pp['before']} -> {pp['after']}", "kind": pp["kind"].split(":")[0], "p_detected": r3(d_), "p_accepted": r3(a_), "p_abstain_after": r3(ab), "evaluable": True})
        fc = []
        for npair in neg_pairs:
            if pn is not None and not npair["pools"][pn]["covered"]: fc.append(None); continue
            dfn, cache = proc_dists(pn or "glm", proc, npair["problem"]); sha = ck[(npair["problem"], npair["a"])]["sha"]
            fc.append(r3(sum(w * ne(sq[0], sq[1]) for sq, w in enum_seqs([sha, sha], dfn, cache))))
        fd = None
        if defect and (pn is None or defect["pools"][pn]["covered"]):
            dfn, cache = proc_dists(pn or "glm", proc, dp); fd = r3(sum(w * ne(sq[0], sq[1]) for sq, w in enum_seqs([ck[(dp, da)]["sha"], ck[(dp, db)]["sha"]], dfn, cache)))
        ev = [r for r in rec if r["evaluable"]]; ncov_neg = sum(v is not None for v in fc)
        return {"label": PROC_LABEL[proc], "cost_ratings_per_lineage": r3(cost[proc]), "cost_total_ratings": total[proc],
                "abstention_rate_checkpoints": r3(abst_ck / n_ck) if n_ck else None, "abstention_rate_conclusions": r3(abst_conc / n_conc) if n_conc else None,
                "stability": {c: (r3(mean(st[c])) if len(cov_l) >= MIN_COVERED else None) for c in CONCS}, "stability_min": {c: (r3(min(st[c])) if st[c] else None) for c in CONCS},
                "deterministic_lineages": {c: f"{det[c]}/{len(cov_l)}" for c in CONCS}, "n_covered_lineages": len(cov_l),
                "detected_expected_of_evaluable": [r3(sum(r["p_detected"] for r in ev)), len(ev)], "accepted_expected_of_evaluable": [r3(sum(r["p_accepted"] for r in ev)), len(ev)],
                "detected_lineages": sorted({f"P{pp['problem']} {pp['lineage_before']}" for pp, r in zip(pos_pairs, rec) if r["evaluable"] and r["p_detected"] > 0}),
                "per_pair": rec, "false_change_identical_texts": r3(mean([v for v in fc if v is not None])) if ncov_neg >= MIN_COVERED else None,
                "false_change_identical_texts_n_covered_pairs": f"{ncov_neg}/{len(neg_pairs)}", "false_change_same_defect_pair": fd}
    for proc in NO_MODEL: remedies["baselines"][proc] = proc_block(None, proc)
    for pn in POOLS:
        R = {proc: proc_block(pn, proc) for proc in PROCS if proc not in NO_MODEL}
        remedies["pools"][pn] = {"name": POOLS[pn]["name"], "workflow": POOLS[pn]["workflow"], "n_covered_lineages": sum(l["covered"][pn] for l in app),
                                 "n_positive_pairs_evaluable": sum(pp["pools"][pn]["evaluable"] for pp in pos_pairs),
                                 "n_positive_pairs_evaluable_before_already_S2": sum(pp["pools"][pn]["evaluable"] and pp["S_ref"][0] == 2 for pp in pos_pairs), "procedures": R}
    remedies["observed_layers"] = {"identical_pairs_layer0_changes": f"{sum(n['layer0_change'] for n in neg_pairs)}/{len(neg_pairs)}",
                                   "same_defect_pair": None if not defect else {k: defect[k] for k in ("layer0_change", "valid_S", "single_evaluator_S")}}
    # ---- 5. same-defect control: exact algebra and what did detect the defect ----------------------------------
    if defect:
        ex = {}
        for pn in POOLS:
            if not defect["pools"][pn]["covered"]: continue
            dA, dB = dist_S(pn, dp, sA), dist_S(pn, dp, sB); mA, mB = dist_maj3(dA), dist_maj3(dB)
            ex[pn] = {"P_S": {"a": {str(k): r3(v) for k, v in dA.items()}, "b": {str(k): r3(v) for k, v in dB.items()}},
                      "single_draw_disagreement": r3(1 - sum(dA.get(v, 0) * dB.get(v, 0) for v in set(dA) | set(dB))),
                      "P_majority3": {"a": {str(k): r3(v) for k, v in mA.items()}, "b": {str(k): r3(v) for k, v in mB.items()}},
                      "majority3_disagreement": r3(1 - sum(mA.get(v, 0) * mB.get(v, 0) for v in set(mA) | set(mB)))}
        defect["exact"] = ex
        defect["algebra"] = ("P(disagree) = 1 - sum_v P(S_a=v) P(S_b=v). With the Claude Opus 5 pools [1,1,2,1] and [1,2,2,1]: 1 - (3/4 * 1/2 + 1/4 * 1/2) = 1/2 exactly. Majority of three "
                             "on [1,2,2,1] gives S=2 with probability 3*(1/2)^2*(1/2) + (1/2)^3 = 1/2 again, so P(disagree) = P(maj_a=1)/2 + P(maj_a=2)/2 = 1/2 whatever the first text's "
                             "distribution: majority voting of this rater does not cure this error (the table's identical values under every procedure are this identity, not separate measurements)")
        detections = {"glm_thinking_repeat_rep1_S": {da: rep_S["rep1"].get((dp, sA)), db: rep_S["rep1"].get((dp, sB))}, "glm_thinking_repeat_rep1_notes": {}, "ordinary_grades": {}}
        for ident_, sha in ((da, sA), (db, sB)):
            g = load(art / POOLS["glm"]["repeat_dir"] / f"p{dp}" / "rep1" / f"p{dp}-h-{sha[:12]}" / "annotation.json")
            if g and g.get("sha256") == sha: detections["glm_thinking_repeat_rep1_notes"][ident_] = ((g.get("grades") or {}).get("notes") or "")[:220]
        for m, d in BASELINE_DIRS.items():
            for ident_, sha in ((da, sA), (db, sB)):
                g = load(art / d / f"p{dp}" / f"p{dp}-h-{sha[:12]}" / "annotation.json")
                if g and g.get("sha256") == sha and isinstance((g.get("grades") or {}).get("grade"), int):
                    detections["ordinary_grades"].setdefault(m, {})[ident_] = {"grade": g["grades"]["grade"], "main_gap": (g["grades"].get("main_gap") or "")[:220]}
        defect["detections_elsewhere"] = detections
        defect["conclusion"] = ("narrow: majority voting of this rater does not cure this error; NOT that repeated grading cannot supply validity in general -- the GLM-5.3 thinking repeat and "
                                "Claude Opus 5's ordinary grader detected the counterexample")

    # ---- 6. sources of instability ------------------------------------------------------------------------------
    kap = {name: {prob: kappa([(live_S[a].get(k), live_S[b].get(k)) for k in lab if k[0] == prob]) for prob in PROBS} for name, (a, b) in KAPPA_PAIRS.items()}
    for name, (a, b) in KAPPA_PAIRS.items(): kap[name]["all"] = kappa([(live_S[a].get(k), live_S[b].get(k)) for k in lab])
    shipped = {name: {prob: ((rel.get(prob if prob != "all" else "overall") or {}).get(key) or {}) for prob in PROBS + ("all",)} for name, key in KAPPA_KEYS.items()}
    for name in KAPPA_PAIRS:
        for prob in PROBS + ("all",):
            sk, rk = shipped[name][prob].get("kappa"), kap[name][prob]["kappa"]
            if sk is not None and rk is not None and abs(sk - rk) > 0.0015: problems.append(f"{name} kappa P{prob}: reliability.json {sk} != recomputed {rk}")
    def krange(prob):
        vals = [shipped[n][prob].get("kappa") for n in KAPPA_PAIRS if shipped[n][prob].get("kappa") is not None]
        return (min(vals), max(vals)) if vals else (None, None)
    k2 = krange("2"); k36 = [v for p in ("3", "6") for v in krange(p) if v is not None]; k36 = (min(k36), max(k36)) if k36 else (None, None)
    p2 = [l for l in lins if l["problem"] == "2"]; na = [l for l in p2 if not l["applicable"]]
    na_grade = [l for l in na if l["grade_for_agreement"] is not None and l["S_final_matrix"] is not None]
    na_dis = [l["lineage"] for l in na_grade if (l["S_final_matrix"] == 2) != (l["grade_for_agreement"] >= 5)]
    final_key = f"6:{ck[('6', 'p6-deedy-gpt-5.6-sol-final')]['sha']}" if ("6", "p6-deedy-gpt-5.6-sol-final") in ck else None
    def p6_policy(policy):
        regress, s1, seqs = [], 0, {}
        for l in lins:
            if l["problem"] != "6": continue
            sq = []
            for s in l["shas"]:
                wf = lab[("6", s)]["fields"]["written"]; ov = overrides.get(f"6:{s}")
                use = ov is not None and (policy == "all" or (policy == "final_only" and f"6:{s}" == final_key))
                sq.append(S_of((ov.get("lower", wf[0]), ov.get("upper", wf[1])) if use else tuple(wf)))
            seqs[l["lineage"]] = sq; s1 += sq.count(1)
            if any(b < a for a, b in zip(sq, sq[1:])): regress.append(l["lineage"])
        return {"regressing_lineages": regress, "n_regressing": len(regress), "n_S1_checkpoints": s1, "sequences": seqs}
    correction = {p: p6_policy(p) for p in ("none", "final_only", "all")}
    sources = {"repeat_variability": {pn: {"name": POOLS[pn]["name"], "workflow": POOLS[pn]["workflow"], "q_workflow": Q[pn], "q_fixed": QF[pn], "q_fixed_primary": q[pn]["pooled"]["q_fixed_primary"],
                                          "q_mixed": q[pn]["pooled"]["q_mixed"], "draw_disagreement_mean": QD[pn], "q_by_problem": {p: q[pn][p]["q"] for p in ("3", "6")},
                                          "q_fixed_by_problem": {p: q[pn][p]["q_fixed"] for p in ("3", "6")},
                                          **{k: q[pn]["pooled"][k] for k in ("pairs", "pairs_differ", "fixed_pairs", "fixed_differ", "fixed_primary_pairs", "fixed_primary_differ", "fixed_fallback_pairs",
                                                                              "fixed_fallback_differ", "mixed_pairs", "mixed_differ", "texts")},
                                          "q_lower_field": q[pn]["pooled"]["q_lower"], "q_upper_field": q[pn]["pooled"]["q_upper"], "q_3plus_ratings": q[pn]["pooled_3plus_ratings"]["q"],
                                          "variable_texts": q[pn]["pooled"]["variable_texts"], "completion": completion[pn]} for pn in POOLS},
               "evaluator_choice": {name: {"reliability_json": shipped[name], "recomputed": kap[name]} for name in KAPPA_PAIRS},
               "rubric_choice": {"kappa_range_P2": k2, "kappa_range_P3_P6": k36, "p2_lineages": len(p2), "p2_route_na": len(na), "p2_route_na_with_grade": len(na_grade),
                                 "p2_route_na_S_final_vs_grade_disagree": len(na_dis), "p2_route_na_disagreeing": na_dis},
               "inconsistent_correction": {"description": f"P6 correction entries applied to none of the texts (written layer), to the final GPT-5.6-Sol file only (v3), or to all listed texts ({REF_NAME} layer)",
                                           **{p: {k: v for k, v in correction[p].items() if k != "sequences"} for p in correction},
                                           "sequences": {p: {k: v for k, v in correction[p]["sequences"].items() if k in ("deedy-gpt-5.6-sol", "deedy-kimi-k3")} for p in correction}},
               "note": "a taxonomy, not a statistical decomposition: within-model q, between-model kappa, route exclusions and correction policy have different units and overlapping causes"}

    # ---- 7. disagreement as an alarm ----------------------------------------------------------------------------
    # (a) rule per text: the evaluators present (four single evaluators + GLM repeat rep1) do not all give the same S
    def alarm(key):
        ev = {e: live_F[e][key] for e in FOUR if key in live_F[e]}
        if key in rep_F["rep1"]: ev["rep1"] = rep_F["rep1"][key]
        Ss = [S_of(f) for f in ev.values()]; fl = [{f[i] for f in ev.values()} for i in (0, 1)]
        return {"evaluators": sorted(ev), "S": {e: S_of(f) for e, f in ev.items()}, "S_disagree": len(set(Ss)) > 1,
                "field_2_vs_lt2": any(2 in v and (0 in v or 1 in v) for v in fl), "any_S2": 2 in Ss}
    # (b) systematic ascertainment of documented-defective texts: every correction entry + every public final of an applicable lineage with a failing released grade
    documented = {}
    def doc_rec(prob, sha):
        return documented.setdefault((prob, sha), {"problem": prob, "sha": sha, "record_ids": rids(prob, sha), "id": rids(prob, sha)[0], "sources": [], "kinds": [],
                                                   "public_score": None, "receipt_excerpt": None})
    for k_, v in sorted(overrides.items()):
        prob, sha = k_.split(":", 1); d = doc_rec(prob, sha)
        if v.get("record_ids"): d["record_ids"] = list(v["record_ids"]); d["id"] = v["record_ids"][0]
        d["sources"].append("closure_adjudicated/validity_overrides.json"); d["kinds"].append("correction entry: independent refutation or recorded fatal invalid step")
        if (prob, sha) not in lab: problems.append(f"correction entry P{prob} {sha[:12]} has no labels.json record")
    PG = load(art / PUBLIC_GRADES) or {}; receipts = {prob: load(art / p) or {} for prob, p in PUBLIC_RECEIPTS.items()}
    for prob, p in PUBLIC_RECEIPTS.items():
        if not receipts[prob].get("entries"): problems.append(f"public receipt {p} missing or empty")
    if not PG.get("final"): problems.append(f"{PUBLIC_GRADES} missing or without final grades")
    public_finals, public_finals_route_na = [], []
    for l in lins:
        if l["source"] != "public": continue
        prob = l["problem"]; fin = {i: s for i, s in zip(l["ids"], l["shas"]) if i.endswith("-final")}
        if not fin: problems.append(f"P{prob} public lineage {l['lineage']}: no final file among its checkpoints"); continue
        for ident, sha in fin.items():
            model = (lab.get((prob, sha)) or {}).get("model") or l["lineage"].split("-", 1)[-1]
            e = next((x for x in receipts.get(prob, {}).get("entries", []) if x.get("model") == model), None)
            tg = ((PG.get("final") or {}).get(prob) or {}).get(model); score = e.get("score") if e else tg
            if e and tg is not None and e.get("score") != tg: problems.append(f"P{prob} {ident}: receipt grade {e.get('score')} != {PUBLIC_GRADES} final grade {tg}")
            if score is None: problems.append(f"P{prob} {ident}: no released public grade for model {model}"); continue
            rec = {"problem": prob, "id": ident, "sha": sha[:12], "model": model, "public_score": score, "source": PUBLIC_RECEIPTS[prob] if e else PUBLIC_GRADES,
                   "failing": score <= PUBLIC_FAIL_MAX, "S": alarm((prob, sha))["S"]}
            if not l["applicable"]: public_finals_route_na.append(rec); continue      # route-N/A lineages are outside the alarm's scope
            public_finals.append(rec)
            if score <= PUBLIC_FAIL_MAX:
                d = doc_rec(prob, sha); d["sources"].append(rec["source"]); d["public_score"] = score; d["kinds"].append(f"public final file with a failing released grade ({score}/7)")
                if e: d["receipt_excerpt"] = (e.get("justification") or "")[:240]
    # first-pass grades attach to earlier texts that no released receipt identifies; they enter only through the correction entries (P6 Kimi 3/7 -> round2-t007)
    fp_not_used = [{"problem": prob, "model": m, "first_pass": g, "final": ((PG.get("final") or {}).get(prob) or {}).get(m)} for prob in ("3", "6")
                   for m, g in (((PG.get("first_pass") or {}).get(prob)) or {}).items() if g <= PUBLIC_FAIL_MAX and (((PG.get("final") or {}).get(prob) or {}).get(m) or 0) > PUBLIC_FAIL_MAX]
    # (c) per-text records; credited-defective = documented AND some evaluator gives S=2 (the target)
    app_keys = {key for prob in PROBS for key in text_keys[prob]}
    per_text = []
    for key, r in sorted(lab.items()):
        a = alarm(key); d = documented.get(key)
        a.update(problem=key[0], sha=key[1][:12], record_ids=r["record_ids"], lineage=r.get("lineage"), applicable=key in app_keys, documented=d is not None,
                 credited_defective=d is not None and a["any_S2"], evidence=d is not None and a["any_S2"], public_score=d["public_score"] if d else None,
                 record_sources=list(d["sources"]) if d else [], S_ref=r["S"].get(REF), S_written=r["S"].get("written"))
        per_text.append(a)
    for key, d in documented.items():
        t = next((t for t in per_text if (t["problem"], t["sha"]) == (key[0], key[1][:12])), None)
        if t is None: problems.append(f"documented-defective text P{key[0]} {d['id']} has no labels.json record"); continue
        d.update(S=t["S"], S_disagree=t["S_disagree"], field_2_vs_lt2=t["field_2_vs_lt2"], credited_defective=t["credited_defective"], S_ref=t["S_ref"], applicable=t["applicable"])
        if not t["applicable"]: problems.append(f"documented-defective text P{key[0]} {d['id']} lies outside the applicable lineages")
    app_texts = [t for t in per_text if t["applicable"]]
    doc_texts = [t for t in app_texts if t["documented"]]; cred_texts = [t for t in doc_texts if t["credited_defective"]]
    flagged = [t for t in app_texts if t["S_disagree"]]; norec_flags = [t for t in flagged if not t["documented"]]
    def n_distinct_defects(ts):
        parent = {(t["problem"], t["sha"]): (t["problem"], t["sha"]) for t in ts}
        def find(k):
            while parent[k] != k: k = parent[k]
            return k
        for prob, a, b in SAME_DEFECT:
            if (prob, a) in ck and (prob, b) in ck:
                ka, kb = (prob, ck[(prob, a)]["sha"][:12]), (prob, ck[(prob, b)]["sha"][:12])
                if ka in parent and kb in parent: parent[find(ka)] = find(kb)
        return len({find(k) for k in parent})
    # (d) sensitivity to the evaluator set: a text counts when at least two evaluators of the set rated it; flag = the set's evaluators present disagree on S
    def eval_set_stats(E):
        o = {"evaluators": list(E), "n_texts": 0, "n_texts_complete": 0, "flags": 0, "credited_hits": 0, "credited_n": 0, "documented_hits": 0, "documented_n": 0,
             "flags_without_record": 0, "texts_without_record": 0, "flagged_ids": [], "credited_hit_ids": [], "credited_miss_ids": [], "flags_without_record_ids": []}
        for t in app_texts:
            s = {e: t["S"][e] for e in E if e in t["S"]}
            if len(s) < 2: continue
            f = len(set(s.values())) > 1
            o["n_texts"] += 1; o["n_texts_complete"] += len(s) == len(E); o["flags"] += f
            if f: o["flagged_ids"].append(t["record_ids"][0])
            if t["credited_defective"]: o["credited_n"] += 1; o["credited_hits"] += f; (o["credited_hit_ids"] if f else o["credited_miss_ids"]).append(t["record_ids"][0])
            if t["documented"]: o["documented_n"] += 1; o["documented_hits"] += f
            else:
                o["texts_without_record"] += 1; o["flags_without_record"] += f
                if f: o["flags_without_record_ids"].append(t["record_ids"][0])
        return o
    pairs = {"-".join(E): eval_set_stats(E) for E in ALARM_PAIRS + ALARM_TRIPLES + (FOUR,)}
    pairs["all"] = eval_set_stats(ALARM_EVALS)
    if pairs["all"]["flags"] != len(flagged) or pairs["all"]["n_texts"] != len(app_texts): problems.append("alarm: evaluator-set 'all' does not reproduce the per-text rule")
    # (e) aggregates; the per_problem keys are read by scripts/fill_numbers.py: evidence_texts = credited-defective texts (the target), hits_of_evidence, flags_of_texts_without_evidence
    def alarm_agg(ts):
        o = {"texts": len(ts), "evidence_texts": sum(t["credited_defective"] for t in ts), "texts_without_evidence": sum(not t["credited_defective"] for t in ts),
             "documented_texts": sum(t["documented"] for t in ts), "texts_without_record": sum(not t["documented"] for t in ts),
             "keys": "evidence_texts = credited-defective texts (documented defect and some evaluator S=2: the alarm's target); documented_texts = every documented-defective text"}
        for rule in ("S_disagree", "field_2_vs_lt2"):
            fl = [t for t in ts if t[rule]]; hits = sum(t["credited_defective"] for t in fl); dh = sum(t["documented"] for t in fl)
            o[rule] = {"flagged": len(fl), "hits_of_evidence": f"{hits}/{o['evidence_texts']}", "flags_of_texts_without_evidence": f"{len(fl) - hits}/{o['texts_without_evidence']}",
                       "precision_hits_of_flagged": f"{hits}/{len(fl)}", "hits_of_documented": f"{dh}/{o['documented_texts']}",
                       "flags_of_texts_without_record": f"{len(fl) - dh}/{o['texts_without_record']}", "flagged_record_ids": [t["record_ids"][0] for t in fl]}
        return o
    eval_names_plain = [ANN_PLAIN.get(live_annot.get(e), live_annot.get(e) or e) for e in FOUR]
    doc_sorted = sorted(documented.values(), key=lambda d: (d["problem"], not d.get("credited_defective"), d["id"]))
    def miss_rec(d): return {"id": d["id"], "problem": d["problem"], "public_score": d["public_score"], "S": d["S"], "sources": d["sources"], "record_ids": d["record_ids"]}
    alarm_res = {
        "target": (f"credited-defective texts: texts with a documented defect (a correction entry of validity_overrides.json, that is an independent refutation or a recorded fatal "
                   f"invalid step, or a public final file whose released public verifier grade is at most {PUBLIC_FAIL_MAX} of 7) that at least one of the evaluators the alarm uses "
                   f"({', '.join(eval_names_plain)} or the GLM-5.3 repeat) nevertheless rates S=2; a documented-defective text that every evaluator rates S<2 is already visible to an "
                   "operator and is not the alarm's target, and a text without any record is unexamined, not a known negative."),
        "definition": {"evaluators": "the four single evaluators (GLM-5.3 re-rating, Kimi K3, Claude Opus 5, GPT-5.6-Sol where present) plus the GLM-5.3 repeat rep1 where present",
                       "S_disagree": "the evaluators present do not all give the same S", "field_2_vs_lt2": "for the lower or the upper field, some evaluator scores 2 while another scores 0 or 1 "
                       "(implied by S disagreement; also fires when equal S hide swapped fields)",
                       "documented_defective": (f"systematic ascertainment, not a selected evidence set: (a) every correction entry of validity_overrides.json; (b) every public final file of an "
                                                f"applicable lineage whose released public verifier grade is <= {PUBLIC_FAIL_MAX}/7, whatever the grader's model or wording (grade from the released "
                                                f"receipt where one exists: {', '.join(f'P{p} {v}' for p, v in PUBLIC_RECEIPTS.items())}; else from {PUBLIC_GRADES}); first-pass grades attach to "
                                                "earlier texts that no released receipt identifies and enter only through (a)"),
                       "credited_defective": "documented-defective and rated S=2 by at least one evaluator the alarm uses: the target, because a text every evaluator rates S<2 needs no alarm",
                       "flags_without_record": "flagged texts with neither a correction entry nor a failing public grade: unexamined, not known negatives",
                       "distinct_defects": "credited-defective texts merged when they carry one and the same defect (SAME_DEFECT: the two P6 GPT-default texts share one false lemma)",
                       "pairs": "for an evaluator set, a text counts when at least two of its evaluators rated it and is flagged when those present disagree on S; credited_n / documented_n "
                                "= credited / documented texts so counted; n_texts_complete = texts every evaluator of the set rated",
                       "scope": "texts of applicable lineages (route-N/A P2 excluded); counts, not rates"},
        "ascertainment": {"public_fail_max": PUBLIC_FAIL_MAX, "n_correction_entries": len(overrides), "public_finals_in_scope": public_finals,
                          "n_public_finals_in_scope": len(public_finals), "n_public_finals_failing": sum(p["failing"] for p in public_finals),
                          "public_finals_route_na_excluded": public_finals_route_na, "first_pass_grades_not_used": fp_not_used},
        "n_texts": len(app_texts), "n_flagged": len(flagged),
        "credited_defective": {"n": len(cred_texts), "hits": sum(t["S_disagree"] for t in cred_texts), "ids": [t["record_ids"][0] for t in cred_texts],
                               "distinct_defects": n_distinct_defects(cred_texts), "misses": [t["record_ids"][0] for t in cred_texts if not t["S_disagree"]]},
        "documented_defective": {"n": len(doc_texts), "hits": sum(t["S_disagree"] for t in doc_texts), "ids": [d["id"] for d in doc_sorted if d.get("applicable")],
                                 "misses": [miss_rec(d) for d in doc_sorted if d.get("applicable") and not d["S_disagree"]],
                                 "never_credited": [d["id"] for d in doc_sorted if d.get("applicable") and not d["credited_defective"]]},
        "flags_without_record": {"n": len(norec_flags), "ids": [t["record_ids"][0] for t in norec_flags], "texts_without_record": len(app_texts) - len(doc_texts),
                                 "note": "unexamined, not known negatives"},
        "pairs": pairs, "evidence_texts": doc_sorted,
        "per_problem": {prob: alarm_agg([t for t in app_texts if prob == "all" or t["problem"] == prob]) for prob in PROBS + ("all",)},
        "all_texts_incl_route_na": alarm_agg(per_text), "texts": app_texts}

    # ---- results.json --------------------------------------------------------------------------------------------
    extra = sorted({k for r in labels for k, v in r["S"].items() if v is not None} - set(single) - set(AGG) - set(REP_LAYERS))
    results = {"meta": {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "computation": "exact enumeration of every replay distribution", "monte_carlo_check": mc,
                        "replays": B, "seed": args.seed, "min_covered_for_cell": MIN_COVERED,
                        "applicable_lineages": len(app), "excluded_route_na_lineages": len(lins) - len(app), "evaluators": list(single), "aggregation_layers": list(AGG),
                        "reference_layer": survival["reference"], "labels_layers_not_used": extra, "annotators": live_annot,
                        "pools": {pn: {"name": POOLS[pn]["name"], "workflow": POOLS[pn]["workflow"]} for pn in POOLS}, "completion": completion, "runtime_sec": None,
                        "replay_definition": "per-text replay: one draw per distinct text from its same-model pool (re-rating + repeats), applied to every checkpoint sharing the text; "
                                             "per-checkpoint replay: independent draw per checkpoint. Texts with a single rating are deterministic; cells are shown only over lineages/pairs "
                                             "whose every text has >=2 ratings in the pool ('covered'), otherwise '--'. The GLM-5.3 pool is the output of the adaptive workflow as run.",
                        "conclusion_definitions": {"improved": "last S > first S", "regressed": "some adjacent decrease",
                                                   "crossing": "0-based index of the first S=2 checkpoint, or 'none' (prose reports 1-based checkpoint positions); null = undetermined"}},
               "coverage": coverage, "q": q, "survival": survival, "identical_text_controls": controls, "checkpoint_effect": effect, "remedies": remedies, "sources": sources,
               "alarm": alarm_res, "data_problems": problems}

    # ---- tables ---------------------------------------------------------------------------------------------------
    PN = {"3": "P3", "6": "P6", "2": "P2$^{\\mathrm{s}}$", "all": "all"}
    S = survival["per_problem"]
    def note_par(txt): return "\\par\\vspace{1pt}{\\raggedright\\scriptsize " + txt + "\\par}"
    def prow(prob):
        s = S[prob]; n = s["n_lineages"]; idn = s["identical_across_evaluators"]; pv = s["reference_prevalence"]
        cells = [f"  {PN[prob]} & {n} & {pv['improved']}/{pv['regressed']}/{pv['crossing']}"] + [f"{idn[c]}/{n}" for c in CONCS]
        for pn in POOLS:
            r = s["replay"][pn]; cells += [fmt(r["survival_text_vs_valid"][c]) for c in CONCS] + [f"{r['n_covered']}/{n}"]
        rows = [" & ".join(cells) + " \\\\"]
        if any(s["replay"][pn]["n_covered"] >= MIN_COVERED for pn in POOLS):
            mins = ["  \\quad min.\\ lineage & & & & &"]
            for pn in POOLS:
                r = s["replay"][pn]; mins += [fmt(r["min_survival_text_vs_valid"][c]) if r["n_covered"] >= MIN_COVERED else "--" for c in CONCS] + [""]
            rows.append(" & ".join(mins) + " \\\\")
        return "\n".join(rows)
    t_surv = "\n".join([
        f"% generated by scripts/conclusion_sensitivity.py -- applicable lineages; evaluators = layer 0, GLM-5.3, Kimi K3, Claude Opus 5, GPT (P3/P6) and every completed repeat;",
        f"% ref. = {REF_NAME} layer (labels.json key '{REF}'); i/r/c = lineages whose ref. conclusion is improved / regressed / crossed; survival = exact P(per-text replay from the",
        f"% same-model pool reproduces the ref. conclusion), mean over covered lineages, then the lowest covered lineage; cov. = lineages whose every text has >=2 ratings; -- = fewer than {MIN_COVERED} covered",
        "\\setlength{\\tabcolsep}{2.6pt}\\begin{tabular}{@{}lrcccccccrcccr@{}}", "  \\toprule",
        f"  & & ref. & \\multicolumn{{3}}{{c}}{{same under every evaluator}} & \\multicolumn{{4}}{{c}}{{survival, {POOLS['glm']['name']} (adaptive)}} & \\multicolumn{{4}}{{c}}{{survival, {POOLS['claude']['name']}}} \\\\",
        "  \\cmidrule(lr){4-6}\\cmidrule(lr){7-10}\\cmidrule(lr){11-14}",
        "  Problem & lin. & i/r/c & impr. & regr. & cross. & impr. & regr. & cross. & cov. & impr. & regr. & cross. & cov. \\\\", "  \\midrule",
        prow("3"), prow("6"), prow("2"), "  \\midrule", prow("all"), "  \\bottomrule", "\\end{tabular}",
        note_par(f"ref.\\ = {REF_NAME} layer, an author-maintained and partly model-derived reference (the written GLM$\\cap$Kimi layer with {len(overrides)} correction entries); "
                 "i/r/c = lineages it reads as improved / regressed / crossed, so every regression conclusion is False and ``never regressed'' matches it perfectly; survival = exact probability "
                 "that the per-text replay reproduces the reference conclusion (agreement with the reference, not accuracy); min.\\ = lowest covered lineage."), ""])
    RB, RP = remedies["baselines"], remedies["pools"]
    def rrow(r, label):
        st = r["stability"]; dx, dn = r["detected_expected_of_evaluable"]; ax, an = r["accepted_expected_of_evaluable"]
        return (f"  {label} & {fnum(r['cost_ratings_per_lineage'])} & {pct(r['abstention_rate_checkpoints'], 0)} & " + " & ".join(fmt(st[c]) for c in CONCS)
                + f" & {fnum(dx)}/{dn} & {fnum(ax)}/{an} & {fmt(r['false_change_identical_texts'])} & {fmt(r['false_change_same_defect_pair'])} \\\\")
    blocks = []
    for pn in POOLS:
        rp = RP[pn]; nc = rp["procedures"]["cached"]["false_change_identical_texts_n_covered_pairs"]
        blocks += ["  \\midrule", f"  \\multicolumn{{10}}{{@{{}}l}}{{\\emph{{{POOLS[pn]['name']} pool{' (adaptive workflow)' if pn == 'glm' else ''}}}: {rp['n_covered_lineages']}/{len(app)} lineages, "
                   f"{nc} identical pairs, {rp['n_positive_pairs_evaluable']}/{len(pos_pairs)} positive pairs evaluable ({rp['n_positive_pairs_evaluable_before_already_S2']} start at $S{{=}}2$)}} \\\\"]
        blocks += [rrow(rp["procedures"][p], TABLE_LABEL[p]) for p in PROCS if p not in NO_MODEL]
    t_rem = "\n".join([
        "% generated by scripts/conclusion_sensitivity.py -- procedures enumerated exactly from each same-model rating pool (re-rating + repeats) and two no-model baselines",
        "% cost = ratings per applicable lineage (mean; a rating-count comparison, not a matched budget); stability = P(two independent runs agree), covered lineages;",
        "% detects = expected number of evaluable positive pairs with S_after > S_before (strict increase); accepts = with S_after = 2 (constant S=2 accepts every pair);",
        f"% false change = P(S differs) on covered identical-text pairs and on the same-defect P6 pair ({REF_NAME} S = 1 and 1); -- = too few covered",
        "\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{@{}lrrccccccc@{}}", "  \\toprule",
        "  & ratings & abstain & \\multicolumn{3}{c}{stability} & detects & accepts & \\multicolumn{2}{c}{false change} \\\\",
        "  \\cmidrule(lr){4-6}\\cmidrule(lr){7-8}\\cmidrule(lr){9-10}",
        "  Procedure & /lineage & (ckpt.) & improved & regressed & crossing & ($S$ rises) & ($S{=}2$ after) & identical & same defect \\\\", "  \\midrule",
        rrow(RB["none"], TABLE_LABEL["none"]), rrow(RB["constant2"], TABLE_LABEL["constant2"]), *blocks, "  \\bottomrule", "\\end{tabular}",
        note_par(f"Costs are rating counts per lineage (a comparison, not a matched budget: calls differ in thinking and token use). Detects = expected number of evaluable independently "
                 f"supported pairs whose later text scores strictly higher; accepts = whose later text scores $S{{=}}2$; {n_closed} of the {len(pos_pairs)} pairs start from a text already at "
                 f"$S{{=}}2$ in the {REF_NAME} layer, so constant $S{{=}}2$ accepts every pair and detects none. Same-defect false change is exactly 0.5 under every Claude procedure "
                 "(pools [1,1,2,1] and [1,2,2,1])."), ""])
    sr = sources["repeat_variability"]; rc = sources["rubric_choice"]; ic = sources["inconsistent_correction"]
    def qrows(pn):
        s_ = sr[pn]
        first = (f"  repeat variability & {s_['name']} same-text $S$ disagreement, fixed-setting / mixed-mode / all pairs (adaptive workflow, {s_['texts']} texts) & "
                 f"{s_['fixed_differ']}/{s_['fixed_pairs']} / {s_['mixed_differ']}/{s_['mixed_pairs']} / {s_['pairs_differ']}/{s_['pairs']} \\\\" if pn == "glm" else
                 f"  repeat variability & {s_['name']} same-text $S$ disagreement, fixed setting ({s_['pairs']} pairs, {s_['texts']} texts) & {s_['pairs_differ']}/{s_['pairs']} ($q{{=}}{fmt(s_['q_fixed'])}$) \\\\")
        return [first, f"   & {s_['name']} lower / upper field disagreement, all pairs & {fmt(s_['q_lower_field'])} / {fmt(s_['q_upper_field'])} \\\\"]
    t_src = "\n".join([
        "% generated by scripts/conclusion_sensitivity.py -- sources of instability (item 6; the paper uses the macro \\SOURCESTXT); a taxonomy, not a statistical decomposition",
        "\\begin{tabular}{@{}llr@{}}", "  \\toprule", "  Source & Measure & Value \\\\", "  \\midrule", *qrows("glm"), *qrows("claude"),
        *[f"  evaluator choice & Cohen's $\\kappa$ on $S$, {name} ($n{{=}}{shipped[name]['all'].get('n', '--')}$) & {fmt(shipped[name]['all'].get('kappa'))} \\\\" for name in KAPPA_PAIRS],
        f"  rubric choice & $\\kappa$ range over evaluator pairs, P2 vs.\\ P3/P6 & {fmt(k2[0])}--{fmt(k2[1])} vs.\\ {fmt(k36[0])}--{fmt(k36[1])} \\\\",
        f"   & P2 lineages route N/A of {rc['p2_lineages']}; of these, $S$ vs.\\ grade would disagree & {rc['p2_route_na']}; {rc['p2_route_na_S_final_vs_grade_disagree']} \\\\",
        f"  inconsistent correction & regressing P6 lineages, correction entries applied to none / final file only / all ({REF_NAME}) & {ic['none']['n_regressing']} / {ic['final_only']['n_regressing']} / {ic['all']['n_regressing']} \\\\",
        "  \\bottomrule", "\\end{tabular}", ""])
    EV_ROWS = [L for L in ("raw",) + FOUR + ("written", "majority3") if L in ALL_LAYERS]
    def erow(L):
        cells = [f"  {EVAL_SHORT[L]}"]
        for prob in PROBS + ("all",):
            ec = survival["evaluator_choice"][prob][L]
            cells += [(f"{ec[c]['equal_valid']}/{ec[c]['evaluable']}" if ec[c]["evaluable"] else "--") for c in CONCS]
        return " & ".join(cells) + " \\\\"
    t_ev = "\n".join([
        f"% generated by scripts/conclusion_sensitivity.py -- evaluator choice: lineages whose conclusion under the layer equals the {REF_NAME} conclusion / lineages where the layer is complete",
        "\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{@{}lccccccccc ccc@{}}", "  \\toprule",
        "  & \\multicolumn{3}{c}{P3} & \\multicolumn{3}{c}{P6} & \\multicolumn{3}{c}{P2$^{\\mathrm{s}}$} & \\multicolumn{3}{c}{all} \\\\",
        "  \\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\\cmidrule(lr){8-10}\\cmidrule(lr){11-13}",
        "  Layer & impr. & regr. & cross. & impr. & regr. & cross. & impr. & regr. & cross. & impr. & regr. & cross. \\\\", "  \\midrule",
        *[erow(L) for L in EV_ROWS], "  \\bottomrule", "\\end{tabular}",
        note_par(f"Each cell: lineages whose conclusion under the layer equals the {REF_NAME} conclusion / lineages where the layer rates every checkpoint."), ""])
    AL = alarm_res["per_problem"]; AA = alarm_res; CD, DD, NR = AA["credited_defective"], AA["documented_defective"], AA["flags_without_record"]
    def arow(prob):
        a = AL[prob]; r = a["S_disagree"]
        return (f"  {PN[prob]} & {a['texts']} & {a['documented_texts']} & {a['evidence_texts']} & {r['flagged']} & {r['hits_of_evidence']} & {r['hits_of_documented']} & "
                f"{r['flags_of_texts_without_record']} \\\\")
    EVN = {"glm": "GLM", "kimi": "Kimi", "claude": "Claude", "gpt": "GPT", "rep1": "GLM rep.~1"}
    def rec_txt(d): return "; ".join(("correction entry" if s.endswith("validity_overrides.json") else f"public grade {d['public_score']}/7") for s in d["sources"])
    def drow(d):
        return (f"  {esc(d['id'])} & P{d['problem']} & {rec_txt(d)} & " + " & ".join("--" if d["S"].get(e) is None else str(d["S"][e]) for e in ALARM_EVALS)
                + f" & {yn(d['credited_defective'])} & {yn(d['S_disagree'])} \\\\")
    same_rule = AL["all"]["field_2_vs_lt2"]["flagged_record_ids"] == AL["all"]["S_disagree"]["flagged_record_ids"]
    n_gpt_texts, n_rep_texts = sum("gpt" in t["S"] for t in app_texts), sum("rep1" in t["S"] for t in app_texts)
    t_alarm = "\n".join([
        "% generated by scripts/conclusion_sensitivity.py -- disagreement as an alarm (item 7): distinct texts of applicable lineages (route-N/A P2 excluded);",
        "% evaluators = GLM-5.3 re-rating, Kimi K3, Claude Opus 5, GPT-5.6-Sol (P3/P6) and the GLM-5.3 repeat rep1 where present; flag = the evaluators present do not all give the same S;",
        f"% documented = every correction entry + every public final of an applicable lineage with a released public grade <= {PUBLIC_FAIL_MAX}/7 (systematic ascertainment);",
        "% credited = documented and some evaluator gives S=2 (the alarm's target); flags among = flagged / texts of the group; no record = neither a correction entry nor a failing",
        "% public grade (unexamined, not known negatives). Second block: every documented-defective text with its S profile (counts, not rates)",
        "\\setlength{\\tabcolsep}{4pt}\\begin{tabular}{@{}lrrrrrrr@{}}", "  \\toprule",
        "  & & \\multicolumn{2}{c}{defective texts} & & \\multicolumn{3}{c}{flags among} \\\\", "  \\cmidrule(lr){3-4}\\cmidrule(lr){6-8}",
        "  Problem & texts & documented & credited & flagged & credited & documented & no record \\\\", "  \\midrule",
        arow("3"), arow("6"), arow("2"), "  \\midrule", arow("all"), "  \\bottomrule", "\\end{tabular}", "\\par\\smallskip",
        "\\setlength{\\tabcolsep}{3.5pt}\\begin{tabular}{@{}lllcccccccc@{}}", "  \\toprule",
        "  & & & \\multicolumn{5}{c}{$S$ by evaluator} & & \\\\", "  \\cmidrule(lr){4-8}",
        "  Documented-defective text & P & record & " + " & ".join(EVN[e] for e in ALARM_EVALS) + " & credited & flag \\\\", "  \\midrule",
        *[drow(d) for d in doc_sorted if d.get("applicable")], "  \\bottomrule", "\\end{tabular}",
        note_par(f"Evaluators: GLM-5.3 re-rating, Kimi~K3, Claude Opus~5, GPT-5.6-Sol (P3/P6) and the GLM-5.3 repeat where present (-- = not rated). Documented = every correction entry of "
                 f"validity\\_overrides.json plus every public final file of an applicable lineage whose released public grade is at most {PUBLIC_FAIL_MAX} of 7 (P3 from the released grader "
                 f"receipt, P6 from the released grade table; every model, any wording): {DD['n']} texts. Credited = documented and rated $S{{=}}2$ by at least one evaluator ({CD['n']} texts "
                 f"carrying {CD['distinct_defects']} distinct defects; the two P6 GPT-default texts share one false lemma): the alarm's target, since a text every evaluator rates $S{{<}}2$ is "
                 f"visible without an alarm. The field-level rule (a field scored 2 by one evaluator and $<2$ by another) flags {AL['all']['field_2_vs_lt2']['flagged']} texts"
                 f"{', the same ones' if same_rule else ''}. Counts, not rates: texts without a record are unexamined, not known negatives."), ""])
    EVN2 = {"glm": "GLM", "kimi": "Kimi", "claude": "Claude", "gpt": "GPT", "rep1": "GLM repeat"}
    def pair_name(E): return "--".join(EVN2[e] for e in E)
    def pairrow(name, p):
        return (f"  {name} & {p['n_texts']} & {p['flags']} & {p['credited_hits']}/{p['credited_n']} & {p['documented_hits']}/{p['documented_n']} & "
                f"{p['flags_without_record']}/{p['texts_without_record']} \\\\")
    t_pairs = "\n".join([
        "% generated by scripts/conclusion_sensitivity.py -- pair sensitivity of the disagreement alarm (item 7): applicable texts rated by at least two evaluators of the set;",
        "% flag = the set's evaluators present do not all give the same S; credited / documented / no record as in table_alarm.tex (counts, not rates); GPT rated P3/P6 only",
        "\\setlength{\\tabcolsep}{4pt}\\begin{tabular}{@{}lrrrrr@{}}", "  \\toprule",
        "  & & & \\multicolumn{3}{c}{flags among} \\\\", "  \\cmidrule(lr){4-6}",
        "  Evaluator set & texts & flagged & credited & documented & no record \\\\", "  \\midrule",
        *[pairrow(pair_name(E), pairs["-".join(E)]) for E in ALARM_PAIRS if "rep1" not in E], "  \\midrule",
        *[pairrow(pair_name(E), pairs["-".join(E)]) for E in ALARM_TRIPLES], "  \\midrule",
        pairrow("four single evaluators", pairs["-".join(FOUR)]), pairrow("four single evaluators + GLM repeat (the rule above)", pairs["all"]),
        pairrow("GLM re-rating against its repeat", pairs["glm-rep1"]), "  \\bottomrule", "\\end{tabular}",
        note_par(f"A text counts for a set when at least two of its evaluators rated it (GPT-5.6-Sol rated the {n_gpt_texts} P3/P6 texts, the GLM-5.3 repeat {n_rep_texts} texts, the others "
                 f"all {len(app_texts)}), so a set containing GPT reduces to its other members on P2. Credited = flagged credited-defective texts / credited-defective texts the set rated; "
                 f"documented and no record likewise. Counts, not rates: with {CD['n']} credited-defective texts the differences between sets are a handful of texts."), ""])

    # ---- macros (at most three sentences each) --------------------------------------------------------------------
    n_all = S["all"]["n_lineages"]; idn = S["all"]["identical_across_evaluators"]; pv = S["all"]["reference_prevalence"]
    PNAME = {pn: POOLS[pn]["name"].replace(" 5", "~5") for pn in POOLS}
    ANN = {"glm-5.3": "GLM-5.3 re-rating", "kimi-k3": "Kimi~K3", "claude-opus-5": "Claude Opus~5", "gpt-5.6-sol": "GPT-5.6-Sol"}
    eval_names = [ANN.get(live_annot.get(e), esc(live_annot.get(e) or e)) + (" on P3/P6" if e == "gpt" else "") for e in FOUR]
    sg, sc = sr["glm"], sr["claude"]
    def comp_txt(pn):
        c = completion[pn]; cp = c["repeat_ratings_parsed"]; passes = [p for p in ("rep1", "rep2", "rep3") if any(cp[pr][p] for pr in cp)]
        if not passes: return f"{PNAME[pn]}: no repeats"
        per = [" + ".join(f"{cp[pr][p]} {pr}" for pr in cp if cp[pr][p]) for p in passes]
        body = (f"{passes[0]} only, {per[0]} texts" if len(passes) == 1 else f"{nword(len(passes))} repeats of {per[0]} texts" if len(set(per)) == 1
                else "; ".join(f"{p}: {x} texts" for p, x in zip(passes, per)))
        return f"{PNAME[pn]}: {body}, {c['repeat_ratings_total']} repeat ratings"
    REPLAYQ = f"{fmt(QF['glm'])} / {fmt(QF['claude'])}"
    vt = [t for t in sg["variable_texts"]]
    vt_txt = "; ".join(f"P{t['problem']} {esc(t['record_ids'][0])}: " + " against ".join(f"{r['mode']} $S{{=}}{r['S']}$" for r in t["ratings"]) for t in vt) or "none"
    REPLAYQTXT = (f"Same-text disagreement on $S$: {PNAME['glm']}, {sg['fixed_differ']} of {sg['fixed_pairs']} fixed-setting pairs ({sg['fixed_primary_pairs']} thinking--thinking, "
                  f"{sg['fixed_fallback_pairs']} fallback--fallback) and {sg['mixed_differ']} of {sg['mixed_pairs']} mixed-mode pairs ({vt_txt}), hence {sg['pairs_differ']} of {sg['pairs']} "
                  f"for the adaptive thinking-then-fallback workflow as run; {PNAME['claude']}, {sc['pairs_differ']} of {sc['pairs']} fixed-setting pairs on {sc['texts']} texts "
                  f"($q{{=}}{fmt(sc['q_fixed'])}$). Completed repeats at freeze: {comp_txt('glm')}; {comp_txt('claude')}. GLM-5.3's one disagreement is a change of thinking mode, "
                  f"not fixed-setting stochastic variation, so every lineage covered by its pool has a deterministic pool"
                  f"{'' if all(l['pool_deterministic']['glm'] for l in app if l['covered']['glm']) else ' except where noted in results.json'}.")
    def flip_desc(f):
        groups = {}
        for pv_ in f["pivot_texts"]: groups.setdefault(pv_["split"], []).append(esc(pv_["label"]))
        txt = "; ".join(f"{join_and(lbls)}: {split}" for split, lbls in groups.items()) or "single-evaluator ratings identical, a layer-0 or repeat rating differs"
        return f"P{f['problem']} {esc(f['lineage'])} ({txt}; flips {join_and(f['conclusions'])})"
    flip_txt = "; ".join(flip_desc(f) for f in survival["flips"][:5]) + (f"; and {len(survival['flips']) - 5} more" if len(survival["flips"]) > 5 else "")
    abn = survival["agree_but_not_valid"]
    def agg_diff_txt(L):
        d = survival["aggregation_vs_valid"][L]
        return f"{nword(len(d))} lineage{plural(len(d))}" + (" (" + "; ".join(f"P{x['problem']} {esc(x['lineage'])}: {', '.join(x['conclusions'])}" for x in d) + ")" if d else "")
    def surv_frag(pn, prob):
        r = S[prob]["replay"][pn]; sv = r["survival_text_vs_valid"]; n = S[prob]["n_lineages"]
        if sv["improved"] is None: return f"the {PNAME[pn]} pool is not reportable ({r['n_covered']} of {n} lineages covered)"
        return f"{fmt(sv['improved'])}/{fmt(sv['regressed'])}/{fmt(sv['crossing'])} with the {PNAME[pn]} pool ({r['n_covered']} of {n} covered)"
    SURVIVALTXT = (f"Under layer~0, the four single evaluators ({join_and(eval_names)}) and every completed same-model repeat ({comp_txt('glm')}; {comp_txt('claude')}), the improved, "
                   f"regressed and first-crossing conclusions are identical for {idn['improved']}, {idn['regressed']} and {idn['crossing']} of the {n_all} applicable lineages"
                   + (f"; the flips are {flip_txt}" if survival["flips"] else "") + ". "
                   f"Among the aggregation layers, written differs from {REF_NAME} for {agg_diff_txt('written')} and majority of three for {agg_diff_txt('majority3')}"
                   + (f"; for {nword(len(abn))} lineage{plural(len(abn))} ({', '.join('P' + a['problem'] + ' ' + esc(a['lineage']) for a in abn)}) every single evaluator agrees and only the "
                      f"correction entries change the conclusion" if abn else "") + ". "
                   f"Under exact enumeration of the per-text replay (every distinct text's $S$ redrawn from its same-model pool; {PNAME['glm']} pool = the adaptive workflow as run, "
                   f"$q{{=}}{sg['fixed_differ']}/{sg['fixed_pairs']}$ on fixed-setting and ${sg['mixed_differ']}/{sg['mixed_pairs']}$ on mixed-mode pairs; {PNAME['claude']} $q{{=}}{fmt(sc['q_fixed'])}$), "
                   f"the {REF_NAME} improved/regressed/crossing conclusions survive with mean probability: Problem~3, {surv_frag('glm', '3')} and {surv_frag('claude', '3')}; "
                   f"Problem~6, {surv_frag('glm', '6')} and {surv_frag('claude', '6')}; Problem~2, no repeats by protocol.")
    def frag_desc(pn):
        fr = survival["fragile_lineages"][pn]
        if not fr: return f"below 1 for no lineage with the {PNAME[pn]} pool"
        items = []
        for f in fr:
            s_ = f"P{f['problem']} {esc(f['lineage'])} {'/'.join(fmt(f['survival_text_vs_valid'][c]) for c in CONCS)}"
            if min(f["survival_text_vs_valid"].values()) == 0 and f["texts_where_pool_differs_from_reference"]:
                s_ += " (" + "; ".join(f"{esc(t['label'])}: pool $S\\in\\{{{','.join(map(str, sorted(set(t['pool_S']))))}\\}}$, reference {t['reference_S']}"
                                       for t in f["texts_where_pool_differs_from_reference"]) + ")"
            items.append(s_)
        return f"with the {PNAME[pn]} pool, " + ", ".join(items)
    SURVIVALREFTXT = (f"The {REF_NAME} reference reads improved for {pv['improved']}, regressed for {pv['regressed']} and a first crossing for {pv['crossing']} of the {n_all} lineages, so a rule that "
                      f"always reports ``no regression'' matches every regression conclusion, and the means hide the affected lineages, whose improved/regressed/crossing survival is below 1: "
                      f"{frag_desc('glm')}; {frag_desc('claude')} (a 0 means the pool never reproduces the reference conclusion, because it rates the text in parentheses the other way). "
                      f"Survival is agreement with an author-maintained, partly model-derived corrected reference (the written GLM$\\cap$Kimi layer with {len(overrides)} correction entries), "
                      f"not out-of-sample accuracy. The units are nested (Claude's {sc['pairs']} same-text pairs are six dependent pairs on each of {sc['texts']} texts; lineages share problems and "
                      f"model families), the replay distribution is enumerated exactly from pools of two or four ratings per text, and the $B{{=}}{B}$ Monte Carlo cross-check "
                      f"(maximum deviation {fmt(mc['max_abs_diff_survival_text_vs_ref'], 3)}) adds precision only, never evaluator evidence.")
    ob = effect["observed_layer0"]; sp = ob["spearman_k_vs_apparent_up"]; assoc = sp["perm_p"] is not None and sp["perm_p"] < 0.05
    rho_txt = "no event to correlate" if sp["rho"] is None else f"Spearman $\\rho{{=}}{sp['rho']}$, permutation $p{{=}}{sp['perm_p']}$"
    ev_txt = "; ".join(f"P{e['problem']} {esc(e['lineage'])} at {join_and(esc(w) for w in e['at'])}" for e in ob["events"]) or "none"
    def null_frag(pn):
        e = effect["pools"][pn]; sm = e["summary"]
        if not sm: return f"not estimable with the {PNAME[pn]} pool ({e['n_covered_lineages']} covered lineages with at least two checkpoints)"
        if not sm["nonzero_lineages"]:
            return (f"0 for all {sm['n_covered']} lineages covered by the {PNAME[pn]} pool"
                    + (" (every covered text has a deterministic pool)" if sm["n_covered_deterministic_pool"] == sm["n_covered"] else ""))
        nz = join_and(f"{fmt(x['p_apparent_up'], 3)} for P{x['problem']} {esc(x['lineage'])} ($k{{=}}{x['k']}$)" for x in sorted(sm["nonzero_lineages"], key=lambda x: -x["p_apparent_up"]))
        return (f"0 for {sm['n_covered_zero']} of the {sm['n_covered']} lineages covered by the {PNAME[pn]} pool, {nz}, a mean of {fmt(sm['p_up_mean_k_ge3'], 3)} over the "
                f"{sm['n_k_ge3']} covered lineages with $k{{\\ge}}3$")
    def heur(pn, k): v = effect["pools"][pn]["by_k"].get(str(k)); return fmt(v[f"heuristic_up_draw_q_1-(1-q/2)^(k-1)"], 3) if v else "--"
    CHECKPOINTEFFECTTXT = (f"In the observed record layer~0 contains {ob['apparent_up_transitions_total']} up-transition{plural(ob['apparent_up_transitions_total'])} absent from the {REF_NAME} layer "
                           f"({ob['lineages_with_any']} of {ob['n_lineages']} lineages: {ev_txt}) and {ob['identical_text_changes_total']} change{plural(ob['identical_text_changes_total'])} between "
                           f"identical adjacent texts, with {'an' if assoc else 'no detectable'} association between lineage length and apparent progress ({rho_txt}); the design compares "
                           f"different lineages of different lengths, texts and models, not one lineage thinned to different $k$, so it cannot isolate a checkpoint-count effect. "
                           f"Under the replay null (independent same-model draws per checkpoint, texts fixed; exact enumeration) the probability of at least one apparent up-transition is "
                           + null_frag("glm") + ", and " + null_frag("claude") + ". "
                           f"The expression $1-(1-q/2)^{{k-1}}$ is only a heuristic (constant up-probability $q/2$ at every adjacent pair, independent adjacent events, no reference exclusion): "
                           f"with the with-replacement disagreement the replay actually draws ({fmt(QD['glm'], 4)} for {PNAME['glm']}, {fmt(QD['claude'], 4)} for {PNAME['claude']}; the pairwise "
                           f"$q$ of {fmt(Q['glm'], 4)} and {fmt(Q['claude'], 4)} counts each observed pair once) it gives {heur('claude', 3)} at $k{{=}}3$ and {heur('claude', 5)} at $k{{=}}5$ "
                           f"for the {PNAME['claude']} pool, not the exact per-lineage values above.")
    def cnt_of(pn, p, key): ex_, of = (RB if p in NO_MODEL else RP[pn]["procedures"])[p][f"{key}_expected_of_evaluable"]; return f"{fnum(ex_)} of {of}"
    def st_txt(pn, p): return "/".join(fmt(RP[pn]["procedures"][p]["stability"][c]) for c in CONCS)
    def both(f, sep=" and "): return sep.join(f(pn) for pn in POOLS)
    det_proc_same = all(len({RP[pn]["procedures"][p]["detected_expected_of_evaluable"][0] for p in PROCS if p not in NO_MODEL}) == 1 for pn in POOLS)
    det_pairs = [pp for pp in pos_pairs if pp["S_ref"][0] != 2]
    label_of = {(l["problem"], i): lb for l in lins for i, lb in zip(l["ids"], l["labels"])}
    def lbl(prob, ident): return esc(label_of.get((prob, ident), ident))
    grp = defaultdict(list)
    for pp in det_pairs: grp[(pp["problem"], pp["lineage_before"], pp["before"], pp["S_ref"][0])].append(pp)
    det_pairs_txt = ("; ".join(f"P{p} {esc(lin)} ({lbl(p, b)}, $S{{=}}{s0}$, to {join_and(lbl(p, x['after']) for x in xs)}, "
                               f"$S{{=}}{'/'.join(str(v) for v in sorted({x['S_ref'][1] for x in xs}))}$)" for (p, lin, b, s0), xs in grp.items()) or "no pair")
    REMEDIESTXT = (f"Caching one rating per distinct text costs {fnum(cost['cached'])} ratings per lineage against {fnum(cost['per_checkpoint'])} for one rating per checkpoint (a rating-count "
                   f"comparison, not a matched budget: calls differ in thinking and token use), makes an identical-text change impossible (one rating per checkpoint: expected false-change rate "
                   f"{both(lambda pn: fmt(RP[pn]['procedures']['per_checkpoint']['false_change_identical_texts']))} on the identical-text controls with the {both(lambda pn: PNAME[pn])} pools), "
                   f"and accepts the later text of the evaluable independently supported pairs at {both(lambda pn: cnt_of(pn, 'cached', 'accepted'))}, exactly as the no-model constant-$S{{=}}2$ "
                   f"baseline does ({cnt_of('glm', 'constant2', 'accepted')}), because {n_closed} of the {len(pos_pairs)} pairs are repairs of a text already at $S{{=}}2$ in the {REF_NAME} layer "
                   f"and test acceptance, not detection. "
                   f"Strict improvement detection ($S$ rises between the paired texts) is {both(lambda pn: cnt_of(pn, 'cached', 'detected'))} with the {both(lambda pn: PNAME[pn])} pools"
                   f"{' under every rating procedure' if det_proc_same else ''}, {'both' if len(det_pairs) == 2 else 'all'} from {det_pairs_txt}, and "
                   f"{cnt_of('glm', 'none', 'detected')} and {cnt_of('glm', 'constant2', 'detected')} for the no-rating and constant-$S{{=}}2$ baselines. "
                   f"Majority of three per text ({fnum(cost['majority3_text'])} ratings per lineage) gives conclusion stability (improved/regressed/crossing) {both(lambda pn: st_txt(pn, 'majority3_text'))} "
                   f"against {both(lambda pn: st_txt(pn, 'cached'))} for one rating per text, at a checkpoint abstention rate of "
                   f"{both(lambda pn: pct(RP[pn]['procedures']['majority3_text']['abstention_rate_checkpoints']))}; the no-rating baseline is perfectly stable, detects nothing and accepts nothing, "
                   f"so stability is only meaningful next to detection.")
    SAMEDEFECTTXT = ""
    if defect:
        ex_c = defect.get("exact", {}).get("claude"); dg = defect["detections_elsewhere"]; og = dg["ordinary_grades"]
        pa, pb = defect["pools"]["claude"]["a"], defect["pools"]["claude"]["b"]
        def frac(x): return {0.25: "1/4", 0.5: "1/2", 0.75: "3/4", 1.0: "1"}.get(round(x, 4), fmt(x, 3))
        if ex_c:
            PA2, PB2 = 1 - ex_c["P_S"]["a"].get("1", 0), 1 - ex_c["P_S"]["b"].get("1", 0)
            alg = (f"independent draws disagree with probability $1-({frac(1 - PA2)}\\cdot{frac(1 - PB2)}+{frac(PA2)}\\cdot{frac(PB2)})={frac(ex_c['single_draw_disagreement'])}$ exactly, and because "
                   f"majority of three still returns $S{{=}}2$ for the second text with probability {frac(1 - ex_c['P_majority3']['b'].get('1', 0))}, it keeps the disagreement at exactly "
                   f"{frac(ex_c['majority3_disagreement'])} whatever the first text's distribution (the table's identical values under every procedure are this identity, not four measurements)")
        else: alg = "the Claude Opus~5 pool does not cover the pair"
        gl = defect["pools"]["glm"]
        glm_txt = (f"the {PNAME['glm']} pool does not cover it (turn~9: {' and '.join(f'{m} $S{{=}}{s}$' for m, s in zip(gl['a_modes'], gl['a']))}; final file: "
                   f"{' and '.join(f'{m} $S{{=}}{s}$' for m, s in zip(gl['b_modes'], gl['b']))})") if not gl["covered"] else f"the {PNAME['glm']} pool gives {fmt(defect['exact']['glm']['single_draw_disagreement'])}"
        cg = og.get("claude", {}); gg = og.get("glm", {})
        def grades_txt(g):
            vals = [g[x]["grade"] for x in (da, db) if x in g]
            return "no grade" if not vals else (f"both texts {vals[0]} of 7" if len(vals) == 2 and vals[0] == vals[1] else " and ".join(map(str, vals)) + " of 7")
        rn = (dg["glm_thinking_repeat_rep1_notes"].get(da) or "").lower(); cgap = " ".join(cg[x]["main_gap"].lower() for x in cg)
        det_txt = (f"the GLM-5.3 thinking repeat rates turn~9 $S{{=}}{dg['glm_thinking_repeat_rep1_S'][da]}$" + (", its notes calling the lemma false" if "false" in rn else "")
                   + f", and Claude Opus~5's ordinary grader gives {grades_txt(cg)}" + (" with the false lemma as the main gap" if "false" in cgap else "")
                   + (f" (GLM-5.3's ordinary grader: {grades_txt(gg)})" if gg else ""))
        SAMEDEFECTTXT = (f"On the same-defect P6 pair (turn~9 and the final file of the public GPT-default lineage, both resting on the refuted finiteness lemma; {REF_NAME} $S{{=}}{defect['valid_S'][0]}$ "
                         f"and {defect['valid_S'][1]}, so the control fixes that target, not identical quality of two different texts) the {PNAME['claude']} pools are "
                         f"$[{','.join(map(str, pa))}]$ and $[{','.join(map(str, pb))}]$: {alg}. {glm_txt[0].upper() + glm_txt[1:]}. "
                         f"The conclusion is narrow, that majority voting of this rater does not cure this error, not that repeated grading cannot supply validity: {det_txt}.")
    def qfrag(pn):
        s_ = sr[pn]; fl = f"; lower/upper fields differ on {pct(s_['q_lower_field'], 0)}/{pct(s_['q_upper_field'], 0)} of pairs" if s_["pairs"] else ""
        if pn == "glm":
            return (f"{s_['fixed_differ']} of {s_['fixed_pairs']} fixed-setting pairs for {PNAME[pn]} ({s_['mixed_differ']} of {s_['mixed_pairs']} mixed thinking--fallback pairs, "
                    f"{s_['pairs_differ']} of {s_['pairs']} for the adaptive workflow as run, on {s_['texts']} texts{fl})")
        return f"{s_['pairs_differ']} of {s_['pairs']} fixed-setting pairs ($q{{=}}{fmt(s_['q_fixed'])}$) for {PNAME[pn]} on {s_['texts']} texts{fl}"
    kp = lambda name: f"{name.replace('-', '--')} {fmt(shipped[name]['all'].get('kappa'))}"
    SOURCESTXT = (f"repeat variability: same-text disagreement on $S$ is {qfrag('glm')} and {qfrag('claude')}. Evaluator choice: pairwise $\\kappa$ on $S$ over the 156 texts is "
                  f"{kp('GLM-Kimi')}, {kp('GLM-Claude')} and {kp('Kimi-Claude')}, and {kp('GLM-GPT')} on the {shipped['GLM-GPT']['all'].get('n', '--')} P3/P6 texts GPT rated; rubric fit: on P2 the same pairs give "
                  f"$\\kappa{{=}}{fmt(k2[0])}$--{fmt(k2[1])} against {fmt(k36[0])}--{fmt(k36[1])} on P3/P6, and the route policy removes {rc['p2_route_na']} of {rc['p2_lineages']} P2 lineages, "
                  f"{rc['p2_route_na_S_final_vs_grade_disagree']} of which would otherwise disagree with their grade. Inconsistent correction: the P6 correction entries applied to the final GPT-5.6-Sol file alone "
                  f"(as in v3) leave {ic['final_only']['n_regressing']} regressing P6 lineage{plural(ic['final_only']['n_regressing'])}, applied to all three refuted texts {ic['all']['n_regressing']}, "
                  f"applied to none {ic['none']['n_regressing']}.")
    A = AL["all"]; aS, aF = A["S_disagree"], A["field_2_vs_lt2"]
    cred_names = join_and(f"P{t['problem']} {esc(t['record_ids'][0])}" for t in cred_texts) or "none"
    norec_names = "; ".join(f"P{p} {join_and(esc(t['record_ids'][0]) for t in norec_flags if t['problem'] == p)}" for p in PROBS if any(t["problem"] == p for t in norec_flags)) or "none"
    def miss_txt():
        parts = []
        for p in PROBS:
            ms = [d for d in doc_sorted if d.get("applicable") and d["problem"] == p and not d["S_disagree"]]
            if not ms: continue
            groups = defaultdict(list)
            for d in ms: groups[tuple(sorted(set(d["S"].values())))].append(d)
            frags = []
            for sv, ds in groups.items():
                gs = [d["public_score"] for d in ds]
                if all(g is None for g in gs): grade = "correction entry"
                elif any(g is None for g in gs): grade = "correction entry or public grade " + join_and(str(g) for g in gs if g is not None) + " of 7"
                elif len(gs) > 1 and len(set(gs)) == 1: grade = f"public grade {gs[0]} of 7 each"
                else: grade = f"public grade{plural(len(gs))} {join_and(map(str, gs))} of 7"
                frags.append(f"{join_and(esc(d['id']) for d in ds)}, {grade}, $S{{=}}{'/'.join(map(str, sv))}$ by every evaluator")
            parts.append(f"P{p} " + "; ".join(frags))
        return "; ".join(parts) or "none"
    cov_txt = f"all {CD['n']} credited-defective texts" if CD["hits"] == CD["n"] else f"{CD['hits']} of the {CD['n']} credited-defective texts"
    same_defect_note = ", the two P6 GPT-default texts sharing one false lemma" if CD["distinct_defects"] < CD["n"] else ""
    ALARMTXT = (f"Disagreement as an alarm: the target is the credited-defective text, one with a documented defect (a correction entry, that is an independent refutation or a recorded fatal "
                f"invalid step, or a public final file whose released public grade is at most {PUBLIC_FAIL_MAX} of 7) that at least one evaluator nevertheless rates $S{{=}}2$, because a text "
                f"every evaluator rates $S{{<}}2$ is visible to an operator without any alarm. Over the {A['texts']} distinct texts of the applicable lineages "
                f"({', '.join(f'{AL[p]['texts']} P{p}' for p in PROBS)}), the four single evaluators plus the GLM-5.3 repeat where present disagree on $S$ for {aS['flagged']} texts: {cov_txt} "
                f"({cred_names}; {CD['distinct_defects']} distinct defect{plural(CD['distinct_defects'])}{same_defect_note}), hence {DD['hits']} of the {DD['n']} documented-defective texts, the "
                f"{DD['n'] - DD['hits']} misses being never credited ({miss_txt()}), and {NR['n']} text{plural(NR['n'])} without any record ({norec_names}). These are counts, not rates: the "
                f"ascertainment is every correction entry plus every public final with a released grade of at most {PUBLIC_FAIL_MAX} (not a selected evidence set), texts without a record are "
                f"unexamined, not known negatives, and the field-level rule (some evaluator scores a field 2 where another scores it $<2$) flags {aF['flagged']} texts"
                f"{', the same ones' if same_rule else ''}.")
    def pair_frag(E):
        p = pairs["-".join(E)]; nt = f" on {p['n_texts']} texts" if p["n_texts"] != len(app_texts) else ""
        return f"{pair_name(E)} {p['credited_hits']} of {p['credited_n']} ({p['flags']} flag{plural(p['flags'])}{nt})"
    two = [E for E in ALARM_PAIRS if "rep1" not in E]
    full = [E for E in two if pairs["-".join(E)]["credited_hits"] == pairs["-".join(E)]["credited_n"]]
    worst = min(two, key=lambda E: pairs["-".join(E)]["credited_hits"]); pw = pairs["-".join(worst)]
    full_tri = [E for E in ALARM_TRIPLES if pairs["-".join(E)]["credited_hits"] == pairs["-".join(E)]["credited_n"]]
    gpt_tri = [E for E in ALARM_TRIPLES if "gpt" in E]
    tri_note = " (every triple containing GPT-5.6-Sol)" if full_tri and set(full_tri) == set(gpt_tri) else ""
    pr = pairs["glm-rep1"]
    ALARMPAIRTXT = (f"The recommendation to rate with at least two labs was tested above only as the union of four evaluators and a repeat; pair by pair, the credited-defective texts flagged "
                    f"are {', '.join(pair_frag(E) for E in two[:-1])}, and {pair_frag(two[-1])}, while the GLM-5.3 re-rating against its own repeat flags {pr['credited_hits']} of the "
                    f"{pr['credited_n']} credited-defective texts it covers ({pr['flags']} flag{plural(pr['flags'])} on {pr['n_texts']} texts). "
                    f"{join_and(pair_name(E) for E in full) if full else 'No pair'} reach{'es' if len(full) == 1 else ''} all {CD['n']} credited-defective texts and {pair_name(worst)} the fewest "
                    f"({pw['credited_hits']} of {pw['credited_n']}); {nword(len(full_tri))} of the {len(ALARM_TRIPLES)} triples reach all {CD['n']}{tri_note}, so which two labs are chosen "
                    f"decides the result, and with {CD['n']} target texts the differences between sets are a handful of texts, not rates.")
    TEXT_MACROS = {"SURVIVALTXT": SURVIVALTXT, "SURVIVALREFTXT": SURVIVALREFTXT, "REPLAYQ": REPLAYQ, "REPLAYQTXT": REPLAYQTXT, "CHECKPOINTEFFECTTXT": CHECKPOINTEFFECTTXT,
                   "REMEDIESTXT": REMEDIESTXT, "SAMEDEFECTTXT": SAMEDEFECTTXT, "SOURCESTXT": SOURCESTXT, "ALARMTXT": ALARMTXT, "ALARMPAIRTXT": ALARMPAIRTXT}
    sentences = {k: n_sentences(v) for k, v in TEXT_MACROS.items() if k != "REPLAYQ"}
    for k, n in sentences.items():
        if n > 3: problems.append(f"macro {k} has {n} sentences (limit 3)")
    macros = "\n".join(["% generated by scripts/conclusion_sensitivity.py -- do not edit; loaded by main.tex via \\InputIfFileExists{gen/sensitivity_macros}",
                        f"% exact enumeration; monte-carlo check replays={B} seed={args.seed} evaluators={','.join(single)} generated={results['meta']['generated_utc']}",
                        f"% REPLAYQ = fixed-setting same-text disagreement q, {POOLS['glm']['name']} / {POOLS['claude']['name']}; the {POOLS['glm']['name']} adaptive-workflow value is in REPLAYQTXT",
                        *[f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in TEXT_MACROS.items()],
                        "\\newcommand{\\SURVIVALTABLE}{" + t_surv.rstrip() + "}", "\\newcommand{\\REMEDIESTABLE}{" + t_rem.rstrip() + "}",
                        "\\newcommand{\\ALARMTABLE}{" + t_alarm.rstrip() + "}",
                        "% ALARMPAIRTABLE inputs the pair-sensitivity table; the path is relative to the repository root, where main.tex is compiled",
                        "\\newcommand{\\ALARMPAIRTABLE}{\\input{artifacts/conclusion_sensitivity/table_alarm_pairs.tex}}", ""])
    results["meta"]["runtime_sec"] = round(time.time() - t0, 2)
    results["meta"]["layout"] = {"flat_bundle": bundle, "macros_written": gen is not None}
    results["macros"] = TEXT_MACROS; results["macro_sentences"] = sentences

    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n")
    (out / "table_survival.tex").write_text(t_surv); (out / "table_remedies.tex").write_text(t_rem); (out / "table_sources.tex").write_text(t_src)
    (out / "table_evaluators.tex").write_text(t_ev); (out / "table_alarm.tex").write_text(t_alarm); (out / "table_alarm_pairs.tex").write_text(t_pairs)
    if gen is not None: gen.mkdir(parents=True, exist_ok=True); (gen / "sensitivity_macros.tex").write_text(macros)

    # ---- summary ----------------------------------------------------------------------------------------------------
    print(f"conclusion_sensitivity: exact enumeration (MC check B={B} seed={args.seed}) | {len(app)} applicable lineages ({len(lins) - len(app)} route-N/A excluded) | {results['meta']['runtime_sec']}s")
    print(f"  evaluators: {', '.join(single)} | aggregation layers: {', '.join(AGG)} | reference = {REF_NAME} (labels.json '{REF}', {len(overrides)} correction entries)"
          + (f" | labels.json layers not used: {', '.join(extra)}" if extra else ""))
    for prob in PROBS:
        c = coverage[prob]
        print(f"  P{prob}: {c['lineages_applicable']} lineages, {c['distinct_texts_applicable']} texts; single-evaluator ratings " + ", ".join(f"{e} {v}" for e, v in c["single_evaluator_ratings"].items()))
        for pn in POOLS:
            cp = c["pools"][pn]
            print(f"      {POOLS[pn]['name']:<14} pool: >=2 ratings {cp['texts_with_2plus_ratings']}, >=3 {cp['texts_with_3plus_ratings']}, 4 {cp['texts_with_4_ratings']}; re-rating fallbacks {cp['rerun_fallbacks']}; repeats: "
                  + (", ".join(f"rep{k[-1]} {v['parsed']} parsed/{v['pending']} pending/{v['unparsed']} unparsed/{v['fallback']} fallback" for k, v in cp["repeat_files"].items()) or "none by protocol"))
    for pn in POOLS:
        s_ = sr[pn]
        print(f"  q {POOLS[pn]['name']}: all pairs {s_['pairs_differ']}/{s_['pairs']} ({fmt(s_['q_workflow'])}) | fixed-setting {s_['fixed_differ']}/{s_['fixed_pairs']} ({fmt(s_['q_fixed'])}; "
              f"primary-primary {s_['fixed_primary_differ']}/{s_['fixed_primary_pairs']}, fallback-fallback {s_['fixed_fallback_differ']}/{s_['fixed_fallback_pairs']}) | mixed {s_['mixed_differ']}/{s_['mixed_pairs']} "
              f"| with-replacement draw disagreement {fmt(s_['draw_disagreement_mean'], 4)} | lower/upper {fmt(s_['q_lower_field'])}/{fmt(s_['q_upper_field'])} | completion: {comp_txt(pn).replace('~', ' ')}")
        for t in s_["variable_texts"]: print(f"      variable text P{t['problem']} {t['record_ids']}: " + ", ".join(f"{r['src']}={r['S']} ({r['mode']})" for r in t["ratings"]))
    print(f"1. SURVIVAL vs {REF_NAME} (identical across all evaluators | across the four | exact per-text replay survival mean (min) per pool | reference prevalence i/r/c)")
    for prob in PROBS + ("all",):
        s = S[prob]; idn_ = s["identical_across_evaluators"]; id4 = s["identical_across_four_single_evaluators"]; pv_ = s["reference_prevalence"]
        print(f"  P{prob:<3} n={s['n_lineages']:<2} identical {idn_['improved']}/{idn_['regressed']}/{idn_['crossing']} | four {id4['improved']}/{id4['regressed']}/{id4['crossing']} | "
              + " | ".join(f"{pn}: {'/'.join(fmt(s['replay'][pn]['survival_text_vs_valid'][c]) for c in CONCS)} (min {'/'.join(fmt(s['replay'][pn]['min_survival_text_vs_valid'][c]) for c in CONCS)}; cov {s['replay'][pn]['n_covered']})" for pn in POOLS)
              + f" | prevalence {pv_['improved']}/{pv_['regressed']}/{pv_['crossing']}")
    for f in survival["flips"]:
        print(f"  FLIP P{f['problem']} {f['lineage']}: " + "; ".join(f"{c}: " + ", ".join(f"{L}={conc_txt(c, f['values'][c][L])}" for L in f["evaluators_used"] + list(AGG)) for c in f["conclusions"]))
    for a in abn: print(f"  EVALUATORS AGREE, {REF_NAME.upper()} DIFFERS P{a['problem']} {a['lineage']}: {a['conclusions']} {a['values']}")
    for L in ("written", "majority3"): print(f"  {L} != {REF_NAME}: {[(x['problem'], x['lineage'], x['conclusions']) for x in survival['aggregation_vs_valid'][L]]}")
    print(f"  evaluator choice (equal to {REF_NAME} / evaluable, all problems): " + " | ".join(f"{L} " + "/".join(f"{survival['evaluator_choice']['all'][L][c]['equal_valid']}:{survival['evaluator_choice']['all'][L][c]['evaluable']}" for c in CONCS) for L in EV_ROWS))
    for pn in POOLS:
        for fr in survival["fragile_lineages"][pn]: print(f"  replay-fragile ({pn}) P{fr['problem']} {fr['lineage']}: {fr['survival_text_vs_valid']} (pool deterministic: {fr['pool_deterministic']})")
    print(f"  MC check: max |MC - exact| survival {mc['max_abs_diff_survival_text_vs_ref']:.4f}, apparent-up {mc['max_abs_diff_p_apparent_up']:.4f}")
    ic_ = controls["identical_adjacent_pairs"]["all"]; dc_ = controls["different_text_adjacent_pairs"]["all"]
    print(f"2. CONTROLS: identical adjacent pairs {ic_['n']} (layer-0 changes {ic_['layer0_changes']}; expected per-checkpoint replay change "
          + ", ".join(f"{pn} {fmt(ic_[pn]['expected_change_rate_per_checkpoint_replay'])} over {ic_[pn]['n_covered']} covered" for pn in POOLS)
          + f"; per-text replay 0 by construction); all lineages incl. route-N/A: {ident_all} pairs, {ident_all_change} layer-0 changes")
    print(f"   different-text adjacent pairs {dc_['n']}: class changes across evaluators {dc_['class_changes_across_evaluators']}, not all equal {REF_NAME} {dc_['class_not_all_equal_valid']}; "
          f"P(class != {REF_NAME}) under per-text replay " + ", ".join(f"{pn} {fmt(dc_[pn]['p_class_differs_from_valid_per_text_replay'])} over {dc_[pn]['n_covered']} covered" for pn in POOLS))
    print(f"3. CHECKPOINT EFFECT: observed layer-0 apparent up-transitions {ob['apparent_up_transitions_total']} in {ob['lineages_with_any']} lineages ({ev_txt.replace('~', ' ')}); identical-text changes "
          f"{ob['identical_text_changes_total']}; Spearman k vs apparent-up rho={sp['rho']} p={sp['perm_p']}; design compares different lineages, not one lineage thinned")
    for pn in POOLS:
        e = effect["pools"][pn]; sm = e["summary"] or {}
        print(f"   {POOLS[pn]['name']} pool ({e['n_covered_lineages']} covered, {sm.get('n_covered_zero')} with P(apparent up)=0, max lineage {fmt(sm.get('p_up_max_lineage'), 3)}, mean k>=3 {fmt(sm.get('p_up_mean_k_ge3'), 4)} "
              f"over {sm.get('n_k_ge3')}): " + "; ".join(f"k={k}: up {fmt(v['p_apparent_up'], 3)} max {fmt(v['p_apparent_up_max'], 3)} chg {fmt(v['p_apparent_change'], 3)} (n={v['n_covered_lineages']}, "
                                                          f"heuristic {fmt(v['heuristic_up_draw_q_1-(1-q/2)^(k-1)'], 3)})" for k, v in e["by_k"].items() if v["n_covered_lineages"]))
        for x in sm.get("nonzero_lineages", []): print(f"      nonzero: P{x['problem']} {x['lineage']} k={x['k']} P(apparent up)={x['p_apparent_up']}")
    print("4. REMEDIES (cost/lineage | abstain | stability impr/regr/cross | detects/evaluable | accepts/evaluable | false change identical (covered pairs) / same-defect)")
    def prr(r, label):
        dx, dn = r["detected_expected_of_evaluable"]; ax, an = r["accepted_expected_of_evaluable"]
        print(f"   {label:<58} {fnum(r['cost_ratings_per_lineage']):>5} | {fmt(r['abstention_rate_checkpoints'], 3):>6} | {'/'.join(fmt(r['stability'][c]) for c in CONCS):<14} | {fnum(dx)}/{dn} | {fnum(ax)}/{an} | "
              f"{fmt(r['false_change_identical_texts'])} ({r['false_change_identical_texts_n_covered_pairs']}) / {fmt(r['false_change_same_defect_pair'])}")
    for p in NO_MODEL: prr(RB[p], PROC_LABEL[p])
    for pn in POOLS:
        print(f"   -- {POOLS[pn]['name']} pool: {RP[pn]['n_covered_lineages']} covered lineages, {RP[pn]['n_positive_pairs_evaluable']}/{len(pos_pairs)} positive pairs evaluable "
              f"({RP[pn]['n_positive_pairs_evaluable_before_already_S2']} already S=2 before), same-defect pair covered: {defect and defect['pools'][pn]['covered']}")
        for p in PROCS:
            if p not in NO_MODEL: prr(RP[pn]["procedures"][p], PROC_LABEL[p])
    ps = remedies["positive_set_summary"]
    print(f"   positive pairs: {ps['n']}, already S=2 before in the reference: {ps['n_before_already_S2_in_reference']}, detection possible: {ps['n_detection_possible']} ({', '.join(ps['detection_possible_lineages'])})")
    if defect:
        print(f"5. SAME-DEFECT PAIR: {REF_NAME} S {defect['valid_S']}; pools " + "; ".join(f"{pn} a={defect['pools'][pn]['a']} {defect['pools'][pn]['a_modes']} b={defect['pools'][pn]['b']} covered={defect['pools'][pn]['covered']}" for pn in POOLS))
        for pn, e in defect["exact"].items(): print(f"   exact ({pn}): single-draw disagreement {e['single_draw_disagreement']}, majority-of-three {e['majority3_disagreement']}, P(S) a={e['P_S']['a']} b={e['P_S']['b']}")
        print(f"   detections elsewhere: rep1 S {defect['detections_elsewhere']['glm_thinking_repeat_rep1_S']}; ordinary grades " + "; ".join(f"{m}: " + ", ".join(f"{k}={v['grade']}" for k, v in g.items()) for m, g in defect["detections_elsewhere"]["ordinary_grades"].items()))
    print(f"6. SOURCES: q fixed {REPLAYQ}; kappa " + ", ".join(f"{n} {fmt(shipped[n]['all'].get('kappa'))} (n={shipped[n]['all'].get('n')})" for n in KAPPA_PAIRS)
          + f"; P2 range {fmt(k2[0])}-{fmt(k2[1])} vs P3/P6 {fmt(k36[0])}-{fmt(k36[1])}; route N/A {rc['p2_route_na']}/{rc['p2_lineages']} ({rc['p2_route_na_S_final_vs_grade_disagree']} would disagree with grade); "
          f"P6 regressing: none={ic['none']['n_regressing']} {ic['none']['regressing_lineages']} final_only={ic['final_only']['n_regressing']} {ic['final_only']['regressing_lineages']} all={ic['all']['n_regressing']}")
    AS = AA["ascertainment"]
    print(f"7. ALARM: {AA['n_texts']} applicable texts, {AA['n_flagged']} flagged | documented-defective {DD['n']} ({AS['n_correction_entries']} correction entries; {AS['n_public_finals_failing']} of "
          f"{AS['n_public_finals_in_scope']} public finals in scope with a released grade <= {PUBLIC_FAIL_MAX}/7) | credited-defective {CD['n']} carrying {CD['distinct_defects']} distinct defects")
    for prob in PROBS + ("all",):
        a = AL[prob]; r = a["S_disagree"]
        print(f"   P{prob:<3} texts {a['texts']:>2} documented {a['documented_texts']:>2} credited {a['evidence_texts']} | flagged {r['flagged']:>2} | hits: credited {r['hits_of_evidence']} documented "
              f"{r['hits_of_documented']} | flags without record {r['flags_of_texts_without_record']} | field 2-vs-<2 flagged {a['field_2_vs_lt2']['flagged']:>2}")
    print(f"   credited-defective coverage {CD['hits']}/{CD['n']}: {', '.join(CD['ids'])}" + (f" | MISSED: {', '.join(CD['misses'])}" if CD["misses"] else ""))
    print(f"   documented-defective coverage {DD['hits']}/{DD['n']}; misses (never credited):")
    for m in DD["misses"]: print(f"      P{m['problem']} {m['id']:<32} public {m['public_score']}/7  S {m['S']}")
    print(f"   flags without record {NR['n']}/{NR['texts_without_record']} (unexamined, not known negatives): {', '.join(NR['ids'])}")
    if AS["public_finals_route_na_excluded"]:
        print("   public finals outside the scope (route-N/A lineages): " + ", ".join(f"P{p['problem']} {p['id']} {p['public_score']}/7" for p in AS["public_finals_route_na_excluded"]))
    if AS["first_pass_grades_not_used"]: print(f"   failing first-pass grades not used (earlier texts, identified only through correction entries): {AS['first_pass_grades_not_used']}")
    print("   evaluator sets: texts rated by >=2 of the set | flags | credited hits | documented hits | flags without record")
    for name, p in pairs.items():
        print(f"      {name:<26} {p['n_texts']:>3} | {p['flags']:>2} | {p['credited_hits']}/{p['credited_n']} | {p['documented_hits']}/{p['documented_n']} | {p['flags_without_record']}/{p['texts_without_record']}")
    print(f"  macro sentences: {sentences}")
    print(f"DATA PROBLEMS ({len(problems)}):"); [print("   -", p) for p in problems[:40]]
    if len(problems) > 40: print(f"   ... {len(problems) - 40} more in results.json")
    print(f"wrote {out}/{{results.json,table_survival.tex,table_remedies.tex,table_sources.tex,table_evaluators.tex,table_alarm.tex,table_alarm_pairs.tex}}"
          + (f" and {gen / 'sensitivity_macros.tex'}" if gen is not None else " (flat bundle without gen/: sensitivity_macros.tex not written)"))


if __name__ == "__main__":
    main()
