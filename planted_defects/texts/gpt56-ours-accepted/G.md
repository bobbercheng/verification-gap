# IMO 2026 Problem 3 — complete candidate solution

For every positive integer \(n\), the exact optimal guarantee is

\[
\boxed{c_n=\frac{2^n}{2^{n+1}-1}}.
\]

The main point is an exact refinement lemma: after Liu creates initial interval
lengths \(a_1,\ldots,a_q\), the least drafting discrepancy that Xiang can
produce with at most \(q-1\) further cuts is the least gap between two distinct
subset sums of the \(a_i\).

## 1. The value of the drafting phase

Let the final positive piece lengths, in nonincreasing order, be

\[
x_1\ge x_2\ge\cdots\ge x_r>0,
\qquad
D(x)=x_1-x_2+x_3-x_4+\cdots.
\]

Set \(D(\varnothing)=0\).

**Drafting lemma.** Under optimal play, the first drafter's total is

\[
x_1+x_3+x_5+\cdots=\frac{1+D(x)}2.
\tag{1}
\]

To prove optimality, let \(V(x)\) be the moving player's final advantage
(their total minus the other player's total). Induct on \(r\), starting with
the empty multiset. If the moving player chooses \(x_i\), the induction
hypothesis makes the resulting advantage

\[
A_i=x_i-D(x_1,\ldots,\widehat{x_i},\ldots,x_r).
\]

Choosing \(x_1\) gives \(A_1=D(x)\). Direct cancellation gives

\[
D(x)-A_i=
\begin{cases}
2\bigl((x_1-x_2)+\cdots +(x_{i-2}-x_{i-1})\bigr),&i\text{ odd},\\[2mm]
2\bigl((x_1-x_2)+\cdots +(x_{i-1}-x_i)\bigr),&i\text{ even}.
\end{cases}
\]

(For \(i=1\), the first sum is empty.) Both expressions are nonnegative.
Thus a largest remaining piece is optimal at every turn and \(V=D(x)\).
Because the two totals sum to \(1\), (1) follows. Ties do not affect the
argument.

## 2. Exact refinement lemma

For positive numbers \(a_1,\ldots,a_q\), define

\[
\Gamma(a_1,\ldots,a_q)
=\min_{A\ne B}
\left|\sum_{i\in A}a_i-\sum_{i\in B}a_i\right|,
\tag{2}
\]

where \(A,B\) range over all subsets of \(\{1,\ldots,q\}\), including the
empty subset.

**Refinement lemma.** Suppose \(a_1,\ldots,a_q\) are the lengths of Liu's
initial intervals. Among all refinements made with at most \(q-1\) new cuts,
the minimum possible final discrepancy \(D\) is exactly \(\Gamma\).

### Lower bound in the lemma

Suppose Xiang makes \(k\le q-1\) effective cuts. There are \(r=q+k\) positive
final pieces. Sort them as \(x_1\ge\cdots\ge x_r\), pair consecutive ranks

\[
(x_1,x_2),(x_3,x_4),\ldots,
\]

and leave \(x_r\) unpaired if \(r\) is odd. Make a multigraph on the \(q\)
original intervals: each pair is an edge joining the two original intervals
containing its pieces. Loops and parallel edges are allowed. This graph has

\[
\left\lfloor\frac r2\right\rfloor
\le q-1
\]

edges on \(q\) vertices. Summing \(e_C-v_C\) over connected components gives a
negative number, so some component satisfies \(e_C<v_C\). Since every connected
multigraph has \(e_C\ge v_C-1\), this component has \(e_C=v_C-1\) and is a tree
(an isolated vertex counts as a tree).

Bipartition one such tree component into vertex sets \(U,W\). Give vertices in
\(U\) sign \(+1\), vertices in \(W\) sign \(-1\), and all other vertices sign
\(0\). Expanding each \(a_i\) as the sum of its descendant final pieces, every
paired edge in the chosen component contributes, up to sign,
\(x_{2j-1}-x_{2j}\). If the unpaired last piece belongs to this component, it
contributes \(\pm x_r\). Therefore

\[
\left|\sum_{i\in U}a_i-\sum_{i\in W}a_i\right|
\le
\sum_j(x_{2j-1}-x_{2j})+
\mathbf 1_{r\text{ odd}}x_r
=D(x).
\tag{3}
\]

The two color classes, viewed as subsets of the real interval labels, are
distinct. This is also true for a one-vertex component, when one class is empty.
Thus (2) and (3) give

\[
D(x)\ge\Gamma.
\tag{4}
\]

This argument includes fewer than \(q-1\) cuts, repeated cutting inside one
initial interval, loops, parallel edges, and both parities of \(r\).

### Upper bound in the lemma

Choose distinct subsets attaining (2), cancel their intersection, and swap
them if necessary. We obtain disjoint sets \(A,B\), not both empty, such that

\[
s_A:=\sum_{i\in A}a_i\ge s_B:=\sum_{i\in B}a_i,
\qquad s_A-s_B=\Gamma.
\tag{5}
\]

First suppose \(B\ne\varnothing\). By overlaying the intervals indexed by \(A\)
and those indexed by \(B\) along a common refinement of a row of length
\(s_B\), and bisecting every initial interval outside \(A\cup B\), Xiang can
make the common-refinement cells occur in equal pairs, one in each row, leave
unpaired pieces only in the \(A\)-tail, of total length \(s_A-s_B=\Gamma\),
and use at most \(q-1\) cuts in total (standard; details omitted).

If \(B=\varnothing\), leave the \(A\)-intervals as residual pieces and bisect
every interval outside \(A\). This uses \(q-|A|\le q-1\) cuts, and again the
residual pieces have total length \(s_A=\Gamma\).

In either case, the final multiset consists of equal pairs plus residual pieces
of total length \(\Gamma\). Deleting two equal entries from a sorted list does
not change \(D\): the two copies may be adjacent within their tie block, their
contributions cancel, and all later ranks shift by two. After all equal pairs
are deleted, the discrepancy of the residual multiset is at most its total.
Consequently \(D\le\Gamma\), which together with (4) proves the refinement
lemma.

All overlay cuts described above lie strictly inside an original interval.
An overlay boundary already equal to a Liu mark requires no new mark, so
coincidences only reduce the cut count.

## 3. Xiang's upper bound

Let Liu's effective marks create \(q\le n+1\) positive initial intervals.

If \(q\le n\), Xiang bisects every interval, using \(q\le n\) marks. Every
final length then occurs in an equal pair, so \(D=0\) and Liu's drafting value
is exactly \(1/2\).

It remains to treat \(q=n+1\), with initial lengths
\(a_1,\ldots,a_q\). Their \(2^q\) subset sums, counted with multiplicity, lie
in \([0,1]\) and include \(0\) and \(1\). Sort them:

\[
0=s_0\le s_1\le\cdots\le s_{2^q-1}=1.
\]

The \(2^q-1\) consecutive gaps sum to \(1\), so one is at most

\[
\frac1{2^q-1}=\frac1{2^{n+1}-1}.
\]

The corresponding occurrences come from distinct subsets, even if the gap is
zero. Hence

\[
\Gamma(a_1,\ldots,a_q)\le\frac1{2^{n+1}-1}.
\tag{7}
\]

By the refinement lemma, Xiang can use at most \(q-1=n\) marks and make
\(D\) no larger than the right side of (7). From (1), Liu can then receive at
most

\[
\frac12\left(1+\frac1{2^{n+1}-1}\right)
=\frac{2^n}{2^{n+1}-1}.
\tag{8}
\]

## 4. Liu's matching lower bound

Put

\[
\delta=\frac1{2^{n+1}-1}.
\]

Liu uses exactly \(n\) marks to create, in order, the interval lengths

\[
\delta,2\delta,4\delta,\ldots,2^n\delta.
\tag{9}
\]

Thus his marks are \((2^j-1)\delta\) for \(1\le j\le n\), all distinct and
strictly inside the stick. Binary expansion says that the subset sums of (9)
are exactly, and uniquely,

\[
0,\delta,2\delta,\ldots,(2^{n+1}-1)\delta=1.
\]

Therefore \(\Gamma=\delta\). Xiang has at most \(n=(n+1)-1\) cuts, so the
lower half of the refinement lemma gives \(D\ge\delta\) for every one of his
marking choices. Liu then follows the optimal drafting strategy from Section 1
and obtains at least

\[
\frac{1+\delta}{2}
=\frac{2^n}{2^{n+1}-1}.
\tag{10}
\]

Equations (8) and (10) prove the asserted value.

## 5. Falsification record and mandatory prior examples

Three structurally different hypotheses were tested before accepting the
binary value.

1. **Equal-cell hypothesis:** \(c_n=(n+1)/(2n+1)\). The proved upper bound gives
   \(c_2\le4/7<3/5\), so this formula is false. Moreover, its previously
   proposed Liu strategy is directly refuted: if Liu marks \(1/5,3/5\), Xiang
   marks \(\varepsilon,1/10\), where \(0<\varepsilon<1/20\). The physical pieces are

   \[
   \varepsilon,\quad \frac1{10}-\varepsilon,\quad\frac1{10},
   \quad\frac25,\quad\frac25.
   \]

   In decreasing order Liu receives
   \(2/5+1/10+\varepsilon=1/2+\varepsilon\), which is below \(3/5\) for,
   say, \(\varepsilon=1/100\), and tends to \(1/2\). In fact Xiang can use just
   the one mark \(1/10\), producing \(1/10,1/10,2/5,2/5\) and holding Liu to
   exactly \(1/2\). Thus the old proposed lower-bound strategy is rigorously
   refuted, not merely numerically doubted.

2. **Universal-pairing hypothesis:** \(c_n=1/2\). This fails for \(n=1\).
   Liu cuts into \(1/3,2/3\). If Xiang cuts the \(1/3\) interval, Liu first
   takes the intact \(2/3\). If Xiang cuts the \(2/3\) interval, the second
   largest of the three final pieces is at most \(1/3\), so Liu's odd-ranked
   sum is at least \(1-1/3=2/3\). With no effective Xiang cut, Liu also takes
   \(2/3\). Hence Liu guarantees \(2/3>1/2\).

3. **Binary subset-spacing hypothesis:**
   \(c_n=2^n/(2^{n+1}-1)\). It was attacked by allowing Xiang fewer cuts,
   repeated cuts in one initial interval, arbitrary interlacing of descendants,
   even and odd final piece counts, equal subset sums, and coincident virtual
   overlay boundaries. The refinement lemma handles all these cases and the
   subset-sum pigeonhole bound plus (9) prove both directions. This hypothesis
   survives and is the theorem proved above.

A related equal-initial-interval heuristic also fails badly. If Liu creates an
even number of equal pieces, Xiang uses no cut and the pieces cancel in equal
pairs, giving Liu \(1/2\). If Liu creates an odd number, Xiang bisects one
interval; the remaining equal full pieces and the two equal halves again occur
in pairs, also giving \(1/2\). Thus “at most \(n\)” marks is an essential part
of the analysis.

The prior grid example is reproduced exactly: on a stick of \(56\) grid units,
Liu marks \((7,21)\), Xiang marks \((8,38)\), and the physical lengths are
\((7,1,13,17,18)\). Sorting gives Liu
\((18+13+1)/56=32/56=4/7\), in agreement with the theorem. This is evidence,
not part of the proof.

## 6. Boundary cases and assumptions

- The stated problem has \(n\ge1\). Formally the same formula gives \(c_0=1\),
  the value of the uncut one-piece game.
- Only effective interior marks matter. If endpoints are considered points on
  the stick, marking them creates no new positive piece and can be discarded.
- A player may use fewer than \(n\) marks. The graph lower bound explicitly
  allows this; Xiang's constructions use no more than the permitted number.
- All actual marks must be distinct. The constructed marks lie in disjoint
  interval interiors or at distinct internal overlay boundaries; a boundary
  already marked by Liu is simply not marked again.
- Equal final lengths may be ordered arbitrarily inside their tie blocks. Both
  the drafting value and \(D\) are unchanged.
- No numerical experiment is used to infer either bound. The exact finite-grid
  checks in `grid_checks.py` are only independent falsification evidence.

The first values are

\[
c_1=\frac23,\qquad c_2=\frac47,\qquad c_3=\frac8{15},
\qquad c_4=\frac{16}{31},
\]

and \(c_n\downarrow1/2\).
