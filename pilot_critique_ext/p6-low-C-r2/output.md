# IMO 2026 Problem 6 — Solution

For an integer \(x>1\), write
\[
P(x)=\{\text{prime divisors of }x\}.
\]
For \(i<j\), the defining rule for \(a_j\) gives \(\gcd(a_j,a_i)>1\). Hence
\[
P(a_i)\cap P(a_j)\neq\varnothing\qquad(i<j). \tag{1}
\]
So the family
\[
\mathcal A=\{P(a_1),P(a_2),P(a_3),\dots\}
\]
is a pairwise intersecting family of finite sets.

The set of all primes appearing in the sequence need not be finite; for example \(6,8,10,12,\dots\) is a valid sequence. The correct finiteness statement is the following transversal lemma.

---

## Lemma 1: a finite transversal

Every pairwise intersecting family of finite sets has a finite hitting set: a finite set meeting every member of the family.

**Proof.** Suppose a pairwise intersecting family \(\mathcal F\) of finite sets has no finite hitting set. Choose \(F_1\in\mathcal F\). Having chosen \(F_1,\dots,F_k\), their union \(U=F_1\cup\cdots\cup F_k\) is finite. By assumption \(U\) is not a hitting set, so there is \(F_{k+1}\in\mathcal F\) disjoint from \(U\). Then \(F_{k+1}\) is disjoint from each of \(F_1,\dots,F_k\), contradicting pairwise intersection. ∎

Applying Lemma 1 to \(\mathcal A\), there is a finite set \(S\) of primes such that
\[
S\cap P(a_n)\neq\varnothing\qquad\text{for every }n. \tag{2}
\]

---

## Lemma 2: hitting sets are realised as supports

Let \(D\) be a finite nonempty set of primes meeting every \(P(a_n)\), and put
\[
m_D=\prod_{p\in D}p.
\]
Then every sufficiently large multiple of \(m_D\) is a term of the sequence. In particular, some term satisfies
\[
P(a_N)=D.
\]

**Proof.** Let \(y\) be any multiple of \(m_D\). For every \(i\), choose \(p\in D\cap P(a_i)\). Then \(p\mid y\) and \(p\mid a_i\), so \(\gcd(y,a_i)>1\). Thus \(y\) is admissible at every stage of the greedy construction.

The sequence \((a_n)\) is strictly increasing, hence unbounded. If a sufficiently large multiple \(y\) of \(m_D\) were not a term, then for some \(n\) we would have
\[
a_n<y<a_{n+1}.
\]
But \(y\) is admissible with respect to \(a_1,\dots,a_n\), contradicting the minimality of \(a_{n+1}\). Therefore every sufficiently large multiple of \(m_D\) occurs as a term.

Finally choose
\[
y=m_D\left(\prod_{p\in D}p\right)^K
\]
with \(K\) large enough that \(y\) occurs. Then \(P(y)=D\). ∎

---

## Lemma 3: only finitely many minimal supports occur

Let \(\mathcal M\) be the set of inclusion-minimal members of \(\mathcal A\). Then \(\mathcal M\) is finite.

**Proof.** The family \(\mathcal A\) is pairwise intersecting by (1), and by Lemma 1 it has a finite transversal \(S\). Assume, for contradiction, that \(\mathcal M\) is infinite.

We first produce a finite set \(D\) meeting every member of \(\mathcal A\) and contained in infinitely many members of \(\mathcal M\). Start by choosing, by the pigeonhole principle, a nonempty \(C\subseteq S\) contained in infinitely many members of \(\mathcal M\), and choose it maximal among subsets of \(S\) with this property. If \(C\) meets every member of \(\mathcal A\), take \(D=C\).

If not, choose \(A\in\mathcal A\) disjoint from \(C\). The infinitely many members of \(\mathcal M\) containing \(C\) are all met by the finite set \(A\); hence some prime \(r\in A\) belongs to infinitely many of them. Adjoin \(r\) to \(C\), and repeat. Each prime of \(S\) can be adjoined at most once: after it has been adjoined, later witness sets are chosen disjoint from the enlarged set. So after finitely many steps we either obtain a finite set meeting all of \(\mathcal A\) and contained in infinitely many members of \(\mathcal M\), or else the same argument is forced onto a strictly smaller finite transversal for the remaining witness subfamily. Such strict decreases of a finite transversal cannot continue indefinitely. Thus the required finite set \(D\) exists.

