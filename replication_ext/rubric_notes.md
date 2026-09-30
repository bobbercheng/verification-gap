# How the P1, P4, P5 closure rubrics were chosen (written before the ratings were launched)

Source of truth: the published solutions in Evan Chen's IMO 2026 Solution Notes (3 September 2026), read against the
official problem statements. As for P2/P3/P6, each rubric fixes two load-bearing universal obligations (quantified over all
instances, unavoidable for the route) mapped onto the JSON fields `lower_bound` / `upper_bound`, a preparatory `reduction`
field, an `answer` field, `wrong_answer_stated`, and `notes`; S counts the obligation fields scored 2. The grading
instructions are those of the earlier rubrics: grade only what is written; a named or sketched mechanism, or one proved only
for special cases, scores 1; a mechanism resting on a false lemma scores 0.

## Problem 1 (gcd / lcm blackboard) -- one published route, two clear obligations
Chen's solution has exactly two parts, each a universal statement. Part (a): a move either permanently increases the number
of 1s (gcd = 1) or decreases the product of the board (gcd > 1), so every play terminates; combined with the observation that
a move never outputs two 1s, exactly one integer > 1 remains. Part (b): for every prime p the gcd of the p-adic valuations
on the board is invariant under every move (gcd(x, y - x) = gcd(x, y)), so v_p(M) is the gcd of the initial valuations and
M is determined. These are the two obligations: `lower_bound` = (T) termination for every play plus exactly one survivor,
`upper_bound` = (I) invariance for every move and prime. The `reduction` field (E) is the per-prime description of a move,
(x, y) -> (min(x, y), |x - y|), together with "at least one output exceeds 1", which both parts use. The `answer` field is the
explicit value M = prod_p p^{gcd_i v_p(a_i)}; the problem does not ask for it, but every published write-up states it, and it
plays the role the closed form plays on P3. Known failure modes named in the rubric: a false monovariant ("the product strictly
decreases at every move"), and the fallacy caught in our own P1 audit ("a quantity above 1 that never increases stays above
1"), both scored 0 as false lemmas; the missing or circular "at least one survivor" step is scored 1 (a gap).
Route ambiguity: none of substance. Other monovariants (lexicographic pairs, potential functions) are all instances of (T);
the invariant in (I) can be phrased as the "2026-number Euclidean algorithm"; the rubric names these as examples only.

## Problem 4 (triangle-cutting game) -- constructions differ, obligations stated route-neutrally
The answer is theta = 180/n for integers n >= 2. Chen's solution proves the two directions of the characterization: (W) a
winning strategy for Mulan when theta = 180/n (multiples-of-theta lemma by induction, an altitude cut to a right triangle,
then a cut producing an angle k*theta with 45 < k*theta <= 90), and (A) an avoidance strategy for Shan-Yu when theta is not
of that form (safe angles are non-multiples of theta; a safe triangle can always be cut so that one piece is safe, because a
sum or difference of a safe and an unsafe angle is safe, using that 180 is not a multiple of theta). The public 7/7 write-ups
use other constructions for (W) (e.g. round-up distances to the next multiple of theta with a halving lemma) and other
starting triangles for (A) (e.g. equilateral), so the rubric states the obligations independently of the construction: each
direction must be a strategy proved against EVERY choice of the opponent, including the discard step (both pieces of Mulan's
cut must be winning positions) and the n = 2 case. `lower_bound` = (W), `upper_bound` = (A). The `reduction` field (K) is the
multiples-of-theta lemma (or an equivalent cut / realizability lemma), the preparatory tool every published construction uses.
Known failure modes named in the rubric: resolving only theta = 90 (scored 1 as a special case), ignoring the discard choice
(scored 1 as a gap), a strategy that assumes Shan-Yu keeps a particular piece or an invariant not preserved by cuts (0),
and the wrong characterizations that appeared in the public campaign (only 90 degrees; the complement of the correct set),
which set `wrong_answer_stated`.

## Problem 5 (functional inequality) -- two published routes for necessity, obligations stated route-neutrally
The answer is f(x) = x + c, c >= 0. Chen gives the verification (QM-AM-GM on x and y + c) and two necessity arguments: an
iterated one (orbits are arithmetic progressions; any two positive common differences are equal; a separation lemma
|x - y| > D excludes functions with both fixed and non-fixed points) and a calculus one (a local estimate f(y) = f(x) +
(y - x) + O((y - x)^2) for every x, hence f' = 1). The public 7/7 write-ups use yet other descents. The two directions of
"determine all functions" are therefore taken as the obligations, as the two bounds are on P3: `lower_bound` = (V) sufficiency
for all x, y and all c >= 0, and `upper_bound` = (N) necessity, i.e. a complete argument that f(x) - x is one constant for
all x, with the fixed-point / identity case handled rather than assumed away (this is where partial write-ups typically stop,
and what distinguishes the two published routes only in method). The `reduction` field (S) is the structural identity
f(f(t)) = 2f(t) - t (AP orbits, nonnegative difference), which every route derives first from the two inequalities at
(x, y) = (f(t), t). Known failure modes named in the rubric: concluding f(x) = x only (the public Grok run; wrong answer),
deducing f(x) = x + c from the structural identity alone (0), and proofs under an unproved extra assumption (continuity,
monotonicity, differentiability, surjectivity, injectivity, "no fixed points"), which score 1.
Design consequence: on P5 the two obligations are unequal in difficulty (sufficiency is one line), so S = 1 will often mean
"answer verified, necessity incomplete"; this is the intended reading and is stated here so it is not mistaken for a
rater-dependent state as on P3.

## What was not done
No validity layer or adjudication is applied on P1/P4/P5 (no independent record of refuted steps exists for these texts);
no human read the texts for this replication; the rubrics were written knowing the published solutions, as for P2/P3/P6.
