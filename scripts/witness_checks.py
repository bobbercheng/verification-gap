#!/usr/bin/env python3
"""Executable certificates for the finite / computable witnesses of the v6 witness experiment.

Written after the run and labelled post hoc (PROTOCOL.md Amendment 1.1). No model is in the loop: every check is a small exact
computation (Fractions, brute force, sympy identities, z3 decision procedures) that a reader can rerun. Each certificate's
docstring states (a) the reading of the text it encodes, (b) the anchored quote as recorded in
artifacts/witness_discovery/RESULTS.md, (c) the case id from artifacts/witness_discovery/cases.json and (d) the ledger statement
(research/v7_plan/REFERENCE_LEDGER.md) the error affects.

Usage
  witness_checks.py --all [--out-dir DIR] [--cases cases.json] [--no-write]
        run every certificate; print one PASS/FAIL line per check with the key numbers; write certificates.json and
        CERTIFICATES.md into DIR (default: <repo>/artifacts/witness_discovery when the script sits in <repo>/scripts,
        otherwise the script's own directory). Exit status 0 iff every certificate passes.
  witness_checks.py <check> [options]        run one check and print its full output

Generic tools (parameterised; the certificates call them):
  p3 --pieces 2/5 2/5 1/5 --n 2 [--grid 12]  Liu's exact claiming value after each searched Xiang reply with <= n cuts on a
                                             rational grid. The minimum over the searched replies is an UPPER bound on what Liu
                                             can guarantee: one Xiang reply refutes a claimed Liu guarantee above it. The search
                                             is not exhaustive, so the value is not a lower bound on what Xiang can force.
  p3-odd-rank --pieces 1/7 2/7 4/7           odd-rank sum = exact claiming-phase minimax (brute force confirms greedy is optimal)
  p3-nested 10 8 7 9 5                       nested absolute difference in the given order and in decreasing order
  p5-chain 1 1 1                             float evaluation of the P5 chain with the true and the written middle term
  p6-transversals --n 6                      the family F_k = {x_1..x_k, y_k}: minimal finite transversals T_k for k <= n
  p1-board --board 2 3                       every play on a small board; terminal survivors versus M = prod_p p^{gcd_i v_p(a_i)}
Certificates (each also a subcommand; all are run by --all):
  p3-muse  p3-deepseek  p3-grok  p3-two-columns  p3-cut-parity  p3-strip-count  p3-kimi-order
  p5-nemotron-z3  p5-deepseek-dichotomy  p5-deepseek-typo
  p6-transversals  p6-gpt-transversals  p6-gpt-recursion  p6-kimi-infinite-transversal
  p1-board
Dependencies: the Python 3 standard library; sympy and z3-solver for the P5 checks and one P3 check (imported only there).
The script imports nothing from the repository; paths come from arguments or are resolved relative to this file, so it also
runs from a flat bundle (copy this file anywhere and run `python3 witness_checks.py --all --out-dir .`).
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, os, re, sys
from datetime import datetime, timezone
from fractions import Fraction as Fr
from functools import lru_cache, reduce
from math import gcd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ARTIFACT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "artifacts", "witness_discovery"))

# Case table: id -> (problem, sha256 of the text), copied from artifacts/witness_discovery/cases.json (built 2026-09-06 04:31 UTC).
# --all cross-checks these against cases.json when that file is found, and recomputes the hashes when the texts are present.
CASES = {
    "deedy-gpt-5.6-sol-final": ("3", "e3e333cc484719ccebc6a5548f8b6c163dddb915e809349911f34a738ea993cb"),
    "deedy-grok-4.5-final": ("3", "13eda1f40c36141ba704bb16e6a8d6ca25d07d3e21c5ba3108dca292b1a228fe"),
    "deedy-muse-spark-1.1-final": ("3", "71a422af6fd1d951df4a1ddf18bc52d185785cca4fb2fba0f2ce598482cd2aaa"),
    "deedy-deepseek-v4-pro-final": ("3", "ca88f79fb210b7f04efa2e2d249db11f004339827e12234f8327b4b3a3e8bbc7"),
    "kimi-k3-round4-t014": ("3", "ea4551d940174ea8d30530fb2028c4928b02bb273e08c18fe25cd6bbdb70019b"),
    "p6-gpt-5.6-sol-main-t009": ("6", "6990dbe90da76622b26f9510d0b8163b19fe175412bcdc7e018e9ca7b6bef1b3"),
    "p6-deedy-gpt-5.6-sol-final": ("6", "fc5dfc45e082cb7098a6eacd00e75ec55f5cc92126933e3e344e7fc02a6877de"),
    "p6-kimi-k3-round2-t007": ("6", "bd6057aef3ec542eb8c7f56e42cab32e612e55f6a646d5944e0699df0c3ff757"),
    "p1-glm52-2ede1c6b-v1": ("1", "e44bf6e398926288265458bf46e3c88c73121bce41f2f70ea19c5c151b1dca55"),
    "p5-deepseek-v4-pro-main-t033": ("5", "cd94261ef509029c1c3e87c752af9f4ab0b8846c7ec6c375e51c59c790c3d523"),
    "p5-deepseek-v4-pro-main-t038": ("5", "98f919cec9ce8b25e96846b2d00edd0ca10307aa56473256a2edafa12aec1573"),
    "p5-nemotron-2587b733-v2": ("5", "b2b39d07c15768898e2fec5011ceb4a759cf3065fd2f71451507e8cc2106b7bf"),
}
# Ledger statements (research/v7_plan/REFERENCE_LEDGER.md) affected by the certified errors.
LEDGER = {
    "L1.2": "P1 L1.2 invariance: for each prime p, gcd_i v_p(a_i) is unchanged by a move; M = prod_p p^{gcd_i v_p(a_i)}",
    "L3.2": "P3 L3.2 upper bound: Xiang's reply, universal over Liu's division (Liu <= 2^n/(2^{n+1}-1))",
    "L3.3": "P3 L3.3 lower bound: Liu's guarantee, universal over Xiang's replies; answer c_n = 2^n/(2^{n+1}-1)",
    "L5.1": "P5 L5.1 sufficiency: the chain holds for f(x) = x + c with middle term (x+y+c)/2",
    "L5.3": "P5 L5.3 nonnegative difference: g(x) = f(x) - x >= 0 for every x, needed before any value-set dichotomy",
    "L6.2": "P6 L6.2 large-prime erasure / finiteness of the relevant prime set for all terms",
    "none": "no ledger statement (harmless display error inside the necessity argument; checkers: fatal no)",
}
# Substantiated objections that have no finite witness object and are therefore not encoded (reported in CERTIFICATES.md).
NOT_ENCODED = [
    ("p6-deedy-gpt-5.6-sol-final", "Konig-tree step 'Insert c at its first such occurrence...' (witnesses gpt/claude, grader e1)",
     "an invalid-inference objection about a proof step; there is no finite object to compute. The false 'finite blocker' fact "
     "that the step argues for is certified instead (p6-gpt-transversals)."),
    ("kimi-k3-round4-t014", "Lemma 1.1 turn order ('moving first on M'' ... guarantees odd(M'')', grader gpt e0)",
     "a bookkeeping error about who moves first; nothing beyond counting two moves is computable, so no certificate is written."),
    ("deedy-gpt-5.6-sol-final", "'each of total length at most (T-d)/2' from 'their uncancelled totals add to T-d' (witness claude, upper_bound)",
     "the objection is that a bound on a sum does not bound each summand; the instance a checker offers depends on a reading of "
     "the text's undefined 'arrays', so it is not encoded. The arithmetic half of the same witness is certified (p3-strip-count)."),
]

# ============================================================================================ generic P3 helpers
def odd_rank_sum(pieces):
    """Claiming phase: players alternately take the largest remaining piece. For a fixed multiset greedy is optimal and the exact
    minimax equals the sum of the pieces of odd rank in decreasing order (brute force in minimax_claim confirms on small inputs)."""
    s = sorted(pieces, reverse=True)
    return sum(s[0::2])

def alt_sum(pieces):
    """D(L) = a_1 - a_2 + a_3 - ... over the decreasing order (the 'alternating sum' of the P3 write-ups); Liu's share is (sum + D)/2."""
    s = sorted(pieces, reverse=True)
    return sum(v if i % 2 == 0 else -v for i, v in enumerate(s))

def minimax_claim(pieces):
    """Exact minimax of the claiming phase by brute force (Liu moves first, both players maximise their own total)."""
    pieces = tuple(sorted(pieces))
    @lru_cache(None)
    def val(mask, turn):  # (liu_total, xiang_total) from this state under optimal play
        rem = [i for i in range(len(pieces)) if mask >> i & 1]
        if not rem: return (Fr(0), Fr(0))
        best = None
        for i in rem:
            l, x = val(mask & ~(1 << i), 1 - turn)
            cand = (l + pieces[i], x) if turn == 0 else (l, x + pieces[i])
            if best is None or cand[turn] > best[turn]: best = cand
        return best
    return val((1 << len(pieces)) - 1, 0)[0]

def xiang_best_reply(pieces, n, denom_grid):
    """Search Xiang replies: choose <= n cut positions on a rational grid inside Liu's pieces (cuts inside a piece split it; several
    cuts may land in one piece). Returns (v, cuts): v is the minimum over the searched replies of Liu's claiming value and cuts is
    a reply attaining it. v is an UPPER bound on what Liu can guarantee with these pieces: the single reply `cuts` refutes any
    claimed guarantee above v. The search is not exhaustive, so v is NOT a lower bound on what Xiang can force."""
    pieces = [Fr(p) for p in pieces]
    cands = [(idx, p * Fr(k, denom_grid)) for idx, p in enumerate(pieces) for k in range(1, denom_grid)]
    best, best_cuts = odd_rank_sum(pieces), ()
    for m in range(1, n + 1):
        for combo in itertools.combinations(cands, m):
            bypiece = {}
            for idx, pos in combo: bypiece.setdefault(idx, []).append(pos)
            new = list(pieces); extra = []; ok = True
            for idx, poss in bypiece.items():
                poss = sorted(set(poss))
                if len(poss) != len(bypiece[idx]): ok = False; break
                prev = Fr(0); parts = []
                for pos in poss: parts.append(pos - prev); prev = pos
                parts.append(pieces[idx] - prev)
                new[idx] = parts[0]; extra += parts[1:]
            if not ok: continue
            v = odd_rank_sum(new + extra)
            if v < best: best, best_cuts = v, combo
    return best, best_cuts

def nested_abs_diff(seq):
    """||...||b1-b2|-b3|...-br| in the given order (the 'chain value' of a P3 write-up is this in the decreasing order)."""
    v = Fr(seq[0])
    for b in seq[1:]: v = abs(v - Fr(b))
    return v

def n_profile(heights):
    """Column model of the GPT P3 final: members are vertical columns; N(t) = number of columns reaching level t. Returns the
    intervals (lo, hi, N) on which N is constant, from level 0 up to the tallest column."""
    hs = [Fr(h) for h in heights]
    bps = sorted(set([Fr(0)] + hs))
    return [(lo, hi, sum(1 for h in hs if h > lo)) for lo, hi in zip(bps, bps[1:])]

def odd_measure(heights):
    """int (N(t) mod 2) dt, the text's display (5) for Delta(A)."""
    return sum(hi - lo for lo, hi, N in n_profile(heights) if N % 2 == 1)

def p5_chain(x, y, c):
    """P5 chain for f(t) = t + c: sqrt((x^2+f(y)^2)/2) >= (f(x)+y)/2 >= sqrt(x f(y)). Returns (left, true middle (x+y+c)/2,
    written middle (x+y+2c)/2, right) as floats."""
    import math
    x, y, c = float(x), float(y), float(c)
    return math.sqrt((x * x + (y + c) ** 2) / 2), (x + c + y) / 2, (x + y + 2 * c) / 2, math.sqrt(x * (y + c))

# ============================================================================================ transversal helpers
def _skey(s):
    m = re.match(r"([A-Za-z]+)(\d+)$", str(s))
    return (m.group(1), int(m.group(2))) if m else (str(s), -1)

def fset(s):
    return "{" + ", ".join(str(v) for v in sorted(s, key=_skey)) + "}"

def is_transversal(T, fam):
    return all(T & f for f in fam)

def is_minimal_transversal(T, fam):
    return is_transversal(T, fam) and all(not is_transversal(T - {t}, fam) for t in T)

def minimal_transversals(fam):
    """All inclusion-minimal transversals of a finite family, by brute force over subsets of the ground set."""
    ground = sorted(set().union(*fam), key=_skey)
    out = []
    for r in range(0, len(ground) + 1):
        for comb in itertools.combinations(ground, r):
            T = frozenset(comb)
            if is_minimal_transversal(T, fam): out.append(T)
    return out

