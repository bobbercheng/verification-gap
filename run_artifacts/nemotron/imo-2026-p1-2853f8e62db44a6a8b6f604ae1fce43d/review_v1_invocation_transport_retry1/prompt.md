EXECUTE THIS REVIEW NOW. Do not ask what the user wants and do not stop after reading files.
You are a fresh adversarial reviewer, not the author.

Read the task at run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/statement.md, the proposed result at run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/candidate_v1.md, and its manifest at run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/candidate_v1.json. Re-derive the critical steps independently. Search for counterexamples, hidden quantifier changes, unjustified limit/continuity claims, degenerate cases, circular arguments, and gaps between experiments and proof. Do not modify Claude Code configuration files.

You MUST call the Write tool to create run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/review_v1.json as JSON with exactly these fields:
- task_id: 'imo-2026-p1'
- verdict: one of "pass", "revise", "reject"
- scores: object with correctness, completeness, rigor, self_contained; each integer 0..4
- fatal_issues: list
- required_fixes: list
- verified_claims: list
- unverified_claims: list
- summary: concise assessment
- transfer_assessment: list of reusable or misleading mechanisms

Use "pass" only when there is no known fatal gap and every score is at least 3. This is still a model review, not an official proof certificate.
Before ending, use Read to confirm that run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/review_v1.json exists and contains valid JSON. Your final response must be REVIEW_ARTIFACT_COMPLETE only. Do not return the JSON merely as chat text.
