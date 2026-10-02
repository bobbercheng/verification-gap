# Supplementary material: The Verification Gap: Auditing Proof Progress and Repair on IMO 2026

Bobber Cheng (Vexorium), bobber.cheng@gmail.com. Camera-ready supplement of the paper accepted at MATH-AI 2026, the 6th
Workshop on Mathematical Reasoning and AI at NeurIPS 2026. Public release: https://github.com/bobbercheng/verification-gap.

- `paper.pdf`: the camera-ready paper, the same file as uploaded to OpenReview.
- `corrections.pdf`: every corrected sentence since the reviewed version as of 29 September 2026, one row per identifier
  (the paper's Appendix Q summarizes them); the text corrections of 2 October 2026 carry no identifier and are listed in
  `CHANGES.md`.
- `paper_source/`: the LaTeX source of the camera-ready paper as built on 2 October 2026 (`main.tex`, `appendix.tex`, `main.bbl`,
  `neurips_2026.sty`, the generated macro and table files under `gen/` and `artifacts/`); `pdflatex main` three times
  reproduces `paper.pdf`'s text (the claim guard's macro registry `gen/CR_MACROS.md` is not included).
- `NOTICE.md`: what here is the author's (CC BY 4.0) and what is third-party material, redistributed for reproduction only
  (`THIRD_PARTY.json` lists every third-party text file).
- `CHANGES.md`: every change from the supplement the reviewers saw.
- Dated addenda (`*/ADDENDUM_2026-09-29.md`): corrections to records that stay exactly as the reviewers saw them.
- `post_submission/`: runs the author made after submission (7 September 2026) on the same 32 planted texts, outside the paper's
  protocol (Appendix S).

## Contents

This archive contains eight published proofs from the author's own campaigns with their reviews and verifications, three
original Nemotron run candidates with reviews/verifications and later logic audits, GLM-5.2's five gate-passing candidates
with their reviews/verifications, reviewer-swap results (GLM-5.3 and Kimi K3 on the eight published proofs; Kimi K3 on the
GLM-5.2 candidates), every structural-closure input for Problems 2, 3 and 6 with all of its ratings and label layers
(`checkpoint_inputs/manifest.json` gives the counts per group), an ordinary-grade baseline on the same texts, the paired
critique/no-critique pilot with its grades and gate reviews, the Problem 1/4/5 replication of the evaluator-variation
measurements together with released copies of the public grade receipts it reads, the witness-discovery experiment and the
reference adjudication of its confirmed errors, the planted-defect study with every gate call, and the post-submission runs
on the planted texts.

## How to verify

From this directory, with Python 3 and its standard library only (tested with Python 3.13):

    python3 verify_bundle.py verify --out .

It is offline (no API calls, no network) and exits non-zero on the first failure. It checks: every file against
`MANIFEST.json` (SHA-256, size and complete coverage); every rating, grade and pilot grade against the bundled text and
rubric it names; the reviewer and gate inputs, prompts and scores; the label adjudication, recomputed by re-running
`scripts/closure_adjudicate.py` on a scratch copy; the closure matrix, recomputed by `scripts/closure_matrix.py --root .
--check`; the P1/P4/P5 replication and the public grade receipts it reads; the witness-discovery analysis, regenerated
offline and compared with the shipped `results.json` and tables; the post-submission records against
`post_submission/records.json` and their tallies against a recomputation; `THIRD_PARTY.json` and the counts `NOTICE.md`
states; and that no local path or credential remains. Its last line begins "Verified".

Each analysis can also be re-run on its own, offline, from this directory:

    python3 scripts/analyze_closure.py --root . --check        # the Problem-3 census
    python3 scripts/closure_matrix.py --root . --check         # progress matrix, agreement, budget medians
    python3 scripts/replication_ext.py analyze --root .        # replication_ext/results.json and table
    python3 scripts/conclusion_sensitivity.py --root .         # conclusion_sensitivity/
    python3 scripts/witness_discovery.py analyze --root . --freeze
    python3 scripts/reference_adjudication.py analyze --root . --freeze
    python3 scripts/planted_defects.py analyze --root . --freeze
    python3 scripts/inspection_cost.py --root .
    python3 post_submission/summarize.py --root . --check
    python3 scripts/witness_checks.py --all                   # executable checks of the finite witnesses (sympy, z3-solver)
    (cd planted_defects && python3 planted_checks.py --all)    # the 16 executable checks of the planted edits (sympy)

