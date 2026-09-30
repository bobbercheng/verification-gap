You are the inner research loop of a domain-neutral portfolio-transfer system.

Task: imo-2026-p5 — IMO 2026 Problem 5
Domain: mathematical-proof
Read the exact task from run_artifacts/nemotron/imo-2026-p5-f3bd351bad3d47879d5aa8cddbcab3c5/statement.md.
Objective: Determine every function satisfying the inequalities and prove the classification.
Constraints: ["Treat numerical experiments as evidence, never as proof.", "State all assumptions and handle boundary or degenerate cases.", "Derive independently from first principles; do not retrieve published solutions."]

Transferred mechanisms from other tasks (ideas, not authority):
[]

Prior attempts on this same task (reuse evidence; do not repeat exhausted exploration):
[
  {
    "id": "imo-2026-p5-aafea892f1d043e78b358eee8edc6458",
    "status": "failed",
    "result_status": "unresolved",
    "run": "[local-path]",
    "operator_audit": null,
    "operator_solution": null
  },
  {
    "id": "imo-2026-p5-47d7317c83b844959978ecc0bef8d0e7",
    "status": "failed",
    "result_status": "unresolved",
    "run": "[local-path]",
    "operator_audit": "[local-path]",
    "operator_solution": null
  },
  {
    "id": "imo-2026-p5-114f4fec682d42e499f804de2587b733",
    "status": "completed",
    "result_status": "provisionally_resolved",
    "run": "[local-path]",
    "operator_audit": "[local-path]",
    "operator_solution": "[local-path]"
  }
]

Do not converge prematurely, but do not explore indefinitely. Form at least three structurally distinct hypotheses, try to falsify each, and develop the strongest survivor into a self-contained result. Use Bash/Python and create experiments when they can test a claim. Clearly distinguish proof, computation, assumption, and conjecture. Do not modify Claude Code configuration files.

Artifact-first stopping policy: create both required artifacts with status "partial" within your first five tool calls, then continuously improve them. Spend at most 40% of the turn on open-ended exploration and reserve the remainder for synthesis, proof dependency checks, and explicit open issues. A rigorous partial result is valid; ending without artifacts is not.

Write the primary artifact to run_artifacts/nemotron/imo-2026-p5-f3bd351bad3d47879d5aa8cddbcab3c5/candidate_v1.md. Write run_artifacts/nemotron/imo-2026-p5-f3bd351bad3d47879d5aa8cddbcab3c5/candidate_v1.json as JSON with exactly these fields:
- task_id: 'imo-2026-p5'
- status: one of "complete", "partial", "blocked"
- answer: concise claimed conclusion
- claims: list of key claims
- assumptions: list
- mechanisms: list of objects with name, summary, transfer_tags (list)
- falsification_attempts: list of objects with hypothesis, attack, outcome
- evidence: list of paths or internally checkable evidence descriptions
- confidence: number from 0 to 1
- open_issues: list
All paths must remain under run_artifacts/nemotron/imo-2026-p5-f3bd351bad3d47879d5aa8cddbcab3c5. Do not claim correctness from confidence alone.
