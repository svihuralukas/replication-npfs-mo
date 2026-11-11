"""
MIP model pre nepermutačný flow shop s chýbajúcimi operáciami a ΣC_j (Sekcia 3.3 článku,
rovnice (2)–(11) s účelovou funkciou ΣC namiesto Cmax). Rieši sa voľným solverom HiGHS
(scipy.optimize.milp) namiesto CPLEX-u, ktorý použili autori.

Premenné:
    C_ij ≥ 0      čas dokončenia existujúcej operácie o_ij
    y_ijk ∈ {0,1} pre j < k: 1, ak je job j na stroji i pred jobom k (obe operácie existujú)
Obmedzenia:
    C_ij ≥ p_ij                                  prvá existujúca operácia jobu
    C_ij ≥ C_i'j + p_ij                          i' = predchádzajúca existujúca operácia jobu j (4)
    C_ik ≥ C_ij + p_ik − M (1 − y_ijk)           j pred k na stroji i                (9), (10)
    C_ij ≥ C_ik + p_ij − M y_ijk                 k pred j na stroji i
Účelová funkcia: Σ_j C_{last(j), j}. M = Σ p_ij.

Použitie v projekte: presné optimá pre malé inštancie (n = 5), aby BKV pre ne zodpovedali
článku (autori ich vyriešili MIP-om všetky optimálne, Tab. 5) – len doplnková analýza.
Autori model štartovali z riešenia 1. fázy IGA; scipy.milp počiatočné riešenie neprijíma,
preto namiesto toho pridávame hornú hranicu ΣC ≤ UB (napr. ΣC z IGA), čo má podobný účinok
na orezávanie stromu.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix


@dataclass
class MIPResult:
    ft: float | None          # najlepšie nájdené ΣC (None, ak sa nenašlo prípustné riešenie)
    bound: float | None       # dolná hranica
    optimal: bool
    time: float
    status: str


def solve_mip(p: np.ndarray, upper_bound: int | None = None, time_limit: float = 60.0) -> MIPResult:
    m, n = p.shape
    ops = [(i, j) for i in range(m) for j in range(n) if p[i, j] > 0]
    cidx = {op: k for k, op in enumerate(ops)}
    pairs = [(i, j, k) for i in range(m) for j in range(n) for k in range(j + 1, n)
             if p[i, j] > 0 and p[i, k] > 0]
    nc, ny = len(ops), len(pairs)
    nv = nc + ny
    M = int(p.sum())

    rows = []                                  # (koeficienty {var: coef}, dolná hranica)
    lb = np.zeros(nv)
    for j in range(n):
        prev = None
        for i in range(m):
            if p[i, j] == 0:
                continue
            if prev is None:
                lb[cidx[(i, j)]] = p[i, j]
            else:
                rows.append(({cidx[(i, j)]: 1, cidx[(prev, j)]: -1}, p[i, j]))
            prev = i
    for t, (i, j, k) in enumerate(pairs):
        y = nc + t
        # C_ik − C_ij − M y ≥ p_ik − M
        rows.append(({cidx[(i, k)]: 1, cidx[(i, j)]: -1, y: -M}, p[i, k] - M))
        # C_ij − C_ik + M y ≥ p_ij
        rows.append(({cidx[(i, j)]: 1, cidx[(i, k)]: -1, y: M}, p[i, j]))

    c = np.zeros(nv)
    for j in range(n):
        last = max((i for i in range(m) if p[i, j] > 0), default=None)
        if last is not None:
            c[cidx[(last, j)]] = 1

    A = lil_matrix((len(rows) + (upper_bound is not None), nv))
    lo = np.empty(A.shape[0])
    hi = np.full(A.shape[0], np.inf)
    for r, (coef, b) in enumerate(rows):
        for v, a in coef.items():
            A[r, v] = a
        lo[r] = b
    if upper_bound is not None:
        A[len(rows), :] = c
        lo[-1], hi[-1] = -np.inf, upper_bound

    integrality = np.r_[np.zeros(nc), np.ones(ny)]
    ub = np.r_[np.full(nc, M), np.ones(ny)]
    t0 = time.perf_counter()
    res = milp(c, constraints=LinearConstraint(A.tocsr(), lo, hi), integrality=integrality,
               bounds=Bounds(lb, ub), options={"time_limit": time_limit, "disp": False})
    elapsed = time.perf_counter() - t0
    ft = round(res.fun) if res.x is not None else None
    bound = getattr(res, "mip_dual_bound", None)
    return MIPResult(ft=ft, bound=bound, optimal=res.status == 0, time=elapsed, status=res.message)
