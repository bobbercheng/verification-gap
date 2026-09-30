#!/usr/bin/env python3
"""Capture source evidence explicitly; build and verify the supplement offline.

Normal use: python3 scripts/supplementary.py build
Verify only: python3 scripts/supplementary.py verify --out supplementary
Capture a new snapshot: ... capture --imo26 DIR --neurogolf DIR --sources NEW_DIR
Capture checks original checkpoint hashes and leaves original evidence untouched.
Build reads only the portable snapshot and repository artifacts, never external
source paths. Standard library only; no model or network calls.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ("reviewer_swap_glm53", "reviewer_swap_kimik3", "reviewer_swap_kimik3_glm52", "closure", "closure_deedy",
          "closure_p6", "closure_p2", "closure_kimi", "closure_glm_rerun", "baseline_glm", "baseline_kimi", "closure_adjudicated",
          "closure_matrix", "closure_analysis", "corrections", "pilot_critique", "pilot_critique_ext",
          "closure_claude", "closure_gpt", "closure_repeat", "closure_repeat_claude", "baseline_claude",
          "verifier_evidence", "verifier_evidence_ext", "conclusion_sensitivity", "closure_ext", "replication_ext", "witness_discovery",
          "reference_adjudication", "planted_defects", "inspection_cost")
# Witness discovery (artifacts/witness_discovery/: PROTOCOL.md, DEVIATIONS.md, cases.json, propose/, check/, baseline/, recovery.json,
# results.json, RESULTS.md, the tables, certificates.json, whatever exists at build time) and the reference adjudication of its confirmed
# errors (artifacts/reference_adjudication/, everything under it if present). Their files name texts by local location: the identifying
# prefix of such a path is dropped and the file name kept (scrub keep_tail), and cases.json is re-linked to the released texts by digest.
TAIL_GROUPS = ("witness_discovery", "reference_adjudication", "planted_defects", "inspection_cost")
# Runs the author made after submission (7 September 2026) on the same 32 planted texts (camera-ready, Appendix S): the repository's
# post_submission/ (outside artifacts/, which holds the paper's own runs), bundled as post_submission/. Its records are byte-for-byte
# copies listed with their digests in records.json and tallied by summarize.py (both checked by verify()).
POST_SUBMISSION = "post_submission"
# Bundle documents (camera-ready): read from supplement_docs/ at build time and written at the bundle root.
DOCS = ("README.md", "NOTICE.md", "LICENSE", "CHANGES.md", "paper.pdf", "corrections.pdf")  # paper.pdf: the camera-ready paper as uploaded
DOCS_DIR = "supplement_docs"
# Dated corrections to frozen records (camera-ready): new files next to the records they amend; the records themselves are unchanged.
ADDENDA = tuple(f"{group}/ADDENDUM_2026-09-29.md" for group in ("planted_defects", "witness_discovery", "reference_adjudication",
                                                              "closure_adjudicated", "pilot_critique", "pilot_critique_ext"))
# Records of non-model judgments (each produced by a model under the author's direction and reviewed by the author; see ADDENDA).
JUDGMENT_RECORDS = ("reference_adjudication/LEDGER.md", "closure_adjudicated/adjudication_notes.md", "witness_discovery/recovery.json",
                    "pilot_critique/author_read.md", "pilot_critique_ext/author_read.md")
# Third-party source of the public-campaign texts (cited in the paper; see NOTICE.md).
THIRD_PARTY_SOURCE = {"repository": "https://github.com/deedy/imo-2026", "commit": "dbe872307883296c5f06bf8bcb90e6bfd0879364"}
WITNESS_SCRIPT = "witness_discovery.py"   # its `analyze --root .` runs offline from the bundle; propose/check/baseline need the model CLIs and the annotation module
OPTIONAL_SCRIPTS = (WITNESS_SCRIPT, "witness_checks.py", "reference_adjudication.py", "planted_defects.py", "inspection_cost.py", "text_store.py", "claim_audit.py")   # bundled when present in the repository
# Closure annotation groups: checkpoint manifest under artifacts/ (None = none), bundled prompt name, rubric source.
CLOSURE = {
    "closure": ("closure_checkpoints.json", "closure_system_p3.txt", ("script", "closure_annotate.py")),
    "closure_deedy": (None, "closure_system_p3.txt", ("script", "closure_annotate.py")),
    "closure_p6": ("closure_p6_checkpoints.json", "closure_system_p6.txt", ("file", "artifacts/closure_rubric_p6.txt")),
    "closure_p2": ("closure_p2_checkpoints.json", "closure_system_p2.txt", ("file", "artifacts/closure_rubric_p2.txt")),
}
CLOSURE_PROBLEM = {group: re.search(r"_p(\d)\.txt$", spec[1]).group(1) for group, spec in CLOSURE.items()}
LAYERS = ("raw", "glm", "kimi", "claude", "gpt", "written", "valid", "majority3", "rep1", "rep2", "rep3", "crep1", "crep2", "crep3")   # label layers written by closure_adjudicate.py
# Per-text ratings outside layer 0: `path` is re-linked to the bundled text at build time and hash-checked at verify time.
RERATING_GROUPS = ("closure_glm_rerun", "closure_kimi", "closure_claude", "closure_gpt", "closure_repeat", "closure_repeat_claude")   # closure ratings of distinct texts -> checkpoint_inputs/<sha>.md
BASELINE_GROUPS = ("baseline_glm", "baseline_kimi", "baseline_claude")        # ordinary 0-7 grades of the same texts under baseline_rubric_p<n>.txt
PILOT_GROUPS = ("pilot_critique", "pilot_critique_ext")    # paired critique pilot: grades_*/p<n>/<id>/annotation.json -> <group>/<run>/output.md
GATE_DIRS = tuple(f"{group}/gate_glm53" for group in PILOT_GROUPS)   # tool-free gate reviews of pilot outputs (reviewer-swap layout)
ADJUDICATED_FILES = ("labels.json", "reliability.json", "validity_overrides.json", "p2_routes.json", "adjudication_notes.md")
MATRIX_FILES = ("matrix.json", "regularities.json", "sensitivity.json", "public_grades.json", "table_matrix.tex", "table_budget.tex")
REVIEWER_GROUPS = ("reviewer_swap_glm53", "reviewer_swap_kimik3", "reviewer_swap_kimik3_glm52")
# Replication on the problems the paper does not analyze: closure_ext/p<N>/<rater>[/rep<k>]/<id>/annotation.json rates every checkpoint
# (claude_ckpt, ids of closure_p<N>_checkpoints.json) or every distinct text (claude_text/rep*, gpt_text, glm_text; ids of
# closure_distinct_p<N>.json) under artifacts/closure_rubric_p<N>.txt. Texts are bundled once per digest as checkpoint_inputs_ext/<sha>.md,
# listed in checkpoint_inputs_ext/manifest.json (one record per rating), and every rating `path` is re-linked to that copy. Rating passes
# may be incomplete: nothing below assumes a count or that every rater covered every text.
EXT_PROBLEMS = ("1", "4", "5")
EXT_FILES = tuple(f"closure_rubric_p{n}.txt" for n in EXT_PROBLEMS) + tuple(f"closure_p{n}_checkpoints.json" for n in EXT_PROBLEMS) + \
    tuple(f"closure_distinct_p{n}.json" for n in EXT_PROBLEMS)
ARTIFACT_FILES = ("trajectory_stats_public.json", "glm52_gate_passes.json", "closure_distinct_p3.json", "closure_distinct_p6.json",
                  "closure_distinct_p2.json", "baseline_rubric_p3.txt", "baseline_rubric_p6.txt", "baseline_rubric_p2.txt", "closure_repeat_PROTOCOL.md") + EXT_FILES
NEMOTRON = ("imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d", "imo-2026-p1-dd064edd0e094391befec955da850012", "imo-2026-p5-f3bd351bad3d47879d5aa8cddbcab3c5")
TABLE = (
    ("gpt-5.6-sol", 1, "efd2737d", "cdc88080cd219cde", "be0c06f7334e3089", "85689a90d97f5c08"),
    ("gpt-5.6-sol", 2, "3c91a536", "eb189909d1bd39a5", "ed46e718c6dbca35", "43e95c9fa5f8bcfc"),
    ("gpt-5.6-sol", 3, "ffa748a9", "cb1bcbb2df8fa81b", "50ee118353e5c1eb", "d7a817dced330831"),
    ("gpt-5.6-sol", 4, "247f5b7c", "4d0a20e17bde3191", "0c3ed2d97b8663ac", "bb932d8de618b006"),
    ("gpt-5.6-sol", 5, "e26aacad", "3090f2134de489ae", "e160a9286b0200cc", "33bc43ad338e5f1a"),
    ("gpt-5.6-sol", 6, "3acd733f", "d31e74d07a68c601", "50750125557778fb", "045730c351052b59"),
    ("nemotron", 1, "2853f8e6", "1a10db6e23dca33d", "eafd1f97c6a2cd84", "631e3fa409d58dc1"),
    ("nemotron", 1, "dd064edd", "f34c81fda467c0c6", "b03adf252b32f492", "9dc3e2d46672c524"),
    ("nemotron", 5, "f3bd351b", "28cf6b5ebb024dc2", "cbf2850544e3b88a", "a200369d810a6368"),
)
# Local-path scan (camera-ready): the paper is no longer anonymous, so README.md and NOTICE.md name the author and the release
# repository; what must never ship is a local path (home directory or agent scratch checkout).
IDENTIFYING = re.compile(r"/(?:home|Users)/|/tmp/" + "claude-", re.I)
# Links into the author's private development repository are replaced (none occur at the camera-ready build); the public release
# repository, https://github.com/bobbercheng/verification-gap, is named in README.md and NOTICE.md.
PRIVATE_REPOSITORY = re.compile(r"https://github\.com/bobbercheng/mathai_neurips_2026[A-Za-z0-9_./-]*", re.I)
SECRET = re.compile(r"\bsk-(?:or-v1-)?[A-Za-z0-9_-]{24,}|\bBearer\s+[A-Za-z0-9_.-]{24,}")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def scrub(data, replacements=(), keep_tail=False):
    """Remove local paths from a copy; preserve original bytes if no replacement is needed.
    keep_tail: a local path loses only its identifying prefix (home directory, scratch checkout) and keeps the file name it points at
    as [local-path]/<tail>; otherwise the whole path becomes [local-path]."""
    text = data.decode("utf-8")
    for original, bundled in sorted(replacements, key=lambda pair: -len(pair[0])):
        text = text.replace(original, bundled)
    if keep_tail:
        text = re.sub(r"/tmp/[A-Za-z]+-[0-9]+(?:/[A-Za-z0-9_.-]+)*?/scratchpad/", "[local-path]/", text)   # the agent scratch checkout
        text = re.sub(r"/(?:home|Users)/[A-Za-z0-9_.-]+/", "[local-path]/", text)
    text = re.sub(r"/(?:home|Users|tmp|var/tmp)/[A-Za-z0-9_./-]+", "[local-path]", text)
    # camera-ready (CHANGES.md): a coding-assistant session id with its scratchpad segment, left behind when a path literal is split
    # across source lines, and the private directory tail of a path under the author's Kaggle workspace (the file name is kept)
    text = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/scratchpad/", "/", text)
    text = re.sub(r"\[local-path\]/Kaggle/(?:[A-Za-z0-9_.-]+/)+", "[local-path]/", text)
    text = PRIVATE_REPOSITORY.sub("[private-repository]", text)
    require(not SECRET.search(text), "Possible credential in selected evidence; refusing to package it")
    return text.encode("utf-8")


def rubric(script):
    # Read the literal without importing API runners or executing their code.
    for node in ast.parse((ROOT / "scripts" / script).read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "RUBRIC" for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"No RUBRIC in {script}")


def rubric_text(source):
    kind, name = source
    return rubric(name) if kind == "script" else (ROOT / name).read_text()


def closure_prompts():
    """{bundled prompt name: exact system text} for every closure annotation group and every replication problem."""
    prompts = {prompt: rubric_text(source) for _, prompt, source in CLOSURE.values()}
    prompts.update({f"closure_system_p{n}.txt": rubric_text(("file", f"artifacts/closure_rubric_p{n}.txt")) for n in EXT_PROBLEMS})
    return prompts


def annotations(group=None):
    groups = (group,) if group else tuple(CLOSURE)
    return [(p, read_json(p)) for g in groups for p in sorted((ROOT / "artifacts" / g).glob("*/annotation.json"))]


def ext_problem(relative):
    """Problem number from the p<N> component of a closure_ext path or group (closure_ext/p4/claude_text/rep2/<id>/annotation.json)."""
    return next(part[1:] for part in Path(relative).parts if re.fullmatch(r"p[1-6]", part))


def ext_annotations():
    """(path, annotation) for every replication rating present under artifacts/closure_ext, at any depth."""
    base = ROOT / "artifacts/closure_ext"
    return [(p, read_json(p)) for p in sorted(base.rglob("annotation.json"))] if base.is_dir() else []


def ext_record(path, item):
    """Manifest record of one replication rating; `group` is its rating directory under closure_ext/ (p1/claude_ckpt, p4/claude_text/rep2, ...)."""
    relative = path.relative_to(ROOT / "artifacts")
    return {"id": item["id"], "group": str(relative.parent.parent.relative_to("closure_ext")), "annotation_path": str(relative),
            "input_path": f"checkpoint_inputs_ext/{item['sha256']}.md", "original_sha256": item["sha256"], "original_bytes": item["bytes"]}


def ext_manifest(records):
    groups = sorted({r["group"] for r in records})
    return {"schema_version": 2, "path_base": "bundle root", "count": len(records),
            "groups": {g: sum(r["group"] == g for r in records) for g in groups}, "records": records}


def file_record(path, base):
    data = path.read_bytes()
    return {"path": str(path.relative_to(base)), "bytes": len(data), "sha256": sha(data)}


def capture(args):
    require(not args.sources.exists(), "Snapshot already exists; use a new --sources directory for an explicit refresh")
    imo, neuro = args.imo26.resolve(), args.neurogolf.resolve()
    runs = neuro / "portfolio_transfer/runtime/imo-2026/runs"
    pairs = []
    repair_replacements = []
    for name in ("problems", "gpt-5.6-sol/solutions", "gpt-5.6-sol/reviews", "gpt-5.6-sol/verifications",
                 "nemotron-3-ultra-550b-a55b/solutions", "nemotron-3-ultra-550b-a55b/reviews",
                 "nemotron-3-ultra-550b-a55b/verifications", "nemotron-3-ultra-550b-a55b/unresolved", "cross-validation"):
        require((imo / name).is_dir(), f"Missing evidence directory: {name}")
        pairs.extend((p, str(p.relative_to(imo))) for p in sorted((imo / name).rglob("*")) if p.is_file())
    for name in ("results.json", "gpt-5.6-sol/README.md", "nemotron-3-ultra-550b-a55b/README.md"):
        pairs.append((imo / name, name))
    for run in NEMOTRON:
        for name in ("statement.md", "candidate_v1.md", "candidate_v1.json", "review_v1.json", "verification_v1.json", "logic_audit_v1.json"):
            pairs.append((runs / run / name, f"run_artifacts/nemotron/{run}/{name}"))
        # Actual applied prompt variants, without provider stdout/request logs.
        pairs.extend((p, f"run_artifacts/nemotron/{run}/{p.relative_to(runs / run)}") for p in sorted((runs / run).glob("*/prompt.md")))
    for model, name in (("kimi-k3", "kimi-k3-openrouter-p3-r1-repair-k2-review"), ("glm-5.2", "glm52-openrouter-p3-r1-repair-r2-review")):
        source = neuro / "work/fullscore_portfolio_loop" / name
        repair_manifest = read_json(source / "manifest.json")
        require(sha((source / "sources/candidate.md").read_bytes()) == repair_manifest["candidate_sha256"],
                f"Repair source candidate digest mismatch: {model}")
        repair_replacements.append((repair_manifest["candidate_source_path"], f"p3_repairs/{model}/sources/candidate.md"))
        for relative in ("sources/candidate.md", "sources/statement.md", "review.json", "manifest.json", "invocation/prompt.md"):
            pairs.append((source / relative, f"p3_repairs/{model}/{relative}"))
    # GLM-5.2's gate-passing candidates (re-graded by Kimi K3) with their original review/verification records.
    for entry in read_json(ROOT / "artifacts/glm52_gate_passes.json"):
        run = Path(entry["path"]).parent
        require(run.is_relative_to(neuro), f"GLM-5.2 run outside the neurogolf tree: {run}")
        n, v = entry["n"], entry["version"]
        pairs.append((Path(entry["path"]), entry["candidate_file"]))
        pairs.append((run / f"review_v{v}.json", f"glm-5.2/reviews/problem-{n}.json"))
        pairs.append((run / f"verification_v{v}.json", f"glm-5.2/verifications/problem-{n}.json"))
    prompts = closure_prompts()
    inputs = []
    for path, item in annotations():
        original = Path(item["path"])
        data = original.read_bytes()
        require(sha(data) == item["sha256"] and len(data) == item["bytes"], f"Original checkpoint hash/size mismatch: {item['id']}")
        group = path.relative_to(ROOT / "artifacts").parts[0]
        require(item["rubric_sha256"] == sha(prompts[CLOSURE[group][1]].encode()), f"Rubric hash mismatch: {item['id']}")
        relative = f"checkpoint_inputs/{item['sha256']}.md"
        pairs.append((original, relative))
        record = {"id": item["id"], "group": group, "annotation_path": str(path.relative_to(ROOT / "artifacts")), "input_path": relative,
                  "original_sha256": item["sha256"], "original_bytes": len(data)}
        # Gate outcome for our candidate_vN.md checkpoints: the sibling review_vN.json (used by closure_matrix.py).
        match = re.fullmatch(r"candidate_v(\d+)\.md", original.name)
        review = original.parent / f"review_v{match.group(1)}.json" if match else None
        if review and review.is_file():
            record["review_path"] = f"checkpoint_reviews/{item['sha256']}.json"
            pairs.append((review, record["review_path"]))
            verification = original.parent / f"verification_v{match.group(1)}.json"
            if verification.is_file():
                record["verification_path"] = f"checkpoint_reviews/{item['sha256']}.verification.json"
                pairs.append((verification, record["verification_path"]))
        inputs.append(record)
    require(len(inputs) == len({r["id"] for r in inputs}), "Duplicate annotation ids across closure groups")
    ext_inputs = []
    for path, item in ext_annotations():
        original = Path(item["path"])
        data = original.read_bytes()
        record = ext_record(path, item)
        require(sha(data) == item["sha256"] and len(data) == item["bytes"], f"Original replication text hash/size mismatch: {record['annotation_path']}")
        require(item["rubric_sha256"] == sha(prompts[f"closure_system_p{ext_problem(record['group'])}.txt"].encode()),
                f"Rubric hash mismatch: {record['annotation_path']}")
        pairs.append((original, record["input_path"]))
        ext_inputs.append(record)
    for name in ARTIFACT_FILES:
        pairs.append((ROOT / "artifacts" / name, name))
    replacements = repair_replacements + [(str(source), relative) for source, relative in pairs]
    replacements += [(str(runs / run), f"run_artifacts/nemotron/{run}") for run in NEMOTRON]
    replacements.append((str(imo) + "/", ""))
    stage = Path(tempfile.mkdtemp(prefix="supplementary-sources-"))
    provenance = {}
    for original, relative in pairs:
        raw = original.read_bytes()
        data = scrub(raw, replacements)
        if relative == "gpt-5.6-sol/README.md":
            before, separator, _ = data.decode().partition("## PDF")
            if separator:
                data = (before + "## PDF\n\nThe separate PDF report and its builder are not distributed in this bundle.\n"
                        "The complete Markdown proofs, reviews, and verifications are included above.\n").encode()
        target = stage / "files" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        require(not target.exists() or target.read_bytes() == data, f"Conflicting copies: {relative}")
        target.write_bytes(data)
        label = "IMO26/" + str(original.relative_to(imo)) if original.is_relative_to(imo) else (
            "neurogolf-2026/" + str(original.relative_to(neuro)) if original.is_relative_to(neuro) else
            "public-checkpoint/" + "/".join(original.parts[-3:]))
        provenance[relative] = {"path": relative, "source_label": label, "original_sha256": sha(raw), "original_bytes": len(raw),
                               "bundled_sha256": sha(data), "bundled_bytes": len(data), "anonymized": raw != data}
    for record in inputs:
        record.update({key: provenance[record["input_path"]][key] for key in ("bundled_sha256", "bundled_bytes", "anonymized")})
    write_json(stage / "files/checkpoint_inputs/manifest.json", {"schema_version": 2, "path_base": "bundle root", "count": len(inputs),
               "groups": {g: sum(r["group"] == g for r in inputs) for g in CLOSURE}, "records": inputs})
    for record in ext_inputs:
        record.update({key: provenance[record["input_path"]][key] for key in ("bundled_sha256", "bundled_bytes", "anonymized")})
    write_json(stage / "files/checkpoint_inputs_ext/manifest.json", ext_manifest(ext_inputs))
    table = []
    for route, problem, lineage, *prefixes in TABLE:
        if route == "gpt-5.6-sol":
            paths = [f"{route}/{kind}/problem-{problem}.{ext}" for kind, ext in (("solutions", "md"), ("reviews", "json"), ("verifications", "json"))]
        else:
            run = next(run for run in NEMOTRON if lineage in run)
            paths = [f"run_artifacts/nemotron/{run}/{kind}_v1.{ext}" for kind, ext in (("candidate", "md"), ("review", "json"), ("verification", "json"))]
        row = {"route": route, "problem": problem, "lineage": lineage, "artifacts": {}}
        for kind, path, prefix in zip(("candidate", "review", "verification"), paths, prefixes):
            record = provenance[path]
            require(record["original_sha256"].startswith(prefix), f"Paper digest mismatch: {lineage} {kind}")
            require(not record["anonymized"], f"Table artifact unexpectedly changed: {path}")
            row["artifacts"][kind] = {"path": path, "sha256": record["bundled_sha256"], "paper_prefix": prefix}
        if route == "nemotron":
            path = f"run_artifacts/nemotron/{run}/logic_audit_v1.json"
            row["artifacts"]["logic_audit"] = {"path": path, "sha256": provenance[path]["bundled_sha256"]}
        table.append(row)
    write_json(stage / "files/run_artifacts/manifest.json", {"schema_version": 1, "rows": table})
    for name, value in list(prompts.items()) + [("reviewer_swap_system_template.txt", rubric("reviewer_swap.py"))]:
        path = stage / "files/prompts" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)
    manifest = {"schema_version": 1, "path_base": "bundle root",
                "files": [file_record(p, stage / "files") for p in sorted((stage / "files").rglob("*")) if p.is_file()],
                "source_provenance": list(provenance.values())}
    write_json(stage / "SOURCES.json", manifest)
    args.sources.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(stage), args.sources)
    print(f"Captured {len(manifest['files'])} portable files; {len(inputs)} checkpoint records, {len({r['original_sha256'] for r in inputs})} distinct inputs; "
          f"{len(ext_inputs)} replication ratings of {len({r['original_sha256'] for r in ext_inputs})} distinct texts")


def files(base):
    """Every file under base, except a git checkout's own .git/ (so that a clone of the release repository verifies)."""
    return [p for p in base.rglob("*") if p.is_file() and p.relative_to(base).parts[0] != ".git"]


