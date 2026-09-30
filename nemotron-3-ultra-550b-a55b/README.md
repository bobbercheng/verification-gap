# NVIDIA Nemotron 3 Ultra 550B A55B results

Exact route: `nvidia/nemotron-3-ultra-550b-a55b:free`, OpenRouter, NVIDIA-only
provider routing.

## Scorecard

| Problem | Attempts | Final status | Strongest result or rejection reason |
|---|---:|---|---|
| [P1](solutions/problem-1.md) | 5 | **Provisionally resolved** | Correct termination argument and primewise Euclidean invariant |
| P2 | 3 | Unresolved | Claimed spiral similarities used the wrong vertex angles |
| P3 | 6 | Unresolved | Correct final value was guessed, but both bounds contained fatal gaps |
| P4 | 3 | Unresolved | Correct special cases; necessity failed for angles such as \(30^\circ\) |
| [P5](solutions/problem-5.md) | 4 | **Provisionally resolved** | Complete orbit/connectedness classification of \(f\) |
| P6 | 4 | Unresolved | Minimal-hitting-set premise was false; CRT argument reversed admissibility |

Total: **2/6 provisionally resolved**.

The accepted candidates have their adversarial reviews in [`reviews/`](reviews/)
and second-order checks in [`verifications/`](verifications/). The rejected
results are summarized in [`unresolved/README.md`](unresolved/README.md). We do
not publish the rejected drafts as solutions.

### Editorial note on P1

The public P1 proof repairs one local sentence in the generated draft. The
draft incorrectly inferred that a nonincreasing product remains above one.
The intended—and sufficient—argument is that every legal move retains at least
one nonunit. The invariant, result, and all remaining steps are unchanged.
