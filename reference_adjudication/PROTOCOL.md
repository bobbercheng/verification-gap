# Reference-anchored adjudication: protocol

Written 2026-09-06 14:27:37 UTC, before any call of this experiment (repository state 65d6fb2 plus uncommitted v7
edits). Implemented by `scripts/reference_adjudication.py`; the ledger is `LEDGER.md` (a copy of
research/v7_plan/REFERENCE_LEDGER.md at this time; author-written from Evan Chen's IMO 2026 Solution Notes, version of
3 September 2026, cross-checked against the AoPS wiki where it could be fetched, see the ledger's status note).

## Question
The v6 witness experiment confirmed local errors but left their consequence for a proof obligation to the checkers'
`fatal` judgment, which the review showed can follow the objection's wording. Here every confirmed objection is
adjudicated against a published reference: which required statement of the ledger does it affect, and does the text
establish that statement elsewhere as written? Severity becomes a reference question instead of a model vote; what the
reference cannot settle (a false display beside a correct argument) is reported as a stated convention, both ways.

## Inputs (fixed)
- The 96 objections of the v6 experiment (`witness_discovery/check/*/*/request.json`: quote and objection text; 42 from the
  witness procedure, 54 from the ordinary grader), on the 20 case texts (`witness_discovery/cases.json`).
- The ledger statements per problem (LEDGER.md; embedded verbatim in the script as LEDGER).

## Stage 1: ledger-guided objection adjudication (192 calls)
Every objection is judged by GPT-5.6-Sol (Codex CLI, read-only sandbox, web search off, reasoning effort high) and Claude
Opus 5 (Claude Code CLI, no tools). The prompt contains: the problem's closure rubric core, the ledger statements, the full
text, the quote and the objection text. It does NOT contain a procedure label, a claimed status, the proposer's identity, or
the v6 checkers' verdicts. The checker is told that the objection's own opinion of severity is not evidence. It returns:
affected_statement (a ledger id or "none"), objection_correct (yes/no/unclear), established_elsewhere (yes/no) with a
verbatim quote when yes (anchored mechanically), status_as_written in {established, not_established, false_display}
(false_display = a false line or misprint beside an argument in the text that does establish the statement),
repair_distance in {symbol, sentence, lemma, none}, explanation (<=120 words).
A checker may see an objection produced by its own lab; same-lab and other-lab judgments are reported separately.

## Stage 2: ledger-guided closure rating of the 20 texts (60 calls)
GPT-5.6-Sol, Claude Opus 5 and GLM-5.3 (Z.ai API, thinking, one retry without thinking) each rate every case text once with
the closure rubric plus the ledger: for each ledger statement, established as written (yes/no) with a verbatim quote when
yes; S_ref = number of the two S obligations all of whose ledger statements are established. GLM has a declared freeze
(analysis time); missing GLM ratings are reported as missing.

## Rules (fixed)
- An objection's adjudicated status is the two checkers' status_as_written when they agree; otherwise "split" (reported
  with both values). Anchoring of established_elsewhere quotes is mechanical (whitespace and markup normalized).
- Per text and obligation: "not established (reference)" iff some objection on it is adjudicated not_established by both
  checkers with an affected ledger statement other than "none"; "false display only" iff the only adjudicated non-established
  outcome is false_display; otherwise "established or no objection". Reported beside the ledger-guided S_ref of each lab and
  the v6 S_valid / grades.
- The open disputes (v6 groups C, D) are resolved by the reference outcome; each resolution names the ledger statement.
- Endpoints: (i) fraction of the 96 objections with an affected ledger statement; (ii) checker agreement on
  status_as_written; (iii) per-text reference outcome vs v6 S_valid and grades; (iv) the stated-convention cases
  (false_display) listed by name; (v) same-lab vs other-lab agreement; (vi) costs (calls, seconds).
- Nothing here is changed after launch; deviations are logged in DEVIATIONS.md with times.
