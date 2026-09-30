\[
\boxed{\,c_n=\dfrac{2^n}{2^{n+1}-1}\, } .
\]

Put \(N=2^{n+1}-1\). We prove that Liu can guarantee \(\frac{2^n}{N}\), and that Xiang can always prevent Liu from getting more.

## 1. The claiming phase

Suppose the final piece lengths are
\[
v_1\ge v_2\ge \cdots \ge v_M>0,\qquad \sum_{i=1}^M v_i=1.
\]
Define
\[
\operatorname{odd}(S)=\sum_{i\text{ odd}}v_i,\qquad
\operatorname{even}(S)=\sum_{i\text{ even}}v_i,\qquad
\delta(S)=\operatorname{odd}(S)-\operatorname{even}(S).
\]
Since the total length is \(1\),
\[
\operatorname{odd}(S)=\frac{1+\delta(S)}2.
\]

**Lemma 1.** In the alternating claiming game, Liu can guarantee \(\operatorname{odd}(S)\), and Xiang can guarantee \(\operatorname{even}(S)\). Hence the value of this phase is exactly \(\operatorname{odd}(S)\) for Liu.

**Proof.** Liu first takes \(v_1\). Pair the remaining pieces as
\[
(v_2,v_3),(v_4,v_5),\dots ,
\]
leaving \(v_M\) unpaired if \(M\) is even. Afterwards, whenever Xiang takes a piece whose mate is still unclaimed, Liu immediately takes that mate; otherwise Liu takes the larger member of any completely untouched pair, if one exists, and otherwise takes any largest remaining piece.

We claim Xiang cannot end up owning both members of any pair \((v_{2k},v_{2k+1})\). Consider the first time such a pair is touched. If Xiang is the one who first takes a member of it, then the mate is still unclaimed, so Liu's next move takes that mate. If Liu is the one who first takes a member of it, then Liu keeps a member of the pair. Thus Xiang cannot own both members. So Liu owns at least one member from every pair, and every member of \((v_{2k},v_{2k+1})\) has length at least \(v_{2k+1}\). Including the initial \(v_1\), Liu gets at least
\[
v_1+v_3+v_5+\cdots=\operatorname{odd}(S).
\]

Similarly, Xiang pairs the pieces as
\[
(v_1,v_2),(v_3,v_4),\dots ,
\]
leaving \(v_M\) unpaired if \(M\) is odd. Whenever Liu takes a piece whose mate is free, Xiang takes the mate; otherwise Xiang takes the larger member of an untouched pair if possible, and otherwise any largest remaining piece. The same argument shows Liu cannot own both members of any pair \((v_{2k-1},v_{2k})\), so Xiang gets at least one member from each such pair, hence at least
\[
v_2+v_4+\cdots=\operatorname{even}(S).
\]
Since \(\operatorname{odd}(S)+\operatorname{even}(S)=1\), the value is exactly \(\operatorname{odd}(S)\). ∎

Liu's marks are equivalent to choosing a composition
\[
A=(a_1,\dots,a_m),\qquad a_i>0,\quad \sum a_i=1,\quad m\le n+1.
\]
Xiang then refines this composition using at most \(n\) further cut points. Therefore it remains to determine
\[
\Delta_n:=\sup_{A:\ |A|\le n+1}\ \inf_{\substack{S\text{ refines }A\\ \text{using }\le n\text{ cuts}}}\delta(S),
\]
because then \(c_n=(1+\Delta_n)/2\). We will show \(\Delta_n=1/N\).

We need one cancellation fact.

**Lemma 2.** If a multiset \(S\) can be partitioned into equal pairs plus a leftover multiset \(L\), then
\[
\delta(S)=\delta(L).
\]

**Proof.** Remove one equal pair \(\{x,x\}\). In decreasing order, all pieces equal to \(x\) form one consecutive block. Deleting two entries from this block leaves a block of the same value whose length is reduced by \(2\) and whose starting position is unchanged; all later entries shift by two positions, so their position-parity is unchanged. The alternating sum over a block of equal entries depends only on the parity of the block length, so deleting the pair does not change \(\delta\). Repeating removes all pairs. ∎

