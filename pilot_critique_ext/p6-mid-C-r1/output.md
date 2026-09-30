# IMO 2026, Problem 6 — Solution

**Setup and notation.** For an integer $m\ge 2$ let $\operatorname{supp}(m)$ denote the set of its prime divisors; for a finite set $s$ of primes write $\pi(s):=\prod_{p\in s}p$ (a squarefree integer), with $\pi(\emptyset)=1$. Note that $\gcd(m,m')>1$ iff $\operatorname{supp}(m)\cap\operatorname{supp}(m')\neq\emptyset$. A set $s$ of primes is a *transversal* of a family $\mathcal F$ of sets if $s$ meets every member of $\mathcal F$. Define
$$S_\infty:=\{m\ge 1:\gcd(m,a_i)>1\ \text{for every }i\ge 1\}.$$

**Idea in one paragraph.** The sequence enumerates $S_\infty\cap[a_1,\infty)$ (Lemma 1), and $S_\infty$ is the union of the multiples of its minimal elements $\mathcal M$; if $\mathcal M$ is finite, periodicity follows immediately (Lemma 8). The supports of the minimal elements form an antichain $\mathcal C$ of finite prime sets that is pairwise intersecting (Lemma 4) and "self-dual for finite transversals" (Lemma 5). The greedy minimality of $a_{n+1}$ yields a *killing property* (Lemma 2): every non-member $x>a_1$ is coprime to an earlier term. Applying it to $x=\pi(t^*\setminus\{q\})$, where $t^*$ is a minimal-value permanent containing a prime $q$, shows every large prime occurring in a permanent occurs in one with small cofactor (Lemma 7). If $\mathcal C$ were infinite, infinitely many such primes $>a_1$ would share one fixed cofactor $s$; then every permanent would meet $s$, and a minimal transversal inside $s$ would (by Lemma 5) be a permanent strictly contained in a permanent — contradicting the antichain property.

---

## Lemma 1 (the sequence enumerates $S_\infty$)

$(a_n)_{n\ge1}$ is the increasing enumeration of $S_\infty\cap[a_1,\infty)$.

**Proof.** Every term lies in $S_\infty$: for $i<j$, the defining property of $a_j$ gives $\gcd(a_j,a_i)>1$; also $\gcd(a_j,a_j)=a_j>1$; and for $i>j$ the defining property of $a_i$ gives $\gcd(a_i,a_j)>1$. Moreover $a_j\ge a_1$ since the sequence is strictly increasing.

Conversely, let $x\in S_\infty$ with $x\ge a_1$, and suppose $x$ is not a term. Then $x>a_1$ (as $a_1$ is a term), and since $(a_n)$ is strictly increasing and unbounded there is a unique $n$ with $a_n<x<a_{n+1}$. Since $x\in S_\infty$, we have $\gcd(x,a_i)>1$ for all $i\le n$; but $a_{n+1}$ is by definition the *smallest* integer $>a_n$ with this property, so $a_{n+1}\le x$ — contradiction. $\blacksquare$

## Lemma 2 (killing property)

If $x>a_1$ and $x\notin S_\infty$, then there is a term $a_i<x$ with $\gcd(x,a_i)=1$.

**Proof.** By Lemma 1, $x$ is not a term; since $x>a_1$ there is $n$ with $a_n<x<a_{n+1}$. By the minimality of $a_{n+1}$, the integer $x$ fails the required condition: $\gcd(x,a_i)=1$ for some $i\le n$, and $a_i\le a_n<x$. $\blacksquare$

## Lemma 3 (minimal elements; permanents)

$S_\infty$ is closed under taking multiples. Let $\mathcal M$ be the set of its minimal elements under divisibility. Then:

**(a)** every $m\in S_\infty$ is a multiple of some $h\in\mathcal M$;

**(b)** every $h\in\mathcal M$ is squarefree;

**(c)** $\mathcal C:=\{\operatorname{supp}(h):h\in\mathcal M\}$ is exactly the family of minimal (under inclusion) transversals of $\{\operatorname{supp}(a_i):i\ge1\}$; in particular $\mathcal C$ is an antichain of finite sets of primes, and $\mathcal M=\{\pi(t):t\in\mathcal C\}$.

**Proof.** (a) Among the divisors of $m$ lying in $S_\infty$ (a nonempty finite set, containing $m$) choose $h$ minimal under divisibility; any element of $S_\infty$ dividing $h$ also divides $m$, so $h$ is minimal in all of $S_\infty$, i.e. $h\in\mathcal M$.

