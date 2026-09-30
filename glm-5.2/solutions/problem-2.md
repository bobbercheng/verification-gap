# IMO 2026 Problem 2 — Candidate v2 (status: complete; revised after adversarial review)

## Problem (verbatim)
Let $ABC$ be a triangle; $M,N$ the midpoints of $AB,AC$. Points $K,L$ are chosen
strictly inside $\triangle BMC$ and $\triangle BNC$ respectively, with $K$ strictly
inside $\triangle ABL$ and $L$ strictly inside $\triangle AKC$, such that
$$\angle KBA=\angle ACL,\qquad \angle LBK=\angle LNC,\qquad \angle LCK=\angle BMK.$$
Let $O$ be the circumcentre of $\triangle AKL$. Prove $OM=ON$.

## 0. Revision summary (changes from v1, addressing review_v1.json `required_fixes`)
1. **Ordering derivation (REQUIRED FIX #1, load-bearing).** v1 *asserted* "ray $BL$
   makes angle $\alpha+\beta$ with $BA$" and "ray $CK$ makes angle $\alpha+\gamma$
   with $CA$" without proof. New §3.0 derives these additive orderings
   $\angle LBA=\alpha+\beta$ and $\angle ACK=\alpha+\gamma$ **from the
   strict-interior hypotheses** (one line each). §3.1 exhibits the concrete
   counterexample showing the ordering genuinely rests on the interiors: a
   solution of the three *bare unsigned-angle equations* that violates the
   interiors has $|OM-ON|\approx 0.381$.
2. **experiment.py repaired (REQUIRED FIX #2).** v1 line `r=rng.default_rng(s)`
   raised `AttributeError` (`rng` was already a `Generator`), so the script did not
   run. Fixed to `r=rng`; the script now executes and reproduces every cited
   numerical confirmation (see §8 for the actual output).
3. **Labeling reconciled (REQUIRED FIX #3).** The quotient $Q$ has **26 terms of
   total degree 10** (v1 mixed "degree 26"/"degree 10"). Stated consistently.
4. **Certificate clarified (rigor hardening).** The exact identity is
   **numerator-level**, $\mathrm{num}(E)=Q\,\mathrm{num}(G2)$; the value-level
   equality $E=Q\cdot G2$ does **not** hold (denominators differ). §5 states the
   precise identity and the implication chain $G2{=}0\Rightarrow E{=}0$ with the
   non-vanishing-denominator condition, so the step is unambiguous. §7 lists
   *every* denominator factor (including $\det(K,L)$, omitted in v1) and verifies
   each is non-zero at valid configurations.

The proof structure is otherwise unchanged and was independently re-verified this
run: symbolic check `expand(num(E)-Q·num(G2))≡0` (1486-term numerator ÷ 395-term
$\mathrm{num}(G2)$, zero remainder), and $|OM-ON|\lesssim10^{-14}$ on every valid
configuration.

## 1. Coordinate set-up
By a rigid motion put $A=(0,0)$, $B=(c,0)$, $C=(b\cos\theta,b\sin\theta)$ with
$c=|AB|>0$, $b=|AC|>0$, $\theta=\angle BAC\in(0,\pi)$. Then $M=\tfrac12 B$,
$N=\tfrac12 C$. Define the three common angle values
$$\alpha=\angle KBA=\angle ACL,\qquad \beta=\angle LBK=\angle LNC,\qquad
\gamma=\angle LCK=\angle BMK.$$
Since $M\in BA$ and $N\in CA$, $\angle MBK=\angle KBA=\alpha$ and
$\angle LCN=\angle ACL=\alpha$. The sine rule in $\triangle MBK$ and $\triangle LCN$
(both non-degenerate by the strict interiors) gives $\alpha+\gamma<\pi$ and
$\alpha+\beta<\pi$; in particular $0<\alpha,\beta,\gamma$ and $0<\alpha+\beta,\alpha+\gamma<\pi$.

## 2. Position of $K$ and $L$
In $\triangle MBK$ ($MB=c/2$, $\angle MBK=\alpha$, $\angle BMK=\gamma$) the sine rule
gives $BK=\dfrac c2\dfrac{\sin\gamma}{\sin(\alpha+\gamma)}$. Ray $BK$ makes the
unsigned angle $\alpha$ with ray $BA$ and points into the upper half-plane, hence
has direction unit $(-\cos\alpha,\sin\alpha)$. Therefore, with
$p:=\dfrac{\sin\gamma}{\sin(\alpha+\gamma)}$,
$$K=B+BK\cdot(-\cos\alpha,\sin\alpha)=\frac c2\bigl(2-p\cos\alpha,\;p\sin\alpha\bigr).\tag{2K}$$
Similarly in $\triangle LCN$ ($CN=b/2$, $\angle LCN=\alpha$, $\angle LNC=\beta$),
$CL=\dfrac b2\dfrac{\sin\beta}{\sin(\alpha+\beta)}$, and ray $CL$ makes unsigned
angle $\alpha$ with ray $CA=(-\cos\theta,-\sin\theta)$, pointing toward the
$B$-side, i.e. direction $(-\cos(\theta+\alpha),-\sin(\theta+\alpha))$. With
$q:=\dfrac{\sin\beta}{\sin(\alpha+\beta)}$,
$$L=\frac b2\bigl(2\cos\theta-q\cos(\theta+\alpha),\;2\sin\theta-q\sin(\theta+\alpha)\bigr).\tag{2L}$$
(These are v1's formulas; both were hand-checked including ray directions and
re-confirmed on solved configurations to machine precision.)

## 3. The two remaining angle conditions as algebraic constraints

### 3.0 Deriving the additive angular orderings from the interiors (REQUIRED FIX #1)
The translations below use the **additive** orderings $\angle LBA=\alpha+\beta$ and
$\angle ACK=\alpha+\gamma$. These are *not* conventions; they are forced by the
strict-interior hypotheses:

* ($K$ strictly inside $\triangle ABL$.) At vertex $B$ of $\triangle ABL$ the wedge
  is bounded by rays $BA$ and $BL$. Since $K\in\mathrm{int}(\triangle ABL)$, ray
  $BK$ lies strictly inside this wedge, so the unsigned angles add:
  $$\angle ABL=\angle ABK+\angle KBL=\angle KBA+\angle LBK=\alpha+\beta.$$
  Thus $\angle LBA=\alpha+\beta$, and ray $BL$ has direction
  $(-\cos(\alpha+\beta),\sin(\alpha+\beta))$ (rotating $BA=(-1,0)$ toward the upper
  half-plane by $\alpha+\beta<\pi$).

* ($L$ strictly inside $\triangle AKC$.) At vertex $C$ of $\triangle AKC$ the wedge
  is bounded by rays $CA$ and $CK$. Since $L\in\mathrm{int}(\triangle AKC)$, ray
  $CL$ lies strictly inside this wedge, so
  $$\angle ACK=\angle ACL+\angle LCK=\alpha+\gamma.$$
  Thus ray $CK$ has direction $(-\cos(\theta+\alpha+\gamma),-\sin(\theta+\alpha+\gamma))$.

(Without the interior hypotheses only the unsigned equations would be known,
admitting the "wrong" branch $\angle LBA=|\alpha-\beta|$ etc.; see §3.1.)

### 3.1 The ordering is load-bearing (concrete counterexample)
A configuration can satisfy the three bare unsigned-angle equations while
**violating** the interiors. The repaired `experiment.py` exhibits one for
$A=(0,0),B=(2,0),C=(1.8,1.5)$: least-squares drives all three angle residuals to
$\sim10^{-15}$, yet the barycentric coordinates go negative
($\lambda^{\min}_{BNC}\approx-0.043$, $\lambda^{\min}_{AKC}\approx-0.029$, i.e.
$L\notin\mathrm{int}\triangle BNC$ and $L\notin\mathrm{int}\triangle AKC$) and
$|OM-ON|\approx 0.381$. By contrast every genuinely-interior solution found has
$|OM-ON|\lesssim10^{-14}$. This is why §3.0 must be invoked before writing G1,G2.

### 3.2 Algebraic form of $\angle LBK=\beta$ (G1)
Ray $BL$ has direction $(-\cos(\alpha+\beta),\sin(\alpha+\beta))$, so $L-B$ is
parallel to it: the 2-D cross product $(L-B)\times(-\cos(\alpha+\beta),\sin(\alpha+\beta))=0$.
Substituting (2L) and simplifying with $q=\sin\beta/\sin(\alpha+\beta)$ and
product-to-sum gives first
$$b\sin(\theta+\alpha+\beta)-\tfrac b2\,q\sin(\theta+2\alpha+\beta)-c\sin(\alpha+\beta)=0,$$
then (multiply by $\sin(\alpha+\beta)$ and apply
$\sin X\sin Y=\tfrac12[\cos(X-Y)-\cos(X+Y)]$)
$$\boxed{\;(\mathrm{G1})\qquad b\bigl[\cos\theta-\cos(\theta+2\alpha+\beta)\cos\beta\bigr]=2c\sin^{2}(\alpha+\beta)\;}$$

### 3.3 Algebraic form of $\angle LCK=\gamma$ (G2)
Ray $CK$ has direction $(-\cos(\theta+\alpha+\gamma),-\sin(\theta+\alpha+\gamma))$;
$K-C$ parallel to it gives, after substituting (2K) with $p=\sin\gamma/\sin(\alpha+\gamma)$
and the same simplification (equivalently by the $B\leftrightarrow C$ swap of G1),
$$\boxed{\;(\mathrm{G2})\qquad 2b\sin^{2}(\alpha+\gamma)=c\bigl[\cos\theta-\cos(\theta+2\alpha+\gamma)\cos\gamma\bigr]\;}$$
Both translations were checked numerically against independently-solved configurations
(residuals $\le1.6\text{e-}13$).

## 4. Antipode reformulation of $OM=ON$
Let $A'=2O$ be the point antipodal to $A$ on the circumcircle of $\triangle AKL$.
Since $K\in\mathrm{int}\triangle ABL$ forces $K$ off the edge $AL$, the points
$A,K,L$ are non-collinear, $\det(K,L)\ne0$, and $O$ exists. The circumcenter equations
$O\!\cdot\! K=|K|^{2}/2$, $O\!\cdot\! L=|L|^{2}/2$ are equivalent to
$$A'\!\cdot\! K=|K|^{2},\qquad A'\!\cdot\! L=|L|^{2}\qquad(\text{i.e. } A'K\perp AK,\;A'L\perp AL).\tag{4}$$
Since $M=B/2$ and $N=C/2$,
$$OM=\tfrac12|A'-B|,\qquad ON=\tfrac12|A'-C|,$$
so
$$OM=ON\;\Longleftrightarrow\;|A'-B|=|A'-C|\;\Longleftrightarrow\;A'\!\cdot\!(C-B)=\tfrac12(b^{2}-c^{2}).\tag{$\star$}$$
(Geometrically: $A'$ lies on the perpendicular bisector of $BC$.) **It suffices to
prove ($\star$).**

## 5. The closing identity (exact, numerator-level symbolic certificate)

### 5.1 Setup
Scale so $c=1$ (similarity preserves $OM=ON$). In any valid configuration (G1)
holds, hence (the G1 bracket being $>0$, see §7)
$$b=\frac{2\sin^{2}(\alpha+\beta)}{\cos\theta-\cos(\theta+2\alpha+\beta)\cos\beta}.\tag{5.1}$$
With $A'$ determined by (4), define
$$E\;:=\;A'\!\cdot\!(C-B)-\tfrac12(b^{2}-1).\tag{5.2}$$
We must show $E=0$; by ($\star$) this is $OM=ON$. We use only (G2) beyond (G1).

### 5.2 The exact identity
Apply the Weierstrass substitution $t_X=\tan(X/2)$ for $X\in\{\theta,\alpha,\beta,\gamma\}$;
every quantity above becomes a rational function in
$\mathbf t=(t_\theta,t_\alpha,t_\beta,t_\gamma)$. Write
$E=\mathrm{num}(E)/\mathrm{den}(E)$ and $G2=\mathrm{num}(G2)/\mathrm{den}(G2)$ as
obtained by `together`/`fraction`. **Exact symbolic computation** gives
$$\boxed{\;\mathrm{num}(E)=Q\cdot\mathrm{num}(G2)\;}\tag{5.3}$$
where $Q\in\mathbb Q[t_\theta,t_\alpha,t_\beta]$ is a polynomial of **total degree
$10$ with $26$ terms** (recorded in `certificate_quotient.txt`; notably it is
independent of $t_\gamma$). The check
$\mathrm{expand}\bigl(\mathrm{num}(E)-Q\cdot\mathrm{num}(G2)\bigr)$ is the **zero
polynomial**: $\mathrm{num}(E)$ has $1486$ terms, $\mathrm{num}(G2)$ has $395$ terms,
and the division leaves zero remainder. This is a finite sequence of rational
operations in $\mathbb Q[\mathbf t]$ — a hand-checkable exact identity, not a
numerical experiment.

### 5.3 Why the numerator identity suffices (and why $E=Q\cdot G2$ is *not* asserted)
The identity is at the **numerator** level. The value-level equality
$E=Q\cdot G2$ does **not** hold in general: the denominators satisfy
$\mathrm{den}(E)\ne\mathrm{den}(G2)$ (a direct numerical evaluation of $E-Q\cdot G2$
is $\mathcal O(1)$–$\mathcal O(b^{2})$, not $0$). This is immaterial, because at
every **valid** configuration both denominators are non-zero (§7), hence
$$G2=0\;\Longleftrightarrow\;\mathrm{num}(G2)=0\;\Longrightarrow\;\mathrm{num}(E)=Q\cdot0=0
\;\Longrightarrow\;E=0,\tag{5.4}$$
which is exactly what is needed. (Equivalently: $\mathrm{num}(G2)$ divides
$\mathrm{num}(E)$ in $\mathbb Q[\mathbf t]$, so every zero of $G2$ that is not a pole
of $E$ is a zero of $E$.)

## 6. Conclusion
In any configuration satisfying the hypotheses, (G1) and (G2) both hold (§3).
By (5.3)–(5.4), $E=0$, i.e. $A'\!\cdot\!(C-B)=\tfrac12(b^{2}-c^{2})$. By ($\star$)
this is $|A'-B|=|A'-C|$, i.e. $OM=ON$. $\quad\blacksquare$

## 7. Degeneracy / non-vanishing denominators
- Non-degenerate triangle: $\theta\in(0,\pi)$, $b,c>0$ (given).
- Strict interiors $\Rightarrow0<\alpha,\beta,\gamma<\pi$ and
  $\alpha+\beta<\pi,\;\alpha+\gamma<\pi$ (§1); hence $\sin(\alpha+\beta)$,
  $\sin(\alpha+\gamma)>0$ and the half-angle parameters $t_X=\tan(X/2)$ are finite.
- The (G1) bracket equals $2c\sin^{2}(\alpha+\beta)/b>0$ in any valid config, so
  (5.1) involves no division by zero and determines the correct $b>0$.
- $A,K,L$ non-collinear ( $K\in\mathrm{int}\triangle ABL\Rightarrow K\notin$ line $AL$ )
  $\Rightarrow\det(K,L)\ne0$; $O$, $A'$ are well defined.
- **Denominator non-vanishing.** The rational expressions are built from:
  $A'=(\text{adjugate of }(K,L))/\det(K,L)$, $b=2\sin^{2}(\alpha+\beta)/(\text{G1 bracket})$,
  $p=\sin\gamma/\sin(\alpha+\gamma)$, $q=\sin\beta/\sin(\alpha+\beta)$, and each
  half-angle substitution $t\mapsto 2t/(1{+}t^{2}),(1{-}t^{2})/(1{+}t^{2})$. Hence
  every factor appearing in $\mathrm{den}(E)$ or $\mathrm{den}(G2)$ is one of
  $\det(K,L)$ (in $\mathrm{den}(E)$ only), the (G1) bracket, $\sin(\alpha+\beta)$,
  $\sin(\alpha+\gamma)$, or $(1+t_X^{2})$; at every valid configuration these are
  respectively $\ne0$ (non-collinearity), $>0$, $>0$, $>0$, $>0$. Therefore
  $\mathrm{den}(E),\mathrm{den}(G2)\ne0$, justifying the equivalences in (5.4).
  (We do not need the exact factorization — only that no factor vanishes, which is
  immediate from the construction.) Boundary (excluded) cases are reached by
  continuity of the polynomial identity (5.3).

## 8. Evidence files (this run; all reproducible)
- **`experiment.py`** (REPAIRED, runs): numerical root-finding of $K,L$ over several
  triangles via the three unsigned-angle residuals, then checks interiors and
  $|OM-ON|$. Actual output on the shipped configs:
  - $C=(0.5,2)$: $|OM-ON|=6.55\text{e-}15$, all interior coords $>0$.
  - $C=(1.0,2.5)$ (with $B=(3,0)$): $|OM-ON|=1.55\text{e-}15$, all interior coords $>0$.
  - $C=(1.8,1.5)$: bare-angle solution but **invalid** ($\lambda^{\min}<0$),
    $|OM-ON|=0.381$ — the §3.1 counterexample.
  - $C=(-0.7,1.6)$: $|OM-ON|=1.07\text{e-}14$, all interior coords $>0$.
- **`certificate_quotient.txt`**: the explicit $Q$ (**26 terms, total degree 10**,
  independent of $t_\gamma$).
- **`review_symbolic.py`** (re-run this revision): confirms
  $\mathrm{num}(E)-Q\cdot\mathrm{num}(G2)\equiv0$ (`ZERO! Identity confirmed`),
  with $\mathrm{num}(E)$ 1486 terms and $\mathrm{num}(G2)$ 395 terms.
- **`review_verify.py`** (re-run): value-level check $E=Q\cdot G2$ **fails**
  ($\max|E-Q\cdot G2|\sim3\!\cdot\!10^{11}$), confirming the identity is
  numerator-level ($\mathrm{den}(E)\ne\mathrm{den}(G2)$); the proof correctly uses
  numerator divisibility.
- An independent sweep (review_v1.json) over 40 random triangles gave 1698 valid
  configurations with $\max|OM-ON|\approx1.1\text{e-}13$ and
  $\max(|G1\text{-res}|,|G2\text{-res}|)\le1.6\text{e-}13$.

## 9. Open issues (honest)
- The closing step is a **computer-algebra identity**: exact and machine-checkable,
  but opaque. A compact human-derivable closed form for $Q$ (or a synthetic proof of
  $A'\in\mathrm{pbis}(BC)$) was sought (`trigsimp`) but did not terminate within
  budget. The zero-remainder polynomial certificate is a complete rigorous proof.
- The value-level identity $E=Q\cdot G2$ fails (denominators differ); the proof
  relies on the numerator-level divisibility (5.3), now stated explicitly with the
  non-vanishing-denominator justification (§7). This is a clarification, not a gap.
- Existence of the configuration is assumed by the problem; the proof is universal
  over all valid configurations (non-emptiness confirmed numerically for generic
  triangles; e.g. the three valid configs in §8).
