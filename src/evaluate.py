"""
Účelová funkcia: časy dokončenia C, makespan Cmax a celkový čas dokončenia ΣC
pre flow shop s chýbajúcimi operáciami (F | skip | ΣC_j).

Pravidlá výpočtu (Ritt & Rossit 2024, Sekcia 1 a obr. 1):
  * Operácia o_ij (job j na stroji i) začne, keď je
      - stroj i voľný (skončila predchádzajúca operácia na stroji i) a
      - job j dokončil svoju predchádzajúcu EXISTUJÚCU operáciu.
    C_ij = max(koniec stroja i, koniec jobu j) + p_ij
  * Chýbajúca operácia (p_ij == 0) sa PRESKOČÍ: neobsadí stroj a job nečaká.
    (Na rozdiel od operácie s nulovým časom, ktorá by job zaradila do poradia na stroji.)
  * Čas dokončenia jobu C_j = koniec jeho poslednej existujúcej operácie
    (job bez operácií má C_j = 0).
  * ΣC = súčet C_j cez joby v rozvrhu, Cmax = max C_j.

Reprezentácia riešení (indexy jobov 0..n-1, strojov 0..m-1; p má tvar (m, n)):
  * permutačný rozvrh: jedno poradie jobov `perm` platné na všetkých strojoch.
    Môže obsahovať len časť jobov (čiastočný rozvrh pri konštrukcii) –
    ΣC sa potom počíta len cez joby v `perm`.
  * non-permutation rozvrh: `orders` tvaru (m, k), riadok i = poradie jobov na stroji i.
    Každý riadok obsahuje tie isté joby (aj tie, ktoré na stroji chýbajú – preskočia sa).

Prečo stačí počítať stroj po stroji:
  Job prechádza stroje vždy v poradí 0, 1, ..., m-1, takže operácia na stroji i závisí
  len od operácií na strojoch < i a od predchádzajúcich operácií na stroji i.
  Graf závislostí je preto vždy acyklický a KAŽDÁ kombinácia poradí na strojoch
  je prípustný rozvrh (nemôže vzniknúť zablokovanie).

Výpočet zodpovedá PSolution::compute_ms_ft_mo a NPSolution::compute_ms_ft_mo
v kóde autorov (npfs-mo/src/solution.cpp); overené testami v tests/test_evaluate.py.

Funkcie sú písané jednoduchými cyklami nad numpy poľami, aby sa dali neskôr
(krok 6) zrýchliť dekorátorom numba.njit bez zmeny logiky.
"""

from __future__ import annotations

import numpy as np


# --------------------------------------------------------------------------- permutácie

def evaluate_permutation(p: np.ndarray, perm) -> tuple[int, int]:
    """Vráti (Cmax, ΣC) permutačného rozvrhu `perm` (zoznam/pole indexov jobov)."""
    m = p.shape[0]
    machine_free = np.zeros(m, dtype=np.int64)   # kedy sa uvoľní stroj i
    total = 0
    cmax = 0
    for j in perm:
        t = 0                                     # kedy job j dokončil poslednú operáciu
        for i in range(m):
            pij = p[i, j]
            if pij > 0:                           # chýbajúcu operáciu preskočíme
                start = machine_free[i] if machine_free[i] > t else t
                t = start + pij
                machine_free[i] = t
        total += t
        if t > cmax:
            cmax = t
    return int(cmax), int(total)


def completion_times_permutation(p: np.ndarray, perm, zero_time: bool = False) -> np.ndarray:
    """Matica časov dokončenia C tvaru (m, n); C[i, j] = 0 pre chýbajúce operácie
    a joby mimo `perm`.

    zero_time=True: chýbajúce operácie sa NEpreskakujú, ale berú ako operácie
    s nulovým časom (job musí "prejsť" strojom v poradí). Slúži len na porovnanie
    s obr. 1 článku – algoritmus to nepoužíva."""
    m, n = p.shape
    C = np.zeros((m, n), dtype=np.int64)
    machine_free = np.zeros(m, dtype=np.int64)
    for j in perm:
        t = 0
        for i in range(m):
            pij = p[i, j]
            if pij > 0 or zero_time:
                t = max(machine_free[i], t) + pij
                machine_free[i] = t
                C[i, j] = t
    return C


# --------------------------------------------------------------------------- non-permutation

def evaluate_nonpermutation(p: np.ndarray, orders: np.ndarray) -> tuple[int, int]:
    """Vráti (Cmax, ΣC) non-permutation rozvrhu. orders[i] = poradie jobov na stroji i."""
    m = p.shape[0]
    n_jobs = p.shape[1]
    job_done = np.zeros(n_jobs, dtype=np.int64)  # koniec poslednej spracovanej operácie jobu
    for i in range(m):
        machine_free = 0
        for j in orders[i]:
            pij = p[i, j]
            if pij > 0:
                start = machine_free if machine_free > job_done[j] else job_done[j]
                machine_free = start + pij
                job_done[j] = machine_free
    jobs = orders[0]
    total = 0
    cmax = 0
    for j in jobs:
        total += job_done[j]
        if job_done[j] > cmax:
            cmax = job_done[j]
    return int(cmax), int(total)


def completion_times_nonpermutation(p: np.ndarray, orders: np.ndarray) -> np.ndarray:
    """Matica časov dokončenia C tvaru (m, n) pre non-permutation rozvrh."""
    m, n = p.shape
    C = np.zeros((m, n), dtype=np.int64)
    job_done = np.zeros(n, dtype=np.int64)
    for i in range(m):
        machine_free = 0
        for j in orders[i]:
            pij = p[i, j]
            if pij > 0:
                machine_free = max(machine_free, job_done[j]) + pij
                job_done[j] = machine_free
                C[i, j] = machine_free
    return C


def permutation_to_orders(perm, m: int) -> np.ndarray:
    """Permutačný rozvrh ako non-permutation (rovnaké poradie na všetkých strojoch)."""
    return np.tile(np.asarray(perm, dtype=np.int64), (m, 1))


def is_valid_orders(orders: np.ndarray, n: int) -> bool:
    """Každý riadok musí byť permutáciou tej istej množiny jobov 0..n-1."""
    target = np.arange(n)
    return all(np.array_equal(np.sort(row), target) for row in orders)
