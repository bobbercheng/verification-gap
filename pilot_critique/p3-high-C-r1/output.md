# IMO 2026 Problem 3

**Problem.** Liu marks at most $n$ points on a stick of length $1$, then Xiang marks at most $n$ points (all marked points distinct). The stick is cut at all marked points; the players then alternately claim pieces, Liu first, each maximising his own total length. Determine the largest $c$ that Liu can guarantee.

**Answer.**
$$\boxed{\,c_n=\frac{2^{n}}{\,2^{n+1}-1\,}\,}$$

**Strategy in one paragraph.** Liu's optimal opening is to mark the stick into parts of lengths proportional to $2^n,2^{n-1},\dots,2,1$; a majorization argument on the sorted piece lengths then caps Xiang's total. Xiang's optimal response to an *arbitrary* opening uses the pigeonhole principle to find two disjoint subfamilies of Liu's parts whose total lengths differ by at most $1/N$ (where $N=2^{n+1}-1$), then cuts so that everything cancels into equal pairs except leftover pieces of total length $\le 1/N$.

**Throughout, $N:=2^{n+1}-1$.**

---

## 1. Setup and the $\delta$-formalism

Marks at the endpoints $0$ or $1$ create no cut, so assume all marks are interior. If Liu makes $k_L\le n$ marks, the stick falls into $m=k_L+1\le n+1$ **parts**; call the resulting composition $A=(a_1,\dots,a_m)$, with $a_i>0$, $\sum a_i=1$. Each of Xiang's $k_X\le n$ marks is distinct from Liu's marks, hence lies in the interior of one part and splits that part into two. So the final configuration is a **refinement** of $A$ produced by at most $n$ cuts, and the number of final pieces is
$$M=m+k_X\le (n+1)+n=2n+1.$$
Each final piece is contained in a unique part, and pieces contained in the same part are pairwise disjoint subintervals of it.

For a finite multiset $S$ of positive reals with decreasing arrangement $v_1\ge v_2\ge\cdots\ge v_M$, define
$$\operatorname{odd}(S)=\sum_{i\text{ odd}}v_i,\qquad \operatorname{even}(S)=\sum_{i\text{ even}}v_i,\qquad \delta(S)=\operatorname{odd}(S)-\operatorname{even}(S)=\sum_{i=1}^M(-1)^{i+1}v_i,$$
and set $\delta(\varnothing):=0$.

**Observation 1.** *(i)* Grouping consecutive terms, $\delta(S)=(v_1-v_2)+(v_3-v_4)+\cdots\ge 0$ (each bracket is $\ge 0$; if $M$ is odd the last term is $+v_M\ge 0$).
*(ii)* $\delta(S)=v_1-\delta\bigl(S\setminus\{v_1\}\bigr)\le v_1=\max S$, since the subtracted term is $\ge 0$ by (i).

## 2. Lemma 1 — the claiming phase is worth the odd sum

**Lemma 1.** With the final multiset $S$ fixed, under optimal play Liu obtains exactly $\operatorname{odd}(S)$ and Xiang exactly $\operatorname{even}(S)$.

*Proof.* Since $\operatorname{odd}(S)+\operatorname{even}(S)=1$, it suffices to show that Liu can guarantee $\ge\operatorname{odd}(S)$ and Xiang can guarantee $\ge\operatorname{even}(S)$.

**A pairing principle.** Suppose a player $P$ responds to the opponent's moves using a fixed pairing of (some of) the pieces, by the following rule: whenever the opponent claims a piece whose mate is still unclaimed, $P$ claims the mate; otherwise $P$ claims the larger member of a completely unclaimed pair if one exists, and otherwise the largest remaining piece.

**Claim.** $P$ finishes holding at least one piece of each pair, and the *first* piece $P$ acquires from each pair has value at least the smaller member of that pair.

*Proof of claim.* Fix a pair $\{x,y\}$, $x\ge y$. Assume first, for contradiction, that at the end $P$ holds no piece of the pair, i.e. both pieces went to the opponent $O$. Consider who claimed the first piece of this pair. It was not $P$: $P$ acquires a piece of a pair only as a mate-response (which requires $O$ to have taken the other piece first — and then $P$ holds the mate, contradiction), or as the larger member of an untouched pair, or as the largest remaining piece (in the last two cases $P$ holds that very piece, contradiction). So $O$ claimed the first piece; but at that moment the pair was untouched, the mate was unclaimed, and $P$'s rule forced $P$ to take the mate immediately — contradiction. Hence $P$ holds at least one piece of the pair.

