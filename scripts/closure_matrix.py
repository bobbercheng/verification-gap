#!/usr/bin/env python3
"""Aggregate structural-closure (S) annotations for IMO 2026 P2/P3/P6 into paper tables.

Inputs (all optional; missing inputs are reported, never fatal):
  artifacts/closure{,_deedy,_p6,_p2}/*/annotation.json   per-checkpoint S annotations
  <scratch>/imo-2026-deedy/grades/problem-0N.json          public final grades
  <scratch>/imo-2026-deedy/README.md                       public first-pass grade table
  artifacts/trajectory_stats_public.json                  public per-session budgets
  <run dir>/review_vN.json next to each of our candidate_vN.md  gate outcomes (ours)
Outputs: artifacts/closure_matrix/{matrix.json,regularities.json,table_matrix.tex,table_budget.tex}
Stdlib only, no network, idempotent.  Usage: closure_matrix.py [--problems 2,3,6]
Bundle mode: closure_matrix.py --root <bundle dir> --check   (recomputes from the released annotations,
checkpoint manifests, checkpoint_reviews/, trajectory stats and closure_matrix/public_grades.json, then
compares with the shipped closure_matrix/regularities.json; exit 1 on any difference).
"""
from __future__ import annotations
import argparse, json, re, statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"          # reset in main() from --root: repo layout (<root>/artifacts) or bundle layout (<root>)
DEEDY = Path("[local-path]"
             "/imo-2026-deedy")   # public campaign checkout (optional)
OUT = ART / "closure_matrix"
ANNOT_DIRS = {"2": ["closure_p2"], "3": ["closure", "closure_deedy"], "6": ["closure_p6"]}
MANIFESTS = {"2": "closure_p2_checkpoints.json", "3": "closure_checkpoints.json", "6": "closure_p6_checkpoints.json"}
PUBLIC = [("Claude Fable 5", "claude-fable-5"), ("GPT-5.6-Sol xhigh", "gpt-5.6-sol-xhigh"),
          ("Kimi K3", "kimi-k3"), ("GPT-5.6-Sol Pro", "gpt-5.6-sol-pro"),
          ("GPT-5.6-Sol max", "gpt-5.6-sol-max"), ("GPT-5.6-Sol default", "gpt-5.6-sol"),
          ("Muse Spark 1.1", "muse-spark-1.1"), ("DeepSeek V4 Pro", "deepseek-v4-pro"),
          ("Grok 4.5", "grok-4.5")]
README_NAMES = {"Claude Fable 5": "claude-fable-5", "GPT-5.6 Sol (xhigh effort)": "gpt-5.6-sol-xhigh",
                "Kimi K3": "kimi-k3", "GPT-5.6 Sol Pro (xhigh effort)": "gpt-5.6-sol-pro",
                "GPT-5.6 Sol (max effort)": "gpt-5.6-sol-max", "GPT-5.6 Sol (default effort)": "gpt-5.6-sol",
                "Meta Muse Spark 1.1": "muse-spark-1.1", "DeepSeek V4 Pro": "deepseek-v4-pro",
                "xAI Grok 4.5": "grok-4.5"}
# Table rows for our lineages: label -> lineage names (they differ across problems' annotation runs).
OURS_ROWS = [("GPT-5.6-Sol ultra", {"ours-gpt56sol-ultra"}), ("Kimi K3 R1", {"ours-kimi-R1"}),
             ("Kimi K3 R2", {"ours-kimi-R2"}), ("GLM-5.2", {"ours-glm52", "ours-glm52-simple"}),
             ("GLM-5.3", {"ours-glm53-thin", "ours-glm53"}), ("Nemotron", {"ours-nemotron"})]
# P3 lanes from the older discovery harness have no review_v*.json; these are the recorded run
# outcomes (campaign retrospective, main.tex Table tab:closure).  Repairs descend from Kimi R1's seed.
LAYER = "valid"            # label layer supplying S: raw | glm | kimi | written | valid (set from --layer)
ROUTE_NA: dict = {}        # (problem, lineage) -> route string for lineages the rubric does not apply to (from p2_routes.json)

