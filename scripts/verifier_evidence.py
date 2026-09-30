#!/usr/bin/env python3
"""Do verifiers respond to decisive evidence?  Four independently checkable local claims taken from the audit, each shown to a
tool-free verifier (a) alone, (b) with a valid counterexample, (c) with a deliberately invalid counterexample.  The verifier is asked
to assess the witness separately from the claim.  Claims C1-C3 are false statements that appeared in accepted or highly rated
proof texts; C4 is a true statement (control for following a confident but wrong objection).
Usage: verifier_evidence.py --verifier glm|kimi --key-file ... [--base-url ...]   Outputs artifacts/verifier_evidence/<verifier>/<claim>-<cond>/
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, hashlib, json, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from reviewer_swap import call as api_call, extract_json  # noqa: E402
from cli_transport import call_claude_cli, call_codex_cli  # noqa: E402

def call(base_url, key, body, timeout, api):
    if api in ("claude-cli", "codex-cli"):
        system = body.get("system") or next((m["content"] for m in body["messages"] if m["role"] == "system"), "")
        user = next(m["content"] for m in body["messages"] if m["role"] == "user")
        return (call_claude_cli if api == "claude-cli" else call_codex_cli)(body["model"], system, user, min(timeout, 1800))
    return api_call(base_url, key, body, timeout, api)

CLAIMS = {
 "C1": {"source": "Nemotron 3 Ultra, IMO 2026 P1 draft accepted by two model gates (invalid local inference)",
        "claim": "Let q_1, q_2, q_3, ... be a sequence of positive real numbers with q_1 > 1 and q_{k+1} <= q_k for every k. Then q_k > 1 for every k.",
        "truth": False,
        "valid": "The sequence q_1 = 2, q_2 = 1, q_3 = 1, ... satisfies q_1 > 1 and is nonincreasing, but q_2 = 1 is not greater than 1.",
        "invalid": "The sequence q_1 = 2, q_2 = 3, q_3 = 0.5, ... has q_3 = 0.5 < 1, so the claim fails."},
 "C2": {"source": "GPT-5.6-Sol (default effort), public IMO 2026 P6 run graded 1/7; two frontier annotators rated the proof complete",
        "claim": "Every family of nonempty finite sets that is pairwise intersecting (any two members share an element) has only finitely many inclusion-minimal finite transversals (finite sets meeting every member of the family).",
        "truth": False,
        "valid": "Take distinct symbols x_1, x_2, ... and y_1, y_2, ..., and let F_n = {x_1, ..., x_n, y_n} for n >= 1. Any two members share x_1, so the family is pairwise intersecting. For each k >= 1, T_k = {y_1, ..., y_{k-1}, x_k} meets F_n through y_n when n < k and through x_k when n >= k, so it is a finite transversal; removing y_i misses F_i and removing x_k misses F_k, so it is inclusion-minimal. The T_k are pairwise distinct, so there are infinitely many.",
        "invalid": "Take F_n = {x_n} for n >= 1 with distinct symbols x_n. Then each T_k = {x_k} is a minimal finite transversal, so there are infinitely many."},
 "C3": {"source": "Nemotron 3 Ultra, IMO 2026 P6 draft (false key observation recorded by the gate)",
        "claim": "Let a_1 < a_2 < ... be the greedy sequence of IMO 2026 Problem 6 (each a_{n+1} is the least integer greater than a_n sharing a prime factor with every earlier term). Then for every n the set of prime factors of a_{n+1} is an inclusion-minimal hitting set of the family of prime-factor sets of a_1, ..., a_n.",
        "truth": False,
        "valid": "Start with a_1 = 6, a_2 = 8. The least integer above 8 sharing a factor with both 6 and 8 is 10, so a_3 = 10 with prime set {2, 5}. The family {{2,3}, {2}} is already hit by {2} alone, so {2, 5} is a hitting set but not inclusion-minimal.",
        "invalid": "Start with a_1 = 6, a_2 = 8, a_3 = 9. Then the prime set of a_3 is {3}, which does not hit {2}, so the claim fails."},
 "C4": {"source": "IMO 2026 P3, published lower-bound argument (true statement, control)",
        "claim": "For the division of a stick into n+1 parts of lengths 1, 2, 4, ..., 2^n (in some unit), all 2^{n+1} subset sums of the parts are pairwise distinct.",
        "truth": True,
        "valid": None,
        "invalid": "For n = 2 the parts are 1, 2, 4; the subsets {1, 4} and {2, 3} both have sum 5, so two subset sums coincide."},
}
SYSTEM = ("You are a careful mathematical verifier. You will be shown a claim and possibly a proposed counterexample (a witness). "
          "Assess them separately and independently. Do not defer to the confidence of the proposer. Do not retrieve or recall published solutions; "
          "reason from first principles. Return ONLY a JSON object with exactly these fields: "
          '{"claim_true": true|false, "claim_reason": "<=60 words", "witness_valid": true|false|null, "witness_reason": "<=60 words or null"}. '
          "witness_valid is null when no witness is given; otherwise it is true only if the witness satisfies every hypothesis of the claim and violates its conclusion.")

def user_text(c, cond):
    t = f"## Claim\n{c['claim']}\n\n"
    if cond == "alone": t += "## Witness\nNone. Assess the claim on its own."
    else: t += f"## Proposed counterexample\n{c[cond]}\n\nAssess (1) whether this witness is a valid counterexample to the claim and (2) whether the claim is true."
    return t

def run_one(args, key, cid, cond):
    c = CLAIMS[cid]
    if cond == "valid" and c["valid"] is None: return
    out = pathlib.Path(args.out) / args.verifier / f"{cid}-{cond}"; out.mkdir(parents=True, exist_ok=True)
    if (out / "parsed.json").exists() and args.only_missing: return
    user = user_text(c, cond)
    if args.api in ("openai", "claude-cli", "codex-cli"):
        body = {"model": args.model, "max_tokens": args.max_tokens, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]}
    else:
        body = {"model": args.model, "max_tokens": args.max_tokens, "system": SYSTEM, "messages": [{"role": "user", "content": user}], "thinking": {"type": "enabled", "budget_tokens": args.thinking_budget}}
    t0 = time.time(); status, resp = call(args.base_url, key, body, 1800, args.api)
    if args.api == "openai": text = ((resp.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    else: text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
    parsed = extract_json(text) if status == 200 else None
    (out / "request.json").write_text(json.dumps({"system": SYSTEM, "user": user, "model": args.model, "condition": cond, "claim_id": cid, "claim_truth": c["truth"]}, indent=1, ensure_ascii=False))
    (out / "response.json").write_text(json.dumps(resp, indent=1, ensure_ascii=False))
    (out / "parsed.json").write_text(json.dumps({"claim_id": cid, "condition": cond, "verifier": args.verifier, "model": args.model, "status": status, "parsed": parsed,
                                                 "expected": {"claim_true": c["truth"], "witness_valid": None if cond == "alone" else (cond == "valid")},
                                                 "elapsed_seconds": round(time.time() - t0, 1)}, indent=1, ensure_ascii=False))
    print(f"[{args.verifier} {cid} {cond}] status={status} parsed={parsed}", flush=True)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--verifier", required=True, choices=["glm", "kimi", "claude", "gpt"]); ap.add_argument("--key-file", default=None)
    ap.add_argument("--base-url", default=None); ap.add_argument("--model", default=None); ap.add_argument("--api", default=None)
    ap.add_argument("--max-tokens", type=int, default=20000); ap.add_argument("--thinking-budget", type=int, default=12000)
    ap.add_argument("--out", default="artifacts/verifier_evidence"); ap.add_argument("--only-missing", action="store_true"); ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    defaults = {"glm": ("https://api.z.ai/api/anthropic", "glm-5.3", "anthropic"), "kimi": ("https://api.moonshot.cn/v1", "kimi-k3", "openai"),
                "claude": ("", "claude-opus-5", "claude-cli"), "gpt": ("", "gpt-5.6-sol", "codex-cli")}
    args.base_url = args.base_url or defaults[args.verifier][0]; args.model = args.model or defaults[args.verifier][1]; args.api = args.api or defaults[args.verifier][2]
    key = pathlib.Path(args.key_file).expanduser().read_text().strip() if args.key_file else ""
    jobs = [(cid, cond) for cid in CLAIMS for cond in ("alone", "valid", "invalid")]
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex: list(ex.map(lambda j: run_one(args, key, *j), jobs))
    print("VERIFIER_EVIDENCE_DONE", args.verifier)

if __name__ == "__main__": main()
# Post-hoc budget extension (2026-09-06 01:20 UTC): the three calls that returned no verdict within budget (GLM C2-alone, Kimi
# C2-alone, Kimi C2-invalid) are repeated once with a 4x larger output budget into artifacts/verifier_evidence_ext/.  Reported separately.
