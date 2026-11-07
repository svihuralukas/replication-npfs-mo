"""Testy 1. fázy algoritmu (src/iga.py) – kroky 3 a 4. Spustenie: python -m pytest tests/"""

import csv
import itertools
from pathlib import Path

import numpy as np
import pytest

from evaluate import evaluate_permutation
from iga import (IGAParams, best_insertion, construct, destruction_size, iga,
                 iteration_limit, perturb, shift_local_search, temperature)
from instance import read_instance

TESTS = Path(__file__).parent
GEN = TESTS.parent / "instances" / "generated"


def load(name):
    return read_instance(GEN / f"{name}.txt").p


# ---------------------------------------------------------------- vkladanie na najlepšiu pozíciu

@pytest.mark.parametrize("name", ["0.2_05_05_00", "0.4_10_20_05", "0.3_20_10_07"])
def test_best_insertion_matches_brute_force(name):
    """Najlepšia pozícia = min ΣC, potom min Cmax, pri zhode najzadnejšia pozícia."""
    p = load(name)
    rng = np.random.default_rng(3)
    n = p.shape[1]
    for _ in range(15):
        perm = list(rng.permutation(n))
        job, partial = perm[-1], perm[:-1]
        candidates = []
        for pos in range(len(partial) + 1):
            ms, ft = evaluate_permutation(p, partial[:pos] + [job] + partial[pos:])
            candidates.append((ft, ms, -pos))          # -pos: pri zhode vyhrá väčšia pozícia
        ft, ms, neg_pos = min(candidates)
        assert best_insertion(p, partial, job) == (-neg_pos, ft, ms)


# ---------------------------------------------------------------- zhoda s kódom autorov
# tests/data/authors_deterministic.csv: ΣC po konštrukcii a po prvom local search
# z programu autorov (reference/run_authors.py) na 144 našich inštanciách (n = 5..100).
# Obe časti sú deterministické, preto musia sedieť PRESNE.

with open(TESTS / "data" / "authors_deterministic.csv") as f:
    AUTHORS_DET = list(csv.DictReader(f))


def test_construction_and_local_search_match_authors():
    mismatches = []
    for row in AUTHORS_DET:
        p = load(row["instance"])
        seq, c_ft, _ = construct(p)
        _, ls_ft, _, _ = shift_local_search(p, seq)
        if (c_ft, ls_ft) != (int(row["construction_ft"]), int(row["ls_ft"])):
            mismatches.append((row["instance"], c_ft, ls_ft, row["construction_ft"], row["ls_ft"]))
    assert not mismatches, mismatches


def test_parameters_match_authors():
    """Hodnoty z riadku PARAM programu npfsmo (d, limit iterácií)."""
    params = IGAParams()
    assert [destruction_size(n, params) for n in (5, 10, 20, 100)] == [4, 8, 8, 8]
    assert [iteration_limit(n, params) for n in (5, 10, 20, 30, 50, 100)] == \
        [3000, 1500, 750, 500, 300, 150]
    p = read_instance(TESTS / "fig3.txt").p
    assert temperature(p, params) == pytest.approx(0.234375 * p.sum() / 25 / 10)


# ---------------------------------------------------------------- vnútorná konzistencia

def test_local_search_never_worsens_and_is_consistent():
    p = load("0.3_20_10_07")
    rng = np.random.default_rng(5)
    for _ in range(5):
        perm = rng.permutation(p.shape[1])
        start_ft = evaluate_permutation(p, perm)[1]
        seq, ft, ms, _ = shift_local_search(p, perm)
        assert ft <= start_ft
        assert evaluate_permutation(p, seq) == (ms, ft)


def test_perturb_keeps_valid_permutation():
    p = load("0.4_20_30_08")
    rng = np.random.default_rng(9)
    seq, _, _ = construct(p)
    for _ in range(10):
        seq, ft, ms = perturb(p, seq, 8, rng)
        assert sorted(seq) == list(range(p.shape[1]))
        assert evaluate_permutation(p, seq) == (ms, ft)


@pytest.mark.parametrize("name", ["0.2_10_05_03", "0.4_30_10_00"])
def test_iga_result_is_consistent_and_reproducible(name):
    p = load(name)
    params = IGAParams(iter_limit=30)
    a = iga(p, seed=11, params=params)
    b = iga(p, seed=11, params=params)
    assert sorted(a.perm) == list(range(p.shape[1]))
    assert evaluate_permutation(p, a.perm) == (a.ms, a.ft)
    assert a.ft <= a.ls_ft <= a.construction_ft
    assert np.array_equal(a.perm, b.perm) and a.ft == b.ft      # rovnaký seed = rovnaký výsledok
    assert a.iterations == 31                                    # limit + 1, ako autori
    bests = [h[2] for h in a.history]
    assert bests == sorted(bests, reverse=True)                  # história len zlepšuje


# ---------------------------------------------------------------- krok 3: hrubá sila

N5 = [f"{r}_05_{m:02d}_{i:02d}" for r in ("0.2", "0.3", "0.4") for m in (5, 10, 20, 30) for i in range(3)]


@pytest.mark.parametrize("name", N5)
def test_iga_finds_permutation_optimum_for_n5(name):
    """Pre n = 5 overíme všetkých 120 permutácií – IGA0 musí nájsť optimum."""
    p = load(name)
    opt = min(evaluate_permutation(p, perm)[1] for perm in itertools.permutations(range(5)))
    assert iga(p, seed=1).ft == opt


def test_iga_finds_permutation_optimum_for_n8():
    """n = 8: 40 320 permutácií, overené hrubou silou na jednej inštancii."""
    rng = np.random.default_rng(42)
    from instance import generate_instance
    p = generate_instance(8, 5, 0.3, rng).p
    opt = min(evaluate_permutation(p, perm)[1] for perm in itertools.permutations(range(8)))
    assert iga(p, seed=1, params=IGAParams(iter_limit=500)).ft == opt
