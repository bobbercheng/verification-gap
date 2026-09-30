#!/usr/bin/env python3
"""Aggregate structural-closure ratings per distinct text into labelled layers and measure inter-annotator reliability.

Inputs  artifacts/closure{,_deedy,_p6,_p2}/*/annotation.json    layer 0: GLM-5.3, every checkpoint (several records may share a text)
        artifacts/closure_glm_rerun/p{3,6,2}/*/annotation.json    GLM-5.3 re-rating (thinking, larger cap), one per distinct text
        artifacts/closure_kimi/p{3,6,2}/*/annotation.json         Kimi K3 rating, one per distinct text (independent lab)
        artifacts/closure_adjudicated/validity_overrides.json     criterion-based entries (independent refutation of a written mechanism)
Layers (per problem, sha256):
        glm     = GLM re-rating fields (fallback: layer-0 majority if the re-rating is missing)
        kimi    = Kimi fields (None if missing)
        written = conservative aggregation: a field counts 2 only if BOTH glm and kimi score it 2, else the lower score;
                  None ("unknown") if either rater is missing -- never a silent raw fallback
        valid   = written, with validity_overrides applied (field forced to the given value)
        raw     = layer-0 majority (reported for comparison only)
Outputs artifacts/closure_adjudicated/labels.json (every vote, every layer, per text) and reliability.json
        (Cohen's kappa and field agreement glm vs kimi, repeated-text consistency of layer 0, overrides, fallbacks).
Stdlib only; offline; idempotent.  Usage: closure_adjudicate.py [--root DIR]
"""
from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
from pathlib import Path

RAW = {"3": ("closure", "closure_deedy"), "6": ("closure_p6",), "2": ("closure_p2",)}
LAYERS = ("raw", "glm", "kimi", "claude", "gpt", "written", "valid", "majority3", "rep1", "rep2", "rep3", "crep1", "crep2", "crep3")

def load(p):
    try: return json.loads(Path(p).read_text())
    except (OSError, ValueError): return None

def fields(a):
    """(lower, upper) of one annotation, or None if it has no parsed grades / S."""
    if not a or a.get("S") is None: return None
    g = a.get("grades") or {}
    try: return (int(g.get("lower_bound")), int(g.get("upper_bound")))
    except (TypeError, ValueError): return None

def S_of(f): return None if f is None else sum(x == 2 for x in f)

def majority(vals):
    vals = [v for v in vals if v is not None]
    if not vals: return None
    c = Counter(vals).most_common()
    return c[0][0] if len(c) == 1 or c[0][1] > c[1][1] else None

