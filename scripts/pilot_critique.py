#!/usr/bin/env python3
"""Paired critique / no-critique continuation pilot (see artifacts/pilot_critique/PREREG.md).
Usage: scripts/pilot_critique.py --key-file ~/.config/vexorium/moonshot_api_key --out artifacts/pilot_critique
Transport: OpenAI-compatible streaming (reuses reviewer_swap.call_openai_stream). Credential never written to outputs.
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, hashlib, json, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from reviewer_swap import call_openai_stream  # noqa: E402

NEURO = pathlib.Path("~/Kaggle/competitions/neurogolf-2026").expanduser()
IMO26 = pathlib.Path("~/Kaggle/competitions/IMO26").expanduser()
SCRATCH = pathlib.Path("[local-path]")
FSL = NEURO / "work/fullscore_portfolio_loop"
KIMI_P6_CRITIQUE = ("A prior reviewer found this defect, which your last session was fixing when it was interrupted (current.md is an "
    "honest partial checkpoint): the Step-4 self-dual-clutter theorem was applied to a Zorn-extracted minimal transversal that is "
    "provably INFINITE in the needed case, while self-duality was only established for FINITE minimal transversals. Continue from "
    "your checkpoint: close the finiteness crux rigorously — either prove the relevant minimal transversal can be taken finite, or "
    "replace the step with an argument using the number-theoretic/greedy structure of the sequence. Update current.md to a complete "
    "self-contained proof only if truly complete.")

def review_text(path, keys=("defects", "fatal_issues", "required_fixes")):
    r = json.loads(pathlib.Path(path).read_text()); out = []
    for k in keys:
        for item in r.get(k) or []: out.append(f"- {item}")
    return "\n".join(out)

CASES = {
  "p3-high": dict(problem=3, state="S=2, local defects",
      text=FSL / "kimi-k3-openrouter-p3-first-pass-replacements-20260813/lane-r1-s3/current.md",
      critique=lambda: review_text(FSL / "kimi-k3-openrouter-p3-first-pass-replacements-20260813/r1-s3-review-only-20260813t0445z/reviews/000.json")),
  "p3-low": dict(problem=3, state="S=0",
      text=FSL / "simple-glm52-p3/p3-glm52-simple-20260811/tasks/imo-2026-p3/candidates/003.md",
      critique=lambda: review_text(FSL / "simple-glm52-p3/p3-glm52-simple-20260811/tasks/imo-2026-p3/reviews/003.json")),
  "p6-mid": dict(problem=6, state="S=1",
      text=SCRATCH / "deedy_ckpts_p6/kimi-k3-round3-t009-01814ca40bb4.md", critique=lambda: "- " + KIMI_P6_CRITIQUE),
  "p6-low": dict(problem=6, state="S=0",
      text=NEURO / "portfolio_transfer/runtime/imo-2026/runs/imo-2026-p6-15817e55f2354705aeee65ac8828b58a/candidate_v2.md",
      critique=lambda: review_text(NEURO / "portfolio_transfer/runtime/imo-2026/runs/imo-2026-p6-15817e55f2354705aeee65ac8828b58a/review_v2.json")),
}
SYSTEM = ("You are a world-class mathematician writing a complete, rigorous, self-contained proof of an IMO 2026 problem in "
          "markdown+LaTeX. You have no tools and no internet access; do not rely on remembering a published solution; every "
          "claim must be proved in your write-up. Output only the full revised write-up.")
TASK_N = "## Task\nRevise the draft above into a complete rigorous proof, fixing any gaps you find. Output the full revised write-up only."
TASK_C = ("## Independent review of the draft\nA reviewer found the following defects:\n{critique}\n\n## Task\nRevise the draft above into "
          "a complete rigorous proof, addressing every listed defect. Output the full revised write-up only.")

def sha(b): return hashlib.sha256(b).hexdigest()

def run_one(args, key, case, cond, rep):
    spec = CASES[case]; out = pathlib.Path(args.out) / f"{case}-{cond}-r{rep}"; out.mkdir(parents=True, exist_ok=True)
    if (out / "output.md").exists() and args.only_missing: return
    lock = out / ".lock"
    if lock.exists() and args.only_missing: return          # another worker/process owns this run
    lock.write_text(str(time.time()))
    statement = (IMO26 / f"problems/problem-{spec['problem']}.md").read_text(); draft = pathlib.Path(spec["text"]).read_bytes()
    user = f"## Problem\n{statement}\n\n## Your current write-up (draft)\n{draft.decode()}\n\n" + (TASK_C.format(critique=spec["critique"]()) if cond == "C" else TASK_N)
    body = {"model": args.model, "max_tokens": args.max_tokens, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]}
    t0 = time.time(); status, resp = 0, {}
    for tries in range(4):
        status, resp = call_openai_stream(args.base_url.rstrip("/") + "/chat/completions", key, body, 900)
        if status < 500 and status != 429: break
        time.sleep(60 * (tries + 1))
    text = ((resp.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    (out / "output.md").write_text(text)
    (out / "response.json").write_text(json.dumps(resp, indent=1, ensure_ascii=False))
    (out / "request_redacted.json").write_text(json.dumps({"model": args.model, "max_tokens": args.max_tokens, "system": SYSTEM,
        "user_sha256": sha(user.encode()), "user_bytes": len(user.encode()), "task_block": TASK_C.format(critique=spec["critique"]()) if cond == "C" else TASK_N}, indent=1, ensure_ascii=False))
    meta = {"case": case, "condition": cond, "repeat": rep, "problem": spec["problem"], "start_state": spec["state"], "draft_sha256": sha(draft),
            "draft_bytes": len(draft), "model": args.model, "endpoint": args.base_url, "http_status": status, "finish_reason": (resp.get("choices") or [{}])[0].get("finish_reason"),
            "usage": resp.get("usage"), "output_sha256": sha(text.encode()), "output_bytes": len(text.encode()), "elapsed_seconds": round(time.time() - t0, 1),
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    lock.unlink(missing_ok=True)
    print(f"[{case} {cond} r{rep}] status={status} finish={meta['finish_reason']} bytes={meta['output_bytes']} ({meta['elapsed_seconds']}s)", flush=True)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="artifacts/pilot_critique"); ap.add_argument("--key-file", required=True)
    ap.add_argument("--base-url", default="https://api.moonshot.cn/v1"); ap.add_argument("--model", default="kimi-k3")
    ap.add_argument("--max-tokens", type=int, default=60000); ap.add_argument("--workers", type=int, default=4); ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--only-missing", action="store_true"); ap.add_argument("--cases", default=None, help="comma-separated subset of cases")
    args = ap.parse_args()
    key = pathlib.Path(args.key_file).expanduser().read_text().strip()
    cases = [c for c in CASES if not args.cases or c in args.cases.split(",")]
    jobs = [(c, cond, r) for c in cases for cond in ("C", "N") for r in range(1, args.repeats + 1)]
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(lambda j: run_one(args, key, *j), jobs))
    print("PILOT_DONE")

if __name__ == "__main__": main()
