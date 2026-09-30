# Executable certificates for the v6 witness experiment (post hoc; no model in the loop)

Generated 2026-09-06 14:47:33 UTC by `python3 scripts/witness_checks.py --all` (Python 3.13.9, sympy 1.14.0, z3 4.15.4). 15/15 certificates PASS.

Reproduce from the repository root with exactly: `python3 scripts/witness_checks.py --all` (writes this file and `certificates.json` into `artifacts/witness_discovery/`). From a flat bundle containing only the script: `python3 witness_checks.py --all --out-dir .` (add `--cases cases.json` to cross-check the text hashes). Each check is also a subcommand printing its full output (last column). PASS means the computation confirms the objection as stated in RESULTS.md (for p1-board: refutes the earlier counterexample); each subcommand's docstring (`python3 scripts/witness_checks.py <check> --help`, or the source) states the reading of the text it encodes, the anchored quote and the case id.

| check | case(s) | ledger statement | what is checked | result | command |
|---|---|---|---|---|---|
| `p3-muse` | deedy-muse-spark-1.1-final | P3 L3.3 lower bound: Liu's guarantee, universal over Xiang's replies; answer c_n = 2^n/(2^{n+1}-1) | one Xiang reply refutes the claimed 3/5 guarantee of the division 2/5,2/5,1/5 | **PASS** | `p3-muse` |
| `p3-deepseek` | deedy-deepseek-v4-pro-final | P3 L3.3 lower bound: Liu's guarantee, universal over Xiang's replies; answer c_n = 2^n/(2^{n+1}-1) | one Xiang reply refutes the equally spaced construction; no 3-piece division reaches 3/5 at n=2 | **PASS** | `p3-deepseek` |
| `p3-grok` | deedy-grok-4.5-final | P3 L3.3 lower bound: Liu's guarantee, universal over Xiang's replies; answer c_n = 2^n/(2^{n+1}-1) | three counterexamples: virtual-cut refinement (L3.3), D(R)=s in Theorem C (L3.2), S_n-mu<=S_{n-1} (L3.3) | **PASS** | `p3-grok` |
| `p3-two-columns` | deedy-gpt-5.6-sol-final | P3 L3.2 upper bound: Xiang's reply, universal over Liu's division (Liu <= 2^n/(2^{n+1}-1)) | s=1, two columns of height T/2: the odd row never reaches d, the prescribed first cut is undefined | **PASS** | `p3-two-columns` |
| `p3-cut-parity` | deedy-gpt-5.6-sol-final | P3 L3.3 lower bound: Liu's guarantee, universal over Xiang's replies; answer c_n = 2^n/(2^{n+1}-1) | a column 2d cut into d/2, 3d/2 interchanges the parity rows below the cut level | **PASS** | `p3-cut-parity` |
| `p3-strip-count` | deedy-gpt-5.6-sol-final | P3 L3.3 lower bound: Liu's guarantee, universal over Xiang's replies; answer c_n = 2^n/(2^{n+1}-1) | strip arithmetic of the induction step for j <= 8 | **PASS** | `p3-strip-count --jmax 8` |
| `p3-kimi-order` | kimi-k3-round4-t014 | P3 L3.2 upper bound: Xiang's reply, universal over Liu's division (Liu <= 2^n/(2^{n+1}-1)) | nested absolute difference is order-dependent on the two quoted examples (decreasing order 5 vs 1; 4 vs 0) | **PASS** | `p3-kimi-order` |
| `p5-nemotron-z3` | p5-nemotron-2587b733-v2 | P5 L5.1 sufficiency: the chain holds for f(x) = x + c with middle term (x+y+c)/2 | z3 proves the chain with middle term (x+y+c)/2 for all x,y,c>0; the written (x+y+2c)/2 chain fails at (1,1,1) | **PASS** | `p5-nemotron-z3` |
| `p5-deepseek-dichotomy` | p5-deepseek-v4-pro-main-t033, p5-deepseek-v4-pro-main-t038 | P5 L5.3 nonnegative difference: g(x) = f(x) - x >= 0 for every x, needed before any value-set dichotomy | f(x)=x+1 is a solution with V={1}: premise holds, neither branch (i) nor (ii) holds; negative values never excluded | **PASS** | `p5-deepseek-dichotomy` |
| `p5-deepseek-typo` | p5-deepseek-v4-pro-main-t033, p5-deepseek-v4-pro-main-t038 | no ledger statement (harmless display error inside the necessity argument; checkers: fatal no) | sympy: A(x,y) at a=0,b=c is (x-y)^2+4cy+2c^2, the display has 4cx (harmless: both nonnegative) | **PASS** | `p5-deepseek-typo` |
| `p6-transversals` | p6-gpt-5.6-sol-main-t009, p6-deedy-gpt-5.6-sol-final | P6 L6.2 large-prime erasure / finiteness of the relevant prime set for all terms | F_k = {x_1..x_k, y_k}: 6 distinct minimal finite transversals T_k for k <= 6 | **PASS** | `p6-transversals --n 6` |
| `p6-gpt-transversals` | p6-gpt-5.6-sol-main-t009, p6-deedy-gpt-5.6-sol-final | P6 L6.2 large-prime erasure / finiteness of the relevant prime set for all terms | the graders' three families (F_k with x_0, E_i, G_i) have 8, 8, 7 distinct minimal finite transversals for K=8 | **PASS** | `p6-gpt-transversals --k 8` |
| `p6-gpt-recursion` | p6-gpt-5.6-sol-main-t009 | P6 L6.2 large-prime erasure / finiteness of the relevant prime set for all terms | the text's induction, run literally, outputs lists that miss genuine transversals on the four quoted instances | **PASS** | `p6-gpt-recursion` |
| `p6-kimi-infinite-transversal` | p6-kimi-k3-round2-t007 | P6 L6.2 large-prime erasure / finiteness of the relevant prime set for all terms | {{2,x_n}}: {x_1..x_N} is a minimal transversal of the truncation whose every subset misses {2,x_{N+1}}, N<=8 | **PASS** | `p6-kimi-infinite-transversal --N 8` |
| `p1-board` | p1-glm52-2ede1c6b-v1 | P1 L1.2 invariance: for each prime p, gcd_i v_p(a_i) is unchanged by a move; M = prod_p p^{gcd_i v_p(a_i)} | board [2, 3]: every play ends with the survivor M = prod p^gcd v_p (gcd(1,0)=1) | **PASS** | `p1-board --board 2 3` |

