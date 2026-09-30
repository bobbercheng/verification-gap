#!/usr/bin/env python3
"""Tally the post-submission runs on the 32 planted texts (post_submission/) and write post_submission/summary.json.

Offline, standard library only, no model calls. Run from the supplement root or the paper repository:

    python3 post_submission/summarize.py --root .           # bundle root (post_submission/, planted_defects/)
    python3 post_submission/summarize.py --root . --check   # exit 1 if summary.json differs from a recomputation

Rules are the paper's, applied to each run's stored parsed.json:
  pass    accept iff grade >= 5            (grade arms)
  strict  accept iff grade = 7             (grade arms)
  flag    accept iff complete = true       (grade arms; the same response as pass and strict)
  witness accept iff S_valid = 2, S_valid = number of lower_bound/upper_bound obligations with status written_and_valid
Per grader (gpt = GPT-5.6-Sol, claude = Claude Opus 5) and for the pair ("both": accept iff both accept). Truth by construction:
O accepted under both conventions; F and G rejected under both; H accepted repair-tolerant (RT) and rejected as written (AW).
"broken" = the 16 F and G texts; "sound" = the 16 O and H texts (sound under RT only). Routing: the pair auto-accepts when both
graders accept, auto-rejects when both reject, and refers the text otherwise.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS = ("gpt", "claude")
GRADE_ARMS = ("grade_rerun", "grade_retest", "grade_instructed")
WITNESS_ARMS = ("witness_keyed_rerun", "witness_keyfree")
TRUTH = {"O": {"RT": "accept", "AW": "accept"}, "F": {"RT": "reject", "AW": "reject"}, "G": {"RT": "reject", "AW": "reject"},
         "H": {"RT": "accept", "AW": "reject"}}
# The five labels recorded as disputed (planted_defects/DEVIATIONS.md, entries of 2026-09-06 and 2026-09-07).
DISPUTED = ("p1-gpt56-5aca5e52-v1-G", "p1-deedy-kimi-k3-final-F", "p5-gpt56-7324ef70-v1-F", "p1-deedy-kimi-k3-final-G",
            "p1-gpt56-5aca5e52-v1-F")


def load(path: Path):
    return json.loads(path.read_text())


def locate(root: Path):
    """(post_submission dir, planted_defects dir) for a bundle root (both at the root) or the paper repository root
    (post_submission/ at the root, planted_defects/ under artifacts/)."""
    for planted in (root / "planted_defects", root / "artifacts" / "planted_defects"):
        if (root / "post_submission").is_dir() and planted.is_dir():
            return root / "post_submission", planted
    raise SystemExit(f"no post_submission/ and planted_defects/ under {root}")


def kind_of(text_id: str) -> str:
    tail = text_id.rsplit("-", 1)[-1]
    return tail if tail in ("F", "G", "H") else "O"


def decisions(post: Path, arm: str, text_id: str) -> dict:
    """{rule: {model: accept|reject}} for one text in one arm."""
    out = {}
    for model in MODELS:
        parsed = load(post / arm / model / text_id / "parsed.json").get("parsed") or {}
        if arm in GRADE_ARMS:
            grade, complete = parsed.get("grade"), parsed.get("complete")
            if not isinstance(grade, int) or not isinstance(complete, bool):
                raise SystemExit(f"unparsed grade response: {arm}/{model}/{text_id}")
            out.setdefault("pass", {})[model] = "accept" if grade >= 5 else "reject"
            out.setdefault("strict", {})[model] = "accept" if grade >= 7 else "reject"
            out.setdefault("flag", {})[model] = "accept" if complete is True else "reject"
        else:
            obligations = parsed.get("obligations") or {}
            s_valid = sum(1 for key in ("lower_bound", "upper_bound") if isinstance(obligations.get(key), dict)
                          and obligations[key].get("status") == "written_and_valid")
            out.setdefault("witness", {})[model] = "accept" if s_valid == 2 else "reject"
    for rule in out:
        out[rule]["both"] = "accept" if all(out[rule][m] == "accept" for m in MODELS) else "reject"
    return out


def frac(k: int, n: int) -> str:
    return f"{k}/{n}"


def tally(per_text: dict, rule: str, who: str, ids: list) -> dict:
    broken = [t for t in ids if kind_of(t) in ("F", "G")]
    sound = [t for t in ids if kind_of(t) in ("O", "H")]
    undisputed = [t for t in broken if t not in DISPUTED]
    dec = {t: per_text[t][rule][who] for t in ids}
    return {"broken_accepted": frac(sum(dec[t] == "accept" for t in broken), len(broken)),
            "broken_accepted_ids": [t for t in broken if dec[t] == "accept"],
            "sound_rejected": frac(sum(dec[t] == "reject" for t in sound), len(sound)),
            "sound_rejected_ids": [t for t in sound if dec[t] == "reject"],
            "broken_accepted_without_five_disputed": frac(sum(dec[t] == "accept" for t in undisputed), len(undisputed)),
            "by_class": {k: {"n": sum(kind_of(t) == k for t in ids), "accepted": sum(kind_of(t) == k and dec[t] == "accept" for t in ids)}
                         for k in ("O", "F", "G", "H")}}


def routing(per_text: dict, rule: str, ids: list) -> dict:
    broken = [t for t in ids if kind_of(t) in ("F", "G")]
    sound = [t for t in ids if kind_of(t) in ("O", "H")]
    route = {}
    for t in ids:
        g, c = per_text[t][rule]["gpt"], per_text[t][rule]["claude"]
        route[t] = "auto-accept" if g == c == "accept" else ("auto-reject" if g == c == "reject" else "refer")
    return {"referred": frac(sum(r == "refer" for r in route.values()), len(ids)),
            "referred_ids": [t for t in ids if route[t] == "refer"],
            "broken_auto_accepted": frac(sum(route[t] == "auto-accept" for t in broken), len(broken)),
            "sound_auto_rejected": frac(sum(route[t] == "auto-reject" for t in sound), len(sound))}


def convention_errors(per_text: dict, rule: str, ids: list) -> dict:
    """Per-grader disagreements with the intended truth over all 32 texts, under each convention."""
    return {conv: {m: sum(per_text[t][rule][m] != TRUTH[kind_of(t)][conv] for t in ids) for m in MODELS} for conv in ("RT", "AW")}


def input_tokens(parsed: dict):
    usage = parsed.get("usage") or {}
    if "cache_creation_input_tokens" in usage or "cache_read_input_tokens" in usage:
        return sum(int(usage.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    return usage.get("input_tokens")


def identity(post: Path, planted: Path, arm: str, ids: list) -> dict:
    """What each arm shares with the paper's primary run (planted_defects/runs/grade or /witness) on every call."""
    gate = "grade" if arm in GRADE_ARMS else "witness"
    out = {"text_sha256_equal": 0, "system_sha256_equal": 0, "system_sha256_ok": 0, "input_tokens_equal": {m: 0 for m in MODELS}, "calls": 0}
    for model in MODELS:
        for t in ids:
            request = load(post / arm / model / t / "request.json")
            primary = load(planted / "runs" / gate / model / t / "request.json")
            base, kind = (t.rsplit("-", 1) if kind_of(t) != "O" else (t, "original"))
            text = (planted / "texts" / base / f"{kind}.md").read_bytes()
            out["calls"] += 1
            out["text_sha256_equal"] += request["text_sha256"] == hashlib.sha256(text).hexdigest() == primary["text_sha256"]
            out["system_sha256_equal"] += request["system_sha256"] == primary["system_sha256"]
            out["system_sha256_ok"] += hashlib.sha256(request["system"].encode()).hexdigest() == request["system_sha256"]
            out["input_tokens_equal"][model] += input_tokens(load(post / arm / model / t / "parsed.json")) == \
                input_tokens(load(planted / "runs" / gate / model / t / "parsed.json"))
    return out