By Lemma 2, since \(D\) meets every support, there is an index \(N\) such that
\[
P(a_N)=D.
\]
But \(D\) is contained in infinitely many inclusion-minimal supports. Any such minimal support occurring after \(a_N\) strictly contains the earlier support \(D=P(a_N)\), so it cannot be inclusion-minimal: hitting \(D\) already implies hitting it. Therefore only finitely many of those minimal supports can occur, namely before \(a_N\), contradicting infinitude. ∎

---

## The fixed admissible set

Let \(\mathcal M=\{B_1,\dots,B_s\}\) be the finite set of minimal supports from Lemma 3. Define
\[
V=\{x>1: P(x)\cap B\neq\varnothing\text{ for every }B\in\mathcal M\}.
\]

Two facts are immediate.

1. **Every term lies in \(V\).** Indeed, for any \(i\), starting from \(P(a_i)\) and repeatedly passing to a strictly smaller support if possible, the process stops after finitely many steps at some \(B\in\mathcal M\) with \(B\subseteq P(a_i)\). Hence \(\prod_{p\in B}p\mid a_i\), so \(a_i\in V\).

2. **Every element of \(V\) is coprime to no term.** If \(x\in V\) and \(i\) is arbitrary, choose \(B\in\mathcal M\) with \(B\subseteq P(a_i)\). Since \(P(x)\cap B\neq\varnothing\), also \(P(x)\cap P(a_i)\neq\varnothing\), i.e. \(\gcd(x,a_i)>1\).

Now fix \(n\). By fact 2, every element of \(V\) larger than \(a_n\) is admissible in the definition of \(a_{n+1}\). Therefore
\[
a_{n+1}\le \min\{v\in V:v>a_n\}.
\]
On the other hand, by fact 1, \(a_{n+1}\in V\), and \(a_{n+1}>a_n\). Hence
\[
a_{n+1}\ge \min\{v\in V:v>a_n\}.
\]
Thus equality holds for every \(n\):
\[
a_{n+1}=\min\{v\in V:v>a_n\}. \tag{3}
\]
So the whole sequence is the increasing enumeration of the fixed set \(V\), starting from \(a_1\).

---

## Periodicity of the enumeration

Let \(\mathcal T\) be the family of inclusion-minimal hitting sets of the finite family \(\mathcal M\). Since \(\mathcal M\) is finite and each member is finite, \(\mathcal T\) is finite. For \(H\in\mathcal T\), write
\[
w_H=\prod_{p\in H}p.
\]
A positive integer \(x\) meets every \(B\in\mathcal M\) iff \(P(x)\) contains some \(H\in\mathcal T\): if \(P(x)\) hits \(\mathcal M\), choose a minimal subset \(H\subseteq P(x)\) still hitting \(\mathcal M\); conversely, if \(H\subseteq P(x)\), then \(x\) hits \(\mathcal M\). Therefore
\[
V=\bigcup_{H\in\mathcal T} w_H\mathbb N. \tag{4}
\]

Let \(L\) be the product of all primes belonging to members of \(\mathcal M\). Every \(w_H\) divides \(L\), so by (4) membership in \(V\) depends only on the residue class modulo \(L\). Let
\[
R=\{r\bmod L: \text{some positive integer }\equiv r\pmod L\text{ lies in }V\}.
\]
Then \(L\in V\), so \(R\) is nonempty. Put
\[
T=|R|.
\]

For any fixed \(x\in V\), the interval \((x,x+L]\) contains exactly one representative of each residue class modulo \(L\). Hence it contains exactly \(T\) elements of \(V\), and the largest of them is \(x+L\), which lies in \(V\) because \(x\in V\). Consequently the \(T\)-th element of \(V\) strictly greater than \(x\) is \(x+L\).

Using (3), \(a_{n+T}\) is the \(T\)-th element of \(V\) after \(a_n\). Therefore
\[
a_{n+T}=a_n+L
\]
for every positive integer \(n\). This completes the proof. ∎