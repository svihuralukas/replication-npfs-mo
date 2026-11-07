"""Testy účelovej funkcie (src/evaluate.py). Spustenie: python -m pytest tests/"""

import itertools
import json
from pathlib import Path

import numpy as np
import pytest

from evaluate import (completion_times_nonpermutation, completion_times_permutation,
                      evaluate_nonpermutation, evaluate_permutation, is_valid_orders,
                      permutation_to_orders)
from instance import read_instance

TESTS = Path(__file__).parent
ROOT = TESTS.parent

# ---------------------------------------------------------------- obr. 1 článku
# Riadky = stroje M1..M4, stĺpce = joby J1..J3, 0 = chýbajúca operácia.
FIG1 = np.array([[2, 2, 1],
                 [2, 3, 0],
                 [2, 0, 5],
                 [3, 2, 0]])


def test_fig1_missing_operations():
    """Obr. 1 (stred): s chýbajúcimi operáciami Cmax = 11, ΣC = 31."""
    C = completion_times_permutation(FIG1, [0, 1, 2])
    expected = np.array([[2, 4, 5],
                         [4, 7, 0],
                         [6, 0, 11],
                         [9, 11, 0]])
    assert np.array_equal(C, expected)
    assert evaluate_permutation(FIG1, [0, 1, 2]) == (11, 31)


def test_fig1_zero_time_operations():
    """Obr. 1 (vpravo): ak chýbajúce operácie berieme ako nulové, Cmax = 12, ΣC = 32."""
    C = completion_times_permutation(FIG1, [0, 1, 2], zero_time=True)
    expected = np.array([[2, 4, 5],
                         [4, 7, 7],
                         [6, 7, 12],
                         [9, 11, 12]])
    assert np.array_equal(C, expected)
    assert C.max() == 12 and C[-1].sum() == 32


# ---------------------------------------------------------------- obr. 3 článku
# Optimálny rozvrh J5, J3[1,3], J2, J3[4,5], J4, J1:
# na M1–M3 poradie J5, J3, J2, J4, J1; na M4–M5 poradie J5, J2, J3, J4, J1.
FIG3_ORDERS = np.array([[4, 2, 1, 3, 0]] * 3 + [[4, 1, 2, 3, 0]] * 2)
FIG3_C = np.array([[223, 83, 23, 144, 17],
                   [262, 108, 55, 214, 0],
                   [333, 124, 102, 0, 38],
                   [410, 167, 176, 216, 129],
                   [0, 0, 225, 0, 173]])


def test_fig3_optimal_nonpermutation():
    p = read_instance(TESTS / "fig3.txt").p
    assert np.array_equal(completion_times_nonpermutation(p, FIG3_ORDERS), FIG3_C)
    assert evaluate_nonpermutation(p, FIG3_ORDERS) == (410, 1191)


def test_fig3_best_permutation_is_worse():
    """Najlepšia permutácia (hrubou silou cez všetkých 120) je horšia než optimum 1191 –
    obr. 3 potrebuje inverziu jobov J2/J3 na M4, M5."""
    p = read_instance(TESTS / "fig3.txt").p
    best = min(evaluate_permutation(p, perm)[1] for perm in itertools.permutations(range(5)))
    assert best == 1194


# ---------------------------------------------------------------- vnútorná konzistencia

@pytest.mark.parametrize("name", ["0.2_10_05_03", "0.4_20_30_08", "0.3_50_10_10"])
def test_permutation_equals_nonpermutation_with_same_orders(name):
    """Permutačný rozvrh zapísaný ako non-permutation musí dať rovnaké výsledky."""
    p = read_instance(ROOT / "instances" / "generated" / f"{name}.txt").p
    rng = np.random.default_rng(0)
    for _ in range(20):
        perm = rng.permutation(p.shape[1])
        orders = permutation_to_orders(perm, p.shape[0])
        assert evaluate_permutation(p, perm) == evaluate_nonpermutation(p, orders)
        assert np.array_equal(completion_times_permutation(p, perm),
                              completion_times_nonpermutation(p, orders))


def test_completion_times_respect_constraints():
    """C splní obmedzenia úlohy: poradie strojov pre job, jedna operácia naraz na stroji."""
    p = read_instance(ROOT / "instances" / "generated" / "0.4_20_10_00.txt").p
    m, n = p.shape
    rng = np.random.default_rng(1)
    orders = np.array([rng.permutation(n) for _ in range(m)])   # náhodné poradia na strojoch
    C = completion_times_nonpermutation(p, orders)
    S = C - p                                                   # časy začiatku
    for j in range(n):                                          # job: operácie idú po sebe
        ops = [i for i in range(m) if p[i, j] > 0]
        for a, b in zip(ops, ops[1:]):
            assert S[b, j] >= C[a, j]
    for i in range(m):                                          # stroj: bez prekryvu, v poradí
        seq = [j for j in orders[i] if p[i, j] > 0]
        for a, b in zip(seq, seq[1:]):
            assert S[i, b] >= C[i, a]


def test_partial_permutation():
    """Čiastočný rozvrh (len časť jobov) – ΣC len cez zaradené joby."""
    assert evaluate_permutation(FIG1, [0]) == (9, 9)
    assert evaluate_permutation(FIG1, [2, 0]) == (11, 6 + 11)   # J3 skončí v 6, J1 v 11


def test_job_without_operations():
    p = np.array([[3, 0], [2, 0]])
    assert evaluate_permutation(p, [0, 1]) == (5, 5)


def test_is_valid_orders():
    assert is_valid_orders(FIG3_ORDERS, 5)
    assert not is_valid_orders(np.array([[0, 1, 1], [0, 1, 2]]), 3)


# ---------------------------------------------------------------- porovnanie s kódom autorov
# tests/data/authors_solutions.json vytvoril reference/make_eval_fixture.py:
# riešenia, ktoré našiel ich program npfsmo, a ΣC, ktoré k nim vypočítal ich kód.

AUTHORS = json.loads((TESTS / "data" / "authors_solutions.json").read_text())


@pytest.mark.parametrize("name", sorted(AUTHORS))
def test_matches_authors_code(name):
    d = AUTHORS[name]
    p = read_instance(ROOT / "instances" / "generated" / f"{name}.txt").p
    assert evaluate_permutation(p, d["perm"])[1] == d["perm_ft"]
    orders = np.array(d["orders"])
    assert is_valid_orders(orders, p.shape[1])
    assert evaluate_nonpermutation(p, orders) == (d["final_ms"], d["final_ft"])
