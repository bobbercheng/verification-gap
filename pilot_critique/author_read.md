# Author read of pilot outputs (2026-09-05, before grades were seen for N r1/r2; after GLM grades for all four)

Protocol: every output rated S=2 or gate-pass is read by an author. The four continuations from the S=2 seed
(p3-high, C r1/r2 and N r1/r2) returned write-ups; the twelve continuations from S<2 texts returned no text
under the 60k budget, so there was nothing to read.

p3-high-N-r2 (read in full). Lemma 1 (claiming phase = alternating sum) by the standard pairing strategies for both
players, correct. Lemma 2 (equal pairs cancel) correct. Lower bound: Liu's geometric division; Lemma E, an even-position
majorization proved by induction on r (case split on v_{2r} <= or > 2^{n-r}; in the second case all 2r pieces lie in the
r largest parts) -- valid for all n. Upper bound: subset-sum pigeonhole (2^{n+1} sums in [0,1] give a gap <= 1/N), halving
of Z-parts, greedy cancellation of P against Q with an explicit cut count c <= |P|+|Q|-1 (including the l=0 case), so
|Z|+c <= n; the one-empty-pool case handled separately with |Z| <= n. Leftover L may be empty; delta(L) <= sum L <= 1/N.
Both seed defects (D1 singleton count, D2 empty leftover) are handled although this run received no critique.
Verdict of the read: complete for all n; no gap found.

p3-high-C-r2 (Theorem A/B read; setup skimmed). Same Lemma E lower bound; Theorem B with Case (i)/(ii) for the pools,
explicit L=empty handling (line 79 and Step 3). Addresses D1 and D2 explicitly. No gap found in the parts read.

p3-high-C-r1 (Theorems A/B read). Lemma E lower bound; Step 2(a)-(c) of Theorem B with the singleton remark
"(The bound |Z|<=n is the correct one here: if P is a singleton then |Z|=n ...)" and the L=empty case in Step 3.
Addresses D1 and D2 explicitly. No gap found in the parts read.

p3-high-N-r1 (Sections 4-5 read). Lemma E lower bound; cancellation procedure with pool-size accounting; one-empty-pool
case with |Z| = n+1-|P u Q| <= n; L possibly empty handled in Step 3. Both seed defects handled without critique.

Note. All four outputs replace the seed's tree-component lower bound by the majorization lemma; the mechanism changed,
the obligation is discharged either way. The author read is a check for gaps, not an official grade; the blind model
grades in grades_glm/, grades_kimi/, gate_glm53/ are the reported endpoints.
