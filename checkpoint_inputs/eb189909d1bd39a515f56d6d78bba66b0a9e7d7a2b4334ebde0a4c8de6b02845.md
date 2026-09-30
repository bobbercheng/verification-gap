# IMO 2026 Problem 2 — Candidate v2

**Status:** complete

We prove that the circumcircle of \(AKL\) has a diameter whose other
endpoint is the centre of a second, naturally constructed circle.
Directed angles below are taken modulo \(180^\circ\).

## Proof

Reflect the configuration if necessary, so that \(ABC\) is oriented
counterclockwise. Since the triangles \(BMC\) and \(BNC\) are contained in
\(ABC\), both \(K\) and \(L\) lie strictly inside \(ABC\). The four strict
interiority assumptions give the following ray orders inside the indicated
angles:
\[
 AB,AK,AL,AC;\qquad BA,BK,BL,BC;\qquad CA,CL,CK,CB. \tag{1}
\]
The first and third orders are counterclockwise, while the second is
clockwise. At the midpoints the orders
\[
 MB,MK,MC\qquad\text{and}\qquad NB,NL,NC \tag{2}
\]
are counterclockwise. Indeed,
\(\det(MB,MC)=\det(NB,NC)=\tfrac12\det(AB,AC)>0\).
In particular, these orders determine all signs when the given ordinary
angles are converted to directed angles. Also, \(A,K,L\) are noncollinear,
because \(K\) lies strictly inside triangle \(ABL\).

Let the ray \(BK\) meet \(AC\) at \(E\), and let the ray \(CL\) meet
\(AB\) at \(F\). Since \(K,L\) are interior to \(ABC\),
\[
 E\in AC^\circ,\qquad F\in AB^\circ,\qquad B-K-E,\qquad C-L-F. \tag{3}
\]
By (1) and the first given equality,
\[
 \measuredangle FBE=-\angle KBA=-\angle ACL
 =\measuredangle FCE.
\]
Hence \(B,C,E,F\) are concyclic. Denote their circle by \(\omega_0\), and
its centre by \(Z\).

Set \(\omega_1=(BLN)\). If \(E\ne N\), then, using (1), (2), and the fact
that the unoriented lines \(NE\) and \(NC\) coincide,
\[
 \measuredangle LBE=\angle LBK=\angle LNC
 \equiv\measuredangle LNE.
\]
Thus \(E\in\omega_1\). If \(E=N\), then \(B-K-N\), and the same equality
reads
\[
 \measuredangle(LN,NC)=\measuredangle(LB,BN).
\]
By the converse tangent--chord theorem, \(AC\) is tangent to \(\omega_1\)
at \(N\). Therefore, in all cases, the intersections of \(AC\) and
\(\omega_1\) are \(E,N\), counted with multiplicity.

Similarly, set \(\omega_2=(CKM)\). If \(F\ne M\), then
\[
 \measuredangle KCF=-\angle LCK=-\angle BMK
 =\measuredangle KMF,
\]
where the last equality uses that the unoriented lines \(MF\) and \(MB\)
coincide. Hence \(F\in\omega_2\). If \(F=M\), then \(C-L-M\), and the
equality becomes
\[
 \measuredangle(CK,CM)=\measuredangle(MK,MB),
\]
so the converse tangent--chord theorem says that \(AB\) is tangent to
\(\omega_2\) at \(M\). Thus the intersections of \(AB\) and \(\omega_2\)
are \(F,M\), counted with multiplicity.

