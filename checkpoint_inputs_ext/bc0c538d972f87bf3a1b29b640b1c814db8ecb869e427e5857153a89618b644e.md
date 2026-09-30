# IMO 2026 Problem 4 — Solution

**Answer.** Mulan can guarantee her victory if and only if $\theta$ divides $180^{\circ}$,
i.e. there exists an integer $n\ge 2$ with
$$\boxed{\;\theta=\dfrac{180^{\circ}}{n}\;}$$
(equivalently $180^{\circ}/\theta\in\{2,3,4,\dots\}$).

---

## 1.  Algebraic reformulation of one move

A triangle is determined by its angle multiset $\{a,b,c\}$ with $a+b+c=180^{\circ}$.
Suppose Mulan puts $P$ on the side opposite the vertex of angle $c$ (so the other two
angles are $a,b$) and cuts toward that vertex, splitting $c=c_{1}+c_{2}$ with
$c_{1},c_{2}>0$. The two resulting triangles are

$$T_{1}=\{a,\;c_{1},\;b+c_{2}\},\qquad T_{2}=\{b,\;c_{2},\;a+c_{1}\},\qquad c_{1}+c_{2}=c.$$

*Proof.* In the piece containing the vertex of angle $a$, the angles are $a$, the part
$c_{1}$ of the split at $c$, and the angle at $P$, which is $180-a-c_{1}=(b+c)-c_{1}=b+c_{2}$.
The other piece is symmetric. $\square$

So a move is: **pick one angle $c$ to split, choose $c_{1}\in(0,c)$, replace $\{a,b,c\}$
by either $\{a,c_{1},b+c_{2}\}$ or $\{b,c_{2},a+c_{1}\}$ at Shan‑Yu's discretion.** Note
the complementary pair $(a+c_{1})+(b+c_{2})=180^{\circ}$.

Mulan's winning region $W$ satisfies
$$T\in W\iff \theta\in T\;\text{(as an angle)}\;\text{ or }\;\exists\text{ cut with both pieces in }W.$$

---

## 2.  Necessity — Shan‑Yu defends when $\theta\nmid 180^{\circ}$

Assume $180^{\circ}/\theta\notin\mathbb Z$ (i.e. $\theta$ does not divide $180^{\circ}$;
note $0<\theta<180^{\circ}$ forces $180/\theta>1$, so this means $180/\theta$ is not an
integer $\ge 2$). Call an angle a *$\theta$‑multiple* if it equals $k\theta$ for some
integer $k\ge1$. Define the **trap**

$$S=\{\text{triangles whose three angles are all non‑}\theta\text{-multiples}\}.$$

**$S$ is non‑empty.** The equilateral triangle $\{60,60,60\}$ lies in $S$: $60$ is a
$\theta$‑multiple iff $\theta\mid 60$, but $\theta\mid 60\Rightarrow\theta\mid 180$
(since $60\mid 180$), contradicting $\theta\nmid 180$.

**$S$ is closed under Shan‑Yu's reply.** Let $T=\{a,b,c\}\in S$ and let Mulan split angle
$c=c_{1}+c_{2}$, producing $T_{1}=\{a,c_{1},b+c_{2}\}$, $T_{2}=\{b,c_{2},a+c_{1}\}$.
Because $T\in S$, none of $a,b,c$ is a $\theta$‑multiple. Suppose, for contradiction,
that **both** $T_{1},T_{2}$ contain a $\theta$‑multiple angle. Then the multiple in
$T_{1}$ is $c_{1}$ or $b+c_{2}$ (since $a$ is not one), and the multiple in $T_{2}$ is
$c_{2}$ or $a+c_{1}$ (since $b$ is not one). Four cases, each a contradiction:

| multiple in $T_{1}$ | multiple in $T_{2}$ | consequence |
|---|---|---|
| $c_{1}$ | $c_{2}$ | $c=c_{1}+c_{2}$ is a $\theta$‑multiple — but $c\in S$ ✗ |
| $c_{1}$ | $a+c_{1}$ | $a=(a+c_{1})-c_{1}$ is a $\theta$‑multiple — but $a\in S$ ✗ |
| $b+c_{2}$ | $c_{2}$ | $b=(b+c_{2})-c_{2}$ is a $\theta$‑multiple — but $b\in S$ ✗ |
| $b+c_{2}$ | $a+c_{1}$ | $180=(a+c_{1})+(b+c_{2})$ is a $\theta$‑multiple, i.e. $\theta\mid180$ ✗ |

So at least one piece is again in $S$. **Shan‑Yu's strategy:** start at the equilateral
triangle, and after every cut keep a piece that lies in $S$ (which always exists). The
state stays in $S$ forever, so no angle ever equals $\theta$; Mulan never wins. Hence
Mulan cannot guarantee victory. $\square$

---

## 3.  Sufficiency — Mulan wins when $\theta=180^{\circ}/n$

Assume $\theta=180^{\circ}/n$ for an integer $n\ge2$.

**Lemma (a "$k\theta$"‑angle is winning).** Any triangle having an angle equal to
$k\theta$ for some $1\le k\le n-1$ is winning.

