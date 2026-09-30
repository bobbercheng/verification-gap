#!/usr/bin/env python3
"""Replication of the evaluator-variation measurements on IMO 2026 Problems 1, 4 and 5.

Three sub-commands, stdlib only, no model calls (ratings are produced by scripts/closure_annotate.py):

  manifests       Reconstruct every version of the public campaign's tracking file (current.md) from the
                  per-turn tool-call logs (main session + repair rounds scratch/logs-roundN.jsonl; killed /
                  degenerate / cut-off scratch sessions are excluded, as for P2/P3/P6), add each model's final
                  file and our retained candidate_vN.md files, and write
                    artifacts/closure_p{N}_checkpoints.json   (one record per checkpoint, recorded order)
                    artifacts/closure_distinct_p{N}.json      (one record per distinct sha256)
                  --check-p6 re-extracts P6 and compares bytes and ids with the shipped P6 corpus.
                  Needs a checkout of the public campaign repository (https://github.com/deedy/imo-2026; --deedy DIR)
                  and our run directories; it is the only sub-command that reads anything outside the repository.
  capture-grades  Copy the public campaign's grade receipts from that checkout into artifacts/replication_ext/public_grades/:
                  grades/problem-0N.json (N = 1, 3, 4, 5, 6: the replication problems and the paper's P3/P6 reference rows),
                  the README's first-pass table as first_pass_grades.json (model -> problem -> grade) and provenance.json
                  (source repository, commit, capture time, sha256 of every copied file).
  analyze         Read the ratings under closure_ext/p{N}/, the checkpoint and distinct-text manifests, freeze.json and the
                  released public grades ONLY (never an external checkout) and write replication_ext/results.json,
                  table_replication.tex and, when <root>/gen exists, gen/replication_macros.tex.
                  --root DIR is the repository root (uses DIR/artifacts) or the flat supplementary bundle (files at the top
                  level); the default is the repository or bundle that contains this script.

Rating layout (see artifacts/replication_ext/PROTOCOL.md):
  closure_ext/p{N}/claude_ckpt/            Claude Opus 5, one rating per checkpoint (per-checkpoint pass)
  closure_ext/p{N}/claude_text/rep{1,2,3}/ Claude Opus 5, one rating per distinct text, three passes
  closure_ext/p{N}/gpt_text/               GPT-5.6-Sol, one rating per distinct text
  closure_ext/p{N}/glm_text/               GLM-5.3, one rating per distinct text (whatever finished)
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, itertools, json, os, re, statistics, subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"          # reset by set_root(): <root>/artifacts (repository) or <root> (flat bundle)
GEN = ROOT / "gen"                # analyze writes replication_macros.tex here only when the directory exists (never in the bundle)
PUBLIC_REPO = "https://github.com/deedy/imo-2026"
GRADE_PROBLEMS = ("1", "3", "4", "5", "6")   # grade receipts released under replication_ext/public_grades/
SCRATCH = Path("[local-path]")
DEEDY = SCRATCH / "imo-2026-deedy"
RUNTIME = Path.home() / "Kaggle/competitions/neurogolf-2026/portfolio_transfer/runtime"
OURS = [  # (runtime dir, lineage, model, id prefix) in the order used by the P6 manifest
    ("imo-2026-glm52-blind", "ours-glm52", "glm-5.2", "glm52"),
    ("imo-2026-codex-gpt56sol-ultra", "ours-gpt56sol-ultra", "gpt-5.6-sol", "gpt56"),
    ("imo-2026", "ours-nemotron", "nemotron-3-ultra", "nemotron"),
]
PUBLIC_MODELS = ["claude-fable-5", "deepseek-v4-pro", "gpt-5.6-sol", "gpt-5.6-sol-max", "gpt-5.6-sol-pro",
                 "gpt-5.6-sol-xhigh", "grok-4.5", "kimi-k3", "muse-spark-1.1"]
README_NAMES = {"Claude Fable 5": "claude-fable-5", "GPT-5.6 Sol (xhigh effort)": "gpt-5.6-sol-xhigh",
                "Kimi K3": "kimi-k3", "GPT-5.6 Sol Pro (xhigh effort)": "gpt-5.6-sol-pro",
                "GPT-5.6 Sol (max effort)": "gpt-5.6-sol-max", "GPT-5.6 Sol (default effort)": "gpt-5.6-sol",
                "Meta Muse Spark 1.1": "muse-spark-1.1", "DeepSeek V4 Pro": "deepseek-v4-pro",
                "xAI Grok 4.5": "grok-4.5"}
PROBLEMS = ("1", "4", "5")
EVALUATORS = ["claude_ckpt", "claude_rep1", "claude_rep2", "claude_rep3", "claude_maj3", "gpt", "glm"]
CONCS = ("improved", "regressed", "crossing")


def sha256(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def load_json(p: Path):
    try: return json.loads(p.read_text())
    except (OSError, ValueError): return None
def utc_mtime(p: Path) -> str: return dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def utc_now() -> str: return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def set_root(root: Path) -> None:
    """analyze --root: a repository root (artifacts/replication_ext/ below it) or the flat supplementary bundle (replication_ext/ at the top)."""
    global ART, GEN
    root = root.resolve()
    ART = root / "artifacts" if (root / "artifacts" / "replication_ext").is_dir() else root
    GEN = root / "gen"


def text_path(p: str) -> Path:
    """Manifest paths are absolute in the repository and relative to the bundle root in the flat bundle."""
    q = Path(p)
    return q if q.is_absolute() else ART / q


def source_digest(p: str) -> str:
    """The sha256 of a manifest's source text. Read from the file when it is present; otherwise taken from the digest
    the stored ratings recorded for it, so a source directory that no longer exists cannot change any result."""
    q = text_path(p)
    if q.exists():
        return sha256(q.read_bytes())
    import text_store as TS  # noqa: E402
    h = TS.digest_for(p)
    if h:
        return h
    raise SystemExit(f"no digest recorded for absent source text {p}")


def checkpoint_manifest(name: str, group: str) -> list[dict]:
    """artifacts/<name> in the repository; <group>/checkpoints_manifest.json (same records, bundle-relative paths) in the bundle."""
    return load_json(ART / name) or load_json(ART / group / "checkpoints_manifest.json") or []


def public_grades_dir() -> Path: return ART / "replication_ext" / "public_grades"


def need_deedy(what: str) -> None:
    if not (DEEDY / "README.md").is_file() or not (DEEDY / "grades").is_dir():
        raise SystemExit(f"{what} needs a checkout of the public campaign repository {PUBLIC_REPO} at {DEEDY} (pass --deedy DIR). "
                         "The analyze sub-command does not need it: it reads only the released files (replication_ext/public_grades/).")


# =============================================================================== manifests
def public_sessions(model: str, prob: str) -> list[tuple[str, Path]]:
    """(session name, log path): the main session plus repair rounds; other scratch sessions are excluded."""
    d = DEEDY / "results" / model / f"problem-0{prob}"
    out = []
    if (d / "logs.jsonl").exists(): out.append(("main", d / "logs.jsonl"))
    rounds = []
    for f in (d / "scratch").glob("logs-round*.jsonl"):
        m = re.fullmatch(r"logs-round(\d+)\.jsonl", f.name)
        if m: rounds.append((int(m.group(1)), f))
    out += [(f"round{k}", f) for k, f in sorted(rounds)]
    return out


def excluded_sessions(model: str, prob: str) -> list[str]:
    d = DEEDY / "results" / model / f"problem-0{prob}"
    keep = {p for _, p in public_sessions(model, prob)}
    return [str(p.relative_to(DEEDY)) for p in sorted(d.glob("**/logs*.jsonl")) if p not in keep]


def snapshots(log: Path) -> list[tuple[int, str, bytes]]:
    """Every write_file whose target basename is current.md: (turn, target path, content bytes)."""
    out = []
    with open(log, encoding="utf-8") as f:
        for line in f:
            try: e = json.loads(line)
            except json.JSONDecodeError: continue
            if e.get("tool_name") != "write_file": continue
            inp = e.get("input_data") or {}
            path = str(inp.get("path") or "")
            if os.path.basename(path.rstrip("/")) != "current.md": continue
            out.append((int(e.get("turn") or 0), path, str(inp.get("content") or "").encode("utf-8")))
    return out


def build_public(prob: str, ckpt_dir: Path, write: bool = True) -> tuple[list[dict], list[dict]]:
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    records, notes = [], []
    for model in PUBLIC_MODELS:
        for session, log in public_sessions(model, prob):
            for turn, target, content in snapshots(log):
                h = sha256(content)
                name = f"{model}-{session}-t{turn:03d}-{h[:12]}.md"
                p = ckpt_dir / name
                if write:
                    if p.exists() and p.read_bytes() != content: raise SystemExit(f"collision {p}")
                    p.write_bytes(content)
                records.append({"id": f"p{prob}-{model}-{session}-t{turn:03d}", "lineage": f"deedy-{model}", "model": model,
                                "context": f"{model}-{session}", "turn": turn, "path": str(p), "source_log": str(log.relative_to(DEEDY)),
                                "source_target": target})
        final = DEEDY / "results" / model / f"problem-0{prob}" / "current.md"
        if final.exists():
            records.append({"id": f"p{prob}-deedy-{model}-final", "lineage": f"deedy-{model}", "model": model, "context": 99, "turn": None, "path": str(final)})
        else:
            notes.append({"model": model, "note": "no final current.md"})
        for ex in excluded_sessions(model, prob):
            n = len(snapshots(DEEDY / ex))
            notes.append({"model": model, "excluded_log": ex, "current_md_writes": n})
    return records, notes


def build_ours(prob: str) -> tuple[list[dict], list[dict]]:
    records, notes = [], []
    pat = re.compile(rf"imo-2026-p{prob}-([0-9a-f]{{32}})$")
    for rt, lineage, model, prefix in OURS:
        runs = RUNTIME / rt / "runs"
        found = []
        with os.scandir(runs) as it:
            for ent in it:
                m = pat.match(ent.name)
                if not m or not ent.is_dir(): continue
                cands = []
                for f in os.scandir(ent.path):
                    mm = re.fullmatch(r"candidate_v(\d+)\.md", f.name)
                    if mm: cands.append((int(mm.group(1)), Path(f.path)))
                    elif f.name.startswith("candidate_v") and f.name.endswith(".md"):
                        notes.append({"lineage": lineage, "run": ent.name, "excluded_file": f.name})
                if cands: found.append((min(p.stat().st_mtime for _, p in cands), m.group(1)[-8:], sorted(cands)))
        for _, ctx, cands in sorted(found):
            for v, p in cands:
                records.append({"id": f"p{prob}-{prefix}-{ctx}-v{v}", "lineage": lineage, "model": model, "context": ctx, "turn": v,
                                "path": str(p), "recorded_mtime_utc": utc_mtime(p)})
    return records, notes


def distinct_manifest(prob: str, records: list[dict]) -> list[dict]:
    groups: dict[str, dict] = {}
    for r in records:
        h = source_digest(r["path"])
        g = groups.get(h)
        if g is None:
            groups[h] = {"id": f"p{prob}-h-{h[:12]}", "problem": prob, "sha256": h, "path": r["path"], "lineage": r["lineage"],
                         "model": r["model"], "context": r["context"], "turn": r["turn"], "record_ids": [r["id"]]}
        else: g["record_ids"].append(r["id"])
    return list(groups.values())


def cmd_manifests(args):
    global DEEDY
    if args.deedy: DEEDY = Path(args.deedy)
    need_deedy("manifests")
    if not (DEEDY / "results").is_dir(): raise SystemExit(f"manifests: {DEEDY} has no results/ directory (per-run logs of the public campaign)")
    if args.check_p6:
        tmp = SCRATCH / "deedy_ckpts_p6_recheck"
        recs, notes = build_public("6", tmp)
        old = {p.name: p.read_bytes() for p in (SCRATCH / "deedy_ckpts_p6").glob("*.md")}
        new = {p.name: p.read_bytes() for p in tmp.glob("*.md")}
        same = old == new
        shipped = [r["id"] for r in load_json(ART / "closure_p6_checkpoints.json") if r["lineage"].startswith("deedy")]
        mine = [r["id"] for r in recs]
        print(f"P6 re-extraction: {len(new)} snapshot files, byte-identical to shipped deedy_ckpts_p6: {same}; "
              f"public ids identical to closure_p6_checkpoints.json: {sorted(shipped) == sorted(mine)} ({len(mine)} records)")
        print("  excluded sessions:", [n for n in notes if "excluded_log" in n])
        if not same:
            print("  only shipped:", sorted(set(old) - set(new))); print("  only mine:", sorted(set(new) - set(old)))
        return
    summary = {}
    for prob in args.problems.split(","):
        pub, pnotes = build_public(prob, SCRATCH / f"deedy_ckpts_p{prob}")
        ours, onotes = build_ours(prob)
        records = pub + ours
        for r in records: r.pop("source_log", None); r.pop("source_target", None)
        (ART / f"closure_p{prob}_checkpoints.json").write_text(json.dumps(records, indent=1, ensure_ascii=False) + "\n")
        dist = distinct_manifest(prob, records)
        (ART / f"closure_distinct_p{prob}.json").write_text(json.dumps(dist, indent=1, ensure_ascii=False) + "\n")
        summary[prob] = {"checkpoints": len(records), "distinct_texts": len(dist), "lineages": len({r["lineage"] for r in records}),
                         "public_snapshots": sum(1 for r in pub if r["context"] != 99), "public_finals": sum(1 for r in pub if r["context"] == 99),
                         "ours": len(ours), "repeated_texts": sum(1 for d in dist if len(d["record_ids"]) > 1),
                         "notes": pnotes + onotes}
        print(f"P{prob}: {summary[prob]['checkpoints']} checkpoints, {summary[prob]['distinct_texts']} distinct texts, {summary[prob]['lineages']} lineages "
              f"({summary[prob]['public_snapshots']} public snapshots + {summary[prob]['public_finals']} finals + {summary[prob]['ours']} ours); "
              f"{summary[prob]['repeated_texts']} texts appear under >1 record")
        for n in summary[prob]["notes"]: print("   note:", n)
    (ART / "replication_ext").mkdir(parents=True, exist_ok=True)
    (ART / "replication_ext" / "manifest_summary.json").write_text(json.dumps(summary, indent=1) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    m = sub.add_parser("manifests", help="build the P1/P4/P5 checkpoint and distinct-text manifests (needs the public checkout and our runs)")
    m.add_argument("--problems", default=",".join(PROBLEMS)); m.add_argument("--check-p6", action="store_true")
    m.add_argument("--deedy", type=Path, default=None, help=f"checkout of {PUBLIC_REPO} (default: the authors' scratch checkout)")
    g = sub.add_parser("capture-grades", help="copy the public grade receipts into replication_ext/public_grades/ with provenance (needs the public checkout)")
    g.add_argument("--deedy", type=Path, default=None, help=f"checkout of {PUBLIC_REPO} (default: the authors' scratch checkout)")
    a = sub.add_parser("analyze", help="compute results.json, table_replication.tex (and gen/replication_macros.tex in the repository) from released files only")
    a.add_argument("--problems", default=",".join(PROBLEMS))
    a.add_argument("--root", type=Path, default=None, help="repository root (uses ROOT/artifacts) or flat supplementary bundle directory; default: the tree containing this script")
    a.add_argument("--freeze-now", action="store_true", help="(re)write replication_ext/freeze.json from the GLM ratings present now; otherwise the existing freeze is used")
    args = ap.parse_args()
    if args.cmd == "manifests": cmd_manifests(args)
    elif args.cmd == "capture-grades": cmd_capture_grades(args)
    elif args.cmd == "analyze": cmd_analyze(args)
    else: ap.print_help()


# =============================================================================== analysis
def annotations(d: Path) -> list[dict]:
    return [a for f in sorted(d.glob("*/annotation.json")) if (a := load_json(f))]


def as_int(v):
    try: return int(v)
    except (TypeError, ValueError): return None


def rating(a: dict) -> dict:
    g = a.get("grades") or {}
    lo, up = as_int(g.get("lower_bound")), as_int(g.get("upper_bound"))
    S = as_int(a.get("S"))
    if S is None and lo is not None and up is not None: S = int(lo == 2) + int(up == 2)
    return {"S": S, "lower": lo, "upper": up, "answer": as_int(g.get("answer")), "reduction": as_int(g.get("reduction")),
            "wrong": g.get("wrong_answer_stated"), "fallback": any(t.get("attempt") == 1 and t.get("parsed") for t in a.get("attempts") or []),
            "rubric_sha256": a.get("rubric_sha256")}


def load_ratings(prob: str, glm_ids: list | None = None) -> tuple[dict, dict]:
    """evaluator -> {key: rating}; key = record id for claude_ckpt, sha256 for the text passes.  Also per-directory stats.
    glm_ids: text ids of the GLM ratings present at the freeze; GLM annotations outside the list are excluded (the GLM chain keeps running)."""
    base = ART / "closure_ext" / f"p{prob}"
    dirs = {"claude_ckpt": base / "claude_ckpt", "claude_rep1": base / "claude_text" / "rep1", "claude_rep2": base / "claude_text" / "rep2",
            "claude_rep3": base / "claude_text" / "rep3", "gpt": base / "gpt_text", "glm": base / "glm_text"}
    ev, stats = {}, {}
    for name, d in dirs.items():
        anns = annotations(d)
        excluded_after_freeze = 0
        if name == "glm" and glm_ids is not None:
            keep = set(glm_ids); excluded_after_freeze = sum(1 for a in anns if a.get("id") not in keep and rating(a)["S"] is not None)
            anns = [a for a in anns if a.get("id") in keep]
        key = "id" if name == "claude_ckpt" else "sha256"
        ev[name] = {a[key]: rating(a) for a in anns if a.get(key)}
        stats[name] = {"dirs": len(list(d.glob("*/"))) if d.is_dir() else 0, "excluded_after_freeze": excluded_after_freeze,
                       "parsed": sum(1 for r in ev[name].values() if r["S"] is not None),
                       "unparsed": sum(1 for r in ev[name].values() if r["S"] is None), "fallbacks": sum(1 for r in ev[name].values() if r["fallback"]),
                       "annotator": next((a.get("annotator") for a in anns), None),
                       "rubric_sha256": sorted({a.get("rubric_sha256") for a in anns if a.get("rubric_sha256")})}
    # majority of the three Claude text passes (abstains when the three values are all different or fewer than two agree)
    maj = {}
    for h in set().union(*(ev[f"claude_rep{r}"] for r in (1, 2, 3))):
        vals = [ev[f"claude_rep{r}"][h]["S"] for r in (1, 2, 3) if h in ev[f"claude_rep{r}"] and ev[f"claude_rep{r}"][h]["S"] is not None]
        c = Counter(vals).most_common(1)
        maj[h] = {"S": c[0][0] if c and c[0][1] >= 2 else None, "lower": None, "upper": None, "fallback": False}
    ev["claude_maj3"] = maj
    return ev, stats


def order_key(it: dict, idx: int):
    """Same ordering as closure_matrix.py: earlier rounds, then the main session, then the final file; ours in manifest order."""
    ctx, turn = it.get("context"), it.get("turn") or 0
    if ctx == 99: return (3, 0, 0, "")
    if isinstance(ctx, int): return (0, ctx, turn, "")
    if (m := re.search(r"round(\d+)$", str(ctx))): return (0, int(m.group(1)), turn, "")
    if str(ctx).endswith("main"): return (1, 0, turn, "")
    return (0, idx, turn, str(ctx))


def conclusions(seq: list):
    """improved / regressed / crossing from an S sequence with possible unknowns (None); as in conclusion_sensitivity.py."""
    first, last = seq[0], seq[-1]
    improved = None if (first is None or last is None) else (last > first)
    dec = any(a is not None and b is not None and b < a for a, b in zip(seq, seq[1:]))
    regressed = True if dec else (None if any(s is None for s in seq) else False)
    crossing = "none"
    for i, s in enumerate(seq):
        if s is None: crossing = None; break
        if s == 2: crossing = i; break
    return {"improved": improved, "regressed": regressed, "crossing": crossing}


def kappa(pairs: list, classes=(0, 1, 2)):
    n = len(pairs)
    if n == 0: return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[c] * cb[c] for c in classes) / n / n
    return {"n": n, "observed": round(po, 3), "kappa": round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0,
            "confusion": {f"{a}{b}": v for (a, b), v in sorted(Counter(pairs).items())}}


def parse_first_pass_readme(readme: Path) -> dict[str, dict[str, int]]:
    """model -> problem -> grade from the 'First pass (before any repair round)' table of the public campaign's README."""
    out: dict[str, dict[str, int]] = defaultdict(dict)
    sec = readme.read_text().split("First pass", 1)[-1]
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7 or cells[0].startswith("Run") or cells[0].startswith("-"):
            if cells and cells[0].startswith("##"): break
            continue
        mid = README_NAMES.get(re.sub(r"\*+", "", cells[0]).strip())
        if not mid: continue
        for k in range(1, 7):
            if cells[k].isdigit(): out[mid][str(k)] = int(cells[k])
    return dict(out)


