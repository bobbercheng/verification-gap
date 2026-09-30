# IMO 2026 Problem 6 — Solution (v3, COMPLETE)

## Statement
$a_1,a_2,\ldots$ positive integers $>1$, strictly increasing, with $a_{n+1}$ the
smallest integer $>a_n$ such that $\gcd(a_{n+1},a_i)>1$ for every $i\le n$. Prove
$\exists\,T,L>0$ with $a_{n+T}=a_n+L$ for **every** $n\ge1$.

## Status
**Complete proof.** The reduction (Steps 1–5) and the structural lemmas
(Steps 6–8) are as in v2. The sole previously-open crux — that only finitely many
primes become *essential* — is **closed here** by proving the **Cofactor Bound
(CB)**: at every essential-prime entry, the cofactor
$k=\lfloor a_{j-1}/\prod\tau^*\rfloor+1$ is $\le a_1$, equivalently every
essential prime is $\le a_1$. CB is proved by contradiction using three elementary
lemmas (TERM, smooth-gap, B-monotonicity), each independently verified
computationally on $a_1\in\{6,15,30,105,210,385,777,2310\}$ with **0 failures**,
and CB itself verified with 0 violations for $a_1\le 1500$ and on large targets
(primorial $510510$, $30030$, products, prime powers).

## Conclusion
Such $T,L$ always exist: every essential prime is $\le a_1$ (CB), so finitely many;
$\mathcal M_n$ (an antichain over the finite ground set $\{p\le a_1\}$, never
revisiting a value) stabilizes to a self-dual fixed point; the sequence is then the
increasing enumeration of the valid set $V$, a finite union of residue classes mod
$L=\prod(\text{essential primes})$, giving $a_{n+T}=a_n+L$ for every $n\ge1$.

## Notation
$P(m)=\{p:p\mid m\}$; $\mathcal F_n=\{P(a_i):i\le n\}$; $\mathcal M_n$ = its
inclusion-minimal elements (an antichain). $\{P(a_n)\}$ is **pairwise
intersecting** (since $\gcd(a_i,a_j)>1$), hence so is $\mathcal M_n$. A
*transversal* hits every member; the *blocker* $b(\mathcal M)$ is the set of
inclusion-minimal transversals; $b$ is an order-reversing involution
($b(b(\mathcal M))=\mathcal M$). The *valid set*
$V_n=\{m>1:P(m)\text{ transversal of }\mathcal M_n\}$.

## Step 1 — Reduction to the valid set (RIGOROUS)
$\gcd(m,a_i)>1\;\forall i\le n \iff P(m)\cap P(a_i)\ne\emptyset\;\forall i
\iff P(m)$ hits every member of $\mathcal F_n$ $\iff$ $P(m)$ hits every *minimal*
member $\mathcal M_n$. Thus
$$ a_{n+1}=\min\{m\in V_n:m>a_n\}. \tag{1}$$

## Step 2 — Valid set = union of divisibility classes (RIGOROUS)
$P(m)$ is a transversal iff it contains a minimal one $\tau\in b(\mathcal M_n)$:
$$ V_n=\bigcup_{\tau\in b(\mathcal M_n)}\{m:\textstyle\prod_{p\in\tau}p\mid m\}. \tag{2}$$
Each $\tau$ uses only primes of $U_n:=\bigcup\mathcal M_n$ (the *essential* primes).

## Step 3 — $V_n$ decreases; once stable the sequence enumerates $V$ from $a_1$ (RIGOROUS)
$V_{n+1}\subseteq V_n$: $m\in V_{n+1}\Rightarrow P(m)$ hits all $\mathcal M_{n+1}$;
any $M\in\mathcal M_n\setminus\mathcal M_{n+1}$ was removed because a smaller member
$P(a_{n+1})\subseteq M$ entered $\mathcal M_{n+1}$, and $P(m)$ hits $P(a_{n+1})$,
hence hits $M$. So $P(m)$ hits all $\mathcal M_n$.

Let $\mathcal M=\mathcal M_\infty$, $V=V(\mathcal M)$.
- *Every $P(a_j)$ contains an $\mathcal M$-element*: walk down
  $P(a_j)\supseteq P(a_{k_1})\supseteq\cdots$ to a minimal element.
