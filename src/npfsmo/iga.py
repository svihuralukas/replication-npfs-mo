"""Fáza 1: iterated greedy v permutačnom priestore (Ritt & Rossit, 2024, sekcia 4, Algoritmus 1).

- Lokálne prehľadávanie: shift – každý job vybrať a vložiť na najlepšiu z n pozícií
  (remízy: menší C_max, potom menší index jobu); opakovať, kým sa nič nezlepší.
- Perturbácia: odstrániť d náhodných jobov, d = min(8, 0.8 n), a vložiť ich späť greedy
  (Ruiz & Stützle, 2007).
- Akceptácia: Metropolis, T = alpha * p_mean / 10, alpha = 0.234375 (Metropolis et al., 1953).
- Stop: 15000 / n iterácií.
"""

from dataclasses import dataclass

import numpy as np

from npfsmo.instance import Instance


@dataclass
class IGAResult:
    permutation: list[int]
    value: int
    history: list[int]  # najlepšia sum C_j po každej iterácii (konvergencia)
    seconds: float


def iga_phase1(
    inst: Instance,
    rng: np.random.Generator,
    iterations: int,
    d: int,
    alpha: float,
) -> IGAResult:
    raise NotImplementedError