def load_routes():
    global ROUTE_NA
    routes = load_json(ART / "closure_adjudicated" / "p2_routes.json") or {}
    ROUTE_NA = {("2", lin): spec["route"] for lin, spec in routes.items() if not lin.startswith("_") and not spec.get("applicable", True)}
RECORDED_OUTCOMES = {"ours-kimi-R1": "6->7", "ours-kimi-R2": "1", "ours-glm52-simple": "2",
                     "ours-glm53-thin": "unreviewed", "ours-kimi-K2-repair": "7", "ours-glm52-repair": "7"}


def load_json(p: Path):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


# ----------------------------------------------------------------------------- inputs
def load_annotations(prob: str) -> tuple[list[dict], list[str]]:
    """Annotated items plus un-annotated stubs (S=None) for manifest entries not yet processed."""
    items, missing = {}, []
    for d in ANNOT_DIRS[prob]:
        base = ART / d
        if not base.is_dir():
            missing.append(str(base)); continue
        for f in sorted(base.glob("*/annotation.json")):
            it = load_json(f)
            if it and str(it.get("id", "")).startswith("p" + prob + "-") == (prob != "3"):
                items[it["id"]] = it
    manifest = load_json(ART / MANIFESTS[prob]) or load_json(ART / ANNOT_DIRS[prob][0] / "checkpoints_manifest.json") or []
    for idx, it in enumerate(manifest):                     # manifest = full checkpoint list, in recorded order
        items.setdefault(it["id"], {**it, "S": None, "grades": None})
        items[it["id"]]["_order"] = idx
    # Label layers (closure_adjudicate.py): one record per distinct text; the selected LAYER supplies S.
    # A text without a label in that layer is UNKNOWN (S None); there is no fallback to another layer.
    adj = {l["sha256"]: l for l in (load_json(ART / "closure_adjudicated" / "labels.json") or []) if l["problem"] == prob}
    for it in items.values():
        it["S_raw"] = it.get("S")
        a = adj.get(it.get("sha256"))
        it["S_layers"] = a["S"] if a else None
        if LAYER == "raw":
            it["S_source"] = "raw"
        else:
            it["S"] = a["S"].get(LAYER) if a else None
            it["S_source"] = (a["status"] if a else "no-label") if it["S"] is not None else "unknown"
    # Integrity: identical text under the same rubric must carry one label.  Fatal unless the layer is 'raw'.
    by_hash = defaultdict(set)
    for it in items.values():
        if it.get("S") is not None: by_hash[(it.get("rubric_sha256"), it.get("sha256"))].add(it["S"])
    conflicts = [k[1][:12] for k, v in by_hash.items() if len(v) > 1]
    if conflicts and LAYER != "raw":
        raise SystemExit(f"FATAL P{prob}: contradictory labels for identical texts in layer {LAYER}: {conflicts}")
    if conflicts:
        print(f"note P{prob} (raw layer): identical texts with different layer-0 labels: {conflicts}")
    return list(items.values()), missing


def public_grades_cache() -> dict:
    return load_json(ART / "closure_matrix" / "public_grades.json") or {}


def first_pass_grades() -> dict[str, dict[str, int]]:
    """{problem: {model: grade}} parsed from README 'First pass' markdown table."""
    out: dict[str, dict[str, int]] = defaultdict(dict)
    if not (DEEDY / "README.md").exists():                  # bundle mode: released copy of the parsed table
        return {p: dict(v) for p, v in public_grades_cache().get("first_pass", {}).items()}
    txt = (DEEDY / "README.md").read_text()
    sec = txt.split("First pass", 1)[-1]
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7 or cells[0].startswith("Run") or cells[0].startswith("-"):
            if cells and cells[0].startswith("##"): break
            continue
        name = re.sub(r"\*+", "", cells[0]).strip()
        mid = README_NAMES.get(name)
        if not mid: continue
        for k in range(1, 7):
            if cells[k].isdigit(): out[str(k)][mid] = int(cells[k])
    return out


