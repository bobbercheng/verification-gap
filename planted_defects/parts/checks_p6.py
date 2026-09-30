#!/usr/bin/env python3
"""Executable checks for the planted defects in parts/p6.json (IMO 2026 Problem 6). Standalone; no model calls.

Each check returns (ok, detail) where ok means the planted statement was confirmed FALSE (type F) or the display was
confirmed false AND the continuation value confirmed correct (type H).
"""
from itertools import combinations
from math import gcd


def sequence(a1, upto):
    """Greedy sequence: a_{n+1} is the least m > a_n with gcd(m, a_i) > 1 for all i <= n. All terms <= upto."""
    terms = [a1]
    for m in range(a1 + 1, upto + 1):
        if all(gcd(m, t) > 1 for t in terms):
            terms.append(m)
    return terms


def supp(x):
    s, p = set(), 2
    while p * p <= x:
        if x % p == 0:
            s.add(p)
            while x % p == 0:
                x //= p
        p += 1
    if x > 1:
        s.add(x)
    return s


def good(S, terms):
    """S is 'good' (meets every term's support) as far as the computed terms go."""
    return all(S & supp(t) for t in terms)


def minimal_good_sets(a1, upto, prime_bound):
    """Inclusion-minimal good subsets of the primes <= prime_bound (the family C of the deedy text), computed against the terms <= upto.
    By the theorem only primes <= a1 matter, and membership is periodic with period dividing prod(primes <= a1), so for the small a1 used
    below the terms <= upto determine the family."""
    primes = [p for p in range(2, prime_bound + 1) if all(p % q for q in range(2, p))]
    terms = sequence(a1, upto)
    goods = []
    for k in range(1, len(primes) + 1):
        for S in combinations(primes, k):
            S = set(S)
            if any(G <= S for G in goods):
                continue
            if good(S, terms):
                goods.append(S)
    return goods, terms


def check_deedy_F_transversal_lemma():
    """Planted: 'every pairwise-intersecting family of finite sets has only finitely many inclusion-minimal finite transversals'.
    Refutation: F_k = {x_1..x_k, y_k}; for every k the set X_k = {y_1..y_{k-1}, x_k} is a distinct minimal finite transversal.
    Verified on the truncation F_1..F_N for N = 14, k <= 10 (X_k meets F_j via y_j for j < k and via x_k for j >= k, so the truncation
    argument is exact for every N >= k). Also: the bogus proof's sunflower 'fact' without a cardinality bound fails for {1..n}."""
    N, KMAX = 14, 10
    x = [("x", i) for i in range(1, N + 1)]
    y = [("y", i) for i in range(1, N + 1)]
    F = [set(x[:k]) | {y[k - 1]} for k in range(1, N + 1)]
    inter = all(A & B for A, B in combinations(F, 2))
    if not inter:
        return False, "F_k family is not pairwise intersecting"
    X = [set(y[:k - 1]) | {x[k - 1]} for k in range(1, KMAX + 1)]

    def transversal(S):
        return all(S & A for A in F)

    def minimal(S):
        return transversal(S) and all(not transversal(S - {e}) for e in S)

    if not all(minimal(S) for S in X):
        return False, "some X_k is not a minimal transversal of F_1..F_N"
    if len({frozenset(S) for S in X}) != KMAX:
        return False, "X_k not distinct"
    # sunflower 'fact' without size bound: initial segments have no 3-sunflower at all
    segs = [set(range(1, n + 1)) for n in range(1, 9)]
    sunflower3 = any(len({frozenset(A & B), frozenset(A & C), frozenset(B & C)}) == 1 for A, B, C in combinations(segs, 3))
    if sunflower3:
        return False, "initial segments unexpectedly contain a 3-sunflower"
    return True, (f"F_k = {{x_1..x_k, y_k}} is pairwise intersecting; X_k = {{y_1..y_(k-1), x_k}} are {KMAX} distinct minimal finite "
                  f"transversals of F_1..F_{N} (k = 1..{KMAX}, unbounded in k) -> the planted general lemma is false; "
                  f"and among the initial segments {{1..n}}, n <= 8, no three sets form a sunflower -> the bogus unbounded sunflower fact is false")


