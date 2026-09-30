# Candidate solution

Status: **complete**.

Let \(A=a_1\), and for an integer \(x>1\) let
\[
P(x)=\{p:p\text{ is prime and }p\mid x\}
\]
be its prime support.

## 1. The greedy rule is a scan of a fixed set

All sequence terms are pairwise non-coprime. Also, the sequence is unbounded. Indeed, if \(M\) is the least multiple of \(A\) greater than \(a_n\), then for every \(i\le n\),
\[
\gcd(M,a_i)\geq \gcd(A,a_i)>1.
\]
Thus \(M\) is admissible and \(a_{n+1}\le M\le a_n+A\).

Call a finite set of primes \(E\) **good** if
\[
E\cap P(a_i)\ne\varnothing\qquad\text{for every }i\ge1.
\]
For every integer \(m\ge A\),
\[
m\text{ is a term of the sequence}\quad\Longleftrightarrow\quad P(m)\text{ is good}. \tag{1}
\]
The forward implication follows from pairwise non-coprimality. Conversely, suppose that \(m\) is not a term. By unboundedness there is an \(n\) with
\[
a_n<m<a_{n+1}.
\]
Had \(m\) shared a prime factor with each of \(a_1,\dots,a_n\), the greedy definition would have given \(a_{n+1}\le m\). Hence \(m\) is coprime to at least one sequence term, so \(P(m)\) is not good. This proves (1).

## 2. Large primes can be erased

Let
\[
Q=\{p:p\text{ is prime and }p\le A\},
\qquad
\sigma(x)=P(x)\cap Q.
\]

We prove the key lemma:

**Lemma.** For every sequence term \(x\), the set \(\sigma(x)\) is good.

**Proof.** We induct over the sequence terms in increasing order. First, \(\sigma(x)\ne\varnothing\): for \(x=A\) this is clear, and every later term has a common prime factor with \(A\), necessarily a prime at most \(A\).

If all prime factors of \(x\) are at most \(A\), then \(\sigma(x)=P(x)\), which is good by (1). Otherwise, choose a prime \(q>A\) dividing \(x\). Put
\[
R=\prod_{r\in\sigma(x)}r,
\]
choose any \(p\in\sigma(x)\), and let \(k\ge0\) be least such that
\[
m=Rp^k\ge A.
\]
Because \(p\mid R\), we have \(P(m)=\sigma(x)\). Moreover, \(m<x\). If \(k=0\), then
\[
m=R<Rq\le x.
\]
If \(k>0\), minimality of \(k\) gives \(Rp^{k-1}<A\), and hence
\[
p^k<\frac{pA}{R}\le A<q.
\]
Again \(m=Rp^k<Rq\le x\).

If \(m=A\), then it is already the first sequence term. Otherwise \(m>A\). Suppose for a contradiction that this \(m\) is not a sequence term. The proof of (1), applied causally to this skipped integer, gives a sequence term \(b<m\) with \(\gcd(b,m)=1\). Since \(b<x\), the induction hypothesis says that \(\sigma(b)\) is good. In particular,
\[
\sigma(b)\cap P(x)\ne\varnothing. \tag{2}
\]
On the other hand, \(P(m)=\sigma(x)\) and \(\gcd(b,m)=1\), so \(\sigma(b)\cap\sigma(x)=\varnothing\). Every prime in \(\sigma(b)\) is at most \(A\), whereas every prime in \(P(x)\setminus\sigma(x)\) is greater than \(A\). Thus \(\sigma(b)\) is in fact disjoint from all of \(P(x)\), contradicting (2).

Therefore \(m\) is a sequence term. By (1), \(P(m)=\sigma(x)\) is good, completing the induction. \(\square\)

Goodness is upward closed: a finite prime set containing a good set is good. Consequently, for every \(m\ge A\),
\[
\begin{aligned}
m\text{ is a sequence term}
&\overset{(1)}\Longleftrightarrow P(m)\text{ is good}\\
&\Longleftrightarrow \sigma(m)\text{ is good}. \tag{3}
\end{aligned}
\]
For the last equivalence, the forward direction is the lemma and the reverse direction follows from \(\sigma(m)\subseteq P(m)\).

## 3. Global translation-periodicity

Set
\[
L=\prod_{p\in Q}p.
\]
This is a positive integer. For every \(m\ge A\) and every \(p\in Q\),
\[
p\mid m+L\quad\Longleftrightarrow\quad p\mid m.
\]
Hence \(\sigma(m+L)=\sigma(m)\), and (3) gives
\[
m\text{ is a sequence term}
\quad\Longleftrightarrow\quad
m+L\text{ is a sequence term}. \tag{4}
\]
This is periodicity from the initial threshold \(A\), not merely eventual periodicity.

Let \(T\) be the number of sequence terms in the interval
\[
[A,A+L-1].
\]
It is positive because it includes \(A=a_1\). Every interval of \(L\) consecutive integers contained in \([A,\infty)\) contains each residue modulo \(L\) once and therefore contains exactly \(T\) sequence terms, by (4). In particular, for every \(n\), the interval
\[
(a_n,a_n+L]
\]
contains exactly \(T\) terms, and its right endpoint is a term by (4). Therefore that endpoint is precisely the \(T\)-th term after \(a_n\):
\[
\boxed{a_{n+T}=a_n+L}
\qquad(n\ge1).
\]

## Hypotheses tested and falsification attempts

1. **Only primes dividing \(a_1\) control the sequence.** This is false. For \(A=15\), the first terms are \(15,18,22\), while \(21\) is skipped because \(\gcd(21,20)=1\). Yet \(18\) and \(21\) have the same trace \(\{3\}\) on the primes dividing \(15\). This forced the larger, but still finite, set of all primes at most \(A\).

2. **An arbitrary infinite pairwise-intersecting constraint family reduces to finitely many constraints.** This is false. For distinct odd primes \(q_i\), the supports \(\{2,q_i\}\) are pairwise intersecting. A finite prime set meeting every one must contain \(2\), but the first \(N\) constraints are also met by \(\{q_1,\dots,q_N\}\). Thus no finite subfamily has the same transversals. The proof above uses the arithmetic scan order, not a generic compactness assertion.

3. **Eventual periodicity would automatically imply the required identity from \(n=1\).** This is false in general. The increasing sequence \(b_1=2\), \(b_n=2n-1\) for \(n\ge2\) has constant tail gaps. If \(b_{n+T}=b_n+L\) held for every \(n\), tail indices would give \(L=2T\), while \(n=1\) would give \(2T+1=2T+2\). This is why (4) was proved globally on \([A,\infty)\).

4. **Surviving hypothesis: delete primes greater than \(A\) without changing global compatibility.** The naive quotient can fall below the initial threshold: for \(A=15\), \(102\) is selected but \(102/17=6<15\). The construction \(Rp^k\) repairs this boundary issue while preserving exactly the small-prime support; the lemma proves the strengthened hypothesis.

## Computational evidence (not used as proof)

The script `experiment.py` directly implements the greedy rule. It reproduces, for example, the smaller valid period \((T,L)=(8,30)\) for \(A=15\). Its `trace` check for \(2\le A\le150\), over the first 400 terms for each start, examines 19,585 selected terms having a prime factor greater than \(A\); in every case an earlier selected term with exactly the \(\le A\) prime support is found. These computations only test the lemma; the argument above proves it independently.
