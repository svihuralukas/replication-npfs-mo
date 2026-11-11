"""Testy MIP modelu (src/mip.py)."""

from pathlib import Path

import numpy as np

from evaluate import evaluate_permutation
from iga import iga
from instance import generate_instance, read_instance
from mip import solve_mip
from nonperm import nonperm_local_search

TESTS = Path(__file__).parent


def test_fig3_optimum():
    """Obr. 3: optimálny nepermutačný rozvrh má ΣC = 1191."""
    res = solve_mip(read_instance(TESTS / "fig3.txt").p, time_limit=60)
    assert res.optimal and res.ft == 1191


def test_fig1():
    """Obr. 1: optimum nesmie byť horšie než permutačný rozvrh z obrázka (ΣC = 31)."""
    p = np.array([[2, 2, 1], [2, 3, 0], [2, 0, 5], [3, 2, 0]])
    res = solve_mip(p, time_limit=30)
    assert res.optimal and res.ft <= evaluate_permutation(p, [0, 1, 2])[1]


def test_optimum_not_worse_than_heuristic():
    """Optimum nesmie byť horšie než IGA (a IGA nesmie byť lepšie než optimum)."""
    for seed in range(3):
        p = generate_instance(5, 4, 0.3, np.random.default_rng(seed)).p
        res = solve_mip(p, time_limit=60)
        heur = nonperm_local_search(p, iga(p, seed=1).perm).ft
        assert res.optimal and res.ft <= heur
        assert solve_mip(p, upper_bound=heur, time_limit=60).ft == res.ft
