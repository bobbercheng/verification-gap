# IMO 2026 Problem 5 — Solution

## Problem
Determine all $f:\mathbb{R}_{>0}\to\mathbb{R}_{>0}$ such that for every $x,y>0$,
$$\sqrt{\frac{x^2+f(y)^2}{2}} \;\ge\; \frac{f(x)+y}{2} \;\ge\; \sqrt{x\,f(y)}.\tag{$*$}$$

## Answer
$$\boxed{\,f(x)=x+c,\quad c\ge 0\ \text{an arbitrary constant.}\,}$$

---

## Verification (these all work)

Let $f(x)=x+c$ with $c\ge0$ (so $f(x)=x+c>0$ for all $x>0$; conversely $c<0$ would give $f(x)<0$ for $0<x<-c$, forbidden).

*Right inequality.* $\dfrac{x+y+c}{2}\ge\sqrt{x(y+c)}$. Squaring (both sides positive):
$(x+y+c)^2-4x(y+c)=x^2+y^2+c^2-2xy-2xc+2yc=(x-y-c)^2\ge0.$ ✓

*Left inequality.* $\sqrt{\dfrac{x^2+(y+c)^2}{2}}\ge\dfrac{x+y+c}{2}$. Squaring:
$2x^2+2(y+c)^2-(x+y+c)^2=x^2+y^2+c^2-2xy-2xc+2yc=(x-y-c)^2\ge0.$ ✓

So every $f(x)=x+c$, $c\ge0$, is a solution.

---

## Proof of uniqueness (no regularity is assumed)

Write the two inequalities (squared) as
$$\text{(C1)}\quad 2x^2+2f(y)^2\ge (f(x)+y)^2,\qquad
  \text{(C2)}\quad (f(x)+y)^2\ge 4x\,f(y).$$

### Step 1 — An exact iteration identity

Substitute $(x,y)=(f(t),t)$ (both entries are positive). Then the middle term is $\tfrac{f(f(t))+t}{2}$, while
- in (C1): $\sqrt{\tfrac{f(t)^2+f(t)^2}{2}}=f(t)$, giving $f(f(t))\le 2f(t)-t$;
- in (C2): $\sqrt{f(t)\cdot f(t)}=f(t)$, giving $f(f(t))\ge 2f(t)-t$.

Hence, for all $t>0$,
$$\boxed{\,f(f(t))=2f(t)-t.\,}\tag{1}$$

### Step 2 — Positivity gives $f\ge\mathrm{id}$

Let $D(t):=f(t)-t$. From (1), $D(f(t))=f(f(t))-f(t)=f(t)-t=D(t)$, so $D$ is constant along each forward orbit. By induction using (1) (the recurrence $a_{n+1}=2a_n-a_{n-1}$),
$$f^{(n)}(t)=t+nD(t),\qquad n=0,1,2,\dots$$
Every iterate lies in $\mathbb{R}_{>0}$. If $D(t)<0$ then $t+nD(t)\to-\infty<0$, impossible. Thus
$$D(t)=f(t)-t\ge0\quad\forall\,t>0.\tag{2}$$

### Step 3 — A master upper bound on $D$

Inequality (C2) with $(u,v)$ in place of $(x,y)$ reads $(f(u)+v)^2\ge4u\,f(v)$, i.e.
$$D(v)=f(v)-v\le\frac{(f(u)+v)^2-4uv}{4u}.$$
Completing the square in $v$,
$$\frac{(f(u)+v)^2-4uv}{4u}=D(u)+\frac{(v-(2u-f(u)))^2}{4u}.$$
Now choose $u=f(s)$ and use $D(f(s))=D(s)$ together with $2f(s)-f(f(s))=s$ (from (1)):
$$\boxed{\,D(v)\le D(s)+\frac{(v-s)^2}{4f(s)}\qquad\forall\,s,v>0.\,}\tag{3}$$
(Verified numerically to be tight for $f=x+c$ and violated by every non-constant candidate tested.)

### Step 4 — $D$ is continuous

Fix $s>0$ and let $v\to s$ with $|v-s|<s/2$ (so $v>s/2$). From (3) and from (3) with roles swapped,
$$D(v)-D(s)\le\frac{(v-s)^2}{4f(s)},\qquad
  D(s)-D(v)\le\frac{(v-s)^2}{4f(v)}\le\frac{(v-s)^2}{2s},$$
using $f(v)\ge v>s/2$ from (2). Both bounds $\to0$, hence $D(v)\to D(s)$: **$D$ is continuous**, and so is $f=s+D$.

### Step 5 — $D$ is constant

Let $[a,b]\subset(0,\infty)$ be compact. Since $f$ is continuous and strictly positive, $m:=\min_{[a,b]}f>0$. For $s,v\in[a,b]$, (3) and its swap give
$$|D(v)-D(s)|\le\frac{(v-s)^2}{4m}.\tag{4}$$
Take any $p,q\in[a,b]$ and partition $[p,q]$ into $n$ equal steps $t_i=p+i(q-p)/n$. By (4) and the triangle inequality,
$$|D(q)-D(p)|\le\sum_{i=1}^{n}\frac{((q-p)/n)^2}{4m}=\frac{(q-p)^2}{4mn}\xrightarrow[n\to\infty]{}0.$$
Thus $D(q)=D(p)$ for all $p,q\in[a,b]$. Since $(0,\infty)=\bigcup_{n}[1/n,n]$, $D\equiv c$ is constant on all of $\mathbb{R}_{>0}$, and by (2) $c\ge0$.

Therefore $f(x)=x+c$ with $c\ge0$, completing the classification. $\blacksquare$

---

## Distinction of proof / computation / assumption
- **Proof:** Steps 1–5 (rigorous, no regularity assumed; continuity is *derived* in Step 4).
- **Computation (evidence only):** grid checks confirming the family and ruling out non-constant candidates; verification of (1) and (3).
- **Assumption:** only the stated domain/codomain $f:\mathbb{R}_{>0}\to\mathbb{R}_{>0}$.
