# Candidate solution v1

**Status: complete.**

## Answer

Mulan can guarantee victory exactly for

\[
\boxed{\theta=\frac{180^\circ}{n}\quad\text{with an integer }n\ge 2.}
\]

The argument below is a proof from the stated rules. The finite-lattice computation recorded later was used only to test hypotheses.

## 1. Exact effect of a cut

Let the angles of the current triangle \(ABC\) be \(A,B,C\), using the same letters for the vertices and their angle measures. Suppose Mulan chooses \(P\) in the open side \(AB\) and cuts from \(C\). Put

\[
x=\angle ACP,\qquad 0<x<C.
\]

Then the angle triples of the two possible new triangles are

\[
T_1=(A,x,180^\circ-A-x)
\tag{1}
\]

and

\[
T_2=(B,C-x,A+x).
\tag{2}
\]

Indeed, the first two entries in each triple are inherited or split angles, and the third follows from the angle sum. Conversely, every \(x\in(0,C)\) is realizable: the corresponding interior ray from \(C\) meets the open segment \(AB\).

## 2. Sufficiency when \(180^\circ=n\theta\)

Assume

\[
180^\circ=n\theta
\]

for an integer \(n\ge2\).

### Lemma 1: an integral multiple can be reduced to the target

If a current triangle has an angle \(m\theta\), where \(1\le m\le n-1\), then Mulan can force victory in at most \(m-1\) further cuts.

For \(m=1\), the stopping condition already gives Mulan the win. If \(m\ge2\), she cuts from that vertex so as to split its angle into

\[
\theta+(m-1)\theta.
\]

One child contains the angle \(\theta\), while the other contains \((m-1)\theta\). Thus Shan-Yu either keeps an immediate winning child or leaves a strictly smaller positive integral multiple. Induction on \(m\) proves the lemma. Every split is strict because both summands are positive.

It remains to show that Mulan can force some integral multiple of \(\theta\) to appear.

### Case \(n\ge3\)

If the current triangle already has an angle \(m\theta\), Lemma 1 applies. Otherwise, let \(C\) be a largest angle and call the other two \(A,B\). Since

\[
C\ge60^\circ=\frac{n\theta}{3}\ge\theta
\]

and \(C\ne\theta\), we have \(C>\theta\).

The open interval \((A,A+C)\) therefore has length greater than \(\theta\), so it contains an integral multiple \(k\theta\). Explicitly, take

\[
k=\left\lfloor\frac A\theta\right\rfloor+1;
\]

then \(A<k\theta\le A+\theta<A+C\). Also \(A+C<180^\circ=n\theta\), so \(1\le k\le n-1\).

Set

\[
x=k\theta-A.
\]

The inequalities just proved give \(0<x<C\), so this is a legal cut of the form (1)--(2). Its two possible children contain, respectively, the angles

\[
180^\circ-A-x=(n-k)\theta
\]

and

\[
A+x=k\theta.
\]

Thus either choice by Shan-Yu leaves a positive integral multiple of \(\theta\), and Lemma 1 finishes the strategy.

### Case \(n=2\)

Here \(\theta=90^\circ\). If the triangle already has a right angle, Mulan has won. Otherwise it has at least two acute angles; label two of them \(A,B<\theta\), and call the remaining angle \(C\). Choose

\[
x=\theta-A.
\]

We have \(x>0\), and

\[
x<C
\iff \theta<A+C=2\theta-B
\iff B<\theta.
\]

Hence the cut is legal. Equations (1)--(2) show that both children have an angle \(\theta\):

\[
2\theta-A-x=\theta,
\qquad
A+x=\theta.
\]

This proves sufficiency. It also proves genuine finite termination: for \(n\ge3\), after the first manufacturing cut the multiplier is at most \(n-1\), so the whole strategy uses at most \(n-1\) cuts; for \(n=2\), at most one cut is needed.

## 3. Necessity when \(180^\circ/\theta\) is not an integer

Call a triangle **clean** if none of its angles is a positive integral multiple of \(\theta\).

Assume

\[
\frac{180^\circ}{\theta}\notin\mathbb Z.
\tag{3}
\]

Shan-Yu starts with an equilateral triangle. It is clean: if \(60^\circ=m\theta\) for a positive integer \(m\), then \(180^\circ=3m\theta\), contrary to (3).

We prove that after every cut of a clean triangle, at least one child is clean. Use the notation (1)--(2). Because the parent is clean, the unchanged angles \(A\) in \(T_1\) and \(B\) in \(T_2\) are not multiples of \(\theta\). If both children were non-clean, one of

\[
x,\quad 180^\circ-A-x
\]

and one of

\[
C-x,\quad A+x
\]

would be positive integral multiples of \(\theta\). There are four pairings:

1. If \(x\) and \(C-x\) are multiples, then their sum \(C\) is a multiple.
2. If \(x\) and \(A+x\) are multiples, then their positive difference \(A\) is a multiple.
3. If \(180^\circ-A-x\) and \(C-x\) are multiples, then their positive difference
   \[
   (180^\circ-A-x)-(C-x)=B
   \]
   is a multiple.
4. If \(180^\circ-A-x\) and \(A+x\) are multiples, then their sum \(180^\circ\) is a multiple.

The first three conclusions contradict cleanliness of the parent, and the fourth contradicts (3). Hence at least one child is clean.

Shan-Yu's strategy is now explicit: after every cut, retain a clean child (choosing either one if both are clean). Inductively, the retained triangle never has an angle \(\theta\), so this play never reaches Mulan's stopping condition. Every finite-stage triangle remains nondegenerate because \(P\) lies in an open side; possible limiting degeneration is irrelevant. Therefore Mulan cannot guarantee a finite victory under (3).

Combining Sections 2 and 3, and using \(0^\circ<\theta<180^\circ\), gives exactly \(\theta=180^\circ/n\) with \(n\ge2\).

## 4. Hypotheses and falsification record

These were exploratory hypotheses, not premises of the proof.

- **Threshold hypothesis:** every \(\theta\le90^\circ\) wins. It fails for \(\theta=180^\circ/\sqrt5<90^\circ\): condition (3) holds, so the equilateral clean-triangle strategy defeats Mulan.
- **Dyadic-only hypothesis:** repeated bisection suggests only \(180^\circ/2^r\) might win. It fails at \(\theta=60^\circ\); the construction in Section 2 with \(n=3\) is a winning strategy.
- **Rational-commensurability hypothesis:** every rational value of \(\theta/180^\circ\) wins. It fails at \(\theta=72^\circ=(2/5)180^\circ\), since \(180^\circ/72^\circ=5/2\) is not an integer and the clean invariant applies.
- **Reciprocal-integer hypothesis:** \(180^\circ/\theta\) must be an integer. Exact lattice searches, the strict-cut boundary cases \(n=2,3\), and the adversarial clean invariant were used to attack it. No counterexample survived, and Sections 2--3 prove it.

## 5. Computational evidence (not proof)

The exact finite-state program `experiments/grid_game.py` restricts all angles and cuts to positive integer units summing to \(N\), then computes the reachability attractor. For every \(3\le N\le60\) and every integer target \(1\le T<N\) (1,769 parameter pairs), it found that every lattice state is winning exactly when \(T\mid N\), i.e. when \(T/N\) is a reciprocal integer. This supported the final hypothesis but cannot replace either direction of the real-angle proof, because off-grid cuts are omitted.
