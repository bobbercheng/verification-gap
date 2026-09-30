# Post-submission runs on the same 32 texts (added 2026-09-29)

These are runs made by the author after submission (7 September 2026), on the same 32 planted texts (`planted_defects/texts/`: 8
originals and their 24 single-edit mutants) and with the same two graders as the paper (GPT-5.6-Sol through the Codex CLI,
Claude Opus 5 through the Claude CLI). **They are outside the paper's protocol** (`planted_defects/PROTOCOL_PLANTINGS.md`) and
are post hoc: the texts, their labels and the paper's results were known before any of these calls. Appendix S of the
camera-ready reports them; no figure in the paper's body rests on them.

Every file under the five run directories is a byte-for-byte copy of the author's run record, filtered to the 32 texts; nothing
was edited, re-run or excluded. `records.json` lists every file with its SHA-256 and, per run, its first and last request time
and two identity checks: the request's `text_sha256` equals the digest of the bundled planted text, and the request's
`system_sha256` equals that of the paper's primary run of the same gate (`planted_defects/runs/grade/` or `/witness/`).

| directory | requests started (UTC) | calls | what changed against the paper's gate |
|---|---|---|---|
| `witness_keyed_rerun/` | 2026-09-08 23:40 to 2026-09-09 00:15 | 64 | nothing in the recorded prompt: a second run of the witness gate (which the paper ran once) with the same system prompt (the problem's marking scheme with the audit instructions) and the same texts |
| `grade_rerun/` | 2026-09-08 13:03 to 13:40 | 64 | nothing in the recorded prompt: a third run of the grade gate (after the paper's first run and same-day re-query) with the same system prompt and texts |
| `witness_keyfree/` | 2026-09-11 03:02 to 03:38 | 64 | the marking scheme is removed (see below); run once, never repeated |
| `grade_instructed/` | 2026-09-21 05:17 to 05:34 | 64 | the grade prompt plus three sentences of the audit's instructions (see below) |
| `grade_retest/` | 2026-09-21 05:36 to 06:11 | 64 | nothing in the recorded prompt: a fourth run of the grade gate, made in the same session right after `grade_instructed/` |

Layout: `<directory>/<grader>/<text id>/request.json` (the exact system prompt, its digest, the text's digest and path, the
request time; no proof text), `response.json` (the raw CLI response) and `parsed.json` (the parsed fields and token usage).
Grader directories are `gpt/` and `claude/`. Text ids are the paper's (`<base>` for an original, `<base>-F|G|H` for its fatal,
gap and harmless edits).

## What each prompt contains

- **Paper's grade prompt** (`grade_rerun/`, `grade_retest/`; identical `system_sha256` to the paper's grade gate on every call): the
  problem statement and the 0-7 coordinator scale, whose 5-6 band admits "minor gaps or a small error that is straightforwardly
  repairable". It forbids consulting a published solution or using a fixed list of required lemmas, and asks for `grade`,
  `complete`, `main_gap` and up to three `errors` with quotes. It does not define "complete".
- **Instructed grade prompt** (`grade_instructed/`): the same prompt with one added line, recorded in `inserted_text`: "Judge
  only what is written. Do not use the length of the text, its confidence, or claims of completeness. Do not repair the argument
  for the author." The 5-6 band is unchanged, so this is a partial instruction control, not a rubric that requires rejecting
  unresolved essential errors. It ran in the same session as `grade_retest/`, so the two share whatever that session changed.
- **Paper's witness prompt** (`witness_keyed_rerun/`; identical `system_sha256` to the paper's witness gate on every call): the
  problem's marking scheme (the closure rubric: the steps a complete proof needs; the answer on P3 and P5, and the value of M in
  P1's field mapping; example wrong approaches on P1, P5 and P6, on P1 the false principle that both P1 fatal edits plant) with
  its return block replaced by the obligation audit instructions, which include "Do not repair the argument for the author".
- **Key-free witness prompt** (`witness_keyfree/`): the same audit instructions with the marking scheme removed. It states no
  answer, no list of required steps and no named lemma or wrong approach; instead it asks the model to identify, from the
  write-up alone, the two load-bearing obligations its route must discharge and to report them as `lower_bound` and
  `upper_bound`. It therefore changes two things at once (no scheme, and self-chosen obligations), and it was run once, so its
  own run-to-run variation is unmeasured.

The recorded prompts are identical where stated, but the model inputs are not byte-identical: the CLI harness changed between
the runs, and the token counts in `parsed.json` differ from the paper's primary run on some calls (`summary.json`,
`identity_with_primary_run`). Requests of 2026-09-21 also carry `runner`, `protocol`, `stratum`, `run_dir` and `run_tag`
fields; they name files and labels of the author's run tooling that are not part of this supplement, and the prompt itself is
complete in `system`.

## Tallies

`summary.json` holds, for each run, rule and grader (and the pair of graders), the broken texts accepted (F and G, 16) and the
sound texts rejected (O and H, 16; sound under the repair-tolerant convention only), the same counts with the five disputed
labels set aside, the pair's routing (refer when the graders disagree), each grader's disagreements with the intended truth
under both conventions, every per-text decision, and two comparisons with the paper's witness gate (the keyed re-run, and the
key-free run per grader and per pair). Rules are the paper's: pass mark (grade at least 5), strict mark (grade 7) and the
completeness flag for the grade runs, `S_valid` = 2 for the witness runs. Regenerate or check it offline:

    python3 post_submission/summarize.py --root .           # rewrite summary.json from the records
    python3 post_submission/summarize.py --root . --check   # exit 1 on any difference

`python3 verify_bundle.py verify --out .` runs the same check and re-hashes every record against `records.json`.
