# Solution

Let  
\[
D=2^{n+1}-1.
\]
We shall prove that the required value is
\[
\boxed{c(n)=\frac{2^n}{2^{n+1}-1}=\frac{2^n}{D}}.
\]

Call the intervals determined by Liu’s marks **blocks**, and the intervals after Xiang’s additional marks **pieces**. Zero-length pieces, if endpoint marks are allowed, play no role and may be ignored.

---

## 1. The claiming stage

Suppose the final piece lengths are
\[
p_1\ge p_2\ge\cdots\ge p_m.
\]
Let Liu and Xiang alternately claim pieces, Liu first.

### Lemma 1
Under optimal play, Liu obtains exactly
\[
L=p_1+p_3+p_5+\cdots .
\]

### Proof
Liu can guarantee at least this much by always taking a largest remaining piece. Before Liu’s \(k\)-th turn, only \(2k-2\) pieces have been taken. Hence at least one of the \(2k-1\) largest original pieces remains, so Liu’s \(k\)-th piece has length at least \(p_{2k-1}\). Summing gives Liu at least \(p_1+p_3+\cdots\).

Conversely, Xiang can always take a largest remaining piece. Before Xiang’s \(k\)-th turn, \(2k-1\) pieces are gone, so one of the \(2k\) largest pieces remains. Thus Xiang obtains at least
\[
p_2+p_4+\cdots .
\]
Since the two totals add to \(1\), Liu obtains at most \(p_1+p_3+\cdots\). ∎

Define Liu’s **advantage** by
\[
\Delta=L-(1-L)=2L-1.
\]
Equivalently,
\[
\Delta=p_1-p_2+p_3-p_4+\cdots .
\]
If the pieces are paired consecutively as
\[
(p_1,p_2),\ (p_3,p_4),\ldots,
\]
then
\[
\Delta=\sum_i (p_{2i-1}-p_{2i}),
\]
plus the last unpaired piece if \(m\) is odd.

---

## 2. A signed-sum lemma for refinements

The lower bound will use the following lemma.

### Lemma 2
Suppose a stick is divided into \(n+1\) positive blocks of lengths
\[
a_1,\dots,a_{n+1},
\]
and is then further cut at at most \(n\) points. Let \(\Delta\) be Liu’s advantage in the resulting piece partition. Then there exist coefficients
\[
\varepsilon_i\in\{-1,0,1\},
\]
not all zero, such that
\[
\left|\sum_{i=1}^{n+1}\varepsilon_i a_i\right|\le \Delta.
\]

### Proof
Ignore zero-length pieces. Let the positive final pieces, in nonincreasing order, be
\[
q_1\ge q_2\ge\cdots\ge q_m.
\]
Since at most \(n\) effective cuts were made,
\[
m\le 2n+1.
\]

Pair the pieces consecutively:
\[
(q_1,q_2),\ (q_3,q_4),\ldots .
\]
There are \(r=\lfloor m/2\rfloor\le n\) pairs and, if \(m\) is odd, one leftover piece \(z\). For a pair \((u,v)\), with \(u\ge v\), call \(u-v\) its **deficit**. Then
\[
\Delta=\sum_{\text{pairs}}(\text{deficit})+z,
\]
where \(z=0\) if there is no leftover.

Construct a multigraph \(G\) whose vertices are the \(n+1\) original blocks. For each paired pair of pieces:

- if the two pieces come from different blocks, join those two vertices by an edge;
- if they come from the same block, add a loop at that vertex.

Thus \(G\) has \(n+1\) vertices and at most \(n\) edges.

A connected component containing a cycle or a loop has at least as many edges as vertices. Since the whole graph has fewer edges than vertices, some connected component \(T\) has fewer edges than vertices. Hence \(T\) is a tree, possibly a single vertex.

Every final piece coming from a block in \(T\) is represented either as an endpoint of an edge of \(T\) or as the unique leftover piece. Indeed, a pair joining a block of \(T\) to a block outside \(T\) would give an edge leaving \(T\), while a pair inside one block would give a loop in \(T\).

For an edge \(e=uv\), let \(w_{u,e}\) and \(w_{v,e}\) be the lengths of the two pieces forming that pair, lying in blocks \(u\) and \(v\), respectively. Then, for every vertex \(v\in T\),
\[
a_v=\sum_{e\ni v} w_{v,e}+z_v,
\]
where \(z_v=z\) if the leftover piece lies in block \(v\), and \(z_v=0\) otherwise.

Since \(T\) is a tree, it is bipartite. Choose signs \(\sigma_v\in\{-1,1\}\) on its vertices so that adjacent vertices have opposite signs. Set
\[
S=\sum_{v\in T}\sigma_v a_v.
\]
Substituting the displayed expression for \(a_v\), every edge \(e=uv\) contributes
\[
\sigma_u w_{u,e}+\sigma_v w_{v,e}.
\]
Because \(\sigma_v=-\sigma_u\), this contribution has absolute value
\[
|w_{u,e}-w_{v,e}|,
\]
which is exactly the deficit of that pair. The leftover, if it lies in \(T\), contributes at most \(z\). Therefore
\[
|S|
\le \sum_{e\in T}(\text{deficit of }e)+z
\le \Delta.
\]
Finally, \(S\) is a signed sum of the distinct block lengths \(a_v\), with coefficients \(-1,0,1\), and not all coefficients are zero. ∎

