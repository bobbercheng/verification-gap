# Nemotron unresolved-attempt audit

These four entries did not pass the portfolio system's adversarial gate. They
are recorded as negative results, not as proposed solutions.

## Problem 2

Best review scores: correctness 1/4, completeness 1/4, rigor 1/4,
self-containedness 2/4.

The candidate inferred spiral similarities centered at \(L\) and \(K\) from
angle equalities located at other vertices. The required angle and ratio
conditions at the proposed centers were neither given nor derived. The later
composition and complex-coordinate claims consequently had no valid base.

## Problem 3

Best review scores: 1/4 throughout.

The candidate stated the ultimately correct value
\(2^n/(2^{n+1}-1)\), but its proposed upper-bound cuts did not span the stick
for \(n\ge2\), its lower-bound calculation was wrong already at \(n=2\), and
the two main refinement lemmas were unproved. This is a useful example of a
correct answer without a valid solution.

## Problem 4

Best review scores: correctness 1/4, completeness 1/4, rigor 1/4,
self-containedness 2/4.

The strategies for \(60^\circ\), \(90^\circ\), and the defensive case above
\(90^\circ\) were sound. The claimed defensive cycle below \(60^\circ\) fails
immediately at \(30^\circ\), and the range between \(60^\circ\) and
\(90^\circ\) lacked the required exhaustive invariant argument.

## Problem 6

Final review scores: correctness 0/4, completeness 0/4, rigor 1/4,
self-containedness 2/4.

The central statement that every next term's prime support is a minimal hitting
set is false; for example, \(6,8,10\) already contradicts it. The accompanying
CRT construction produced a number coprime to the previous terms rather than
one intersecting them, and it also reversed the growth relation between a
prime and the preceding primorial. Two revision cycles did not repair the
foundation.
