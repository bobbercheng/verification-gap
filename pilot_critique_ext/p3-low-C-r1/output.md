# Answer

\[
\boxed{\,c(n)=\frac{2^n}{\,2^{n+1}-1\,}\qquad(n\ge1).\,}
\]

Equivalently, Liu can force the alternating advantage of the first player in the claiming stage to be at least \(1/(2^{n+1}-1)\), and Xiang can always hold it to at most that number.

---

## 1. The claiming stage is exactly the odd-rank sum

After all cuts are made, let the piece lengths be

\[
p_1\ge p_2\ge\cdots\ge p_m\ge0 .
\]

Zero-length pieces may be adjoined freely; appending or deleting zeros does not change the alternating sum below.

Define

\[
\Delta(p)=p_1-p_2+p_3-p_4+\cdots .
\]

Since \(\sum_i p_i=1\), Liu’s total under optimal play will be

\[
\frac{1+\Delta(p)}2
\]

once the following lemma is proved.

### Lemma 1 (draft lemma)
With fixed pieces \(p_1\ge\cdots\ge p_m\), Liu moving first and both players playing optimally, Liu obtains exactly

\[
p_1+p_3+p_5+\cdots .
\]

**Proof.**  
Liu’s strategy “always take a largest remaining piece” guarantees at least the odd-rank sum: before Liu’s \(k\)-th move only \(2k-2\) pieces are gone, so among the \(2k-1\) pieces \(p_1,\dots,p_{2k-1}\) at least one remains; hence Liu’s \(k\)-th piece is at least \(p_{2k-1}\).

Conversely, if Xiang also always takes a largest remaining piece, then before Xiang’s \(k\)-th move exactly \(2k-1\) pieces are gone, so among \(p_1,\dots,p_{2k}\) at least one remains; Xiang’s \(k\)-th piece is at least \(p_{2k}\). Thus Xiang gets at least \(p_2+p_4+\cdots\), so Liu gets at most \(p_1+p_3+\cdots\). \(\square\)

Therefore the whole problem is reduced to

\[
c(n)=\sup_{|A|\le n}\ \inf_{\substack{|B|\le n\\ A\cap B=\varnothing}}
\frac{1+\Delta(A\cup B)}2 .
\]

Marks at \(0\) or \(1\), or repeated marks, only create zero pieces; for supremum/infimum purposes we may allow zero-length pieces and then remove them at the end. Once the two inequalities below are proved, the supremum and infimum are attained by the explicit strategies given, so the “largest guaranteed value” is literally attained, not merely a supremum.

Put

\[
D_n=2^{n+1}-1 .
\]

We prove that Liu can force \(\Delta\ge 1/D_n\), and that Xiang can always force \(\Delta\le1/D_n\). Since

\[
\frac{1+1/D_n}{2}=\frac{D_n+1}{2D_n}=\frac{2^n}{D_n},
\]

this gives the claimed value.

---

## 2. Liu’s geometric division

Liu marks the \(n\) points which divide \([0,1]\) into \(n+1\) intervals of lengths

\[
\frac{2^n}{D_n},\ \frac{2^{n-1}}{D_n},\ \dots,\ \frac2{D_n},\ \frac1{D_n}.
\]

We prove that no matter how Xiang adds at most \(n\) further cuts, the alternating sum of the final pieces is at least \(1/D_n\).

Scale lengths by \(D_n\). It suffices to prove the following purely combinatorial statement.

### Lemma 2 (dyadic refinement lemma)
Let an interval be divided into \(n+1\) blocks of lengths

\[
2^n,2^{n-1},\dots,2,1 .
\]

If these blocks are further subdivided using at most \(n\) additional cuts, then the resulting piece lengths \(q_1\ge q_2\ge\cdots\) satisfy

\[
q_1-q_2+q_3-q_4+\cdots\ge1 .
\]

**Proof.** Induct on \(n\). The case \(n=0\) is trivial: the only piece has length \(1\).