## Key values (one line per check, as printed by `--all`)

- `p3-muse`: Liu 2/5,2/5,1/5; Xiang halves 1/5 -> Liu 1/2 (minimax 1/2) < claimed 3/5; search min 1/2; c_2 = 4/7
- `p3-deepseek`: Liu 1/5,1/5,3/5; Xiang halves 3/5 -> Liu 1/2 (minimax 1/2) < claimed 3/5; no 3-piece division reaches 3/5 (z3 unsat); c_2 = 4/7
- `p3-grok`: (a) cuts 3/2,5/2: midpoint 2 inside [3/2,5/2]; (b) L=4,3/2,3/2: D(R)=0 not 3; (c) cut 7/2: S_2-mu=7/2 > S_1=3, dummy -1/2
- `p3-two-columns`: s=1, columns T/2,T/2: N(t)=2 on (0,T/2); odd row total 0 < d = 1/3; prescribed first cut exists: False
- `p3-cut-parity`: column 2d -> d/2 + 3d/2: N 1->2 on (0,d/2): parity interchanged below the cut level (also on (3d/2,2d))
- `p3-strip-count`: preceding strips 2^(j+1)-1; two copies+1 = 2^(j+2)-1 != 2^(j+1) for all j<=8 (two copies alone matches only j=0)
- `p3-kimi-order`: {10,9,8,7,5}: decreasing 5 vs 10,8,7,9,5 -> 1; {8,7,6,5,4}: decreasing 4 vs 8,6,5,7,4 -> 0
- `p5-nemotron-z3`: correct chain: z3 unsat/unsat; written left ineq at (1,1,1): sqrt(5/2)>=2 false; z3 finds violation (x=1, y=1, c=1)
- `p5-deepseek-dichotomy`: f=x+1: z3 both ineqs hold; V={1}: branch (i) False, branch (ii) False; premise-true/conclusion-false value sets: 5
- `p5-deepseek-typo`: A(a=0,b=c) = 2*c**2 + 4*c*y + x**2 - 2*x*y + y**2 vs displayed 4cx: difference 4*c*(x - y); at (1,2,1): 11 vs 7; harmless (both >= 0)
- `p6-transversals`: F_k={x_1..x_k,y_k}, k<=6: pairwise intersecting True; 6 distinct minimal transversals T_k (all verified)
- `p6-gpt-transversals`: F_k/E_i/G_i truncated at K=8: pairwise intersecting; 24 listed minimal transversals verified (grow linearly with K)
- `p6-gpt-recursion`: F={{1,2},{2,3}}, C={1,2}: list {{1,2},{2}} misses {1,3}; C\{1}={2} not a member of F_1; 4/4 instances miss a transversal
- `p6-kimi-infinite-transversal`: {{2,x_n}}: T={x_1..x_N} minimal transversal for N<=8; every subset of T misses {2,x_{N+1}}; infinite minimal transversal exists
- `p1-board`: board [2, 3]: valuation gcds {2: 1, 3: 1} (gcd(1,0)=1), M = 6, survivors [6]: earlier {2,3} counterexample refuted

