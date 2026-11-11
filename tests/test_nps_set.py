"""Testy konštrukčnej heuristiky NPS-set (src/nps_set.py)."""

import json
from pathlib import Path

import numpy as np
import pytest

from evaluate import evaluate_nonpermutation, evaluate_permutation, is_valid_orders
from iga import construct
from instance import generate_instance, read_instance
from nps_set import nps_set, nps_set_schedule

TESTS = Path(__file__).parent
ROOT = TESTS.parent
AUTHORS = json.loads((TESTS / "data" / "authors_solutions.json").read_text())


@pytest.mark.parametrize("name", sorted(AUTHORS))
def test_matches_authors(name):
    """Presná zhoda s PSolution::evaluateNPSset autorov – na permutácii z 1. fázy
    aj na štartovacej konštrukcii."""
    p = read_instance(ROOT / "instances" / "generated" / f"{name}.txt").p
    a = AUTHORS[name]
    assert nps_set(p, a["perm"]) == (a["nps_ms"], a["nps_ft"])
    assert nps_set(p, construct(p)[0])[1] == a["nps0_ft"]


def test_fills_idle_slot():
    """Malý príklad: J2 nemá operáciu na M2, preto môže na M3 predbehnúť J1,
    ktorý čaká na dlhú operáciu na M2 – vloží sa do medzery [0, 6) na M3."""
    #             J1 J2 J3
    p = np.array([[1, 1, 1],     # M1
                  [5, 0, 1],     # M2
                  [1, 1, 1]])    # M3
    perm = [0, 1, 2]
    assert evaluate_permutation(p, perm) == (9, 7 + 8 + 9)
    ms, ft, orders = nps_set_schedule(p, perm)
    # J2 na M3 v [2, 3) – pred J1 (ten na M3 začne až v 6); J3 potom ako v permutácii.
    assert orders[2].tolist() == [1, 0, 2]
    assert (ms, ft) == (8, 7 + 3 + 8)
    assert evaluate_nonpermutation(p, orders) == (ms, ft)


@pytest.mark.parametrize("seed", range(10))
def test_never_worse_and_consistent(seed):
    """ΣC(σ) ≤ ΣC(π) (Algoritmus 2) a poradie podľa začiatkov dá rovnaký rozvrh."""
    rng = np.random.default_rng(seed)
    n, m = int(rng.integers(3, 15)), int(rng.integers(2, 10))
    p = generate_instance(n, m, [0.2, 0.3, 0.4][seed % 3], np.random.default_rng(100 + seed)).p
    perm = rng.permutation(n)
    ms, ft, orders = nps_set_schedule(p, perm)
    assert is_valid_orders(orders, n)
    assert ft <= evaluate_permutation(p, perm)[1]
    assert evaluate_nonpermutation(p, orders) == (ms, ft)


def test_no_missing_operations_not_worse():
    """Aj bez chýbajúcich operácií NPS-set nesmie byť horší než permutácia."""
    p = np.array([[3, 2, 4], [2, 5, 1], [4, 1, 3]])
    perm = [0, 1, 2]
    assert nps_set(p, perm)[1] <= evaluate_permutation(p, perm)[1]
