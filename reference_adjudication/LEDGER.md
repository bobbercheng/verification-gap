# Reference ledger for the disputed problems (P1, P3, P5, P6), written 2026-09-06 14:40 UTC

Primary reference: Evan Chen, IMO 2026 Solution Notes, version updated 3 September 2026 (`chen2026notes` in refs.bib; the
notes state they draw on the official and shortlisted solutions and give AoPS thread links per problem). Secondary
cross-check: the AoPS wiki solution pages (community-written); fetched through a browser because the site blocks scripts.
Status of the cross-check: P5 fetched (three community solutions and a video link); P3 supplied by the author as a saved page
(14:50 UTC; one community solution and a video link); P6 and P1 supplied by the author as saved pages (15:05 UTC; two community
solutions each). All four pages of the disputed set are therefore cross-checked; none changes a ledger statement.

A ledger statement is one that every complete proof must establish (route-independent), or, where routes differ, one that the
cited route establishes and that a text following that route must therefore establish. The ledger is used to adjudicate a
confirmed local error: which statement it affects, and whether the text establishes that statement elsewhere. It is not a
grading scheme.

## P5 (functional inequality). Answer: f(x) = x + c, c >= 0.
Chen, pp. 13-14. Statements:
- L5.1 Sufficiency: for every c >= 0 and all x, y > 0 the chain holds; Chen: "immediate by QM-AM-GM on x and y + c", with the
  middle term written as (x + c) + y over 2, i.e. (x + y + c)/2.
- L5.2 Structural identity: f(f(t)) = 2 f(t) - t for every t > 0, from P(f(t), t) and Q(f(t), t); hence S(t) = (t, f(t), ...)
  is an arithmetic progression.
- L5.3 Nonnegative difference: the common difference of S(t) is nonnegative for every t, "since all terms of the sequence
  are positive". Chen proves this before anything else in the necessity argument.
- L5.4 Equal positive differences: if the differences A, B of S(x), S(y) are both positive then A = B (iterate comparison
  using Q only).