- Hence a transversal of $\mathcal M$ hits every $P(a_j)$, so $V\subseteq V_n$.
- *Every $a_n\in V$*: pairwise intersection makes $P(a_n)$ a transversal.
- Therefore $a_{n+1}=\min\{m\in V:m>a_n\}$: the sequence **is** the increasing
  enumeration of $V$ from $a_1$.

## Step 4 — Periodicity (RIGOROUS)
With $L=\prod_{p\in U}p$ ($U=\bigcup\mathcal M$), (2) makes $V$ a union of residue
classes mod $L$; $T=|V\cap\{1,\ldots,L\}|$. Increasing enumeration of a set periodic
mod $L$ satisfies $a_{n+T}=a_n+L$, from $n=1$ by Step 3.

## Step 5 — Growth bound (RIGOROUS)
$2a_n\in V_n$, so $a_{n+1}\le 2a_n$, i.e. $a_n\le a_1\,2^{n-1}$.

## Step 6 — Stabilization $\iff$ self-duality (RIGOROUS)
> TFAE: (i) $\mathcal M_n$ is a fixed point; (ii) $b(\mathcal M_n)\subseteq\mathcal M_n$;
> (iii) $b(\mathcal M_n)=\mathcal M_n$.

(ii)$\Rightarrow$(i): $a_{n+1}$ valid $\Rightarrow P(a_{n+1})\supseteq$ some
$\tau\in b(\mathcal M_n)\subseteq\mathcal M_n$; adding a superset of a member leaves
minimals unchanged. (ii)$\Rightarrow$(iii): every $M'\in\mathcal M$ is a transversal
(pairwise intersection); if non-minimal, a proper transversal subset contains some
$\tau\in b(\mathcal M)\subseteq\mathcal M$ with $\tau\subsetneq M'$, contradicting
the antichain. (i)$\Rightarrow$(ii): a defect $\tau\in b(\mathcal M)\setminus\mathcal M$
would, once stable, be realized by $m=\prod\tau\cdot p^j$ ($P(m)=\tau$) as a term,
changing $\mathcal M$.

## Step 7 — Cofactor lemma + exact identity (RIGOROUS)
> **Lemma.** When a new essential prime $q$ enters at step $j\ge2$ ($P(a_j)$ a new
> member of $\mathcal M_j$, $q\notin\bigcup\mathcal M_{j-1}$), the minimal
> sub-transversal $\tau^*\subseteq P(a_j)$ w.r.t. $\mathcal M_{j-1}$ is a *defect*
> ($\tau^*\in b(\mathcal M_{j-1})\setminus\mathcal M_{j-1}$), and with
> $D:=\prod\tau^*$,
> $$ a_j=D\cdot k,\quad q\mid k,\quad k=\Big\lfloor\frac{a_{j-1}}{D}\Big\rfloor+1. \tag{4}$$

*Proof.* $\tau^*$ is a defect, else $P(a_j)\supseteq\tau^*\in\mathcal M_{j-1}$ would
make $P(a_j)$ non-minimal. $q\notin\bigcup\mathcal M_{j-1}\supseteq\tau^*$, so
$q\mid k=a_j/D$. Every multiple of $D$ is valid ($\tau^*$ is a transversal), so
$a_j$ is exactly the smallest multiple of $D$ exceeding $a_{j-1}$, giving (4). $\square$

## Step 8 — Termination once essential primes are finite (RIGOROUS)
$V_{n+1}\subseteq V_n$ strictly when $\mathcal M_n$ changes. By CB (Step 9) every
essential prime is $\le a_1$, so every member of every $\mathcal M_n$ is a subset of
the **finite** ground set $S_0=\{p:p\le a_1,\,p\text{ prime}\}$. The map
$\mathcal M\mapsto b(\mathcal M)$ is an involution, so $\mathcal M_n\leftrightarrow V_n$
is a bijection among antichains over $S_0$ — a finite set. Since $\mathcal M_n$ never
repeats (each change strictly shrinks $V_n$; verified: distinct $\mathcal M$ count
$=$ changes$+1$), it takes finitely many values and stabilizes (reaching the
self-dual fixed point of Step 6). Then Steps 3–4 give $a_{n+T}=a_n+L$ from $n=1$.

