# Reference-anchored adjudication notes (2026-09-06)

Scope and method. These notes record how three label decisions that drive observations in the paper were settled.
The author does not act as a mathematical expert. Every judgement is anchored either to a published solution
(Evan Chen, *IMO 2026 Solution Notes*, web.evanchen.cc, version updated 3 September 2026; "Chen" below) or to a
recorded rationale of the public campaign's verifier or of our own gate, and each comparison is written out so that
a reader can redo it against the released texts. Texts are identified by record id and SHA-256 prefix as in
`labels.json`; the model ratings quoted are the layer-1 records in `artifacts/closure_glm_rerun/` (GLM-5.3
re-rating) and `artifacts/closure_kimi/` (Kimi K3), and layer 0 is the first GLM-5.3 pass in `artifacts/closure*/`.
Label layers: raw / glm / kimi / written (a mechanism counts 2 only if both annotators score it 2, else the lower
score) / valid (written, minus mechanisms independently refuted; see `validity_overrides.json`).

## 1. Problem 3: the disputed checkpoint `kimi-k3-round3-t007` (sha256 15413cb68d86...)

Ratings. Layer 0: lower_bound 1, upper_bound 1, S = 0. GLM-5.3 re-rating: lower_bound 1, S = 0 ("substantive
all-n sketch -- matching formula (proof asserted), slack/tree-component count, block lemma proved -- yet
self-labelled sketch needing write-up"). Kimi K3: lower_bound 2, S = 1 ("coherent all-n argument (matching
identity, slack counting forces a tree component, tree inequality, block lemma with proof) covering arbitrary
replies, though telegraphic sketch"). Conservative rule: lower_bound = min(1, 2) = 1, so S = 0 in the written and
valid layers; S = 1 in the Kimi-only layer. This is the only Problem-3 text in the corpus that any annotator
places at S = 1.

What the text is. A tracking file (`## Status: partial`). Its lower-bound material sits under the heading
"Part A proof (lower bound) SKETCH -- looks complete"; the "Current best" section says Part A "needs writing +
numeric checks"; the "Full proof" section reads "(in progress -- Part A essentially done modulo write-up; Part B
open)". The upper bound (Part B) is open in the text: the subset-sum pigeonhole is written and the text itself
records the obstacle ("such a signed sum is NOT always realizable by cancel/chain ops ... Realizability gap").
The reduction of the claiming phase to an alternating sum is stated as "proved (and verified by brute force)" but
its proof is not written; the reduction is recorded by the rubric but not counted in S.

The published lower-bound argument (Chen, "Converse direction in general", pp. 8-9). For Liu's n+1 segments
a_1, ..., a_{n+1} define Delta := min |eps_1 a_1 + ... + eps_{n+1} a_{n+1}| over nonzero (eps_i) in {-1, 0, 1}^{n+1}.
Claim: whatever Xiang does, G := x_1 - x_2 + x_3 - ... + x_{2n+1} >= Delta. Steps:

- (C1) Pair the sorted pieces by rank: d_i = x_{2i-1} - x_{2i} >= 0 for i <= n, d_{n+1} = x_{2n+1}; then G = sum d_i.
- (C2) Build a multigraph Gamma on n+2 vertices: one per segment plus a dummy vertex of length 0. For each i <= n
  join the segments from which x_{2i-1} and x_{2i} were cut; join the dummy to the segment containing x_{2n+1}.
- (C3) Gamma has n+2 vertices and n+1 edges, so some component is a tree (no parallel edges, no loops).
- (C4) The tree is bipartite, vertex set S u T; |Sigma(S) - Sigma(T)| = |sum_{i in I} (+/-) d_i| <= sum_{i in I} d_i <= G,
  and |Sigma(S) - Sigma(T)| >= Delta by the definition of Delta.
- (C5) In the division 1 : 2 : 4 : ... : 2^n, Delta = 1/(2^{n+1} - 1) exactly (a nonzero signed sum of distinct
  powers of two has absolute value at least 1 on the scaled stick).

Chen remarks that for powers of two the bipartite colouring in (C4) can be replaced by summing at the vertex
carrying the largest power of two in the tree component, and that the claim can also be proved by induction if
stated for a general division.

Step-by-step comparison with the draft (all quotations from the draft's "NEW THIS SESSION" items).

| Published step | Counterpart in the draft | Status in the draft |
|---|---|---|
| (C1) rank pairing, G = sum d_i | "Matching formula: D(M) = min over matchings mu of sum_{pairs} abs(p-q) + sum_{unmatched} p_i"; an optimal matching mu is then fixed | Asserted, not proved: "Proof: D = S - 2 sum p_{2k} and sum p_{2k} = max_mu sum min(p,q) by an exchange argument". The published proof does not need this claim: the rank pairing is one particular matching and no minimisation is required. In the draft the formula is load-bearing for the way the multigraph is built. |
| (C2) multigraph on segments; dummy for the odd fragment | "build multigraph on pieces (edge = matched pair of fragments, unmatched frag = mark)" | Present. The unmatched fragment plays the role of Chen's dummy edge. |
| (C3) vertex/edge count forces a tree component | "slack(K) = frags(K) - 2*pieces(K) + 1; cyclic components (E >= V) have slack >= 1; total slack = c - m + #comp <= #comp - 1 (since cuts c <= m-1) => at least one TREE component" | Present, with the count written out. It is a slack-count form of Chen's "n+2 vertices, n+1 edges". |
| (C4) bipartite signs; the signed segment sum is bounded by the component's cost | "For a tree component on piece-set I: bipartite signs give w_I := abs(sum_{i in I} eps_i a_i) <= cost(component) (algebra: sum eps_i a_i = sum_edges (x_e - y_e) + sum_i eps_i U_i, then triangle ineq)" | Present with a one-line justification. The draft also records why cyclic components must be dropped ("odd cycles ... break the per-component inequality", a triangle counterexample checked by hand), the same reason Chen needs a tree. |
| (C5) Delta for the geometric division | "Block lemma": for a super-increasing family with margin delta (a_1 >= delta, a_{i+1} >= delta + a_1 + ... + a_i), the alternating sum of the block values v_B = abs(sum_{i in B} eps_i a_i) is >= delta; proof written (the block containing the largest index exceeds the sum of all other blocks by at least delta). For pieces 2^{i-1}/(2^{n+1}-1) the margin is delta = 1/(2^{n+1}-1), with equality a_{i+1} = delta + sum_{j<=i} a_j. | Present with proof. It is more general than (C5) because the draft sums the costs of all tree components and then takes an alternating sum, where Chen uses a single tree component. |

Verdict recorded. Every step of the published lower-bound argument has a counterpart in the draft, in outline:
the multigraph, the count that forces a tree component, the bipartite-sign inequality, and the estimate for
super-increasing pieces, the last with a written proof. One supporting claim that the published proof does not
need, the min-cost matching formula, is asserted "by an exchange argument" without proof, and the part is
self-labelled a sketch "modulo write-up". The rubric scores 2 only for a mechanism "written out as an argument for
all n" and 1 for one "named/sketched"; on the letter of the rubric the text is a 1 (GLM's reading), on the
substance of the argument it is a 2 (Kimi's reading). We do not overrule the instrument: S = 0 under the
conservative rule (written and valid layers), S = 1 under Kimi alone, and the paper reports both. What the
reference comparison adds is an interpretation: the lower bound was in hand, in outline, one session before both
mechanisms were written out (round 4, turn 14, S = 2 by every layer). The observation that no Problem-3 checkpoint
sits at S = 1 therefore depends in part on the write-up standard the rubric imposes, and cannot be read as evidence
that the two mechanisms were found together. The record cannot separate "not found" from "found but not written to
standard"; the paper states this as a limitation. Nothing here certifies that the draft's outline is correct in
every detail (the matching formula is unproved in the text; we checked only that each published step has a
counterpart and that the block lemma's proof and the margin computation are as stated).

## 2. Problem 6: the false finite-transversal lemma and the three refuted texts

The counterexample, in full. Let x_1, x_2, ... and y_1, y_2, ... be distinct symbols and put

    F_n = {x_1, ..., x_n, y_n}   for n >= 1.

Every F_n is finite and any two members meet (all contain x_1). For each k >= 1 let

    T_k = {y_1, ..., y_{k-1}, x_k}.

T_k is a transversal: it meets F_n in y_n when n < k and in x_k when n >= k. It is inclusion-minimal: removing y_j
(j < k) leaves nothing in F_j = {x_1, ..., x_j, y_j}, because x_k is not in F_j (k > j) and no other y_i is in F_j;
removing x_k leaves {y_1, ..., y_{k-1}}, which misses F_k. The T_k are pairwise distinct, so the family has
infinitely many inclusion-minimal finite transversals. Hence the statement "every pairwise-intersecting family of
finite sets has only finitely many inclusion-minimal finite transversals" is false, and so is any lemma equivalent
to it. The public campaign's verifier recorded a machine-verified counterexample of the same kind in its 1/7 grade
of the GPT-5.6-Sol default final (its own family with T_n = {1, z_1, ..., z_n, w_n} minimal for every n;
`grades/problem-06.json` of the public campaign). What is and is not refuted: the lemma is false in the generality
stated; the IMO statement is true, and the arguments that survive (public Kimi's compactness theorem, the accepted
proofs of the other lineages) use the number-theoretic structure of the greedy sequence, not pairwise intersection
alone.

Criterion (`validity_overrides.json`, `_criterion`). A mechanism scored 2 by the instrument is set to 0 in the valid
layer when an independent record shows the written argument for it is invalid as written: an explicit counterexample
to a lemma it relies on, or a fatal invalid step in that mechanism recorded by the public verifier or our gate. The
criterion is applied to every retained text carrying the same defect, not only to final files. There are no author
overrides.

Affected texts (three, all Problem 6, all on the finiteness field `lower_bound`):

1. `p6-gpt-5.6-sol-main-t009` (sha256 6990dbe90da7...), public GPT-5.6-Sol default, main session turn 9. The text
   states: "Let F be a nonempty, possibly infinite family of nonempty finite subsets of a set P. If every two members
   of F intersect, then there are finitely many nonempty finite sets B_1, ..., B_s subset P such that, for every finite
   X subset P, [X meets every member of F iff X contains some B_j]", and proves it by induction on the size of a finite
   transversal C. Refuted: the family {F_n} above satisfies the hypothesis and violates the conclusion (each T_k would
   have to contain some B_j, forcing infinitely many distinct minimal B_j). Ratings: layer 0 finiteness 2, GLM
   re-rating 2, Kimi 2; written S = 2, valid S = 1.
2. `p6-deedy-gpt-5.6-sol-final` (sha256 fc5dfc45e082...), the same lineage's final file. The same "Finite-transversal
   lemma", now proved by a pruned search tree and Koenig's lemma ("If a family of finite sets is pairwise intersecting
   and has a member C of size r, then it has only finitely many inclusion-minimal finite transversals"). Refuted by
   the same counterexample (take C = F_1 = {x_1, y_1}, r = 2). Public verifier 1/7: "The central 'Finite-transversal
   lemma' is FALSE". Ratings: layer 0 finiteness 2, GLM re-rating 2, Kimi 2; written S = 2, valid S = 1. In v3 this
   text alone carried an author override, which turned the lineage into a spurious 2 -> 1 regression from turn 9
   (`research/acceptance_review_v3/annotation_audit.md`, item 1); the criterion now covers both texts.
3. `p6-kimi-k3-round2-t007` (sha256 bd6057aef3ec...), public Kimi K3, round 2 turn 7. A different mechanism:
   finiteness of the "permanents" (minimal elements of S_infinity, identified with a family C of finite prime sets) is
   derived from a theorem "an antichain of finite sets that is pairwise intersecting and self-dual is finite". The
   theorem's proof extracts, by Zorn's lemma, a minimal transversal T of C contained in I u Z_omega and concludes
   "T in C by (iii)" (self-duality), whence T is finite. But Claim 3.2, which establishes self-duality, is proved only
   for finite minimal transversals (its proof forms the product pi(T) of the primes in T), while the Zorn-extracted T
   may be infinite; the step is circular in exactly the case it needs. This is not a counterexample to the theorem's
   statement (the verifier's later re-grade notes that the family above fails self-duality and so does not threaten
   the theorem), but the argument as written is invalid at this step. Record: the public verifier's first pass graded
   the file 3/7 with this as the fatal defect (its 7/7 re-grade describes "the previously fatal gap (finite-only
   self-duality applied to a provably infinite minimal transversal)"), and the harness quoted it to the next session:
   "the Step-4 self-dual-clutter theorem was applied to a Zorn-extracted minimal transversal that is provably
   INFINITE in the needed case, while self-duality was only established for FINITE minimal transversals. ... close
   the finiteness crux rigorously". Ratings: layer 0 finiteness 2 ("complete, correct"), GLM re-rating 2, Kimi 2;
   written S = 2, valid S = 1. The lineage's main session replaced the step by a compactness theorem ("every
   transversal of C contains a finite transversal"), verified line by line in the 7/7 re-grade; that text
   (`p6-kimi-k3-main-t005`) is S = 2 in every layer.

Consequences.

- Under the written layer the corpus has one regressing lineage, public Kimi on Problem 6 (2 -> 1 from round 2 to
  round 3); v3 additionally reported the GPT-default 2 -> 1 produced by the final-only override. Under the valid
  layer both disappear: public Kimi runs 0 -> 1 -> 1 -> 2 -> 2 and GPT default 0 -> 1 -> 1. Both "regressions" were
  artifacts of crediting a refuted finiteness mechanism at the earlier checkpoint; the round-3 Kimi file that marked
  finiteness "not proved" described its state more accurately than the round-2 file that claimed it.
- Public Kimi's first valid S = 2 on Problem 6 is the main-session turn-5 write (`p6-kimi-k3-main-t005`), the
  session whose prompt carried the critique quoted above. The pilot's S = 1 seed (`p6-kimi-k3-round3-t009`, sha256
  01814ca40bb4...) is byte-identical to the file that session first read.
- The valid layer adds three S = 1 checkpoints on Problem 6 relative to the written layer and removes one final at
  S = 2 (GPT default). `sensitivity.json` carries the counts per layer.
- Both annotators credited the false lemma in both GPT-default texts and the invalid step in the Kimi text. The
  instrument measures what is written, not what is true; these three entries are the paper's evidence for that limit.

## 3. Problem 2: route taxonomy and applicability

Published route available to us. Chen's notes give one solution for Problem 2. With X = BK n AC and Y = CL n AB, the
three angle conditions become cyclic quadrilaterals (BYXC, equivalently MYXN; XNLB; YMKC). Using power of a point
only: the second intersections of XK, XC with circle (YMKC) and of YL, YB with circle (XNLB) are located (B', C' are
the midpoints of AY, AX); with E, F the midpoints of BY, CX, the points A, K, L, E, F, K', L' are concyclic; the
powers of M and N with respect to circle (AEF) are equal (MA * ME = NA * NF), hence OM = ON. This is the synthetic
key-circle route: a circle through A and the midpoints of BY and CX, proved to contain K and L, with OM = ON from
equal powers of M and N. It is exactly the (T) / (K) / (F) obligation structure of the Problem-2 rubric. The
rubric's alternative description of the key circle, the circle with diameter AZ where Z is the centre of (BCXY), is
the same circle: ZE is perpendicular to the chord BY and ZF to the chord CX, so E and F lie on the circle with
diameter AZ. Chen's notes contain no trigonometric, complex-coordinate or Cartesian solution for Problem 2 and no
remark on alternative routes. The AoPS thread linked from the notes could not be consulted: the fetched page
(scratch copy `aops_p2.html`) is a Cloudflare block page with no thread content. So the classes "trigonometric" and
"coordinates" below are read off the texts and the annotators' notes, not matched to a specific published solution.

Classification (`p2_routes.json`: from the final retained text of each lineage and both annotators' mechanism notes,
fixed before any count was regenerated, applied to every checkpoint of the lineage).

| Lineage | Final text (sha256) | Route of the final text | Matches the published route | Rubric applies |
|---|---|---|---|---|
| public Claude Fable 5 | 9fa7a3d46101... | synthetic: X, Y and the three concyclicities by directed angles (Claims 4.1-4.3, tangency cases included); an affine function pow(., omega) - pow(., omega_K) - pow(., omega_L) + pow(., omega_1) vanishing at A, K, L replaces the explicit key circle; finish from pow(B, omega), pow(C, omega) and the median-length formula | yes: same translation step; the key circle is replaced by an equivalent power identity and the finish is a variant of "equal powers of M and N" (public verifier: "a complete synthetic solution") | yes |
| our GPT-5.6-Sol ultra | eb189909d1bd... (v2; v1 4ed2348c5f6d...) | synthetic: the circle Omega with diameter AZ shown to contain K and L by radical axes; O is the midpoint of AZ; MO = BZ/2 = CZ/2 = NO | yes: the same key circle, with the rubric's second finish | yes |
| public GPT-5.6-Sol Pro | b249cd31eb8a... | trigonometric: sine-rule encoding of the three angle conditions; OM = ON reduced to cd - be = (c^2 - b^2)/2 and closed by a trigonometric identity | no | N/A |
| public GPT-5.6-Sol max | 4efadec329eb... | Cartesian coordinates; circumcircle of AKL with a polynomial certificate | no | N/A |
| public GPT-5.6-Sol xhigh | 848a04cd9dd2... | complex coordinates; determinant factorisation lemma; equal powers of M and N | no (the finish coincides with the published one, the key-circle step is a coordinate computation) | N/A |
| public GPT-5.6-Sol default | 74cde2147129... | complex setup with sine-rule coordinates; circle (AKL) by explicit equations; crux H = 0 asserted | no | N/A |
| public Kimi K3 | e2a57ad245a0... | law-of-sines / power-of-a-point coordinates: four sine relations eliminated to quadratics; powers of B and C w.r.t. (AKL); Apollonius median identity | no | N/A |
| public DeepSeek V4 Pro | 406f7046d596... | complex coordinates (plan, nothing executed) | no | N/A |
| public Muse Spark 1.1 | bed5ff37042f... | coordinate reduction OM = ON iff O_x = 0; angle conditions sketched | no | N/A |
| public Grok 4.5 | 89e724008cfc... | undetermined (spiral similarities, reflection, coordinates listed; nothing executed) | no | N/A |
| our GLM-5.2 | 548b8f8d8940... | sine-rule parametrisation; decisive identity certified in external CAS files | no | N/A |
| our Nemotron | ec1ad94b7a34... (last of six candidates) | complex reality conditions and spiral similarity, unexecuted; crux KA = KB false in general | no | N/A |

Consequence. The synthetic rubric (obligations K and F) applies to 2 of the 12 Problem-2 lineages; the other 10 are
route N/A: their S values are displayed in the matrix but excluded from agreement and transition counts. Within the
two applicable lineages both end at S = 2, both crossings lie inside the record, and there is no S = 1 checkpoint
and no regression in any layer. Problem 2 therefore contributes almost nothing to the trajectory analysis under this
rubric. This is a limitation of a route-specific obligation set on a geometry problem with several workable routes,
and the paper states it as such rather than scoring non-synthetic proofs against synthetic obligations, which is what
produced v3's two Problem-2 "disagreements" (GPT-5.6-Sol max at S = 0 with grade 7; Kimi K3 at S = 1 with grade 7).
The lower inter-annotator agreement on Problem 2 (kappa 0.64, against 0.88 and 0.95) is consistent with a rubric
applied to texts it does not fit.
