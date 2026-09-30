# IMO 2026 Problem 5 — candidate solution

**Status: complete.**

## Claimed classification

The solutions are
\[
\boxed{f(x)=x+C\quad\text{for all }x>0,\qquad C\ge 0.}
\]

No continuity, measurability, monotonicity, boundedness, or surjectivity is assumed.

## Hypotheses and falsification record

1. **Identity-only hypothesis.** This is false: for example, \(f(x)=x+1\) changes the chain into RMS--AM--GM for the two numbers \(x\) and \(y+1\).
2. **Affine/scaling hypothesis.** Writing \(f(x)=ax+b\), the necessary iterate identity derived below forces \((a-1)^2=0\), so the only possible affine slope is \(a=1\). The remaining translations with \(b\ge0\) survive exact substitution.
3. **Nonlinear power-law hypothesis.** If \(f(x)=x^p\), the necessary iterate identity derived below becomes \(y^{p^2}=2y^p-y\). Differentiating this identity at \(y=1\) gives \(p^2=2p-1\), hence \(p=1\); thus no nonlinear real power works. Exact spot checks also give upper squared margins \(-15\) for \(f(x)=\sqrt{x}\) at \((x,y)=(1,4)\), and \(-260\) for \(f(x)=x^2\) at \((4,2)\).
4. **Nonconstant orbitwise-shift hypothesis.** The necessary iterate identity alone permits pathological candidates. For instance, \(f(x)=x\) for \(x<1\) and \(f(x)=x+1\) for \(x\ge1\) obeys \(f(f(t))=2f(t)-t\), but at \((x,y)=(1,1/2)\) the squared upper margin is
   \[
   2(1^2+(1/2)^2)-(2+1/2)^2=-\frac{15}{4}<0.
   \]
   The quadratic displacement estimate in the proof rules out every nonconstant orbitwise shift.
5. **Translation hypothesis.** Deterministic grid tests found no negative squared margin for several \(C\ge0\), while non-unit scalings and powers failed. This is only computational evidence; the exact converse proof below is decisive.

The reproducible numerical checks are in `experiment_candidates.py`. They are not used as proof.

## Proof

### 1. An exact iterate law

Put \(x=f(y)\) in the given chain. Both outer terms are then \(f(y)\), because
\[
\sqrt{\frac{f(y)^2+f(y)^2}{2}}=f(y)
\quad\text{and}\quad
\sqrt{f(y)f(y)}=f(y).
\]
Thus the middle term equals \(f(y)\), and hence
\[
f(f(y))+y=2f(y). \tag{1}
\]

Define
\[
d(t)=f(t)-t.
\]
Equation (1) gives
\[
d(f(t))=f(f(t))-f(t)=f(t)-t=d(t). \tag{2}
\]
Consequently, induction using \(f(t)=t+d(t)\) and (2) yields
\[
f^n(t)=t+n d(t)\qquad(n=0,1,2,\ldots). \tag{3}
\]
Every iterate is defined and positive, since the codomain equals the domain. If \(d(t)<0\), then (3) is nonpositive for every integer \(n>t/(-d(t))\), a contradiction. Therefore
\[
d(t)\ge0\qquad(t>0). \tag{4}
\]

### 2. A quadratic local estimate

Fix arbitrary \(t,y>0\), and abbreviate
\[
c=d(t),\qquad b=d(y).
\]
Use \(x=f(t)=t+c\) in the original inequalities. By (1)--(2),
\[
f(x)=f(f(t))=t+2c,\qquad f(y)=y+b.
\]
All quantities are positive, so squaring either inequality is equivalent to the original comparison. The lower inequality gives
\[
\begin{aligned}
0
&\le (f(x)+y)^2-4x f(y)\\
&=(t+2c+y)^2-4(t+c)(y+b)\\
&=(t-y)^2+4(t+c)(b-c).
\end{aligned}
\]
It follows that
\[
b-c\le \frac{(t-y)^2}{4(t+c)}\le \frac{(t-y)^2}{4t}. \tag{5}
\]
The upper inequality similarly gives
\[
\begin{aligned}
0
&\le 2x^2+2f(y)^2-(f(x)+y)^2\\
&=2(t+c)^2+2(y+b)^2-(t+2c+y)^2\\
&=(t-y)^2+2(b-c)(2y+b+c).
\end{aligned}
\]
Therefore
\[
c-b\le \frac{(t-y)^2}{2(2y+b+c)}\le \frac{(t-y)^2}{4y}. \tag{6}
\]
The denominators are positive; the last inequalities also use \(b,c\ge0\). Combining (5) and (6), with the applicable one chosen according to the sign of \(b-c\), yields
\[
\boxed{
|d(y)-d(t)|\le \frac{(y-t)^2}{4\min\{t,y\}}.
} \tag{7}
\]

### 3. The displacement is constant

Let \(0<u<v\). For an arbitrary positive integer \(n\), partition \([u,v]\) at
\[
t_i=u+\frac{i(v-u)}n\qquad(0\le i\le n).
\]
Writing \(h=(v-u)/n\), estimate (7) and \(t_{i-1}\ge u\) give
\[
\begin{aligned}
|d(v)-d(u)|
&\le\sum_{i=1}^n |d(t_i)-d(t_{i-1})|\\
&\le n\frac{h^2}{4u}
=\frac{(v-u)^2}{4un}.
\end{aligned}
\]
This holds for every \(n\), so letting \(n\to\infty\) gives \(d(v)=d(u)\). Since any two positive reals can be ordered, \(d\) is constant on \(\mathbb R_{>0}\). Write this constant as \(C\). By (4), \(C\ge0\), and hence
\[
f(x)=x+C.
\]

### 4. Converse and boundary case

For any fixed \(C\ge0\), the function \(f(x)=x+C\) maps positive reals to positive reals. For all \(x,y>0\), the desired chain becomes
\[
\sqrt{\frac{x^2+(y+C)^2}{2}}
\ge \frac{x+(y+C)}2
\ge \sqrt{x(y+C)},
\]
which is RMS--AM--GM for the positive numbers \(x\) and \(y+C\). Thus every such \(C\) works. The boundary case \(C=0\) is the identity. A negative constant is impossible both by (4) and because \(x+C\) would fail to be positive for sufficiently small \(x>0\).
