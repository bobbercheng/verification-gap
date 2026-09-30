#!/usr/bin/env python3
"""Quote localization: where in a proof each acceptance rule's evidence points.

A rule's decision is easier to check when its evidence names a place in the proof. This script measures only that,
from the objections already stored in artifacts/planted_defects/results.json, and makes no model calls.

Unit model, derived from the texts themselves:
  unit   a markdown-heading-delimited section of the proof; the base texts have between 5 and 12.
For each rule that returns quotes, every anchored quote is mapped to the unit containing it, and we report how many of
the edited texts get at least one such pointer and how many distinct units the pointers cover.

What this does NOT show: locating a quote says nothing about whether the units it does not touch are correct, so these
numbers are not a measure of verification work saved. An earlier version of this script also reported dependency-closure
sizes, downstream consumers, a prose-localization rate for the completeness verdict and a finite-check share. Those
rested on heuristics that mis-parse decimal equation labels, treat a lemma's mention as its definition, absorb prose into
a generic heading, and match the ordinary word "set", so they were withdrawn rather than repaired.

Usage: python3 scripts/inspection_cost.py [--root DIR]
Writes artifacts/inspection_cost/{results.json,RESULTS.md,table_cost.tex} and gen/inspection_macros.tex.
"""
import argparse, json, pathlib, re, statistics, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
HEAD = re.compile(r"^(#{2,4})\s+(.+)$", re.M)

# Each row: macro suffix, label, and the gate whose anchored quotes it reports.
SOURCES = [("GRADER", "ordinary grader's error quotes", "grade"),
           ("WITNESS", "witness objections", "witness"),
           ("REFERENCE", "witness objections, reference-adjudicated", "refadj")]


def units_of(text):
    """Heading-delimited units with their character spans; a preamble unit covers anything before the first heading."""
    marks = [(m.start(), m.group(2).strip()) for m in HEAD.finditer(text)]
    if not marks:
        return [{"i": 0, "title": "(whole text)", "start": 0, "end": len(text)}]
    spans = []
    if marks[0][0] > 0:
        spans.append((0, marks[0][0], "(preamble)"))
    for k, (pos, title) in enumerate(marks):
        spans.append((pos, marks[k + 1][0] if k + 1 < len(marks) else len(text), title))
    return [{"i": i, "title": t, "start": a, "end": b} for i, (a, b, t) in enumerate(spans)]


def unit_of_span(units, span):
    if not span:
        return None
    for u in units:
        if u["start"] <= span[0] < u["end"]:
            return u["i"]
    return None


