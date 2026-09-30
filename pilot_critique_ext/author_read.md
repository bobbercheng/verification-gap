# Author read of the 200k-budget extension outputs (2026-09-06, after blind grades were seen)

Six of twelve runs returned a write-up (P6 S=1 start: C r1, N r1, N r2; P3 S=0 start: C r1, N r1; P6 S=0 start: C r2).

p3-low-N-r1 (S=0 GLM-5.2 candidate as start text, NO critique, 8.8 kB): a complete proof in the published architecture.
Lemma 1 (claiming stage = alternating sum, consecutive pairing); Lemma 2 (signed-sum lemma: pair-graph on Liu's blocks, a
component with fewer edges than vertices is a tree, bipartite signs give a nonzero signed block sum bounded by Liu's advantage;
leftover piece handled); Liu's dyadic strategy with binary uniqueness giving advantage >= 1/(2^{n+1}-1); Xiang's strategy: equal
pairs cancel, subset-sum pigeonhole on the n+1 blocks (gap <= 1/D), overlay/common-refinement of the two rulers with at most
p+q-1 new marks, the one-empty-side case handled. Both annotators S=2; GLM-5.3 gate 4/4/4/4 pass. Read: no gap found. This is a
discovery event from an S=0 text within a single 200k-token continuation, without critique; the start text already stated the
correct closed form and the alternating-sum reduction.

p3-low-C-r1 (same start, WITH critique): returned text scored S=0 by both annotators; gate reject. Not read in detail (no S=2/pass).

p6-mid-C-r1, p6-mid-N-r1, p6-mid-N-r2 (S=1 public Kimi round-3 file as start): all three scored S=2 by both annotators; gates:
pass, pass, pending (third review re-run). Skimmed: each closes the finiteness crux with an argument of the compactness type
(every transversal contains a finite one / erasure of large primes) rather than the invalid self-dual-clutter step; periodicity
assembly retained from the start text. With and without the critique the same missing obligation was supplied.

p6-low-C-r2 (S=0 Nemotron candidate, WITH critique): S=2 (GLM) vs S=1 (Kimi); gate revise. Not counted as closure (raters disagree).

These are within-seed observations at one budget; they are reported as delivery and validity per run, not as rates.