def _released(name: str) -> Path:
    p = public_grades_dir() / name
    if not p.is_file():
        raise SystemExit(f"missing {p}: the public grade receipts are part of the release; in the repository run "
                         f"`scripts/replication_ext.py capture-grades --deedy <checkout of {PUBLIC_REPO}>` to (re)create them")
    return p


def first_pass_grades() -> dict[str, dict[str, int]]:
    """problem -> model -> public first-pass grade, from the released copy of the README table (public_grades/first_pass_grades.json)."""
    out: dict[str, dict[str, int]] = defaultdict(dict)
    for model, grades in (load_json(_released("first_pass_grades.json")) or {}).items():
        for prob, g in grades.items(): out[prob][model] = g
    return out


def final_grades(prob: str) -> dict[str, int]:
    """model -> public final grade, from the released copy of the campaign's grades/problem-0N.json."""
    d = load_json(_released(f"problem-0{prob}.json")) or {}
    return {e["model"]: e.get("score") for e in d.get("entries", [])}


def cmd_capture_grades(args):
    """Copy the public grade receipts into replication_ext/public_grades/ and record where they came from."""
    global DEEDY
    if args.deedy: DEEDY = Path(args.deedy)
    need_deedy("capture-grades")
    out = public_grades_dir(); out.mkdir(parents=True, exist_ok=True)
    files = {}
    for prob in GRADE_PROBLEMS:
        name = f"problem-0{prob}.json"
        data = (DEEDY / "grades" / name).read_bytes()
        json.loads(data)   # must be the verifier's JSON receipt
        (out / name).write_bytes(data)
        files[name] = {"source_path": f"grades/{name}", "sha256": sha256(data), "bytes": len(data),
                       "content": "public verifier receipt: one entry per run with score (final grade), justification and key_issues"}
    fp = parse_first_pass_readme(DEEDY / "README.md")
    missing = sorted(set(PUBLIC_MODELS) - set(fp))
    if missing: raise SystemExit(f"first-pass table: runs not found in README.md: {missing}")
    fp_bytes = (json.dumps(fp, indent=1, sort_keys=True) + "\n").encode()
    (out / "first_pass_grades.json").write_bytes(fp_bytes)
    files["first_pass_grades.json"] = {"source_path": "README.md", "source_sha256": sha256((DEEDY / "README.md").read_bytes()), "sha256": sha256(fp_bytes), "bytes": len(fp_bytes),
                                       "content": "model -> problem -> grade, parsed from the README table 'First pass (before any repair round)'; run names mapped by README_NAMES in scripts/replication_ext.py"}

    def git(*a):
        try: return subprocess.run(["git", "-C", str(DEEDY), *a], capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError): return None
    prov = {"source_repository": PUBLIC_REPO, "source_commit": git("rev-parse", "HEAD"), "source_commit_date": git("log", "-1", "--format=%cI"),
            "source_dirty": bool(git("status", "--short")), "captured_utc": utc_now(), "captured_by": "scripts/replication_ext.py capture-grades",
            "files": files,
            "note": "Byte-for-byte copies of the public campaign's grade files (final grades = 'score'); first_pass_grades.json is the README's first-pass "
                    "table (grades before any reviewer-feedback repair round). `replication_ext.py analyze` reads only these copies. P2 receipts are not needed "
                    "by the replication and are omitted; closure_matrix/public_grades.json carries the P2/P3/P6 grades used by the paper's matrix."}
    (out / "provenance.json").write_text(json.dumps(prov, indent=1) + "\n")
    print(f"wrote {len(files)} files to {out} (source commit {prov['source_commit']}, captured {prov['captured_utc']})")


