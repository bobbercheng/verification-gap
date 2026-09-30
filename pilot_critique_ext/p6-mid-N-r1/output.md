## Solution

For an integer \(m\ge 2\), let \(\operatorname{supp}(m)\) denote the set of its prime divisors. For a finite set \(s\) of primes, write

\[
\pi(s):=\prod_{p\in s}p,
\]

with \(\pi(\varnothing)=1\). A set \(s\) of primes is a **transversal** of a family of sets if it meets every member of that family.

Define

\[
S_\infty:=\{m\ge 1:\gcd(m,a_i)>1\text{ for every }i\ge 1\}.
\]

### 1. Two basic properties of the sequence

**Lemma 1.1.** The sequence \((a_n)\) is the increasing enumeration of
\[
S_\infty\cap[a_1,\infty).
\]

**Proof.** First, every term belongs to \(S_\infty\). Indeed, for \(i<j\), the defining property of \(a_j\) gives \(\gcd(a_j,a_i)>1\), and \(\gcd(a_i,a_i)=a_i>1\). Thus every two terms have a common divisor greater than \(1\).

Conversely, suppose \(x\in S_\infty\), \(x\ge a_1\), and \(x\) is not a term. Then \(x>a_1\). Since the sequence is strictly increasing and unbounded, there is an \(n\) such that

\[
a_n<x<a_{n+1}.
\]

Because \(x\in S_\infty\), we have \(\gcd(x,a_i)>1\) for every \(i\le n\). Hence \(x\) was an admissible candidate for \(a_{n+1}\), and minimality of \(a_{n+1}\) gives \(a_{n+1}\le x\), a contradiction. \(\blacksquare\)

**Lemma 1.2 (Killing property).** If \(x>a_1\) and \(x\notin S_\infty\), then there is a term \(a_i<x\) such that

\[
\gcd(x,a_i)=1.
\]

**Proof.** By Lemma 1.1, \(x\) is not a term, so for some \(n\),

\[
a_n<x<a_{n+1}.
\]

If \(\gcd(x,a_i)>1\) for every \(i\le n\), then \(x\) would again be an admissible candidate for \(a_{n+1}\), forcing \(a_{n+1}\le x\), a contradiction. Thus \(\gcd(x,a_i)=1\) for some \(i\le n\), and \(a_i\le a_n<x\). \(\blacksquare\)

### 2. Minimal generators of \(S_\infty\)

The set \(S_\infty\) is closed under taking multiples. Let \(\mathcal M\) be the set of its minimal elements under divisibility.

Every \(m\in S_\infty\) is divisible by an element of \(\mathcal M\): among the finitely many divisors of \(m\) lying in \(S_\infty\), choose one minimal under divisibility. Consequently,

\[
S_\infty=\bigcup_{h\in\mathcal M}h\mathbb Z_{>0}.
\]

**Lemma 2.1.** If \(\mathcal M\) is finite, then the required \(T\) and \(L\) exist.

**Proof.** Write

\[
\mathcal M=\{h_1,\dots,h_k\},
\qquad
L:=\operatorname{lcm}(h_1,\dots,h_k).
\]

For every positive integer \(m\),

\[
m\in S_\infty
\iff h_i\mid m\text{ for some }i
\iff h_i\mid m+L\text{ for some }i
\iff m+L\in S_\infty,
\]

because each \(h_i\) divides \(L\). Thus membership in \(S_\infty\) is periodic with period \(L\).

Let

\[
T:=\#\bigl(S_\infty\cap[a_1,a_1+L)\bigr).
\]

Since \(a_1\in S_\infty\), we have \(T\ge1\). Write

\[
S_\infty\cap[a_1,a_1+L)=\{b_1<\cdots<b_T\}.
\]

By periodicity, for every \(j\ge0\),

\[
S_\infty\cap[a_1+jL,a_1+(j+1)L)
=
\{b_1+jL<\cdots<b_T+jL\}.
\]

Lemma 1.1 therefore gives

\[
a_{jT+r}=b_r+jL
\qquad (j\ge0,\ 1\le r\le T).
\]

Every positive integer \(n\) has a unique representation \(n=jT+r\) with \(1\le r\le T\), and hence

\[
a_{n+T}
=
a_{(j+1)T+r}
=
b_r+(j+1)L
=
a_n+L.
\]

Thus the conclusion holds. \(\blacksquare\)

It remains to prove that \(\mathcal M\) is finite.

### 3. The set-system formed by the minimal generators

Every \(h\in\mathcal M\) is squarefree. Indeed, if \(p^2\mid h\), then \(h/p\) has the same prime divisors as \(h\), so \(h/p\in S_\infty\), contradicting the minimality of \(h\).

Thus every \(h\in\mathcal M\) is of the form \(h=\pi(t)\), where

\[
t=\operatorname{supp}(h).
\]

For a finite set \(s\) of primes,

\[
\pi(s)\in S_\infty
\]

if and only if \(s\) meets \(\operatorname{supp}(a_i)\) for every \(i\). Therefore

\[
\mathcal C:=\{\operatorname{supp}(h):h\in\mathcal M\}
\]

is exactly the family of inclusion-minimal transversals of

\[
\{\operatorname{supp}(a_i):i\ge1\}.
\]

In particular, \(\mathcal C\) is an antichain: if \(c,d\in\mathcal C\) and \(c\subseteq d\), then \(c=d\).

We record three properties.

**Lemma 3.1.** Every term \(a_i\) is divisible by some \(h\in\mathcal M\). Equivalently, \(\operatorname{supp}(a_i)\) contains some member of \(\mathcal C\).

