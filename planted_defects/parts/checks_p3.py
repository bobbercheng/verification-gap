#!/usr/bin/env python3
"""Executable checks for the P3 planted defects in parts/p3.json (exact rational arithmetic, no model calls).

Each check returns (ok, detail): for an F entry ok means the planted statement was confirmed FALSE on a finite
instance; for an H entry ok means the planted display was confirmed false AND the continuation value confirmed correct.
The claiming value of a sorted multiset is the sum of its odd-ranked pieces; D = alternating sum of the sorted lengths.
"""
from fractions import Fraction as Fr
from itertools import product

def sorted_desc(parts):  # parts: list of (length, origin) -> nonincreasing by length
    return sorted(parts, key=lambda p: -p[0])

def rank_pairs(parts):
    """Adjacent rank pairs (a_{2i-1}, a_{2i}) of the sorted parts; returns (pairs, singleton_or_None)."""
    s = sorted_desc(parts)
    pairs = [(s[2 * i], s[2 * i + 1]) for i in range(len(s) // 2)]
    return pairs, (s[-1] if len(s) % 2 else None)

def alt_sum(lengths):
    s = sorted(lengths, reverse=True)
    return sum(x if i % 2 == 0 else -x for i, x in enumerate(s))

def components(n_vertices, edges):
    parent = list(range(n_vertices))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for a, b in edges: parent[find(a)] = find(b)
    return {v: find(v) for v in range(n_vertices)}

def tree_step_counterexample(pieces, cuts):
    """pieces: list of Fractions indexed by vertex; cuts: {vertex: [sub-lengths summing to the piece]}.
    Builds the rank-pair multigraph; returns dict with |E|, |V|, loops, and whether the component of the last vertex
    (the longest piece) contains a loop."""
    parts = []
    for v, q in enumerate(pieces):
        subs = cuts.get(v, [q]); assert sum(subs) == q, (v, subs, q)
        parts += [(x, v) for x in subs]
    pairs, single = rank_pairs(parts)
    edges = [(a[1], b[1]) for a, b in pairs]
    loops = [e for e in edges if e[0] == e[1]]
    comp = components(len(pieces), edges)
    last = len(pieces) - 1
    loop_in_last = any(comp[e[0]] == comp[last] for e in loops)
    return {"E": len(edges), "V": len(pieces), "edges": edges, "loops": loops, "loop_in_last_component": loop_in_last,
            "sorted": [(str(x), v) for x, v in sorted_desc(parts)], "D": alt_sum([x for x, _ in parts])}

# ---------------------------------------------------------------- deedy-claude-fable-5-final-F
def check_claude_F():
    """Planted: |E|<|V| implies G has no cycle and no loop, and the component containing vertex n is a simple tree."""
    n = 2; u = Fr(1, 2 ** (n + 1) - 1)
    pieces = [u * 2 ** j for j in range(n + 1)]                      # geometric configuration q_j = 2^j u
    cuts = {2: [Fr(5, 2) * u, Fr(3, 2) * u], 1: [Fr(6, 5) * u, Fr(4, 5) * u]}   # K = 2 <= n cuts
    r = tree_step_counterexample(pieces, cuts)
    ok = r["E"] < r["V"] and bool(r["loops"]) and r["loop_in_last_component"]
    detail = (f"n={n}, u=1/7, Y cuts 4u->2.5u+1.5u and 2u->1.2u+0.8u: sorted parts {r['sorted']}, edges {r['edges']}, "
              f"|E|={r['E']}<|V|={r['V']} yet loops {r['loops']}; component of vertex n={n} has a loop -> planted claim false "
              f"(D(A)={r['D']} = {r['D']/u}u, so the lemma's conclusion still holds but its written argument breaks)")
    return ok, detail

# ---------------------------------------------------------------- deedy-claude-fable-5-final-H
def check_claude_H():
    """Planted display (1-u)/2 = (2^n-1)/2^{n+1}; continuation uses (1+u)/2 = c = 2^n/(2^{n+1}-1)."""
    bad, cont = [], []
    for n in range(1, 11):
        u = Fr(1, 2 ** (n + 1) - 1)
        bad.append((1 - u) / 2 != Fr(2 ** n - 1, 2 ** (n + 1)))
        cont.append((1 + u) / 2 == Fr(2 ** n, 2 ** (n + 1) - 1))
    ok = all(bad) and all(cont)
    u1 = Fr(1, 3)
    return ok, (f"display false for n=1..10 (n=1: (1-u)/2={(1-u1)/2} vs planted {Fr(1,4)}); continuation "
                f"(1+u)/2 = 2^n/(2^{{n+1}}-1) = c holds for n=1..10")

# ---------------------------------------------------------------- deedy-gpt-5.6-sol-xhigh-final-F
def subset_sums(a, nonempty_proper):
    q = len(a); out = []
    for mask in range(2 ** q):
        if nonempty_proper and mask in (0, 2 ** q - 1): continue
        out.append(sum(a[i] for i in range(q) if mask >> i & 1))
    return sorted(out)

def check_xhigh_F():
    """Planted (11): consecutive sums of the NONEMPTY PROPER subsets differ by at most d = 1/(2^{n+1}-1)."""
    n = 1; d = Fr(1, 2 ** (n + 1) - 1); a = [Fr(7, 10), Fr(3, 10)]
    s = subset_sums(a, True); gap = min(y - x for x, y in zip(s, s[1:]))
    s_all = subset_sums(a, False); gap_all = min(y - x for x, y in zip(s_all, s_all[1:]))
    # what the planted route can guarantee for this division: D <= gap (2/5) versus the required d = 1/3;
    # the true reply (bisect 7/10) gives D = 3/10 <= d.
    D_true_reply = alt_sum([Fr(7, 20), Fr(7, 20), Fr(3, 10)])
    ok = gap > d and gap_all <= d and D_true_reply <= d
    return ok, (f"n={n}, Liu (7/10,3/10): nonempty-proper subset sums {[str(x) for x in s]} min gap {gap} > d={d} -> planted (11) false; "
                f"all subset sums (with the empty set) give min gap {gap_all} <= d; bisecting 7/10 gives D={D_true_reply} <= d")

# ---------------------------------------------------------------- deedy-gpt-5.6-sol-xhigh-final-H
def check_xhigh_H():
    """Planted display 1+2+...+2^{k-1} = 2^k-2; continuation: a nonempty signed sum of distinct powers of two has |.| >= 1."""
    bad = all(sum(2 ** j for j in range(k)) != 2 ** k - 2 for k in range(1, 12))
    mins = []
    for k in range(0, 6):
        vals = [abs(sum(s * 2 ** j for j, s in enumerate(signs))) for signs in product((-1, 0, 1), repeat=k + 1) if any(signs)]
        mins.append(min(vals))
    ok = bad and all(m == 1 for m in mins)
    return ok, (f"display false for k=1..11 (true sum is 2^k-1); min |nonempty signed sum| over powers 2^0..2^k = {mins} "
                f"for k=0..5, so the continuation 'at least 1' is correct")

# ---------------------------------------------------------------- gpt56-ours-accepted-F
def check_ours_F():
    """Planted: fewer edges than vertices implies no cycle/loop; the component containing the vertex of a_q is a tree."""
    a = [Fr(1, 5), Fr(3, 10), Fr(1, 2)]                              # q = 3 initial intervals (n = 2)
    cuts = {2: [Fr(13, 50), Fr(12, 50)], 1: [Fr(8, 50), Fr(7, 50)]}    # k = 2 <= q-1 cuts
    r = tree_step_counterexample(a, cuts)
    ok = r["E"] < r["V"] and bool(r["loops"]) and r["loop_in_last_component"]
    return ok, (f"q=3, a=(1/5,3/10,1/2), cuts 1/2->13/50+12/50, 3/10->8/50+7/50: sorted parts {r['sorted']}, edges {r['edges']}, "
                f"|E|={r['E']}<|V|={r['V']} yet loops {r['loops']}; the component of the vertex of a_q has a loop -> planted claim false")

# ---------------------------------------------------------------- gpt56-ours-accepted-H
def pieces_from_marks(marks):
    pts = [Fr(0)] + sorted(marks) + [Fr(1)]
    return [y - x for x, y in zip(pts, pts[1:])]

def gamma(a):
    best = None
    for signs in product((-1, 0, 1), repeat=len(a)):
        if not any(signs): continue
        v = abs(sum(s * x for s, x in zip(signs, a)))
        best = v if best is None else min(best, v)
    return best

def check_ours_H():
    """Planted: marks 2^j delta (j=1..n); continuation: lengths (9) delta,2delta,...,2^n delta have Gamma = delta."""
    det, ok = [], True
    for n in (1, 2, 3):
        dl = Fr(1, 2 ** (n + 1) - 1); target = [dl * 2 ** j for j in range(n + 1)]
        planted = [dl * 2 ** j for j in range(1, n + 1)]
        correct = [dl * (2 ** j - 1) for j in range(1, n + 1)]
        p_ok = all(0 < m < 1 for m in planted) and pieces_from_marks(planted) == target   # 'in order' as displayed in (9)
        c_ok = pieces_from_marks(correct) == target
        g_ok = gamma(target) == dl
        ok &= (not p_ok) and c_ok and g_ok
        det.append(f"n={n}: planted marks give {[str(x) for x in pieces_from_marks(planted)]} (matches (9): {p_ok}); "
                   f"correct marks give (9): {c_ok}; Gamma of (9) = delta: {g_ok}")
    return ok, "; ".join(det)

CHECKS = {"check_claude_F": check_claude_F, "check_claude_H": check_claude_H, "check_xhigh_F": check_xhigh_F,
          "check_xhigh_H": check_xhigh_H, "check_ours_F": check_ours_F, "check_ours_H": check_ours_H}

if __name__ == "__main__":
    import sys
    fails = 0
    for name, fn in CHECKS.items():
        ok, detail = fn(); fails += (not ok)
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
    sys.exit(1 if fails else 0)