def final_grades(prob: str) -> dict[str, int]:
    d = load_json(DEEDY / "grades" / f"problem-0{prob}.json")
    if d is None:                                           # bundle mode
        return dict(public_grades_cache().get("final", {}).get(prob, {}))
    return {e["model"]: e.get("score") for e in d.get("entries", [])}


def budgets(prob: str) -> dict[str, dict]:
    rows = load_json(ART / "trajectory_stats_public.json") or []
    by: dict[str, list] = defaultdict(list)
    for r in rows:
        if r.get("problem") == "0" + prob: by[r["model"]].append(r)
    out = {}
    for m, rs in by.items():
        tok = sum(r.get("completion_tokens", 0) for r in rs); tc = sum(r.get("tool_calls", 0) for r in rs)
        out[m] = {"sessions": len(rs), "completion_tokens": tok, "tool_calls": tc,
                  "current_md_writes": sum(r.get("current_md_writes", 0) for r in rs),
                  "sessions_without_current_write": sum(1 for r in rs if not r.get("current_md_writes")),
                  "tokens_per_tool_call": round(tok / tc) if tc else None,
                  "minutes": round(sum(r.get("minutes", 0) for r in rs), 1)}
    return out


def review_for(path: str) -> dict | None:
    """Gate outcome for one of our candidate_vN.md files from the sibling review_vN.json."""
    m = re.search(r"^(.*/runs/[^/]+)/candidate_v(\d+)\.md$", path or "")
    rv = vf = None
    if m:
        rv = load_json(Path(m.group(1)) / f"review_v{m.group(2)}.json"); vf = load_json(Path(m.group(1)) / f"verification_v{m.group(2)}.json")
    if rv is None:                                          # bundle mode: checkpoint_reviews/<input sha>{,.verification}.json
        b = re.search(r"checkpoint_inputs/([0-9a-f]{64})\.md$", path or "")
        if b:
            rv = load_json(ART / "checkpoint_reviews" / f"{b.group(1)}.json"); vf = load_json(ART / "checkpoint_reviews" / f"{b.group(1)}.verification.json")
    if not rv: return None
    scores = rv.get("scores") or {}
    review_ok = (rv.get("verdict") == "pass" and set(scores) == {"correctness", "completeness", "rigor", "self_contained"}
                 and all(v >= 3 for v in scores.values()) and not rv.get("fatal_issues") and not rv.get("unverified_claims"))
    verify_ok = bool(vf) and vf.get("verdict") == "confirm" and not vf.get("dependency_gaps") and not vf.get("required_fixes")
    return {"verdict": rv.get("verdict"), "scores": scores, "n_fatal": len(rv.get("fatal_issues") or []),
            "n_unverified": len(rv.get("unverified_claims") or []), "review_pass": bool(review_ok),
            "verification": (vf or {}).get("verdict") if vf is not None else "missing", "gate_pass": bool(review_ok and verify_ok)}


# ----------------------------------------------------------------------------- lineages
def order_key(it: dict):
    ctx, turn = it.get("context"), it.get("turn") or 0
    if ctx == 99: return (3, 0, 0, "")
    if isinstance(ctx, int): return (0, ctx, turn, "")
    if (m := re.search(r"round(\d+)$", str(ctx))): return (0, int(m.group(1)), turn, "")
    if str(ctx).endswith("main"): return (1, 0, turn, "")
    return (0, it.get("_order", 0), turn, str(ctx))                 # our run ids: recorded manifest order


def label(it: dict) -> str:
    ctx, turn = it.get("context"), it.get("turn")
    if ctx == 99: return "final file"
    if isinstance(ctx, int): return f"c{ctx}" + (f", t{turn}" if turn else "")
    return f"{ctx}" + (f", t{turn}" if turn is not None else "")