**Proof.** Since \(a_i\in S_\infty\), some minimal element \(h\in\mathcal M\) divides \(a_i\). \(\blacksquare\)

**Lemma 3.2.** Any two members of \(\mathcal C\) intersect.

**Proof.** Fix \(c\in\mathcal C\). Every multiple of \(\pi(c)\) belongs to \(S_\infty\). Choose \(k\) large enough that

\[
\pi(c)^k\ge a_1.
\]

By Lemma 1.1, \(\pi(c)^k\) is a term of the sequence. Its support is exactly \(c\). Every \(d\in\mathcal C\) is a transversal of all term supports, so \(d\cap c\ne\varnothing\). \(\blacksquare\)

**Lemma 3.3.** Every finite transversal of \(\mathcal C\) contains a member of \(\mathcal C\).

**Proof.** Let \(Q\) be a finite set of primes meeting every member of \(\mathcal C\). By Lemma 3.1, each \(\operatorname{supp}(a_i)\) contains a member of \(\mathcal C\), so \(Q\) meets every \(\operatorname{supp}(a_i)\). Hence

\[
\pi(Q)\in S_\infty.
\]

Therefore some \(h\in\mathcal M\) divides \(\pi(Q)\). Since \(h\) is squarefree, its support \(c\in\mathcal C\) satisfies \(c\subseteq Q\). \(\blacksquare\)

### 4. A descent lemma

**Lemma 4.1.** Let \(p\) be a prime belonging to at least one member of \(\mathcal C\). Then there exists \(d\in\mathcal C\) such that

\[
p\in d
\qquad\text{and}\qquad
\pi(d)\le a_1p.
\]

**Proof.** Start with any \(d\in\mathcal C\) containing \(p\). We repeatedly replace \(d\) while preserving the property \(p\in d\).

If \(\pi(d)\le a_1p\), we are done. Otherwise set

\[
F:=d\setminus\{p\}.
\]

Then

\[
\pi(F)=\frac{\pi(d)}p>a_1.
\]

Because \(d\) is a minimal transversal, its proper subset \(F\) is not a transversal, so \(\pi(F)\notin S_\infty\). By the killing property, Lemma 1.2, there is a term \(a_i<\pi(F)\) such that

\[
\gcd(\pi(F),a_i)=1.
\]

By Lemma 3.1, choose \(h\in\mathcal M\) with \(h\mid a_i\), and put

\[
e:=\operatorname{supp}(h)\in\mathcal C.
\]

Since \(\gcd(\pi(F),a_i)=1\), we have \(e\cap F=\varnothing\). Also

\[
\pi(e)=h\le a_i<\pi(F).
\]

By Lemma 3.2, \(e\cap d\ne\varnothing\). Since \(d=F\cup\{p\}\) and \(e\cap F=\varnothing\), it follows that \(p\in e\). Moreover,

\[
\pi(e)<\pi(F)=\frac{\pi(d)}p<\pi(d).
\]

Thus we may replace \(d\) by \(e\), preserving \(p\in d\) and strictly decreasing the positive integer \(\pi(d)\). This process must terminate, and at termination

\[
\pi(d)\le a_1p.
\]

\(\blacksquare\)

### 5. Finiteness of \(\mathcal C\)

Suppose, for contradiction, that \(\mathcal C\) is infinite.

Let

\[
U:=\bigcup_{c\in\mathcal C}c.
\]

If \(U\) were finite, then \(\mathcal C\), being a family of subsets of \(U\), would be finite. Hence \(U\) is infinite. Choose distinct primes

\[
p_1,p_2,p_3,\dots\in U.
\]

For each \(j\), Lemma 4.1 gives a member \(d_j\in\mathcal C\) such that

\[
p_j\in d_j,
\qquad
\pi(d_j)\le a_1p_j.
\]

Set

\[
Q_j:=d_j\setminus\{p_j\}.
\]

Then

\[
\pi(Q_j)=\frac{\pi(d_j)}{p_j}\le a_1.
\]

There are only finitely many finite prime sets \(Q\) with \(\pi(Q)\le a_1\), since they correspond to squarefree positive integers at most \(a_1\). Therefore, after passing to an infinite subsequence, we may assume that all \(Q_j\) are equal to one fixed set \(Q\).

Because \(Q\) is finite and the \(p_j\) are distinct, after discarding finitely many indices we may also assume \(p_j\notin Q\) for every remaining \(j\). Thus

\[
d_j=Q\cup\{p_j\}
\]

for infinitely many distinct primes \(p_j\).

We claim that \(Q\) is a transversal of \(\mathcal C\). Let \(e\in\mathcal C\). Since \(e\) is finite, choose one of the above indices \(j\) such that \(p_j\notin e\). By Lemma 3.2,

\[
e\cap d_j\ne\varnothing.
\]

But \(d_j=Q\cup\{p_j\}\) and \(p_j\notin e\), so \(e\cap Q\ne\varnothing\). Hence \(Q\) meets every member of \(\mathcal C\).

By Lemma 3.3, there is some \(c\in\mathcal C\) with

\[
c\subseteq Q.
\]

Choosing any of the above \(j\), we obtain

\[
c\subseteq Q\subsetneq Q\cup\{p_j\}=d_j.
\]

This contradicts the fact that \(\mathcal C\) is an antichain.

Therefore \(\mathcal C\) is finite, and hence \(\mathcal M\) is finite. Lemma 2.1 now provides positive integers \(T\) and \(L\) such that

\[
\boxed{a_{n+T}=a_n+L}
\]

for every positive integer \(n\). \(\blacksquare\)