- L5.5 Fixed points: if f is not the identity there is D > 0 with f(x) in {x, x + D} for all x, and f(x) = x + D and f(y) = y
  force |x - y| > D (from P(x, y) and Q(y, x)), hence f(t) = t + D on [x - D, x + D] and everywhere.
  (Calculus route alternative: f(y) = f(x) + (y - x) + O(|y - x|^2) for each x, so f' = 1; needs a Taylor estimate.)
AoPS cross-check (community): Solution 3 follows the arithmetic-progression route and states L5.3 ("increment ... must not be
negative, otherwise x_n eventually would become negative"); its final step is sketched. Solution 1 and Solution 2 are NOT
valid as written: Solution 2's Lemma 1 concludes f(x)+y = f(y)+x from two inequalities that share a lower bound ("the converse
of AM-GM proves that the two values must be equal"), which does not follow; Solution 1 asserts "as long as f(x) is not of
the form x + b, g is injective" without proof. So the wiki agrees with Chen on the answer and on L5.1-L5.3 and cannot be used
as a reference for L5.4-L5.5. (This is itself an observation for the paper: two of three community solutions to P5 contain an
invalid inference of the kind the model texts contain.)
Mapping of the v6 disputes:
- p5-deepseek-v4-pro-main-t033 / t038 (negative g never excluded): the missing statement is L5.3; the texts go from "at most
  one positive value" to V in {0} or {0, c}. Adjudication: L5.3 is required (Chen proves it explicitly and uses it); the
  texts do not establish it anywhere (checkers found no anchored passage). Status: obligation (N) not established as written.
- p5-nemotron-2587b733-v2 (middle term (x+y+2c)/2): affects L5.1; Chen's chain has (x+y+c)/2. The text's next line verifies
  the identity that belongs to the correct chain, so the argument for L5.1 is present and the display is false. Adjudication:
  L5.1 is established by the identity beside a false display; severity depends on the convention (as-written: false line;
  dependency: harmless). Both readings reported.
- Group E control p4 is outside this ledger (P4 not disputed).

## P3 (stick game). Answer: c_n = 2^n / (2^{n+1} - 1), Liu's division 1 : 2 : ... : 2^n.
Chen, pp. 7-10 ("uses some different ideas from the various shortlisted official solutions"). Statements:
- L3.1 Reduction: under optimal play Liu's score is x_1 + x_3 + ... + x_{2n+1} for the sorted lengths; the gap G = x_1 - x_2 +
  x_3 - ... + x_{2n+1} (players may be required to make exactly n cuts with coincident points allowed).
- L3.2 Upper bound (Xiang's reply), universal over Liu's division: for disjoint subsets S, T of Liu's n+1 segments Xiang can
  guarantee G <= |Sigma(S) - Sigma(T)| (mirrored cuts pairing S against T, bisect the rest); by pigeonhole on the 2^{n+1}
  subset sums there are S != T with 0 <= Sigma(S) - Sigma(T) <= 1/(2^{n+1} - 1); prune common elements. (Remark: a
  "take the two longest pieces and bisect or subtract" algorithm fails; counterexample (12.80, 6.42, 5.35, 4.34, 2.09) for n=5.)
- L3.3 Lower bound (Liu's guarantee), universal over Xiang's replies: for any division, G >= Delta := min over nonzero
  sign vectors of |sum eps_i a_i| (tree component of the multigraph on segments, bipartition S, T; |Sigma(S) - Sigma(T)| is a
  signed sum of the d_i, at most G); for 1 : 2 : ... : 2^n, Delta = 1/(2^{n+1} - 1). Alternative for the specific division:
  induction on k showing x_2 + ... + x_{2k} <= 2^{n-1} + ... + 2^{n-k}.
AoPS cross-check for P3 (page saved by the author, one community solution "Solution 1"): agrees with Chen on the answer and on
Liu's division 1 : 2 : ... : 2^n. Its lower-bound argument ("Lemma 2") assumes that Xiang's only plausible reply is to halve every
larger segment, which is exactly the false-guarantee failure mode the public verifier flagged in the model texts (a guarantee
must hold against every reply); its "Lemma 1" is a heuristic, and no upper bound (L3.2) is proved at all. So the wiki page
confirms the answer and the construction and does not provide a valid proof of L3.2 or L3.3; Chen's notes remain the reference.
Mapping of the v6 disputes:
- kimi-k3-round4-t014 (chain value defined by the decreasing order; Theorem 4.2 / Lemma 4.1 yield some ordering): the
  text's route for L3.2 is a "chain value" strategy, not Chen's pairing-by-subsets; Chen's L3.2 needs only the existence of
  the pair (S, T), independent of any ordering. Adjudication: the text's inference is a non-sequitur as written (order
  changes the nested difference, checked); whether the strategy can be repaired by processing the lemma's ordering is a
  repair, not something the text establishes. Status: L3.2 not established as written by this text; repair distance:
  sentence to lemma (disputed between graders).
- kimi-k3-round3-t007 (sketch): L3.1 asserted "by an exchange argument", L3.3 sketched, L3.2 "still open" by the text itself.
  Status: L3.2 absent, L3.3 not written out. Supports the S=0 ratings.
- deedy-gpt-5.6-sol-final (refinement lemma by column sweep): both bounds rest on a lemma whose proof was refuted by
  counterexample (a cut interchanges parity rows below its level; the prescribed first cut need not exist). Status: L3.2 and
  L3.3 not established.
- deedy-grok-4.5-final: Theorem B step refuted (S_n - mu <= S_{n-1} fails at n=2), Theorem C incomplete: L3.3, L3.2 not
  established. deedy-muse-spark-1.1-final, deedy-deepseek-v4-pro-final: wrong answer (n+1)/(2n+1) contradicts L3 answer; the
  constructions' guarantees refuted by exact claiming values (checked).

## P6 (greedy gcd sequence). Statement: a_{n+T} = a_n + L for all n >= 1.
Chen, pp. 16-17. Statements:
- L6.1 Characterization: x appears in the sequence iff gcd(x, a_i) > 1 for every i (equivalently for every i with a_i < x, or
  every ≺-minimal a_i), where a_m ≺ a_n iff m < n and rad a_m | rad a_n.
- L6.2 Large-prime erasure (the heart): if a_n is divisible by a large prime (> a_1^2) then a_n is not ≺-minimal; proof by
  induction on n via the numbers c, qc, q^2 c, ... with q | gcd(a_1, a_n) and the interval [a_1, a_n).
- L6.3 Periodicity: with P the small primes and S(a) the set of small primes dividing a, the sequence is exactly the integers
  a >= a_1 with S(a) in F := {S(a_n)}; membership depends only on a mod prod_{p in P} p; take L = that product and T the
  number of residues that appear.
AoPS cross-check for P6 (page saved by the author; two community solutions): both agree with Chen that finitely many primes
"matter" and that membership is then periodic. Solution 1's finiteness lemma is asserted ("by the Pigeonhole Principle,
eventually new primes will no longer be introduced"), not proved, and its periodicity step is a sketch. Solution 2 selects "key
terms" (terms whose prime support contains no earlier key term's support, i.e. Chen's minimal terms) and proves there are
finitely many by a contradiction argument on a new prime factor, which is the same statement as L6.2 on a different route.
So the wiki confirms L6.1-L6.3 as the required statements; its first solution fails the same as-written test as the model texts.
Mapping of the v6 disputes:
- p6-gpt-5.6-sol-main-t009, p6-deedy-gpt-5.6-sol-final: the texts derive finiteness from the lemma "a pairwise-intersecting
  family of finite sets has finitely many minimal finite transversals", which is false (family F_k = {x_1..x_k, y_k}; checked
  by scripts/witness_checks.py p6-transversals). Chen's L6.2 uses the arithmetic structure (q | gcd(a_1, a_n), the interval
  [a_1, a_n)), which the lemma route never touches; the public verifier also notes pairwise intersection alone is insufficient.
  Status: L6.2 not established (false lemma). Independent of any convention.
- p6-kimi-k3-round2-t007: Claim 3.2 (self-duality) is proved for finite minimal transversals and applied to a Zorn-extracted
  minimal transversal not shown finite; L6.2 needs finiteness of the relevant prime set for all terms. Status: L6.2 not
  established as written (the lineage later replaced the step by a compactness argument; the repaired final was graded 7/7).
- p6-kimi-k3-round1-t021: L6.2 explicitly left open by the text ("prove shrinkage stops"); L6.3 conditional. Status: absent.
- p6-deedy-grok-4.5-final: "(Not yet complete.)"; L6.2 absent.

## P1 (gcd/lcm board). Statement: exactly one integer > 1 survives; M = prod_p p^{gcd_i v_p(a_i)}.
Chen, p. 4. Statements:
- L1.1 Termination: a move with gcd = 1 permanently increases the number of 1s; a move with gcd > 1 decreases the product;
  hence finitely many moves; at the end at most one integer > 1 (two would allow a move) and at least one (a move never
  outputs two 1s: if gcd(m, n) = 1 the second output is mn > 1).
- L1.2 Invariance: for each prime p, gcd(v_p(t_1), ..., v_p(t_2026)) is unchanged by a move, since (x, y) -> (min, |x - y|)
  and gcd(x, y - x) = gcd(x, y); hence v_p(M) = gcd_i v_p(a_i).
AoPS cross-check for P1 (page saved by the author; two community solutions plus an external link): Solution 2 gives the
monovariant argument of L1.1 (a move producing a 1 can happen at most 2025 times; otherwise the product decreases); Solution 1
gives the valuation-gcd invariance of L1.2 (Lemma 3) with a muddled survivor argument (Lemma 2 speaks of the Euclidean
algorithm on exponents). Both agree with Chen on the two required statements and on M.
Mapping of the v6 dispute:
- p1-glm52-2ede1c6b-v1: GPT's earlier S=1 rating claimed the text falsely infers positive valuation gcd from a prime dividing
  some entry, with the board {2,3} as counterexample; but gcd(1, 0) = 1, so the inference is correct and the counterexample
  fails (checked: p1-board --board 2 3 gives M = 6). No proposer or grader objected in v6. Status: L1.1 and L1.2 established;
  the S=2 ratings stand.

## What the references settle and what they do not
- They settle which statements are required (L*.k) and the truth of the specific claims the disputes turn on (L5.3 required;
  the P6 finite-transversal lemma is not part of any valid route and is false; L1.2's inference is valid).
- They do not settle the convention for a false display beside a correct argument (Nemotron): that is a definitional choice
  the paper must state and report both ways.
- Community wiki solutions are not a reliable reference on their own (P5: two of three invalid as written); they are used only
  where they agree with Chen.
