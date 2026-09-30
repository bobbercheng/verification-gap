# Witness discovery on disputed texts: protocol

Written 2026-09-06 04:21:30 UTC, before any proposer or checker call of this experiment was made (repository state at writing: 21ca1f7, with uncommitted v6 edits in progress). The case list, the prompts, the checking rule and the endpoints below are fixed by this file; `scripts/witness_discovery.py` implements them. Anything decided after the runs is marked "post hoc" in RESULTS.md.

## Question

The v5 alarm test showed that cross-evaluator disagreement on structural closure S flags the texts whose credited mechanisms are refuted by an independent record. The unmeasured link is the next step: from a flagged text to a *decisive witness*, an object that settles the dispute by inspection (a counterexample to the quoted claim, an explicit non-sequitur, or the precise missing statement) rather than by another vote. This experiment measures whether a single tool-free call to a frontier model, given the same rubric as the closure instrument and asked for verdicts *with witnesses*, produces witnesses that (a) independent checkers confirm and (b) coincide with the defect the independent record documents; and whether it produces confirmed witnesses on texts that the public verifier graded 7/7 (false witnesses).

## Case list (20 texts, fixed before launch)

Texts are identified by the record ids of the closure corpus (P3/P6/P2 corpus: `closure_adjudicated/labels.json`; P1/P4/P5 replication corpus: `replication_ext/results.json`). The sha256 of each text is recorded in `cases.json` at launch.

Group A, credited-defective (alarm hits): texts with an independent refutation or sketch record AND at least one single-evaluator rating S=2.
- A1 `p6-gpt-5.6-sol-main-t009` (P6). Record: validity_overrides.json; the finiteness step (F) rests on the false lemma "every pairwise-intersecting family of finite sets has finitely many minimal finite transversals". Recovery target: a witness for lower_bound (F) that targets this lemma or its proof (e.g. a family with infinitely many minimal finite transversals).
- A2 `p6-deedy-gpt-5.6-sol-final` (P6). Record: validity_overrides.json and public verifier grade 1/7 with a machine-verified counterexample. Same target as A1.
- A3 `p6-kimi-k3-round2-t007` (P6). Record: validity_overrides.json, public verifier first-pass grade 3/7: the self-duality theorem, established for finite minimal transversals, is applied to a Zorn-extracted minimal transversal not shown to be finite. Recovery target: a witness for lower_bound (F) that targets this application.
- A4 `deedy-gpt-5.6-sol-final` (P3). Record: public verifier grade 2/7: both bounds rest on the refinement lemma whose "column sweep" proof is a sketch (part (i) sweep/cancellation induction not valid as written; part (ii) strip survival asserted). Recovery target: a witness for lower_bound or upper_bound that targets the refinement lemma's proof.

Group B, documented-defective but never credited (all single evaluators S=0): the three P3 public finals the v5 review named as alarm misses.
- B1 `deedy-grok-4.5-final` (P3). Record: public verifier grade 2/7: Theorem B's k>=1 induction step is garbled (lower_bound); Theorem C never completes (upper_bound). Recovery target: witnesses targeting Theorem B's step or Theorem C.
- B2 `deedy-muse-spark-1.1-final` (P3). Record: grade 1/7: wrong answer (n+1)/(2n+1); the lower-bound guarantee of the "even-multiples" construction is false (n=2, pieces 0.4,0.4,0.2: Xiang slices the small piece and holds Liu to 0.505); no upper bound. Recovery target: a witness for lower_bound targeting the construction's guarantee (or the wrong closed form), and not_written for upper_bound.
- B3 `deedy-deepseek-v4-pro-final` (P3). Record: grade 1/7: wrong answer; the equally-spaced construction's guarantee is false (n=2, pieces 0.2,0.2,0.6: Xiang holds Liu to 53/105); no proof of either direction. Same target as B2.

Group C, alarm flags without an independent record (unresolved in v5):
- C1 `kimi-k3-round3-t007` (P3): lower_bound scored 2 by Kimi, Claude, GPT and 1 by GLM.
- C2 `kimi-k3-round4-t014` (P3): upper_bound scored 2 by GLM, Kimi, Claude and 1 by GPT.
- C3 `p6-kimi-k3-round1-t021` (P6): upper_bound scored 2 by Kimi and <=1 by GLM, Claude, GPT.