def build_lineage(prob, lin, items, fp, fg, bud):
    items = sorted(items, key=order_key)
    S = [it.get("S") for it in items]
    known = [s for s in S if s is not None]
    src = "ours" if lin.startswith("ours") else "public"
    model = items[0].get("model")
    seq = [{"id": it["id"], "label": label(it), "S": it.get("S"),
            "wrong_answer": (it.get("grades") or {}).get("wrong_answer_stated"),
            "review": review_for(it.get("path")) if src == "ours" else None} for it in items]
    last = items[-1]                     # S_final is the LAST checkpoint's S; None while it is unannotated
    first2 = next((it for it in items if it.get("S") == 2), None)
    seen0 = False; crossing = False
    for s in S:
        if s == 0: seen0 = True
        if s == 2 and seen0: crossing = True
    g = last.get("grades") or {}
    rec = {"problem": prob, "lineage": lin, "model": model, "source": src, "n_checkpoints": len(items), "route_na": ROUTE_NA.get((prob, lin)),
           "S_raw_sequence": [it.get("S_raw") for it in items], "S_sources": sorted({it.get("S_source", "raw") for it in items}),
           "n_annotated": len(known), "S_sequence": seq, "S_final": last.get("S"),
           "first_S2": label(first2) if first2 else None, "ever_S1": 1 in known,
           "monotone": all(a <= b for a, b in zip(known, known[1:])), "crossing_inside_record": crossing,
           "wrong_answer_final": g.get("wrong_answer_stated"),
           "wrong_answer_any": any(c["wrong_answer"] for c in seq),
           "final_mechanisms": {"lower": g.get("lower_bound_mechanism"), "upper": g.get("upper_bound_mechanism"),
                                "notes": g.get("notes")}}
    if src == "public":
        rec.update(first_pass_grade=fp.get(model), final_grade=fg.get(model), budget=bud.get(model))
        # Stage-matched grade: the public "final file" follows any repair session, so it is compared with the
        # final grade; every other last checkpoint predates the first-pass grade.  The first-pass comparison
        # is kept alongside (agreement_first_pass) so both readings are reproducible.
        last_is_final = last.get("context") == 99
        rec["grade_for_agreement"] = fg.get(model) if (last_is_final and fg.get(model) is not None) else fp.get(model)
        rec["grade_first_pass"] = fp.get(model)
    else:
        revs = [c["review"] for c in seq if c["review"]]
        gate = "pass" if any(r["gate_pass"] for r in revs) else ("fail" if revs else None)
        rec.update(gate=gate, gate_passing_checkpoints=[c["label"] for c in seq if c["review"] and c["review"]["gate_pass"]],
                   recorded_outcome=RECORDED_OUTCOMES.get(lin) if prob == "3" else None)
        ro = rec["recorded_outcome"]
        rec["grade_for_agreement"] = ({"pass": 7, "fail": 0}[gate] if gate else
                                      int(ro.split("-")[0]) if ro and ro[0].isdigit() else None)
    return rec


def grade_label(r: dict) -> str:
    if r["source"] == "public":
        fp, fg = r.get("first_pass_grade"), r.get("final_grade")
        if fp is None: return "?" if fg is None else str(fg)
        return f"{fp}$\\to${fg}" if fg is not None and fg != fp else str(fp)
    if r.get("gate"): return r["gate"]
    ro = r.get("recorded_outcome")
    return (ro or "?").replace("->", "$\\to$")


