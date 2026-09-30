# IMO 2026 Problem 5 — Candidate Solution v1

**Problem:** Find all functions $f: \mathbb{R}_{>0} \to \mathbb{R}_{>0}$ such that for all $x, y > 0$,
$$
\sqrt{\frac{x^2 + f(y)^2}{2}} \geq \frac{f(x) + y}{2} \geq \sqrt{x f(y)}.
$$

**Claimed Answer:** The only solutions are $f(x) = x + c$ for any constant $c \geq 0$.

---

## Complete Proof

### 1. Substitution and Basic Functional Equation

Let $g(x) = f(x) - x$. Then $f(x) = x + g(x)$ with $g: \mathbb{R}_{>0} \to \mathbb{R}_{>-x}$ (since $f(x) > 0$).

**Key step:** Set $x = f(y)$ in the original chain. The outer terms become
$$
\sqrt{\frac{f(y)^2 + f(y)^2}{2}} = f(y) \quad \text{and} \quad \frac{f(f(y)) + y}{2}.
$$
The rightmost term is $\sqrt{f(y) f(y)} = f(y)$. Thus the chain forces
$$
f(y) \geq \frac{f(f(y)) + y}{2} \geq f(y),
$$
so equality holds throughout: **$f(f(y)) = 2f(y) - y$ for all $y > 0$.**

In terms of $g$:
$$
f(f(y)) = f(y + g(y)) = y + g(y) + g(y + g(y)) = 2y + 2g(y) - y = y + 2g(y),
$$
hence **$g(y + g(y)) = g(y)$ for all $y > 0$.**   (★)

### 2. Iterates and Non-negativity of $g$

From $f(x) = x + g(x)$ and (★), a simple induction gives the $n$-th iterate:
$$
f^n(x) = x + n g(x) \quad \text{for all } n \in \mathbb{N}.
$$
Since every iterate must be positive, $x + n g(x) > 0$ for all $n$. If $g(x) < 0$, this fails for large $n$. Therefore **$g(x) \geq 0$ for all $x > 0$.**

### 3. Exact Squared Differences

Write $A = g(x)$, $B = g(y)$. Squaring both inequalities and simplifying:

**Right inequality difference:**
$$
R := \frac{(f(x)+y)^2}{4} - x f(y) = \frac{(x+A+y)^2}{4} - x(y+B)
= \frac{1}{4}\bigl[(x-y-B)^2 + (A-B)(2x+2y+A+B)\bigr].
$$

**Left inequality difference:**
$$
L := \frac{x^2+f(y)^2}{2} - \frac{(f(x)+y)^2}{4}
= \frac{x^2+(y+B)^2}{2} - \frac{(x+A+y)^2}{4}
= \frac{1}{4}\bigl[(x-y-B)^2 - (A-B)(2x+2y+A+B)\bigr].
$$

Since both $R \geq 0$ and $L \geq 0$, their combination gives the **exact bound**
$$
|A-B|(2x+2y+A+B) \leq (x-y-B)^2 \qquad \text{for all } x,y > 0. \tag{1}
$$

### 4. All Positive Values of $g$ Are Equal

Suppose $g$ attains two distinct positive values $A \neq B$. Then there exist $x,y$ with $g(x)=A$, $g(y)=B$.

By (★), $g(x + nA) = A$ and $g(y + mB) = B$ for all $n,m \in \mathbb{N}$.
Choose $n$ arbitrarily large, and pick $m \in \mathbb{N}_0$ to minimize $|x+nA - y - mB - B|$. Then
$$
|x+nA - y - mB - B| \leq B/2.
$$

Apply (1) to the pair $(x+nA,\; y+mB)$:
- Left side: $|A-B|(2(x+nA)+2(y+mB)+A+B) \sim 2nA|A-B| \to \infty$ as $n \to \infty$ (since $A>0$).
- Right side: $(x+nA - y - mB - B)^2 \leq B^2/4$, **bounded**.

Contradiction. Hence **$g$ takes at most one positive value**; its range is contained in $\{0, c\}$ for some $c \geq 0$.