Group D, replication flips (P1/P5 texts on which the evaluators' S differ and a lineage conclusion changes):
- D1 `p1-glm52-2ede1c6b-v1` (P1): Claude (all passes) and GLM S=2, GPT S=1 (GPT's rating note: Section 3 falsely infers positive valuation gcd from a prime dividing some initial entry; board {2,3}).
- D2 `p5-deepseek-v4-pro-main-t033` (P5): Claude and GLM S=2, GPT S=1.
- D3 `p5-deepseek-v4-pro-main-t038` (P5): Claude S=2, GLM and GPT S=1.
- D4 `p5-nemotron-2587b733-v2` (P5): Claude's three text passes 1, 2, 0.

Group E, controls: public verifier grade 7/7 and every single evaluator S=2.
- E1 `deedy-claude-fable-5-final` (P3); E2 `deedy-gpt-5.6-sol-xhigh-final` (P3); E3 `p6-deedy-gpt-5.6-sol-pro-final` (P6); E4 `p1-deedy-kimi-k3-final` (P1); E5 `p4-deedy-claude-fable-5-final` (P4).

Group F, low control: `p6-deedy-grok-4.5-final` (P6), public grade 1/7, every evaluator S=0, the text says "(Not yet complete.)".

Authorship overlap (declared): GPT-5.6-Sol wrote A1, A2, A4, E2, E3 (and the default-setting final A2 is the same lineage as A1); Claude Fable 5 wrote E1, E5. The proposers are GPT-5.6-Sol and Claude Opus 5; a proposer's verdicts on texts written by its own lab are reported separately.

## Proposers and prompt

Two proposers, run independently on identical prompts, tool-free, one call per text: GPT-5.6-Sol (Codex CLI, read-only sandbox, web search off, reasoning effort high) and Claude Opus 5 (Claude Code CLI, no tools, no settings, no session). The system prompt is the problem's closure rubric (P3: the RUBRIC constant of `closure_annotate.py`; P1/P4/P5/P6: `closure_rubric_pN.txt`) with its JSON return block replaced by the witness instructions in `scripts/witness_discovery.py` (function `proposer_system`). The user message is the text (first 120,000 characters, as in the closure instrument). The proposer returns, for each of the three obligations (reduction, lower_bound, upper_bound), a status in {written_and_valid, written_but_invalid, not_written} and, for every status other than written_and_valid, a witness: a verbatim quote (40-400 characters), the witness proper (counterexample / non-sequitur / missing statement) and why the step is load-bearing.

## Checking

Every witness on lower_bound or upper_bound (the two obligations that define S) is checked by two checkers that did not propose it: GPT proposals by Claude Opus 5 and GLM-5.3; Claude proposals by GPT-5.6-Sol and GLM-5.3 (GLM-5.3 through the Z.ai Anthropic-compatible API with thinking, as in the closure instrument). A checker sees the rubric, the full text, the obligation, the quote and the witness; it does not see who proposed, the proposer's other verdicts, or the other checker. It returns quote_faithful in {yes, no, unclear}, verdict in {confirmed, rejected, unclear}, fatal_for_obligation in {yes, no, unclear} and an explanation. Witnesses on the reduction obligation are recorded but not checked.

Anchoring (mechanical): a quote is anchored if, after collapsing whitespace and removing the characters `* _ $ \` on both sides, it is a substring of the text. Unanchored quotes are still checked (the checker judges faithfulness in context) and the anchor rate is reported.

Confirmation rule (fixed): a witness is **confirmed** if both checkers return verdict = confirmed and neither returns quote_faithful = no; **contested** if exactly one checker confirms; **rejected** otherwise. fatal_for_obligation is reported alongside, not used in the rule. A text is **resolved** by a proposer if at least one of its lower_bound/upper_bound witnesses is confirmed.

## Endpoints

- E-A (recovery on credited-defective texts, n=4): per proposer and for the union of the two proposers, the number of Group A texts with a confirmed witness whose target coincides with the documented defect (targets above). The coincidence judgment is made by the author after the runs from the published quotes and witnesses, and RESULTS.md prints the quote and witness next to the record so the judgment can be audited.
- E-B (recovery on never-credited documented texts, n=3): same for Group B.
- E-E (false witnesses on controls, n=5): the number of confirmed witnesses on Group E texts (expected 0). Every confirmed witness on a Group E text is printed in full and inspected by hand; if it is a genuine error the public verifier missed, that is reported as such, not hidden.
- E-CD (resolution of open disputes, n=7): the number of Group C and D texts resolved by at least one proposer, and which side of the earlier evaluator disagreement each confirmed witness supports.
- E-F: Group F outcome (expected not_written on both obligations).
- Agreement: status agreement between the two proposers per obligation over all 20 texts (60 obligation verdicts).
- Cost: wall-clock seconds and reported tokens per proposer call and per checker call, next to the closure instrument's per-rating cost on the same texts where available.

Counts, not rates: with 4, 3, 5 and 7 texts per group the endpoints are reported as counts with the texts named. Nothing in this protocol is changed after launch; deviations (e.g. a CLI failure, a retry) are logged in RESULTS.md with the time.

## Amendment 1 (2026-09-06 04:28:33 UTC, still before any call of this experiment)

Adopted from a second reading of the plan before launch. These replace the corresponding parts above where they conflict.

1. **Success is defined by the evidence produced, not by agreement.** Every checked objection (from either procedure below) is classified after checking into exactly one of: **substantiated defect** (an exact quoted claim and a counterexample that satisfies its assumptions, or an inspectable invalid inference; both checkers confirm and both classify the evidence as a counterexample or an invalid inference), **localized concern** (both checkers confirm that a specific justification is missing, but no decisive refutation is supplied), **unsupported allegation** (both checkers reject), or **unresolved** (checkers split, unclear, or a checker missing at freeze). Checkers therefore also return `evidence_kind` in {counterexample, invalid_inference, missing_justification, none}. Where a substantiated counterexample is finite or computable, the author writes an executable check after the run and ships it with the witness (post hoc, labelled). Group E texts are called **high-grade agreement controls**: their public grade 7/7 and unanimous S=2 are model judgments, and finding no witness does not establish correctness.
2. **Ordinary-review baseline at the same budget.** The same two models (GPT-5.6-Sol, Claude Opus 5; same transports, same reasoning effort) grade the same 20 texts once each with the ordinary 0-7 coordinator rubric of the paper's grade baseline (`baseline_rubric_pN.txt`; the P1/P4/P5 files were created from the P3 template with the problem statement swapped, before launch) extended only to return the errors the grader found (at most three, ordered by severity, each a description that names the step and, optionally, a verbatim quote). Budget per text and per procedure: one first-stage call. The checking stage is applied identically to both procedures: at most two objections per text per procedure (the proposer's lower_bound and upper_bound witnesses; the grader's two most severe errors), each judged by the same two checkers under the same rule, so the evidence standard is the same. The checkers see the objection and the text, not which procedure produced it. Measured for both: substantiated defects (texts and distinct defects), localized concerns, unsupported allegations, unresolved outcomes, calls, tokens, elapsed seconds, and delivery failures (no parseable output).
3. **Known-defect recovery is reported apart from new discovery.** Groups A and B are texts with defects known before the run (recovery); Groups C and D are open disputes (discovery); E and F are controls. Results are reported per group and never pooled into one rate; distinct defects are counted as well as texts (the two P6 GPT texts share one false lemma). A witness found on a Group B text shows witness-finding capability; it is not a success of the disagreement-triggered workflow, because those texts were never flagged. Group D is four texts from two problems and three lineages (P1 GLM-5.2; P5 DeepSeek x2; P5 Nemotron), not a three-problem replication. Proposers and graders see only the rubric and the text; no receipt, prior rating, or override is shown to them. Texts, prompts, budgets and the outcome rules are frozen by this file.
4. **Which conclusions the evidence changes.** For every substantiated defect or localized concern on a Group C/D text, the author records after the run which side of the earlier evaluator disagreement it supports and which lineage conclusion (S=2 status, improvement, regression, first crossing) would change if the defect were applied as a correction, with the same criterion as validity_overrides.json. This mapping is post hoc and is published with the quotes.
5. **Checker fallback.** If a checker has not returned for an objection by the analysis freeze (time recorded in RESULTS.md), the objection is classified from the returned checker alone and marked single-checker; counts of such cases are reported.
