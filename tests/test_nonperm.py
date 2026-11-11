"""Testy 2. fázy – local search v nepermutačnom priestore (src/nonperm.py)."""

import json
from pathlib import Path

import numpy as np
import pytest

from evaluate import evaluate_nonpermutation, evaluate_permutation, is_valid_orders
from iga import iga
from instance import generate_instance, read_instance
from nonperm import apply_insertion, best_np_insertion, nonperm_local_search

TESTS = Path(__file__).parent
ROOT = TESTS.parent
AUTHORS = json.loads((TESTS / "data" / "authors_solutions.json").read_text())


# ---------------------------------------------------------------- presná zhoda s kódom autorov
# 2. fáza je deterministická: z rovnakej permutácie musí vyjsť rovnaký rozvrh ako u autorov.

@pytest.mark.parametrize("name", sorted(AUTHORS))
def test_matches_authors_phase2(name):
    p = read_instance(ROOT / "instances" / "generated" / f"{name}.txt").p
    a = AUTHORS[name]
    res = nonperm_local_search(p, a["perm"])
    assert (res.ms, res.ft) == (a["final_ms"], a["final_ft"])
    assert np.array_equal(res.orders, np.array(a["orders"]))


def test_fig3_reaches_optimum():
    """Obr. 3: najlepšia permutácia má ΣC = 1194, 2. fáza nájde optimum 1191
    (inverzia J3 a J2 na strojoch M4, M5)."""
    p = read_instance(TESTS / "fig3.txt").p
    perm = iga(p, seed=1).perm
    assert evaluate_permutation(p, perm)[1] == 1194
    res = nonperm_local_search(p, perm)
    assert res.ft == 1191
    assert evaluate_nonpermutation(p, res.orders) == (res.ms, 1191)


# ---------------------------------------------------------------- vkladanie vs. hrubá sila

def _candidates(n, m):
    """Všetky vkladania v poradí, v akom ich vyhodnocujú autori: (k, code)."""
    out = []
    for k in range(n, 0, -1):
        out.append((k, 0))
        if k == 1:
            break
        out += [(k, -l) for l in range(m, 1, -1)]
    for k in range(n, 1, -1):
        out += [(k, l) for l in range(2, m + 1)]
    return out


@pytest.mark.parametrize("seed", range(12))
def test_best_insertion_matches_brute_force(seed):
    """Zrýchlené vyhodnotenie (prefixy + orezanie) dá to isté ako úplné vyhodnotenie
    každého kandidáta, vrátane rozhodovania pri zhode (prvý najlepší vyhráva)."""
    rng = np.random.default_rng(seed)
    n, m = int(rng.integers(3, 9)), int(rng.integers(2, 7))
    p = generate_instance(n, m, [0.2, 0.3, 0.4][seed % 3], np.random.default_rng(100 + seed)).p
    # nepermutačný základ: rôzne poradia na strojoch
    job = int(rng.integers(n))
    others = [j for j in range(n) if j != job]
    base = np.array([rng.permutation(others) for _ in range(m)], dtype=np.int64)

    best = None
    for k, code in _candidates(n, m):
        orders = apply_insertion(base, job, k, code)
        assert is_valid_orders(orders, n)
        ms, ft = evaluate_nonpermutation(p, orders)
        if best is None or ft < best[2] or (ft == best[2] and ms < best[3]):
            best = (k, code, ft, ms)
    assert best_np_insertion(p, base, job) == best


def test_insertion_kinds():
    """Anticipation a delay posúvajú job o jednu pozícu od stroja l ďalej (Sekcia 3.2)."""
    base = np.array([[0, 1, 2]] * 4)
    # straight na pozíciu 2 (1-indexovane)
    assert apply_insertion(base, 9, 2, 0).tolist() == [[0, 9, 1, 2]] * 4
    # anticipation na stroji 3 do pozície 3: stroje 1–2 pozícia 3, stroje 3–4 pozícia 2
    assert apply_insertion(base, 9, 3, -3).tolist() == [[0, 1, 9, 2]] * 2 + [[0, 9, 1, 2]] * 2
    # delay na stroji 3 (kód autorov k = 3): stroje 1–2 pozícia 2, stroje 3–4 pozícia 3
    assert apply_insertion(base, 9, 3, 3).tolist() == [[0, 9, 1, 2]] * 2 + [[0, 1, 9, 2]] * 2


# ---------------------------------------------------------------- vlastnosti výsledku

@pytest.mark.parametrize("name", ["0.2_10_10_00", "0.3_20_05_01", "0.4_30_20_02"])
def test_never_worse_than_permutation(name):
    p = read_instance(ROOT / "instances" / "generated" / f"{name}.txt").p
    perm = iga(p, seed=3).perm
    res = nonperm_local_search(p, perm)
    assert is_valid_orders(res.orders, p.shape[1])
    assert evaluate_nonpermutation(p, res.orders) == (res.ms, res.ft)
    assert res.ft <= evaluate_permutation(p, perm)[1]
    assert nonperm_local_search(p, perm).ft == res.ft      # deterministické
