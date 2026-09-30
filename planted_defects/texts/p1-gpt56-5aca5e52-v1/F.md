# Candidate solution

Status: **complete**.

## Conclusion

Write the initial integers as \(A_1,\ldots,A_{2026}\). Every sequence of legal moves is finite and ends with exactly one entry \(M>1\). More precisely,
\[
\boxed{\displaystyle
M=\prod_{p}p^{\,\gcd\bigl(v_p(A_1),\ldots,v_p(A_{2026})\bigr)} },
\tag{1}
\]
where \(v_p(r)\) is the exponent of \(p\) in \(r\), \(v_p(1)=0\), and
\(\gcd(0,\ldots,0)=0\). Only primes dividing at least one \(A_i\) contribute
to the product, so it is finite. Formula (1) depends only on the initial
board and therefore proves the required choice-independence.

## Proof of termination

At any stage let the entries be \(x_1,\ldots,x_{2026}\), and set
\[
P=\prod_{i=1}^{2026}x_i,\qquad
K=\#\{i:x_i>1\}.
\]
Order pairs \((P,K)\) lexicographically, with \(P\) as the first coordinate.

Consider a legal move on entries \(m,n>1\), and put \(g=\gcd(m,n)\). The
product of the two new entries is
\[
g\cdot\frac{\operatorname{lcm}(m,n)}g
=\operatorname{lcm}(m,n)=\frac{mn}{g}.
\]
Consequently the new board product is \(P'=P/g\).

- If \(g>1\), then \(P'<P\).
- If \(g=1\), the new entries are \(1\) and \(mn\). Thus \(P'=P\), while
  exactly two nonunits have been replaced by one, so \(K'=K-1\).

Hence \((P,K)\) strictly decreases after every move. This order is
well-founded here: \(P\) is a positive integer and never increases, so it
can strictly decrease only finitely many times; while \(P\) is fixed, every
move decreases the integer \(K\). Thus no infinite sequence of legal moves
exists, regardless of how the pairs are chosen.

When the process stops, at most one entry is greater than \(1\), because
any two such entries would form a legal pair. On the other hand, the number
\(K\) of nonunits never increases, and initially \(K=2026\). A nonnegative integer that
never increases and starts at a positive value can never reach \(0\); hence \(K\ge1\) at
every stage, so at least one nonunit remains at every stage. Therefore the terminal board
has exactly one nonunit; call it \(M\).

## Proof that the value is forced

Fix a prime \(p\). For a current entry \(x_i\), write
\[
e_i=v_p(x_i).
\]
Suppose the selected entries have \(p\)-adic exponents \(a\) and \(b\).
The exponents in the two new entries are
\[
v_p(\gcd(m,n))=\min(a,b)
\]
and
\[
v_p\left(\frac{\operatorname{lcm}(m,n)}{\gcd(m,n)}\right)
=\max(a,b)-\min(a,b)=|a-b|.
\]
Thus a move replaces
\[
(a,b)\quad\text{by}\quad\bigl(\min(a,b),|a-b|\bigr).
\tag{2}
\]
If, say, \(a\le b\), the Euclidean identity gives
\[
\gcd(a,b)=\gcd(a,b-a)
=\gcd\bigl(\min(a,b),|a-b|\bigr).
\tag{3}
\]
This remains valid when one or both exponents are zero. Since the gcd of
the selected pair of exponents is preserved, associativity of gcd shows
that
\[
G_p=\gcd(e_1,\ldots,e_{2026})
\tag{4}
\]
is invariant under every move.

At the terminal board, all entries except \(M\) are \(1\). Its \(p\)-adic
exponent list is therefore
\[
v_p(M),0,\ldots,0.
\]
Using \(\gcd(c,0,\ldots,0)=c\), invariance of (4) yields
\[
v_p(M)=\gcd\bigl(v_p(A_1),\ldots,v_p(A_{2026})\bigr)
\]
for every prime \(p\). A prime absent initially has an all-zero exponent
list and remains absent. Hence only finitely many primes occur, and unique
factorization now gives exactly (1). This completes both parts of the
problem.

## Boundary and degeneracy audit

- The entries are attached to places. Equal values in different places
  are allowed: \((m,m)\) becomes \((m,1)\), and (2) becomes
  \((a,a)\mapsto(a,0)\).
- For coprime selected entries, \((m,n)\mapsto(1,mn)\); this is precisely
  the case where \(P\) stays fixed and \(K\) falls.
- Zero valuations do not force \(G_p\) to be zero:
  \(\gcd(0,e)=e\). Thus, for example, a prime occurring in only one initial
  entry persists with that entry's exponent. If all valuations are zero,
  the stated all-zero convention applies.
- The restriction that both selected entries exceed \(1\) is used. If
  selecting \(1\) were allowed, a pair \((1,n)\) would be unchanged, but
  such a move is not legal in the problem.

## Hypotheses and falsification

The following structurally different possibilities were tested before
selecting the proof mechanisms above.

1. **Additive-size hypothesis:** the sum of the board entries strictly
   decreases. Refuted by
   \((2,3)\mapsto(1,6)\), for which the selected sum rises from \(5\) to
   \(7\).
2. **Multiplicative-size hypothesis:** the board product strictly
   decreases. Refuted by the same coprime move: both products equal \(6\).
   This is why the second coordinate \(K\) is needed.
3. **Ordinary-lcm outcome hypothesis:** the final value is the initial
   lcm. Refuted by the complete legal sequence
   \[
   (4,8)\mapsto(4,2)\mapsto(2,2)\mapsto(2,1),
   \]
   whose terminal value is \(2\), whereas the initial lcm is \(8\).
4. **Coupled descent hypothesis:** \((P,K)\) always strictly decreases.
   Attempts using coprime inputs, equal inputs, and inputs with a proper
   nontrivial gcd leave no exceptional case; the two-case calculation in
   the termination proof establishes it.
5. **Primewise Euclidean hypothesis:** the gcd of the exponent vector for
   each prime is invariant and determines the terminal value. The cases
   \((0,b)\), \((a,a)\), and \((0,0)\) respectively map to
   \((0,b)\), \((a,0)\), and \((0,0)\), and identity (3) proves the claim
   in general.

## Computational evidence (not used as proof)

The reproducible script **verify_small.py** exhaustively explored all move
trees from the 1,278 multisets of lengths \(2\) through \(5\) whose entries
lie from \(2\) through \(9\). Across 9,607 memoized reachable states, every
terminal value was unique and agreed with (1). The script also explicitly
checks the three counterexamples above. This finite experiment is only a
falsification check; the proof is the descent and invariant argument given
above.