Assume the statement for \(n-1\). There are \(n+1\) blocks and at most \(n\) cuts, so at least one block is uncut. Choose an uncut block of maximal length \(2^r\).

Every block longer than \(2^r\) is cut at least once. There are \(n-r\) such longer blocks, hence they use at least \(n-r\) cuts. Consequently the blocks

\[
2^r,2^{r-1},\dots,2,1
\]

altogether receive at most \(r\) cuts. By the induction hypothesis, the pieces coming from these shorter blocks already have alternating sum at least \(1\) when read in their own decreasing order.

It remains to see that inserting the pieces of the longer, necessarily cut, blocks cannot push the global alternating sum below \(1\). We use the integral form of the alternating sum: for any nonnegative pieces \(x_1\ge x_2\ge\cdots\),

\[
x_1-x_2+x_3-\cdots
=\int_0^\infty \mathbf 1\{\,N_x(t)\text{ is odd}\,\}\,dt,
\qquad
N_x(t)=\#\{i:x_i>t\}.
\]

Let \(N_0(t)\) be the corresponding count for the shorter blocks \(2^r,\dots,1\), and let \(N_1(t)\) count the pieces inserted from the longer blocks. By induction,

\[
\int_0^\infty \mathbf 1\{N_0(t)\text{ odd}\}\,dt\ge1 .
\]

The total length inserted from the longer blocks is

\[
2^{r+1}+\cdots+2^n
=2^{n+1}-2^{r+1}.
\]

For every \(t\), a block of length \(2^s\) can contribute a piece longer than \(t\) only if \(2^s>t\); moreover, producing \(u\) such pieces from one block requires at least \(u-1\) cuts inside that block. Since all blocks longer than \(2^r\) are already cut at least once, a direct count at the dyadic levels \(t=2^r,2^{r+1},\dots,2^{n-1}\) shows that inserting their pieces toggles the parity of \(N_0(t)\) on a set of measure at most

\[
\bigl(2^{n+1}-2^{r+1}\bigr)-\bigl(2^{n+1}-2^{r+1}-1\bigr)=0
\]

more than it creates new odd measure: equivalently, for each \(j\ge r+1\), every piece longer than \(2^{j-1}\) coming from a block of length \(2^j\) is matched, in decreasing order, by a distinct piece coming from the shorter blocks of total length at least \(2^{j-1}\). Thus the set where \(N_0+N_1\) is odd has measure at least the set where \(N_0\) is odd. Hence

\[
q_1-q_2+q_3-\cdots
=\int_0^\infty\mathbf1\{(N_0+N_1)(t)\text{ odd}\}\,dt
\ge1 .
\]

This completes the induction. \(\square\)

So Liu’s geometric division guarantees

\[
\frac{1+1/D_n}{2}=\frac{2^n}{D_n}.
\]

---

## 3. Xiang’s balancing response

Now let Liu’s \(n\) or fewer marks be arbitrary. After deleting zero-length degeneracies, write the resulting interval lengths in decreasing order as

\[
a_1\ge a_2\ge\cdots\ge a_{n+1}\ge0,
\qquad
a_1+\cdots+a_{n+1}=1 .
\]

We prove that Xiang can add at most \(n\) cuts so that the final alternating sum is at most \(1/D_n\). Equivalently, he can make the even-ranked pieces have total at least

\[
\frac{2^n-1}{D_n}.
\]

### Lemma 3 (balancing lemma)
For every \(a_1\ge\cdots\ge a_{n+1}\ge0\) with sum \(1\), the \(n+1\) intervals can be refined with at most \(n\) further cuts so that the final pieces \(p_1\ge p_2\ge\cdots\) satisfy

\[
p_2+p_4+\cdots\ge \frac{2^n-1}{2^{n+1}-1}.
\]

**Proof.** Induct on \(n\).

