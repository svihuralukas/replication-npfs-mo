"""
1. fáza algoritmu Ritt & Rossit (2024): Iterated Greedy Algorithm (IGA) v priestore
PERMUTÁCIÍ pre F | skip | ΣC_j. Výsledok tejto fázy samotnej je ablácia "IGA0" (Tab. 6).

Postup (Sekcia 4 článku, Algoritmus 1):
    S  := konštrukcia (zoradenie jobov + postupné vkladanie)   – detail z kódu autorov
    S  := shift_local_search(S)
    opakuj (limit iterácií):
        S' := perturbácia(S, d)      deštrukcia d náhodných jobov + ich spätné vloženie
        S' := shift_local_search(S')
        S  := akceptácia(S, S')      Metropolisovo kritérium
    vráť najlepšie nájdené riešenie

Detaily, ktoré článok neuvádza a sú prevzaté z pôvodnej implementácie
(npfs-mo/src/npfsmo.cpp a heuristics.cpp) – v reporte uvedené ako doplnenia:
  * Štartovacie riešenie: joby zoradené podľa celkového času spracovania Σ_i p_ij
    zostupne (pri zhode menší index), potom vkladané jeden po druhom na najlepšiu pozíciu.
  * Najlepšia pozícia pri vkladaní: min ΣC, pri zhode min Cmax; pri úplnej zhode
    vyhráva pozícia skúmaná ako prvá – autori skúmajú pozície od konca, teda
    vyhráva NAJZADNEJŠIA z rovnocenných pozícií.
  * Shift local search postupne berie job na POZÍCII 1, 2, ..., n (nie job s indexom 1..n),
    vyberie ho a vloží na najlepšiu pozíciu (pôvodná pozícia je medzi kandidátmi,
    takže riešenie sa nezhorší). Krok sa opakuje, kým sa ΣC zlepšuje.
  * d = min(8, ceil(0.8 n)) – v kóde (8n + 9) // 10.
  * T = α · p̄ / 10, p̄ = Σ p_ij / (n m) (chýbajúce operácie sa počítajú ako 0).
  * Limit iterácií = max(1, int(iter_factor · 150000 / n)); pri iter_factor = 0.1
    je to 15000/n ako v článku. Cyklus beží, kým počet krokov NEPREKROČÍ limit,
    t. j. vykoná sa limit + 1 iterácií.
  * Akceptácia: nové najlepšie riešenie sa vždy prijme; inak sa prijme, ak je
    lepšie než pred perturbáciou alebo s pravdepodobnosťou exp(-(ΣC' - ΣC)/T).

Výber odstránených jobov pri perturbácii: článok hovorí o d náhodných jobov, preto predvolene
(sampling="uniform") vyberáme d pozícií rovnomerne. Program autorov (random.hpp, sample_floyd)
používa Floydov algoritmus s posunom o jedna: v kroku u losuje z {0, ..., u-1} namiesto
{0, ..., u}, takže posledné pozície permutácie sa vyberajú zriedkavejšie (pri n = 100, d = 8
asi 0,071 namiesto 0,080). Voľba sampling="autori" tento výber napodobňuje – slúži len na
experiment, či tento detail vysvetľuje malý rozdiel medzi implementáciami (nevysvetľuje ho,
results/original/analysis/summary.txt).

Implementácia (naša): výpočtové jadro (vkladanie, local search) je zrýchlené cez numba.
Náhodné rozhodnutia sa robia v Pythone cez numpy Generator so zadaným seedom,
takže beh je plne reprodukovateľný. Generátor náhodných čísel je iný ako v C++
kóde autorov, preto pri rovnakom seede nevznikne rovnaký priebeh – porovnávame
štatisticky cez viac seedov.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np

try:
    from numba import njit
except ImportError:          # bez numby to funguje tiež, len oveľa pomalšie
    def njit(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        return lambda f: f


# =========================================================================== numba jadro

@njit(cache=True)
def _best_insertion(p, seq, L, job):
    """Nájde najlepšiu pozíciu pre `job` v čiastočnej permutácii seq[0:L].

    Vráti (pos, ΣC, Cmax): job sa má vložiť pred seq[pos] (pos = L znamená na koniec).
    Kritérium: min ΣC, potom min Cmax; pri zhode vyhráva prvá skúmaná pozícia,
    pozície skúmame od konca (pos = L, L-1, ..., 0) – rovnako ako autori."""
    m = p.shape[0]
    # heads[k, i] = kedy sa uvoľní stroj i po spracovaní prvých k jobov
    # prefix[k]   = ΣC prvých k jobov
    heads = np.zeros((L + 1, m), dtype=np.int64)
    prefix = np.zeros(L + 1, dtype=np.int64)
    for k in range(L):
        jb = seq[k]
        t = 0
        for i in range(m):
            pij = p[i, jb]
            if pij > 0:
                start = heads[k, i] if heads[k, i] > t else t
                t = start + pij
                heads[k + 1, i] = t
            else:
                heads[k + 1, i] = heads[k, i]
        prefix[k + 1] = prefix[k] + t

    best_pos = -1
    best_ft = np.iinfo(np.int64).max
    best_ms = np.iinfo(np.int64).max
    C = np.empty(m, dtype=np.int64)
    for pos in range(L, -1, -1):
        for i in range(m):
            C[i] = heads[pos, i]
        ft = prefix[pos]
        # vložený job
        t = 0
        for i in range(m):
            pij = p[i, job]
            if pij > 0:
                start = C[i] if C[i] > t else t
                t = start + pij
                C[i] = t
        ft += t
        if ft > best_ft:
            continue
        # joby za ním
        pruned = False
        for k in range(pos, L):
            jb = seq[k]
            t = 0
            for i in range(m):
                pij = p[i, jb]
                if pij > 0:
                    start = C[i] if C[i] > t else t
                    t = start + pij
                    C[i] = t
            ft += t
            if ft > best_ft:            # už horšie než najlepšie – ďalej netreba počítať
                pruned = True
                break
        if pruned:
            continue
        ms = 0
        for i in range(m):
            if C[i] > ms:
                ms = C[i]
        if ft < best_ft or (ft == best_ft and ms < best_ms):
            best_pos = pos
            best_ft = ft
            best_ms = ms
    return best_pos, best_ft, best_ms


@njit(cache=True)
def _insert_at(seq, L, pos, job):
    """Vloží job na pozíciu pos do seq[0:L] (posunie zvyšok doprava)."""
    for k in range(L, pos, -1):
        seq[k] = seq[k - 1]
    seq[pos] = job


@njit(cache=True)
def _insert_jobs(p, seq, L, jobs):
    """Postupne vloží joby `jobs` (v danom poradí) na ich najlepšie pozície.
    seq musí mať miesto aspoň na L + len(jobs) prvkov. Vráti (ΣC, Cmax) výsledku."""
    ft = 0
    ms = 0
    for job in jobs:
        pos, ft, ms = _best_insertion(p, seq, L, job)
        _insert_at(seq, L, pos, job)
        L += 1
    return ft, ms


@njit(cache=True)
def _shift_step(p, seq, ft):
    """Jeden krok shift local search: pre pozície 0..n-1 vyberie job na danej pozícii
    a vloží ho na najlepšie miesto. Vráti nové (ΣC, Cmax)."""
    n = seq.shape[0]
    ms = 0
    for k in range(n):
        job = seq[k]
        for q in range(k, n - 1):        # odstránenie jobu z pozície k
            seq[q] = seq[q + 1]
        pos, ft, ms = _best_insertion(p, seq, n - 1, job)
        _insert_at(seq, n - 1, pos, job)
    return ft, ms


@njit(cache=True)
def _shift_local_search(p, seq, ft):
    """Opakuje shift kroky, kým sa ΣC zlepšuje. Vráti (ΣC, Cmax, počet zlepšujúcich krokov)."""
    steps = 0
    while True:
        new_ft, new_ms = _shift_step(p, seq, ft)
        if new_ft < ft:
            ft = new_ft
            steps += 1
        else:
            return new_ft, new_ms, steps


# =========================================================================== parametre a výsledok

@dataclass
class IGAParams:
    alpha: float = 0.234375          # násobok teploty (Sekcia 5.1)
    d_max: int = 8                   # max. počet odstránených jobov pri perturbácii
    iter_factor: float = 0.1         # 0.1 → 15000/n iterácií ako v článku
    iter_base: float = 150000.0
    iter_limit: int | None = None    # ak je zadané, prepíše iter_factor
    sampling: str = "uniform"        # výber odstránených jobov: "uniform" alebo "autori"


@dataclass
class IGAResult:
    perm: np.ndarray                 # najlepšia permutácia (indexy jobov 0..n-1)
    ft: int                          # jej ΣC
    ms: int                          # jej Cmax
    construction_ft: int             # ΣC po konštrukcii
    ls_ft: int                       # ΣC po prvom local search
    iterations: int                  # počet vykonaných iterácií IGA
    time: float                      # čas behu v sekundách
    time_found: float                # kedy bolo nájdené najlepšie riešenie
    history: list = field(default_factory=list)   # (iterácia, čas, najlepšie ΣC) pri každom zlepšení


def iteration_limit(n: int, params: IGAParams) -> int:
    if params.iter_limit is not None:
        return params.iter_limit
    return max(1, int(params.iter_factor * params.iter_base / n))


def destruction_size(n: int, params: IGAParams) -> int:
    return min(params.d_max, (8 * n + 9) // 10)


def temperature(p: np.ndarray, params: IGAParams) -> float:
    m, n = p.shape
    p_avg = p.sum() / (n * m)
    return params.alpha * p_avg / 10


# =========================================================================== verejné funkcie

def construct(p: np.ndarray) -> tuple[np.ndarray, int, int]:
    """Štartovacie riešenie: joby podľa Σ_i p_ij zostupne (pri zhode menší index),
    vkladané jeden po druhom na najlepšiu pozíciu. Vráti (perm, ΣC, Cmax)."""
    n = p.shape[1]
    totals = p.sum(axis=0)
    order = np.array(sorted(range(n), key=lambda j: (-totals[j], j)), dtype=np.int64)
    seq = np.empty(n, dtype=np.int64)
    ft, ms = _insert_jobs(p, seq, 0, order)
    return seq, int(ft), int(ms)


def best_insertion(p: np.ndarray, partial, job: int) -> tuple[int, int, int]:
    """Python obal pre testy: (pozícia, ΣC, Cmax) najlepšieho vloženia jobu do `partial`."""
    seq = np.empty(len(partial) + 1, dtype=np.int64)
    seq[:len(partial)] = partial
    pos, ft, ms = _best_insertion(p, seq, len(partial), job)
    return int(pos), int(ft), int(ms)


def shift_local_search(p: np.ndarray, perm) -> tuple[np.ndarray, int, int, int]:
    """Python obal: vráti (nová permutácia, ΣC, Cmax, počet zlepšujúcich krokov)."""
    from evaluate import evaluate_permutation
    seq = np.array(perm, dtype=np.int64)
    ft = evaluate_permutation(p, seq)[1]
    ft, ms, steps = _shift_local_search(p, seq, ft)
    return seq, int(ft), int(ms), int(steps)


def sample_positions_authors(n: int, d: int, rng: np.random.Generator) -> np.ndarray:
    """d rôznych pozícií z {0, ..., n-1} rovnako ako sample_floyd v programe autorov
    (losuje sa z {0, ..., u-1} namiesto {0, ..., u}, preto výber nie je rovnomerný)."""
    chosen: set[int] = set()
    for u in range(n - d, n):
        s = int(rng.integers(u))
        chosen.add(u if s in chosen else s)
    return np.array(sorted(chosen), dtype=np.int64)


def perturb(p: np.ndarray, seq: np.ndarray, d: int, rng: np.random.Generator,
            sampling: str = "uniform"):
    """Deštrukcia a rekonštrukcia: odstráni d náhodných jobov a vloží ich späť
    v náhodnom poradí, každý na najlepšiu pozíciu. Vráti (nová permutácia, ΣC, Cmax)."""
    n = seq.shape[0]
    if sampling == "autori":
        positions = sample_positions_authors(n, d, rng)
    elif sampling == "uniform":
        positions = rng.choice(n, size=d, replace=False)
    else:
        raise ValueError(f"neznámy sampling {sampling!r}")
    removed = rng.permutation(seq[positions])
    mask = np.ones(n, dtype=bool)
    mask[positions] = False
    new = np.empty(n, dtype=np.int64)
    new[:n - d] = seq[mask]
    ft, ms = _insert_jobs(p, new, n - d, removed)
    return new, int(ft), int(ms)


def iga(p: np.ndarray, seed: int, params: IGAParams | None = None) -> IGAResult:
    """Spustí 1. fázu (IGA v permutačnom priestore) na inštancii s časmi p (tvar m × n)."""
    params = params or IGAParams()
    rng = np.random.default_rng(seed)
    n = p.shape[1]
    t0 = time.perf_counter()

    seq, construction_ft, ms = construct(p)
    ft, ms, _ = _shift_local_search(p, seq, construction_ft)
    ft, ms = int(ft), int(ms)
    ls_ft = ft

    best_seq, best_ft, best_ms = seq.copy(), ft, ms
    time_found = time.perf_counter() - t0
    history = [(0, time_found, best_ft)]

    limit = iteration_limit(n, params)
    d = destruction_size(n, params)
    T = temperature(p, params)

    steps = 0
    while steps <= limit:                     # ako autori: stop až keď steps > limit
        new_seq, new_ft, _ = perturb(p, seq, d, rng, params.sampling)
        new_ft, new_ms, _ = _shift_local_search(p, new_seq, new_ft)
        new_ft, new_ms = int(new_ft), int(new_ms)
        if new_ft < best_ft:                  # nové najlepšie – vždy prijmi
            seq, ft = new_seq, new_ft
            best_seq, best_ft, best_ms = new_seq.copy(), new_ft, new_ms
            time_found = time.perf_counter() - t0
            history.append((steps + 1, time_found, best_ft))
        elif new_ft < ft or rng.random() < math.exp(-(new_ft - ft) / T):
            seq, ft = new_seq, new_ft         # Metropolis: prijmi
        # inak ostáva pôvodné riešenie (seq, ft)
        steps += 1

    return IGAResult(perm=best_seq, ft=best_ft, ms=best_ms,
                     construction_ft=construction_ft, ls_ft=ls_ft,
                     iterations=steps, time=time.perf_counter() - t0,
                     time_found=time_found, history=history)