Let \(F'\) be the second intersection of \(AB\) with \(\omega_1\), the
first being \(B\), and let \(E'\) be the second intersection of \(AC\)
with \(\omega_2\), the first being \(C\). All intersections are counted
with multiplicity. Orient \(AB\) and \(AC\) away from \(A\). Power of
\(A\) with respect to \(\omega_0,\omega_1,\omega_2\), respectively, gives
\[
 AF\cdot AB=AE\cdot AC, \tag{4}
\]
\[
 \overline{AF'}\cdot AB=AE\cdot AN,
 \qquad
 \overline{AE'}\cdot AC=AF\cdot AM. \tag{5}
\]
The bars in (5) denote directed distances in the chosen orientations.
Since \(AN=AC/2\) and \(AM=AB/2\), comparison with (4) yields
\[
 \overline{AF'}=\frac{AF}{2},
 \qquad
 \overline{AE'}=\frac{AE}{2}. \tag{6}
\]
Both quantities are positive. Thus \(F'\) and \(E'\) are literally the
midpoints of \(AF\) and \(AE\), and in particular
\[
 A-F'-F-B,\qquad A-E'-E-C. \tag{7}
\]

Let \(P\) and \(Q\) be the midpoints of \(BF\) and \(CE\), respectively,
and let \(\Omega\) be the circle with diameter \(AZ\). This circle is
nondegenerate. Indeed, if \(Z=A\), then the distinct points \(C,E\) of
\(\omega_0\), which lie on the same ray from \(A\), would have to satisfy
\(AC=AE\), contradicting \(E\in AC^\circ\).

Because \(P,Q\) are the midpoints of the chords \(BF,CE\) of \(\omega_0\),
we have \(ZP\perp AB\) when \(P\ne Z\), and \(ZQ\perp AC\) when
\(Q\ne Z\). Thales' theorem then gives \(P,Q\in\Omega\); if \(P=Z\) or
\(Q=Z\), the corresponding point is already an endpoint of the diameter.

We now compare powers with respect to \(\omega_1\) and \(\Omega\). Since
\(N,Q\) are the midpoints of \(CA,CE\),
\[
 \operatorname{Pow}_{\omega_1}(C)=CN\cdot CE
 =CA\cdot CQ=\operatorname{Pow}_{\Omega}(C). \tag{8}
\]
Moreover, (6) gives \(FF'=FA/2\), while \(FP=FB/2\); using the order in
(7),
\[
 \operatorname{Pow}_{\omega_1}(F)=-FF'\cdot FB
 =-FA\cdot FP=\operatorname{Pow}_{\Omega}(F). \tag{9}
\]
The circles \(\omega_1\) and \(\Omega\) are distinct: \(\Omega\) contains
\(A\), whereas \(\omega_1\cap AB=\{B,F'\}\), counted with multiplicity,
and (7) shows that neither point is \(A\). Hence their radical axis is the
line \(CF\). Since \(L\in CF\cap\omega_1\), it follows that
\[
 L\in\Omega. \tag{10}
\]

Likewise, since \(M,P\) are the midpoints of \(BA,BF\),
\[
 \operatorname{Pow}_{\omega_2}(B)=BM\cdot BF
 =BA\cdot BP=\operatorname{Pow}_{\Omega}(B), \tag{11}
\]
and since \(EE'=EA/2\) and \(EQ=EC/2\),
\[
 \operatorname{Pow}_{\omega_2}(E)=-EE'\cdot EC
 =-EA\cdot EQ=\operatorname{Pow}_{\Omega}(E). \tag{12}
\]
The circles \(\omega_2\) and \(\Omega\) are distinct because \(\Omega\)
contains \(A\), whereas \(\omega_2\cap AC=\{C,E'\}\) and neither point is
\(A\). Their radical axis is therefore \(BE\). As
\(K\in BE\cap\omega_2\), we obtain
\[
 K\in\Omega. \tag{13}
\]

Thus \(\Omega\) contains the three noncollinear points \(A,K,L\), so it is
the circumcircle of \(AKL\). Its centre \(O\) is the midpoint of \(AZ\).
Together with the definitions of \(M,N\), this gives
\[
 \overrightarrow{MO}=\frac12\overrightarrow{BZ},
 \qquad
 \overrightarrow{NO}=\frac12\overrightarrow{CZ}.
\]
Finally, \(ZB=ZC\), because \(B,C\in\omega_0\) and \(Z\) is its centre.
Therefore
\[
 \boxed{OM=ON}.
\]

## Robustness audit

No generic-position assumption was used. The strict interiority conditions
make \(BLN\), \(CKM\), and \(AKL\) nondegenerate. The possible repetitions
\(E=N\) and \(F=M\) are handled as tangent double intersections before any
power calculation. Formula (6) places \(F'\) and \(E'\) strictly inside
\(AF\) and \(AE\), so tangency of \(AB\) to \(\omega_1\) at \(B\), or of
\(AC\) to \(\omega_2\) at \(C\), is automatically ruled out. The cases
\(P=Z\) and \(Q=Z\) are covered directly, \(Z=A\) is impossible, and the
two auxiliary circles are proved distinct from \(\Omega\). Thus all power
identities and radical-axis steps remain valid in every allowed case.