def p6_family(n):
    """F_k = {x_1,...,x_k, y_k} for k = 1..n: pairwise intersecting (all contain x_1). T_k = {y_1,...,y_{k-1}, x_k} meets every F_j
    (j < k via y_j, j >= k via x_k) and is minimal: dropping y_j (j < k) leaves F_j unhit (its y is y_j and its x's are x_1..x_j
    with j < k, none equal to x_k); dropping x_k leaves F_k unhit (F_k contains none of y_1..y_{k-1})."""
    F = [frozenset([f"x{i}" for i in range(1, k + 1)] + [f"y{k}"]) for k in range(1, n + 1)]
    out = []
    for k in range(1, n + 1):
        T = frozenset([f"y{j}" for j in range(1, k)] + [f"x{k}"])
        out.append((k, sorted(T, key=_skey), is_transversal(T, F), is_minimal_transversal(T, F)))
    pairwise = all(F[i] & F[j] for i in range(n) for j in range(i + 1, n))
    return pairwise, out

def restricted_list(F, C):
    """The GPT P6 text's induction, run literally. Input: a pairwise-intersecting family F (list of frozensets) and a finite
    transversal C of F. Output: the list of sets {c} u D_{c,k} (c in C, D_{c,k} from the recursive call on (F_c, C \\ {c}) with
    F_c = members not containing c), which the text uses as 'X traverses F iff X contains a listed set'. Base case: F empty -> [{}]
    (the text: C = {} forces F = {}, and then every finite set is a transversal). The assertion the text actually proves at each
    level covers only transversals meeting the current C; the output is exactly that restricted list."""
    if not F: return [frozenset()]
    out = []
    for c in sorted(C, key=_skey):
        Fc = [f for f in F if c not in f]
        for D in restricted_list(Fc, C - {c}):
            S = frozenset({c}) | D
            if S not in out: out.append(S)
    return out

