"""Testy načítania a generovania inštancií. Spustenie: python -m pytest tests/"""

from pathlib import Path

import numpy as np
import pytest

from instance import (Instance, generate_instance, instance_rng, num_missing_for,
                      read_instance, write_instance)

TESTS = Path(__file__).parent

# Inštancia z obr. 3 článku (riadky = stroje M1..M5, stĺpce = joby J1..J5, 0 = chýba)
FIG3 = np.array([[79, 60, 6, 61, 17],
                 [39, 25, 32, 70, 0],
                 [71, 16, 47, 0, 21],
                 [77, 38, 9, 2, 91],
                 [0, 0, 49, 0, 44]])


def test_read_fig3():
    inst = read_instance(TESTS / "fig3.txt")
    assert (inst.m, inst.n) == (5, 5)
    assert np.array_equal(inst.p, FIG3)
    assert inst.num_missing() == 5            # 0.2 * 25 = 5
    assert inst.num_pseudo_jobs() == 7        # zhodné s ich table2.csv (pj = 7)


def test_write_read_roundtrip(tmp_path):
    inst = Instance(p=FIG3.copy(), r=0.2)
    write_instance(inst, tmp_path / "x.txt")
    again = read_instance(tmp_path / "x.txt")
    assert np.array_equal(again.p, inst.p) and again.r == inst.r


@pytest.mark.parametrize("n,m,r,expected", [
    (5, 5, 0.2, 5), (5, 5, 0.3, 8), (5, 5, 0.4, 10),   # 7.5 -> 8 (zaokrúhlenie nahor pri ,5)
    (10, 5, 0.3, 15), (100, 30, 0.4, 1200),
])
def test_num_missing(n, m, r, expected):
    assert num_missing_for(n, m, r) == expected


@pytest.mark.parametrize("n,m,r", [(5, 5, 0.3), (20, 10, 0.2), (50, 30, 0.4)])
def test_generate_properties(n, m, r):
    inst = generate_instance(n, m, r, instance_rng(1, r, n, m, 0))
    assert inst.p.shape == (m, n)
    assert inst.num_missing() == num_missing_for(n, m, r)
    present = inst.p[inst.p > 0]
    assert present.min() >= 1 and present.max() <= 99


def test_generate_reproducible():
    a = generate_instance(20, 10, 0.3, instance_rng(7, 0.3, 20, 10, 3))
    b = generate_instance(20, 10, 0.3, instance_rng(7, 0.3, 20, 10, 3))
    c = generate_instance(20, 10, 0.3, instance_rng(7, 0.3, 20, 10, 4))
    assert np.array_equal(a.p, b.p)
    assert not np.array_equal(a.p, c.p)
