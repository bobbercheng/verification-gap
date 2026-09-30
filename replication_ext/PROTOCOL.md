# Replication of the evaluator-variation measurements on IMO 2026 P1, P4, P5 (written 2026-09-06 03:00 UTC, before any rating was launched)

Question. The paper measures, on P2/P3/P6, how much of the apparent progress in a proof trajectory is evaluator variation:
identical texts receiving different structural-closure labels, same-text repeat disagreement q, cross-evaluator kappa on S, and
whether the per-lineage trajectory conclusions (improved / regressed / first crossing) change with the evaluator. This protocol
repeats those measurements on the three problems the paper does not analyze (P1, P4, P5), with new rubrics and new ratings.
Nothing here decides which score is right; the endpoints are observable without any mathematical judgment.

## Texts (frozen before launch; built by `scripts/replication_ext.py manifests`)
- Public campaign (nine runs): every `write_file` to a file named `current.md` in the per-turn logs of the main session
  (`results/<model>/problem-0N/logs.jsonl`) and of the repair rounds (`scratch/logs-roundK.jsonl`) is one snapshot, plus each
  run's final `current.md`. Sessions under `scratch/killed-*`, `scratch/degenerate-*`, `scratch/cutoff-*`, `scratch/rerun*`
  are excluded, exactly as in the shipped P2/P3/P6 corpus (`manifests --check-p6` re-extracts P6 byte-identically: 19 files,
  28 public records). Excluded on P4: gpt-5.6-sol-max `scratch/killed-402` (one 1.7 kB snapshot); on P5 the two killed sessions
  wrote no `current.md`. Snapshots are written to `<scratchpad>/deedy_ckpts_p{1,4,5}/<model>-<session>-t<turn>-<sha12>.md`.
- Our runs: `candidate_v<N>.md` under `runtime/imo-2026/runs/imo-2026-pN-*` (Nemotron 3 Ultra, lineage ours-nemotron),
  `runtime/imo-2026-glm52-blind/runs/` (GLM-5.2, ours-glm52) and `runtime/imo-2026-codex-gpt56sol-ultra/runs/` (GPT-5.6-Sol,
  ours-gpt56sol-ultra); provisional / schema-repair drafts (`candidate_v1_*.md`, one P4 Nemotron run) are excluded as for P6.
  The non-blind `runtime/imo-2026-glm52/` directory is not part of the corpus (not used for P2/P3/P6 either).
- Manifests: `artifacts/closure_p{1,4,5}_checkpoints.json` (one record per checkpoint; fields id, lineage, model, context, turn,
  path, recorded_mtime_utc for our runs) and `artifacts/closure_distinct_p{1,4,5}.json` (one record per sha256).
  Counts at freeze: P1 38 checkpoints / 30 distinct texts / 12 lineages (8 texts under more than one record);
  P4 33 / 25 / 12 (8 repeated); P5 35 / 27 / 12 (7 repeated, one text under three records). Lineages: the nine public runs
  plus ours-glm52, ours-gpt56sol-ultra, ours-nemotron on every problem.

