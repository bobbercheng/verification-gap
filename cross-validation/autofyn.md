# IMO 2026 cross-validation: Codex campaign vs. AutoFyn

Last updated: 2026-07-20T23:30:26Z

## Verdict

The two campaigns agree on the final conclusion of all six problems. There is
no discovered contradiction. This is meaningful corroboration, but it is not
six fully independent replications: both campaigns used GPT-5.6-Sol/Pro, and
some proof mechanisms converge closely.

The external report is *ChatGPT 5.6 Pro on the IMO 2026 Problems: One-Shot
Solution Attempts*, by Akashnil Dutta, Adib Hasan, and Tarik Moon. It reports
61m 42s of displayed solution time and an author-assessed score of 41/42. Its
only deduction is Problem 2, scored 6/7 after an additional jury-style review.
These are author assessments, not official IMO jury results.

- Source: <https://github.com/SignalPilot-Labs/AutoFyn/blob/production/results/imo-2026/pdfs/IMO_performance_by_GPT_5_6_sol.pdf>
- PDF SHA-256: `a8d08d30da2f000bf433597f7ec634c98fc9d166ef5e84ca07dcdb04f8b54c1f`
- PDF metadata creation time: `2026-07-16T17:55:07Z`

## Our campaign timing

The timestamped invocation records give three useful measurements:

| Milestone | Interval | Wall time |
|---|---:|---:|
| First solve call to six complete candidate answers | 21:17:37–22:34:09 UTC | **1h 16m 32s** |
| First solve call to six strict-gate completions | 21:17:37–23:13:54 UTC | **1h 56m 17s** |
| Route canary through final strict-gate completion | 21:16:15–23:13:54 UTC | **1h 57m 39s** |

The 23 recorded adapter invocations sum to 16,726.492 seconds (**4h 38m
46.492s**) of process time, much of it concurrent and including two abandoned
30-minute attempts. That sum is not comparable to wall time, and it excludes
some direct specialist auditing. AutoFyn's 61m 42s is the sum of six one-shot
times displayed by the ChatGPT application, so it is also not an apples-to-
apples wall-clock benchmark.

## Problem-by-problem comparison

| Problem | Conclusion agreement | Mechanism comparison | Cross-validation strength |
|---|---|---|---|
| P1 | Exact: \(M=\prod_p p^{\gcd_i v_p(A_i)}\). | Both use the primewise Euclidean gcd invariant. AutoFyn uses \(\Omega\)-mass plus nonunit count for termination; ours uses lexicographic board product plus nonunit count. | **Strong answer check; moderate proof independence.** |
| P2 | Exact: \(OM=ON\). | AutoFyn uses a long trigonometric power calculation and is author-scored 6/7 because directed signs and degenerate second intersections were not justified. Ours uses a different cyclic/radical-axis construction and explicitly handles tangent multiplicities, signed powers, and circle distinctness. | **Strong complementary check**, though neither assessment is official. |
| P3 | Exact: \(c_n=2^n/(2^{n+1}-1)\). | Both reduce optimal drafting to a decreasing alternating sum, use subset-sum spacing for the upper bound, and a sparse graph/tree argument for binary lengths. | **Strong answer agreement but weak mechanism independence.** |
| P4 | Exact: \(\theta=180^\circ/n\), \(n\ge2\). | Both use an integral-multiple descent and the same clean-triangle obstruction. Our manufacturing cut uses a largest-angle interval; AutoFyn uses a fractional-part lemma. | **Strong answer check; moderate proof independence.** |
| P5 | Exact: \(f(x)=x+C\), \(C\ge0\). | Both begin with the forced iterate identity and end with RMS–AM–GM. AutoFyn aligns positive-displacement orbits and uses connectedness; ours derives a quadratic local estimate and kills variation with fine partitions. | **Strong, materially different middle proof.** |
| P6 | Same required theorem: \(a_{n+T}=a_n+L\). | AutoFyn proves periodicity using finitely many minimal squarefree compatibility supports. Ours proves the stronger small-prime erasure lemma and permits \(L=\prod_{p\le a_1}p\). | **Strong for the required existence theorem; partial for our stronger explicit period.** |

## P2 detail exposed by the comparison

Our synthetic proof compresses the derivation of the ray order

\[
AB,AK,AL,AC.
\]

The external proof supplies a clean justification. For an interior point
\(P=(a:b:c)\) in barycentric coordinates, its ray positions from \(B,C,A\)
are monotone in \(c/a,b/a,c/b\), respectively. The hypotheses give

\[
\frac{c_K}{a_K}<\frac{c_L}{a_L},\qquad
\frac{b_L}{a_L}<\frac{b_K}{a_K}.
\]

Dividing the first comparison by the second yields

\[
\frac{c_K}{b_K}<\frac{c_L}{b_L},
\]

which is exactly the required order from \(A\). Thus the cross-check fills
the one step that is terse in our presentation. Conversely, our treatment of
tangencies and signs addresses the central gap identified in AutoFyn's P2.

## Overall assessment

- **Answer-level agreement:** 6/6.
- **No conflicting lemma or counterexample found.**
- **Most independent corroboration:** P2, P5, and the required part of P6.
- **Least independent corroboration:** P3, because the core proof architecture
  is essentially the same.
- **Residual risk:** same-model-family correlation, unofficial grading, and
  AutoFyn not independently establishing our stronger explicit P6 period.

The appropriate status remains **6/6 provisionally resolved**, now with
external answer-level corroboration and a documented proof-dependency audit.