# ----------------------------------------------------------------------------- outputs
def regularities(lins: list[dict]) -> dict:
    out = {"n_lineages": len(lins), "n_S_final_2": sum(r["S_final"] == 2 for r in lins),
           "n_crossings_inside_record": sum(r["crossing_inside_record"] for r in lins),
           "n_S1_checkpoints": sum(c["S"] == 1 for r in lins for c in r["S_sequence"]),
           "n_checkpoints": sum(r["n_checkpoints"] for r in lins), "n_annotated": sum(r["n_annotated"] for r in lins),
           "n_route_na": sum(bool(r.get("route_na")) for r in lins), "n_unknown_final": sum(r["S_final"] is None and not r.get("route_na") for r in lins)}
    # transition counts over applicable lineages only (route N/A lineages are displayed but not counted)
    app = [r for r in lins if not r.get("route_na")]
    out.update({"n_lineages_applicable": len(app), "n_S_final_2": sum(r["S_final"] == 2 for r in app),
                "n_crossings_inside_record": sum(r["crossing_inside_record"] for r in app),
                "n_S1_checkpoints": sum(c["S"] == 1 for r in app for c in r["S_sequence"]),
                "n_ramps_1_to_2": sum(any(a == 1 and b == 2 for a, b in zip(seq, seq[1:])) for r in app for seq in [[c["S"] for c in r["S_sequence"] if c["S"] is not None]]),
                "n_regressing_lineages": sum(any(a > b for a, b in zip(seq, seq[1:])) for r in app for seq in [[c["S"] for c in r["S_sequence"] if c["S"] is not None]])})
    def compare(key):
        agree = Counter(); dis = []
        for r in lins:
            g = r.get(key, r.get("grade_for_agreement")) if key != "grade_for_agreement" else r.get(key)
            if r["source"] != "public": g = r.get("grade_for_agreement")
            if r.get("route_na"): agree["route_na"] += 1; continue
            if r["S_final"] is None or g is None: agree["skipped"] += 1; continue
            ok = (r["S_final"] == 2) == (g >= 5)
            agree["agree" if ok else "disagree"] += 1
            if not ok:
                dis.append({"problem": r["problem"], "lineage": r["lineage"], "S_final": r["S_final"], "grade": g,
                            "grade_label": grade_label(r).replace("$\\to$", "->"), **r["final_mechanisms"]})
        return dict(agree), dis
    out["agreement"], out["disagreements"] = compare("grade_for_agreement")          # stage-matched (paper)
    out["agreement_first_pass"], out["disagreements_first_pass"] = compare("grade_first_pass")
    pub = [r for r in lins if r["source"] == "public" and r.get("budget") and r["S_final"] is not None]
    med = lambda xs: statistics.median(xs) if xs else None
    out["budget"] = {"median_tokens_S_final_2": med([r["budget"]["completion_tokens"] for r in pub if r["S_final"] == 2]),
                     "median_tokens_S_final_lt2": med([r["budget"]["completion_tokens"] for r in pub if r["S_final"] < 2]),
                     "tokens_per_tool_call_by_S_final": {
                         str(s): sorted((r["model"], r["budget"]["tokens_per_tool_call"]) for r in pub if r["S_final"] == s)
                         for s in (0, 1, 2)}}
    return out


def cell(r: dict | None) -> str:
    if r is None: return "--"
    s = r["S_final"]; g = grade_label(r); marks = ""
    if s is None: return f"-- / {g}"
    ga = r.get("grade_for_agreement")
    if s == 2 and ga is not None and ga < 5 and not r.get("route_na"): marks += "$^{*}$"
    if r.get("wrong_answer_final"): marks += "$^{\\ddagger}$"
    if r.get("route_na"): marks += "$^{\\mathrm{r}}$"
    return f"{s}{marks} / {g}"


def table_matrix(by_prob: dict[str, list[dict]], probs: list[str]) -> str:
    def find(prob, pred):
        return next((r for r in by_prob.get(prob, []) if pred(r)), None)
    rows = [f"    {name} & " + " & ".join(cell(find(p, lambda r, m=mid: r["source"] == "public" and r["model"] == m))
                                         for p in probs) + " \\\\" for name, mid in PUBLIC]
    rows.append("    \\midrule")
    rows += [f"    {name} & " + " & ".join(cell(find(p, lambda r, ls=lins: r["lineage"] in ls)) for p in probs) + " \\\\"
             for name, lins in OURS_ROWS]
    hdr = " & ".join(f"P{p}" for p in probs)
    return "\n".join([
        "% generated by scripts/closure_matrix.py -- cells: S_final / grade label a->b (first-pass -> final, public) or gate (ours)",
        "\\begin{tabular}{@{}l" + "c" * len(probs) + "@{}}", "  \\toprule", f"  Model & {hdr} \\\\", "  \\midrule",
        *rows, "  \\bottomrule", "\\end{tabular}",
        "% $^{*}$ S=2 but stage-matched grade<5 (mechanisms named, proofs sketched); $^{\\ddagger}$ wrong final answer stated;",
        "% a$\\to$b = first-pass grade repaired to b; -- / g = checkpoints exist, S not yet annotated.", ""])


