"""Vyhodnotenie rozvrhu: časy dokončenia, sum C_j a C_max s chýbajúcimi operáciami.

Rekurzia časov dokončenia: Ritt & Rossit (2024), sekcia 1; pseudo-joby: sekcia 3.1.
Chýbajúca operácia sa nevykonáva – job pokračuje na ďalšiu nechýbajúcu operáciu,
akonáhle je príslušný stroj voľný.
"""

import numpy as np

from npfsmo import PseudoJob
from npfsmo.instance import Instance


def permutation_to_pseudo_jobs(perm: list[int], m: int) -> list[PseudoJob]:
    """Permutačný rozvrh ako postupnosť kompletných jobov ``(j, 0, m - 1)``."""
    raise NotImplementedError


def completion_times(inst: Instance, seq: list[PseudoJob]) -> np.ndarray:
    """Matica (m, n) časov dokončenia; pri chýbajúcich operáciách NaN."""
    raise NotImplementedError


def total_completion_time(inst: Instance, seq: list[PseudoJob]) -> int:
    """sum_j max_i C_ij cez nechýbajúce operácie (účelová funkcia)."""
    raise NotImplementedError


def makespan(inst: Instance, seq: list[PseudoJob]) -> int:
    """C_max – používa sa na rozhodovanie remíz pri vkladaní (sekcia 4)."""
    raise NotImplementedError
