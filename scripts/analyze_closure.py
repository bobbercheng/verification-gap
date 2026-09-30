#!/usr/bin/env python3
"""Recompute the retrospective closure census and agreement check, offline.

Repository: python scripts/analyze_closure.py
Unpacked supplement: python scripts/analyze_closure.py --root .

Only retained annotations and independent grade receipts are read. No new
annotations are requested. A record is one annotation, not an independent
sample, a complete workspace, or necessarily a solver-authored final output.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re


REPAIRS = {"ours-kimi-K2-repair", "ours-glm52-repair"}
PUBLIC_COMMIT = "dbe872307883296c5f06bf8bcb90e6bfd0879364"


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def position(item):
    context = item["context"]
    if isinstance(context, str):
        match = re.search(r"-round(\d+)$", context)
        return (int(match.group(1)) if match else 1, item["turn"], 0)
    if item["id"].startswith("deedy-"):
        return (99, 99, 1)
    return (context, 0, 0)


def role(item, directory):
    if item["lineage"] in REPAIRS:
        return "local_repair_descendant"
    if directory == "closure_deedy":
        return "public_logged_write_file"
    if item["id"].startswith("deedy-"):
        return "public_final_file"
    return "local_discovery_snapshot"


def model_family(name):
    return "gpt-5.6-sol" if name.startswith("gpt-5.6-sol") else name


def census(data_root):
    records = []
    for directory in ("closure", "closure_deedy"):
        for path in sorted((data_root / directory).glob("*/annotation.json")):
            item = read(path)
            s = sum(item["grades"][key] == 2 for key in ("lower_bound", "upper_bound"))
            if s != item["S"]:
                raise ValueError(f"Derived S disagrees with retained S: {item['id']}")
            # Anonymized bundle annotations retain original_sha256 separately.
            original_hash = item.get("original_sha256", item["sha256"])
            records.append({
                "id": item["id"], "annotation_path": path.relative_to(data_root).as_posix(),
                "original_sha256": original_hash,
                "original_bytes": item.get("original_bytes", item["bytes"]),
                "lineage_label": item["lineage"], "model": item["model"],
                "model_family": model_family(item["model"]),
                "role": role(item, directory), "context": item["context"],
                "turn": item.get("turn"), "S": s,
                "order": list(position(item)),
                "scope": ("Serializer-produced candidate snapshot of discovery thinking"
                          if item["id"].startswith("glm53-") else
                          "One retained text; auxiliary files and intervening shell edits are excluded"),
            })
    if len({r["id"] for r in records}) != len(records):
        raise ValueError("Duplicate annotation IDs")
    by_group, by_hash = defaultdict(list), defaultdict(list)
    for record in records:
        by_group[record["lineage_label"]].append(record)
        by_hash[record["original_sha256"]].append(record["id"])
    groups = []
    for label, items in sorted(by_group.items()):
        items.sort(key=lambda item: (item["order"], item["id"]))
        first = next((i for i, item in enumerate(items) if item["S"] == 2), None)
        classification = ("repair_descendant" if label in REPAIRS else
                          "no_sampled_S2" if first is None else
                          "already_S2_at_first_sample" if first == 0 else
                          "sampled_0_to_2_transition")
        groups.append({
            "group": label, "classification": classification,
            "record_ids_in_order": [item["id"] for item in items],
            "S_sequence": [item["S"] for item in items],
            "first_sampled_S2_id": items[first]["id"] if first is not None else None,
            "last_sample_before_first_S2_id": items[first-1]["id"] if first else None,
            "note": ("Default-effort final S2 follows turn-11 S0; unannotated bash edits at turns 13-16 prevent exact crossing localization."
                     if label == "deedy-gpt-5.6-sol" else
                     "Round-4 turn-14 S2 precedes further bash edits before the 5/7 review; final file is post-repair."
                     if label == "deedy-kimi-k3" else
                     "Two sampled GPT attempts are grouped; the first is already S2."
                     if label == "ours-gpt56sol-ultra" else
                     "Repair output shares the local Kimi R1 seed and is not independent discovery."
                     if label in REPAIRS else
                     "Sampled text states do not locate all intermediate workspace states."),
        })
    classes = Counter(g["classification"] for g in groups)
    return {
        "schema_version": 1,
        "record_count": len(records), "distinct_original_texts": len(by_hash),
        "source_split": dict(sorted(Counter(r["role"] for r in records).items())),
        "S_counts": dict(sorted(Counter(str(r["S"]) for r in records).items())),
        "model_families": sorted({r["model_family"] for r in records}),
        "discovery_groups": len(groups) - len(REPAIRS),
        "repair_descendant_groups": len(REPAIRS),
        "group_classification_counts": dict(sorted(classes.items())),
        "duplicate_text_groups": [{"original_sha256": h, "record_ids": sorted(ids)}
                                  for h, ids in sorted(by_hash.items()) if len(ids) > 1],
        "groups": groups, "records": sorted(records, key=lambda r: r["id"]),
        "limitations": [
            "Groups aggregate attempts/contexts and are not independent statistical lineages.",
            "No retained text is scored S1; unsampled intermediate states can still have S1.",
            "The 26 public reconstructions cover selected write_file calls, not bash edits or every archived run.",
            "The public GPT Pro killed-402 archive has two excluded write_file snapshots.",
            "The four GLM-5.3 texts are serialized from discovery thinking, not direct discovery text responses.",
            "Local context fields sometimes index revisions/attempts rather than fresh contexts over one workspace.",
        ],
    }


def agreement(analysis_root, census_result):
    manifest = read(analysis_root / "grade_sources_manifest.json")
    for metadata in manifest.values():
        path = analysis_root / metadata["path"]
        if digest(path) != metadata["bundled_sha256"] or path.stat().st_size != metadata["bundled_bytes"]:
            raise ValueError(f"Grade source digest mismatch: {metadata['path']}")
    records = {r["id"]: r for r in census_result["records"]}
    public = read(analysis_root / "grade_sources/public_problem03.json")
    entries = []
    for source_index, grade in enumerate(public["entries"]):
        identifier = f"deedy-{grade['model']}-final"
        record = records[identifier]
        entries.append({
            "id": identifier, "original_sha256": record["original_sha256"],
            "S": record["S"], "grade": grade["score"], "grade_scale": 7,
            "independent_grade_high": grade["score"] >= 5,
            "grade_sources": ["grade_sources/public_problem03.json"],
            "grade_json_pointer": f"/entries/{source_index}",
            "grade_scope": "Public run/workspace grade, including supporting lemmas where consulted",
            "checkpoint_identity": {
                "repository": "https://github.com/deedy/imo-2026", "commit": PUBLIC_COMMIT,
                "path": f"results/{grade['model']}/problem-03/current.md",
            },
        })
    for identifier, filename in (("kimi-k2-repair", "kimi_repair.json"), ("glm52-repair", "glm_repair.json")):
        record = records[identifier]
        review = read(analysis_root / "grade_sources" / filename)
        if review["candidate_sha256"] != record["original_sha256"]:
            raise ValueError(f"Review/candidate identity mismatch: {identifier}")
        entries.append({
            "id": identifier, "original_sha256": record["original_sha256"],
            "S": record["S"], "grade": review["score"], "grade_scale": 7,
            "independent_grade_high": review["score"] >= 5,
            "grade_sources": [f"grade_sources/{filename}"], "grade_json_pointer": "/score",
            "grade_scope": "Blind review bound to the exact candidate SHA-256",
        })
    record = records["gpt56-ours-accepted"]
    review = read(analysis_root / "grade_sources/gpt_accepted_review.json")
    verification = read(analysis_root / "grade_sources/gpt_accepted_verification.json")
    gate = (review["verdict"] == "pass" and min(review["scores"].values()) >= 3
            and not review["fatal_issues"] and not review["unverified_claims"]
            and verification["verdict"] == "confirm"
            and not verification["dependency_gaps"] and not verification["required_fixes"])
    entries.append({
        "id": record["id"], "original_sha256": record["original_sha256"] , "S": record["S"],
        "grade": None, "rubric_scores": review["scores"], "gate_pass": gate,
        "independent_grade_high": gate,
        "grade_sources": ["grade_sources/gpt_accepted_review.json", "grade_sources/gpt_accepted_verification.json"],
        "grade_scope": "Review and dependency audit retained in the same accepted run as the sampled candidate",
    })
    for entry in entries:
        entry["agrees"] = (entry["S"] == 2) == entry["independent_grade_high"]
    unscored = read(analysis_root / "grade_sources/kimi_seed_unscored_review.json")
    if unscored["candidate_sha256"] != records["kimi-r1-c3"]["original_sha256"]:
        raise ValueError("Unscored seed receipt does not match the seed checkpoint")
    return {
        "schema_version": 1,
        "selection": "Nine pinned public final files, accepted local GPT candidate, and both local repair outputs",
        "comparison_rule": "S == 2 iff numeric independent grade >= 5/7 or local gate pass",
        "count": len(entries), "agreements": sum(e["agrees"] for e in entries),
        "disagreements": [e["id"] for e in entries if not e["agrees"]],
        "items": sorted(entries, key=lambda e: e["id"]),
        "excluded_historical_thirteenth_item": {
            "id": "kimi-r1-c3", "S": records["kimi-r1-c3"]["S"],
            "frozen_review_score": unscored["score"], "frozen_review_verdict": unscored["verdict"],
            "grade_source": "grade_sources/kimi_seed_unscored_review.json",
            "explanation": "The historical 6/7 label appears in retrospective prose; the frozen defect review records score:null. It is excluded from numeric/gate agreement.",
        },
        "limitations": [
            "This is an explicitly selected retrospective agreement check, not all available graded checkpoints or a preregistered calibration set.",
            "The two local repair outputs share a parent and are correlated.",
            "Public grades concern submitted workspaces; the closure annotator saw only the sampled text.",
            "The public Kimi final is post-repair; its 7/7 grade is not assigned to the different round-4 turn-14 text.",
            "S is a model annotation of written mechanisms, not a proof certificate.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check", action="store_true", help="Compare retained outputs without rewriting them")
    args = parser.parse_args()
    root = args.root.resolve()
    data_root = root / "artifacts" if (root / "artifacts/closure").is_dir() else root
    analysis_root = data_root / "closure_analysis"
    out = args.out or analysis_root
    if not args.check:
        out.mkdir(parents=True, exist_ok=True)
    counted = census(data_root)
    source_audit = read(analysis_root / "source_audit.json")
    audited_inputs = {r["id"]: (r["original_sha256"], r["original_bytes"])
                      for r in source_audit["records"]}
    if audited_inputs != {r["id"]: (r["original_sha256"], r["original_bytes"])
                          for r in counted["records"]}:
        raise ValueError("Retained annotations disagree with the source-input audit")
    compared = agreement(analysis_root, counted)
    for name, value in (("census.json", counted), ("agreement.json", compared)):
        if args.check:
            if read(out / name) != value:
                raise ValueError(f"Retained analysis differs from recomputed analysis: {name}")
        else:
            write(out / name, value)
    print(f"{counted['record_count']} records; {counted['distinct_original_texts']} distinct texts; "
          f"{counted['discovery_groups']} discovery groups + {counted['repair_descendant_groups']} repair groups")
    print("S counts:", counted["S_counts"])
    print("Discovery classifications:", counted["group_classification_counts"])
    print(f"Independent grade/gate agreement: {compared['agreements']}/{compared['count']}")


if __name__ == "__main__":
    main()
