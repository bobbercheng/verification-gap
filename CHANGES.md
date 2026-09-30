# Changes from the supplement the reviewers saw

The reviewers saw `supplementary.zip` of 2026-09-07 (18,059,371 bytes, 7,898 files, SHA-256
c96fab12d47524f4921ef4459af1380a4e0174da1ab7947116c72a60063019c3), uploaded with the reviewed version of the paper. This is the
camera-ready supplement (2026-09-29). It keeps every file of the reviewed archive; no stored request, response, parse, rating,
label, check, result, table, protocol or log was edited, re-run or removed. Corrections to those records are dated addenda next
to them. The release script checks that every file added, changed or removed since the reviewed archive is named here.

## Added

- `paper.pdf`: the camera-ready paper, the same file as uploaded to OpenReview.
- `corrections.pdf`: the full list of corrections since the reviewed version, one row per corrected sentence.
- `NOTICE.md`: licensing and attribution. The texts from the public IMO 2026 campaign (the repository and commit cited in the
  paper) are redistributed for reproduction only, with no licence granted; the IMO problem statements and quoted solutions are
  quotation; the author's own material is under CC BY 4.0. The reviewed archive had no licence notice.
- `LICENSE`: the scope of the CC BY 4.0 licence (the author's material only) and the licence's official text.
- `THIRD_PARTY.json`: every file that reproduces a third-party text, found from the archive's own records; the verifier
  recomputes it and checks the counts `NOTICE.md` states.
- `CHANGES.md`: this file.
- Dated addenda of 2026-09-29, each next to the records it corrects:
  - `planted_defects/ADDENDUM_2026-09-29.md`: who wrote the planted edits (the study design is the author's; AI agents
    wrote the specification, edits, dependency arguments, intended labels and checks; the author read no individual edit
    before the gates ran); what each gate's prompt contains (the witness and closure
    prompts carry the problem's marking scheme, which the grade prompt forbids; the two P1 collisions; who saw which rubric or
    ledger); what the executable checks establish and the P5 release note; the protocol's status (prespecified and
    self-timestamped, with the commit and request times) and which reads were prespecified or post hoc; the five disputed
    labels; the post-hoc status of the re-query `runs/grade_rep2/`; what "review" means in the log; the post-submission records.
  - `witness_discovery/ADDENDUM_2026-09-29.md`: the proposer and grader prompts were not information-matched; the protocol is
    prespecified and self-timestamped; who made the judgments in `recovery.json`; "review" in the log.
  - `reference_adjudication/ADDENDUM_2026-09-29.md`: who wrote the ledger; two ledger corrections found by a model check on
    2026-09-29 (P6 L6.2 in `LEDGER_v2.md`: "equivalently" states only a sufficient condition for a fixed P; P1 L1.1: the
    survivor argument attributed to Chen is the ledger's own gloss); "review" in the records.
  - `closure_adjudicated/ADDENDUM_2026-09-29.md`: who wrote the comparisons in `adjudication_notes.md`.
  - `pilot_critique/ADDENDUM_2026-09-29.md` and `pilot_critique_ext/ADDENDUM_2026-09-29.md`: who made the reads in
    `author_read.md`; `pilot_critique_ext/gate_glm53/summary.json` was never produced.
  In each case the corrected record says "author" for work that was produced by a model under the author's direction and
  reviewed by the author, or "pre-registered" for a protocol that is prespecified and self-timestamped.
- `post_submission/`: runs the author made after submission (7 September 2026) on the same 32 planted texts, outside the paper's
  protocol (Appendix S): a re-run of the witness gate (2026-09-08/09), a witness audit with the marking scheme removed
  (2026-09-11), a third run of the grade gate (2026-09-08), a grade prompt with three added sentences of the audit's instructions and a fourth
  run of the grade gate (both 2026-09-21). Five runs of two graders on 32 texts, three files per call, each a byte-for-byte copy of the
  author's run record, listed with its digest in `records.json`; `summary.json` with every tally and per-text decision;
  `summarize.py`, which recomputes it; `README.md`, which states the dates, how the prompts differ and the runs' status.

## Changed

- `README.md`: names the author and the release repository; says how to verify and what the verifier checks; points to
  `NOTICE.md`, `CHANGES.md`, the addenda and `post_submission/`; adds sections on the planted-defect study, the
  post-submission runs and the terms used in the dated records. In the reviewed text it corrects the attribution of
  `author_read.md`, `recovery.json`, the ledger and the adjudication notes (produced by a model under the author's direction
  and reviewed by the author), the witness protocol's status (prespecified and self-timestamped), the stale note on files "not
  yet released", and the description of `reference_adjudication/`; and it names what the release leaves out (the IMO 2025
  campaign of the paper's Appendix A, the internal model-run review reports, the record of the 29 September 2026 model
  check of the bases, the session logs behind the provenance statements).
- `verify_bundle.py` (a copy of the builder, `scripts/supplementary.py`): the author and organisation name scan is removed,
  since the archive now names its author, and the local-path and credential scans stay. New checks cover `NOTICE.md`,
  `LICENSE`, `CHANGES.md`, `THIRD_PARTY.json` and the counts `NOTICE.md` states, the six addenda and the five records they
  correct, and the post-submission records and tallies. The pilot note that printed "not yet released (grading in progress)"
  for a file that was never produced now says so. A `.git/` directory is ignored, so a clone of the release repository verifies.
  The builder also runs from a git worktree (records that name the original checkout's path are re-based) and no longer
  replaces the author's name in copied scripts.
- `scripts/pilot_critique.py`, `scripts/planted_defects.py`, `scripts/reference_adjudication.py`,
  `scripts/witness_discovery.py`: the reviewed archive's anonymization replaced the author's organisation name inside five
  key-file defaults, producing paths of the form `~/.config/the authors/...`. The scripts now ship byte-identical to the
  author's (`~/.config/vexorium/...`). No logic changed.
- `scripts/closure_matrix.py` and `scripts/witness_discovery.py`: the builder's local-path scrub now also removes a
  coding-assistant session id and scratchpad segment that the reviewed archive left in `closure_matrix.py` (a path literal
  split across two source lines) and the private directory tail of two case paths in `witness_discovery.py` (the file names
  are kept). Both are defaults that the bundle's own runs do not read. No logic changed.
- `scripts/claim_audit.py`: the claim guard that gates the paper's build, extended for the camera-ready (population, paired
  outcome, attribution, run-qualifier and post-hoc checks over the camera-ready's macro registry, and a positive control that
  must flag the reviewed abstract). It reads the paper's sources and generated macros, which are not part of this archive;
  nothing in the archive depends on it.
- `MANIFEST.json`: regenerated for the files above.

## Not changed

Every other file is byte-identical to the reviewed archive. In particular the texts, plantings, checks and every stored model
call of the planted-defect study, the closure corpora and their ratings and label layers, the pilot, the replication, the
witness-discovery and reference-adjudication experiments, and their results and tables are exactly as the reviewers saw them.