def pair_stats(groups: list[list[dict]]) -> dict:
    """Same-text disagreement over groups of ratings of one text: every unordered pair counts."""
    pairs = differ = lo = up = 0; texts = texts_eq = 0
    for g in groups:
        g = [r for r in g if r["S"] is not None]
        if len(g) < 2: continue
        texts += 1; texts_eq += len({r["S"] for r in g}) == 1
        for a, b in itertools.combinations(g, 2):
            pairs += 1; differ += a["S"] != b["S"]
            lo += (a["lower"] is not None and b["lower"] is not None and a["lower"] != b["lower"])
            up += (a["upper"] is not None and b["upper"] is not None and a["upper"] != b["upper"])
    return {"texts": texts, "texts_all_equal_S": texts_eq, "pairs": pairs, "pairs_differ": differ, "pairs_lower_differ": lo, "pairs_upper_differ": up,
            "q": round(differ / pairs, 4) if pairs else None, "q_lower": round(lo / pairs, 4) if pairs else None, "q_upper": round(up / pairs, 4) if pairs else None}


def analyze_problem(prob: str, fp_all: dict, glm_ids: list | None = None) -> dict:
    records = load_json(ART / f"closure_p{prob}_checkpoints.json") or []
    dist = load_json(ART / f"closure_distinct_p{prob}.json") or []
    ev, stats = load_ratings(prob, glm_ids)
    sha_of, orig_of = {}, {}
    for d in dist:
        for rid in d["record_ids"]: sha_of[rid] = d["sha256"]; orig_of[rid] = d.get("original_sha256") or d["sha256"]
    for i, r in enumerate(records):
        r["_order"] = i; r["sha256"] = sha_of.get(r["id"]) or sha256(text_path(r["path"]).read_bytes())
        r["sha12"] = (orig_of.get(r["id"]) or r["sha256"])[:12]   # original digest where the released copy of a text was anonymized
    text_evs = ["claude_rep1", "claude_rep2", "claude_rep3", "claude_maj3", "gpt", "glm"]

    def S_of(evname, r):
        if evname == "claude_ckpt": x = ev["claude_ckpt"].get(r["id"])
        else: x = ev[evname].get(r["sha256"])
        return None if x is None else x["S"]

    n_dist = len(dist)
    coverage = {e: {"rated_texts": sum(1 for d in dist if ev[e].get(d["sha256"]) and ev[e][d["sha256"]]["S"] is not None), "of_texts": n_dist} for e in text_evs}
    coverage["claude_ckpt"] = {"rated_checkpoints": sum(1 for r in records if S_of("claude_ckpt", r) is not None), "of_checkpoints": len(records)}
    complete = {e for e in text_evs if coverage[e]["rated_texts"] == n_dist} | ({"claude_ckpt"} if coverage["claude_ckpt"]["rated_checkpoints"] == len(records) else set())

    # 1. identical-text control under the per-checkpoint pass
    ctrl_texts, ctrl_detail = [], []
    for d in dist:
        if len(d["record_ids"]) < 2: continue
        rs = [ev["claude_ckpt"].get(rid) for rid in d["record_ids"]]
        Ss = [r["S"] if r else None for r in rs]
        ctrl_texts.append([r for r in rs if r])
        ctrl_detail.append({"text": d["id"], "record_ids": d["record_ids"], "S": Ss, "lower": [r["lower"] if r else None for r in rs],
                            "upper": [r["upper"] if r else None for r in rs], "differs": len({s for s in Ss if s is not None}) > 1,
                            "field_differs": len({(r["lower"], r["upper"]) for r in rs if r}) > 1})
    ctrl = pair_stats(ctrl_texts)
    ctrl.update({"repeated_texts": len(ctrl_detail), "texts_with_different_S": sum(c["differs"] for c in ctrl_detail),
                 "texts_with_different_fields": sum(c["field_differs"] for c in ctrl_detail), "detail": ctrl_detail})

    # 2. Claude same-text disagreement over the three text passes (primary) and over every Claude rating of the text (secondary)
    groups3 = [[ev[f"claude_rep{k}"][d["sha256"]] for k in (1, 2, 3) if d["sha256"] in ev[f"claude_rep{k}"]] for d in dist]
    groups_all = [g + [ev["claude_ckpt"][rid] for rid in d["record_ids"] if rid in ev["claude_ckpt"]] for g, d in zip(groups3, dist)]
    q3, qall = pair_stats(groups3), pair_stats(groups_all)
    per_text = [{"text": d["id"], "lineage": d["lineage"], "records": len(d["record_ids"]),
                 "claude_rep": [S_of(f"claude_rep{k}", {"sha256": d["sha256"]}) for k in (1, 2, 3)],
                 "claude_ckpt": [S_of("claude_ckpt", {"id": rid}) for rid in d["record_ids"]],
                 "gpt": S_of("gpt", {"sha256": d["sha256"]}), "glm": S_of("glm", {"sha256": d["sha256"]})} for d in dist]

    # 3. cross-evaluator agreement on S over distinct texts
    def kap(e1, e2):
        pairs = [(ev[e1][h]["S"], ev[e2][h]["S"]) for h in (d["sha256"] for d in dist)
                 if h in ev[e1] and h in ev[e2] and ev[e1][h]["S"] is not None and ev[e2][h]["S"] is not None]
        return kappa(pairs)
    agreement = {"claude_rep1_vs_gpt": kap("claude_rep1", "gpt"), "claude_maj3_vs_gpt": kap("claude_maj3", "gpt"),
                 "claude_rep1_vs_glm": kap("claude_rep1", "glm"), "claude_maj3_vs_glm": kap("claude_maj3", "glm"), "gpt_vs_glm": kap("gpt", "glm"),
                 "claude_rep2_vs_gpt": kap("claude_rep2", "gpt"), "claude_rep3_vs_gpt": kap("claude_rep3", "gpt")}
    field_agreement = {}
    for e1, e2 in (("claude_rep1", "gpt"), ("claude_rep1", "glm")):
        both = [(ev[e1][h], ev[e2][h]) for h in (d["sha256"] for d in dist) if h in ev[e1] and h in ev[e2] and ev[e1][h]["S"] is not None and ev[e2][h]["S"] is not None]
        field_agreement[f"{e1}_vs_{e2}"] = {"both_present": len(both), "lower_equal": sum(a["lower"] == b["lower"] for a, b in both),
                                              "upper_equal": sum(a["upper"] == b["upper"] for a, b in both)}

    # 4. trajectory conclusions per lineage under each evaluator
    evaluators = ["claude_ckpt", "claude_rep1", "claude_rep2", "claude_rep3", "claude_maj3", "gpt", "glm"]
    core = ["claude_ckpt", "claude_rep1", "claude_rep2", "claude_rep3", "gpt"]
    singles = ["claude_ckpt", "claude_rep1", "claude_rep2", "claude_rep3", "gpt", "glm"]   # every single evaluator (majority is derived)
    fp, fg = fp_all.get(prob, {}), final_grades(prob)
    groups = defaultdict(list)
    for r in records: groups[r["lineage"]].append(r)
    lineages = []
    for lin, its in sorted(groups.items()):
        its = sorted(its, key=lambda r: order_key(r, r["_order"]))
        seqs = {e: [S_of(e, r) for r in its] for e in evaluators}
        concs = {e: conclusions(seqs[e]) for e in evaluators}
        full = [e for e in evaluators if all(s is not None for s in seqs[e])]
        core_full = [e for e in core if e in full]
        rec = {"lineage": lin, "model": its[0]["model"], "source": "ours" if lin.startswith("ours") else "public", "n_checkpoints": len(its),
               "checkpoints": [{"id": r["id"], "sha12": r["sha12"]} for r in its], "S_sequences": seqs, "conclusions": concs,
               "evaluators_complete": full, "identical_core": {}, "identical_all_complete": {}}
        rec["core_complete"] = len(core_full) == len(core)
        rec["all_complete"] = all(e in full for e in singles)
        rec["identical_all_evaluators"] = {}
        for c in CONCS:
            vals_six = [concs[e][c] for e in singles]
            rec["identical_all_evaluators"][c] = None if not rec["all_complete"] else (len({json.dumps(v) for v in vals_six}) == 1 and None not in vals_six)
            vals_core = [concs[e][c] for e in core_full]
            vals_all = [concs[e][c] for e in full]
            # None = not evaluable (a core evaluator has not rated every checkpoint of the lineage); True/False otherwise
            rec["identical_core"][c] = None if not rec["core_complete"] else (len({json.dumps(v) for v in vals_core}) == 1 and None not in vals_core)
            rec["identical_all_complete"][c] = None if not rec["core_complete"] else (len({json.dumps(v) for v in vals_all}) == 1 and None not in vals_all)
        rec["S_final"] = {e: seqs[e][-1] for e in evaluators}
        rec["n_S1"] = {e: sum(s == 1 for s in seqs[e]) for e in evaluators}
        if rec["source"] == "public":
            m = its[0]["model"]
            rec.update(first_pass_grade=fp.get(m), final_grade=fg.get(m), last_is_final=(its[-1].get("context") == 99))
        lineages.append(rec)
    n_lin = len(lineages)
    identical = {"core": {c: sum(l["identical_core"][c] is True for l in lineages) for c in CONCS},
                 "all_complete": {c: sum(l["identical_all_complete"][c] is True for l in lineages) for c in CONCS},
                 "all_evaluators": {c: sum(l["identical_all_evaluators"][c] is True for l in lineages) for c in CONCS},
                 "core_evaluators": core, "single_evaluators": singles,
                 "lineages_with_glm_complete": sum("glm" in l["evaluators_complete"] for l in lineages),
                 "n_lineages_core_complete": sum(l["core_complete"] for l in lineages),
                 "n_lineages_complete": sum(l["all_complete"] for l in lineages),
                 "lineages_not_evaluable": [l["lineage"] for l in lineages if not l["core_complete"]],
                 "definitions": {"all_complete": "identical and determined under every evaluator with complete coverage of the lineage; denominator n_lineages_core_complete (the five core evaluators must be complete)",
                                 "all_evaluators": "identical under all six single evaluators (Claude per-checkpoint, Claude passes 1-3, GPT, GLM); denominator n_lineages_complete (every evaluator rated every checkpoint of the lineage)"}}
    flips = [{"lineage": l["lineage"], "conclusions": [c for c in CONCS if l["identical_all_complete"][c] is False],
              "values": {c: {e: l["conclusions"][e][c] for e in l["evaluators_complete"]} for c in CONCS if l["identical_all_complete"][c] is False},
              "sequences": {e: l["S_sequences"][e] for e in l["evaluators_complete"]}}
             for l in lineages if l["core_complete"] and any(v is False for v in l["identical_all_complete"].values())]

    # 5. regularities per evaluator (checkpoint-level S=1 counts, crossings, regressions, S_final=2)
    per_eval = {}
    for e in evaluators:
        seqs = [l["S_sequences"][e] for l in lineages]
        known = [[s for s in q if s is not None] for q in seqs]
        per_eval[e] = {"complete": e in complete, "n_S1_checkpoints": sum(s == 1 for q in seqs for s in q),
                       "n_S0_checkpoints": sum(s == 0 for q in seqs for s in q), "n_S2_checkpoints": sum(s == 2 for q in seqs for s in q),
                       "n_unknown_checkpoints": sum(s is None for q in seqs for s in q),
                       "n_S_final_2": sum(q[-1] == 2 for q in seqs), "n_regressing_lineages": sum(any(a > b for a, b in zip(k, k[1:])) for k in known),
                       "n_crossings_inside_record": sum(l["conclusions"][e]["crossing"] not in (None, "none", 0) for l in lineages),
                       "n_improved": sum(l["conclusions"][e]["improved"] is True for l in lineages),
                       "n_ramps_1_to_2": sum(any(a == 1 and b == 2 for a, b in zip(k, k[1:])) for k in known)}
        # 6. public finals: S=2 iff first-pass grade >= 5 (and iff final grade >= 5)
        pub = [l for l in lineages if l["source"] == "public"]
        for gname, gkey in (("first_pass", "first_pass_grade"), ("final", "final_grade")):
            ok = [l for l in pub if l["S_final"][e] is not None and l.get(gkey) is not None]
            agree = sum((l["S_final"][e] == 2) == (l[gkey] >= 5) for l in ok)
            per_eval[e][f"grade_agreement_{gname}"] = {"agree": agree, "of": len(ok), "disagree": [
                {"lineage": l["lineage"], "S_final": l["S_final"][e], "grade": l[gkey]} for l in ok if (l["S_final"][e] == 2) != (l[gkey] >= 5)]}
    s1_range = [per_eval[e]["n_S1_checkpoints"] for e in evaluators if e in complete and e != "claude_maj3"]
    return {"n_checkpoints": len(records), "n_distinct_texts": n_dist, "n_lineages": n_lin, "n_public_lineages": sum(l["source"] == "public" for l in lineages),
            "n_repeated_texts": sum(len(d["record_ids"]) > 1 for d in dist), "rating_stats": stats, "coverage": coverage, "complete_evaluators": sorted(complete),
            "identical_text_control_claude_ckpt": ctrl, "claude_q_three_text_passes": q3, "claude_q_all_claude_ratings": qall,
            "agreement": agreement, "field_agreement": field_agreement, "conclusions_identical": identical, "flips": flips, "per_evaluator": per_eval,
            "S1_range_complete_single_evaluators": [min(s1_range), max(s1_range)] if s1_range else None, "lineages": lineages, "per_text": per_text}