---

## 3. Liu’s strategy

Liu marks the points
\[
x_j=\frac{2^j-1}{D},\qquad j=1,2,\dots,n.
\]
The resulting block lengths are
\[
\frac1D,\frac2D,\frac4D,\dots,\frac{2^n}{D}.
\]

Consider any nontrivial signed sum of these lengths. It has the form
\[
\frac{K}{D},
\qquad
K=\sum_{i=0}^{n}\varepsilon_i2^i,
\]
where \(K\) is an integer. If \(K=0\), then the sum of the powers of \(2\) with coefficient \(+1\) equals the sum with coefficient \(-1\). By uniqueness of binary representation, the two index sets are identical, so all coefficients are zero. Hence every nontrivial signed sum has absolute value at least \(1/D\).

By Lemma 2, whatever Xiang does, Liu’s advantage satisfies
\[
\Delta\ge \frac1D.
\]
Therefore Liu’s total is at least
\[
L=\frac{1+\Delta}{2}
\ge \frac{1+1/D}{2}
=\frac{D+1}{2D}
=\frac{2^n}{D}.
\]
Thus Liu can guarantee at least \(2^n/D\).

---

## 4. Xiang’s strategy against an arbitrary Liu marking

We now show that, against any Liu configuration, Xiang can hold Liu’s advantage to at most \(1/D\).

### Equal pairs cancel

If two equal pieces are added to a piece partition, the alternating advantage does not change: in the sorted list the two equal pieces may be placed consecutively, contributing \(x-x=0\), while every later piece keeps the same parity of position.

Consequently, if all pieces except a subcollection \(R\) can be partitioned into equal pairs, then the advantage of the whole partition is at most the total length of \(R\).

---

### Choosing two subfamilies of blocks

Suppose Liu’s marks produce \(r\le n+1\) positive block lengths
\[
b_1,\dots,b_r.
\]
Pad this list with zeros so that it has exactly \(n+1\) entries. The zero entries are merely bookkeeping devices.

There are
\[
2^{n+1}=D+1
\]
subset sums of these \(n+1\) lengths, all lying in \([0,1]\). Sort them. Since there are only \(D\) gaps between \(D+1\) consecutive values, some two subset sums differ by at most
\[
\frac1D.
\]

Let the corresponding subsets be \(I\) and \(J\). After deleting \(I\cap J\) from both, we obtain disjoint subfamilies \(P\) and \(Q\) whose total lengths differ by
\[
\delta\le \frac1D.
\]
Say \(Q\) has total length \(\delta\) more than \(P\).

---

### Producing equal pairs

First, halve every positive block belonging to neither \(P\) nor \(Q\). Each such block contributes an equal pair.

Let \(p\) and \(q\) be the numbers of positive blocks in \(P\) and \(Q\).

#### Case 1: \(p,q>0\)

Let the total lengths of \(P\) and \(Q\) be \(L\) and \(L+\delta\), respectively.

Imagine concatenating the \(p\) blocks of \(P\) on one ruler, and the \(q\) blocks of \(Q\) on another ruler. On the initial portion \([0,L]\) of both rulers, mark all coordinates that are endpoints of blocks on either ruler, including the coordinate \(L\).

This gives a common refinement of the two rulers: corresponding small intervals on the two rulers have equal lengths. Transfer these coordinates back to the actual blocks. A coordinate that is already an endpoint of a block requires no new cut; otherwise it determines an interior point of a block, where Xiang marks a point.

There are at most
\[
(p-1)+(q-1)+1=p+q-1
\]
such coordinates, hence at most \(p+q-1\) new marks are needed. After these cuts, all pieces coming from \(P\) and \(Q\) form equal pairs, except for one final piece of length \(\delta\) from the longer side.

The total number of Xiang marks used is at most
\[
(r-p-q)+(p+q-1)=r-1\le n.
\]

#### Case 2: one of \(P,Q\) has no positive block

Then the positive blocks on the other side have total length \(\delta\). Leave them uncut and halve all remaining positive blocks. If there are \(k\ge1\) selected positive blocks, this uses \(r-k\le n\) marks. If there are none, then \(\delta=0\) and at least one of the padded zero blocks was selected, so \(r\le n\); halving all \(r\) positive blocks is therefore still legal.

In all cases, the final pieces consist of equal pairs together with an unpaired collection of total length at most \(\delta\). Hence Liu’s advantage is at most \(\delta\le 1/D\).

Therefore Liu’s total in this response is at most
\[
\frac{1+\delta}{2}
\le \frac{1+1/D}{2}
=\frac{2^n}{D}.
\]

---

## 5. Conclusion

Liu has a marking that guarantees
\[
\frac{2^n}{2^{n+1}-1},
\]
and Xiang has a response to every Liu marking that prevents Liu from obtaining more than this amount. Hence the largest guaranteed value is

\[
\boxed{c(n)=\frac{2^n}{2^{n+1}-1}}.
\]