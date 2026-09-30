#!/usr/bin/env python3
"""Generate planted-defect mutants from search/replace specifications.

Input: parts/*.json, each a list of entries:
  {"id": "<base_id>-F", "base_id": "...", "base_path": "/abs/path/original", "problem": "3", "type": "F|H|G",
   "obligation": "lower_bound|upper_bound", "ledger_statement": "L3.2", "search": "<verbatim substring occurring exactly once>",
   "replace": "<replacement>", "dependency_argument": "...", "truth": {"AW": "reject", "RT": "reject"}, "check": "<check name or 'none: deletion'>"}
Output: texts/<base_id>/original.md (byte copy), texts/<base_id>/<type>.md, plantings.json (with sha256s and unified diffs), and a
manifest of originals. Fails loudly if a search string is absent or not unique. No model calls.
"""
import difflib, hashlib, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
PARTS = sorted((HERE / "parts").glob("*.json"))

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    entries, originals = [], {}
    for part in PARTS:
        for e in json.load(open(part)):
            entries.append(e)
    problems = []
    for e in entries:
        base = e["base_id"]; src = pathlib.Path(e["base_path"])
        odir = HERE / "texts" / base; odir.mkdir(parents=True, exist_ok=True)
        ob = src.read_bytes()
        (odir / "original.md").write_bytes(ob); originals[base] = {"base_id": base, "path": str(src), "sha256": sha(ob), "problem": e["problem"]}
        text = ob.decode("utf-8")
        n = text.count(e["search"])
        if n != 1:
            problems.append(f"{e['id']}: search string occurs {n} times"); continue
        if e["search"] == e["replace"]:
            problems.append(f"{e['id']}: replace equals search"); continue
        mutant = text.replace(e["search"], e["replace"], 1)
        (odir / f"{e['type']}.md").write_text(mutant)
        diff = "".join(difflib.unified_diff(text.splitlines(True), mutant.splitlines(True), fromfile=f"{base}/original.md", tofile=f"{base}/{e['type']}.md", n=1))
        e2 = dict(e); e2.update({"sha256_original": sha(ob), "sha256_mutant": sha(mutant.encode()), "hunk": diff, "hunk_chars_removed": len(e["search"]), "hunk_chars_added": len(e["replace"])})
        entries[entries.index(e)] = e2
    out = {"generated_by": "make_mutants.py", "originals": list(originals.values()), "plantings": [e for e in entries if "sha256_mutant" in e], "problems": problems}
    (HERE / "plantings.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"originals {len(originals)}, mutants {len(out['plantings'])}, problems {len(problems)}")
    for p in problems: print("  PROBLEM:", p)
    return 1 if problems else 0

if __name__ == "__main__": sys.exit(main())