Now consider the *first* piece of the pair that $P$ acquires. It cannot be acquired via the "largest remaining piece" rule: at such a moment no pair is completely unclaimed, so this pair was already touched; the touched piece was not claimed by $O$ (otherwise $P$ would immediately have taken its free mate, and would already hold a piece of the pair), so it was already claimed by $P$ — contradicting "first". Therefore the first acquisition is a mate-response or the larger member of an untouched pair. In the first case $P$ receives the mate of $O$'s piece, of value $\ge y$; in the second case $P$ receives $x\ge y$. $\blacksquare$ (claim)

**Liu's strategy.** First move: claim $v_1$. Thereafter apply the pairing principle with the pairs $(v_2,v_3),(v_4,v_5),\dots$ (leaving $v_M$ unpaired if $M$ is even). The pairs are disjoint and disjoint from $v_1$, so by the claim Liu's total is at least
$$v_1+\sum_{k\ge 1}v_{2k+1}=\operatorname{odd}(S).$$

**Xiang's strategy.** Apply the pairing principle with the pairs $(v_1,v_2),(v_3,v_4),\dots$ (leaving $v_M$ unpaired if $M$ is odd). By the claim Xiang's total is at least $\sum_{k\ge1}v_{2k}=\operatorname{even}(S)$, so Liu's total is at most $\operatorname{odd}(S)$. $\blacksquare$

## 3. Lemma 2 — reduction to a one-dimensional game

**Lemma 2.** $\displaystyle c_n=\sup_{A}\ \inf_{R}\ \frac{1+\delta(R)}{2}$, where $A$ ranges over compositions of $1$ into at most $n+1$ positive parts and $R$ over refinements of $A$ with at most $n$ cuts.

*Proof.* By Lemma 1, once the final multiset $S$ is fixed, Liu's take under optimal play is $\operatorname{odd}(S)=\dfrac{1+\delta(S)}{2}$ (the pieces sum to $1$). Liu chooses $A$, then Xiang — who maximises his own take, equivalently minimises Liu's — chooses the refinement $R$. $\blacksquare$

We will prove $\delta_n:=\sup_A\inf_R\delta(R)=\dfrac1N$, i.e. $c_n=\dfrac{1+1/N}{2}=\dfrac{2^n}{2^{n+1}-1}$, by exhibiting Liu's strategy (Theorem A) and Xiang's strategy (Theorem B).

## 4. Lemma 3 — equal pairs cancel

**Lemma 3.** If a multiset $S$ is partitioned into pairs of equal pieces and a (possibly empty) leftover sub-multiset $L$, then $\delta(S)=\delta(L)$.

*Proof.* It suffices to show that deleting one equal pair $\{p,p\}$ from $S$ does not change $\delta$. In the decreasing arrangement of $S$, all entries equal to $p$ form a consecutive block of length at least $2$; choose the two deleted copies to be the first two entries of this block, occupying adjacent positions $j,j+1$. Their joint contribution to $\delta$ is $(-1)^{j+1}p+(-1)^{j+2}p=0$, and every entry after position $j+1$ keeps the parity of its position after the deletion (its index drops by $2$). Hence $\delta$ is unchanged. Iterating over all the pairs leaves exactly $L$. $\blacksquare$

## 5. Theorem A — Liu's strategy (lower bound)

**Theorem A.** Liu marks the $n$ points that split the stick into parts of lengths
$$\frac{2^n}{N},\ \frac{2^{n-1}}{N},\ \dots,\ \frac{2}{N},\ \frac{1}{N}$$
(these sum to $\frac{2^{n+1}-1}{N}=1$). Then Liu guarantees $\dfrac{2^n}{N}$.

*Proof.* Work in units of $1/N$: the parts are $2^n,2^{n-1},\dots,2,1$, with total $N$. Let $S$ be any refinement of this composition by at most $n$ cuts, with pieces $v_1\ge v_2\ge\cdots\ge v_M$; note $M\le 2n+1$.

**Lemma E (even-position majorization).** For every $1\le r\le\lfloor M/2\rfloor$,
$$v_2+v_4+\cdots+v_{2r}\ \le\ 2^n-2^{\,n-r}.$$

*Proof of Lemma E.* Induction on $r$.

*Base $r=1$.* Suppose $v_2>2^{n-1}$. Then $v_1\ge v_2>2^{n-1}$. A piece longer than $2^{n-1}$ is a subinterval of a part of size $>2^{n-1}$, and the only such part is $2^n$; so $v_1$ and $v_2$ are disjoint subintervals of the same part of size $2^n$, giving $2v_2\le v_1+v_2\le 2^n$, i.e. $v_2\le 2^{n-1}$ — contradiction. Hence $v_2\le 2^{n-1}=2^n-2^{n-1}$.

*Step $r-1\to r$.* Note $r\le\lfloor M/2\rfloor\le n$. Two cases.

**Case 1: $v_{2r}\le 2^{n-r}$.** By the induction hypothesis,
$$\sum_{i=1}^{r}v_{2i}\le\bigl(2^n-2^{\,n-r+1}\bigr)+2^{\,n-r}=2^n-2^{\,n-r}.$$