def summarize(root: Path) -> dict:
    post, planted = locate(root)
    records = load(post / "records.json")
    ids = records["text_ids"]
    arms = {}
    for arm in GRADE_ARMS + WITNESS_ARMS:
        per_text = {t: decisions(post, arm, t) for t in ids}
        rules = ("pass", "strict", "flag") if arm in GRADE_ARMS else ("witness",)
        arms[arm] = {"dates_utc": [records["arms"][arm]["started_utc_first"], records["arms"][arm]["started_utc_last"]],
                     "identity_with_primary_run": identity(post, planted, arm, ids),
                     "rules": {rule: {"per_grader": {who: tally(per_text, rule, who, ids) for who in MODELS + ("both",)},
                                      "routing": routing(per_text, rule, ids),
                                      "convention_errors": convention_errors(per_text, rule, ids)} for rule in rules},
                     "per_text": per_text}
    # The keyed re-run against the paper's primary witness gate, and the key-free arm against the keyed gate.
    def primary_witness(model, text_id):
        obligations = (load(planted / "runs" / "witness" / model / text_id / "parsed.json").get("parsed") or {}).get("obligations") or {}
        s_valid = sum(1 for key in ("lower_bound", "upper_bound") if isinstance(obligations.get(key), dict)
                      and obligations[key].get("status") == "written_and_valid")
        return "accept" if s_valid == 2 else "reject"

    primary = {t: {m: primary_witness(m, t) for m in MODELS} for t in ids}
    keyed = arms["witness_keyed_rerun"]["per_text"]
    keyfree = arms["witness_keyfree"]["per_text"]
    pair = lambda d: "accept" if all(d[m] == "accept" for m in MODELS) else "reject"
    comparisons = {
        "witness_keyed_rerun_vs_paper_witness_gate": {
            "per_grader_decisions_changed": frac(sum(keyed[t]["witness"][m] != primary[t][m] for t in ids for m in MODELS), 2 * len(ids)),
            "pair_decisions_changed": frac(sum(keyed[t]["witness"]["both"] != pair(primary[t]) for t in ids), len(ids))},
        "witness_keyfree_vs_paper_witness_gate": {
            "per_grader_changes": [{"text": t, "grader": m, "keyed": primary[t][m], "keyfree": keyfree[t]["witness"][m]}
                                   for t in ids for m in MODELS if keyfree[t]["witness"][m] != primary[t][m]],
            "pair_changes": [{"text": t, "keyed": pair(primary[t]), "keyfree": keyfree[t]["witness"]["both"]}
                             for t in ids if keyfree[t]["witness"]["both"] != pair(primary[t])]},
    }
    return {"schema_version": 1, "generated_by": "post_submission/summarize.py",
            "note": "Runs made by the author after submission (7 September 2026), on the same 32 texts; outside the paper's protocol and post hoc. "
                    "See post_submission/README.md for what each run changed.",
            "population": {"texts": len(ids), "broken": "F+G", "sound": "O+H (repair-tolerant convention)", "disputed_labels": list(DISPUTED)},
            "arms": arms, "comparisons": comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=HERE.parent)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    post, _ = locate(args.root.resolve())
    text = json.dumps(summarize(args.root.resolve()), indent=1, ensure_ascii=False) + "\n"
    target = post / "summary.json"
    if args.check:
        if not target.is_file() or target.read_text() != text:
            raise SystemExit("post_submission/summary.json differs from a recomputation from the records")
        print("post_submission/summary.json equals a recomputation from the records")
        return
    target.write_text(text)
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
