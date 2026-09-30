# IMO 2026 Problem 1 — Complete Proof

## Problem Statement

There are $2026$ integers greater than $1$ written on a blackboard, not necessarily distinct. In a move, Confucius chooses two integers $m>1$ and $n>1$ from different places on the blackboard and replaces these two integers with $\gcd(m,n)$ and $\frac{\operatorname{lcm}(m,n)}{\gcd(m,n)}$. He continues to make moves while it is possible to do so.

**Prove that:**
1. The process always terminates with exactly one integer $M$ on the blackboard greater than $1$.
2. The value of $M$ does not depend on the choices of Confucius.

---

## Notation and Preliminaries

For an integer $x > 1$ and a prime $p$, let $v_p(x)$ denote the exponent of $p$ in the prime factorisation of $x$ (with $v_p(1) = 0$ for all $p$). The **total number of prime factors with multiplicity** is
\[
\Omega(x) = \sum_{p} v_p(x).
\]
For $x = 1$ we set $\Omega(1) = 0$.

Recall the identities:
- $\gcd(m,n) \cdot \operatorname{lcm}(m,n) = m n$,
- $v_p(\gcd(m,n)) = \min(v_p(m), v_p(n))$,
- $v_p(\operatorname{lcm}(m,n)) = \max(v_p(m), v_p(n))$,
- $\frac{\operatorname{lcm}(m,n)}{\gcd(m,n)}$ has $p$-adic valuation $|v_p(m) - v_p(n)|$.

A move replaces $m, n > 1$ with
\[
g = \gcd(m,n), \qquad L = \frac{\operatorname{lcm}(m,n)}{\gcd(m,n)}.
\]
For each prime $p$, the pair of exponents $(v_p(m), v_p(n))$ is replaced by $(\min(a,b), |a-b|)$.

---

## Part 1: Termination with exactly one integer $> 1$

### Lemma 1 (Product non-increase)
The product of all integers on the board never increases. In each move it is multiplied by $\frac{1}{\gcd(m,n)} \le 1$.

*Proof.* The product of the two new numbers is $g \cdot L = \operatorname{lcm}(m,n) = \frac{mn}{g}$. The total product is therefore multiplied by $\frac{1}{g} \le 1$. $\square$

### Lemma 2 (Lexicographic descent)
Define the **state** of the board by the pair $(K, S)$ where
- $K$ = number of integers $> 1$ on the board,
- $S$ = sum of $\Omega(x)$ over all integers on the board.

Order states lexicographically: $(K_1, S_1) < (K_2, S_2)$ iff $K_1 < K_2$, or $K_1 = K_2$ and $S_1 < S_2$.

**Every legal move strictly decreases the state.**

*Proof.* Consider a move on $m, n > 1$ with $g = \gcd(m,n)$, $L = \operatorname{lcm}(m,n)/g$.

For each prime $p$, the sum of exponents changes from $a+b$ to $\min(a,b) + |a-b| = \max(a,b)$. The decrease is $\min(a,b) = v_p(g)$. Hence
\[
\Delta S = -\sum_p v_p(g) = -\Omega(g).
\]

**Case 1:** $g = 1$. Then $\Omega(g) = 0$, so $S$ is unchanged. But $L = mn > 1$ and $g = 1$, so one number $>1$ is replaced by $1$. Thus $K$ decreases by $1$.

**Case 2:** $g > 1$. Then $\Omega(g) \ge 1$, so $S$ decreases by at least $1$.
- If $m \neq n$, then $|v_p(m)-v_p(n)| > 0$ for some $p$, so $L > 1$. Both new numbers are $> 1$, hence $K$ is unchanged.
- If $m = n$, then $g = m = n$ and $L = 1$. One number $>1$ is replaced by $1$, so $K$ decreases by $1$.

In all cases $(K,S)$ strictly decreases lexicographically. $\square$

### Termination
Initially $K = 2026$ and $S \ge 2026$. The state $(K,S)$ takes values in $\mathbb{N}^2$ with the well-founded lexicographic order, so the process must terminate.

### Final state
At termination no move is possible, so $K \le 1$. A legal move can never
remove every nonunit: if $g>1$, then the first output is the nonunit $g$;
if $g=1$, then the second output is the nonunit $mn$. Since the initial board
contains nonunits, every reachable board has at least one, so $K\ge1$.
Therefore $K=1$: **exactly one integer greater than $1$ remains.** $\square$

