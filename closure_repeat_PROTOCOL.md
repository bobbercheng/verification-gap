# Controlled repeat-rating experiment (written 2026-09-06 00:55 UTC, before launch)

Question: how often would the structural-closure annotator, applied twice to the SAME text under the SAME rubric, model and
settings, produce different scores, i.e. an apparent crossing or regression with no change in the proof?
Design: every distinct P3 text (48) and P6 text (36) is rated three more times by GLM-5.3 with exactly the settings of the
layer-1 re-rating (thinking enabled, budget 16000, max_tokens 30000, per-problem rubric, provider-default sampling), in three
sequential passes rep1, rep2, rep3 (artifacts/closure_repeat/p{3,6}/rep{1,2,3}). P2 is excluded because its rubric applies to
2 of 12 lineages (route policy).
Analysis (scripts/closure_repeat_analysis.py, written after launch but before results were read): per text, the multiset of S
over {re-rating, rep1, rep2, rep3}; repeatability = share of texts with identical S in all four; pairwise disagreement rate q;
per-field disagreement; and the trajectory conclusions (S=1 checkpoints, crossings, regressions per problem) recomputed with each
repeat as the sole evaluator, via closure_matrix.py layers rep1/rep2/rep3. The paper reports q and the range of conclusions.
Endpoint: same-text score change is observable without any mathematical judgment; which score is correct is not decided here.

## Additional evaluators (added 2026-09-06 01:30 UTC, before their launch)
Claude Opus 5 (Claude Code CLI, tool-free, no settings) rates all 156 distinct texts under the same per-problem rubrics
(artifacts/closure_claude/), then repeats P3/P6 three times under identical settings (artifacts/closure_repeat_claude/), then
grades all texts with the ordinary coordinator-style rubric (artifacts/baseline_claude/). GPT-5.6-Sol (Codex CLI, read-only
sandbox, web search off, reasoning effort high) rates the P3/P6 texts (artifacts/closure_gpt/); it authored several of them, so
it is reported as a fourth evaluator, not as an independent one. Both CLIs are subscription services; provider-default sampling.
The same four verifiers are used in the decisive-evidence test (artifacts/verifier_evidence/{glm,kimi,claude,gpt}/).

## Status at freeze (2026-09-06 02:10 UTC)
GLM-5.3 repeats: rep1 complete for P3 (48/48) and partial for P6; rep2/rep3 not started because the provider served about one
call per minute all night. Claude Opus 5: all three repeats complete for P3 and P6 (252 ratings). The analysis uses every rating
present at freeze; coverage per pool is stated in artifacts/conclusion_sensitivity/results.json. Ratings arriving after the
freeze are kept in the repository but are not part of the submitted numbers unless a later commit says so.