Also, for any sorted leftover \(L=\{\ell_1\ge \ell_2\ge\cdots\}\),
\[
\delta(L)=\ell_1-\delta(L\setminus\{\ell_1\})\le \ell_1\le \sum L. \tag{1}
\]

## 2. Liu's strategy: the lower bound

Liu marks \(n\) points so that the stick is divided into lengths
\[
\frac{2^n}{N},\frac{2^{n-1}}{N},\dots,\frac{2}{N},\frac1N .
\]
We prove that this guarantees \(\frac{2^n}{N}\).

Work in units of \(1/N\). The parts are
\[
2^n,2^{n-1},\dots,2,1,
\]
with total \(N=2^{n+1}-1\). Let Xiang refine them with at most \(n\) cuts, producing pieces
\[
v_1\ge v_2\ge\cdots\ge v_M,\qquad M\le 2n+1.
\]

**Lemma E.** For every \(1\le r\le \lfloor M/2\rfloor\),
\[
v_2+v_4+\cdots+v_{2r}\le 2^n-2^{\,n-r}.
\]

**Proof.** Induct on \(r\).

For \(r=1\), suppose \(v_2>2^{n-1}\). Then \(v_1\ge v_2>2^{n-1}\). A piece larger than \(2^{n-1}\) must lie inside a part larger than \(2^{n-1}\), and among the part sizes \(2^n,2^{n-1},\dots,1\), only \(2^n\) is larger. Thus \(v_1\) and \(v_2\) are disjoint subpieces of the same part of size \(2^n\), so
\[
2v_2\le v_1+v_2\le 2^n,
\]
contradicting \(v_2>2^{n-1}\). Hence \(v_2\le 2^{n-1}=2^n-2^{n-1}\).

Now assume the statement for \(r-1\). If \(v_{2r}\le 2^{n-r}\), then by induction
\[
\sum_{i=1}^r v_{2i}
\le \bigl(2^n-2^{\,n-r+1}\bigr)+2^{\,n-r}
=2^n-2^{\,n-r}.
\]

Otherwise \(v_{2r}>2^{n-r}\). Then all of \(v_1,\dots,v_{2r}\) exceed \(2^{n-r}\). Each must lie in a part of size larger than \(2^{n-r}\); since the part sizes are powers of two, these parts are among
\[
2^{\,n-r+1},2^{\,n-r+2},\dots,2^n,
\]
whose total size is
\[
\sum_{j=n-r+1}^n 2^j=2^{n+1}-2^{\,n-r+1}.
\]
The pieces \(v_1,\dots,v_{2r}\) are disjoint subintervals of these parts, so
\[
\sum_{i=1}^{2r}v_i\le 2^{n+1}-2^{\,n-r+1}.
\]
But \(v_{2i}\le v_{2i-1}\) for each \(i\), hence
\[
2\sum_{i=1}^r v_{2i}
\le \sum_{i=1}^{2r}v_i
\le 2^{n+1}-2^{\,n-r+1},
\]
so
\[
\sum_{i=1}^r v_{2i}\le 2^n-2^{\,n-r}.
\]
This proves Lemma E. ∎

Now \(r:=\lfloor M/2\rfloor\le n\), so by Lemma E,
\[
\operatorname{even}(S)=\sum_{i=1}^r v_{2i}
\le 2^n-2^{\,n-r}\le 2^n-1.
\]
Therefore, in units,
\[
\operatorname{odd}(S)=N-\operatorname{even}(S)
\ge N-(2^n-1)=2^n.
\]
Returning to ordinary length, Liu guarantees
\[
\frac{2^n}{N}.
\]

## 3. Xiang's strategy: the upper bound

Let \(A=(a_1,\dots,a_m)\) be any composition with \(m\le n+1\). We show Xiang can refine it with at most \(n\) cuts so that \(\delta\le 1/N\). By Lemma 1, this caps Liu's take at
\[
\frac{1+1/N}{2}=\frac{2^n}{N}.
\]

If \(m\le n\), Xiang cuts every part into two equal halves. This uses \(m\le n\) cuts, and all pieces occur in equal pairs, so by Lemma 2, \(\delta=0\).

Now suppose \(m=n+1\).