## Texts

Each certificate names the case id(s) and the sha256 of the text (from `cases.json`). At generation time: 
- deedy-gpt-5.6-sol-final (P3): sha256 `e3e333cc484719cc...`; in cases.json: True; recomputed from the text file: True
- deedy-grok-4.5-final (P3): sha256 `13eda1f40c36141b...`; in cases.json: True; recomputed from the text file: True
- deedy-muse-spark-1.1-final (P3): sha256 `71a422af6fd1d951...`; in cases.json: True; recomputed from the text file: True
- deedy-deepseek-v4-pro-final (P3): sha256 `ca88f79fb210b7f0...`; in cases.json: True; recomputed from the text file: True
- kimi-k3-round4-t014 (P3): sha256 `ea4551d940174ea8...`; in cases.json: True; recomputed from the text file: True
- p6-gpt-5.6-sol-main-t009 (P6): sha256 `6990dbe90da76622...`; in cases.json: True; recomputed from the text file: True
- p6-deedy-gpt-5.6-sol-final (P6): sha256 `fc5dfc45e082cb70...`; in cases.json: True; recomputed from the text file: True
- p6-kimi-k3-round2-t007 (P6): sha256 `bd6057aef3ec542e...`; in cases.json: True; recomputed from the text file: True
- p1-glm52-2ede1c6b-v1 (P1): sha256 `e44bf6e398926288...`; in cases.json: True; recomputed from the text file: True
- p5-deepseek-v4-pro-main-t033 (P5): sha256 `cd94261ef509029c...`; in cases.json: True; recomputed from the text file: True
- p5-deepseek-v4-pro-main-t038 (P5): sha256 `98f919cec9ce8b25...`; in cases.json: True; recomputed from the text file: True
- p5-nemotron-2587b733-v2 (P5): sha256 `b2b39d07c1576889...`; in cases.json: True; recomputed from the text file: True

## Substantiated objections not encoded (no finite witness object)

- p6-deedy-gpt-5.6-sol-final: Konig-tree step 'Insert c at its first such occurrence...' (witnesses gpt/claude, grader e1). Reason: an invalid-inference objection about a proof step; there is no finite object to compute. The false 'finite blocker' fact that the step argues for is certified instead (p6-gpt-transversals).
- kimi-k3-round4-t014: Lemma 1.1 turn order ('moving first on M'' ... guarantees odd(M'')', grader gpt e0). Reason: a bookkeeping error about who moves first; nothing beyond counting two moves is computable, so no certificate is written.
- deedy-gpt-5.6-sol-final: 'each of total length at most (T-d)/2' from 'their uncancelled totals add to T-d' (witness claude, upper_bound). Reason: the objection is that a bound on a sum does not bound each summand; the instance a checker offers depends on a reading of the text's undefined 'arrays', so it is not encoded. The arithmetic half of the same witness is certified (p3-strip-count).

Generic tools used by the certificates: `p3` (rational-grid search of Xiang replies; its minimum is an upper bound on Liu's guarantee, one reply refutes a claimed guarantee above it), `p3-odd-rank` (exact claiming value, brute-force minimax), `p3-nested`, `p5-chain`, `p6-transversals`, `p1-board`.