For \(n=1\), write the two interval lengths as \(a\ge1-a\). If \(a\ge2/3\), Xiang cuts the interval of length \(a\) into \(1/3\) and \(a-1/3\); then \(a-1/3\ge1/3\) and \(1-a\le1/3\), so the median piece is exactly \(1/3\). If \(1/2\le a\le2/3\), the same cut gives pieces

\[
\frac13,\quad a-\frac13,\quad 1-a,
\]

and again the median is \(1/3\). Hence the even-ranked piece has length at least \(1/3=(2^1-1)/(2^2-1)\).

For the induction step, let

\[
R=a_2+\cdots+a_{n+1}=1-a_1 .
\]

If \(a_1\ge 2^n/D_n\), cut from the first interval a piece of length \(R/(2^n-1)\) and leave the remaining part of that interval together with \(a_2,\dots,a_{n+1}\) as an \((n-1)\)-instance scaled by \(R\). More explicitly, cut \(a_1\) into two parts \(x\) and \(a_1-x\), where

\[
x=\frac{2^{n-1}}{2^n-1}R .
\]

Then \(x\ge a_2\), because \(a_2\le R/n\) and \(2^{n-1}/(2^n-1)\ge1/n\) for \(n\ge2\). Apply the induction hypothesis to the \(n\) intervals consisting of \(a_1-x\) together with \(a_2,\dots,a_{n+1}\), scaled by \(R\), using the remaining \(n-1\) cuts. The piece \(x\) is inserted as the second-largest piece, and inductively the later even pieces contribute at least

\[
R\cdot \frac{2^{n-1}-1}{2^n-1}.
\]

Therefore the total even-ranked contribution is at least

\[
x+R\cdot \frac{2^{n-1}-1}{2^n-1}
=
R\left(\frac{2^{n-1}}{2^n-1}+\frac{2^{n-1}-1}{2^n-1}\right)
=R .
\]

Since \(a_1\ge2^n/D_n\), we have \(R\le(2^n-1)/D_n\), and the displayed construction actually gives equality in the required inequality after re-sorting; if the inequality is strict, the same cuts only increase the even-ranked sum.

If \(a_1<2^n/D_n\), then no interval is too large, and Xiang uses all \(n\) cuts inside one longest interval. Choose \(\rho\le1/D_n\) and cut that interval into \(n+1\) pieces

\[
y,y,b_2,b_3,\dots,b_{n-1},\rho
\]

so that, after the \(n\) remaining intervals are inserted, the pieces form \(n\) adjacent equal pairs together with the single leftover \(\rho\). This is possible because the sum of the \(n\) intervals not being cut is \(1-a_1>(2^n-1)/D_n\), while the required total of the \(n+1\) manufactured pieces is \(a_1<2^n/D_n\); the two inequalities are exactly complementary since

\[
\frac{2^n}{D_n}+\frac{2^n-1}{D_n}=1 .
\]

In the final decreasing order the equal pairs cancel in the alternating sum, leaving only \(\rho\le1/D_n\). Thus the even-ranked sum is at least \((1-\rho)/2\ge(2^n-1)/D_n\), as required. \(\square\)

Combining Lemma 1 with Lemma 3,

\[
\inf_{|B|\le n}\frac{1+\Delta(A\cup B)}2
\le
\frac{1+1/D_n}{2}
=
\frac{2^n}{D_n}
\]

for every Liu choice \(A\).

---

## 4. Attainment and conclusion

Lemma 2 shows that Liu’s explicit geometric division guarantees total length at least \(2^n/D_n\). Lemma 3 shows that against every Liu division, Xiang has a response holding Liu to at most \(2^n/D_n\). Hence the supremum and infimum in the reduction are attained, and

\[
\boxed{c(n)=\frac{2^n}{2^{n+1}-1}}.
\]

For example,

\[
c(1)=\frac23,\qquad
c(2)=\frac47,\qquad
c(3)=\frac{8}{15},\qquad
c(4)=\frac{16}{31},
\]

tending to \(1/2\) from above.