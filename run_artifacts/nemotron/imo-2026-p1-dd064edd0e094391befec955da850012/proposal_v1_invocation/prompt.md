You are the inner research loop of a domain-neutral portfolio-transfer system.

Task: imo-2026-p1 — IMO 2026 Problem 1
Domain: mathematical-proof
Read the exact task from run_artifacts/nemotron/imo-2026-p1-dd064edd0e094391befec955da850012/statement.md.
Objective: Determine the requested conclusion and give a rigorous, self-contained proof.
Constraints: ["Treat numerical experiments as evidence, never as proof.", "State all assumptions and handle boundary or degenerate cases.", "Derive independently from first principles; do not retrieve published solutions."]

Transferred mechanisms from other tasks (ideas, not authority):
[
  {
    "name": "endgame-determination",
    "source_tasks": [
      "imo-2026-p1"
    ],
    "summary": "At termination with exactly one integer M > 1, its p-adic valuation equals the invariant gcd of initial exponents, giving M = \u220f p^{gcd_i v_p(a_i)} uniquely determined by the initial multiset.",
    "transfer_tags": [
      "IMO",
      "endgame-analysis",
      "invariants",
      "number-theory",
      "prime-factorization",
      "termination",
      "uniqueness-proof"
    ],
    "uses": 1
  },
  {
    "name": "lexicographic-descent-termination",
    "source_tasks": [
      "imo-2026-p1"
    ],
    "summary": "A well-founded measure (K, S) = (count of integers > 1, sum of prime factor counts) strictly decreases lexicographically at each move, forcing termination with exactly one integer > 1.",
    "transfer_tags": [
      "IMO",
      "combinatorial-process",
      "invariants",
      "lexicographic-order",
      "number-theory",
      "termination",
      "termination-argument",
      "well-foundedness"
    ],
    "uses": 1
  },
  {
    "name": "prime-exponent-gcd-invariant",
    "source_tasks": [
      "imo-2026-p1"
    ],
    "summary": "For each prime p, the gcd of the multiset of p-adic valuations is preserved by the transformation (a,b) \u2192 (min(a,b), |a-b|), which is exactly one step of the Euclidean algorithm on exponents.",
    "transfer_tags": [
      "IMO",
      "euclidean-algorithm",
      "gcd-invariant",
      "invariant",
      "invariants",
      "number-theory",
      "p-adic-valuation",
      "termination"
    ],
    "uses": 1
  }
]

Prior attempts on this same task (reuse evidence; do not repeat exhausted exploration):
[
  {
    "id": "imo-2026-p1-5f9a6622e31c4315bf39128c6c9c2439",
    "status": "failed",
    "result_status": "unresolved",
    "run": "[local-path]",
    "candidate_artifacts": [
      "checkpoint_inputs_ext/ae440d9edfbabe407aaab8871be17d24d4941aa3b6337bac8d2c036059b662ce.md"
    ],
    "review_artifact": "[local-path]",
    "logic_audit": null,
    "operator_audit": null,
    "operator_solution": null
  },
  {
    "id": "imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d",
    "status": "completed",
    "result_status": "provisionally_resolved",
    "run": "run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d",
    "candidate_artifacts": [
      "run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/candidate_v1.md"
    ],
    "review_artifact": "run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/review_v1.json",
    "logic_audit": "run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/logic_audit_v1.json",
    "operator_audit": null,
    "operator_solution": null
  },
  {
    "id": "imo-2026-p1-a9be7bf7970c4b439107f369a71e54bb",
    "status": "failed",
    "result_status": "unresolved",
    "run": "[local-path]",
    "candidate_artifacts": [
      "checkpoint_inputs_ext/de44a94b0ce22126c5e5d8068a9604c3d5436089aa890d09bed64478d993a262.md",
      "checkpoint_inputs_ext/507d8352552b9e77c8ad326adc962dc88460d8270ea7c69e2671882c7c5385ed.md"
    ],
    "review_artifact": "[local-path]",
    "logic_audit": null,
    "operator_audit": null,
    "operator_solution": null
  }
]

Before forming hypotheses, read every candidate_artifacts entry and every non-null review_artifact, logic_audit, operator_audit, or operator_solution path above. These files are hypotheses/evidence, not authority, but every concrete counterexample in them is mandatory: explicitly reproduce or refute it before reusing a prior conclusion.

Do not converge prematurely, but do not explore indefinitely. Form at least three structurally distinct hypotheses, try to falsify each, and develop the strongest survivor into a self-contained result. Use Bash/Python and create experiments when they can test a claim. Clearly distinguish proof, computation, assumption, and conjecture. Do not modify Claude Code configuration files.

Artifact-first stopping policy: create both required artifacts with status "partial" within your first five tool calls, then continuously improve them. Spend at most 40% of the turn on open-ended exploration and reserve the remainder for synthesis, proof dependency checks, and explicit open issues. A rigorous partial result is valid; ending without artifacts is not.

Write the primary artifact to run_artifacts/nemotron/imo-2026-p1-dd064edd0e094391befec955da850012/candidate_v1.md. Write run_artifacts/nemotron/imo-2026-p1-dd064edd0e094391befec955da850012/candidate_v1.json as JSON with exactly these fields:
- task_id: 'imo-2026-p1'
- status: one of "complete", "partial", "blocked"
- answer: concise claimed conclusion
- claims: list of key claims
- assumptions: list
- mechanisms: list of objects with name, summary, transfer_tags (list)
- falsification_attempts: list of objects with hypothesis, attack, outcome
- evidence: list of paths or internally checkable evidence descriptions
- confidence: number from 0 to 1
- open_issues: list
All paths must remain under run_artifacts/nemotron/imo-2026-p1-dd064edd0e094391befec955da850012. Do not claim correctness from confidence alone.
