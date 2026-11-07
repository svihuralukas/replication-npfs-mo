"""Konštruktívna heuristika NPS-set (Pugazhendhi et al., 2003; Ritt & Rossit, 2024, Algoritmus 2).

Používa sa v ablácii IGA+NPS-set (Tab. 6): permutácia z fázy 1 sa prevedie na nepermutačný
rozvrh vkladaním operácií do najskoršej voľnej medzery, ktorá je dosť veľká a začína
po aktuálnom čase dokončenia jobu. Výsledok nie je horší ako vstupná permutácia.
"""

import numpy as np

from npfsmo.instance import Instance


def nps_set(inst: Instance, perm: list[int]) -> np.ndarray:
    """Vráti maticu (m, n) časov dokončenia nepermutačného rozvrhu."""
    raise NotImplementedError