(b) If $p^2\mid h$ for a prime $p$, then $h/p<h$ and $\operatorname{supp}(h/p)=\operatorname{supp}(h)$ still meets every $\operatorname{supp}(a_i)$, so $h/p\in S_\infty$, contradicting minimality.

(c) For squarefree $\pi(t)$ we have $\pi(t)\in S_\infty$ iff $t$ is a transversal of the supports. If $h=\pi(t)\in\mathcal M$ and $t'\subsetneq t$ were a smaller transversal, then $\pi(t')\in S_\infty$ would be a proper divisor of $h$ — contradiction; so $t$ is a minimal transversal. Conversely, if $t$ is a minimal transversal then $\pi(t)\in S_\infty$; and if $d\mid\pi(t)$ lies in $S_\infty$, then $\operatorname{supp}(d)\subseteq t$ is a transversal, so $\operatorname{supp}(d)=t$ by minimality and $d\ge\pi(t)$, forcing $d=\pi(t)$. Hence $\pi(t)\in\mathcal M$. The antichain property is immediate from minimality under inclusion. $\blacksquare$

We call the members of $\mathcal C$ **permanents**.

## Lemma 4 (permanents pairwise intersect)

Any two members of $\mathcal C$ intersect.

**Proof.** Let $t\in\mathcal C$. Since $t$ is a transversal of the supports, every multiple of $\pi(t)$ lies in $S_\infty$. Choose $k\ge1$ with $\pi(t)^k\ge a_1$; by Lemma 1, $\pi(t)^k$ is a term $a_j$, and $\operatorname{supp}(a_j)=t$. Every $t'\in\mathcal C$ is a transversal of the supports, hence $t'\cap t=t'\cap\operatorname{supp}(a_j)\neq\emptyset$. $\blacksquare$

## Lemma 5 (self-duality for finite transversals)

Every finite minimal (under inclusion) transversal of the family $\mathcal C$ belongs to $\mathcal C$.

