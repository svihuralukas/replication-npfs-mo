"""
2. fáza algoritmu Ritt & Rossit (2024): lokálne prehľadávanie v NEPERMUTAČNOM priestore.
Vstupom je najlepšia permutácia z 1. fázy (src/iga.py), výstupom nepermutačný rozvrh
`orders` (m × n, riadok i = poradie jobov na stroji i). Výsledok IGA = 1. fáza + táto fáza.

Postup (Sekcia 4 a 3.2 článku):
    S := permutácia z 1. fázy (rovnaké poradie na všetkých strojoch)
    opakuj krok, kým sa ΣC zlepšuje (stop v prvom lokálnom minime – bez perturbácie):
        pre každý job j: vyber j zo všetkých strojov a vlož ho späť najlepším z vkladaní
            * straight      – na pozíciu k na všetkých strojoch,
            * anticipation  – na stroji l a ďalších o jednu pozíciu skôr (k na strojoch 1..l-1,
                              k-1 na strojoch l..m),
            * delay         – na stroji l a ďalších o jednu pozíciu neskôr (k-1 na strojoch
                              1..l-1, k na strojoch l..m; v článku zapísané ako k a k+1).
Opakovaným vkladaním vznikajú pseudo-joby (súvislé bloky operácií jobu), ktoré môžu byť
od seba aj vzdialenejšie než o jednu pozíciu.

Detaily, ktoré článok neuvádza a sú prevzaté z pôvodnej implementácie
(npfs-mo/src/heuristics.cpp, ENPSolution::insert_all_ft, shift_step) – v reporte ako doplnenia:
  * Krok local search berie joby podľa INDEXU jobu 0..n-1 (nie podľa pozície ako 1. fáza).
  * Vybratý job sa vkladá vždy, aj keď je nová hodnota horšia než pred vybratím (pôvodné
    umiestnenie nemusí byť medzi kandidátmi). Až na konci kroku sa porovná ΣC s hodnotou
    pred krokom; ak nie je ostro lepšia, celý krok sa zahodí a vráti sa pôvodný rozvrh.
  * Kritérium: min ΣC, potom min Cmax; pri úplnej zhode vyhráva kandidát vyhodnotený
    skôr. Poradie vyhodnocovania (pozície 1-indexované, n = počet jobov):
        A) k = n, n-1, ..., 1:  straight(k); ak k > 1: anticipation(k, l) pre l = m, m-1, ..., 2
        B) k = n, n-1, ..., 2:  delay(k, l) pre l = 2, 3, ..., m
       kde anticipation(k, l) = pozícia k na strojoch < l, k-1 na strojoch ≥ l
       a   delay(k, l)        = pozícia k-1 na strojoch < l, k na strojoch ≥ l.
  * Štart: ΣC permutácie z 1. fázy.

Naša implementácia vyhodnocuje kandidátov rovnako ako autori (úplný prepočet rozvrhu),
ale so zrýchlením, ktoré nemení výsledok:
  * prefixy – stav po strojoch 1..l-1 je pre anticipation(k, l) rovnaký ako pre straight(k)
    a pre delay(k, l) rovnaký ako pre straight(k-1); ukladáme ho a dopočítame len stroje l..m,
  * orezanie – po spracovaní strojov 1..i je dolná hranica ΣC súčet doterajších časov
    dokončenia jobov plus súčet všetkých zvyšných operácií na strojoch i+1..m (každý job
    musí ešte spracovať svoje zvyšné operácie za sebou); ak je ostro väčšia než doteraz
    najlepšia ΣC, kandidát nemôže vyhrať ani pri zhode, preto ho netreba dopočítať.
Správnosť overujú testy presnou zhodou s výsledkami programu autorov (tests/test_nonperm.py).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

try:
    from numba import njit
except ImportError:          # bez numby to funguje tiež, len oveľa pomalšie
    def njit(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        return lambda f: f

INF = np.iinfo(np.int64).max


# =========================================================================== numba jadro

@njit(cache=True)
def _evaluate_orders(p, orders):
    """(Cmax, ΣC) nepermutačného rozvrhu – rovnaké ako evaluate.evaluate_nonpermutation."""
    m, n = orders.shape
    done = np.zeros(p.shape[1], dtype=np.int64)
    for i in range(m):
        free = 0
        for q in range(n):
            jb = orders[i, q]
            pij = p[i, jb]
            if pij > 0:
                s = free if free > done[jb] else done[jb]
                free = s + pij
                done[jb] = free
    ft = 0
    ms = 0
    for q in range(n):
        c = done[orders[0, q]]
        ft += c
        if c > ms:
            ms = c
    return ms, ft


@njit(cache=True)
def _process_machine(p, i, row, nb, pos, job, done):
    """Spracuje stroj i: poradie = row[0:nb] s jobom `job` vloženým na index `pos`.
    `done[j]` = kedy job j dokončil poslednú operáciu; aktualizuje sa na mieste."""
    free = 0
    for q in range(nb + 1):
        if q < pos:
            jb = row[q]
        elif q == pos:
            jb = job
        else:
            jb = row[q - 1]
        pij = p[i, jb]
        if pij > 0:
            s = free if free > done[jb] else done[jb]
            free = s + pij
            done[jb] = free


@njit(cache=True)
def _suffix(p, base, nb, i0, pos, job, done, bound, rest):
    """Dopočíta stroje i0..m-1 s jobom na indexe `pos`, začína zo stavu `done` (mení ho).
    rest[i] = súčet procesných časov všetkých jobov na strojoch i..m-1.
    Vráti (ok, ΣC, Cmax); ok = False, ak dolná hranica ΣC prekročí `bound` (orezanie)."""
    m = base.shape[0]
    n = nb + 1
    for i in range(i0, m):
        _process_machine(p, i, base[i], nb, pos, job, done)
        lb = rest[i + 1]
        for q in range(n):
            lb += done[q]
        if lb > bound:
            return False, lb, 0
    ft = 0
    ms = 0
    for q in range(n):
        ft += done[q]
        if done[q] > ms:
            ms = done[q]
    return True, ft, ms


@njit(cache=True)
def _rest_work(p):
    """rest[i] = súčet procesných časov všetkých jobov na strojoch i..m-1 (rest[m] = 0)."""
    m, n = p.shape
    rest = np.zeros(m + 1, dtype=np.int64)
    for i in range(m - 1, -1, -1):
        rest[i] = rest[i + 1]
        for j in range(n):
            rest[i] += p[i, j]
    return rest


@njit(cache=True)
def _best_np_insertion(p, base, job, pre, buf, rest):
    """Najlepšie vloženie jobu do rozvrhu `base` (m × (n-1), job v ňom nie je).

    Vráti (k, code, ΣC, Cmax): k = 1-indexovaná pozícia, code = 0 straight,
    code = -l anticipation na stroji l, code = +l delay na stroji l (stroje 1-indexované).
    `pre` (n+1, m+1, n) a `buf` (n) sú pracovné polia, `rest` viď _suffix."""
    m, nb = base.shape
    n = nb + 1
    best_k = 0
    best_code = 0
    best_ft = INF
    best_ms = INF

    # A) straight(k) a anticipation(k, l)
    for k in range(n, 0, -1):
        for q in range(n):
            pre[k, 0, q] = 0
        for i in range(m):
            for q in range(n):
                pre[k, i + 1, q] = pre[k, i, q]
            _process_machine(p, i, base[i], nb, k - 1, job, pre[k, i + 1])
        ft = 0
        ms = 0
        for q in range(n):
            ft += pre[k, m, q]
            if pre[k, m, q] > ms:
                ms = pre[k, m, q]
        if ft < best_ft or (ft == best_ft and ms < best_ms):
            best_k, best_code, best_ft, best_ms = k, 0, ft, ms
        if k == 1:
            break
        for l in range(m, 1, -1):
            for q in range(n):
                buf[q] = pre[k, l - 1, q]
            ok, ft, ms = _suffix(p, base, nb, l - 1, k - 2, job, buf, best_ft, rest)
            if ok and (ft < best_ft or (ft == best_ft and ms < best_ms)):
                best_k, best_code, best_ft, best_ms = k, -l, ft, ms

    # B) delay(k, l): stroje < l na pozícii k-1 (prefix zo straight(k-1)), stroje ≥ l na k
    for k in range(n, 1, -1):
        for l in range(2, m + 1):
            for q in range(n):
                buf[q] = pre[k - 1, l - 1, q]
            ok, ft, ms = _suffix(p, base, nb, l - 1, k - 1, job, buf, best_ft, rest)
            if ok and (ft < best_ft or (ft == best_ft and ms < best_ms)):
                best_k, best_code, best_ft, best_ms = k, l, ft, ms

    return best_k, best_code, best_ft, best_ms


@njit(cache=True)
def _apply_insertion(base, job, k, code, out):
    """Zapíše do `out` (m × n) rozvrh `base` s jobom vloženým podľa (k, code)."""
    m, nb = base.shape
    for i in range(m):
        mi = i + 1                         # 1-indexovaný stroj
        if code == 0:
            pos = k - 1
        elif code < 0:                     # anticipation na stroji -code
            pos = k - 1 if mi < -code else k - 2
        else:                              # delay na stroji code
            pos = k - 2 if mi < code else k - 1
        for q in range(pos):
            out[i, q] = base[i, q]
        out[i, pos] = job
        for q in range(pos, nb):
            out[i, q + 1] = base[i, q]


@njit(cache=True)
def _remove_job(orders, job, base):
    """Do `base` (m × (n-1)) zapíše `orders` bez jobu `job` (poradie ostatných zachová)."""
    m, n = orders.shape
    for i in range(m):
        c = 0
        for q in range(n):
            if orders[i, q] != job:
                base[i, c] = orders[i, q]
                c += 1


@njit(cache=True)
def _np_shift_step(p, orders, of):
    """Jeden krok: každý job (podľa indexu) vyberie a vloží najlepšie. Ak výsledok nie je
    ostro lepší než `of`, vráti pôvodný rozvrh. Vráti (nové ΣC, zlepšilo sa?)."""
    m, n = orders.shape
    saved = orders.copy()
    base = np.empty((m, n - 1), dtype=np.int64)
    pre = np.empty((n + 1, m + 1, n), dtype=np.int64)
    buf = np.empty(n, dtype=np.int64)
    rest = _rest_work(p)
    ft = of
    for job in range(n):
        _remove_job(orders, job, base)
        k, code, ft, ms = _best_np_insertion(p, base, job, pre, buf, rest)
        _apply_insertion(base, job, k, code, orders)
    if ft >= of:
        orders[:, :] = saved
        return of, False
    return ft, True


@njit(cache=True)
def _np_local_search(p, orders, of):
    steps = 0
    while True:
        of, improved = _np_shift_step(p, orders, of)
        if not improved:
            return of, steps
        steps += 1


# =========================================================================== verejné funkcie

@dataclass
class NonpermResult:
    orders: np.ndarray       # m × n, riadok i = poradie jobov na stroji i
    ft: int                  # ΣC výsledného rozvrhu
    ms: int                  # Cmax výsledného rozvrhu
    steps: int               # počet zlepšujúcich krokov local search
    time: float              # čas behu v sekundách


def best_np_insertion(p: np.ndarray, base: np.ndarray, job: int) -> tuple[int, int, int, int]:
    """Python obal pre testy: (k, code, ΣC, Cmax) najlepšieho vloženia jobu do `base`."""
    base = np.ascontiguousarray(base, dtype=np.int64)
    m, nb = base.shape
    n = nb + 1
    pre = np.empty((n + 1, m + 1, n), dtype=np.int64)
    buf = np.empty(n, dtype=np.int64)
    p = np.ascontiguousarray(p, dtype=np.int64)
    k, code, ft, ms = _best_np_insertion(p, base, job, pre, buf, _rest_work(p))
    return int(k), int(code), int(ft), int(ms)


def apply_insertion(base: np.ndarray, job: int, k: int, code: int) -> np.ndarray:
    base = np.ascontiguousarray(base, dtype=np.int64)
    out = np.empty((base.shape[0], base.shape[1] + 1), dtype=np.int64)
    _apply_insertion(base, job, k, code, out)
    return out


def nonperm_local_search(p: np.ndarray, perm) -> NonpermResult:
    """2. fáza: local search s vkladaním straight / anticipation / delay, štart z permutácie
    `perm` (výsledok 1. fázy), stop v prvom lokálnom minime."""
    t0 = time.perf_counter()
    p = np.ascontiguousarray(p, dtype=np.int64)
    m = p.shape[0]
    orders = np.tile(np.asarray(perm, dtype=np.int64), (m, 1))
    of = int(_evaluate_orders(p, orders)[1])
    of, steps = _np_local_search(p, orders, of)
    ms, ft = _evaluate_orders(p, orders)
    assert ft == of
    return NonpermResult(orders=orders, ft=int(ft), ms=int(ms), steps=int(steps),
                         time=time.perf_counter() - t0)