# ============================================================================================ P1 board
def p1_moves(board):
    """All plays: a move replaces two entries m, n > 1 by gcd(m, n) and lcm(m, n)/gcd(m, n). Returns (reachable boards, terminal boards)."""
    board = tuple(sorted(board)); seen = set(); finals = set(); stack = [board]
    while stack:
        b = stack.pop()
        if b in seen: continue
        seen.add(b)
        idx = [i for i, v in enumerate(b) if v > 1]
        if len(idx) < 2: finals.add(b); continue
        for i, j in itertools.combinations(idx, 2):
            m, n_ = b[i], b[j]; g = gcd(m, n_)
            nb = list(b); nb[i] = g; nb[j] = (m * n_ // g) // g
            stack.append(tuple(sorted(nb)))
    return seen, finals

def vp(n, p):
    c = 0
    while n > 0 and n % p == 0: n //= p; c += 1
    return c

def primes_dividing(board):
    return sorted({p for v in board for p in range(2, v + 1) if v % p == 0 and all(p % q for q in range(2, int(p ** .5) + 1))})

def p1_M(board):
    """M = prod_p p^{gcd_i v_p(a_i)} with Python's convention gcd(k, 0) = k (so a prime dividing only some entries contributes gcd(...,0,...))."""
    return reduce(lambda acc, p: acc * p ** reduce(gcd, [vp(v, p) for v in board]), primes_dividing(board), 1)

# ============================================================================================ certificate plumbing
def cert(check, case_ids, ledger_key, what, claim, ok, key_values, lines, summary):
    return {"check": check, "case_ids": list(case_ids), "ledger_statement": LEDGER[ledger_key], "ledger_key": ledger_key,
            "what_is_checked": what, "claim_checked": claim, "result": "PASS" if ok else "FAIL", "summary": summary,
            "key_values": key_values, "sha256_of_texts": {c: CASES[c][1] for c in case_ids}, "_lines": lines}

def J(o):
    """JSON-friendly copy: Fractions as 'p/q' strings (integers as ints), sets as sorted lists."""
    if isinstance(o, bool) or o is None or isinstance(o, (int, float, str)): return o
    if isinstance(o, Fr): return int(o) if o.denominator == 1 else str(o)
    if isinstance(o, dict): return {str(k): J(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [J(v) for v in o]
    if isinstance(o, (set, frozenset)): return sorted((J(v) for v in o), key=str)
    return str(o)

def fr(v):
    return str(Fr(v))

# ============================================================================================ P3 certificates
def check_p3_muse(grid=12):
    """p3-muse -- case deedy-muse-spark-1.1-final (P3), ledger L3.3 (and the answer).
    Quote: 'So seems this construction guarantees at least 3/5.' (grader claude e0, substantiated). Reading: 'this construction' is
    the text's n = 2 division 2/5, 2/5, 1/5 (n pieces of size 2d and one of size d, d = 1/(2n+1)), and a guarantee is universal over
    Xiang's replies, so ONE reply with Liu value below 3/5 refutes it. Reply: Xiang uses a single cut (fewer than n is allowed)
    halving the 1/5 piece: pieces 2/5, 2/5, 1/10, 1/10; claiming value = odd-rank sum = 2/5 + 1/10 = 1/2; brute-force minimax
    confirms. Also reported: the replies quoted by the checkers (0.4 -> 0.35 + 0.05 and 0.2 -> 0.1 + 0.1, and both cuts inside the
    1/5 piece as 1/10, 1/20, 1/20; both give 11/20 < 3/5) and the minimum of the p3 grid search with <= 2 cuts. cases.json records
    the coarser documented value 0.505; the exact reply gives 1/2, the floor (the alternating sum is never negative)."""
    pieces = [Fr(2, 5), Fr(2, 5), Fr(1, 5)]; claimed = Fr(3, 5); correct = Fr(4, 7)
    after = [Fr(2, 5), Fr(2, 5), Fr(1, 10), Fr(1, 10)]
    v, mm = odd_rank_sum(after), minimax_claim(after)
    alt_glm = [Fr(2, 5), Fr(7, 20), Fr(1, 20), Fr(1, 10), Fr(1, 10)]
    alt_gpt = [Fr(2, 5), Fr(2, 5), Fr(1, 10), Fr(1, 20), Fr(1, 20)]
    vg, vp_ = odd_rank_sum(alt_glm), odd_rank_sum(alt_gpt)
    smin, cuts = xiang_best_reply(pieces, 2, grid)
    ok = v == Fr(1, 2) and mm == v and v < claimed and smin <= v and minimax_claim(alt_glm) == vg and minimax_claim(alt_gpt) == vp_
    kv = {"liu_pieces": pieces, "claimed_guarantee": claimed, "correct_c_2": correct, "xiang_reply": "halve the 1/5 piece (one cut)",
          "pieces_after": after, "liu_value_odd_rank": v, "liu_value_minimax": mm,
          "checker_replies": {"glm 0.35/0.05 + 0.1/0.1": vg, "gpt both cuts in 1/5 (1/10,1/20,1/20)": vp_},
          "grid_search_min_liu_value": smin, "grid_search_cuts": [(i, p) for i, p in cuts], "grid": grid}
    lines = [f"Liu pieces {[fr(p) for p in pieces]} (text's n=2 construction), claimed guarantee {claimed}, correct c_2 = {correct}",
             f"Xiang halves the 1/5 piece -> {[fr(p) for p in after]}: odd-rank sum {v}, brute-force minimax {mm}: {v} < {claimed}",
             f"checker replies: {[fr(p) for p in alt_glm]} -> {vg}; {[fr(p) for p in alt_gpt]} -> {vp_}",
             f"grid search (<= 2 cuts, 1/{grid} grid): min Liu value {smin} at cuts {[(i, fr(p)) for i, p in cuts]} (upper bound on Liu's guarantee)"]
    return cert("p3-muse", ["deedy-muse-spark-1.1-final"], "L3.3", "one Xiang reply refutes the claimed 3/5 guarantee of the division 2/5,2/5,1/5",
                "the text's n=2 construction (2/5, 2/5, 1/5) guarantees Liu at least 3/5 against every Xiang reply", ok, kv, lines,
                f"Liu 2/5,2/5,1/5; Xiang halves 1/5 -> Liu {v} (minimax {mm}) < claimed {claimed}; search min {smin}; c_2 = {correct}")

def check_p3_deepseek(grid=12, denom=60):
    """p3-deepseek -- case deedy-deepseek-v4-pro-final (P3), ledger L3.3 (and the answer).
    Quote: 'The strategy is to mark points at 1/(2n+1), 2/(2n+1), ..., n/(2n+1).' offered as guaranteeing c = (n+1)/(2n+1)
    (grader claude e1, substantiated). Reading: n = 2, marks 1/5, 2/5 -> pieces 1/5, 1/5, 3/5. Reply: one Xiang cut halving the 3/5
    piece -> 3/10, 3/10, 1/5, 1/5, which pair up; claiming value 1/2 < 3/5 (odd-rank sum; brute-force minimax confirms).
    Second part, quote 'Conjecture: Liu Bang can guarantee c = (n+1)/(2n+1).' (grader claude e0, substantiated): no division into
    at most 3 pieces guarantees 3/5 at n = 2. For pieces a >= b >= c > 0 with a + b + c = 1 three replies give Liu exactly
    (1+c)/2 (halve a and b: the equal pairs cancel, D = c), a + c/2 (halve c: D = a - b) and b + a/2 (halve a). The formulas are
    verified exactly against the odd-rank sum on the rational grid of all (a, b, c) with denominator `denom`, and z3 (linear real
    arithmetic) reports unsat for 'all three >= 3/5'. With fewer than two marks Xiang halves every piece and Liu gets 1/2."""
    pieces = [Fr(1, 5), Fr(1, 5), Fr(3, 5)]; claimed = Fr(3, 5); correct = Fr(4, 7)
    after = [Fr(1, 5), Fr(1, 5), Fr(3, 10), Fr(3, 10)]
    v, mm = odd_rank_sum(after), minimax_claim(after)
    smin, cuts = xiang_best_reply(pieces, 2, grid)
    # formulas for the three replies, checked exactly on a rational grid
    n_grid = 0; formulas_ok = True
    for cn in range(1, denom):
        for bn in range(cn, denom):
            an = denom - bn - cn
            if an < bn: continue
            a, b, c = Fr(an, denom), Fr(bn, denom), Fr(cn, denom); n_grid += 1
            if odd_rank_sum([a / 2, a / 2, b / 2, b / 2, c]) != (1 + c) / 2: formulas_ok = False
            if odd_rank_sum([a, b, c / 2, c / 2]) != a + c / 2: formulas_ok = False
            if odd_rank_sum([a / 2, a / 2, b, c]) != b + a / 2: formulas_ok = False
    try:
        import z3
        a, b, c = z3.Reals("a b c"); s = z3.Solver()
        s.add(a >= b, b >= c, c > 0, a + b + c == 1, (1 + c) / 2 >= z3.Q(3, 5), a + c / 2 >= z3.Q(3, 5), b + a / 2 >= z3.Q(3, 5))
        z3_res = str(s.check())
    except ImportError:
        z3_res = "z3 not installed"
    forced = (Fr(2, 5), Fr(3, 10), Fr(3, 10)); forced_val = forced[1] + forced[0] / 2
    ok = v == Fr(1, 2) and mm == v and v < claimed and smin <= v and formulas_ok and z3_res == "unsat" and forced_val == Fr(1, 2)
    kv = {"liu_marks": [Fr(1, 5), Fr(2, 5)], "liu_pieces": pieces, "claimed_guarantee": claimed, "correct_c_2": correct,
          "xiang_reply": "halve the 3/5 piece (one cut)", "pieces_after": after, "liu_value_odd_rank": v, "liu_value_minimax": mm,
          "grid_search_min_liu_value": smin, "grid_search_cuts": [(i, p) for i, p in cuts],
          "three_reply_formulas_verified_on_grid": formulas_ok, "grid_points": n_grid, "grid_denominator": denom,
          "z3_all_three_replies_ge_3_over_5": z3_res, "division_forced_by_the_inequalities": forced, "its_value_after_halving_a": forced_val}
    lines = [f"Liu marks 1/5, 2/5 -> pieces {[fr(p) for p in pieces]}; claimed guarantee {claimed}; correct c_2 = {correct}",
             f"Xiang halves the 3/5 piece -> {[fr(p) for p in after]}: odd-rank sum {v}, brute-force minimax {mm}: {v} < {claimed}",
             f"grid search (<= 2 cuts, 1/{grid} grid): min Liu value {smin} at cuts {[(i, fr(p)) for i, p in cuts]}",
             f"no 3-piece division guarantees 3/5: reply values (1+c)/2, a+c/2, b+a/2 verified on {n_grid} grid points ({formulas_ok});"
             f" z3 'all three >= 3/5' under a>=b>=c>0, a+b+c=1: {z3_res}; the inequalities force {tuple(fr(t) for t in forced)}, halving a then gives {forced_val}"]
    return cert("p3-deepseek", ["deedy-deepseek-v4-pro-final"], "L3.3", "one Xiang reply refutes the equally spaced construction; no 3-piece division reaches 3/5 at n=2",
                "marks at k/(2n+1) guarantee (n+1)/(2n+1) (n=2: 1/5,1/5,3/5 guarantees 3/5), and 3/5 is attainable at n=2", ok, kv, lines,
                f"Liu 1/5,1/5,3/5; Xiang halves 3/5 -> Liu {v} (minimax {mm}) < claimed {claimed}; no 3-piece division reaches 3/5 (z3 {z3_res}); c_2 = {correct}")

def check_p3_grok():
    """p3-grok -- case deedy-grok-4.5-final (P3). Three finite witnesses, all substantiated. D(L) is the text's alternating sum
    sum_i (-1)^{i-1} a_i over the decreasing order; B_n = {1, 2, ..., 2^n}, S_n = 2^{n+1} - 1.
    (a) ledger L3.3, quote: 'The virtual cut partitions the large bin into two sub-sticks of length tau each; the actual pieces of
        Q are a common refinement of those two sub-sticks.' (witness gpt, lower_bound). Reading: n = 2, large bin of length 4,
        tau = 2; Xiang's two cuts inside the bin at 1.5 and 2.5 give Q = {1.5, 1, 1.5} (all <= tau, so the subcase's hypothesis
        holds); Q refines the halves [0,2], [2,4] only if the midpoint 2 is a cut point, and 2 lies strictly inside [1.5, 2.5].
    (b) ledger L3.2, quote: 'Taking the remainder as a single piece (using 0 cuts) already yields D(R)=s=S_n-mu, hence' (witness
        gpt, upper_bound). Reading: Theorem C's large-piece case; L = {4, 1.5, 1.5}, n = 2, S_2 = 7, tau = 2^n = 4, unique mu = 4
        >= tau, remainder R = {1.5, 1.5} already split by Liu's marks: D(R) = 0, not s = S_2 - mu = 3 (Xiang can cut, not merge).
        The text's D(M) = mu - D(R) then gives 4, not <= 1. (Side value: cutting 4 into 2.5 + 1.5 does give D = 1, an argument the
        text does not make.)
    (c) ledger L3.3, quote: '... a subdivision of a stick of length 2^n-mu+sum P=S_n-mu<=S_{n-1} performed with at most m+(k-1)<=n-1
        cuts.' (witness claude, lower_bound). Reading: n = 2, S_2 = 7, S_1 = 3, tau = 2, P = {1, 2}; one cut inside the bin of
        length 4 at 3.5: Q = {3.5, 0.5}, mu = 3.5 > tau (the subcase's hypothesis); S_2 - mu = 3.5 > 3 = S_1, so the asserted
        inequality fails; the dummy piece S_1 - (S_2 - mu) = -0.5 has negative length and d := mu - tau = 1.5 is not
        S_{n-1} - (S_n - mu) = mu - 2^n = -0.5."""
    n = 2; bins = [1, 2, 4]; L = Fr(4); tau_b = Fr(2); S2, S1 = Fr(7), Fr(3)
    # (a)
    cuts = [Fr(3, 2), Fr(5, 2)]; pts = [Fr(0)] + cuts + [L]
    Q = [hi - lo for lo, hi in zip(pts, pts[1:])]
    mid = L / 2; refines = mid in set(pts)
    straddle = next(((lo, hi) for lo, hi in zip(pts, pts[1:]) if lo < mid < hi), None)
    a_ok = Q == [Fr(3, 2), Fr(1), Fr(3, 2)] and all(q <= tau_b for q in Q) and not refines and straddle == (Fr(3, 2), Fr(5, 2))
    # (b)
    Lb = [Fr(4), Fr(3, 2), Fr(3, 2)]; tau_c = Fr(2 ** n); mu_b = max(Lb); R = [Fr(3, 2), Fr(3, 2)]
    DR = alt_sum(R); s_text = S2 - mu_b; DM = alt_sum(Lb); DM_text = mu_b - DR
    side = alt_sum([Fr(5, 2), Fr(3, 2), Fr(3, 2), Fr(3, 2)])
    b_ok = sum(Lb) == S2 and mu_b >= tau_c and sum(1 for p in Lb if p >= tau_c) == 1 and DR == 0 and s_text == 3 and DM == 4 and DM_text == 4 and side == 1
    # (c)
    cut = Fr(7, 2); Qc = [cut, L - cut]; mu_c = max(Qc); P = [Fr(1), Fr(2)]
    lhs = S2 - mu_c; dummy = S1 - lhs; d_text = mu_c - tau_b; d_true = mu_c - 2 ** n
    c_ok = mu_c > tau_b and lhs > S1 and dummy < 0 and d_text != d_true and sum(P) + (2 ** n - mu_c) == lhs
    ok = a_ok and b_ok and c_ok
    kv = {"n": n, "bins": bins,
          "a": {"cuts_in_bin_of_length_4": cuts, "Q": Q, "all_pieces_le_tau": all(q <= tau_b for q in Q), "midpoint": mid,
                "midpoint_is_a_cut_point": refines, "piece_straddling_midpoint": straddle},
          "b": {"L": Lb, "S_2": S2, "tau": tau_c, "mu": mu_b, "R": R, "D_R": DR, "text_s_equals_S_n_minus_mu": s_text,
                "text_D_M_equals_mu_minus_D_R": DM_text, "D_of_L": DM, "side_value_D_after_cutting_4_into_2.5_1.5": side},
          "c": {"cut_in_bin_of_length_4": cut, "Q": Qc, "mu": mu_c, "tau": tau_b, "S_2_minus_mu": lhs, "S_1": S1,
                "dummy_length_S_1_minus_(S_2_minus_mu)": dummy, "d_text_mu_minus_tau": d_text, "mu_minus_2^n": d_true}}
    lines = [f"(a) n=2, bin of length 4, tau=2, cuts at 3/2 and 5/2: Q = {[fr(q) for q in Q]} (all <= tau); midpoint 2 is a cut point: {refines};"
             f" it lies strictly inside [{fr(straddle[0])}, {fr(straddle[1])}] -> Q is not a common refinement of the two halves",
             f"(b) L = {[fr(p) for p in Lb]}, S_2 = 7, tau = 4, unique mu = 4: remainder R = {[fr(p) for p in R]} has D(R) = {DR}, text asserts s = S_2 - mu = {s_text};"
             f" text's D(M) = mu - D(R) = {DM_text} (not <= 1); cutting 4 into 5/2 + 3/2 would give D = {side}",
             f"(c) one cut at 7/2 in the bin of length 4: Q = {[fr(q) for q in Qc]}, mu = {mu_c} > tau = 2; S_2 - mu = {lhs} > S_1 = {S1};"
             f" dummy length {dummy} < 0; d = mu - tau = {d_text} but S_1 - (S_2 - mu) = mu - 2^n = {d_true}"]
    return cert("p3-grok", ["deedy-grok-4.5-final"], "L3.3", "three counterexamples: virtual-cut refinement (L3.3), D(R)=s in Theorem C (L3.2), S_n-mu<=S_{n-1} (L3.3)",
                "(a) Q refines the two virtual halves; (b) the untouched remainder has D(R) = S_n - mu; (c) S_n - mu <= S_{n-1} whenever mu > tau", ok, kv, lines,
                f"(a) cuts 3/2,5/2: midpoint 2 inside [3/2,5/2]; (b) L=4,3/2,3/2: D(R)={DR} not 3; (c) cut 7/2: S_2-mu={lhs} > S_1={S1}, dummy {dummy}")

def check_p3_two_columns(T=Fr(1)):
    """p3-two-columns -- case deedy-gpt-5.6-sol-final (P3), ledger L3.2 (Lemma (i) carries the upper bound).
    Quote: 'Set d=T/(2^{s+1}-1). When the first row has accumulated length d, cut the column crossed at that instant and put its
    lower portion in the other row; below that level the two rows are interchanged.' (witness gpt, upper_bound, substantiated).
    Reading (the checkers'): members are vertical columns, N(t) = number of columns reaching level t, Delta(A) = int (N(t) mod 2) dt
    (the text's display (5)); the sweep descends from the top and records each portion in the odd row when N(t) is odd and in the
    even row when N(t) is even; 'the first row' is the odd-parity row (its total is Delta, the quantity being bounded). Witness:
    s = 1 and two columns of height T/2 (at most s+1 columns, total T): N(t) = 2 on (0, T/2) and 0 above, so the odd row accumulates
    length 0 < d = T/3 at every level and the prescribed first cut never occurs. The check computes N(t) exactly on the intervals
    between the sorted heights, the odd/even accumulated lengths and Delta, and verifies display (5) on this and other examples.
    Note: here Delta = 0 <= d already, so the lemma's conclusion holds with zero cuts; the certified gap is that the written
    construction is undefined for this input (checkers: claude 'fatal no', glm 'fatal yes')."""
    s = 1; heights = [T / 2, T / 2]; d = T / (2 ** (s + 1) - 1)
    prof = n_profile(heights)
    odd_total = sum(hi - lo for lo, hi, N in prof if N % 2 == 1)
    even_total = sum(hi - lo for lo, hi, N in prof if N >= 1 and N % 2 == 0)
    first_cut_exists = odd_total >= d
    delta = alt_sum(heights)
    examples = [[Fr(1), Fr(2), Fr(4)], [Fr(3, 2), Fr(1), Fr(3, 2)], [Fr(9, 10), Fr(1, 10)], [Fr(7, 2), Fr(1, 2), Fr(1), Fr(2)]]
    ident = all(alt_sum(e) == odd_measure(e) for e in examples + [heights])
    ok = (not first_cut_exists) and odd_total == 0 and all(N % 2 == 0 for _, _, N in prof) and ident and delta == 0 and delta <= d
    kv = {"s": s, "T": T, "columns": heights, "d": d, "N_profile": [(lo, hi, N) for lo, hi, N in prof], "odd_row_total": odd_total,
          "even_row_total": even_total, "first_cut_instant_exists": first_cut_exists, "Delta": delta, "Delta_le_d": delta <= d,
          "display_5_verified_on": [[fr(v) for v in e] for e in examples + [heights]], "display_5_ok": ident}
    lines = [f"s = {s}, T = {T}, columns {[fr(h) for h in heights]}, d = T/(2^(s+1)-1) = {d}",
             f"N(t): " + "; ".join(f"({fr(lo)},{fr(hi)}) -> {N}" for lo, hi, N in prof) + " (even everywhere)",
             f"odd row accumulates {odd_total} (< d = {d}) at every level, even row {even_total}: the instant 'first row has accumulated length d' does not exist: {not first_cut_exists}",
             f"Delta = int(N mod 2) = {delta} = a_1 - a_2 (display (5) verified on {len(examples) + 1} examples: {ident}); Delta <= d holds here without any cut"]
    return cert("p3-two-columns", ["deedy-gpt-5.6-sol-final"], "L3.2", "s=1, two columns of height T/2: the odd row never reaches d, the prescribed first cut is undefined",
                "the sweep's first operation ('when the first row has accumulated length d, cut ...') exists for every input of Lemma (i)", ok, kv, lines,
                f"s=1, columns T/2,T/2: N(t)=2 on (0,T/2); odd row total {odd_total} < d = {d}; prescribed first cut exists: {first_cut_exists}")

def check_p3_cut_parity(d=Fr(1)):
    """p3-cut-parity -- case deedy-gpt-5.6-sol-final (P3), ledger L3.3 (Lemma (ii) carries the lower bound).
    Quote: 'A cut can interchange the two parity rows only above its level.' (witness gpt, lower_bound, substantiated).
    Reading: the same column model; a split replaces one column of height u+v by columns of heights u and v (each based at level
    0). Witness: a column of height 2d cut into d/2 and 3d/2. Before, N(t) = 1 on (0, 2d); after, N(t) = 2 on (0, d/2), 1 on
    (d/2, 3d/2), 0 on (3d/2, 2d). Parity is interchanged on (0, d/2), strictly below the cut level under either reading of 'its
    level' (d/2 or 3d/2). In general a split of u+v with u <= v changes N by +1 on (0, u) and -1 on (v, u+v); the check verifies
    both on the witness."""
    before = [2 * d]; after = [d / 2, 3 * d / 2]
    bps = sorted({Fr(0), d / 2, 3 * d / 2, 2 * d}); rows = []
    for lo, hi in zip(bps, bps[1:]):
        nb = sum(1 for h in before if h > lo); na = sum(1 for h in after if h > lo)
        rows.append((lo, hi, nb, na, nb % 2 != na % 2))
    flips = [(lo, hi) for lo, hi, nb, na, fl in rows if fl]
    flips_below = [(lo, hi) for lo, hi in flips if hi <= d / 2]
    general = [r[3] - r[2] for r in rows] == [1, 0, -1]
    ok = bool(flips_below) and general and flips == [(Fr(0), d / 2), (3 * d / 2, 2 * d)]
    kv = {"d": d, "before": before, "after": after, "levels": [(lo, hi, nb, na, fl) for lo, hi, nb, na, fl in rows],
          "parity_interchanged_on": flips, "interchanged_strictly_below_d_over_2": flips_below, "delta_N_is_plus1_0_minus1": general}
    lines = [f"column 2d = {fr(2 * d)} cut into d/2 = {fr(d / 2)} and 3d/2 = {fr(3 * d / 2)}",
             "level (lo,hi): N before -> N after, parity interchanged: " + "; ".join(f"({fr(lo)},{fr(hi)}): {nb}->{na}, {fl}" for lo, hi, nb, na, fl in rows),
             f"parity rows interchanged on {[(fr(a), fr(b)) for a, b in flips]}; below the cut level d/2: {[(fr(a), fr(b)) for a, b in flips_below]} (the quoted claim is false)"]
    return cert("p3-cut-parity", ["deedy-gpt-5.6-sol-final"], "L3.3", "a column 2d cut into d/2, 3d/2 interchanges the parity rows below the cut level",
                "'A cut can interchange the two parity rows only above its level.'", ok, kv, lines,
                f"column 2d -> d/2 + 3d/2: N 1->2 on (0,d/2): parity interchanged below the cut level (also on (3d/2,2d))")

def check_p3_strip_count(jmax=8):
    """p3-strip-count -- case deedy-gpt-5.6-sol-final (P3), ledger L3.3.
    Quote: 'adding the next column, whose 2^{j+1} strips consist of two identical copies of all preceding strips plus one parity
    interchange, preserves this alternative.' (witness claude, lower_bound, substantiated; also the graders' e1 objections).
    Reading: columns of heights d, 2d, ..., 2^j d divided into strips of height d; 'all preceding strips' number 1 + 2 + ... + 2^j =
    2^{j+1} - 1; the next column 2^{j+1} d has 2^{j+1} strips. Two copies of the preceding strips are 2^{j+2} - 2 strips and two
    copies plus one are 2^{j+2} - 1; neither equals 2^{j+1} for any j >= 1 (without the '+1' the counts agree only at j = 0)."""
    rows = []
    for j in range(0, jmax + 1):
        pre = 2 ** (j + 1) - 1; two = 2 * pre; two1 = two + 1; nxt = 2 ** (j + 1)
        rows.append({"j": j, "preceding_strips": pre, "two_copies": two, "two_copies_plus_one": two1, "next_column_strips": nxt})
    ok = all(r["two_copies_plus_one"] != r["next_column_strips"] for r in rows) and \
         all(r["two_copies"] != r["next_column_strips"] for r in rows if r["j"] >= 1) and rows[0]["two_copies"] == rows[0]["next_column_strips"]
    lines = ["j: preceding strips 2^(j+1)-1 | two copies | two copies + 1 | strips of the next column 2^(j+1)"] + \
            [f"{r['j']}: {r['preceding_strips']} | {r['two_copies']} | {r['two_copies_plus_one']} | {r['next_column_strips']}" for r in rows] + \
            ["'two copies plus one' never matches; 'two copies' matches only at j = 0"]
    return cert("p3-strip-count", ["deedy-gpt-5.6-sol-final"], "L3.3", "strip arithmetic of the induction step for j <= %d" % jmax,
                "the next column's 2^{j+1} strips consist of two identical copies of all preceding strips plus one", ok,
                {"rows": rows, "jmax": jmax}, lines, f"preceding strips 2^(j+1)-1; two copies+1 = 2^(j+2)-1 != 2^(j+1) for all j<={jmax} (two copies alone matches only j=0)")

def check_p3_kimi_order():
    """p3-kimi-order -- case kimi-k3-round4-t014 (P3), ledger L3.2.
    Quote: 'So the hypothesis of Lemma 4.1(b) holds, and some ordering of P cup N has chain value g <= S/(2^m-1).' (witnesses gpt
    and claude, upper_bound, substantiated). Reading: the text defines the chain value of a multiset by the DECREASING order,
    v(B) = |...||b_1-b_2|-b_3|...-b_r| with b_1 >= ... >= b_r, and its strategy processes the pieces in that order, while Lemma 4.1
    only supplies SOME ordering whose nested absolute difference is |Sigma P - Sigma N|. The nested absolute difference depends on
    the order. B = {10,9,8,7,5}: decreasing order gives 5, the order 10,8,7,9,5 gives 1; P = {8,7,5}, N = {10,9} have sums 20, 19 and
    no subset of B has sum strictly between them (integers), so Lemma 4.1(b) applies and promises 1 for some order.
    B = {8,7,6,5,4}: decreasing order gives 4, the order 8,6,5,7,4 gives 0; P = {8,7}, N = {6,5,4} have equal sums 15 (case (a)).
    The check also reports the minimum over all orderings and the checkers' further examples {8,5,2} and {10,6,4,2}."""
    def subset_sums(B):
        return {sum(c) for r in range(len(B) + 1) for c in itertools.combinations(B, r)}
    ex = []
    for B, order, P, N in [([10, 9, 8, 7, 5], [10, 8, 7, 9, 5], [8, 7, 5], [10, 9]), ([8, 7, 6, 5, 4], [8, 6, 5, 7, 4], [8, 7], [6, 5, 4])]:
        dec = nested_abs_diff(sorted(B, reverse=True)); alt = nested_abs_diff(order)
        g = Fr(sum(P) - sum(N)); lo, hi = min(sum(P), sum(N)), max(sum(P), sum(N))
        between = sorted(s for s in subset_sums(B) if lo < s < hi)
        mn = min(nested_abs_diff(p) for p in itertools.permutations(B))
        ex.append({"B": B, "decreasing_order_value": dec, "alternative_order": order, "alternative_order_value": alt, "P": P, "N": N,
                   "sigmaP_minus_sigmaN": g, "subset_sums_strictly_between": between, "lemma_4_1_case": "(b)" if g > 0 else "(a)",
                   "min_over_all_orderings": mn, "lemma_value_attained_by_alternative_order": alt == abs(g)})
    extra = {"{8,5,2}: decreasing vs (5,2,8)": (nested_abs_diff([8, 5, 2]), nested_abs_diff([5, 2, 8])),
             "{10,6,4,2}: decreasing vs (2,4,6,10)": (nested_abs_diff([10, 6, 4, 2]), nested_abs_diff([2, 4, 6, 10]))}
    ok = ex[0]["decreasing_order_value"] == 5 and ex[0]["alternative_order_value"] == 1 and not ex[0]["subset_sums_strictly_between"] and \
         ex[1]["decreasing_order_value"] == 4 and ex[1]["alternative_order_value"] == 0 and ex[1]["sigmaP_minus_sigmaN"] == 0 and \
         all(e["lemma_value_attained_by_alternative_order"] for e in ex) and extra["{8,5,2}: decreasing vs (5,2,8)"] == (1, 5)
    lines = [f"B = {e['B']}: decreasing order -> {e['decreasing_order_value']}; order {e['alternative_order']} -> {e['alternative_order_value']};"
             f" P = {e['P']}, N = {e['N']}, sum P - sum N = {e['sigmaP_minus_sigmaN']}, subset sums strictly between: {e['subset_sums_strictly_between'] or 'none'}"
             f" (Lemma 4.1{e['lemma_4_1_case']} applies); min over all orderings = {e['min_over_all_orderings']}" for e in ex] + \
            [f"checkers' extra examples: {k} -> {v[0]} vs {v[1]}" for k, v in extra.items()]
    return cert("p3-kimi-order", ["kimi-k3-round4-t014"], "L3.2", "nested absolute difference is order-dependent on the two quoted examples (decreasing order 5 vs 1; 4 vs 0)",
                "the chain value v(B), defined by the decreasing order, is at most the value that Lemma 4.1 attains for some ordering", ok,
                {"examples": ex, "checker_examples": extra}, lines,
                f"{{10,9,8,7,5}}: decreasing {ex[0]['decreasing_order_value']} vs 10,8,7,9,5 -> {ex[0]['alternative_order_value']}; {{8,7,6,5,4}}: decreasing {ex[1]['decreasing_order_value']} vs 8,6,5,7,4 -> {ex[1]['alternative_order_value']}")

# ============================================================================================ P5 certificates
def _z3_val(v):
    try: return Fr(v.as_fraction())
    except Exception:
        try: return v.as_decimal(12)
        except Exception: return str(v)

def check_p5_nemotron_z3():
    """p5-nemotron-z3 -- case p5-nemotron-2587b733-v2 (P5), ledger L5.1.
    Quote: 'For f(x) = x + c (c >= 0) the chain becomes sqrt((x^2 + (y+c)^2)/2) >= (x + y + 2c)/2 >= sqrt(x(y+c)).' followed by
    'Both inequalities are equivalent to (x - y - c)^2 >= 0' (witnesses gpt and claude, lower_bound, substantiated; grader gpt e1).
    Reading: with f(t) = t + c the problem's middle term (f(x)+y)/2 is (x+y+c)/2; the text displays (x+y+2c)/2.
    (1) The CORRECT chain is proved for all x, y, c > 0 with z3. Both sides of each inequality are positive, so each is equivalent
        to its squared polynomial form 2(x^2+(y+c)^2) >= (x+y+c)^2 resp. (x+y+c)^2 >= 4x(y+c); z3 (nonlinear real arithmetic)
        reports unsat for the negation of each under x, y, c > 0. sympy: both differences expand to (x-y-c)^2.
    (2) The WRITTEN chain fails: at x = y = c = 1 its left inequality reads sqrt(5/2) >= 2 (false; the true middle term is 3/2), and
        at c = 1, x = 2, y = 1 it reads 2 >= 5/2 (false, although (x-y-c)^2 = 0 >= 0 holds). z3 is asked for a violation of the
        written left inequality under x, y, c > 0 and returns one (sat; the model is re-checked exactly). sympy: the written left
        difference is (x-y)^2 - 4cx - 2c^2, not a square; the written right inequality is true ((x-y)^2 + 4cy + 4c^2 >= 0)."""
    try:
        import z3, sympy as sp
    except ImportError as e:
        return cert("p5-nemotron-z3", ["p5-nemotron-2587b733-v2"], "L5.1", "z3/sympy proof of the correct chain; violation of the written one",
                    "the displayed chain with middle term (x+y+2c)/2 holds and is equivalent to (x-y-c)^2 >= 0", False, {"error": str(e)}, [str(e)], f"ERROR {e}")
    x, y, c = z3.Reals("x y c"); pos = [x > 0, y > 0, c > 0]
    def status(*cons):
        s = z3.Solver(); s.add(*pos); s.add(*cons); r = s.check()
        return str(r), (s.model() if r == z3.sat else None)
    left_ok, _ = status(2 * (x * x + (y + c) * (y + c)) < (x + y + c) * (x + y + c))
    right_ok, _ = status((x + y + c) * (x + y + c) < 4 * x * (y + c))
    wl, model = status(2 * (x * x + (y + c) * (y + c)) < (x + y + 2 * c) * (x + y + 2 * c))
    wr, _ = status((x + y + 2 * c) * (x + y + 2 * c) < 4 * x * (y + c))
    mv = {str(v): _z3_val(model[v]) for v in (x, y, c)} if model is not None else {}
    recheck = None
    if all(isinstance(v, Fr) for v in mv.values()) and mv:
        X, Y, C = mv["x"], mv["y"], mv["c"]
        recheck = 2 * (X * X + (Y + C) ** 2) < (X + Y + 2 * C) ** 2
    mv_str = "(" + ", ".join(f"{k}={v}" for k, v in mv.items()) + ")"
    sx, sy, sc = sp.symbols("x y c", positive=True)
    left_diff = sp.expand(2 * (sx ** 2 + (sy + sc) ** 2) - (sx + sy + sc) ** 2)
    right_diff = sp.expand((sx + sy + sc) ** 2 - 4 * sx * (sy + sc))
    wleft_diff = sp.expand(2 * (sx ** 2 + (sy + sc) ** 2) - (sx + sy + 2 * sc) ** 2)
    wright_diff = sp.expand((sx + sy + 2 * sc) ** 2 - 4 * sx * (sy + sc))
    sq = sp.expand((sx - sy - sc) ** 2)
    sym_ok = left_diff == sq and right_diff == sq and wleft_diff == sp.expand((sx - sy) ** 2 - 4 * sc * sx - 2 * sc ** 2) \
             and wright_diff == sp.expand((sx - sy) ** 2 + 4 * sc * sy + 4 * sc ** 2)
    pts = {}
    for (X, Y, C) in [(Fr(1), Fr(1), Fr(1)), (Fr(2), Fr(1), Fr(1))]:
        l, mt, mw, r = p5_chain(X, Y, C)
        pts[f"x={X},y={Y},c={C}"] = {"left": round(l, 6), "true_middle": mt, "written_middle": mw, "right": round(r, 6),
                                     "written_left_ineq_holds": 2 * (X * X + (Y + C) ** 2) >= (X + Y + 2 * C) ** 2,
                                     "true_left_ineq_holds": 2 * (X * X + (Y + C) ** 2) >= (X + Y + C) ** 2}
    ok = left_ok == "unsat" and right_ok == "unsat" and wl == "sat" and sym_ok and (recheck is None or recheck) and \
         not pts["x=1,y=1,c=1"]["written_left_ineq_holds"] and not pts["x=2,y=1,c=1"]["written_left_ineq_holds"]
    kv = {"correct_chain_left_negation": left_ok, "correct_chain_right_negation": right_ok, "written_left_negation": wl,
          "written_right_negation": wr, "z3_violation_of_written_left": mv, "violation_rechecked_exactly": recheck,
          "sympy": {"2(x^2+(y+c)^2)-(x+y+c)^2": str(left_diff), "(x+y+c)^2-4x(y+c)": str(right_diff),
                    "2(x^2+(y+c)^2)-(x+y+2c)^2": str(wleft_diff), "(x+y+2c)^2-4x(y+c)": str(wright_diff), "both_correct_differences_equal_(x-y-c)^2": sym_ok},
          "sample_points": pts}
    lines = [f"correct chain, x,y,c>0: z3 negation of 2(x^2+(y+c)^2) >= (x+y+c)^2 -> {left_ok}; negation of (x+y+c)^2 >= 4x(y+c) -> {right_ok}",
             f"sympy: both differences = {left_diff} = (x-y-c)^2: {left_diff == sq and right_diff == sq}",
             f"written chain: left negation -> {wl}, z3 witness {mv_str} (exact recheck of the violation: {recheck}); right negation -> {wr} (the written right inequality is true)",
             f"sympy: written left difference = {wleft_diff} (not a square)",
             f"x=y=c=1: left {pts['x=1,y=1,c=1']['left']} >= written middle {pts['x=1,y=1,c=1']['written_middle']}? {pts['x=1,y=1,c=1']['written_left_ineq_holds']} (true middle 1.5);"
             f" x=2,y=1,c=1: left {pts['x=2,y=1,c=1']['left']} >= written middle {pts['x=2,y=1,c=1']['written_middle']}? {pts['x=2,y=1,c=1']['written_left_ineq_holds']}"]
    return cert("p5-nemotron-z3", ["p5-nemotron-2587b733-v2"], "L5.1", "z3 proves the chain with middle term (x+y+c)/2 for all x,y,c>0; the written (x+y+2c)/2 chain fails at (1,1,1)",
                "the displayed chain with middle term (x+y+2c)/2 holds for all x, y > 0 and both its inequalities are equivalent to (x-y-c)^2 >= 0", ok, kv, lines,
                f"correct chain: z3 {left_ok}/{right_ok}; written left ineq at (1,1,1): sqrt(5/2)>=2 false; z3 finds violation {mv_str}")

def check_p5_deepseek_dichotomy():
    """p5-deepseek-dichotomy -- cases p5-deepseek-v4-pro-main-t033 and -t038 (P5; identical on these lines), ledger L5.3.
    Quote: 'Thus V contains at most one positive number. Consequently, either (i) g == 0 (constant), which gives f(x)=x, a solution;
    or (ii) there is c>0 such that V subset {0, c} with both values attainable.' (witness gpt, upper_bound, substantiated; witness
    claude and both graders name the same step). Reading: V is the value set of g(x) = f(x) - x, and the text's only statement about
    the sign of g is g(x) > -x.
    (1) f(x) = x + 1 is a solution: g == 1 (sympy), V = {1}; both inequalities of the problem hold for all x, y > 0 (z3, the
        argument of p5-nemotron-z3 with c = 1) and at sample points (exact rational arithmetic on the squared forms).
    (2) V = {1} satisfies the premise (at most one positive value) but neither branch: (i) fails since g is not 0; (ii) fails
        since 0 is not attained ('both values attainable').
    (3) The inference is a non-sequitur on value sets: of the seven nonempty value sets drawn from {-1, 0, 1} every one satisfies the
        premise and five ({1}, {-1}, {-1,0}, {-1,1}, {-1,0,1}) violate the conclusion. {1} is realised by f(x) = x + 1; the sets with
        a negative value are excluded only by proving g >= 0 (ledger L5.3), which the text does not do."""
    try:
        import z3, sympy as sp
    except ImportError as e:
        return cert("p5-deepseek-dichotomy", ["p5-deepseek-v4-pro-main-t033", "p5-deepseek-v4-pro-main-t038"], "L5.3", "f(x)=x+1 vs the (i)/(ii) dichotomy",
                    "'V has at most one positive value' implies 'g == 0 or V subset {0,c} with both values attained'", False, {"error": str(e)}, [str(e)], f"ERROR {e}")
    sx = sp.symbols("x", positive=True); f = sx + 1; g = sp.simplify(f - sx)
    x, y = z3.Reals("x y")
    def status(con):
        s = z3.Solver(); s.add(x > 0, y > 0, con); return str(s.check())
    left = status(2 * (x * x + (y + 1) * (y + 1)) < (x + y + 1) * (x + y + 1))      # sqrt((x^2+f(y)^2)/2) >= (f(x)+y)/2, squared
    right = status((x + y + 1) * (x + y + 1) < 4 * x * (y + 1))                       # (f(x)+y)/2 >= sqrt(x f(y)), squared
    samples = [(Fr(1), Fr(1)), (Fr(2), Fr(1)), (Fr(1), Fr(2)), (Fr(1, 2), Fr(3)), (Fr(5), Fr(1, 3)), (Fr(7, 3), Fr(7, 3))]
    sample_ok = all(2 * (X * X + (Y + 1) ** 2) >= (X + Y + 1) ** 2 and (X + Y + 1) ** 2 >= 4 * X * (Y + 1) for X, Y in samples)
    V = {Fr(X) + 1 - Fr(X) for X, _ in samples}
    premise = sum(1 for v in V if v > 0) <= 1
    branch_i = V == {Fr(0)}
    branch_ii = any(V <= {Fr(0), cc} and {Fr(0), cc} <= V for cc in V if cc > 0)
    table = []
    for r in range(1, 4):
        for comb in itertools.combinations([-1, 0, 1], r):
            Vs = set(comb); prem = sum(1 for v in Vs if v > 0) <= 1
            concl = Vs == {0} or any(Vs <= {0, cc} and {0, cc} <= Vs for cc in Vs if cc > 0)
            table.append({"V": sorted(Vs), "premise": prem, "conclusion": concl})
    violators = [t["V"] for t in table if t["premise"] and not t["conclusion"]]
    ok = g == 1 and left == "unsat" and right == "unsat" and sample_ok and V == {Fr(1)} and premise and not branch_i and not branch_ii \
         and {tuple(v) for v in violators} == {(1,), (-1,), (-1, 0), (-1, 1), (-1, 0, 1)} and all(t["premise"] for t in table)
    kv = {"f": "x + 1", "g_symbolic": str(g), "z3_left_inequality_negation": left, "z3_right_inequality_negation": right,
          "sample_points_hold_exactly": sample_ok, "samples": samples, "V": V, "premise_at_most_one_positive": premise,
          "branch_i_g_identically_0": branch_i, "branch_ii_V_subset_0_c_both_attained": branch_ii,
          "value_sets_from_{-1,0,1}": table, "premise_true_conclusion_false": violators}
    lines = [f"f(x) = x + 1: g = f - x = {g} (sympy); V = {sorted(V)}",
             f"both inequalities hold for all x,y>0: z3 negations -> {left}, {right}; exact check at {len(samples)} sample points: {sample_ok}",
             f"premise 'V has at most one positive value': {premise}; branch (i) g == 0: {branch_i}; branch (ii) V subset {{0,c}} with both attained: {branch_ii}",
             f"value sets from {{-1,0,1}} satisfying the premise but not the conclusion: {violators} (those with -1 need L5.3 to be excluded; the text does not prove g >= 0)"]
    return cert("p5-deepseek-dichotomy", ["p5-deepseek-v4-pro-main-t033", "p5-deepseek-v4-pro-main-t038"], "L5.3",
                "f(x)=x+1 is a solution with V={1}: premise holds, neither branch (i) nor (ii) holds; negative values never excluded",
                "'V contains at most one positive number' implies 'either g == 0 or V subset {0,c} with both values attainable'", ok, kv, lines,
                f"f=x+1: z3 both ineqs hold; V={{1}}: branch (i) {branch_i}, branch (ii) {branch_ii}; premise-true/conclusion-false value sets: {len(violators)}")

def check_p5_deepseek_typo():
    """p5-deepseek-typo -- cases p5-deepseek-v4-pro-main-t033 and -t038 (P5); a harmless display error inside the necessity argument
    (no ledger statement; checkers: fatal no). Quote: 'A(x,y) &= (x-y)^2 + 4cx + 2c^2 >= 0 (always true)' (grader claude e1,
    substantiated). Reading: the text defines A(x,y) := 2x^2 + 2(y+b)^2 - (x+y+a)^2 and B(x,y) := (x+y+a)^2 - 4x(y+b), expands
    A(x,y) = (x-y)^2 - a^2 - 2a(x+y) + 4by + 2b^2 and B(x,y) = (x-y)^2 + a^2 + 2a(x+y) - 4bx, and states A + B = 2(x-y-b)^2 (its (5));
    the quoted line is the specialisation a = 0, b = c. sympy: the general expansions and (5) are correct; specialising A gives
    (x-y)^2 + 4cy + 2c^2; the displayed expression differs from it by 4c(x-y) (x=1, y=2, c=1: 11 versus 7). Both expressions are >= 0
    for x, y, c > 0, so '(always true)' is unaffected, and the neighbouring display B(x,y) = (x-y)^2 - 4cx is correct."""
    try:
        import sympy as sp
    except ImportError as e:
        return cert("p5-deepseek-typo", ["p5-deepseek-v4-pro-main-t033", "p5-deepseek-v4-pro-main-t038"], "none", "4cx versus 4cy",
                    "A(x,y) specialised to a=0, b=c equals (x-y)^2 + 4cx + 2c^2", False, {"error": str(e)}, [str(e)], f"ERROR {e}")
    x, y, a, b, c = sp.symbols("x y a b c", positive=True)
    A = 2 * x ** 2 + 2 * (y + b) ** 2 - (x + y + a) ** 2
    B = (x + y + a) ** 2 - 4 * x * (y + b)
    A_text = (x - y) ** 2 - a ** 2 - 2 * a * (x + y) + 4 * b * y + 2 * b ** 2
    B_text = (x - y) ** 2 + a ** 2 + 2 * a * (x + y) - 4 * b * x
    gen_ok = sp.expand(A - A_text) == 0 and sp.expand(B - B_text) == 0 and sp.expand(A + B - 2 * (x - y - b) ** 2) == 0
    A_spec = sp.expand(A.subs({a: 0, b: c})); B_spec = sp.expand(B.subs({a: 0, b: c}))
    displayed = sp.expand((x - y) ** 2 + 4 * c * x + 2 * c ** 2); correct = sp.expand((x - y) ** 2 + 4 * c * y + 2 * c ** 2)
    diff = sp.factor(displayed - A_spec)
    B_disp_ok = B_spec == sp.expand((x - y) ** 2 - 4 * c * x)
    pt = {x: 1, y: 2, c: 1}
    val_true, val_disp = int(A_spec.subs(pt)), int(displayed.subs(pt))
    ok = gen_ok and A_spec == correct and A_spec != displayed and sp.expand(diff - 4 * c * (x - y)) == 0 and val_true == 11 and val_disp == 7 and B_disp_ok
    kv = {"A_definition": "2x^2 + 2(y+b)^2 - (x+y+a)^2", "text_general_expansions_and_(5)_correct": gen_ok,
          "A_at_a=0,b=c": str(A_spec), "displayed": str(displayed), "displayed_minus_correct": str(diff),
          "value_at_x=1,y=2,c=1": {"correct": val_true, "displayed": val_disp}, "B_display_(x-y)^2-4cx_correct": B_disp_ok,
          "both_nonnegative_for_positive_x_y_c": "yes: (x-y)^2 + 4c*x + 2c^2 and (x-y)^2 + 4c*y + 2c^2 are sums of nonnegative terms"}
    lines = [f"general expansions of A, B and identity (5) as written in the text: {gen_ok}",
             f"A at a=0, b=c: {A_spec}; displayed: {displayed}; displayed - correct = {diff}",
             f"x=1, y=2, c=1: correct {val_true}, displayed {val_disp}; both >= 0 for positive variables (harmless); B display (x-y)^2 - 4cx correct: {B_disp_ok}"]
    return cert("p5-deepseek-typo", ["p5-deepseek-v4-pro-main-t033", "p5-deepseek-v4-pro-main-t038"], "none",
                "sympy: A(x,y) at a=0,b=c is (x-y)^2+4cy+2c^2, the display has 4cx (harmless: both nonnegative)",
                "the specialised display A(x,y) = (x-y)^2 + 4cx + 2c^2 is the expansion of the text's A at a=0, b=c", ok, kv, lines,
                f"A(a=0,b=c) = {A_spec} vs displayed 4cx: difference {diff}; at (1,2,1): {val_true} vs {val_disp}; harmless (both >= 0)")

# ============================================================================================ P6 certificates
def check_p6_transversals(n=6):
    """p6-transversals -- cases p6-gpt-5.6-sol-main-t009 and p6-deedy-gpt-5.6-sol-final (P6), ledger L6.2 (the ledger's own check).
    Reading: the texts' finiteness comes from the lemma 'a pairwise-intersecting family of nonempty finite sets has finitely many
    minimal finite transversals' (in the form: finitely many B_1..B_s such that a finite X is a transversal iff it contains some
    B_j; each B_j is then a transversal, so every inclusion-minimal transversal equals some B_j). Family F_k = {x_1..x_k, y_k},
    k = 1..n: pairwise intersecting via x_1; T_k = {y_1..y_{k-1}, x_k} is a minimal finite transversal for each k, and the T_k are
    distinct, so there are infinitely many as n grows (see p6_family for the argument; the check verifies it for k <= n)."""
    pw, out = p6_family(n)
    ok = pw and all(h and m for _, _, h, m in out) and len({tuple(T) for _, T, _, _ in out}) == n
    lines = [f"family F_k = {{x_1..x_k, y_k}}, k=1..{n}: pairwise intersecting = {pw}"] + \
            [f"  T_{k} = {T}: transversal = {h}, minimal = {m}" for k, T, h, m in out] + \
            [f"{n} distinct minimal finite transversals for n = {n}; one per k, so infinitely many as n grows"]
    return cert("p6-transversals", ["p6-gpt-5.6-sol-main-t009", "p6-deedy-gpt-5.6-sol-final"], "L6.2",
                f"F_k = {{x_1..x_k, y_k}}: {n} distinct minimal finite transversals T_k for k <= {n}",
                "a pairwise-intersecting family of nonempty finite sets has finitely many inclusion-minimal finite transversals", ok,
                {"n": n, "pairwise_intersecting": pw, "T_k": [(k, T, h, m) for k, T, h, m in out]}, lines,
                f"F_k={{x_1..x_k,y_k}}, k<={n}: pairwise intersecting {pw}; {n} distinct minimal transversals T_k (all verified)")

def check_p6_gpt_transversals(K=8):
    """p6-gpt-transversals -- cases p6-gpt-5.6-sol-main-t009 and p6-deedy-gpt-5.6-sol-final (P6), ledger L6.2.
    Quotes: 'If every two members of F intersect, then there are finitely many nonempty finite sets B_1,...,B_s subset P such that...'
    (t009; graders gpt e0 and claude e0) and 'If a family of finite sets is pairwise intersecting and has a member C of size r,
    then it has only finitely many inclusion-minimal finite transversals.' (final; graders gpt e0 and claude e0); all substantiated.
    Reading: both statements are made for every pairwise-intersecting family of nonempty finite sets; if the first held, each B_j
    would be a transversal and every inclusion-minimal transversal would equal some B_j, so at most s exist. The graders' families:
      F_k = {x_0,...,x_k, y_k} (k >= 0):        T_n = {y_0,...,y_{n-1}, x_n}  (grader gpt e0 on t009);
      E_i = {a_1,...,a_i, b_i} (i >= 1):        T_k = {b_1,...,b_{k-1}, a_k}  (grader claude e0 on the final; member E_1 has size 2);
      G_i = {c, a_i, b_1,...,b_{i-1}} (i >= 1): B_n = {a_1,...,a_n, b_n}      (grader gpt e0 on the final; member G_1 has size 2).
    For each family truncated at index K the check verifies pairwise intersection, that each listed set is a transversal, that
    deleting any of its elements leaves a member unhit, and distinctness. Each verification involves only members of index <= K
    (F, E) or <= K+1 (G), which is why the finite computation certifies minimality for the full infinite family. For K <= 4 all
    inclusion-minimal transversals of the truncation are also enumerated by brute force."""
    fams = {
        "F_k={x_0..x_k,y_k}": (lambda K: [frozenset([f"x{i}" for i in range(0, k + 1)] + [f"y{k}"]) for k in range(0, K + 1)],
                              lambda K: [(n, frozenset([f"y{j}" for j in range(0, n)] + [f"x{n}"])) for n in range(0, K + 1)]),
        "E_i={a_1..a_i,b_i}": (lambda K: [frozenset([f"a{j}" for j in range(1, i + 1)] + [f"b{i}"]) for i in range(1, K + 1)],
                              lambda K: [(k, frozenset([f"b{j}" for j in range(1, k)] + [f"a{k}"])) for k in range(1, K + 1)]),
        "G_i={c,a_i,b_1..b_{i-1}}": (lambda K: [frozenset(["c", f"a{i}"] + [f"b{j}" for j in range(1, i)]) for i in range(1, K + 1)],
                                    lambda K: [(n, frozenset([f"a{j}" for j in range(1, n + 1)] + [f"b{n}"])) for n in range(1, K)]),
    }
    res = {}; ok = True; lines = []
    for name, (mk, mkT) in fams.items():
        fam = mk(K); Ts = mkT(K)
        pw = all(fam[i] & fam[j] for i in range(len(fam)) for j in range(i + 1, len(fam)))
        rows = [(n, T, is_transversal(T, fam), is_minimal_transversal(T, fam)) for n, T in Ts]
        distinct = len({T for _, T in Ts}) == len(Ts)
        size2 = min(len(f) for f in fam)
        brute = {k: len(minimal_transversals(mk(k))) for k in range(1, 5)}
        contained = all(T in set(minimal_transversals(mk(min(K, 4)))) for n, T in Ts if (n <= 4 if name.startswith("F") or name.startswith("E") else n <= 3))
        good = pw and all(h and m for _, _, h, m in rows) and distinct and size2 == 2
        ok = ok and good
        res[name] = {"K": K, "pairwise_intersecting": pw, "smallest_member_size": size2, "listed_transversals": [(n, sorted(T, key=_skey), h, m) for n, T, h, m in rows],
                     "all_listed_are_minimal_transversals": all(h and m for _, _, h, m in rows), "distinct": distinct, "count": len(rows),
                     "brute_force_count_of_minimal_transversals_of_truncation_K=1..4": brute, "listed_ones_found_by_brute_force": contained}
        lines.append(f"{name}, K={K}: pairwise intersecting {pw}, smallest member size {size2}; {len(rows)} listed sets, all minimal transversals: "
                     f"{all(h and m for _, _, h, m in rows)}, distinct: {distinct}; brute-force count of minimal transversals of the truncation K=1..4: {brute}")
        lines.append("   " + "; ".join(f"{fset(T)}" for _, T, _, _ in rows))
    total = sum(r["count"] for r in res.values())
    return cert("p6-gpt-transversals", ["p6-gpt-5.6-sol-main-t009", "p6-deedy-gpt-5.6-sol-final"], "L6.2",
                f"the graders' three families (F_k with x_0, E_i, G_i) have {K}, {K}, {K - 1} distinct minimal finite transversals for K={K}",
                "a pairwise-intersecting family of nonempty finite sets (with a member of size r) has finitely many inclusion-minimal finite transversals", ok,
                res, lines, f"F_k/E_i/G_i truncated at K={K}: pairwise intersecting; {total} listed minimal transversals verified (grow linearly with K)")

def check_p6_gpt_recursion():
    """p6-gpt-recursion -- case p6-gpt-5.6-sol-main-t009 (P6), ledger L6.2.
    Quotes: 'Every transversal X of F meets C, since C itself is a member of F whenever this assertion is applied below; more
    generally, for the inductive assertion we only need to restrict attention to transversals meeting C.' and 'Conversely, a
    transversal X meeting C contains some c in C and traverses F_c, so it contains a corresponding D_{c,k}.' (witnesses gpt and
    claude, lower_bound; graders' e1 objections; all substantiated). Reading: the text's induction on |C| (C a finite transversal
    of the pairwise-intersecting family F) forms, for each c in C, the family F_c of members not containing c, applies the
    induction hypothesis to (F_c, C minus {c}) to get lists D_{c,k}, and outputs the sets {c} u D_{c,k} as a characterisation of
    all transversals; but the assertion proved covers only transversals meeting the current C, and C minus {c} need not be a member
    of F_c, so transversals of F_c avoiding C minus {c} are never characterised. The check runs the induction literally
    (restricted_list) and compares its output with the inclusion-minimal transversals found by brute force, on the instances in
    RESULTS.md: F = {{1,2},{2,3}} with C = {1,2} (list {{1,2},{2}} misses {1,3}) and with C = {2} (witness claude);
    F = {{1,2},{2,3},{2,4}}, C = {1,2} (misses {1,3,4}); F = {{1,2},{1,3},{2,3}}, C = {1,2} (misses {1,3} and {2,3}). For each
    instance the failing recursive call is exhibited: c, F_c, whether C minus {c} is a member of F_c, and a transversal of F_c
    disjoint from C minus {c} that the restricted list does not cover."""
    instances = [("witness gpt / checkers", [{1, 2}, {2, 3}], {1, 2}), ("witness claude", [{1, 2}, {2, 3}], {2}),
                 ("grader claude e1", [{1, 2}, {2, 3}, {2, 4}], {1, 2}), ("checker claude (grader gpt e1)", [{1, 2}, {1, 3}, {2, 3}], {1, 2})]
    res = []; ok = True; lines = []
    for label, F, C in instances:
        F = [frozenset(f) for f in F]; C = frozenset(C)
        assert is_transversal(C, F)
        lst = restricted_list(F, C); mins = minimal_transversals(F)
        missed = [T for T in mins if not any(D <= T for D in lst)]
        diag = None
        for c in sorted(C):
            Fc = [f for f in F if c not in f]; Cc = C - {c}
            if not Fc: continue
            sub = restricted_list(Fc, Cc)
            uncovered = [T for T in minimal_transversals(Fc) if not any(D <= T for D in sub)]
            if uncovered:
                diag = {"c": c, "F_c": [sorted(f) for f in Fc], "C_minus_c": sorted(Cc), "C_minus_c_is_member_of_F_c": Cc in set(Fc),
                        "restricted_list_for_(F_c,C_minus_c)": [sorted(D) for D in sub], "transversal_of_F_c_not_covered": sorted(uncovered[0]),
                        "it_meets_C_minus_c": bool(uncovered[0] & Cc)}
                break
        # where the restriction 'transversals meeting C' fails: in a recursive call (C\{c} not a member of F_c, a transversal of F_c
        # avoids it) or, when C itself is not a member of F, already at the top level (a transversal of F avoids C)
        top_level = None
        if C not in set(F):
            avoid = [T for T in mins if not (T & C)]
            top_level = {"C_is_member_of_F": False, "transversal_of_F_disjoint_from_C": sorted(avoid[0]) if avoid else None}
        recursive_fail = diag is not None and not diag["C_minus_c_is_member_of_F_c"] and not diag["it_meets_C_minus_c"]
        top_fail = top_level is not None and top_level["transversal_of_F_disjoint_from_C"] is not None
        good = bool(missed) and all(is_transversal(D, F) for D in lst) and (recursive_fail or top_fail)
        ok = ok and good
        res.append({"instance": label, "F": [sorted(f) for f in F], "C": sorted(C), "C_is_member_of_F": C in set(F), "text_list": [sorted(D) for D in lst],
                    "minimal_transversals": [sorted(T) for T in mins], "missed_by_the_list": [sorted(T) for T in missed], "failing_recursive_call": diag,
                    "top_level_failure": top_level})
        lines.append(f"{label}: F = {[sorted(f) for f in F]}, C = {sorted(C)} (member of F: {C in set(F)}): text's list {[sorted(D) for D in lst]};"
                     f" minimal transversals {[sorted(T) for T in mins]}; missed: {[sorted(T) for T in missed]}")
        if diag:
            lines.append(f"   failing call c={diag['c']}: F_c = {diag['F_c']}, C\\{{c}} = {diag['C_minus_c']} (member of F_c: {diag['C_minus_c_is_member_of_F_c']});"
                         f" transversal {diag['transversal_of_F_c_not_covered']} of F_c is disjoint from C\\{{c}} and is not covered by the restricted list {diag['restricted_list_for_(F_c,C_minus_c)']}")
        if top_level:
            lines.append(f"   top level: C = {sorted(C)} is not a member of F, and the transversal {top_level['transversal_of_F_disjoint_from_C']} of F is disjoint from C,"
                         f" so 'every transversal of F meets C' already fails here")
    return cert("p6-gpt-recursion", ["p6-gpt-5.6-sol-main-t009"], "L6.2", "the text's induction, run literally, outputs lists that miss genuine transversals on the four quoted instances",
                "a finite X traverses F iff X contains one of the sets {c} u D_{c,k} produced by the induction restricted to transversals meeting C", ok,
                {"instances": res}, lines, "F={{1,2},{2,3}}, C={1,2}: list {{1,2},{2}} misses {1,3}; C\\{1}={2} not a member of F_1; 4/4 instances miss a transversal")

def check_p6_kimi_infinite(N=8):
    """p6-kimi-infinite-transversal -- case p6-kimi-k3-round2-t007 (P6), ledger L6.2.
    Quote: 'Let T be a minimal (under inclusion) transversal of C. For each i, a_i in S_infty is a multiple of some pi(t) with
    t in C; then t subset supp(a_i), and T meeting t implies T meets supp(a_i). Hence pi(T) in S_infty' (witnesses gpt and claude,
    lower_bound, substantiated; both graders name the same step). Reading: pi(s) = prod_{p in s} p is defined by the text only for
    FINITE sets s of primes, Claim 3.2 takes an arbitrary minimal transversal T, and its premises (T meets every member) do not make
    T finite. Witness (witness gpt): for distinct odd primes x_1, x_2, ... the family C = {{2, x_n} : n >= 1} is a
    pairwise-intersecting antichain of finite sets with the INFINITE minimal transversal T = {x_n : n >= 1}: T meets every member,
    and deleting x_k leaves {2, x_k} unhit. No finite subset of T is a transversal: a finite F subset T has a largest index M and
    misses {2, x_{M+1}}. The check uses symbols x1..xN for the distinct odd primes and, for the truncation n <= N (N up to 8),
    verifies pairwise intersection, the antichain property, that {x_1..x_N} hits every member, that each single deletion leaves
    {2, x_k} unhit, and that every one of the 2^N subsets of {x_1..x_N} misses {2, x_{N+1}}. ({2} is a finite minimal transversal
    and the family is not self-dual, so the witness shows the finiteness step of Claim 3.2 is not automatic; it is not a
    counterexample to the Step-4 theorem, whose hypothesis (iii) this family fails.)"""
    rows = []; ok = True
    for n in range(1, N + 1):
        fam = [frozenset({"2", f"x{i}"}) for i in range(1, n + 1)]
        T = frozenset(f"x{i}" for i in range(1, n + 1))
        pw = all(a & b for a, b in itertools.combinations(fam, 2))
        antichain = all(not (a < b) for a in fam for b in fam)
        hits = is_transversal(T, fam)
        deletions = all(not (T - {f"x{k}"}) & frozenset({"2", f"x{k}"}) for k in range(1, n + 1))
        nxt = frozenset({"2", f"x{n + 1}"})
        no_finite = all(not (frozenset(sub) & nxt) for r in range(0, n + 1) for sub in itertools.combinations(sorted(T, key=_skey), r))
        two_minimal = is_minimal_transversal(frozenset({"2"}), fam); self_dual = frozenset({"2"}) in set(fam)
        good = pw and antichain and hits and deletions and no_finite and two_minimal and not self_dual
        ok = ok and good
        rows.append({"N": n, "pairwise_intersecting": pw, "antichain": antichain, "T=x1..xN_hits_all": hits, "each_deletion_of_x_k_leaves_{2,x_k}_unhit": deletions,
                     "all_2^N_subsets_of_T_miss_{2,x_{N+1}}": no_finite, "subsets_checked": 2 ** n, "{2}_is_a_finite_minimal_transversal": two_minimal, "{2}_is_a_member": self_dual})
    lines = [f"C = {{{{2, x_n}}}}, symbols x1..x{N} for distinct odd primes; T = {{x_1..x_N}}"] + \
            [f"N={r['N']}: pairwise {r['pairwise_intersecting']}, antichain {r['antichain']}, T hits all {r['T=x1..xN_hits_all']}, deleting any x_k leaves {{2,x_k}} unhit {r['each_deletion_of_x_k_leaves_{2,x_k}_unhit']},"
             f" all {r['subsets_checked']} subsets of T miss {{2,x_{r['N'] + 1}}} {r['all_2^N_subsets_of_T_miss_{2,x_{N+1}}']}" for r in rows] + \
            ["so {x_n : n >= 1} is an infinite minimal transversal with no finite sub-transversal; {2} is a finite minimal transversal not in C (family not self-dual)"]
    return cert("p6-kimi-infinite-transversal", ["p6-kimi-k3-round2-t007"], "L6.2",
                f"{{{{2,x_n}}}}: {{x_1..x_N}} is a minimal transversal of the truncation whose every subset misses {{2,x_{{N+1}}}}, N<={N}",
                "every inclusion-minimal transversal T of the intersecting antichain C is finite (so that pi(T) is defined)", ok,
                {"rows": rows, "N_max": N}, lines, f"{{{{2,x_n}}}}: T={{x_1..x_N}} minimal transversal for N<={N}; every subset of T misses {{2,x_{{N+1}}}}; infinite minimal transversal exists")

# ============================================================================================ P1 certificate
def check_p1_board(board=(2, 3)):
    """p1-board -- case p1-glm52-2ede1c6b-v1 (P1), ledger L1.2. This certificate REFUTES an earlier counterexample; no v6 proposer or
    grader objected to the text. Reading: a move replaces m, n > 1 by gcd(m, n) and lcm(m, n)/gcd(m, n), i.e. on p-adic valuations
    (x, y) -> (min(x, y), |x - y|). The text states that for each prime p the gcd of all valuations on the board,
    G_p = gcd(v_p(a_1), ..., v_p(a_N)) with the convention gcd(k, 0) = k, is invariant, hence M = prod_p p^{G_p}. GPT's earlier
    S=1 rating took the board {2, 3} as a counterexample; but gcd(1, 0) = 1 for p = 2 and gcd(0, 1) = 1 for p = 3, so the formula
    predicts M = 6, and the only play 2, 3 -> 1, 6 leaves 6. The check enumerates every play on the board, collects the terminal
    survivors, and compares them with M (also on a few other boards as receipts)."""
    board = tuple(board)
    seen, finals = p1_moves(board); primes = primes_dividing(board)
    vals = {p: [vp(v, p) for v in board] for p in primes}; gcds = {p: reduce(gcd, vals[p]) for p in primes}
    M = p1_M(board)
    survivors = sorted({max(b) for b in finals}); one_survivor = all(sum(1 for v in b if v > 1) == 1 for b in finals)
    receipts = {}
    for other in [(4, 6, 9), (12, 18, 8), (2, 4, 8, 3)]:
        _, fo = p1_moves(other); receipts[str(list(other))] = {"M": p1_M(other), "survivors": sorted({max(b) for b in fo}), "terminal_boards": len(fo)}
    ok = survivors == [M] and one_survivor and gcd(1, 0) == 1 and all(r["survivors"] == [r["M"]] for r in receipts.values())
    tail = "earlier {2,3} counterexample refuted" if tuple(sorted(board)) == (2, 3) else "formula confirmed on every play"
    kv = {"board": list(board), "reachable_states": len(seen), "terminal_boards": [list(b) for b in sorted(finals)], "primes": primes,
          "valuations": {str(p): v for p, v in vals.items()}, "valuation_gcds": {str(p): g for p, g in gcds.items()}, "M_formula": M, "survivors": survivors,
          "note": "gcd(1,0) = 1 (Python's math.gcd and the text's convention): the earlier {2,3} counterexample fails", "receipts_other_boards": receipts}
    lines = [f"board {list(board)}: reachable states {len(seen)}, terminal boards {[list(b) for b in sorted(finals)]}"] + \
            [f"  prime {p}: valuations {vals[p]}, gcd = {gcds[p]}" for p in primes] + \
            [f"  M = prod p^gcd = {M}; survivors of all plays: {survivors}; gcd(1,0) = {gcd(1, 0)}, so the earlier {{2,3}} counterexample fails",
             "  receipts on other boards: " + "; ".join(f"{k}: M={v['M']}, survivors {v['survivors']}" for k, v in receipts.items())]
    return cert("p1-board", ["p1-glm52-2ede1c6b-v1"], "L1.2", f"board {list(board)}: every play ends with the survivor M = prod p^gcd v_p (gcd(1,0)=1)",
                "the earlier counterexample: on the board {2,3} the valuation-gcd formula for M fails", ok, kv, lines,
                f"board {list(board)}: valuation gcds {gcds} (gcd(1,0)=1), M = {M}, survivors {survivors}: {tail}")

# ============================================================================================ --all: run, receipts, files
ALL_CHECKS = [check_p3_muse, check_p3_deepseek, check_p3_grok, check_p3_two_columns, check_p3_cut_parity, check_p3_strip_count,
              check_p3_kimi_order, check_p5_nemotron_z3, check_p5_deepseek_dichotomy, check_p5_deepseek_typo,
              check_p6_transversals, check_p6_gpt_transversals, check_p6_gpt_recursion, check_p6_kimi_infinite, check_p1_board]
CHECK_COMMANDS = {"p3-muse": "p3-muse", "p3-deepseek": "p3-deepseek", "p3-grok": "p3-grok", "p3-two-columns": "p3-two-columns",
                  "p3-cut-parity": "p3-cut-parity", "p3-strip-count": "p3-strip-count --jmax 8", "p3-kimi-order": "p3-kimi-order",
                  "p5-nemotron-z3": "p5-nemotron-z3", "p5-deepseek-dichotomy": "p5-deepseek-dichotomy", "p5-deepseek-typo": "p5-deepseek-typo",
                  "p6-transversals": "p6-transversals --n 6", "p6-gpt-transversals": "p6-gpt-transversals --k 8", "p6-gpt-recursion": "p6-gpt-recursion",
                  "p6-kimi-infinite-transversal": "p6-kimi-infinite-transversal --N 8", "p1-board": "p1-board --board 2 3"}

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()

def versions():
    v = {"python": sys.version.split()[0]}
    try: import sympy; v["sympy"] = sympy.__version__
    except ImportError: v["sympy"] = None
    try: import z3; v["z3"] = z3.get_version_string()
    except ImportError: v["z3"] = None
    return v

def text_receipts(cases_path):
    """Cross-check the embedded case table against cases.json and recompute the text hashes when the texts are present."""
    out = {"cases_json": cases_path, "found": bool(cases_path and os.path.exists(cases_path)), "texts": {}}
    table = {}
    if out["found"]:
        with open(cases_path) as fh: data = json.load(fh)
        table = {c["id"]: c for c in data.get("cases", [])}
    for cid, (prob, sha) in CASES.items():
        rec = {"problem": prob, "sha256": sha}
        if table:
            c = table.get(cid)
            rec["in_cases_json"] = c is not None
            rec["sha256_matches_cases_json"] = (c is not None and c.get("sha256") == sha)
            path = c.get("path") if c else None
            if path and os.path.exists(path):
                rec["text_file"] = path; rec["recomputed_sha256_matches"] = sha256_file(path) == sha
            else:
                rec["text_file"] = path; rec["recomputed_sha256_matches"] = None
        out["texts"][cid] = rec
    return out

def write_outputs(certs, meta, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    jpath = os.path.join(out_dir, "certificates.json"); mpath = os.path.join(out_dir, "CERTIFICATES.md")
    payload = dict(meta)
    payload["certificates"] = [J({k: v for k, v in c.items() if k != "_lines"}) for c in certs]
    with open(jpath, "w") as fh: json.dump(payload, fh, indent=1); fh.write("\n")
    n_pass = sum(c["result"] == "PASS" for c in certs)
    md = [f"# Executable certificates for the v6 witness experiment (post hoc; no model in the loop)", "",
          f"Generated {meta['generated_utc']} by `python3 scripts/witness_checks.py --all` "
          f"(Python {meta['python']}, sympy {meta['sympy']}, z3 {meta['z3']}). {n_pass}/{len(certs)} certificates PASS.",
          "",
          "Reproduce from the repository root with exactly: `python3 scripts/witness_checks.py --all` (writes this file and "
          "`certificates.json` into `artifacts/witness_discovery/`). From a flat bundle containing only the script: "
          "`python3 witness_checks.py --all --out-dir .` (add `--cases cases.json` to cross-check the text hashes). Each check is also "
          "a subcommand printing its full output (last column). PASS means the computation confirms the objection as stated in "
          "RESULTS.md (for p1-board: refutes the earlier counterexample); each subcommand's docstring (`python3 scripts/witness_checks.py "
          "<check> --help`, or the source) states the reading of the text it encodes, the anchored quote and the case id.",
          "",
          "| check | case(s) | ledger statement | what is checked | result | command |", "|---|---|---|---|---|---|"]
    for c in certs:
        md.append(f"| `{c['check']}` | {', '.join(c['case_ids'])} | {LEDGER[c['ledger_key']]} "
                  f"| {c['what_is_checked']} | **{c['result']}** | `{CHECK_COMMANDS.get(c['check'], c['check'])}` |")
    md += ["", "## Key values (one line per check, as printed by `--all`)", ""]
    md += [f"- `{c['check']}`: {c['summary']}" for c in certs]
    md += ["", "## Texts", "", "Each certificate names the case id(s) and the sha256 of the text (from `cases.json`). At generation time: "]
    for cid, r in meta["text_receipts"]["texts"].items():
        md.append(f"- {cid} (P{r['problem']}): sha256 `{r['sha256'][:16]}...`; in cases.json: {r.get('in_cases_json', 'n/a')}; "
                  f"recomputed from the text file: {r.get('recomputed_sha256_matches', 'n/a')}")
    md += ["", "## Substantiated objections not encoded (no finite witness object)", ""]
    md += [f"- {cid}: {what}. Reason: {why}" for cid, what, why in NOT_ENCODED]
    md += ["", "Generic tools used by the certificates: `p3` (rational-grid search of Xiang replies; its minimum is an upper bound on Liu's "
           "guarantee, one reply refutes a claimed guarantee above it), `p3-odd-rank` (exact claiming value, brute-force minimax), "
           "`p3-nested`, `p5-chain`, `p6-transversals`, `p1-board`.", ""]
    with open(mpath, "w") as fh: fh.write("\n".join(md))
    return jpath, mpath

def run_all(args):
    certs = []
    for fn in ALL_CHECKS:
        try:
            c = fn()
        except Exception as e:  # a crashing check is a failing certificate, never a silent omission
            name = fn.__name__.replace("check_", "").replace("_", "-")
            c = {"check": name, "case_ids": [], "ledger_statement": "n/a", "ledger_key": "none", "what_is_checked": "n/a", "claim_checked": "n/a",
                 "result": "FAIL", "summary": f"ERROR {type(e).__name__}: {e}", "key_values": {}, "sha256_of_texts": {}, "_lines": []}
        certs.append(c)
        print(f"{c['result']:4s} {c['check']:29s} {c['summary']}")
    v = versions()
    cases_path = args.cases or (os.path.join(DEFAULT_ARTIFACT_DIR, "cases.json") if os.path.exists(os.path.join(DEFAULT_ARTIFACT_DIR, "cases.json")) else None)
    meta = {"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"), "python": v["python"], "sympy": v["sympy"], "z3": v["z3"],
            "script": os.path.relpath(os.path.abspath(__file__), os.getcwd()), "script_sha256": sha256_file(os.path.abspath(__file__)),
            "command": "python3 scripts/witness_checks.py --all",
            "protocol_note": "post hoc executable certificates (PROTOCOL.md Amendment 1.1); PASS = the computation confirms the objection as recorded in RESULTS.md (p1-board: refutes the earlier counterexample)",
            "ledger": LEDGER, "not_encoded": [{"case_id": a, "objection": b, "reason": c} for a, b, c in NOT_ENCODED],
            "text_receipts": text_receipts(cases_path),
            "summary": {"n_checks": len(certs), "n_pass": sum(c["result"] == "PASS" for c in certs), "n_fail": sum(c["result"] != "PASS" for c in certs)}}
    n_pass = meta["summary"]["n_pass"]
    print(f"{n_pass}/{len(certs)} PASS  (python {v['python']}, sympy {v['sympy']}, z3 {v['z3']})")
    tr = meta["text_receipts"]
    if tr["found"]:
        m1 = sum(bool(r.get("sha256_matches_cases_json")) for r in tr["texts"].values()); m2 = sum(bool(r.get("recomputed_sha256_matches")) for r in tr["texts"].values())
        print(f"text receipts: {m1}/{len(tr['texts'])} embedded sha256 match {tr['cases_json']}; {m2}/{len(tr['texts'])} recomputed from the text files")
    else:
        print("text receipts: cases.json not found (pass --cases to cross-check the embedded sha256 values)")
    if not args.no_write:
        out_dir = args.out_dir or (DEFAULT_ARTIFACT_DIR if os.path.isdir(DEFAULT_ARTIFACT_DIR) else SCRIPT_DIR)
        jpath, mpath = write_outputs(certs, meta, out_dir)
        print(f"wrote {jpath} and {mpath}")
    return 0 if n_pass == len(certs) else 1

# ============================================================================================ CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="run every certificate, print one line each, write certificates.json and CERTIFICATES.md")
    ap.add_argument("--out-dir", default=None, help="directory for certificates.json / CERTIFICATES.md (default: the artifacts dir next to the repo's scripts/, else the script's dir)")
    ap.add_argument("--cases", default=None, help="cases.json to cross-check the embedded text hashes against (default: the repo copy if present)")
    ap.add_argument("--no-write", action="store_true", help="with --all: print only, write nothing")
    sub = ap.add_subparsers(dest="cmd")
    def add(name, fn, **kw):
        p = sub.add_parser(name, help=(fn.__doc__ or "").strip().splitlines()[0], description=fn.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
        for a, opts in kw.items(): p.add_argument(a, **opts)
        return p
    add("p3", xiang_best_reply, **{"--pieces": dict(nargs="+", required=True), "--n": dict(type=int, required=True), "--grid": dict(type=int, default=12)})
    add("p3-odd-rank", odd_rank_sum, **{"--pieces": dict(nargs="+", required=True)})
    add("p3-nested", nested_abs_diff, **{"seq": dict(nargs="+")})
    add("p5-chain", p5_chain, **{"x": {}, "y": {}, "c": {}})
    add("p6-transversals", check_p6_transversals, **{"--n": dict(type=int, default=6)})
    add("p1-board", check_p1_board, **{"--board": dict(nargs="+", type=int, default=[2, 3])})
    add("p3-muse", check_p3_muse, **{"--grid": dict(type=int, default=12)})
    add("p3-deepseek", check_p3_deepseek, **{"--grid": dict(type=int, default=12), "--denom": dict(type=int, default=60)})
    add("p3-grok", check_p3_grok)
    add("p3-two-columns", check_p3_two_columns, **{"--T": dict(default="1")})
    add("p3-cut-parity", check_p3_cut_parity, **{"--d": dict(default="1")})
    add("p3-strip-count", check_p3_strip_count, **{"--jmax": dict(type=int, default=8)})
    add("p3-kimi-order", check_p3_kimi_order)
    add("p5-nemotron-z3", check_p5_nemotron_z3)
    add("p5-deepseek-dichotomy", check_p5_deepseek_dichotomy)
    add("p5-deepseek-typo", check_p5_deepseek_typo)
    add("p6-gpt-transversals", check_p6_gpt_transversals, **{"--k": dict(type=int, default=8)})
    add("p6-gpt-recursion", check_p6_gpt_recursion)
    add("p6-kimi-infinite-transversal", check_p6_kimi_infinite, **{"--N": dict(type=int, default=8)})
    args = ap.parse_args()
    if args.all: return run_all(args)
    if not args.cmd: ap.print_help(); return 2
    if args.cmd == "p3":
        ps = [Fr(x) for x in args.pieces]; base = odd_rank_sum(ps); v, cuts = xiang_best_reply(ps, args.n, args.grid)
        print(f"Liu pieces {[str(p) for p in ps]} (sum {sum(ps)}), Liu value with no Xiang cuts = {base} = {float(base):.6f}")
        print(f"searched Xiang replies with <= {args.n} cuts on a 1/{args.grid} grid: min Liu value = {v} = {float(v):.6f}; attained by cuts "
              f"(piece index, position within piece) = {[(i, str(p)) for i, p in cuts]}")
        print("this minimum is an upper bound on what Liu can guarantee with these pieces (the single reply above refutes any claimed guarantee "
              "exceeding it); the search is not exhaustive, so it is not a lower bound on what Xiang can force")
        print(f"correct answer c_n = 2^n/(2^(n+1)-1) = {Fr(2 ** args.n, 2 ** (args.n + 1) - 1)} = {2 ** args.n / (2 ** (args.n + 1) - 1):.6f}")
        return 0
    if args.cmd == "p3-odd-rank":
        ps = [Fr(x) for x in args.pieces]; v = odd_rank_sum(ps)
        print(f"pieces {[str(p) for p in ps]} sum {sum(ps)}: odd-rank sum = {v} = {float(v):.6f}; brute-force minimax = {minimax_claim(ps)}")
        return 0
    if args.cmd == "p3-nested":
        dec = sorted(map(Fr, args.seq), reverse=True)
        print(f"order {args.seq}: nested absolute difference = {nested_abs_diff(args.seq)}; decreasing order {[str(v) for v in dec]}: {nested_abs_diff(dec)}")
        return 0
    if args.cmd == "p5-chain":
        l, mt, mw, r = p5_chain(args.x, args.y, args.c)
        print(f"x={args.x} y={args.y} c={args.c}: left={l:.4f}; true middle (x+y+c)/2={mt:.4f} (left>=middle {l >= mt - 1e-12}); "
              f"written middle (x+y+2c)/2={mw:.4f} (left>=written {l >= mw - 1e-12}); right={r:.4f}")
        return 0
    runners = {"p6-transversals": lambda: check_p6_transversals(args.n), "p1-board": lambda: check_p1_board(tuple(args.board)),
               "p3-muse": lambda: check_p3_muse(args.grid), "p3-deepseek": lambda: check_p3_deepseek(args.grid, args.denom), "p3-grok": check_p3_grok,
               "p3-two-columns": lambda: check_p3_two_columns(Fr(args.T)), "p3-cut-parity": lambda: check_p3_cut_parity(Fr(args.d)),
               "p3-strip-count": lambda: check_p3_strip_count(args.jmax), "p3-kimi-order": check_p3_kimi_order, "p5-nemotron-z3": check_p5_nemotron_z3,
               "p5-deepseek-dichotomy": check_p5_deepseek_dichotomy, "p5-deepseek-typo": check_p5_deepseek_typo,
               "p6-gpt-transversals": lambda: check_p6_gpt_transversals(args.k), "p6-gpt-recursion": check_p6_gpt_recursion,
               "p6-kimi-infinite-transversal": lambda: check_p6_kimi_infinite(args.N)}
    c = runners[args.cmd]()
    print(f"[{c['check']}] cases {c['case_ids']}; ledger {c['ledger_key']}: {c['ledger_statement']}")
    print(f"claim checked: {c['claim_checked']}")
    for ln in c["_lines"]: print(ln)
    print(f"{c['result']}: {c['summary']}")
    return 0 if c["result"] == "PASS" else 1

if __name__ == "__main__": sys.exit(main())