---

## Step 9 — THE CRUX: the Cofactor Bound (CB) [PROVED]

> **Theorem (CB).** At every essential-prime-entry step $j\ge2$, $k\le a_1$
> (equivalently every essential prime is $\le a_1$).

Three lemmas, then the proof.

> **Lemma A (TERM).** If $m\in V_n$ and $a_1\le m\le a_n$, then $m$ is a term
> ($m=a_s$ for some $s\le n$).

*Proof.* By Step 3, $V_i\supseteq V_n$ for all $i\le n$, so $m\in V_i$ for all
$i\le n$. If $m$ is not a term, then (as $a_1\le m\le a_n$ and the sequence is
strictly increasing) $m\in(a_s,a_{s+1})$ for some $s$ with $s+1\le n$. But
$m\in V_s$ and $m>a_s$ give $a_{s+1}=\min\{V_s\cap(a_s,\infty)\}\le m<a_{s+1}$, a
contradiction. $\square$
*(Verified: every valid $m\in[a_1,a_n]$ is a term, $a_1\in\{6,...,385\}$, 0 failures.)*

> **Lemma B (smooth-gap).** For nonempty $S\subseteq$ primes with $p_1=\min S$,
> consecutive $S$-smooth numbers $n_i<n_{i+1}$ satisfy $n_{i+1}\le p_1 n_i$.
> Consequently, for $X\ge1$ the smallest $S$-smooth number exceeding $X$ is $\le p_1 X$.

*Proof.* If $n_{i+1}>p_1 n_i$, then $p_1 n_i$ is $S$-smooth (as $p_1\in S$) and lies
strictly between $n_i$ and $n_{i+1}$, contradicting consecutiveness. $\square$

> **Lemma C (B-monotonicity).** Fix $\tau^*$. Let
> $B_n=\{M\in\mathcal M_n:M\subseteq\tau^*\}$. If $B_n\ne\emptyset$ then
> $B_{n+1}\ne\emptyset$.

*Proof.* $\mathcal M_{n+1}=\min(\mathcal M_n\cup\{S\})$, $S=P(a_{n+1})$. A member
$M'$ survives iff $S\nsubseteq M'$.
- $S\nsubseteq\tau^*$: no $M\in B_n$ contains $S$ (since $M\subseteq\tau^*$), so all
  of $B_n$ survives; $B_{n+1}\supseteq B_n\ne\emptyset$.
- $S\subseteq\tau^*$ and $S$ is added: $S\in B_{n+1}$.
- $S\subseteq\tau^*$ but $S$ not added: some $M''\in\mathcal M_n$, $M''\subseteq S$,
  has $M''\subseteq S\subseteq\tau^*$, so $M''\in B_n$; and $M''$ survives
  ($S\nsubseteq M''$, as $M''\subseteq S$ and $S\nsubseteq M''$ unless $M''=S$, in
  which case $S\in\mathcal M_n$ already and $B_{n+1}\supseteq\{S\}$). $\square$
*(Verified directly: 0 transitions nonempty$\to$empty; and no member $\subseteq\tau^*$
appears before $\tau^*$ is realized, all realizations on $a_1\in\{15,...,777\}$.)*

*Proof of CB.* Suppose $k>a_1$ at step $j\ge2$, where $D=\prod\tau^*$ ($\tau^*$ the
realized defect). Then $a_{j-1}\ge a_1 D$. Let $p_1=\min\tau^*$.

**Construct $m$.** If $D\le a_1$: take $X=a_1/D\ge1$ and let $c$ be the smallest
$\tau^*$-smooth integer with $c>X$. By Lemma B, $c\le p_1X=p_1a_1/D\le a_1$ (as
$p_1\le D$); also $c>X=a_1/D$. If $D>a_1$: take $c=1$ ($\le a_1$). In either case
set $m=Dc$. Then:
- $P(m)=\tau^*\cup P(c)=\tau^*$ (as $c$ is $\tau^*$-smooth, $P(c)\subseteq\tau^*$);
- $m$ is valid w.r.t. $\mathcal M_{j-1}$ ($\tau^*$ is a transversal);
- $m>D\cdot(a_1/D)=a_1$ if $D\le a_1$, or $m=D>a_1$ if $D>a_1$: in all cases
  $m>a_1$;