def verify_manifest(base, records, exhaustive=False):
    listed = set()
    for row in records:
        relative = Path(row["path"])
        require(not relative.is_absolute() and ".." not in relative.parts, f"Unsafe manifest path: {relative}")
        require(str(relative) not in listed, f"Repeated manifest path: {relative}")
        listed.add(str(relative))
        path = base / relative
        require(path.is_file(), f"Missing payload: {relative}")
        data = path.read_bytes()
        require(sha(data) == row["sha256"] and len(data) == row["bytes"], f"Payload hash/size mismatch: {relative}")
    if exhaustive:
        actual = {str(p.relative_to(base)) for p in files(base) if p.name != "MANIFEST.json"}
        require(actual == listed, f"Manifest coverage mismatch: {sorted(actual ^ listed)}")


def recorded_roots():
    """Repository roots named by stored records: this checkout, plus the checkout the pilot grades were recorded in when the build
    runs elsewhere (e.g. a git worktree). Found from the records themselves, so no path is written into this script."""
    roots = {ROOT}
    for group in PILOT_GROUPS:
        for path in (ROOT / "artifacts" / group).glob("grades_*/p*/*/annotation.json"):
            head, separator, _ = str(read_json(path).get("path", "")).partition(f"/artifacts/{group}/")
            if separator and head.startswith("/"):
                roots.add(Path(head))
    return sorted(roots, key=str)


