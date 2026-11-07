"""Cieľové testy pre evaluate.py na príkladoch z článku Ritt & Rossit (2024).

Kým nie je evaluate.py implementovaný, tieto testy padajú – to je zámer.
"""

import numpy as np

from npfsmo.evaluate import makespan, permutation_to_pseudo_jobs, total_completion_time
from npfsmo.instance import Instance

X = -1  # chýbajúca operácia


def make_instance(name: str, rows: list[list[int]]) -> Instance:
    p = np.array(rows)
    return Instance(name=name, p=np.where(p == X, 0, p), present=p != X)


# Obr. 1: 4 stroje (riadky) x 3 joby (stĺpce).
FIG1 = make_instance("fig1", [
    [2, 2, 1],
    [2, 3, X],
    [2, X, 5],
    [3, 2, X],
])

# Obr. 3: inštancia "00" s hustotou 0.2, n = m = 5 (Henneberg & Neufeld, 2016).
FIG3 = make_instance("fig3", [
    [79, 60, 6, 61, 17],
    [39, 25, 32, 70, X],
    [71, 16, 47, X, 21],
    [77, 38, 9, 2, 91],
    [X, X, 49, X, 44],
])


def test_fig1_missing_operations():
    seq = permutation_to_pseudo_jobs([0, 1, 2], FIG1.m)
    assert total_completion_time(FIG1, seq) == 31
    assert makespan(FIG1, seq) == 11


def test_fig1_zero_time_operations_are_worse():
    zero = FIG1.as_zero_time()
    seq = permutation_to_pseudo_jobs([0, 1, 2], zero.m)
    assert total_completion_time(zero, seq) == 32
    assert makespan(zero, seq) == 12


def test_fig3_optimal_nonpermutation_schedule():
    # J5, J3[1,3], J2, J3[4,5], J4, J1 (v článku indexované od 1).
    seq = [(4, 0, 4), (2, 0, 2), (1, 0, 4), (2, 3, 4), (3, 0, 4), (0, 0, 4)]
    assert total_completion_time(FIG3, seq) == 1191
