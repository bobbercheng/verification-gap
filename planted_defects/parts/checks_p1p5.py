#!/usr/bin/env python3
"""Executable checks for the planted defects in parts/p1p5.json (types F and H). Standalone: no repo imports, no model calls.

Each check takes no arguments and returns (ok, detail). ok == True means:
  F entries: the planted statement was confirmed FALSE by exact computation;
  H entries: the planted display was confirmed FALSE and the continuation value was confirmed CORRECT.
"""
from fractions import Fraction
from itertools import product
from math import gcd, isqrt
import sympy as sp


# ----------------------------------------------------------------------------------------------------------------------
# P1 helpers: the board process (m, n) -> (gcd, lcm/gcd)
def move(m, n):
    g = gcd(m, n)
    return g, (m * n // g) // g


def all_terminal_boards(board):
    """Exhaustive play-out; returns the set of terminal boards (as sorted tuples)."""
    seen, out, stack = set(), set(), [tuple(sorted(board))]
    while stack:
        b = stack.pop()
        if b in seen:
            continue
        seen.add(b)
        idx = [i for i, x in enumerate(b) if x > 1]
        if len(idx) < 2:
            out.add(b)
            continue
        for i in range(len(idx)):
            for j in range(i + 1, len(idx)):
                g, l = move(b[idx[i]], b[idx[j]])
                nb = list(b)
                nb[idx[i]], nb[idx[j]] = g, l
                stack.append(tuple(sorted(nb)))
    return out


# ----------------------------------------------------------------------------------------------------------------------
def check_p1_kimi_F():
    """Planted lemma: 'A positive integer that never increases and starts above 1 can never reach 1.'
    Confirm it is false: exhibit a non-increasing sequence of positive integers starting above 1 that reaches 1, and exhibit a
    non-increasing product sequence in an analogous process (halving) that reaches 1. Also confirm, for the record, that the
    conclusion the lemma was used for (some entry > 1 survives) is nevertheless true on small boards, i.e. the mutant relies on
    a false lemma for a true statement."""
    seq = [2, 1]
    non_increasing = all(seq[i + 1] <= seq[i] for i in range(len(seq) - 1))
    hyp = non_increasing and seq[0] > 1
    reaches_one = 1 in seq
    lemma_false = hyp and reaches_one
    # a longer instance: P = 8 halving each step: 8, 4, 2, 1
    seq2 = [8, 4, 2, 1]
    lemma_false2 = all(seq2[i + 1] <= seq2[i] for i in range(3)) and seq2[0] > 1 and 1 in seq2
    survivor_ok = True
    for board in product(range(2, 7), repeat=3):
        for t in all_terminal_boards(board):
            if sum(1 for x in t if x > 1) != 1:
                survivor_ok = False
    ok = lemma_false and lemma_false2
    return ok, (f"lemma refuted by non-increasing sequences {seq} and {seq2} (start > 1, reach 1); "
                f"true survivor claim on all 3-boards with entries 2..6: {survivor_ok}")


def check_p1_kimi_H():
    """Planted display: type B (gcd = 1) move outputs ell = m + n. Confirm false for every coprime pair with 2 <= m, n <= 40,
    and confirm the continuation '(m, n) is replaced by (1, mn): P unchanged, z increases by exactly 1' is correct."""
    display_false_everywhere, continuation_ok, cases = True, True, 0
    for m in range(2, 41):
        for n in range(2, 41):
            if gcd(m, n) != 1:
                continue
            cases += 1
            g, l = move(m, n)
            if l == m + n:
                display_false_everywhere = False
            if not (g == 1 and l == m * n and g * l == m * n):
                continuation_ok = False
    g, l = move(2, 3)
    return (display_false_everywhere and continuation_ok,
            f"{cases} coprime pairs: ell = mn != m+n in all of them (e.g. (2,3) -> {(g, l)}, m+n = 5); continuation (1, mn) with "
            f"product unchanged confirmed")


def check_p1_gpt56_F():
    """Planted lemma: 'A nonnegative integer that never increases and starts at a positive value can never reach 0.'
    Confirm false by the sequence 1, 0 (and 2026, 2025, ..., 0). Also record that K is genuinely non-increasing in the process
    (so the mutant's hypothesis is true) while the conclusion K >= 1 is not a consequence of the hypothesis."""
    seq = [1, 0]
    lemma_false = seq[0] > 0 and all(seq[i + 1] <= seq[i] for i in range(len(seq) - 1)) and 0 in seq
    seq2 = list(range(2026, -1, -1))
    lemma_false2 = seq2[0] > 0 and all(seq2[i + 1] <= seq2[i] for i in range(len(seq2) - 1)) and 0 in seq2
    K_non_increasing = True
    for m in range(2, 30):
        for n in range(2, 30):
            g, l = move(m, n)
            if (g > 1) + (l > 1) > 2:
                K_non_increasing = False
    return (lemma_false and lemma_false2,
            f"lemma refuted by {seq} and by 2026, 2025, ..., 0; K non-increasing in the real process: {K_non_increasing} "
            f"(hypothesis true, conclusion does not follow)")


def check_p1_gpt56_H():
    """Planted display: g * (lcm/g) = lcm(m, n) = mn/g^2. Confirm the display is false for every pair with gcd > 1 (2 <= m, n <= 40)
    and that the continuation P' = P/g (i.e. the product of the two outputs equals mn/g) is correct for all pairs."""
    display_false, continuation_ok, n_false = True, True, 0
    for m in range(2, 41):
        for n in range(2, 41):
            g, l = move(m, n)
            lcm = m * n // g
            if Fraction(m * n, g) != g * l:
                continuation_ok = False
            if g > 1:
                if Fraction(m * n, g * g) == lcm:
                    display_false = False
                else:
                    n_false += 1
    return (display_false and continuation_ok,
            f"lcm(m,n) != mn/g^2 for all {n_false} pairs with g > 1 in [2,40]^2 (e.g. (4,6): 12 vs 6); "
            f"product of outputs = mn/g for all pairs, so P' = P/g is correct")


def check_p5_gpt56_F():
    """Planted identity: (t+2c+y)^2 - 4(t+c)(y+b) = (t-y)^2 + 4(t+c)(b-c). Confirm false symbolically (the difference is the
    nonzero polynomial 8(t+c)(c-b)) and at an exact point; confirm the original identity with (c-b) is true."""
    t, y, c, b = sp.symbols("t y c b", positive=True)
    lhs = (t + 2 * c + y) ** 2 - 4 * (t + c) * (y + b)
    planted = (t - y) ** 2 + 4 * (t + c) * (b - c)
    original = (t - y) ** 2 + 4 * (t + c) * (c - b)
    diff_planted = sp.expand(lhs - planted)
    diff_original = sp.expand(lhs - original)
    pt = {t: 1, y: 1, c: 1, b: 0}
    lhs_v, planted_v, orig_v = [Fraction(int(e.subs(pt))) for e in (lhs, planted, original)]
    ok = diff_planted != 0 and diff_original == 0 and lhs_v != planted_v and lhs_v == orig_v
    return ok, (f"lhs - planted = {sp.factor(diff_planted)} (nonzero); lhs - original = {diff_original}; at t=y=c=1,b=0: "
                f"lhs={lhs_v}, planted={planted_v}, original={orig_v}")


def _sqrt_ge(a, b):
    """Exact test sqrt(a) >= b for nonnegative Fractions a, b (compare squares)."""
    return a >= b * b


def check_p5_gpt56_H():
    """Planted display: middle term (x+y+2C)/2. Confirm the planted chain is false for f(x) = x + C at an exact point, that the
    correct middle term equals (f(x)+y)/2 = (x+(y+C))/2 identically, and that the correct chain (RMS >= AM >= GM of x and y+C)
    holds on an exact grid."""
    x, y, C = sp.symbols("x y C", positive=True)
    f = lambda s: s + C
    correct_middle_identity = sp.simplify((f(x) + y) / 2 - (x + (y + C)) / 2) == 0
    planted_differs = sp.simplify((x + y + 2 * C) / 2 - (f(x) + y) / 2) != 0
    # planted chain at x = y = 1, C = 10: sqrt((1 + 121)/2) >= 11 ?  61 >= 121 is false
    X, Y, c = Fraction(1), Fraction(1), Fraction(10)
    rms_sq = (X ** 2 + (Y + c) ** 2) / 2
    planted_mid = (X + Y + 2 * c) / 2
    planted_first_fails = not _sqrt_ge(rms_sq, planted_mid)
    # correct chain on a grid
    correct_holds = True
    for X in (Fraction(1, 3), Fraction(1), Fraction(5, 2), Fraction(7)):
        for Y in (Fraction(1, 4), Fraction(1), Fraction(3), Fraction(9, 2)):
            for c in (Fraction(0), Fraction(1, 2), Fraction(2), Fraction(10)):
                rms_sq = (X ** 2 + (Y + c) ** 2) / 2
                am = (X + (Y + c)) / 2
                gm_sq = X * (Y + c)
                if not (_sqrt_ge(rms_sq, am) and am * am >= gm_sq):
                    correct_holds = False
    ok = correct_middle_identity and planted_differs and planted_first_fails and correct_holds
    return ok, ("planted chain fails at x=y=1, C=10 (61 >= 121 is false); correct middle term (x+(y+C))/2 = (f(x)+y)/2 "
                f"identically and the correct RMS >= AM >= GM chain holds on a 64-point exact grid: {correct_holds}")


CHECKS = {
    "check_p1_kimi_F": check_p1_kimi_F,
    "check_p1_kimi_H": check_p1_kimi_H,
    "check_p1_gpt56_F": check_p1_gpt56_F,
    "check_p1_gpt56_H": check_p1_gpt56_H,
    "check_p5_gpt56_F": check_p5_gpt56_F,
    "check_p5_gpt56_H": check_p5_gpt56_H,
}

if __name__ == "__main__":
    import sys
    bad = 0
    for name, fn in CHECKS.items():
        ok, detail = fn()
        bad += not ok
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
    sys.exit(1 if bad else 0)