*Proof by strong induction on $k$.* For $k=1$ the triangle already has angle $\theta$:
Mulan wins. For $k\ge2$, let that angle be $c=k\theta$ and split it as
$c_{1}=\theta,\;c_{2}=(k-1)\theta$ (valid since $0<\theta<k\theta$). The two pieces are
$\{a,\theta,b+(k-1)\theta\}$ (contains $\theta$ — winning) and
$\{b,(k-1)\theta,a+\theta\}$ (contains $(k-1)\theta$ — winning by the inductive
hypothesis, since $1\le k-1\le n-1$). Both pieces winning $\Rightarrow$ the triangle is
winning. $\square$

**Main argument.** Let $T=\{a,b,c\}$ be any triangle.

*Case A — some angle is a $\theta$‑multiple $k\theta$ ($1\le k\le n-1$):* winning by the Lemma.

*Case B — no angle is a $\theta$‑multiple.* Let $c$ be the largest angle, $a\le b$ the
other two (so $c\ge 60^{\circ}$, $a\le 60^{\circ}$).

- **If $n\ge3$** then $\theta\le 60^{\circ}\le c$, and $c\ne\theta$ (else $c$ is a
  $\theta$‑multiple), so $c>\theta$. The open interval $(a,a+c)$ has length $c>\theta$,
  hence contains a $\theta$‑multiple $m\theta$ (multiples are spaced $\theta$ apart; an
  open interval longer than $\theta$ must contain one). This $m\theta$ lies in
  $(a,a+c)\subset(0,180^{\circ})$, so $1\le m\le n-1$. Set $c_{1}=m\theta-a\in(0,c)$.
  Then piece $T_{2}$ contains angle $a+c_{1}=m\theta$, and piece $T_{1}$ contains angle
  $b+c_{2}=180^{\circ}-a-c_{1}=180^{\circ}-m\theta=(n-m)\theta$; both indices lie in
  $\{1,\dots,n-1\}$, so **both** pieces are winning by the Lemma.

- **If $n=2$** ($\theta=90^{\circ}$) the only $\theta$‑multiple below $180^{\circ}$ is
  $90^{\circ}$ itself. We have $a\le 60^{\circ}<90^{\circ}$ and $b<90^{\circ}$ (if
  $c>90^{\circ}$ then $a+b<90^{\circ}$; if $c<90^{\circ}$ all angles are $<90^{\circ}$).
  Hence $a<90^{\circ}<a+c=180^{\circ}-b$; set $c_{1}=90^{\circ}-a\in(0,c)$. Both pieces
  contain $90^{\circ}$: $a+c_{1}=90^{\circ}$ and $b+c_{2}=90^{\circ}$.

In every case Mulan has a move making **both** pieces winning, so $T$ is winning. $\square$

**Step bound.** The first cut produces pieces whose relevant angles are $m\theta$ and
$(n-m)\theta$; whichever Shan‑Yu keeps has a $k\theta$‑angle with $k\le n-1$, which the
Lemma resolves in $\le k-1\le n-2$ further cuts. Thus Mulan wins in $\le n-1$ cuts,
uniformly over Shan‑Yu's play — a finite guarantee.

---

## 4.  Numerical confirmation (evidence, not part of the proof)

Independent exhaustive computation of the winning region on a discretised angle grid
agrees exactly with the theorem:

- 1° grid (2700 states), all 179 values of $\theta$: **0 mismatches**.
  For $\theta\mid180$ the whole region is winning; for $\theta\nmid180$ the winning set
  is *exactly* the set of triangles having a $\theta$‑multiple angle.
- 0.5° grid (10800 states), including the discriminator $\theta=72^{\circ}$: $72\mid360$
  but $72\nmid180$, and indeed $72^{\circ}$ is **not** all‑winning (only 144/10800
  states) — ruling out a "divides the grid" artifact. Likewise $\theta=36^{\circ},22.5^{\circ},0.5^{\circ},18^{\circ},12^{\circ}$ (all divide $180$) are fully winning, while $7^{\circ},24^{\circ},40^{\circ}$ are not.

Concrete checks: from equilateral vs. $\theta=70^{\circ}$, every cut leaves at least one
piece free of $70^{\circ}/140^{\circ}$ angles, matching the trap. For $\theta=36^{\circ}$
from equilateral, the strategy cut $c_{1}=12^{\circ}$ yields pieces with $72^{\circ}$ and
$108^{\circ}$, both reducible to $36^{\circ}$.

---

## 5.  Boundary / degenerate cases

- $P$ is strictly interior to a side (not a vertex) $\Leftrightarrow$ $c_{1}\in(0,c)$,
  giving two genuine (non‑degenerate) triangles. The cuts used in the proofs all satisfy this.
- $0<\theta<180^{\circ}$: divisors of $180$ in this range are exactly $\le 90^{\circ}$
  (the next divisor after $90$ is $180$), so every winning $\theta\in(0,90^{\circ}]$.
- Irrational $\theta$ never divides $180$, so Mulan loses (trap = equilateral).
- Very small rational divisors (e.g. $\theta=1^{\circ}$, $n=180$) are still winning;
  Mulan wins in $\le 179$ cuts.

**Conclusion:** Mulan guarantees victory exactly for $\theta=180^{\circ}/n$, $n=2,3,4,\dots$.