def rebase(path):
    """A recorded absolute path under any recorded root's artifacts/ -> the same file under this checkout's artifacts/."""
    for root in recorded_roots():
        if path.is_relative_to(root / "artifacts"):
            return ROOT / "artifacts" / path.relative_to(root / "artifacts")
    return path


def build(args):
    source_manifest = read_json(args.sources / "SOURCES.json")
    verify_manifest(args.sources / "files", source_manifest["files"], exhaustive=True)
    stage = Path(tempfile.mkdtemp(prefix="supplementary-build-")) / "bundle"
    shutil.copytree(args.sources / "files", stage)
    inputs = read_json(stage / "checkpoint_inputs/manifest.json")["records"]
    by_id = {record["id"]: record for record in inputs}
    active = annotations()
    require(set(by_id) == {item["id"] for _, item in active}, "Snapshot does not cover current annotations; capture new sources explicitly")
    replacements = []
    for _, item in active:
        record = by_id[item["id"]]
        require(item["sha256"] == record["original_sha256"] and item["bytes"] == record["original_bytes"], f"Checkpoint identity changed: {item['id']}")
        replacements.append((item["path"], record["input_path"]))
    # Repository artifact paths recorded by the pilot scripts become bundle-relative (the bundle mirrors artifacts/).
    replacements += [(str(root / "artifacts") + "/", "") for root in recorded_roots()]
    # Replication ratings are matched to captured texts by digest, so ratings that arrived after the capture need no new snapshot;
    # a rating of a text the snapshot lacks does.
    require((stage / "checkpoint_inputs_ext/manifest.json").is_file(), "Snapshot has no replication texts (checkpoint_inputs_ext/); capture new sources explicitly")
    ext_by_sha = {r["original_sha256"]: r for r in read_json(stage / "checkpoint_inputs_ext/manifest.json")["records"]}
    ext_inputs = []
    for path, item in ext_annotations():
        record = ext_by_sha.get(item["sha256"])
        require(record is not None and record["original_bytes"] == item["bytes"],
                f"Snapshot does not cover the text rated by {path.relative_to(ROOT / 'artifacts')}; capture new sources explicitly")
        replacements.append((item["path"], record["input_path"]))
        ext_inputs.append({**ext_record(path, item), **{key: record[key] for key in ("bundled_sha256", "bundled_bytes", "anonymized")}})
    replacements = sorted(set(replacements))
    historical = []
    for group in GROUPS:
        source = ROOT / "artifacts" / group
        if not source.exists():
            continue
        if group == "planted_defects" and not (source / "plantings.json").exists():
            continue   # the planted-defect experiment is bundled only once its plantings and protocol exist
        for path in sorted(source.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            relative = path.relative_to(ROOT / "artifacts")
            target = stage / relative
            # Older unreferenced retries can survive an --only-failed rerun (any annotation group).
            if re.fullmatch(r"response_attempt\d+\.json", path.name) and (path.parent / "annotation.json").is_file():
                item = read_json(path.parent / "annotation.json")
                names = {f"response_attempt{attempt['attempt']}.json" for attempt in item["attempts"]}
                if path.name not in names:
                    target = stage / "historical_responses" / relative
                    historical.append({"path": str(target.relative_to(stage)), "annotation_id": item["id"],
                                       "reason": "Not referenced by active annotation attempts; retained as an older response, not used in reported grades."})
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(scrub(path.read_bytes(), replacements, keep_tail=group in TAIL_GROUPS))
    for path in sorted((ROOT / POST_SUBMISSION).rglob("*")) if (ROOT / POST_SUBMISSION).is_dir() else []:
        if path.is_file() and "__pycache__" not in path.parts:
            target = stage / POST_SUBMISSION / path.relative_to(ROOT / POST_SUBMISSION)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(scrub(path.read_bytes()))
    for path, item in active:
        record = by_id[item["id"]]
        changed = dict(item)
        changed.update({"path": record["input_path"], "path_base": "bundle root", "sha256": record["bundled_sha256"],
                        "bytes": record["bundled_bytes"], "original_sha256": record["original_sha256"],
                        "original_bytes": record["original_bytes"], "input_anonymized": record["anonymized"]})
        write_json(stage / path.relative_to(ROOT / "artifacts"), changed)
    by_sha = {r["original_sha256"]: r for r in inputs}

    def relink(item, records=by_sha):
        """Point a per-text record at its bundled input; carry the original digest if that copy was anonymized."""
        record = records.get(item.get("sha256"))
        if record is None:
            return False
        item.update({"path": record["input_path"], "path_base": "bundle root"})
        if record["anonymized"]:
            item.update({"original_sha256": record["original_sha256"], "original_bytes": record["original_bytes"], "sha256": record["bundled_sha256"],
                         "bytes": record["bundled_bytes"], "input_anonymized": True})
        return True

    for group, records in [(group, by_sha) for group in RERATING_GROUPS + BASELINE_GROUPS] + [("closure_ext", ext_by_sha)]:
        for path in sorted((stage / group).rglob("annotation.json")):
            item = read_json(path)
            require(relink(item, records), f"Rating of a text that is not a released checkpoint input: {path.relative_to(stage)}")
            write_json(path, item)
        for path in sorted((stage / group).rglob("summary.json")):
            summary = read_json(path)
            for item in summary.get("items", []):
                relink(item, records)
            write_json(path, summary)
    # Witness-discovery case list (present only if that experiment ran before the build): every case points at the released copy of
    # its text, in the P2/P3/P6 corpus or the P1/P4/P5 replication corpus, found by digest; a text in neither keeps its anonymized path.
    cases_path = stage / "witness_discovery/cases.json"
    if cases_path.is_file():
        try:
            cases = read_json(cases_path)
        except ValueError:
            cases = None
            print("note: witness_discovery/cases.json is not complete JSON (experiment still writing?); copied as is")
        if cases is not None:
            unlinked = [case.get("id") for case in cases.get("cases", []) if not (relink(case, by_sha) or relink(case, ext_by_sha))]
            if unlinked:
                print("note: witness_discovery cases without a released text: " + ", ".join(map(str, unlinked)))
            write_json(cases_path, cases)
    for problem, records in [(p, by_sha) for p in dict.fromkeys(CLOSURE_PROBLEM.values())] + [(p, ext_by_sha) for p in EXT_PROBLEMS]:
        name = f"closure_distinct_p{problem}.json"
        if (stage / name).exists():
            rows = read_json(stage / name)
            for row in rows:
                require(relink(row, records), f"Distinct text without a released copy: {name} {row['id']}")
            write_json(stage / name, rows)
    for problem in EXT_PROBLEMS:
        # The checkpoint manifest carries no digest: resolve each id through the distinct-text manifest's record_ids.
        sha_by_id = {record_id: row["sha256"] for row in read_json(ROOT / "artifacts" / f"closure_distinct_p{problem}.json") for record_id in row["record_ids"]}
        name = f"closure_p{problem}_checkpoints.json"
        rows = read_json(stage / name)
        for row in rows:
            record = ext_by_sha.get(sha_by_id.get(row["id"]))
            require(record is not None, f"Checkpoint without a released text: {name} {row['id']}")
            row.update({"path": record["input_path"], "path_base": "bundle root"})
        write_json(stage / name, rows)
    write_json(stage / "checkpoint_inputs_ext/manifest.json", ext_manifest(ext_inputs))
    for group in PILOT_GROUPS:
        for path in sorted((stage / group).glob("grades_*/p*/*/annotation.json")):
            item = read_json(path)
            source = rebase(Path(read_json(ROOT / "artifacts" / path.relative_to(stage))["path"]))   # repository copy: unscrubbed path
            require(source.is_relative_to(ROOT / "artifacts" / group) and source.name == "output.md", f"Pilot grade input outside {group}/: {item['id']}")
            relative = str(source.relative_to(ROOT / "artifacts"))
            require((stage / relative).is_file(), f"Pilot output not bundled: {relative}")
            require(sha(source.read_bytes()) == item["sha256"], f"Pilot output changed since it was graded: {item['id']}")
            data = (stage / relative).read_bytes()
            item.update({"path": relative, "path_base": "bundle root"})
            if sha(data) != item["sha256"]:
                item.update({"original_sha256": item["sha256"], "original_bytes": item["bytes"], "sha256": sha(data), "bytes": len(data), "input_anonymized": True})
            write_json(path, item)
    for group, (manifest_name, _, _) in CLOSURE.items():
        path = stage / group / "summary.json"
        if path.exists():
            summary = read_json(path)
            summary["items"] = [read_json(stage / by_id[item["id"]]["annotation_path"]) for item in summary["items"]]
            write_json(path, summary)
        if manifest_name:
            initial = read_json(ROOT / "artifacts" / manifest_name)
            for item in initial:
                item.update({"path": by_id[item["id"]]["input_path"], "path_base": "bundle root"})
            write_json(stage / group / "checkpoints_manifest.json", initial)
    write_json(stage / "historical_responses/manifest.json", {"files": historical})
    write_json(stage / "provenance/source_snapshot.json", source_manifest)
    prompt_records = []
    for group in REVIEWER_GROUPS + GATE_DIRS:
        for path in sorted((stage / group).glob("*/request_redacted.json")):
            request, meta = read_json(path), read_json(path.parent / "meta.json")
            system = request["system"].encode()
            require(sha(system) == meta["rubric_sha256"], f"Reviewer prompt hash mismatch: {path.parent.name}")
            name = f"prompts/{group}/{path.parent.name}.txt"
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(system)
            prompt_records.append({"path": name, "sha256": sha(system), "meta_path": str((path.parent / 'meta.json').relative_to(stage))})
    write_json(stage / "prompts/manifest.json", {"closure_systems": {g: f"prompts/{spec[1]}" for g, spec in CLOSURE.items()},
               "closure_ext_systems": {f"p{n}": f"prompts/closure_system_p{n}.txt" for n in EXT_PROBLEMS},
               "reviewer_systems": prompt_records,
               "note": "Closure, reviewer-swap and pilot-gate system text is exact. Campaign and repair prompts retain wording with local paths anonymized; original/bundled digests are in provenance/source_snapshot.json."})
    for name in DOCS:
        source = ROOT / DOCS_DIR / name
        require(source.is_file(), f"Missing bundle document: {DOCS_DIR}/{name}")
        (stage / name).write_bytes(source.read_bytes())
    write_json(stage / "THIRD_PARTY.json", third_party_inventory(stage))
    # The distributed verifier is this script, unchanged.
    (stage / "verify_bundle.py").write_bytes(Path(__file__).read_bytes())
    (stage / "scripts").mkdir(exist_ok=True)
    for script in ("analyze_closure.py", "closure_matrix.py", "closure_adjudicate.py", "pilot_critique.py", "conclusion_sensitivity.py", "verifier_evidence.py", "cli_transport.py",
                   "replication_ext.py") + OPTIONAL_SCRIPTS:
        source = ROOT / "scripts" / script
        if script in OPTIONAL_SCRIPTS and not source.is_file():
            continue
        (stage / "scripts" / script).write_bytes(scrub(source.read_bytes(), keep_tail=script == WITNESS_SCRIPT))
    rows = [file_record(p, stage) for p in sorted(stage.rglob("*")) if p.is_file()]
    write_json(stage / "MANIFEST.json", {"files": rows})
    verify(stage)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        backup = Path(tempfile.mkdtemp(prefix="previous-supplementary-")) / "bundle"
        shutil.move(str(args.out), backup)
    shutil.move(str(stage), args.out)
    archive = args.out.with_suffix(".zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(args.out.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(str(path.relative_to(args.out)), date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type, info.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
                bundle.writestr(info, path.read_bytes())
    print(f"Built {args.out.name}/ and {archive.name}: {len(rows)} payload files")


def response_grades(annotation_dir, item):
    """Grades JSON of the last parsed active response, or None when no attempt parsed (a file is not a rating)."""
    expected = {f"response_attempt{attempt['attempt']}.json" for attempt in item["attempts"]}
    actual = {p.name for p in annotation_dir.glob("response_attempt*.json")}
    require(actual == expected, f"Stale or missing active response: {item['id']}")
    parsed = [attempt for attempt in item["attempts"] if attempt["parsed"]]
    if not parsed:
        return None
    response = read_json(annotation_dir / f"response_attempt{parsed[-1]['attempt']}.json")
    text = "".join(block.get("text", "") for block in response.get("content", []) if block.get("type") == "text")
    match = re.search(r"\{.*\}", text, re.S)
    require(match is not None, f"Parsed active response holds no JSON object: {item['id']}")
    return json.loads(match.group())


def closure_score(grades):
    return int(grades.get("lower_bound", 0) == 2) + int(grades.get("upper_bound", 0) == 2)


def verify_ratings(out, inputs):
    """Layer-1 re-ratings, baseline grades and pilot grades: each record hashes to the bundled text it names and to its bundled rubric."""
    bundled_inputs = {r["input_path"] for r in inputs}
    counts = {}
    for group in RERATING_GROUPS + BASELINE_GROUPS + PILOT_GROUPS:
        paths = sorted((out / group).glob("grades_*/p*/*/annotation.json")) if group in PILOT_GROUPS else sorted((out / group).rglob("annotation.json"))
        for path in paths:
            item = read_json(path)
            relative = Path(item["path"])
            require(not relative.is_absolute() and ".." not in relative.parts and item.get("path_base") == "bundle root",
                    f"Rating path is not bundle-relative: {group}/{item['id']}")
            require((out / relative).is_file(), f"Rated text is not bundled: {group}/{item['id']} -> {relative}")
            data = (out / relative).read_bytes()
            require(sha(data) == item["sha256"] and len(data) == item["bytes"], f"Rated text differs from the bundled input: {group}/{item['id']}")
            problem = str(item.get("problem") or next(part[1:] for part in reversed(path.parts) if re.fullmatch(r"p[236]", part)))
            if group in PILOT_GROUPS:
                require(relative.parts[0] == group and relative.parts[1].startswith(f"p{problem}-") and relative.name == "output.md",
                        f"Pilot grade points outside its run directory: {group}/{item['id']}")
                rubric_path = out / "prompts" / f"closure_system_p{problem}.txt"
            else:
                require(str(relative) in bundled_inputs, f"Rating of a text that is not a released checkpoint input: {group}/{item['id']}")
                rubric_path = out / (f"baseline_rubric_p{problem}.txt" if group in BASELINE_GROUPS else f"prompts/closure_system_p{problem}.txt")
            require(rubric_path.is_file() and item["rubric_sha256"] == sha(rubric_path.read_bytes()), f"Rubric digest mismatch: {group}/{item['id']}")
            grades = response_grades(path.parent, item)
            require(grades == item["grades"], f"Active response grades differ from annotation: {group}/{item['id']}")
            if grades is None:
                require(item["S"] is None, f"Score without a parsed response: {group}/{item['id']}")
            elif group in BASELINE_GROUPS:
                require(item["S"] is None and isinstance(grades.get("grade"), int) and 0 <= grades["grade"] <= 7, f"Baseline grade out of range: {item['id']}")
            else:
                require(item["S"] == closure_score(grades), f"Closure score mismatch: {group}/{item['id']}")
            counts[group] = counts.get(group, 0) + 1
    return counts


def verify_replication(out):
    """P1/P4/P5 replication: every closure_ext rating hashes to the bundled text and rubric it names, and every text manifest resolves."""
    manifest = read_json(out / "checkpoint_inputs_ext/manifest.json")
    records = manifest["records"]
    require(len(records) == manifest["count"] and len({r["annotation_path"] for r in records}) == len(records), "Replication record count/uniqueness mismatch")
    actual = {str(p.relative_to(out)) for p in (out / "closure_ext").rglob("annotation.json")} if (out / "closure_ext").is_dir() else set()
    require(actual == {r["annotation_path"] for r in records}, "Replication coverage does not match closure_ext annotations")
    bundled = {r["input_path"] for r in records}
    counts = {}
    for record in records:
        relative = Path(record["input_path"])
        require(relative.parts[0] == "checkpoint_inputs_ext" and len(relative.parts) == 2, f"Replication input outside checkpoint_inputs_ext/: {record['annotation_path']}")
        data = (out / relative).read_bytes()
        require(sha(data) == record["bundled_sha256"] and len(data) == record["bundled_bytes"], f"Replication input mismatch: {record['annotation_path']}")
        require(record["anonymized"] or sha(data) == record["original_sha256"], f"Original replication input digest mismatch: {record['annotation_path']}")
        item = read_json(out / record["annotation_path"])
        require(item["path"] == record["input_path"] and item.get("path_base") == "bundle root" and item["sha256"] == record["bundled_sha256"]
                and item["bytes"] == record["bundled_bytes"] and item.get("original_sha256", item["sha256"]) == record["original_sha256"],
                f"Replication rating input link mismatch: {record['annotation_path']}")
        problem = ext_problem(record["annotation_path"])
        require(record["annotation_path"].startswith(f"closure_ext/{record['group']}/") and ext_problem(record["group"]) == problem,
                f"Replication group mismatch: {record['annotation_path']}")
        require(item["rubric_sha256"] == sha((out / "prompts" / f"closure_system_p{problem}.txt").read_bytes()), f"Rubric digest mismatch: {record['annotation_path']}")
        grades = response_grades((out / record["annotation_path"]).parent, item)
        require(grades == item["grades"], f"Active response grades differ from annotation: {record['annotation_path']}")
        require(item["S"] == (None if grades is None else closure_score(grades)), f"Closure score mismatch: {record['annotation_path']}")
        counts[record["group"]] = counts.get(record["group"], 0) + 1
    for path in sorted((out / "closure_ext").rglob("summary.json")) if (out / "closure_ext").is_dir() else []:
        for item in read_json(path).get("items", []):
            require(item.get("path") in bundled and item.get("path_base") == "bundle root", f"Summary item is not linked to a bundled text: {path.relative_to(out)} {item.get('id')}")
    problems = sorted({ext_problem(r["group"]) for r in records})
    for problem in problems:
        require((out / f"closure_rubric_p{problem}.txt").read_bytes() == (out / "prompts" / f"closure_system_p{problem}.txt").read_bytes(),
                f"Rubric copy differs from the bundled prompt: P{problem}")
        for row in read_json(out / f"closure_distinct_p{problem}.json"):
            require(row.get("path") in bundled and row.get("path_base") == "bundle root" and sha((out / row["path"]).read_bytes()) == row["sha256"],
                    f"Distinct-text manifest entry does not resolve to a bundled input: P{problem} {row['id']}")
        for row in read_json(out / f"closure_p{problem}_checkpoints.json"):
            require(row.get("path") in bundled and row.get("path_base") == "bundle root", f"Checkpoint manifest entry does not resolve to a bundled input: P{problem} {row['id']}")
    return counts, problems, len({r["original_sha256"] for r in records})


def verify_adjudication(out, inputs):
    """Recompute the label layers from the released ratings in a scratch copy and require the shipped adjudication to agree."""
    for name in ADJUDICATED_FILES:
        require((out / "closure_adjudicated" / name).is_file(), f"Missing adjudication file: closure_adjudicated/{name}")
    for name in MATRIX_FILES:
        require((out / "closure_matrix" / name).is_file(), f"Missing closure-matrix file: closure_matrix/{name}")
    labels = read_json(out / "closure_adjudicated/labels.json")
    reliability = read_json(out / "closure_adjudicated/reliability.json")
    by_id = {r["id"]: r for r in inputs}
    to_bundled = {r["original_sha256"]: r["bundled_sha256"] for r in inputs}
    seen, unknown = set(), 0
    for label in labels:
        key = (label["problem"], label["sha256"])
        require(key not in seen, f"Two label records for one text: P{key[0]} {key[1][:12]}")
        seen.add(key)
        require(label["record_ids"], f"Label without annotation records: {key[1][:12]}")
        for record_id in label["record_ids"]:
            require(record_id in by_id, f"Label cites an annotation that is not bundled: {record_id}")
            require(by_id[record_id]["original_sha256"] == label["sha256"], f"Label digest differs from annotation {record_id}")
            require(CLOSURE_PROBLEM[by_id[record_id]["group"]] == label["problem"], f"Label problem differs from annotation group: {record_id}")
        require(set(label["S"]) == set(LAYERS) and (label["S"]["valid"] is None) == (label["status"] == "unknown"), f"Malformed label layers: {key[1][:12]}")
        unknown += label["status"] == "unknown"
    # The adjudication covers P2/P3/P6 only: its texts are exactly the primary checkpoint_inputs/ manifest, never checkpoint_inputs_ext/.
    require({key[1] for key in seen} == set(to_bundled), "Labelled texts differ from the primary checkpoint_inputs/ manifest")
    require(reliability["overall"]["distinct_texts"] == len(labels) and reliability["overall"]["status"].get("unknown", 0) == unknown,
            "reliability.json does not describe labels.json")
    with tempfile.TemporaryDirectory(prefix="supplementary-adjudicate-") as scratch:
        copy = Path(scratch) / "bundle"
        shutil.copytree(out, copy)
        run = subprocess.run([sys.executable, str(copy / "scripts/closure_adjudicate.py"), "--root", str(copy)], capture_output=True, text=True)
        require(run.returncode == 0, "closure_adjudicate.py failed on the released ratings:\n" + run.stdout + run.stderr)
        recomputed = read_json(copy / "closure_adjudicated/labels.json")
        recomputed_reliability = read_json(copy / "closure_adjudicated/reliability.json")
    layers = lambda rows, digest: sorted((l["problem"], digest(l["sha256"]), json.dumps(l["S"], sort_keys=True)) for l in rows)
    shipped, fresh = layers(labels, lambda h: to_bundled.get(h, h)), layers(recomputed, lambda h: h)
    changed = sorted({f"P{p} {h[:12]}" for p, h, _ in set(shipped) ^ set(fresh)})
    require(shipped == fresh, "Shipped label layers differ from a recomputation over the released ratings (rerun closure_adjudicate.py): " + ", ".join(changed))
    require(recomputed_reliability == reliability, "Shipped reliability.json differs from a recomputation over the released ratings")
    regularities = read_json(out / "closure_matrix/regularities.json")
    require(read_json(out / "closure_matrix/sensitivity.json") == regularities["sensitivity_by_layer"], "sensitivity.json differs from regularities.json")
    require(read_json(out / "closure_matrix/matrix.json")["layer"] == regularities["layer"], "matrix.json and regularities.json use different layers")
    return len(labels), unknown


def verify_pilot(out):
    """Pilot runs: output digests, and shipped summaries that agree with the released grades and gate reviews."""
    runs, pending = 0, []
    for group in PILOT_GROUPS:
        base = out / group
        if not base.is_dir():
            continue
        require((base / "PREREG.md").is_file(), f"Missing protocol text: {group}/PREREG.md")
        for meta_path in sorted(base.glob("p*-*-r*/meta.json")):
            meta = read_json(meta_path)
            data = (meta_path.parent / "output.md").read_bytes()
            require(sha(data) == meta["output_sha256"] and len(data) == meta["output_bytes"], f"Pilot output digest mismatch: {group}/{meta_path.parent.name}")
            runs += 1
        pending += [f"{group}/{name}" for name in ("summary.json", "author_read.md", "gate_glm53/summary.json") if not (base / name).is_file()]
        if not (base / "summary.json").is_file():
            continue
        gates = {meta["candidate_file"]: meta for meta in map(read_json, base.glob("gate_glm53/*/meta.json"))}
        for row in read_json(base / "summary.json")["rows"]:
            meta = read_json(base / row["run"] / "meta.json")
            if row.get("no_output"):
                require(meta["output_bytes"] == 0, f"Summary marks a delivered run as empty: {group}/{row['run']}")
                continue
            record_id = f"pilot-{meta['output_sha256'][:12]}"
            for annotator, key in (("grades_glm", "S_glm"), ("grades_kimi", "S_kimi")):
                path = base / annotator / f"p{row['problem']}" / record_id / "annotation.json"
                require((read_json(path)["S"] if path.is_file() else None) == row[key], f"Summary {key} differs from the released grade: {group}/{row['run']}")
            gate = gates.get(f"{group}/{row['run']}/output.md")
            require((gate or {}).get("passes_gate") == row["gate_pass"], f"Summary gate outcome differs from the released review: {group}/{row['run']}")
    # pilot_critique_ext/gate_glm53/summary.json was never produced (pilot_critique_ext/ADDENDUM_2026-09-29.md): its per-run gate
    # reviews are released and checked above against the group's summary.json. Nothing else may be missing.
    require(set(pending) <= set(NEVER_PRODUCED), "Pilot files missing: " + ", ".join(sorted(set(pending) - set(NEVER_PRODUCED))))
    return runs, pending


NEVER_PRODUCED = ("pilot_critique_ext/gate_glm53/summary.json",)


def third_party_inventory(out):
    """Full texts and receipts from the public campaign (THIRD_PARTY_SOURCE) in this bundle, found from the bundle's own records:
    a checkpoint text is the campaign's if its lineage in closure_distinct_p<N>.json is one of the campaign's runs (deedy-*); a planted
    base is the campaign's if its original text is one of those checkpoint texts (the three edited copies of such a base keep the rest
    of its text); the grade receipts are listed in replication_ext/public_grades/provenance.json."""
    lineage = {}
    for n in range(1, 7):
        if (out / f"closure_distinct_p{n}.json").is_file():
            for row in read_json(out / f"closure_distinct_p{n}.json"):
                lineage[row["path"]] = row["lineage"]
    texts = sorted(str(p.relative_to(out)) for d in ("checkpoint_inputs", "checkpoint_inputs_ext") for p in (out / d).glob("*.md"))
    require(set(texts) <= set(lineage), "Checkpoint text without a lineage record: " + ", ".join(sorted(set(texts) - set(lineage))[:3]))
    campaign = [t for t in texts if lineage[t].startswith("deedy-")]
    campaign_digests = {sha((out / t).read_bytes()) for t in campaign}
    planted = sorted(str(p.relative_to(out)) for p in (out / "planted_defects/texts").glob("*/*.md"))
    bases = sorted({Path(t).parent.name for t in planted if sha((out / Path(t).parent / "original.md").read_bytes()) in campaign_digests})
    planted_campaign = [t for t in planted if Path(t).parent.name in bases]
    receipts = read_json(out / "replication_ext/public_grades/provenance.json")["files"]
    return {"schema_version": 1, "source": THIRD_PARTY_SOURCE,
            "note": "Files of this bundle that reproduce text from the public campaign cited in the paper (see NOTICE.md). Excerpts quoted "
                    "inside other files (model responses, plantings.json search/replace/hunk fields, diffs) are not listed.",
            "counts": {"checkpoint_texts": len(campaign), "checkpoint_texts_total": len(texts), "planted_bases": len(bases),
                       "planted_texts": len(planted_campaign), "planted_texts_total": len(planted), "grade_receipts": len(receipts)},
            "checkpoint_texts": [{"path": t, "lineage": lineage[t]} for t in campaign],
            "planted_texts": planted_campaign,
            "grade_receipts": [f"replication_ext/public_grades/{name}" for name in sorted(receipts)]}


def verify_documents(out):
    """Camera-ready documents: README/NOTICE/CHANGES present, NOTICE states the third-party counts this bundle actually holds,
    the dated addenda and the judgment records they correct are present, and THIRD_PARTY.json equals a recomputation."""
    for name in DOCS + ADDENDA + JUDGMENT_RECORDS + ("THIRD_PARTY.json",):
        require((out / name).is_file(), f"Missing file: {name}")
    inventory = third_party_inventory(out)
    require(read_json(out / "THIRD_PARTY.json") == json.loads(json.dumps(inventory)), "THIRD_PARTY.json differs from a recomputation")
    counts, notice = inventory["counts"], (out / "NOTICE.md").read_text()
    for phrase in (f"{counts['checkpoint_texts']} of the {counts['checkpoint_texts_total']} checkpoint texts",
                   f"{counts['planted_texts']} of the {counts['planted_texts_total']} planted texts",
                   f"{counts['planted_bases']} public base proofs", f"{counts['grade_receipts']} files", THIRD_PARTY_SOURCE["commit"]):
        require(phrase in " ".join(notice.split()), f"NOTICE.md does not state: {phrase}")
    return counts


def verify_post_submission(out):
    """Post-submission runs (post_submission/): every record re-hashes to records.json, the directory holds nothing else, every
    request names one of the 32 planted texts by its bundled digest and carries the system prompt its digest names, and
    summary.json equals a recomputation by post_submission/summarize.py."""
    base = out / POST_SUBMISSION
    if not base.is_dir():
        return None
    records = read_json(base / "records.json")
    verify_manifest(base, records["files"])
    listed = {row["path"] for row in records["files"]}
    extra = {str(p.relative_to(base)) for p in base.rglob("*") if p.is_file()} - listed - {"records.json", "summary.json", "summarize.py", "README.md"}
    require(not extra, "Unlisted files in post_submission/: " + ", ".join(sorted(extra)[:5]))
    planted = {}
    for path in (out / "planted_defects/texts").glob("*/*.md"):
        planted[path.parent.name if path.stem == "original" else f"{path.parent.name}-{path.stem}"] = sha(path.read_bytes())
    require(sorted(planted) == records["text_ids"], "post_submission/records.json does not name the 32 planted texts")
    calls = 0
    for arm, info in records["arms"].items():
        for model in info["models"]:
            for text_id in records["text_ids"]:
                request = read_json(base / arm / model / text_id / "request.json")
                require(request["text_id"] == text_id and request["text_sha256"] == planted[text_id], f"Post-submission text mismatch: {arm}/{model}/{text_id}")
                require(sha(request["system"].encode()) == request["system_sha256"], f"Post-submission prompt digest mismatch: {arm}/{model}/{text_id}")
                require((base / arm / model / text_id / "parsed.json").is_file(), f"Post-submission parse missing: {arm}/{model}/{text_id}")
                calls += 1
    check = subprocess.run([sys.executable, str(base / "summarize.py"), "--root", str(out), "--check"], capture_output=True, text=True)
    require(check.returncode == 0, "post_submission/summarize.py --check failed:\n" + check.stdout + check.stderr)
    return {"runs": len(records["arms"]), "calls": calls, "files": len(listed)}


def verify_public_grades(out):
    """Released copies of the public campaign's grade receipts (read by replication_ext.py analyze): each file listed in
    replication_ext/public_grades/provenance.json is present with the recorded digest, i.e. unchanged by anonymization."""
    base = out / "replication_ext/public_grades"
    if not (base / "provenance.json").is_file():
        return 0
    files = read_json(base / "provenance.json")["files"]
    for name, record in files.items():
        require("/" not in name and (base / name).is_file(), f"Public grade receipt missing: {name}")
        data = (base / name).read_bytes()
        require(sha(data) == record["sha256"] and len(data) == record["bytes"], f"Public grade receipt differs from its recorded digest: {name}")
    return len(files)


def verify_witness(out):
    """Witness-discovery files, if the experiment ran before the build: every re-linked case hashes to the bundled text it names;
    the per-directory counts are reported (a partial experiment is allowed); and where the analysis and the analyzer script are both
    present, the analysis is regenerated offline from the retained responses in a scratch copy (`witness_discovery.py analyze --root`)
    and must equal the shipped results.json apart from its generation time, and both shipped tables byte for byte."""
    base = out / "witness_discovery"
    if not base.is_dir():
        return None
    summary = {"cases": 0, "cases_linked": 0, "regenerated": False}
    if (base / "cases.json").is_file():
        for case in read_json(base / "cases.json").get("cases", []):
            summary["cases"] += 1
            if case.get("path_base") != "bundle root":
                continue
            relative = Path(case["path"])
            require(not relative.is_absolute() and ".." not in relative.parts and (out / relative).is_file(), f"Witness case text is not bundled: {case.get('id')}")
            data = (out / relative).read_bytes()
            require(sha(data) == case["sha256"] and len(data) == case["bytes"], f"Witness case text differs from the bundled input: {case.get('id')}")
            summary["cases_linked"] += 1
    for name in ("propose", "check", "baseline"):
        summary[name] = len(list((base / name).rglob("parsed.json"))) if (base / name).is_dir() else 0
    summary["analysis"] = [name for name in ("results.json", "RESULTS.md", "table_witness.tex", "table_witness_summary.tex", "recovery.json", "certificates.json")
                           if (base / name).is_file()]
    script = out / "scripts" / WITNESS_SCRIPT
    if (base / "results.json").is_file() and script.is_file():
        shipped = read_json(base / "results.json")
        with tempfile.TemporaryDirectory(prefix="supplementary-witness-") as scratch:
            copy = Path(scratch) / "bundle"
            copy.mkdir()
            shutil.copytree(base, copy / "witness_discovery")
            shutil.copytree(out / "scripts", copy / "scripts")
            command = [sys.executable, str(copy / "scripts" / WITNESS_SCRIPT), "analyze", "--root", str(copy)] + (["--freeze"] if shipped.get("frozen") else [])
            run = subprocess.run(command, capture_output=True, text=True)
            require(run.returncode == 0, "witness_discovery.py analyze --root failed on the released responses:\n" + run.stdout[-3000:] + run.stderr[-3000:])
            fresh = read_json(copy / "witness_discovery/results.json")
            untimed = lambda record: {key: value for key, value in record.items() if key != "analyzed_utc"}
            changed = sorted(key for key in set(untimed(fresh)) | set(untimed(shipped)) if untimed(fresh).get(key) != untimed(shipped).get(key))
            require(not changed, "Shipped witness_discovery/results.json differs from an offline regeneration (rerun scripts/witness_discovery.py analyze): " + ", ".join(changed))
            for name in ("table_witness.tex", "table_witness_summary.tex"):
                if (base / name).is_file():
                    require((copy / "witness_discovery" / name).read_bytes() == (base / name).read_bytes(), f"Shipped witness_discovery/{name} differs from an offline regeneration")
        summary["regenerated"] = True
    return summary


def verify(out):
    verify_manifest(out, read_json(out / "MANIFEST.json")["files"], exhaustive=True)
    manifest = read_json(out / "checkpoint_inputs/manifest.json")
    inputs = manifest["records"]
    require(len(inputs) == manifest["count"] and len({r['id'] for r in inputs}) == len(inputs), "Checkpoint record count/uniqueness mismatch")
    actual_annotations = {str(p.relative_to(out)) for group in CLOSURE for p in (out / group).glob("*/annotation.json")}
    require(actual_annotations == {r["annotation_path"] for r in inputs}, "Checkpoint coverage does not match annotations")
    for group, (manifest_name, _, _) in CLOSURE.items():
        if manifest_name:
            listed = {item["id"] for item in read_json(out / group / "checkpoints_manifest.json")}
            require(listed <= {r["id"] for r in inputs}, f"Checkpoint manifest lists unknown ids: {group}")
    for record in inputs:
        data = (out / record["input_path"]).read_bytes()
        require(sha(data) == record["bundled_sha256"] and len(data) == record["bundled_bytes"], f"Input mismatch: {record['id']}")
        item = read_json(out / record["annotation_path"])
        require(item["path"] == record["input_path"] and item["sha256"] == record["bundled_sha256"], f"Annotation input link mismatch: {record['id']}")
        require(item["original_sha256"] == record["original_sha256"], f"Original hash mismatch: {record['id']}")
        if not record["anonymized"]:
            require(sha(data) == record["original_sha256"], f"Original input digest mismatch: {record['id']}")
        require(item["rubric_sha256"] == sha((out / "prompts" / CLOSURE[record["group"]][1]).read_bytes()), f"Closure prompt digest mismatch: {record['id']}")
        if record.get("review_path"):
            require((out / record["review_path"]).is_file(), f"Missing checkpoint review: {record['id']}")
        grades = item["grades"]
        require(grades is not None and item["S"] == closure_score(grades), f"Closure score mismatch: {record['id']}")
        response = response_grades((out / record["annotation_path"]).parent, item)
        require(response is not None, f"No parsed active response: {record['id']}")
        require(response == grades, f"Active response grades differ from annotation: {record['id']}")
    table = read_json(out / "run_artifacts/manifest.json")["rows"]
    require(len(table) == 9, "Expected all nine accepted-proof table rows")
    for row in table:
        for record in row["artifacts"].values():
            actual = sha((out / record["path"]).read_bytes())
            require(actual == record["sha256"] and actual.startswith(record.get("paper_prefix", "")), f"Table digest mismatch: {row['lineage']}")
    for group in REVIEWER_GROUPS + GATE_DIRS:
        for path in sorted((out / group).glob("*/meta.json")):
            meta = read_json(path)
            require(sha((out / meta["candidate_file"]).read_bytes()) == meta["candidate_sha256"], f"Reviewer candidate mismatch: {path.parent.name}")
            number = meta["task_id"].rsplit("p", 1)[1]
            require(sha((out / f"problems/problem-{number}.md").read_bytes()) == meta["statement_sha256"], f"Reviewer statement mismatch: {path.parent.name}")
            require(sha(read_json(path.parent / "request_redacted.json")["system"].encode()) == meta["rubric_sha256"], "Reviewer rubric mismatch")
    for model in ("kimi-k3", "glm-5.2"):
        path = out / "p3_repairs" / model / "manifest.json"
        repair = read_json(path)
        candidate_path = f"p3_repairs/{model}/sources/candidate.md"
        require(repair["candidate_source_path"] == candidate_path, f"Repair candidate link mismatch: {model}")
        require(sha((out / candidate_path).read_bytes()) == repair["candidate_sha256"], f"Repair candidate hash mismatch: {model}")
        require(sha((path.parent / "sources/statement.md").read_bytes()) == repair["statement_sha256"], f"Repair statement hash mismatch: {model}")
    ratings = verify_ratings(out, inputs)
    replication, ext_problems, ext_texts = verify_replication(out)
    n_labels, unknown = verify_adjudication(out, inputs)
    runs, pending = verify_pilot(out)
    grade_files = verify_public_grades(out)
    witness = verify_witness(out)
    third_party = verify_documents(out)
    post = verify_post_submission(out)
    for path in files(out):
        # Bytes, not text: the bundle carries one binary document (paper.pdf); its uncompressed metadata is scanned too.
        text = path.read_bytes().decode("utf-8", errors="replace")
        require(not IDENTIFYING.search(text), f"Local path remains in {path.relative_to(out)}")
        require(not SECRET.search(text), f"Possible credential remains in {path.relative_to(out)}")
    # Recompute the closure matrix offline from the released labels and compare with the shipped regularities.
    check = subprocess.run([sys.executable, str(out / "scripts/closure_matrix.py"), "--root", str(out), "--check"],
                           capture_output=True, text=True)
    require(check.returncode == 0, "closure_matrix.py --check failed:\n" + check.stdout + check.stderr)
    if pending:
        print("note: never produced, so not in this release: " + ", ".join(pending) + " (its per-run gate reviews are released and "
              "checked; pilot_critique_ext/ADDENDUM_2026-09-29.md)")
    print(f"Verified {len(inputs)} checkpoint records, {len({r['original_sha256'] for r in inputs})} distinct inputs, "
          f"{n_labels} adjudicated labels ({unknown} unknown) equal to a recomputation from {sum(ratings.values())} released ratings "
          f"({', '.join(f'{g} {n}' for g, n in ratings.items())}), {runs} pilot runs, nine table rows, reviewer and gate inputs, prompts, "
          f"complete manifest, and closure-matrix recomputation; replication: "
          + (f"{sum(replication.values())} closure_ext ratings of {ext_texts} distinct P{'/P'.join(ext_problems)} texts, each hashing to its "
             f"bundled text and rubric ({', '.join(f'{g} {n}' for g, n in replication.items())})" if replication else "no closure_ext ratings")
          + f"; public grade receipts: {grade_files} files match replication_ext/public_grades/provenance.json"
          + ("; witness discovery: not included" if witness is None else
             f"; witness discovery: {witness['cases']} cases ({witness['cases_linked']} linked to bundled texts), {witness['propose']} proposals, "
             f"{witness['check']} checks, {witness['baseline']} baseline grades, analysis files {witness['analysis'] or 'none'}"
             + ("; results.json and both tables regenerated offline and equal to the shipped files" if witness["regenerated"] else ""))
          + ("; post-submission runs: not included" if post is None else
             f"; post-submission runs: {post['runs']} runs, {post['calls']} calls on the 32 planted texts, {post['files']} records matching "
             f"records.json, summary.json equal to a recomputation")
          + f"; NOTICE.md states the third-party counts of THIRD_PARTY.json ({third_party['checkpoint_texts']} of "
            f"{third_party['checkpoint_texts_total']} checkpoint texts, {third_party['planted_texts']} of {third_party['planted_texts_total']} "
            f"planted texts, {third_party['grade_receipts']} grade files); README.md, NOTICE.md, CHANGES.md, the dated addenda and the "
            f"judgment records are present")


# The bundle README, NOTICE and CHANGES are supplement_docs/{README,NOTICE,CHANGES}.md (camera-ready); see DOCS.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("capture", "build", "verify"))
    parser.add_argument("--sources", type=Path, default=ROOT / "artifacts/supplementary_sources")
    parser.add_argument("--out", type=Path, default=ROOT / "supplementary")
    parser.add_argument("--imo26", type=Path)
    parser.add_argument("--neurogolf", type=Path)
    args = parser.parse_args()
    if args.command == "capture":
        if not args.imo26 or not args.neurogolf:
            parser.error("capture requires --imo26 and --neurogolf")
        capture(args)
    elif args.command == "build":
        build(args)
    else:
        verify(args.out)


if __name__ == "__main__":
    main()