### 5. The Range Cannot Be $\{0, c\}$ with $c > 0$

Assume $c > 0$ and both $0$ and $c$ are attained. Define
$$
C = \{x : g(x) = c\}, \quad F = \{x : g(x) = 0\}.
$$
Both are nonempty and partition $(0,\infty)$.

Take $x \in C$, $y \in F$. Then $A=c$, $B=0$, and (1) becomes
$$
c(2x+2y+c) \leq (x-y)^2. \tag{2}
$$

- For fixed $x \in C$, (2) implies $|x-y| \geq \sqrt{c(2x+c)}$ for all $y \in F$. Hence every $x \in C$ has a neighbourhood disjoint from $F$; **$C$ is open**.
- For fixed $y \in F$, (2) implies $|x-y| \geq \sqrt{c(2y+c)}$ for all $x \in C$. Hence every $y \in F$ has a neighbourhood disjoint from $C$; **$F$ is open**.

But $(0,\infty)$ is connected and cannot be the disjoint union of two nonempty open sets. Contradiction.

Therefore $g$ is **constant**: $g(x) = c \geq 0$ for all $x$.

### 6. Verification

For $f(x) = x + c$ with $c \geq 0$:
- $f: \mathbb{R}_{>0} \to \mathbb{R}_{>0}$ since $x+c > 0$.
- The three terms in the chain are exactly the quadratic mean, arithmetic mean, and geometric mean of $x$ and $y+c$:
  $$
  \sqrt{\frac{x^2+(y+c)^2}{2}} \geq \frac{x+y+c}{2} \geq \sqrt{x(y+c)},
  $$
  which is the standard QM-AM-GM inequality.

---

## Summary of Key Claims

1. **$f(f(x)) = 2f(x) - x$** — obtained by setting $x = f(y)$ in the original chain.
2. **$g(x+g(x)) = g(x)$** where $g(x)=f(x)-x$ — equivalent reformulation.
3. **$g(x) \geq 0$ for all $x$** — from positivity of iterates $f^n(x)=x+ng(x)$.
4. **Exact inequality (1):** $|g(x)-g(y)|(2x+2y+g(x)+g(y)) \leq (x-y-g(y))^2$ — derived by squaring and combining both original inequalities.
5. **All positive values of $g$ coincide** — orbit argument using (1) and unbounded growth of left side vs. bounded right side.
6. **Range cannot be $\{0,c\}$ with $c>0$** — topological connectedness argument using the separation forced by (2).
7. **$f(x) = x+c$ for $c \geq 0$** — the only solutions, verified by QM-AM-GM.

---

## Falsification Attempts on Intermediate Hypotheses

| Hypothesis | Attack | Outcome |
|------------|--------|---------|
| $g$ could be negative somewhere | Iterates $f^n(x)=x+ng(x)$ must stay positive for all $n$ | **Falsified** — forces $g \geq 0$ |
| $g$ could take two positive values $A \neq B$ | Use orbits $x+nA$, $y+mB$; choose $m$ to make RHS of (1) bounded while LHS $\to \infty$ | **Falsified** |
| $g$ could take values $\{0,c\}$ with $c>0$ | Separation inequality (2) makes both level sets open, contradicting connectedness of $(0,\infty)$ | **Falsified** |
| $f(x)=kx$ for $k \neq 1$ | Direct substitution shows left inequality fails unless $k=1$ | **Falsified** (only $f(x)=x$ works, which is $c=0$) |

---

## Evidence

- Algebraic derivation of (1) is internally checkable.
- Iterate formula $f^n(x)=x+ng(x)$ follows from $g(x+g(x))=g(x)$ by induction.
- Orbit density argument is a standard Diophantine approximation step.
- Topological connectedness argument is rigorous.
- Verification step uses only QM-AM-GM, a standard inequality.

---

## Confidence recorded by the generating lane: 0.99

The proof subsequently passed the portfolio system's adversarial review and
second-order verification gates. This is a model-based audit, not an official
IMO jury assessment.

---

## Open Issues

- None — the solution is complete and verified.