def table_budget(by_prob: dict[str, list[dict]], probs: list[str]) -> str:
    lines = ["% generated by scripts/closure_matrix.py -- public lineages, sorted by S_final desc then tokens",
             "\\begin{tabular}{@{}lrrrrcl@{}}", "  \\toprule",
             "  Model & Sess. & Tokens (k) & Tool calls & \\texttt{current.md} writes & $S$ & Grade \\\\"]
    names = dict((m, n) for n, m in PUBLIC)
    for p in probs:
        pub = [r for r in by_prob.get(p, []) if r["source"] == "public" and r.get("budget")]
        if not pub: continue
        lines += ["  \\midrule", f"  \\multicolumn{{7}}{{@{{}}l}}{{\\textbf{{Problem {p}}}}} \\\\"]
        for r in sorted(pub, key=lambda r: (-(r["S_final"] if r["S_final"] is not None else -1), r["budget"]["completion_tokens"])):
            b = r["budget"]; s = "--" if r["S_final"] is None else r["S_final"]
            lines.append(f"    {names.get(r['model'], r['model'])} & {b['sessions']} & {b['completion_tokens'] / 1000:.0f} & "
                         f"{b['tool_calls']} & {b['current_md_writes']} & {s} & {grade_label(r)} \\\\")
    return "\n".join(lines + ["  \\bottomrule", "\\end{tabular}", ""])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--problems", default="2,3,6", help="comma-separated subset of 2,3,6")
    ap.add_argument("--root", type=Path, default=ROOT, help="repository root (uses <root>/artifacts) or a bundle directory")
    ap.add_argument("--out", type=Path, default=None, help="output directory (default <artifacts>/closure_matrix)")
    ap.add_argument("--check", action="store_true", help="recompute and compare with the shipped regularities.json; do not write")
    ap.add_argument("--layer", default="valid", choices=("raw", "glm", "kimi", "claude", "gpt", "written", "valid", "majority3", "rep1", "rep2", "rep3", "crep1", "crep2", "crep3"), help="label layer for the primary outputs")
    args = ap.parse_args()
    global ART, OUT, LAYER
    ART = args.root / "artifacts" if (args.root / "artifacts").is_dir() else args.root
    OUT = args.out or ART / "closure_matrix"
    load_routes()
    probs = [p for p in args.problems.split(",") if p in ANNOT_DIRS]
    fp_all = first_pass_grades()

    def compute(layer):
        global LAYER
        LAYER = layer
        by_prob: dict[str, list[dict]] = {}; coverage = {}
        for p in probs:
            items, missing = load_annotations(p)
            groups = defaultdict(list)
            for it in items: groups[it["lineage"]].append(it)
            fp, fg, bud = fp_all.get(p, {}), final_grades(p), budgets(p)
            by_prob[p] = [build_lineage(p, lin, its, fp, fg, bud) for lin, its in sorted(groups.items())]
            coverage[p] = {"items": len(items), "annotated": sum(it.get("S") is not None for it in items),
                           "lineages": len(groups), "missing_dirs": missing, "first_pass_grades": len(fp),
                           "final_grades": len(fg), "budget_models": len(bud)}
        reg = {p: regularities(by_prob[p]) for p in probs}
        reg["overall"] = regularities([r for p in probs for r in by_prob[p]])
        reg["coverage"] = coverage; reg["layer"] = layer
        return by_prob, reg

    KEYS = ("n_lineages_applicable", "n_S_final_2", "n_crossings_inside_record", "n_S1_checkpoints", "n_ramps_1_to_2", "n_regressing_lineages", "agreement", "n_unknown_final")
    sensitivity = {}
    for layer in ("raw", "glm", "kimi", "claude", "gpt", "written", "valid", "majority3", "rep1", "rep2", "rep3", "crep1", "crep2", "crep3"):
        _, r = compute(layer)
        sensitivity[layer] = {p: {k: r[p].get(k) for k in KEYS} for p in probs + ["overall"]}
    by_prob, reg = compute(args.layer)
    reg["sensitivity_by_layer"] = sensitivity
    if args.check:
        shipped = load_json(OUT / "regularities.json") or {}
        strip = lambda d: {k: v for k, v in json.loads(json.dumps(d)).items() if k != "coverage"}
        same = strip(shipped) == strip(reg)
        print(f"closure_matrix --check: {'MATCH' if same else 'MISMATCH'} against {OUT / 'regularities.json'}")
        if not same:
            for k in sorted(set(strip(shipped)) | set(strip(reg))):
                if shipped.get(k) != reg.get(k): print("  differs:", k)
        raise SystemExit(0 if same else 1)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "public_grades.json").write_text(json.dumps({"first_pass": {p: fp_all.get(p, {}) for p in probs},
                                                        "final": {p: final_grades(p) for p in probs}}, indent=1) + "\n")
    for p in probs:                                          # strip private ordering key from released records
        for r in by_prob[p]:
            for c in r["S_sequence"]: c.pop("_order", None)
    (OUT / "matrix.json").write_text(json.dumps({"coverage": reg["coverage"], "layer": args.layer, "lineages": [r for p in probs for r in by_prob[p]]},
                                                indent=1, ensure_ascii=False) + "\n")
    (OUT / "regularities.json").write_text(json.dumps(reg, indent=1, ensure_ascii=False) + "\n")
    (OUT / "sensitivity.json").write_text(json.dumps(sensitivity, indent=1) + "\n")
    (OUT / "table_matrix.tex").write_text(table_matrix(by_prob, probs))
    (OUT / "table_budget.tex").write_text(table_budget(by_prob, probs))

    print(f"closure matrix -> {OUT}")
    for p in probs:
        c, g = reg["coverage"][p], reg[p]
        print(f"\nP{p}: {c['annotated']}/{c['items']} checkpoints annotated in {c['lineages']} lineages"
              + (f"  [missing: {', '.join(c['missing_dirs'])}]" if c["missing_dirs"] else ""))
        print(f"  S_final==2: {g['n_S_final_2']}/{g['n_lineages']} | crossings inside record: {g['n_crossings_inside_record']}"
              f" | S=1 checkpoints: {g['n_S1_checkpoints']} | agreement: {g['agreement']}")
        b = g["budget"]
        print(f"  public median tokens S_final=2: {b['median_tokens_S_final_2']}  vs <2: {b['median_tokens_S_final_lt2']}")
        for r in by_prob[p]:
            seq = "".join("?" if c["S"] is None else str(c["S"]) for c in r["S_sequence"])
            extra = f"gate={r['gate']}" if r["source"] == "ours" else f"grade={r.get('first_pass_grade')}->{r.get('final_grade')}"
            print(f"    {r['lineage']:<28} S={seq:<8} first S=2: {r['first_S2'] or '--':<28} {extra}"
                  + ("  [recorded " + r["recorded_outcome"] + "]" if r.get("recorded_outcome") else ""))
    o = reg["overall"]
    print(f"\nOVERALL: {o['n_lineages']} lineages, {o['n_S_final_2']} with S_final=2, {o['n_crossings_inside_record']} crossings"
          f" inside record, {o['n_S1_checkpoints']} S=1 checkpoints, agreement {o['agreement']}")
    for d in o["disagreements"]:
        print(f"  DISAGREE P{d['problem']} {d['lineage']}: S_final={d['S_final']} grade={d['grade_label']}\n"
              f"    lower: {d['lower']}\n    upper: {d['upper']}\n    notes: {(d['notes'] or '')[:300]}")


if __name__ == "__main__":
    main()
