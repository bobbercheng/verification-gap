# Paired critique / no-critique pilot — pre-registration (written before any run; 2026-09-05 22:20 UTC)

Design. Four frozen starting texts (hash-identified), two problems, two conditions, two repeats: 16 single-shot,
tool-free continuations by one model (kimi-k3, Moonshot API, max_tokens 60000, provider-default sampling).
  P3-high  S=2, local defects:  our Kimi R1 third-context seed (sha 5a75aa5c…), critique = its frozen defect review (D1, D2).
  P3-low   S=0:                 GLM-5.2 simple-campaign candidate 003 (sha of glm52-simple-c4), critique = its frozen review (D1, D2).
  P6-mid   S=1:                 public Kimi round-3 turn-9 tracking file (sha 01814ca4…), critique = the exact reviewer text the public
                                harness gave the next session ("close the finiteness crux rigorously …").
  P6-low   S=0:                 our Nemotron candidate 8828b58a v2, critique = fatal_issues + required_fixes of its frozen review.
Conditions. C = draft + the critique + "revise into a complete rigorous proof addressing every listed defect";
            N = draft + "revise into a complete rigorous proof, fixing any gaps you find". Identical otherwise.
Endpoints (graded blind to condition, by the paper's annotator pipeline): structural closure S of the output (GLM-5.3, thinking,
per-problem rubric; Kimi K3 as second annotator; adjudicated as in the paper) and the tool-free gate review (GLM-5.3, reviewer
rubric, fail-closed predicate). Author reads every output rated S=2 or gate-pass.
Hypotheses stated in advance.
  H1 (repair above closure): from P3-high, C reaches gate pass more often than N.
  H2 (no discovery from S=0 in one shot): from P3-low and P6-low, neither condition reaches S=2.
  H3 (critique names the missing object): from P6-mid, C raises S relative to N.
Limits. One model, one continuation per run, no tools, 16 runs, 4 seeds; a pilot for within-text contrasts, not a rate estimate.

## Post-hoc extension (added 2026-09-05 22:40 UTC, after 14 of 16 pre-registered runs had finished)
Observation: all four continuations from the S=2 text returned a write-up (finish=stop) within the 60k-token budget; every
continuation from an S<2 text observed so far ended with finish=length after ~160k-210k characters of reasoning and no write-up.
Extension: the twelve S<2 runs (p3-low, p6-mid, p6-low; C/N; two repeats) are re-run with identical prompts and a 200,000-token
budget into `pilot_critique_ext/`. The 60k-budget results remain the pre-registered primary outcome; the extension is reported
separately as a budget sensitivity check. No other change.

## Correction (2026-09-06)
The header above says the protocol was "written before any run; 2026-09-05 22:20 UTC", and the extension note says it
was "added 2026-09-05 22:40 UTC, after 14 of 16 pre-registered runs had finished". Both times were typed from memory
and are wrong. What the run records show (each run's meta.json: finished_at, elapsed_seconds; UTC from time.gmtime):
- The protocol text and the launch command were issued in the same step, not one before the other. The machine
  clock at launch was about 21:44 UTC. The four runs from the S=2 seed (p3-high, C/N, two repeats) finished between
  21:52 and 21:58 UTC.
- The twelve other runs (p3-low, p6-mid, p6-low) started at about 22:05 UTC, after a restart with more parallel
  workers; the partial runs of the first launch were lost and are not retained. They finished between 22:25 and
  22:37 UTC.
- The extension note was written at about 22:34 UTC, when 14 of 16 runs had finished; the last two finished at
  22:36:50 and 22:37:12 UTC.
- No immutable pre-run record of this file exists. The first git commit containing it is 0940706 (2026-09-05
  22:51 UTC), after every primary run had finished.
Consequently the paper describes the pilot as "protocol-first, exploratory", not as pre-registered. The design,
conditions, endpoints and hypotheses H1-H3 above are as issued at launch and were not changed after any outcome was
seen. The original header and extension note are left unmodified above so that the error remains visible.