**Proof.** Let $T$ be a finite minimal transversal of $\mathcal C$. For each $i$, the term $a_i\in S_\infty$ is a multiple of some $\pi(t)$ with $t\in\mathcal C$ (Lemma 3(a)); then $t\subseteq\operatorname{supp}(a_i)$, and since $T$ meets $t$, it meets $\operatorname{supp}(a_i)$. Hence $\pi(T)\in S_\infty$, so some $\pi(t')\in\mathcal M$ divides $\pi(T)$, i.e. $t'\subseteq T$ with $t'\in\mathcal C$. By Lemma 4, $t'$ meets every member of $\mathcal C$, so $t'$ is a transversal of $\mathcal C$ contained in $T$; minimality of $T$ gives $T=t'\in\mathcal C$. $\blacksquare$

## Lemma 6 (killing, permanent form)

Let $F$ be a finite set of primes with $\pi(F)>a_1$ and $\pi(F)\notin S_\infty$. Then there exists a permanent $t\in\mathcal C$ disjoint from $F$ with $\pi(t)<\pi(F)$.

**Proof.** By Lemma 2 there is a term $a_i<\pi(F)$ with $\gcd(a_i,\pi(F))=1$, i.e. $\operatorname{supp}(a_i)\cap F=\emptyset$. By Lemma 3(a), some $h=\pi(t)\in\mathcal M$ with $t\in\mathcal C$ divides $a_i$; then $t\subseteq\operatorname{supp}(a_i)$ avoids $F$, and $\pi(t)=h\le a_i<\pi(F)$. $\blacksquare$

## Lemma 7 (reduction of large primes)

If a prime $q$ belongs to some permanent, then there is a permanent $t^*\ni q$ with $\pi\bigl(t^*\setminus\{q\}\bigr)\le a_1$.

**Proof.** Among permanents containing $q$, choose $t^*$ with $\pi(t^*)$ minimal. Suppose, for contradiction, that $\pi\bigl(t^*\setminus\{q\}\bigr)>a_1$. The set $F:=t^*\setminus\{q\}$ is a proper subset of $t^*$; since $\pi(t^*)$ is a *minimal* element of $S_\infty$ under divisibility, its proper divisor $\pi(F)$ does not lie in $S_\infty$. Lemma 6 then gives a permanent $t$ disjoint from $F$ with $\pi(t)<\pi(F)$. By Lemma 4, $t$ meets $t^*=F\cup\{q\}$; since $t\cap F=\emptyset$, necessarily $q\in t$. But
$$\pi(t)<\pi(F)=\frac{\pi(t^*)}{q}<\pi(t^*),$$
contradicting the choice of $t^*$. Hence $\pi\bigl(t^*\setminus\{q\}\bigr)\le a_1$. $\blacksquare$

## Theorem (finiteness of the permanents)

$\mathcal C$ is finite.

**Proof.** Suppose $\mathcal C$ is infinite. Its members are finite sets, so $\bigcup_{t\in\mathcal C}t$ contains infinitely many primes (finitely many primes have only finitely many subsets). Choose distinct primes $q_1,q_2,\dots$ in this union with $q_j>a_1$, and for each $j$ a permanent $t_j\ni q_j$ as in Lemma 7; write $s_j:=t_j\setminus\{q_j\}$, so that $\pi(s_j)\le a_1$. Every element of $s_j$ is a prime $\le\pi(s_j)\le a_1$, so the $s_j$ range over the finitely many subsets of the set of primes $\le a_1$; hence some fixed $s$ occurs as $s_j$ for infinitely many $j$. Passing to that subsequence, we have
$$t_j=s\cup\{q_j\}\in\mathcal C\quad\text{for all }j,$$
these members are pairwise distinct, and $q_j\notin s$ since every prime in $s$ is at most $a_1<q_j$.

Now take any $u\in\mathcal C$. By Lemma 4, $u$ meets every $t_j=s\cup\{q_j\}$. If $u\cap s=\emptyset$, then $u$ must contain $q_j$ for every $j$ — impossible, since $u$ is finite and the $q_j$ are distinct. Hence every member of $\mathcal C$ meets $s$: the finite set $s$ is a transversal of $\mathcal C$. Let $u_0\subseteq s$ be minimal (under inclusion) among transversals of $\mathcal C$ contained in $s$; then $u_0$ is a finite minimal transversal of $\mathcal C$, so by Lemma 5, $u_0\in\mathcal C$. But then
$$u_0\subseteq s\subsetneq s\cup\{q_1\}=t_1,$$
so $u_0$ and $t_1$ are two distinct comparable members of $\mathcal C$, contradicting the antichain property (Lemma 3(c)). $\blacksquare$

## Lemma 8 (periodicity from finitely many permanents)

If $\mathcal M$ is finite, then there exist positive integers $T$ and $L$ with $a_{n+T}=a_n+L$ for every $n\ge1$.

**Proof.** Note $\mathcal M\neq\emptyset$ (since $a_1\in S_\infty$, Lemma 3(a) applies). Write $\mathcal M=\{h_1,\dots,h_k\}$ and set $L:=\operatorname{lcm}(h_1,\dots,h_k)\ge1$. Since each $h_i\mid L$, for every integer $m\ge1$:
$$m\in S_\infty\iff \text{some }h_i\mid m\iff \text{some }h_i\mid m+L\iff m+L\in S_\infty.$$
Hence $x\mapsto x+L$ is an order-preserving bijection $S_\infty\cap[a_1,\infty)\to S_\infty\cap[a_1+L,\infty)$. Set
$$T:=\#\bigl(S_\infty\cap[a_1,a_1+L)\bigr);$$
then $T\ge1$ because $a_1$ lies in that interval. Iterating the bijection, each block $[a_1+jL,\,a_1+(j+1)L)$ ($j\ge0$) contains exactly $T$ elements of $S_\infty$, namely $\{x+jL : x\in S_\infty\cap[a_1,a_1+L)\}$. Since $(a_n)$ enumerates $S_\infty\cap[a_1,\infty)$ in increasing order (Lemma 1), the elements of $S_\infty$ in the $j$-th block are precisely $a_{jT+1},\dots,a_{jT+T}$, and therefore
$$a_{jT+r}=a_r+jL\qquad(1\le r\le T,\ j\ge0).$$
Given any $n\ge1$, write uniquely $n=jT+r$ with $1\le r\le T$; then
$$a_{n+T}=a_{(j+1)T+r}=a_r+(j+1)L=a_{jT+r}+L=a_n+L.\qquad\blacksquare$$

## Conclusion

By the Theorem, $\mathcal C$ is finite, and hence so is $\mathcal M=\{\pi(t):t\in\mathcal C\}$. Lemma 8 then yields positive integers $T$ and $L$ such that
$$a_{n+T}=a_n+L\qquad\text{for every positive integer }n.$$
$\blacksquare$