def reference_values() -> dict:
    """The paper's P3/P6 numbers, read from the released artifacts (no recomputation of adjudicated layers)."""
    rel = load_json(ART / "closure_adjudicated" / "reliability.json") or {}
    cs = load_json(ART / "conclusion_sensitivity" / "results.json") or {}
    reg = load_json(ART / "closure_matrix" / "regularities.json") or {}
    fp_all = first_pass_grades()
    out = {}
    for prob, mani, group, cdir, gdir in (("3", "closure_checkpoints.json", "closure", "closure_claude/p3", "closure_gpt/p3"),
                                          ("6", "closure_p6_checkpoints.json", "closure_p6", "closure_claude/p6", "closure_gpt/p6")):
        r = rel.get(prob, {}); q = ((cs.get("q") or {}).get("claude") or {}).get(prob) or {}
        sv = ((cs.get("survival") or {}).get("per_problem") or {}).get(prob) or {}
        cov = (cs.get("coverage") or {}).get(prob) or {}
        sens = reg.get("sensitivity_by_layer") or {}
        s1 = [sens[l][prob]["n_S1_checkpoints"] for l in ("raw", "glm", "kimi", "claude", "gpt") if l in sens and prob in sens[l] and sens[l][prob].get("n_S1_checkpoints") is not None]
        # like-for-like Claude-vs-GPT kappa and grade agreement, recomputed from the released per-text ratings
        cl = {a["sha256"]: rating(a) for a in annotations(ART / cdir)}; gp = {a["sha256"]: rating(a) for a in annotations(ART / gdir)}
        gl = {a["sha256"]: rating(a) for a in annotations(ART / f"closure_glm_rerun/p{prob}")}
        common = [h for h in cl if h in gp and cl[h]["S"] is not None and gp[h]["S"] is not None]
        kcg = kappa([(cl[h]["S"], gp[h]["S"]) for h in common])
        kcl = kappa([(cl[h]["S"], gl[h]["S"]) for h in cl if h in gl and cl[h]["S"] is not None and gl[h]["S"] is not None])
        recs = checkpoint_manifest(mani, group)
        fp = fp_all.get(prob, {}); fg = final_grades(prob); ga = {}; gaf = {}
        for e, pool in (("claude", cl), ("gpt", gp)):
            ok = agree = okf = agreef = 0
            for rec in recs:
                if rec.get("context") != 99: continue
                h = source_digest(rec["path"]); g = fp.get(rec["model"]); x = pool.get(h)
                if x is None or x["S"] is None: continue
                if g is not None: ok += 1; agree += (x["S"] == 2) == (g >= 5)
                if fg.get(rec["model"]) is not None: okf += 1; agreef += (x["S"] == 2) == (fg[rec["model"]] >= 5)
            ga[e] = {"agree": agree, "of": ok}; gaf[e] = {"agree": agreef, "of": okf}
        out[prob] = {"n_lineages": sv.get("n_lineages") or cov.get("lineages"), "n_checkpoints": cov.get("checkpoints_applicable"), "n_distinct_texts": r.get("distinct_texts"),
                     "layer0_repeated_texts": r.get("repeated_texts"), "layer0_repeated_consistent_S": r.get("repeated_consistent_S"),
                     "claude_q": q.get("q"), "claude_q_pairs": q.get("pairs"), "claude_q_texts": q.get("texts"),
                     "kappa_claude_vs_gpt_released": kcg, "kappa_claude_vs_glm_released": kcl,
                     "kappa_glm_vs_claude_paper": (r.get("kappa_S_glm_vs_claude") or {}).get("kappa"), "kappa_glm_vs_gpt_paper": (r.get("kappa_S_glm_vs_gpt") or {}).get("kappa"),
                     "identical_across_evaluators": sv.get("identical_across_evaluators"), "S1_range_single_evaluators": [min(s1), max(s1)] if s1 else None,
                     "S1_layers": {l: sens[l][prob]["n_S1_checkpoints"] for l in ("raw", "glm", "kimi", "claude", "gpt") if l in sens},
                     "grade_agreement_first_pass_public_finals": ga, "grade_agreement_final_public_finals": gaf}
    # Layer-0 identical-text control of the paper (closure_adjudicated/reliability.json), per problem and pooled; the macro text quotes it.
    lt = {}
    for prob in ("3", "6", "2"):
        r = rel.get(prob) or {}
        if r.get("repeated_texts") is not None and r.get("repeated_consistent_S") is not None:
            lt[prob] = {"repeated_texts": r["repeated_texts"], "consistent_S": r["repeated_consistent_S"], "differ": r["repeated_texts"] - r["repeated_consistent_S"]}
    if lt: lt["pooled"] = {"repeated_texts": sum(v["repeated_texts"] for v in lt.values()), "differ": sum(v["differ"] for v in lt.values())}
    out["layer0_identical_text_paper"] = lt
    return out