def kappa(pairs, classes=(0, 1, 2)):
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    n = len(pairs)
    if n == 0: return None
    po = sum(a == b for a, b in pairs) / n
    pa, pb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(pa[c] * pb[c] for c in classes) / (n * n)
    return {"n": n, "observed": round(po, 3), "kappa": None if pe == 1 else round((po - pe) / (1 - pe), 3)}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1]); args = ap.parse_args()
    art = args.root / "artifacts" if (args.root / "artifacts").is_dir() else args.root
    out_dir = art / "closure_adjudicated"; out_dir.mkdir(parents=True, exist_ok=True)
    overrides = {k: v for k, v in (load(out_dir / "validity_overrides.json") or {}).items() if not k.startswith("_")}
    labels, rel = [], {}
    for prob, groups in RAW.items():
        raw = defaultdict(list)
        for g in groups:
            for f in sorted((art / g).glob("*/annotation.json")):
                a = load(f)
                if a: raw[a["sha256"]].append(a)
        rerun = {a["sha256"]: a for f in (art / "closure_glm_rerun" / f"p{prob}").glob("*/annotation.json") if (a := load(f))}
        reps = {r: {a["sha256"]: a for f in (art / "closure_repeat" / f"p{prob}" / r).glob("*/annotation.json") if (a := load(f))} for r in ("rep1", "rep2", "rep3")}
        creps = {r: {a["sha256"]: a for f in (art / "closure_repeat_claude" / f"p{prob}" / f"rep{r[-1]}").glob("*/annotation.json") if (a := load(f))} for r in ("crep1", "crep2", "crep3")}
        claude = {a["sha256"]: a for f in (art / "closure_claude" / f"p{prob}").glob("*/annotation.json") if (a := load(f))}
        gpt = {a["sha256"]: a for f in (art / "closure_gpt" / f"p{prob}").glob("*/annotation.json") if (a := load(f))}
        pairs_gc, pairs_kc, pairs_gg = [], [], []
        rep_stats = {"texts_with_3plus_ratings": 0, "all_equal_S": 0, "pairs": 0, "pairs_differ": 0, "pairs_lower_differ": 0, "pairs_upper_differ": 0}
        kimi = {a["sha256"]: a for f in (art / "closure_kimi" / f"p{prob}").glob("*/annotation.json") if (a := load(f))}
        pairs, fa, repeated, consistent, fallbacks = [], Counter(), 0, 0, 0
        for h, recs in sorted(raw.items()):
            raw_fields = [fields(a) for a in recs]; raw_S = [S_of(f) for f in raw_fields]
            if len(recs) > 1: repeated += 1; consistent += len(set(raw_S)) == 1
            raw_maj = majority([f for f in raw_fields if f])
            r, k = rerun.get(h), kimi.get(h)
            gf = fields(r) or raw_maj; kf = fields(k)
            glm_fallback = bool(r) and any(t["attempt"] == 1 and t["parsed"] for t in r["attempts"]); fallbacks += glm_fallback
            if gf is not None and kf is not None:
                written = tuple(2 if (a == 2 and b == 2) else min(a, b) for a, b in zip(gf, kf))
                status = "agree" if S_of(gf) == S_of(kf) else "conservative"
            else:
                written = None; status = "unknown"
            valid = written
            ov = overrides.get(f"{prob}:{h}")
            if ov and written is not None:
                valid = (ov.get("lower", written[0]), ov.get("upper", written[1])); status = "validity_override"
            cf_, gpf = fields(claude.get(h)), fields(gpt.get(h))
            # majority3: a field counts 2 if at least two of the three independent labs (GLM re-rating, Kimi, Claude) score it 2; else the median
            maj3 = None
            if gf is not None and kf is not None and cf_ is not None:
                maj3 = tuple(2 if sum(x == 2 for x in trio) >= 2 else sorted(trio)[1] for trio in zip(gf, kf, cf_))
            layer = {"raw": raw_maj, "glm": gf, "kimi": kf, "claude": cf_, "gpt": gpf, "written": written, "valid": valid, "majority3": maj3}
            for rn in ("rep1", "rep2", "rep3"): layer[rn] = fields(reps[rn].get(h))
            for rn in ("crep1", "crep2", "crep3"): layer[rn] = fields(creps[rn].get(h))
            if fields(r) and cf_: pairs_gc.append((S_of(fields(r)), S_of(cf_)))
            if kf and cf_: pairs_kc.append((S_of(kf), S_of(cf_)))
            if fields(r) and gpf: pairs_gg.append((S_of(fields(r)), S_of(gpf)))
            same_model = [x for x in (fields(r) if r else None, layer["rep1"], layer["rep2"], layer["rep3"]) if x is not None]
            if len(same_model) >= 3:           # re-rating plus at least two repeats under identical settings
                rep_stats["texts_with_3plus_ratings"] += 1; rep_stats["all_equal_S"] += len({S_of(x) for x in same_model}) == 1
                for i in range(len(same_model)):
                    for j in range(i + 1, len(same_model)):
                        rep_stats["pairs"] += 1; rep_stats["pairs_differ"] += S_of(same_model[i]) != S_of(same_model[j])
                        rep_stats["pairs_lower_differ"] += same_model[i][0] != same_model[j][0]; rep_stats["pairs_upper_differ"] += same_model[i][1] != same_model[j][1]
            rec = {"problem": prob, "sha256": h, "record_ids": [a["id"] for a in recs], "lineage": recs[0].get("lineage"), "model": recs[0].get("model"),
                   "raw_fields": raw_fields, "raw_S": raw_S, "glm_rerun_present": bool(fields(r)), "glm_rerun_fallback": glm_fallback, "kimi_present": kf is not None,
                   "fields": {L: list(v) if v else None for L, v in layer.items()}, "S": {L: S_of(v) for L, v in layer.items()},
                   "status": status, "override": {"reason": ov["reason"], "evidence": ov["evidence"]} if ov else None}
            labels.append(rec)
            if fields(r) and kf:
                pairs.append((S_of(fields(r)), S_of(kf))); fa["both_present"] += 1
                fa["lower_equal"] += fields(r)[0] == kf[0]; fa["upper_equal"] += fields(r)[1] == kf[1]
        rel[prob] = {"distinct_texts": len(raw), "repeated_texts": repeated, "repeated_consistent_S": consistent,
                     "kappa_S_glm_rerun_vs_kimi": kappa(pairs), "kappa_S_glm_vs_claude": kappa(pairs_gc), "kappa_S_kimi_vs_claude": kappa(pairs_kc), "kappa_S_glm_vs_gpt": kappa(pairs_gg),
                     "field_agreement_rerun_vs_kimi": dict(fa), "glm_rerun_fallbacks": fallbacks,
                     "repeat": dict(rep_stats, pairwise_disagreement_rate=(round(rep_stats["pairs_differ"] / rep_stats["pairs"], 3) if rep_stats["pairs"] else None)),
                     "status": dict(Counter(l["status"] for l in labels if l["problem"] == prob))}
    allp = [(l["S"]["glm"], l["S"]["kimi"]) for l in labels if l["glm_rerun_present"] and l["kimi_present"]]
    allgc = [(l["S"]["glm"], l["S"]["claude"]) for l in labels if l["S"]["glm"] is not None and l["S"]["claude"] is not None]
    allkc = [(l["S"]["kimi"], l["S"]["claude"]) for l in labels if l["S"]["kimi"] is not None and l["S"]["claude"] is not None]
    allgg = [(l["S"]["glm"], l["S"]["gpt"]) for l in labels if l["S"]["glm"] is not None and l["S"]["gpt"] is not None]
    rp = {k: sum(rel[p]["repeat"][k] for p in ("3", "6")) for k in ("texts_with_3plus_ratings", "all_equal_S", "pairs", "pairs_differ", "pairs_lower_differ", "pairs_upper_differ")}
    rp["pairwise_disagreement_rate"] = round(rp["pairs_differ"] / rp["pairs"], 3) if rp["pairs"] else None
    rel["overall"] = {"distinct_texts": len(labels), "kappa_S_glm_rerun_vs_kimi": kappa(allp), "kappa_S_glm_vs_claude": kappa(allgc), "kappa_S_kimi_vs_claude": kappa(allkc), "kappa_S_glm_vs_gpt": kappa(allgg),
                      "status": dict(Counter(l["status"] for l in labels)), "repeat": rp,
                      "glm_rerun_fallbacks": sum(l["glm_rerun_fallback"] for l in labels),
                      "unknown": [{"problem": l["problem"], "record_ids": l["record_ids"]} for l in labels if l["status"] == "unknown"],
                      "validity_overrides": [{"problem": l["problem"], "record_ids": l["record_ids"], "S_written": l["S"]["written"], "S_valid": l["S"]["valid"], "reason": l["override"]["reason"]}
                                             for l in labels if l["status"] == "validity_override"],
                      "changed_vs_raw": [{"problem": l["problem"], "record_ids": l["record_ids"], "raw_S": l["raw_S"], "S_written": l["S"]["written"], "S_valid": l["S"]["valid"], "status": l["status"]}
                                         for l in labels if l["S"]["valid"] is not None and majority(l["raw_S"]) != l["S"]["valid"]]}
    (out_dir / "labels.json").write_text(json.dumps(labels, indent=1, ensure_ascii=False) + "\n")
    (out_dir / "reliability.json").write_text(json.dumps(rel, indent=1, ensure_ascii=False) + "\n")
    for p, r in rel.items():
        print(p, json.dumps({k: v for k, v in r.items() if k not in ("unknown", "validity_overrides", "changed_vs_raw")}))
    print("unknown:", len(rel["overall"]["unknown"]), "| overrides:", len(rel["overall"]["validity_overrides"]), "| changed vs raw:", len(rel["overall"]["changed_vs_raw"]))

if __name__ == "__main__": main()
