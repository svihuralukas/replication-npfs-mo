"""
Konštrukčná heuristika NPS-set (Pugazhendhi et al. 2003) – ablácia "IGA+NPS-set" (Tab. 6 článku):
2. fáza IGA sa nahradí touto heuristikou aplikovanou na permutáciu z 1. fázy.

Postup (Sekcia 4.1 a Algoritmus 2 článku):
    pre joby j v poradí permutácie π:
        pre stroje i = 1..m (chýbajúce operácie preskočí):
            vlož operáciu o_ij do najskoršej voľnej medzery (idle slot) na stroji i,
            ktorá začína / pokračuje po aktuálnom dokončení jobu j a je dosť veľká.
Operácia sa vloží len tam, kde nič nezdrží (medzera ≥ p_ij), preto platí ΣC(σ) ≤ ΣC(π):
v najhoršom prípade operácia skončí na konci stroja ako v permutačnom rozvrhu.

Autori (npfs-mo/src/solution.cpp PSolution::evaluateNPSset, holes.cpp) držia medzery
v množine zoradenej podľa dĺžky a vyberajú medzeru s najmenším začiatkom, do ktorej sa
operácia zmestí po čase pripravenosti jobu (hlist::earliest). Medzery sú disjunktné, takže
je to to isté ako najskorší prípustný začiatok operácie – ten tu hľadáme priamo prechodom
obsadených intervalov stroja zoradených podľa začiatku (jednoduchšie, výsledok rovnaký;
overené testom presnej zhody s programom autorov v tests/test_nps_set.py).
"""

from __future__ import annotations

import numpy as np

try:
    from numba import njit
except ImportError:          # bez numby to funguje tiež, len pomalšie
    import warnings
    warnings.warn("numba nie je nainštalovaná – výpočet beží v čistom Pythone, asi 100× pomalšie "
                  "(pip install -r requirements.txt)", stacklevel=2)

    def njit(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        return lambda f: f


@njit(cache=True)
def _nps_set(p, perm, start):
    """Vráti (Cmax, ΣC) a do `start` (m × n) zapíše začiatky operácií (-1 = chýbajúca)."""
    m = p.shape[0]
    n = perm.shape[0]
    # obsadené intervaly na strojoch, zoradené podľa začiatku: bs[i, :cnt[i]], be[i, :cnt[i]]
    bs = np.empty((m, n), dtype=np.int64)
    be = np.empty((m, n), dtype=np.int64)
    cnt = np.zeros(m, dtype=np.int64)
    ms = 0
    ft = 0
    for q in range(n):
        j = perm[q]
        ct = 0                                   # kedy je job pripravený na ďalšiu operáciu
        for i in range(m):
            pij = p[i, j]
            if pij == 0:
                start[i, j] = -1
                continue
            # najskorší začiatok t >= ct, pri ktorom [t, t + pij) neprekryje obsadený interval
            t = ct
            idx = cnt[i]                          # kam sa interval zaradí
            for r in range(cnt[i]):
                if be[i, r] <= t:                 # interval končí pred t – nevadí
                    continue
                if bs[i, r] >= t + pij:           # operácia sa zmestí pred tento interval
                    idx = r
                    break
                t = be[i, r]                      # prekrytie – skús hneď za intervalom
            for r in range(cnt[i], idx, -1):      # vloženie intervalu na pozíciu idx
                bs[i, r] = bs[i, r - 1]
                be[i, r] = be[i, r - 1]
            bs[i, idx] = t
            be[i, idx] = t + pij
            cnt[i] += 1
            start[i, j] = t
            ct = t + pij
        ft += ct
        if ct > ms:
            ms = ct
    return ms, ft


def nps_set(p: np.ndarray, perm) -> tuple[int, int]:
    """NPS-set z permutácie `perm`: vráti (Cmax, ΣC) výsledného nepermutačného rozvrhu."""
    ms, ft, _ = nps_set_schedule(p, perm)
    return ms, ft


def nps_set_schedule(p: np.ndarray, perm) -> tuple[int, int, np.ndarray]:
    """Ako nps_set, navyše vráti `orders` (m × n): poradie jobov na strojoch podľa začiatkov
    operácií (joby s chýbajúcou operáciou sú na konci riadku – na výsledok nemajú vplyv)."""
    p = np.ascontiguousarray(p, dtype=np.int64)
    perm = np.asarray(perm, dtype=np.int64)
    m, n = p.shape
    start = np.empty((m, n), dtype=np.int64)
    ms, ft = _nps_set(p, perm, start)
    big = np.iinfo(np.int64).max
    orders = np.empty((m, len(perm)), dtype=np.int64)
    for i in range(m):
        key = np.where(start[i, perm] >= 0, start[i, perm], big)
        orders[i] = perm[np.argsort(key, kind="stable")]
    return int(ms), int(ft), orders
