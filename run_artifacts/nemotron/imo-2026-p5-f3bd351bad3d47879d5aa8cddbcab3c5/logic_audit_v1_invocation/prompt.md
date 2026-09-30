EXECUTE A LINE-BY-LINE LOGIC AUDIT NOW. You are a fresh skeptical referee, not the author and not a summarizer.
Read run_artifacts/nemotron/imo-2026-p5-f3bd351bad3d47879d5aa8cddbcab3c5/statement.md, run_artifacts/nemotron/imo-2026-p5-f3bd351bad3d47879d5aa8cddbcab3c5/candidate_v1.md, run_artifacts/nemotron/imo-2026-p5-f3bd351bad3d47879d5aa8cddbcab3c5/review_v1.json, and run_artifacts/nemotron/imo-2026-p5-f3bd351bad3d47879d5aa8cddbcab3c5/verification_v1.json. Ignore their verdicts as evidence. For every load-bearing paragraph, translate the asserted step into explicit premises and conclusion, then test whether the conclusion follows. Attack monotonicity directions, converses, quantifier changes, existence and nonzero claims, induction bases, limiting arguments, and uses of named theorems. A true final theorem does not excuse one invalid inference. Do not retrieve or use any published solution and do not modify Claude Code configuration files.

You MUST call Write to create run_artifacts/nemotron/imo-2026-p5-f3bd351bad3d47879d5aa8cddbcab3c5/logic_audit_v1.json as JSON with exactly:
- task_id: 'imo-2026-p5'
- verdict: "confirm" or "overturn"
- implication_checks: nonempty list of objects, each with location, premises, conclusion, and assessment
- invalid_inferences: list
- counterexample_search: list
- required_fixes: list
- summary: string
Use "confirm" only if every load-bearing implication checked is valid and both invalid_inferences and required_fixes are empty. Then Read the JSON back. Reply LOGIC_AUDIT_ARTIFACT_COMPLETE only after it exists.
