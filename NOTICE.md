# Licensing and attribution

This archive is the supplementary material of "The Verification Gap: Auditing Proof Progress and Repair on IMO 2026" by
Bobber Cheng (MATH-AI 2026, the 6th Workshop on Mathematical Reasoning and AI at NeurIPS 2026), released at
https://github.com/bobbercheng/verification-gap. It mixes the author's own material with third-party material under
different terms. Each is named here so that a reader can tell them apart.

## Third-party material

**Texts from the public IMO 2026 campaign cited in the paper**: the repository https://github.com/deedy/imo-2026 at commit
dbe872307883296c5f06bf8bcb90e6bfd0879364 (short form dbe8723). They are redistributed here only so that the paper's numbers
can be recomputed from the texts that were graded. `THIRD_PARTY.json` lists every such file; the verifier recomputes that
list from the bundle's own records and checks the counts below.

- 169 of the 238 checkpoint texts in `checkpoint_inputs/` and `checkpoint_inputs_ext/`: intermediate and final proof files
  of the campaign's runs, each named by its SHA-256 (the other 69 are from the author's own runs).
- 16 of the 32 planted texts in `planted_defects/texts/`: the 4 public base proofs of the planted-defect study and the
  three edited copies of each. The edits are part of this study; the rest of each edited copy is the campaign's text.
- 6 files in `replication_ext/public_grades/`: byte-for-byte copies of five of the campaign's grade receipts (per run: final
  grade, justification and named issues) and a table of first-pass grades parsed from its README.
- Excerpts: stored model responses quote passages of the texts they grade, `planted_defects/plantings.json` holds the edited
  passages (`search`, `replace`, `hunk`), and grades and statistics derived from the campaign appear in
  `closure_matrix/public_grades.json` and `trajectory_stats_public.json`.

At the cited commit the repository contains no licence file, and its README's only rights statement concerns the problem
statements ("Problem statements © IMO; sourced from tempcollab/proval"); this was checked against the repository at that
commit on 2026-09-29. No licence to these texts is granted by this archive. Anyone who intends to reuse or redistribute them
should seek terms from that source rather than rely on this archive. The same applies to any line of them quoted in the
paper.

**Problem statements** (`problems/`, and inside the system prompt of the stored requests): the six IMO 2026 problem
statements are the copyright of the International Mathematical Olympiad. They are quoted for research use, because every
prompt embeds the statement it grades against, and are not relicensed.

**Published solutions**: the reference ledger (`reference_adjudication/LEDGER*.md`), the adjudication notes and the marking
schemes (`closure_rubric_p*.txt`, `prompts/`) quote or paraphrase short passages of Evan Chen's IMO 2026 Solution Notes and of
community solutions on the AoPS wiki. These are quotation; the notes and pages themselves are not included.

## The author's own material

Everything else in this archive is the author's own material and is licensed by its rights holder, Bobber Cheng, under the
Creative Commons Attribution 4.0 International licence (CC BY 4.0, https://creativecommons.org/licenses/by/4.0/). It
includes the analysis and build scripts; the protocols, deviation logs and dated addenda; the planted-defect specifications,
edits, diffs, dependency arguments and executable checks (written by AI agents in the author's pipeline, as
`planted_defects/ADDENDUM_2026-09-29.md` records); the proofs, checkpoints, reviews and verifications of the author's own
campaigns; the stored requests and model responses included here; the labels, ledgers, results and
tables; and this archive's documentation. Attribute it as: Bobber Cheng, "The Verification Gap: Auditing Proof Progress and
Repair on IMO 2026", MATH-AI 2026 (NeurIPS 2026 workshop), https://github.com/bobbercheng/verification-gap.

CC BY 4.0 does not extend to the third-party material above, including the third-party part of each edited copy and any
excerpt of it quoted inside the author's files.