**Case 2: $v_{2r}>2^{n-r}$.** Then each of $v_1\ge\cdots\ge v_{2r}$ exceeds $2^{n-r}$, so each lies in a part of size $>2^{n-r}$; part sizes being powers of $2$, those parts have size $\ge 2^{\,n-r+1}$, i.e. they are among the $r$ parts $2^{\,n-r+1},\dots,2^n$, whose total size is
$$\sum_{j=n-r+1}^{n}2^j=2^{n+1}-2^{\,n-r+1}.$$
The pieces $v_1,\dots,v_{2r}$ are pairwise disjoint subintervals of these parts, so $\sum_{i=1}^{2r}v_i\le 2^{n+1}-2^{\,n-r+1}$. Since $v_2\le v_1,\ v_4\le v_3,\ \dots,\ v_{2r}\le v_{2r-1}$,
$$\sum_{i=1}^{r}v_{2i}\le\frac12\sum_{i=1}^{2r}v_i\le 2^n-2^{\,n-r}.\qquad\blacksquare\ \text{(Lemma E)}$$

By Lemma 1, Xiang's total is $\operatorname{even}(S)=\sum_{i=1}^{\lfloor M/2\rfloor}v_{2i}$. With $r:=\lfloor M/2\rfloor\le n$, Lemma E gives
$$\operatorname{even}(S)\le 2^n-2^{\,n-r}\le 2^n-1,$$
because $2^{\,n-r}\ge 1$. Therefore Liu's total, in units of $1/N$, is
$$\operatorname{odd}(S)=N-\operatorname{even}(S)\ge N-(2^n-1)=2^n,$$
i.e. $\dfrac{2^n}{N}$ of the stick, no matter how Xiang plays. $\blacksquare$ (Theorem A)

## 6. Theorem B — Xiang's strategy (upper bound)

**Theorem B.** For every composition $A$ into $m\le n+1$ parts, Xiang has a refinement by at most $n$ cuts achieving $\delta\le\dfrac1N$. Consequently, against any opening, Liu's take is at most $\dfrac{1+1/N}{2}=\dfrac{2^n}{N}$.

*Proof.* Let $A=(a_1,\dots,a_m)$.

**Case $m\le n$.** Xiang marks the midpoint of each part ($m\le n$ marks): every piece then has an equal mate, so by Lemma 3 (with $L=\varnothing$), $\delta=0\le 1/N$.

**Assume now $m=n+1$.**

**Step 1: a near-cancelling sign pattern (pigeonhole).** Consider the $2^{n+1}=N+1$ subset sums $s_I=\sum_{i\in I}a_i$, $I\subseteq\{1,\dots,n+1\}$; they all lie in $[0,1]$. Sort them as $t_0\le t_1\le\cdots\le t_N$. The $N$ gaps satisfy
$$\sum_{k=0}^{N-1}(t_{k+1}-t_k)=t_N-t_0\le 1,$$
so some gap is at most $1/N$: there are distinct subsets $I\ne J$ with $|s_I-s_J|\le 1/N$. Set
$$P=I\setminus J,\qquad Q=J\setminus I,\qquad Z=\{1,\dots,n+1\}\setminus(P\cup Q).$$
Then $P,Q$ are disjoint, $P\cup Q\ne\varnothing$ (since $I\ne J$), and
$$D:=\Bigl|\sum_{i\in P}a_i-\sum_{j\in Q}a_j\Bigr|=|s_I-s_J|\le\frac1N.$$

**Step 2: the cuts.** Xiang's marks are of two kinds.

**(a)** For each $i\in Z$, Xiang marks the midpoint of the part $a_i$, producing an equal pair $(a_i/2,a_i/2)$. This uses $|Z|$ marks.

**(b)** If $P$ and $Q$ are both nonempty, Xiang matches the parts of $P$ ("supply") against the parts of $Q$ ("demand") by the following process. Maintain two pools of pieces, initially $S=\{a_i:i\in P\}$ and $T=\{a_j:j\in Q\}$, and repeat while both pools are nonempty: let $s=\max S$, $t=\max T$.
- If $s=t$: match the two pieces as a pair; delete both. (No cut.)
- If $s>t$: cut the piece $s$ into pieces of lengths $t$ and $s-t$ (one mark, interior to the piece, since $0<t<s$); match the new $t$-piece with the $T$-piece of length $t$; delete both from the pools; return the piece $s-t$ to $S$.
- If $s<t$: symmetrically, cut $t$ into $s$ and $t-s$, match the two $s$'s, return $t-s$ to $T$.