### Step 1: find two nearly equal disjoint subsums

There are \(2^{n+1}\) subset sums
\[
\sum_{i\in I}a_i,\qquad I\subseteq\{1,\dots,n+1\},
\]
all lying in \([0,1]\). Sort them. If all \(2^{n+1}-1=N\) consecutive gaps were \(>1/N\), the total spread would be \(>1\), impossible. Hence there are distinct \(I,J\) with
\[
\left|\sum_{i\in I}a_i-\sum_{j\in J}a_j\right|\le \frac1N.
\]
Remove the intersection: set
\[
P=I\setminus J,\qquad Q=J\setminus I,\qquad
Z=\{1,\dots,n+1\}\setminus(P\cup Q).
\]
Then \(P,Q\) are disjoint, \(P\cup Q\ne\varnothing\), and
\[
D:=\left|\sum_{i\in P}a_i-\sum_{j\in Q}a_j\right|\le \frac1N. \tag{2}
\]

### Step 2: cut everything else into equal pairs, then cancel \(P\) against \(Q\)

For every \(i\in Z\), Xiang halves the part \(a_i\), producing an equal pair \((a_i/2,a_i/2)\). This uses \(|Z|\) cuts.

If one of \(P,Q\) is empty, leave the parts on the other side uncut as leftovers; their total is \(D\) by (2). The number of cuts used is \(|Z|\le n\), since \(P\cup Q\) is nonempty.

Now suppose both \(P\) and \(Q\) are nonempty. Run the following cancellation procedure on two pools
\[
S=\{a_i:i\in P\},\qquad T=\{a_j:j\in Q\}.
\]
Repeatedly take \(s=\max S\) and \(t=\max T\).

- If \(s=t\), pair these two equal pieces and remove both.
- If \(s>t\), split the piece \(s\) into lengths \(t\) and \(s-t\); pair the new \(t\)-piece with the old \(t\)-piece, and return \(s-t\) to \(S\).
- If \(s<t\), do the symmetric operation with \(S\) and \(T\) interchanged.

The process ends when one pool is empty. Because paired mass removed from the two sides is equal, the remaining pool \(L\) has total
\[
\sum L=\left|\sum_{i\in P}a_i-\sum_{j\in Q}a_j\right|=D\le \frac1N.
\]

Let \(f\) be the number of equality steps and \(c\) the number of splitting steps. Initially there are \(|P|+|Q|\) pieces in the pools; an equality step reduces the pool count by \(2\), and a splitting step reduces it by \(1\). If the final leftover pool has size \(\ell\), then
\[
|P|+|Q|-2f-c=\ell. \tag{3}
\]
If \(\ell\ge1\), then \(c\le |P|+|Q|-1\). If \(\ell=0\), the last step cannot have been a splitting step, since a splitting step returns a positive remainder to the larger side; hence \(f\ge1\), and again \(c\le |P|+|Q|-2\). Thus always
\[
c\le |P|+|Q|-1.
\]
The final pieces arising from the parts in \(P\cup Q\) consist of \(2(f+c)\) paired pieces plus \(\ell\) leftover pieces. By (3), the number of extra pieces beyond the original \(|P|+|Q|\) parts is exactly \(c\), so these subdivisions are realized by exactly \(c\) interior cut points. Therefore the total number of Xiang marks is at most
\[
|Z|+c\le |Z|+|P|+|Q|-1=n.
\]
All cut points are interior to the corresponding original parts, hence distinct from Liu's marks and from one another.

### Step 3: evaluate \(\delta\)

The final multiset consists of equal pairs plus a leftover multiset \(L\) with \(\sum L=D\le 1/N\). By Lemma 2 and (1),
\[
\delta=\delta(L)\le \sum L=D\le \frac1N.
\]
Thus Xiang can always force \(\delta\le 1/N\), as claimed.

## 4. Conclusion

Liu's geometric marking guarantees
\[
\frac{2^n}{N},
\]
and Xiang's strategy shows that no opening by Liu can guarantee more than
\[
\frac{1+1/N}{2}=\frac{2^n}{N}.
\]
Hence
\[
\boxed{\,c_n=\frac{2^n}{\,2^{n+1}-1\,}\,}.
\]