The analyze commands rewrite their outputs in place with a new generation time (the other fields equal the shipped
files), so run `verify_bundle.py` before them or on a fresh copy. The exception is `inspection_cost.py`, which writes its
outputs to a new directory, `artifacts/inspection_cost/`, and leaves the shipped `inspection_cost/` untouched. `verify_bundle.py` is a copy of the script that built this
archive; its `build` and `capture` modes need the author's working tree and source snapshot, which are not part of this
release (`provenance/source_snapshot.json` records the snapshot's digests). Re-running the model calls needs the model CLIs
or APIs, which are not part of this archive either.

## Planted defects

- `planted_defects/` holds the planted-defect study: 8 base proofs accepted at selection and 24 single-edit mutants of
  them (a fatal, a gap and a harmless edit per base; `texts/<base>/{original,F,G,H}.md`), their specification and diffs
  (`plantings.json`, `parts/`, `make_mutants.py`, `manifest.json`), the 16 executable checks (`parts/checks_*.py`,
  `planted_checks.py`, `checks.json`), the protocol (`PROTOCOL_PLANTINGS.md`) and the log (`DEVIATIONS.md`), every gate
  call (`runs/grade/`, `runs/witness/`, `runs/closure/`, the reference checks `runs/refadj/`, and the post-hoc re-query of
  the grade gate `runs/grade_rep2/`; per call `request.json` with the exact system prompt and the text's digest,
  `response.json`, `parsed.json`), and the analysis (`results.json`, `RESULTS.md`, `table_*.tex`). The specification,
  the edits, their dependency arguments, intended labels and checks were written by AI agents to the author's design; the
  witness and closure prompts carry the problem's marking scheme, which the grade prompt forbids; five intended labels are
  disputed; the protocol is prespecified and self-timestamped: all in `planted_defects/ADDENDUM_2026-09-29.md`.
- `inspection_cost/` holds the quote-localization measurement read from the same stored responses.
- `post_submission/` holds five later runs on the same 32 texts (a re-run of the witness gate, a witness audit with the
  marking scheme removed, two more runs of the grade gate and a grade prompt with three added sentences of the audit's instructions), each record a
  byte-for-byte copy listed in `records.json`, with `summary.json` and the script that recomputes it; see
  `post_submission/README.md`.

## Terms used in the dated records

- "Review", "reviewer", "the vN review" and "post-vN review" in the logs and protocols mean internal pre-submission reviews
  run by language models (OpenAI Codex in its desktop application with the gpt-6-astra model; a few reviewer-role
  subagents in Claude Code). No human reviewer took part, and none of them is a review by the workshop's referees; their
  reports are not released.
- "Author" in the records of non-model judgments (`reference_adjudication/LEDGER.md`, `closure_adjudicated/adjudication_notes.md`,
  `witness_discovery/recovery.json`, `pilot_critique/author_read.md`, `pilot_critique_ext/author_read.md`): each was
  produced by a model under the author's direction and reviewed by the author (the addendum next to each).
- "Pre-registered" in the planted-defect records means prespecified and self-timestamped; nothing here was registered with
  a third party.

## Structural closure: inputs, ratings, label layers

- `checkpoint_inputs/manifest.json` maps all layer-0 annotations to bundled inputs.
  Paths are relative to this archive root. `original_sha256`/`original_bytes`
  describe the original input; `bundled_sha256`/`bundled_bytes` describe its released
  copy. Annotations' `sha256` and `bytes` describe their relative `path`, and
  `input_anonymized` flags a difference (local paths removed from the copy). `review_path` points to the gate review
  of the author's own candidate checkpoints (`checkpoint_reviews/`).
- `closure/`, `closure_deedy/`, `closure_p6/`, `closure_p2/` hold the layer-0 annotations
  (GLM-5.3, every checkpoint) and raw annotator responses; `<group>/checkpoints_manifest.json`
  records lineage, context/session, turn and order. `closure_glm_rerun/` and `closure_kimi/`
  hold the layer-1 re-ratings of each distinct text (`closure_distinct_p*.json`) by GLM-5.3
  (thinking, larger output cap) and by Kimi K3; their `path` fields point to the same
  `checkpoint_inputs/` texts. Every call is recorded per annotation in `attempts`: a GLM-5.3
  record whose first (thinking) attempt returned no parsable grade carries a second,
  no-thinking fallback attempt (`attempt: 1`), so fallbacks are recorded per annotation and
  counted in `reliability.json` (`glm_rerun_fallbacks`); a record whose attempts all failed
  carries `grades: null` and `S: null` and is not a rating.
- `closure_adjudicated/labels.json` has one record per distinct text (`sha256`, the
  `record_ids` of the layer-0 checkpoints carrying it, every raw vote) with five label
  layers in `fields` and `S`: `raw` is the layer-0 majority; `glm` the GLM-5.3 re-rating
  (layer-0 majority where the re-rating is missing); `kimi` the Kimi K3 rating (missing
  where absent); `written` the conservative aggregate, in which a mechanism counts 2 only
  if both re-raters score it 2 and otherwise takes the lower score, and which is `unknown`
  (null) when either rater is missing, never filled from another layer; `valid` is `written`
  with the entries of `validity_overrides.json` applied. `status` is one of agree,
  conservative, validity_override, unknown. `validity_overrides.json` states the validity
  criterion (a mechanism scored 2 is set to 0 when an independent record shows the written
  argument is invalid: an explicit counterexample to a lemma it relies on, or a fatal invalid
  step recorded by the public verifier or our gate, applied to every retained text carrying
  the same defect) and each override with its evidence. `p2_routes.json` is the Problem-2
  route policy: the route of each lineage classified from its final text, and whether the
  synthetic-route rubric applies; lineages with `applicable: false` are displayed but excluded
  from every agreement and transition count. `reliability.json` gives Cohen's kappa and field
  agreement between the two re-raters, repeated-text consistency of layer 0, fallback counts,
  and lists the unknown, overridden and changed-vs-raw texts; `adjudication_notes.md` is the
  written record of the adjudication (what each layer settles, every override, and the texts
  whose label changed; its comparisons were produced by a model under the author's direction and reviewed by the author,
  `closure_adjudicated/ADDENDUM_2026-09-29.md`). `scripts/closure_adjudicate.py --root .` recomputes labels and reliability.
- `closure_matrix/` holds the generated matrix (`matrix.json`; `layer` names the label layer
  used, valid), `regularities.json` (stage-matched and first-pass agreement, transitions,
  budget medians, and `sensitivity_by_layer`), `sensitivity.json` (every headline count
  recomputed under each of the five layers; `scripts/closure_matrix.py --root . --layer <layer>
  --out <dir>` regenerates the primary outputs under another layer), the LaTeX tables and
  `public_grades.json`, the public first-pass and final grades used.
  `trajectory_stats_public.json` holds per-session budgets of the public logs.
- `baseline_glm/` and `baseline_kimi/` hold an ordinary 0-7 grade of each distinct text by
  GLM-5.3 and Kimi K3 under `baseline_rubric_p<n>.txt` (at the archive root; no closure
  fields, `S: null`), used to test what S adds beyond a grade. Their `path` fields point to
  the same `checkpoint_inputs/` texts.

## Paired critique pilot

- `pilot_critique/` holds the primary 60k-token runs: `PREREG.md` (the protocol text as
  issued with the launch command, its dated post-hoc extension note, and a dated correction
  of the header timestamps against the run records, so the pilot is protocol-first and
  exploratory, not registered), one directory per run
  (`meta.json` with case, condition, seed digest, finish reason and output digest;
  `request_redacted.json` with the draft replaced by its hash; `output.md`; the raw
  `response.json`), blind grades of every delivered output by both annotators under the
  paper's closure rubric (`grades_glm/`, `grades_kimi/`; `annot_manifest_p*.json` lists the
  blind ids, a hash prefix of the output), the tool-free GLM-5.3 gate reviews
  (`gate_glm53/`, reviewer-swap layout with per-request prompt hashes; `gate_proofs.json`
  lists what was reviewed), the read of every output rated S=2 or gate-pass (`author_read.md`; produced by a model under
  the author's direction and reviewed by the author, `pilot_critique/ADDENDUM_2026-09-29.md`) and `summary.json` (per run:
  both annotators' S, gate verdict and scores, and the generated table). `pilot_critique_ext/` holds the post-hoc
  200k-token repeats of the S<2 runs in the same layout; its `gate_glm53/` has no `summary.json`, which was never produced
  (the per-run gate reviews are released and checked; `pilot_critique_ext/ADDENDUM_2026-09-29.md`).

## Everything else

- `run_artifacts/manifest.json` maps all nine rows of the paper's accepted-proof
  table to full digests. The Nemotron candidate/review/verification/audit files
  retain original bytes. Edited published Nemotron solutions are stored separately.
- `p3_repairs/` contains both corrected P3 candidates, blind-review receipts,
  review manifests and prompt copies. Agreement-check sources are in `closure_analysis/`.
- `prompts/` contains the exact applied closure system prompts (one per problem) and the
  task-specific reviewer-swap and pilot-gate system prompts. Historical campaign and repair
  prompts retain their wording with local paths replaced; these prompt copies are not
  claimed to be byte-identical to their originals.
- `historical_responses/` retains older response-attempt files unreferenced by
  active annotations in any annotation group. Its manifest excludes them from reported grades.
- `provenance/source_snapshot.json` records original and released digests for
  captured source evidence. Original external and repository evidence is untouched.
- `MANIFEST.json` hashes every other file of this archive as released (after local paths were removed).

The separate PDF report and builder are omitted; complete Markdown proofs are
included. Full provider traces and executable research workspaces are outside this
release, as are the IMO 2025 campaign of the paper's Appendix A, the internal model-run review reports, the record of the
29 September 2026 model check of the bases and ledger against Chen's notes, and the session logs behind the paper's
provenance statements. Model reviews are evidence, not official IMO grading.

- `closure_claude/`, `closure_gpt/` (Claude Opus 5 and GPT-5.6-Sol ratings of the distinct texts; GPT on P3/P6 only and it
  authored some of them), `closure_repeat/` and `closure_repeat_claude/` (same-model repeat ratings under identical settings,
  protocol in `closure_repeat_PROTOCOL.md`), `baseline_claude/` (Claude ordinary grades). Label layers in `closure_adjudicated/`
  now include claude, gpt, majority3 (two of three labs) and the repeat layers.
- `verifier_evidence/` and `verifier_evidence_ext/`: four checkable claims x {alone, valid counterexample, invalid counterexample}
  shown to four tool-free verifiers; request, response and parsed verdict per call (the extension repeats three no-verdict calls
  with a larger budget).
- `conclusion_sensitivity/`: results.json and tables of the conclusion-survival study (replay under two same-model pools,
  identical-text controls, checkpoint-count test, remedies at matched budget, sources of instability); regenerate offline
  with `python3 scripts/conclusion_sensitivity.py --root .`.

## Replication on Problems 1, 4 and 5

- `checkpoint_inputs_ext/` holds one copy per distinct text of the P1/P4/P5 trajectories
  (`<sha256>.md`); its `manifest.json` has one record per replication rating, with the same
  fields as `checkpoint_inputs/manifest.json` and `group` naming the rating directory (for
  example `p4/claude_text/rep2`). These texts are separate from the P2/P3/P6 corpus and take no
  part in the adjudication or the closure matrix. `closure_ext/p<N>/claude_ckpt/` rates every
  checkpoint of `closure_p<N>_checkpoints.json` (Claude Opus 5, one rating per checkpoint);
  `claude_text/rep1..3/`, `gpt_text/` and `glm_text/` rate each distinct text of
  `closure_distinct_p<N>.json` (three Claude Opus 5 passes, GPT-5.6-Sol, GLM-5.3), all under
  `prompts/closure_system_p<N>.txt`, a byte-identical copy of `closure_rubric_p<N>.txt`. Every
  `path` in these ratings, summaries and manifests points into `checkpoint_inputs_ext/`. A rating
  pass that had not finished when the bundle was built is simply shorter; the verifier checks what
  is present and prints the per-directory counts. `replication_ext/` holds the protocol written
  before any rating was launched (`PROTOCOL.md`, with dated correction notes), the rubric rationale
  (`rubric_notes.md`), the corpus summary (`manifest_summary.json`), the GLM freeze (`freeze.json`),
  `results.json` and `table_replication.tex`. `replication_ext/public_grades/` holds byte-for-byte
  copies of the public campaign's grade receipts that the analysis reads (`problem-0{1,3,4,5,6}.json`:
  final grade, justification and named defects per run; `first_pass_grades.json`: the campaign
  README's first-pass table as model -> problem -> grade) with `provenance.json` (source repository
  and commit, capture time, sha256 of each file; the verifier re-checks these digests).
  `python3 scripts/replication_ext.py analyze --root .` regenerates `results.json` and
  `table_replication.tex` from these bundled files alone (the LaTeX macro file is written only in
  the paper repository, where a `gen/` directory exists).

## Witness discovery

- `witness_discovery/` holds the witness-discovery experiment on twenty disputed and control texts of
  the closure corpora: the protocol (`PROTOCOL.md`; prespecified and self-timestamped, not registered: its first
  commit postdates the first calls) and the log of what happened afterwards
  (`DEVIATIONS.md`), the case list with digests (`cases.json`; each `path` points at the released
  copy of the text in `checkpoint_inputs/` or `checkpoint_inputs_ext/`), one proposer call per text
  and model under `propose/<proposer>/<case>/` (Claude Opus 5 through its CLI without tools;
  GPT-5.6-Sol through the Codex CLI in a read-only sandbox with web search disabled; `request.json`
  with the exact system prompt and its digest, `response.json`, `parsed.json` with the obligation
  verdicts, witnesses and quote anchoring), the ordinary-grader arm under `baseline/<grader>/<case>/`
  (same models and transports, one call per text), the checks of every lower/upper witness and of
  each grader's two most severe errors under `check/<checker>/<job>/` (the objection as sent is in
  `request.json`; its `Claimed status` field names the procedure for grader objections, so checkers
  were not blind to the procedure), the post-hoc target-match and conclusion-change judgments (`recovery.json`; produced
  by a model under the author's direction and reviewed by the author), and the analysis (`results.json` with the classes, the severity layer
  `fatal_layer`, and the cost accounting `cost`; `RESULTS.md`; `table_witness.tex`;
  `table_witness_summary.tex`). `certificates.json`, where present, records the executable checks
  of the finite witnesses (`scripts/witness_checks.py`). The proposer prompt carries the problem's marking scheme and
  the grader prompt forbids one (`witness_discovery/ADDENDUM_2026-09-29.md`). The verifier prints the counts and
  regenerates the analysis offline with
  `python3 scripts/witness_discovery.py analyze --root .` and requires equality. Re-running the
  proposer, grader or checker calls needs the model CLIs or API and the annotation module, which are
  not part of this bundle.

## Reference adjudication

- `reference_adjudication/` holds the adjudication of the confirmed local errors of the witness experiment against a
  published reference: the reference ledger (`LEDGER.md`, the version every judgment used, and `LEDGER_v2.md`; produced by
  a model under the author's direction and reviewed by the author), `PROTOCOL.md`, `DEVIATIONS.md`, the checker and rater
  calls (`check/`, `rate/`), `results.json`, `RESULTS.md` and the tables. `ADDENDUM_2026-09-29.md` corrects two ledger
  entries (P6 L6.2 in `LEDGER_v2.md`, P1 L1.1) and the ledger's attribution. `python3 scripts/reference_adjudication.py
  analyze --root . --freeze` recomputes the analysis offline.

## Provenance

Local filesystem paths are replaced by `[local-path]` (or `[local-path]/<file name>` where the file name identifies the
text) in every released copy; `provenance/source_snapshot.json` and the manifests record original and released digests,
and a copy differs from its original only by that replacement. The supplement the reviewers saw also replaced the author's
name, which turned five key-file defaults in the scripts into `~/.config/the authors/...`; this release ships the scripts
with their original defaults. Model reviews and gates are evidence, not official IMO grading.