def fmt(x, nd=2): return "--" if x is None else f"{x:.{nd}f}"
def frac(a, b): return "--" if a is None or b is None else f"{a}/{b}"
def rng(v): return "--" if not v else (str(v[0]) if v[0] == v[1] else f"{v[0]}--{v[1]}")
def nword(n): return {0: "no", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}.get(n, str(n))
def esc(s): return str(s).replace("_", "\\_").replace("&", "\\&").replace("%", "\\%")


def table(res: dict, ref: dict, probs: list[str]) -> str:
    L = ["% generated by scripts/replication_ext.py -- do not edit.  Rows P1/P4/P5: this replication; P3/P6: the paper's values for reference.",
         "% identical text = distinct texts retained under >1 record whose records got different S under one rating per checkpoint",
         "%   (P1/P4/P5: Claude Opus 5 per-checkpoint pass; P3/P6: the paper's layer 0, GLM-5.3);",
         "% q = same-model same-text pairwise disagreement on S (P1/P4/P5: three Claude Opus 5 text passes; P3/P6: paper, four Claude ratings per text);",
         "% kappa = Cohen's kappa on S over distinct texts (Claude Opus 5 first text pass vs GPT-5.6-Sol / GLM-5.3; P3/P6 recomputed from the released per-text ratings, n in results.json);",
         "% same conclusions = lineages whose improved/regressed/first-crossing conclusions are identical under every evaluator with complete coverage;",
         "% S=1 = range over complete single evaluators of the number of S=1 checkpoints; grade = public final files with (S=2) == (first-pass grade >= 5), Claude / GPT.",
         "\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{@{}lrrrccccccc@{}}", "  \\toprule",
         "  & & & & identical & Claude & \\multicolumn{2}{c}{$\\kappa$ on $S$} & same conclusions & $S{=}1$ & $S{=}2$ iff grade${\\ge}5$ \\\\",
         "  \\cmidrule(lr){7-8}",
         "  Problem & lin. & ckpt. & texts & differs & $q$ & Cl--GPT & Cl--GLM & impr./regr./cross. & ckpts & Claude, GPT \\\\", "  \\midrule"]
    for p in probs:
        r = res[p]; c = r["identical_text_control_claude_ckpt"]; ag = r["agreement"]; idn = r["conclusions_identical"]["all_complete"]; n = r["n_lineages"]
        kcg = ag["claude_rep1_vs_gpt"]; kcl = ag["claude_rep1_vs_glm"]
        glm_cov = r["coverage"]["glm"]
        kcl_txt = "--" if kcl is None else (fmt(kcl["kappa"]) + ("" if glm_cov["rated_texts"] == glm_cov["of_texts"] else f"$^{{({kcl['n']})}}$"))
        pe = r["per_evaluator"]
        ga = f"{frac(pe['claude_rep1']['grade_agreement_first_pass']['agree'], pe['claude_rep1']['grade_agreement_first_pass']['of'])}, {frac(pe['gpt']['grade_agreement_first_pass']['agree'], pe['gpt']['grade_agreement_first_pass']['of'])}"
        L.append(f"  P{p} & {n} & {r['n_checkpoints']} & {r['n_distinct_texts']} & {c['texts_with_different_S']}/{c['repeated_texts']} & {fmt(r['claude_q_three_text_passes']['q'])} & "
                 f"{fmt(kcg['kappa']) if kcg else '--'} & {kcl_txt} & {idn['improved']}/{idn['regressed']}/{idn['crossing']} & {rng(r['S1_range_complete_single_evaluators'])} & {ga} \\\\")
    L.append("  \\midrule")
    for p in ("3", "6"):
        r = ref.get(p) or {}; idn = r.get("identical_across_evaluators") or {}; n = r.get("n_lineages"); kcg = r.get("kappa_claude_vs_gpt_released"); kcl = r.get("kappa_claude_vs_glm_released")
        ga = r.get("grade_agreement_first_pass_public_finals") or {}
        rep = r.get("layer0_repeated_texts"); cons = r.get("layer0_repeated_consistent_S")
        L.append(f"  P{p} (paper) & {n} & {r.get('n_checkpoints')} & {r.get('n_distinct_texts')} & {'--' if rep is None else f'{rep - cons}/{rep}'}$^{{\\mathrm{{a}}}}$ & {fmt(r.get('claude_q'))}$^{{\\mathrm{{b}}}}$ & "
                 f"{fmt(kcg['kappa']) if kcg else '--'} & {fmt(kcl['kappa']) if kcl else '--'} & {idn.get('improved', '--')}/{idn.get('regressed', '--')}/{idn.get('crossing', '--')} & {rng(r.get('S1_range_single_evaluators'))} & "
                 f"{frac(ga.get('claude', {}).get('agree'), ga.get('claude', {}).get('of'))}, {frac(ga.get('gpt', {}).get('agree'), ga.get('gpt', {}).get('of'))} \\\\")
    L += ["  \\bottomrule", "\\end{tabular}",
          "\\par\\smallskip\\scriptsize identical text: texts retained under more than one record whose records received different $S$ from one rating per checkpoint "
          "(P1/P4/P5: Claude Opus~5; $^{\\mathrm{a}}$P3/P6: the paper's layer~0, GLM-5.3). $q$: same-text pairwise disagreement on $S$ over three Claude Opus~5 text passes "
          "($^{\\mathrm{b}}$paper: four Claude ratings per text). $\\kappa$: Cohen's $\\kappa$ on $S$ over distinct texts, Claude first text pass vs.\\ GPT-5.6-Sol / GLM-5.3 "
          "(P3/P6 recomputed from the released per-text ratings; a superscript gives $n$ where GLM-5.3 had not rated every text at the freeze). "
          "Same conclusions: lineages (of the number in column lin.) whose improved / regressed / first-crossing conclusions coincide under every evaluator with complete coverage. "
          "$S{=}1$: range over complete single evaluators of the number of $S{=}1$ checkpoints. Grade: public final files with $(S{=}2)\\Leftrightarrow(\\text{first-pass grade}\\ge5)$ under Claude and GPT "
          "(P1/P4/P5: first-pass and final grades coincide; P6 (paper): the Kimi K3 final file follows a repair round, first-pass 3, final 7, and against final grades the P6 cells read "
          + ", ".join(frac(ref["6"]["grade_agreement_final_public_finals"][e]["agree"], ref["6"]["grade_agreement_final_public_finals"][e]["of"]) for e in ("claude", "gpt")) + ")."]
    return "\n".join(L) + "\n"