def spans_for(entry, gate):
    """Anchored quote spans a rule hands the reader, pooled over both models."""
    out = []
    if gate == "refadj":
        for o in entry["gates"]["refadj"]["objections"]:
            if o.get("source_gate") == "witness" and (o.get("locus") or {}).get("anchored"):
                out.append(o["locus"]["span"])
        return out
    for m in ("gpt", "claude"):
        g = entry["gates"][gate].get(m) or {}
        for o in g.get("objections", []):
            if (o.get("locus") or {}).get("anchored"):
                out.append(o["locus"]["span"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    a = ap.parse_args()
    root = pathlib.Path(a.root).resolve() if a.root else ROOT
    pd = root / "artifacts" / "planted_defects"
    if not pd.is_dir():
        pd = root / "planted_defects"
    per = json.load(open(pd / "results.json"))["per_text"]

    rows = []
    for e in per:
        tp = pd / "texts" / e["base_id"] / ((e["type"] + ".md") if e["type"] != "O" else "original.md")
        if not tp.exists():
            continue
        units = units_of(tp.read_text(errors="replace"))
        rows.append({"id": e["id"], "type": e["type"], "n_units": len(units),
                     "located": {g: len(sorted({unit_of_span(units, s) for s in spans_for(e, g)} - {None}))
                                 for _, _, g in SOURCES}})

    POPS = (("fg", "fatal or gap", ("F", "G")), ("all", "all edited", ("F", "G", "H")))
    summary = {}
    for key, plabel, types in POPS:
        sub = [r for r in rows if r["type"] in types]
        for _, label, gate in SOURCES:
            hit = [r for r in sub if r["located"][gate] > 0]
            summary[f"{key}:{gate}"] = {"population": plabel, "n": len(sub), "label": label,
                                        "texts_localized": f"{len(hit)}/{len(sub)}",
                                        "median_units_located": int(statistics.median([r["located"][gate] for r in hit])) if hit else None}
    edited = [r for r in rows if r["type"] in ("F", "G")]
    med_units = int(statistics.median([r["n_units"] for r in rows])) if rows else None
    out = {"generated_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
           "measures": "quote localization only; the module docstring records what was withdrawn and why",
           "median_units_per_proof": med_units, "n_edited": len(edited), "summary": summary, "per_text": rows}
    od = root / "artifacts" / "inspection_cost"
    od.mkdir(parents=True, exist_ok=True)
    (od / "results.json").write_text(json.dumps(out, indent=1))

    T = [r"\begin{tabular}{@{}lcccc@{}}", r"\toprule",
         r" & \multicolumn{2}{c}{fatal or gap ($n{=}16$)} & \multicolumn{2}{c}{all edited ($n{=}24$)} \\",
         r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
         r"Evidence the rule returns & with a pointer & sections & with a pointer & sections \\", r"\midrule"]
    for _, label, gate in SOURCES:
        a_, b_ = summary[f"fg:{gate}"], summary[f"all:{gate}"]
        T.append(f"{label} & {a_['texts_localized']} & {a_['median_units_located']} & {b_['texts_localized']} & {b_['median_units_located']} \\\\")
    T += [r"\bottomrule", r"\end{tabular}"]
    (od / "table_cost.tex").write_text("\n".join(T) + "\n")

    m = [r"% generated by scripts/inspection_cost.py; do not edit",
         r"\newcommand{\COSTUNITS}{%s}" % med_units,
         r"\newcommand{\COSTGRADERLOC}{%s}" % summary["fg:grade"]["texts_localized"],
         r"\newcommand{\COSTGRADERSEC}{%s}" % summary["fg:grade"]["median_units_located"],
         r"\newcommand{\COSTWITNESSLOC}{%s}" % summary["fg:witness"]["texts_localized"],
         r"\newcommand{\COSTWITNESSSEC}{%s}" % summary["fg:witness"]["median_units_located"],
         r"\newcommand{\COSTALLGRADERLOC}{%s}" % summary["all:grade"]["texts_localized"],
         r"\newcommand{\COSTALLGRADERSEC}{%s}" % summary["all:grade"]["median_units_located"],
         r"\newcommand{\COSTALLWITNESSLOC}{%s}" % summary["all:witness"]["texts_localized"],
         r"\newcommand{\COSTALLWITNESSSEC}{%s}" % summary["all:witness"]["median_units_located"],
         r"\newcommand{\COSTTABLE}{\input{artifacts/inspection_cost/table_cost.tex}}"]
    gen = root / "gen"
    if gen.is_dir():
        (gen / "inspection_macros.tex").write_text("\n".join(m) + "\n")

    md = ["# Quote localization\n",
          f"Generated {out['generated_utc']}. No model calls; computed from the stored planted-defect objections.\n",
          f"Median heading-delimited sections per proof: {med_units}. Edited texts: {len(edited)}.\n",
          "| evidence the rule returns | fatal/gap: pointer | sections | all edited: pointer | sections |", "|---|---|---|---|---|"]
    for _, label, gate in SOURCES:
        a_, b_ = summary[f"fg:{gate}"], summary[f"all:{gate}"]
        md.append(f"| {label} | {a_['texts_localized']} | {a_['median_units_located']} | {b_['texts_localized']} | {b_['median_units_located']} |")
    md.append("\nMedians are taken over the texts that receive a pointer.\n")
    md.append("\nLocating a quote does not establish that the sections it does not touch are correct, so these are not "
              "estimates of verification work saved. Dependency-closure, consumer, prose-localization and finite-check "
              "measures reported by an earlier version of this script were withdrawn as unvalidated heuristics.\n")
    (od / "RESULTS.md").write_text("\n".join(md) + "\n")
    print(json.dumps({"median_units_per_proof": med_units, "summary": summary}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