Each iteration deletes at least one piece, so the process terminates with at least one pool empty; call the remaining pieces (if any) the **leftover** $L$, with $\ell:=|L|$. Every matched pair consists of one piece originating from a $P$-part and one from a $Q$-part, and the two members have equal length; hence the matched mass is the same on both sides, and the leftover total is
$$\sum L=\Bigl|\sum_{i\in P}a_i-\sum_{j\in Q}a_j\Bigr|=D\le\frac1N.$$

*Cut count.* Let $c$ and $f$ be the numbers of cut-steps and free steps. A cut-step decreases $|S|+|T|$ by exactly $1$ (one piece is consumed from the smaller side; the larger side trades one piece for one piece), and a free step decreases it by $2$; hence
$$c+2f=|P|+|Q|-\ell.$$
If $\ell\ge1$, then $c\le|P|+|Q|-1$. If $\ell=0$, the last step was free — a cut-step always leaves a remainder piece behind in the pool whose piece was cut, so a cut-step can terminate the process only with $\ell\ge1$ — thus $f\ge1$ and $c\le|P|+|Q|-2$. In either subcase the total number of marks is
$$|Z|+c\le |Z|+|P|+|Q|-1=(n+1)-1=n.$$

**(c)** If one of $P,Q$ is empty, then the other is nonempty (because $P\cup Q\ne\varnothing$); say $Q=\varnothing$ and $P\ne\varnothing$. Then $D=\sum_{i\in P}a_i\le 1/N$. Xiang makes no cuts beyond (a); the parts of $P$ remain whole as the leftover $L$. The number of marks used is
$$|Z|=(n+1)-|P|\le n,$$
since $|P|\ge1$. (The bound $|Z|\le n$ is the correct one here: if $P$ is a singleton then $|Z|=n$, which is still a legal number of marks.)

**Step 3: evaluation.** In every case the final multiset $S$ is the disjoint union of equal pairs (the midpoint pairs from (a) and the matched pairs from (b)) and a leftover family $L$ of total length $\sum L=D\le 1/N$ — where $L$ may be **empty** (this happens, for instance, when $D=0$ and the process in (b) matches everything, e.g. $n=1$, $A=(\tfrac12,\tfrac12)$, $P=\{1\}$, $Q=\{2\}$). By Lemma 3, $\delta(S)=\delta(L)$. If $L=\varnothing$, then $\delta(S)=\delta(\varnothing)=0\le 1/N$. If $L\ne\varnothing$, then by Observation 1(ii),
$$\delta(S)=\delta(L)\le\max L\le\sum L=D\le\frac1N.$$

**Legality.** Every mark of type (a) or (b) lies in the interior of a part of $A$, hence is distinct from Liu's marks. The marks are pairwise distinct: the midpoint marks lie in distinct parts; each process mark lies in the interior of a current piece (a sub-piece of a part in $P\cup Q$ created only after all earlier cuts inside that part), so it differs from every earlier mark; and marks in parts of $Z$ cannot coincide with marks in parts of $P\cup Q$. Cutting the stick at these $\le n$ distinct marks produces exactly the pieces described above. Hence this is a legal play for Xiang, and it holds Liu to
$$\operatorname{odd}(S)=\frac{1+\delta(S)}{2}\le\frac{1+1/N}{2}=\frac{2^n}{N}.\qquad\blacksquare\ \text{(Theorem B)}$$

## 7. Conclusion and tightness

By Theorem A, Liu guarantees $\dfrac{2^n}{N}$ by marking geometrically; by Theorem B, Xiang prevents Liu from obtaining more than $\dfrac{2^n}{N}$ against any opening. Therefore
$$c_n=\frac{2^n}{2^{n+1}-1}.$$

**Tightness remark.** The value is attained, not merely approached. Against Liu's geometric composition (parts $1,2,4,\dots,2^n$ in units of $1/N$), all $2^{n+1}$ subset sums are distinct integers in $[0,N]$ (uniqueness of binary representation), so every near-cancelling pattern in Step 1 of Theorem B has $D\ge 1/N$: Xiang cannot push $\delta$ below $1/N$ by this method. The pattern $P=\{2^n\}$, $Q=\{1,2,\dots,2^{n-1}\}$ (with $Z=\varnothing$, $D=1$ unit) is realized by successively halving the current supply piece — $n$ cuts producing the pieces
$$2^{n-1},2^{n-1},2^{n-2},2^{n-2},\dots,1,1,1,$$
for which Lemma 3 gives $\delta=1$ unit $=1/N$. So Xiang holds Liu to exactly $2^n/N$ on this opening, matching Theorem A.

**Sanity check ($n=1$).** $c_1=\tfrac23$: Liu marks at $\tfrac23$; Xiang's best reply halves the part $\tfrac23$, leaving $(\tfrac13,\tfrac13,\tfrac13)$ with $\delta=\tfrac13$, and Liu takes $\tfrac23$. $\blacksquare$