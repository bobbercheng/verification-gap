You are the inner research loop of a domain-neutral portfolio-transfer system.

Task: imo-2026-p1 — IMO 2026 Problem 1
Domain: mathematical-proof
Read the exact task from run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/statement.md.
Objective: Determine the requested conclusion and give a rigorous, self-contained proof.
Constraints: ["Treat numerical experiments as evidence, never as proof.", "State all assumptions and handle boundary or degenerate cases.", "Derive independently from first principles; do not retrieve published solutions."]

Transferred mechanisms from other tasks (ideas, not authority):
[
  {
    "name": "exact-squared-difference-decomposition",
    "source_tasks": [
      "imo-2026-p5"
    ],
    "summary": "Squaring both inequalities and subtracting gives R = \u00bc[(x-y-B)\u00b2 + (A-B)(2x+2y+A+B)] and L = \u00bc[(x-y-B)\u00b2 - (A-B)(2x+2y+A+B)], combining to the tight bound (1).",
    "transfer_tags": [
      "algebraic-manipulation",
      "analysis",
      "difference-of-squares",
      "functional-equation",
      "inequalities",
      "inequality-squaring"
    ],
    "uses": 1
  },
  {
    "name": "functional-equation-from-equality-case",
    "source_tasks": [
      "imo-2026-p5"
    ],
    "summary": "Setting x = f(y) forces equality in both outer inequalities, yielding f(f(y)) = 2f(y) - y.",
    "transfer_tags": [
      "IMOSL",
      "analysis",
      "equality-case",
      "functional-equation",
      "functional-equations",
      "inequalities"
    ],
    "uses": 1
  },
  {
    "name": "iterate-linearization",
    "source_tasks": [
      "imo-2026-p5"
    ],
    "summary": "From g(x+g(x)) = g(x) we get f\u207f(x) = x + n g(x), which forces g(x) \u2265 0 by positivity.",
    "transfer_tags": [
      "analysis",
      "functional-equation",
      "functional-iteration",
      "induction",
      "inequalities",
      "positivity-constraint"
    ],
    "uses": 1
  }
]

Prior attempts on this same task (reuse evidence; do not repeat exhausted exploration):
[
  {
    "id": "imo-2026-p1-5117ac1b9a334f429ebd87287ff751bc",
    "status": "completed",
    "result_status": "unresolved",
    "run": "[local-path]",
    "operator_audit": null,
    "operator_solution": null
  },
  {
    "id": "imo-2026-p1-f1a9f99660ae43b0a14b581257ce82c6",
    "status": "failed",
    "result_status": "unresolved",
    "run": "[local-path]",
    "operator_audit": null,
    "operator_solution": null
  },
  {
    "id": "imo-2026-p1-5f9a6622e31c4315bf39128c6c9c2439",
    "status": "failed",
    "result_status": "unresolved",
    "run": "[local-path]",
    "operator_audit": null,
    "operator_solution": null
  }
]

Before forming hypotheses, read every non-null operator_audit or operator_solution path above. Operator files are hypotheses/evidence, not authority, but every concrete counterexample in them is mandatory: explicitly reproduce or refute it before reusing a prior conclusion.

Do not converge prematurely, but do not explore indefinitely. Form at least three structurally distinct hypotheses, try to falsify each, and develop the strongest survivor into a self-contained result. Use Bash/Python and create experiments when they can test a claim. Clearly distinguish proof, computation, assumption, and conjecture. Do not modify Claude Code configuration files.

Artifact-first stopping policy: create both required artifacts with status "partial" within your first five tool calls, then continuously improve them. Spend at most 40% of the turn on open-ended exploration and reserve the remainder for synthesis, proof dependency checks, and explicit open issues. A rigorous partial result is valid; ending without artifacts is not.

Write the primary artifact to run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/candidate_v1.md. Write run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/candidate_v1.json as JSON with exactly these fields:
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
All paths must remain under run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d. Do not claim correctness from confidence alone.