def check_deedy_H_cardinality_display():
    """Planted display: 2^{|D|} <= w(D\\{p}) < a_1 for a terminal D with its p. Show it is false (a_1 = 15, D = {2,3}, p = 3),
    while the correct display 2^{|D|-1} <= w(D\\{p}) and the continuation |D| <= a_1 hold for every terminal member for a_1 <= 60."""
    def w(S):
        r = 1
        for q in S:
            r *= q
        return r
    fails_planted, ok_correct, ok_cont, witness = 0, True, True, None
    for a1 in range(2, 61):
        C, _ = minimal_good_sets(a1, 6 * a1 + 400, a1)
        for D in C:
            for p in D:
                if w(D - {p}) < a1:  # D is terminal via p
                    if not (2 ** (len(D) - 1) <= w(D - {p})):
                        ok_correct = False
                    if not (len(D) <= a1):
                        ok_cont = False
                    if not (2 ** len(D) <= w(D - {p})):
                        fails_planted += 1
                        if witness is None or a1 == 15 and witness[0] != 15:
                            witness = (a1, sorted(D), p, w(D - {p}))
    C15, terms15 = minimal_good_sets(15, 500, 15)
    d15 = {2, 3} in C15
    ok = fails_planted > 0 and ok_correct and ok_cont and d15
    return ok, (f"planted display fails {fails_planted} times for a_1 <= 60, e.g. a_1, D, p, w(D-p) = {witness} (2^|D| = {2 ** len(witness[1])}); "
                f"correct display 2^(|D|-1) <= w(D-p) holds always: {ok_correct}; continuation |D| <= a_1 holds always: {ok_cont}; "
                f"C(15) = {sorted(map(sorted, C15))}, first terms {terms15[:9]}")


def check_ours_F_prime_set():
    """Planted: Q = primes dividing A (instead of primes <= A); lemma 'sigma(x) is good for every term x'. Refute for A = 15:
    sigma(18) = {3} is not good (20 is a term with support {2,5}); with L = prod(primes | 15) = 15, (4) fails (18 term, 33 not) and
    a_{n+T} = a_n + L fails for the proof's own T = #terms in [15, 29]."""
    A = 15
    terms = sequence(A, 400)
    Q = {p for p in supp(A)}
    sigma = lambda x: supp(x) & Q
    if 18 not in terms or 20 not in terms:
        return False, "unexpected sequence"
    s18 = sigma(18)
    lemma_false = not good(s18, terms) and not (s18 & supp(20))
    L = 1
    for p in Q:
        L *= p
    four_fails = (18 in terms) != (18 + L in terms)
    T = sum(1 for t in terms if A <= t <= A + L - 1)
    boxed_fails = any(terms[n + T] != terms[n] + L for n in range(0, 6))
    # the correct Q = primes <= A does work here
    Qc = {p for p in range(2, A + 1) if all(p % q for q in range(2, p))}
    Lc = 1
    for p in Qc:
        Lc *= p
    ok = lemma_false and four_fails and boxed_fails
    return ok, (f"A=15: terms {terms[:9]}; sigma(18) on primes dividing 15 = {s18}, meets supp(20)={supp(20)}? {bool(s18 & supp(20))} -> lemma false; "
                f"L={L}: 18 term {18 in terms}, 33 term {33 in terms} -> (4) false; T={T}: a_(n+T) = a_n + {L} fails within n<=6: {boxed_fails} "
                f"(a_2={terms[1]}, a_(2+T)={terms[1 + T]}); correct L={Lc} untouched")


def check_ours_H_example_terms():
    """Planted display: 'the first terms are 15,18,22'. Show 22 is not a term (gcd(22,15)=1), the third term is 20, and the continuation
    values are correct: 21 skipped with gcd(21,20)=1, and 18, 21 have the same trace {3} on the primes dividing 15."""
    terms = sequence(15, 100)
    display_false = terms[:3] != [15, 18, 22] and 22 not in terms and gcd(22, 15) == 1
    cont_ok = (terms[:3] == [15, 18, 20] and 21 not in terms and gcd(21, 20) == 1
               and supp(18) & supp(15) == {3} and supp(21) & supp(15) == {3})
    return display_false and cont_ok, (f"first terms {terms[:5]}; 22 term? {22 in terms} (gcd(22,15)={gcd(22, 15)}) -> display false; "
                                        f"continuation: 21 term? {21 in terms}, gcd(21,20)={gcd(21, 20)}, traces of 18, 21 on {{3,5}}: "
                                        f"{supp(18) & {3, 5}}, {supp(21) & {3, 5}} -> correct")


CHECKS = {
    "check_deedy_F_transversal_lemma": check_deedy_F_transversal_lemma,
    "check_deedy_H_cardinality_display": check_deedy_H_cardinality_display,
    "check_ours_F_prime_set": check_ours_F_prime_set,
    "check_ours_H_example_terms": check_ours_H_example_terms,
}

if __name__ == "__main__":
    import sys
    rc = 0
    for name, fn in CHECKS.items():
        ok, detail = fn()
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
        rc |= (not ok)
    sys.exit(rc)