## Rubrics (`artifacts/closure_rubric_p{1,4,5}.txt`, frozen before launch; choices in `rubric_notes.md`)
Same schema and grading instructions as P2/P3/P6 (grade only what is written; sketches score 1; a false lemma scores 0).
S = number of the two obligation fields (`lower_bound`, `upper_bound`) scored 2. Obligations, anchored to the published
solutions (Evan Chen's notes, 3 September 2026):
- P1: lower_bound = termination for every play AND exactly one integer > 1 remains; upper_bound = invariance of the gcd of the
  p-adic valuations under every move (so M is determined); reduction = per-prime move description; answer = explicit M.
- P4 (routes differ; route-neutral): lower_bound = Mulan wins for theta = 180/n against every play; upper_bound = Shan-Yu avoids
  theta forever for every other theta; reduction = the multiples-of-theta lemma (or an equivalent cut lemma); answer = 180/n.
- P5 (routes differ; route-neutral): lower_bound = sufficiency of f(x) = x + c for all x, y; upper_bound = necessity, i.e. the
  difference f(x) - x is one constant for all x with the fixed-point case handled; reduction = f(f(t)) = 2f(t) - t (AP orbits);
  answer = f(x) = x + c, c >= 0.

## Ratings (all through `scripts/closure_annotate.py --rubric-file <rubric>`; the annotator sees the text only)
(i)  Claude Opus 5, one rating per CHECKPOINT (every record rated independently, like the paper's layer 0):
     `--api claude-cli --model claude-opus-5 --workers 6 --manifest closure_pN_checkpoints.json` -> `artifacts/closure_ext/pN/claude_ckpt/`
(ii) Claude Opus 5, one rating per DISTINCT TEXT, three sequential passes with identical settings:
     `--manifest closure_distinct_pN.json` -> `artifacts/closure_ext/pN/claude_text/rep{1,2,3}/`
(iii) GPT-5.6-Sol, one rating per distinct text: `--api codex-cli --model gpt-5.6-sol --workers 4` -> `artifacts/closure_ext/pN/gpt_text/`
     (Codex CLI, read-only sandbox, web search off, reasoning effort high). GPT-5.6-Sol authored several of the texts
     (public gpt-5.6-sol* lineages and ours-gpt56sol-ultra), so it is a second lab but not an independent one on those texts.
(iv) GLM-5.3, one rating per distinct text, launched LAST and in the background because the provider serves about one call per
     minute: `--key-file the GLM-5.3 key file --model glm-5.3 --max-tokens 30000 --thinking-budget 16000 --workers 3`
     (the settings of the paper's re-rating and repeat passes) -> `artifacts/closure_ext/pN/glm_text/`. Whatever has finished at
     the freeze is used; its coverage is stated. Kimi K3 is not used (paid API).
Order of launch: (i)+(ii) as one chain per problem (P1, P4, P5), (iii) as a parallel chain, then (iv). Provider-default sampling.
Claude Code CLI 2.1.261 (tool-free, no settings, no session persistence), Codex CLI 0.153.4. Unparsed or failed calls are
re-run once with `--only-failed`; the number of such re-runs is reported. No rating is edited by hand.

## Analysis (`scripts/replication_ext.py analyze`, pre-specified; outputs `results.json`, `table_replication.tex`, `gen/replication_macros.tex`)
Per problem:
1. Identical-text control under the per-checkpoint pass (i): among distinct texts that appear under >= 2 records, the number
   whose records received different S (and the number of record pairs that differ). Any difference is evaluator variation with
   no change in the proof. Reported alongside the paper's layer-0 value (P3/P6: 0 of 8 and 0 of 6 repeated texts; P2: 2 of 19).
   [Correction (2026-09-06): the P2 value is 2 of 5 repeated texts (`closure_adjudicated/reliability.json`: `2.repeated_texts` 5,
   `2.repeated_consistent_S` 3); 19 is the pooled denominator over P3/P6/P2 (8 + 6 + 5), so the pooled figure is 2 of 19 (17/19
   consistent). The generated macro text carried the same slip until this date; `analyze` now computes that sentence from
   reliability.json instead of quoting it.]
2. Same-text disagreement q of Claude Opus 5 over the three text passes (ii): every unordered pair among a text's three ratings;
   q = pairs with different S / all pairs; also per-field (lower_bound, upper_bound) and the share of texts with identical S in all
   three passes. Paper reference: q = 0.024 (P3) and 0.032 (P6) for Claude Opus 5 with four ratings per text.
3. Cross-evaluator agreement over distinct texts: Cohen's kappa on S (three classes) and exact agreement for Claude vs GPT,
   Claude vs GLM and GPT vs GLM where present. The Claude text rating used for these comparisons is rep1 (the first pass,
   fixed here in advance); the majority of the three passes is reported alongside. Where GLM is incomplete, kappa is computed on
   the rated texts and the count is stated.
4. Trajectory conclusions per lineage (checkpoints ordered as in closure_matrix.py: main session by turn, then round1, ..., then
   the final file; our runs in manifest order): improved = last S > first S; regressed = some adjacent decrease; crossing =
   0-based index of the first S = 2 checkpoint or 'none'. Computed under each evaluator: claude_ckpt (pass i), claude_rep1/2/3
   and claude_maj3 (text ratings applied to every checkpoint sharing the text), gpt, glm (if complete). Reported: the number of
   lineages whose three conclusions are identical across all evaluators with complete coverage, and the flips.
   [Correction (2026-09-06): the implementation (`order_key` in `scripts/replication_ext.py`, the ordering of `closure_matrix.py`)
   sorts the repair rounds round1, round2, ... BEFORE the main session, then the final file, not main session first as written
   above. No P1/P4/P5 lineage has a repair round (`closure_p{1,4,5}_checkpoints.json` contain no round contexts), so the two orders
   give identical checkpoint sequences and no reported conclusion changes; the code is left as it is and this note records the
   discrepancy between the text and the implementation.]
5. S = 1 checkpoint counts per evaluator (range across evaluators).
6. Public final files: agreement of (S = 2) with (public first-pass grade >= 5) per evaluator, with the final grade alongside.
Freeze: the analysis runs once (i)-(iii) are complete for all three problems; (iv) is folded in only where complete at that time,
otherwise reported as partial coverage. Ratings arriving later are kept in the repository but are not part of the reported
numbers unless a later note in this file says so. No validity layer, adjudication, or human reading is part of this replication.

## Status at freeze (2026-09-06 03:29 UTC)
Claude Opus 5: per-checkpoint pass complete on all 106 checkpoints (P1 38, P4 33, P5 35) and three per-text passes complete on all
82 distinct texts (P1 30, P4 25, P5 27); GPT-5.6-Sol: complete on all 82 distinct texts. GLM-5.3 (launched last, about 3-4 calls per
minute with 3 workers): P1 30 of 30 texts, P4 25 of 25, P5 7 of 27 rated at the freeze (2026-09-06 03:28:27 UTC; the exact text ids are
listed in `artifacts/replication_ext/freeze.json`). No call was unparsed or failed, so no `--only-failed` re-run was needed and no
fallback (no-thinking) rating exists. The GLM chain was left running; GLM ratings written after the freeze stay in
`artifacts/closure_ext/p5/glm_text/` but are EXCLUDED from every reported number: `scripts/replication_ext.py analyze` reads
`freeze.json` and ignores GLM annotations outside the frozen list (`--freeze-now` would move the freeze and is not to be used for
the reported numbers). Consequences for the analysis: the Claude-vs-GLM and GPT-vs-GLM kappas on P5 are computed on 7 texts; the
"identical under all six evaluators" count covers the 25 lineages GLM rated fully (12 on P1, 12 on P4, 1 on P5); the primary
identity count (evaluators with complete coverage, the five Claude/GPT evaluators required) covers all 36 lineages. Outputs frozen:
`artifacts/replication_ext/results.json`, `table_replication.tex`, `gen/replication_macros.tex`.

## Freeze update (2026-09-06T03:38:40Z)
GLM-5.3 completed its P5 pass at 03:37:28 UTC (82/82 texts, no unparsed calls). The freeze was moved to include it so that all six
evaluators are complete on every lineage; the earlier freeze (03:28:27 UTC, GLM 30/25/7) is retained in git history (commit d923a35).

## Inputs note (2026-09-06)
The public first-pass grade table and the per-problem grade receipts that `analyze` reads (step 6 and the P3/P6 reference rows) are
released copies under `replication_ext/public_grades/` (`problem-0{1,3,4,5,6}.json`, `first_pass_grades.json` = the README table as
model -> problem -> grade, and `provenance.json`: source repository https://github.com/deedy/imo-2026, commit
dbe872307883296c5f06bf8bcb90e6bfd0879364, capture time, sha256 of every file), written by `scripts/replication_ext.py capture-grades`.
Until this date `analyze` read them from a local checkout of that repository, so the analysis could not be re-run from the
supplementary bundle (found by the acceptance review of v5); `analyze --root <repository or bundle>` now runs offline from the released
files alone (the LaTeX macro file is written only where a `gen/` directory exists). No reported number changes.