---

## Part 2: Uniqueness of the final integer

### Invariant: gcd of prime exponents
Fix a prime $p$. Consider the multiset of exponents $\{v_p(x) : x \text{ on the board}\}$. Initially it has $2026$ elements (the $v_p$ of the starting integers).

A move on $m,n$ replaces the two entries $a = v_p(m)$, $b = v_p(n)$ with $\min(a,b)$ and $|a-b|$. The **gcd of the multiset is unchanged** by this operation because
\[
\gcd(a,b) = \gcd(\min(a,b), |a-b|)
\]
and the other elements are untouched. (This is exactly one step of the Euclidean algorithm.)

Thus **for every prime $p$, the quantity**
\[
g_p := \gcd\bigl(\{v_p(x) : x \text{ on the board}\}\bigr)
\]
**is invariant throughout the process.** Let $g_p$ denote this invariant value, computed from the initial $2026$ integers.

### Behaviour of $p$-adic valuations during the process
As long as at least two numbers on the board have positive $p$-adic valuation, they are both $>1$ (since they are divisible by $p$), so Confucius may choose that pair. Performing a move on such a pair replaces their $p$-valuations $a,b>0$ by $\min(a,b)$ and $|a-b|$. The sum of all $p$-adic valuations on the board **strictly decreases** in this case because
\[
a+b \;>\; \min(a,b) + |a-b| \quad\text{for } a,b>0.
\]
The sum of $p$-adic valuations is a non‑negative integer; therefore we cannot perform infinitely many moves that involve two positive $p$-valuations. Consequently, the process must eventually reach a state where **at most one number on the board has positive $p$-adic valuation**.

### Determination of the final $p$-adic valuation
By Part 1, the process terminates with exactly one integer $M>1$ on the board; all other $2025$ integers equal $1$.

For the prime $p$, all numbers equal $1$ have $v_p=0$. The number $M$ has some valuation $v_p(M) \ge 0$. The multiset of $p$-adic valuations at the end therefore consists of one entry $v_p(M)$ and $2025$ zeros. The gcd of this multiset is exactly $v_p(M)$ (since $\gcd(x,0,\dots,0) = x$). By invariance,
\[
v_p(M) = g_p = \gcd\bigl(v_p(a_1), v_p(a_2), \dots, v_p(a_{2026})\bigr),
\]
where $a_1,\dots,a_{2026}$ are the initial integers.

This argument holds for **every prime $p$ independently**. The operations on different primes are coupled only by the choice of which pair of numbers to pick; however, as argued above, as long as a prime $p$ has at least two positive valuations, those two numbers are $>1$ and form a legal pair. The process cannot “get stuck” for $p$ before its valuations reduce to the invariant gcd.

### The final integer $M$
The final integer $M$ is uniquely determined by its $p$-adic valuations for all primes $p$:
\[
M = \prod_{p \text{ prime}} p^{\,g_p},
\qquad\text{where } g_p = \gcd\bigl(v_p(a_1), v_p(a_2), \dots, v_p(a_{2026})\bigr).
\]
This value depends **only** on the initial multiset of $2026$ integers, not on the sequence of moves. $\square$

---

## Remarks

1. The invariant $g_p = \gcd_i v_p(a_i)$ is the exponent-wise gcd of the initial numbers. It is **not** the usual $\gcd(a_1,\dots,a_{2026})$ (which would use $\min$ instead of $\gcd$ of exponents). For example, starting with $\{4, 8\}$ (exponents $2,3$), the final number is $2^{\gcd(2,3)} = 2$, while $\gcd(4,8) = 4$.

2. The termination proof used the well-founded measure $(K, \sum \Omega)$. The invariant proof is completely independent of the choices made; it only uses the fact that the process *must* terminate with one number $>1$, which was established in Part 1.

3. The number $2026$ plays no special role; the proof works for any initial number $N \ge 2$ of integers $> 1$.

---

**Proof complete.** The final integer is
\[
\boxed{M = \prod_{p \text{ prime}} p^{\,\gcd(v_p(a_1),\,v_p(a_2),\,\dots,\,v_p(a_{2026}))}}
\]
where $v_p(x)$ denotes the exponent of the prime $p$ in the factorisation of $x$. This integer is completely determined by the initial multiset of $2026$ integers and does not depend on the choices Confucius makes.