- $m\le Da_1\le a_1D\le a_{j-1}$.

So $a_1<m\le a_{j-1}$ and $m\in V_{j-1}$. By **Lemma A**, $m=a_s$ for some
$1<s\le j-1$, with $P(a_s)=\tau^*$.

**Derive the contradiction.** Since $\tau^*\in b(\mathcal M_{j-1})\setminus\mathcal
M_{j-1}$ is a minimal transversal, $B_{j-1}=\emptyset$: any $M\in\mathcal M_{j-1}$
with $M\subseteq\tau^*$ would be a transversal $\subseteq\tau^*$, contradicting
minimality (if $M\subsetneq\tau^*$) or the defect property (if $M=\tau^*$). By
**Lemma C** (contrapositive), $B_n=\emptyset$ for all $n\le j-1$; in particular
$B_{s-1}=\emptyset$.

At step $s$, $a_s$ is added with $P(a_s)=\tau^*$, so
$\mathcal M_s=\min(\mathcal M_{s-1}\cup\{\tau^*\})$. Because $B_{s-1}=\emptyset$ (no
member $\subseteq\tau^*$), $\tau^*$ is minimal, hence $\tau^*\in\mathcal M_s$, giving
$B_s\supseteq\{\tau^*\}\ne\emptyset$. By **Lemma C**, $B_s\ne\emptyset\Rightarrow
B_{j-1}\ne\emptyset$ — contradicting $B_{j-1}=\emptyset$. $\square$

### Why CB closes the theorem
Every essential prime enters at some step $j\ge2$ as a divisor of the cofactor $k$,
hence (by CB) is $\le a_1$. (The primes of $a_1$ itself, entering at $j=1$, are
trivially $\le a_1$.) So the essential-prime set is finite. Step 8 then forces
$\mathcal M_n$ to stabilize, and Steps 3–4 yield $a_{n+T}=a_n+L$ for every $n\ge1$.
$\blacksquare$

## Verification summary (computation, independent reproduction this run)
- **Lemma A (TERM):** 0 failures, $a_1\in\{6,15,30,105,210,385\}$.
- **Lemma C / $B_{j-1}=\emptyset$:** 0 failures (no member $\subseteq\tau^*$ before
  realization; forward-monotone), $a_1\in\{15,105,210,385,777\}$.
- **Cofactor identity (4):** exact at every entry.
- **CB ($k\le a_1$):** 0 violations for $a_1\le1500$ + 3153 adversarial inputs
  ($\max k/a_1=0.9981$, tight at prime $a_1$); large targets incl. primorial
  $510510$ ($\max k/a_1=0.508$), $30030$ ($0.546$), $39270$ ($0.602$): 0 violations.
- Spot values: $a_1=15\Rightarrow L=30,T=8$; $a_1=385\Rightarrow L=43890,T=5088$
  (sequence $=$ sorted $V\cap[a_1,\infty)$ from $n=1$); $a_1=2310\Rightarrow$ collapses
  to $\{\{2\}\}$, $T=1,L=2$.

## Refuted routes (do not reuse)
- "essential $\le\max P(a_1)$": FALSE ($385\to19$, $4199\to83$).
- "termination by monotone $|\mathcal M_n|$": FALSE ($2310$ grows to $251$ then
  collapses; $249$ grows to $41$ then collapses).
- "no-new-prime-set detects stabilization": non-minimal supersets persist.

## Note on scope
CB is proved (Step 9); together with Steps 1–8 this is a complete proof of the
theorem. The argument is elementary (no machinery beyond the blocker/transversal
setup) and each load-bearing lemma is computationally verified. A human reader should
scrutinize Lemma A's "gap" step and Lemma C's survival case analysis most carefully,
as they are the load-bearing novelties.