def macros(res: dict, ref: dict, probs: list[str], tbl: str) -> str:
    def rp(p): return res[p]
    cov = "; ".join(f"P{p}: {rp(p)['n_checkpoints']} checkpoints, {rp(p)['n_distinct_texts']} distinct texts, {rp(p)['n_lineages']} lineages" for p in probs)
    glm = [(p, rp(p)["coverage"]["glm"]) for p in probs]
    glm_txt = ", ".join(f"{c['rated_texts']} of {c['of_texts']} P{p} texts" for p, c in glm)
    total_texts = sum(rp(p)["n_distinct_texts"] for p in probs); total_ck = sum(rp(p)["n_checkpoints"] for p in probs); total_lin = sum(rp(p)["n_lineages"] for p in probs)
    ck_n = sum(rp(p)["coverage"]["claude_ckpt"]["rated_checkpoints"] for p in probs)
    tx_n = sum(rp(p)["coverage"][f"claude_rep{k}"]["rated_texts"] for p in probs for k in (1, 2, 3))
    gpt_n = sum(rp(p)["coverage"]["gpt"]["rated_texts"] for p in probs)
    ck_txt = "every checkpoint once" if ck_n == total_ck else f"{ck_n} of the {total_ck} checkpoints once"
    tx_txt = "every distinct text three times" if tx_n == 3 * total_texts else f"the distinct texts three times ({tx_n} of {3 * total_texts} ratings)"
    gpt_txt = "every distinct text once" if gpt_n == total_texts else f"{gpt_n} of the {total_texts} distinct texts once"
    coverage = (f"Corpus ({cov}; {total_ck} checkpoints, {total_texts} distinct texts, {total_lin} lineages in all, the nine public runs and our GLM-5.2, GPT-5.6-Sol ultra and Nemotron runs on each problem). "
                f"Claude Opus~5 rated {ck_txt} and {tx_txt}, GPT-5.6-Sol rated {gpt_txt}, "
                f"and GLM-5.3, launched last, had rated {glm_txt} at the freeze (rubrics anchored to the published solutions; no validity layer).")
    # headline sentences
    rep_total = sum(rp(p)["identical_text_control_claude_ckpt"]["repeated_texts"] for p in probs)
    dif_total = sum(rp(p)["identical_text_control_claude_ckpt"]["texts_with_different_S"] for p in probs)
    dif_detail = "; ".join(f"P{p}: {rp(p)['identical_text_control_claude_ckpt']['texts_with_different_S']} of {rp(p)['identical_text_control_claude_ckpt']['repeated_texts']}" for p in probs)
    fld = sum(rp(p)["identical_text_control_claude_ckpt"]["texts_with_different_fields"] for p in probs)
    qs = "/".join(fmt(rp(p)["claude_q_three_text_passes"]["q"]) for p in probs)
    qpairs = sum(rp(p)["claude_q_three_text_passes"]["pairs"] for p in probs); qdiff = sum(rp(p)["claude_q_three_text_passes"]["pairs_differ"] for p in probs)
    qall = sum(rp(p)["claude_q_all_claude_ratings"]["pairs_differ"] for p in probs), sum(rp(p)["claude_q_all_claude_ratings"]["pairs"] for p in probs)
    kcg = "/".join(fmt(rp(p)["agreement"]["claude_rep1_vs_gpt"]["kappa"]) if rp(p)["agreement"]["claude_rep1_vs_gpt"] else "--" for p in probs)
    kcl_parts = []
    for p in probs:
        k = rp(p)["agreement"]["claude_rep1_vs_glm"]
        kcl_parts.append("--" if k is None else fmt(k["kappa"]) + (f" ($n{{=}}{k['n']}$)" if k["n"] != rp(p)["n_distinct_texts"] else ""))
    idn = [rp(p)["conclusions_identical"]["all_complete"] for p in probs]; ns = [rp(p)["conclusions_identical"]["n_lineages_core_complete"] for p in probs]
    idn_txt = ", ".join(f"{d['improved']}/{d['regressed']}/{d['crossing']} of {n} on P{p}" for d, n, p in zip(idn, ns, probs))
    six = [rp(p)["conclusions_identical"]["all_evaluators"] for p in probs]; n6 = [rp(p)["conclusions_identical"]["n_lineages_complete"] for p in probs]
    six_txt = ", ".join(f"{d['improved']}/{d['regressed']}/{d['crossing']} of {n} on P{p}" for d, n, p in zip(six, n6, probs))
    n_all = sum(ns); n_six = sum(n6)
    flips = [(p, f) for p in probs for f in rp(p)["flips"]]
    EVN = {"claude_ckpt": "Claude per-checkpoint", "claude_rep1": "Claude pass~1", "claude_rep2": "Claude pass~2", "claude_rep3": "Claude pass~3",
           "claude_maj3": "Claude majority", "gpt": "GPT", "glm": "GLM"}
    def val_txt(c, v):
        if c == "crossing": return "none" if v == "none" else ("?" if v is None else f"checkpoint {v + 1}")
        return "?" if v is None else ("yes" if v else "no")
    def flip_desc(p, f):
        parts = []
        for c in f["conclusions"]:
            by = defaultdict(list)
            for e, v in f["values"][c].items(): by[json.dumps(v)].append(EVN.get(e, e))
            groups = sorted(by.items(), key=lambda kv: -len(kv[1]))
            parts.append(f"{c} " + "; ".join(f"{val_txt(c, json.loads(k))} under {', '.join(ev)}" for k, ev in groups))
        return f"P{p} {esc(f['lineage'])} ({'; '.join(parts)})"
    flip_txt = ("; the flips are " + "; ".join(flip_desc(p, f) for p, f in flips)) if flips else "; no lineage's conclusions change with the evaluator"
    s1 = ", ".join(f"{rng(rp(p)['S1_range_complete_single_evaluators'])} on P{p}" for p in probs)
    ga_c = sum(rp(p)["per_evaluator"]["claude_rep1"]["grade_agreement_first_pass"]["agree"] for p in probs); ga_of = sum(rp(p)["per_evaluator"]["claude_rep1"]["grade_agreement_first_pass"]["of"] for p in probs)
    ga_g = sum(rp(p)["per_evaluator"]["gpt"]["grade_agreement_first_pass"]["agree"] for p in probs); ga_of_g = sum(rp(p)["per_evaluator"]["gpt"]["grade_agreement_first_pass"]["of"] for p in probs)
    ref_id = "; ".join(f"P{p}: {ref[p]['identical_across_evaluators']['improved']}/{ref[p]['identical_across_evaluators']['regressed']}/{ref[p]['identical_across_evaluators']['crossing']} of {ref[p]['n_lineages']}" for p in ("3", "6") if ref.get(p) and ref[p].get("identical_across_evaluators"))
    lt = ref.get("layer0_identical_text_paper") or {}
    def lt_txt(keys):
        vals = [lt[k] for k in keys if k in lt]
        return None if not vals else f"{sum(v['differ'] for v in vals)} of {sum(v['repeated_texts'] for v in vals)}"
    paper_ctrl = ", ".join(s for s in ((f"{lt_txt(('3', '6'))} on P3/P6" if lt_txt(("3", "6")) else None), (f"{lt_txt(('2',))} on P2" if lt_txt(("2",)) else None)) if s) or "--"
    txt = (f"Under one Claude Opus~5 rating per checkpoint, {dif_total} of the {rep_total} texts retained under more than one record received different labels ({dif_detail}"
           f"{'; ' + str(fld) + ' differed on an obligation field without changing $S$' if fld > dif_total else ''}; paper, layer~0: {paper_ctrl}), "
           f"the same-text disagreement of Claude Opus~5 over three text passes is $q{{=}}{qs}$ on P1/P4/P5 ({qdiff} of {qpairs} pairs; {qall[0]} of {qall[1]} pooling the per-checkpoint ratings; paper: 0.02/0.03 on P3/P6), "
           f"and Cohen's $\\kappa$ on $S$ between Claude Opus~5 and GPT-5.6-Sol is {kcg} (Claude--GLM-5.3: {', '.join(kcl_parts)}; paper: 0.88/0.95 and 0.94/0.90 on P3/P6). "
           f"The improved/regressed/first-crossing conclusions are identical under every evaluator with complete coverage for {idn_txt} lineages "
           f"(the five Claude/GPT evaluators are complete on all {n_all}; over the {n_six} lineages that GLM-5.3 had also rated fully, identical under all six evaluators for {six_txt}; paper: {ref_id}){flip_txt}. "
           f"Across complete single evaluators the number of $S{{=}}1$ checkpoints is {s1}, and $S{{=}}2$ of the final file agrees with the public first-pass grade ${{\\ge}}5$ for "
           f"{ga_c} of {ga_of} public finals under Claude Opus~5 and {ga_g} of {ga_of_g} under GPT-5.6-Sol.")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (f"% generated by scripts/replication_ext.py analyze -- do not edit; loaded by main.tex via \\InputIfFileExists{{gen/replication_macros}}\n% generated={stamp}\n"
            f"\\newcommand{{\\REPLCOVERAGE}}{{{coverage}}}\n\\newcommand{{\\REPLTXT}}{{{txt}}}\n\\newcommand{{\\REPLTABLE}}{{{tbl.rstrip()}}}\n")


