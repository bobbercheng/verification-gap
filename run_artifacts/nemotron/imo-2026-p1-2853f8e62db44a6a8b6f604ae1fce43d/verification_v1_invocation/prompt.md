EXECUTE A SECOND-ORDER AUDIT NOW. You are not the author and your job is to try to overturn a prior pass, not summarize it.
Read run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/statement.md, run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/candidate_v1.md, and run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/review_v1.json. Reconstruct the proof or technical dependency graph. Identify the single weakest inference, reverse every inequality implication, test existence/nonzero conclusions, check circular dependencies, and seek a concrete counterexample. Agreement with the first reviewer is not evidence.

You MUST call Write to create run_artifacts/nemotron/imo-2026-p1-2853f8e62db44a6a8b6f604ae1fce43d/verification_v1.json as JSON with exactly:
- task_id: 'imo-2026-p1'
- verdict: "confirm" or "overturn"
- weakest_inference: nonempty string
- counterexample_search: list
- dependency_gaps: list
- required_fixes: list
- summary: string
Use "confirm" only if dependency_gaps and required_fixes are empty after the attack. Then Read the JSON back. Reply VERIFICATION_ARTIFACT_COMPLETE only after it exists. Do not ask a question or return the JSON only in chat.