def cmd_analyze(args):
    set_root(args.root or ROOT)
    probs = [p for p in args.problems.split(",") if p]
    fp_all = first_pass_grades()
    out = ART / "replication_ext"; out.mkdir(parents=True, exist_ok=True)
    fpath = out / "freeze.json"
    if args.freeze_now or not fpath.exists():
        ids = {p: sorted(a["id"] for a in annotations(ART / "closure_ext" / f"p{p}" / "glm_text") if rating(a)["S"] is not None) for p in probs}
        fpath.write_text(json.dumps({"frozen_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                     "note": "GLM-5.3 text ratings present (parsed) at the freeze; analyze excludes GLM ratings outside this list. Claude and GPT passes were complete.",
                                     "glm_rated_ids": ids, "glm_rated_counts": {p: len(v) for p, v in ids.items()}}, indent=1) + "\n")
        print(f"freeze written: {fpath} (GLM rated: { {p: len(v) for p, v in ids.items()} })")
    freeze = load_json(fpath) or {}
    res = {p: analyze_problem(p, fp_all, (freeze.get("glm_rated_ids") or {}).get(p)) for p in probs}
    ref = reference_values()
    tbl = table(res, ref, probs)
    pooled = {"n_checkpoints": sum(res[p]["n_checkpoints"] for p in probs), "n_distinct_texts": sum(res[p]["n_distinct_texts"] for p in probs), "n_lineages": sum(res[p]["n_lineages"] for p in probs),
              "identical_text_repeated_texts": sum(res[p]["identical_text_control_claude_ckpt"]["repeated_texts"] for p in probs),
              "identical_text_differ": sum(res[p]["identical_text_control_claude_ckpt"]["texts_with_different_S"] for p in probs),
              "claude_q_three_passes": pair_stats([]) if False else {"pairs": sum(res[p]["claude_q_three_text_passes"]["pairs"] for p in probs), "pairs_differ": sum(res[p]["claude_q_three_text_passes"]["pairs_differ"] for p in probs)},
              "n_lineages_core_complete": sum(res[p]["conclusions_identical"]["n_lineages_core_complete"] for p in probs),
              "n_lineages_complete": sum(res[p]["conclusions_identical"]["n_lineages_complete"] for p in probs),
              "conclusions_identical_all_complete": {c: sum(res[p]["conclusions_identical"]["all_complete"][c] for p in probs) for c in CONCS},
              "conclusions_identical_all_evaluators": {c: sum(res[p]["conclusions_identical"]["all_evaluators"][c] for p in probs) for c in CONCS},
              "denominators": "conclusions_identical_all_complete is over n_lineages_core_complete lineages (evaluators with complete coverage; the five core evaluators required); conclusions_identical_all_evaluators is over n_lineages_complete lineages (all six single evaluators, GLM included, complete)"}
    pooled["claude_q_three_passes"]["q"] = round(pooled["claude_q_three_passes"]["pairs_differ"] / pooled["claude_q_three_passes"]["pairs"], 4) if pooled["claude_q_three_passes"]["pairs"] else None
    prov = load_json(public_grades_dir() / "provenance.json") or {}
    meta = {"generated_utc": utc_now(), "problems": probs, "protocol": "artifacts/replication_ext/PROTOCOL.md",
            "freeze": {"file": "artifacts/replication_ext/freeze.json", "frozen_utc": freeze.get("frozen_utc"), "glm_rated_counts": freeze.get("glm_rated_counts")},
            "public_grades": {"dir": "artifacts/replication_ext/public_grades", **{k: prov.get(k) for k in ("source_repository", "source_commit", "captured_utc")}},
            "evaluators": EVALUATORS, "conclusion_definitions": {"improved": "last S > first S", "regressed": "some adjacent decrease",
            "crossing": "0-based index of the first S=2 checkpoint, or 'none'; null = undetermined"},
            "identical_definition": "a lineage counts as identical for a conclusion when the conclusion is equal and determined under every evaluator with complete coverage of the lineage, the five core evaluators (Claude per-checkpoint, Claude text passes 1-3, GPT) being required"}
    # Audit anchors: texts the paper's failure catalogue names, with every evaluator's label (a consistency check, not a validity layer).
    anchors = {}
    for prob, rid, desc in (("1", "p1-nemotron-e1fce43d-v1", "Nemotron P1 draft accepted by two gates on 2026-07-20 (paper id 2853f8e6, run imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d): 'nonincreasing product stays above one'"),
                            ("1", "p1-nemotron-da850012-v1", "Nemotron P1 corrected fresh attempt of 2026-07-21 (paper id dd064edd, run imo-2026-p1-dd064edd0e094391befec955da850012)")):
        if prob not in res: continue
        lin = next((l for l in res[prob]["lineages"] for c in l["checkpoints"] if c["id"] == rid), None)
        if not lin: continue
        pos = next(i for i, c in enumerate(lin["checkpoints"]) if c["id"] == rid)
        anchors[rid] = {"description": desc, "S_by_evaluator": {e: lin["S_sequences"][e][pos] for e in lin["S_sequences"]}}
    (out / "results.json").write_text(json.dumps({"meta": meta, "pooled": pooled, "problems": res, "reference_p3_p6": ref, "audit_anchors": anchors}, indent=1, ensure_ascii=False) + "\n")
    (out / "table_replication.tex").write_text(tbl)
    macro_path = None
    if GEN.is_dir():   # the repository; the flat bundle has no gen/ and receives results.json and the table only
        macro_path = GEN / "replication_macros.tex"; macro_path.write_text(macros(res, ref, probs, tbl))
    for p in probs:
        r = res[p]; c = r["identical_text_control_claude_ckpt"]
        print(f"P{p}: {r['n_checkpoints']} ckpts / {r['n_distinct_texts']} texts / {r['n_lineages']} lineages | complete evaluators: {r['complete_evaluators']}")
        print(f"   identical-text control (claude_ckpt): {c['texts_with_different_S']}/{c['repeated_texts']} texts differ on S ({c['texts_with_different_fields']} on fields); pairs {c['pairs_differ']}/{c['pairs']}")
        q3 = r["claude_q_three_text_passes"]; qa = r["claude_q_all_claude_ratings"]
        print(f"   Claude q (3 text passes): {q3['pairs_differ']}/{q3['pairs']} = {q3['q']} (lower {q3['q_lower']}, upper {q3['q_upper']}); all Claude ratings: {qa['pairs_differ']}/{qa['pairs']} = {qa['q']}")
        for k, v in r["agreement"].items():
            if v: print(f"   kappa {k}: {v['kappa']} (agree {v['observed']}, n={v['n']})")
        idn = r["conclusions_identical"]
        print(f"   conclusions identical: core {idn['core']}  all-complete {idn['all_complete']} (core complete on {idn['n_lineages_core_complete']}, all six evaluators complete on {idn['n_lineages_complete']}, glm complete on {idn['lineages_with_glm_complete']} lineages; not evaluable: {idn['lineages_not_evaluable']})")
        for f in r["flips"]: print(f"   FLIP {f['lineage']}: {f['conclusions']} " + " | ".join(f"{e}={''.join('?' if s is None else str(s) for s in sq)}" for e, sq in f["sequences"].items()))
        for e, v in r["per_evaluator"].items():
            print(f"   {e:<12} complete={v['complete']!s:<5} S1={v['n_S1_checkpoints']} S2final={v['n_S_final_2']} cross={v['n_crossings_inside_record']} regress={v['n_regressing_lineages']} "
                  f"grade-agree fp={v['grade_agreement_first_pass']['agree']}/{v['grade_agreement_first_pass']['of']} final={v['grade_agreement_final']['agree']}/{v['grade_agreement_final']['of']}")
        for l in r["lineages"]:
            print(f"      {l['lineage']:<28} " + " ".join(f"{e[:10]}={''.join('?' if s is None else str(s) for s in l['S_sequences'][e])}" for e in ("claude_ckpt", "claude_rep1", "claude_rep2", "claude_rep3", "gpt", "glm"))
                  + (f"  grade {l.get('first_pass_grade')}->{l.get('final_grade')}" if l["source"] == "public" else ""))
    print(f"\nwrote {out / 'results.json'}, {out / 'table_replication.tex'}" + (f", {macro_path}" if macro_path else f" (no {GEN} directory: replication_macros.tex not written)"))


if __name__ == "__main__":
    main()
