"""
Inštancie flow shopu s chýbajúcimi operáciami (F | skip | ΣC_j).

Formát súborov je rovnaký ako v pôvodných inštanciách Henneberg & Neufeld (2016),
ktoré používajú Ritt & Rossit (2024) (pozri npfs-mo/src/instance.cpp, funkcia read_hn):

    numberMachines <m> numberJobs <n> missing Operations <r>
    t_0_0 <p>
    t_0_1 <p>
    ...
    t_<m-1>_<n-1> <p>

kde t_i_j je čas spracovania jobu j na stroji i (indexované od 0)
a hodnota 0 znamená CHÝBAJÚCU operáciu (nie operáciu s nulovým časom).

Vnútorná reprezentácia: numpy pole p tvaru (m, n), p[i, j] = čas jobu j na stroji i,
čo zodpovedá notácii p_ij v článku.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Instance:
    p: np.ndarray          # tvar (m, n), int64; 0 = chýbajúca operácia
    r: float               # deklarovaná miera chýbajúcich operácií
    name: str = ""

    @property
    def m(self) -> int:
        return self.p.shape[0]

    @property
    def n(self) -> int:
        return self.p.shape[1]

    @property
    def present(self) -> np.ndarray:
        """Boolovská maska (m, n): True tam, kde operácia existuje."""
        return self.p > 0

    def num_missing(self) -> int:
        return int((self.p == 0).sum())

    def num_pseudo_jobs(self) -> int:
        """Počet "prirodzených" pseudo jobov = blokov po sebe idúcich nechýbajúcich
        operácií jobu (Sekcia 3.1 článku). Zhodné s Instance::numPseudojobs v ich kóde."""
        pres = self.present
        # pseudo job začína na stroji i, ak operácia existuje a na stroji i-1 chýba (alebo i = 0)
        starts = pres.copy()
        starts[1:, :] &= ~pres[:-1, :]
        return int(starts.sum())


def read_instance(path: str | Path) -> Instance:
    """Načíta inštanciu vo formáte Henneberg & Neufeld."""
    path = Path(path)
    tokens = path.read_text().split()
    if tokens[0] != "numberMachines" or tokens[2] != "numberJobs" \
            or tokens[4] != "missing" or tokens[5] != "Operations":
        raise ValueError(f"{path}: neočakávaná hlavička {tokens[:7]}")
    m, n, r = int(tokens[1]), int(tokens[3]), float(tokens[6])
    p = np.zeros((m, n), dtype=np.int64)
    pos = 7
    for i in range(m):
        for j in range(n):
            label, value = tokens[pos], tokens[pos + 1]
            if label != f"t_{i}_{j}":
                raise ValueError(f"{path}: očakávané t_{i}_{j}, nájdené {label}")
            p[i, j] = int(value)
            pos += 2
    return Instance(p=p, r=r, name=path.stem)


def write_instance(inst: Instance, path: str | Path) -> None:
    """Zapíše inštanciu vo formáte Henneberg & Neufeld (čitateľnom aj ich programom npfsmo)."""
    lines = [f"numberMachines {inst.m} numberJobs {inst.n} missing Operations {inst.r}"]
    for i in range(inst.m):
        for j in range(inst.n):
            lines.append(f"t_{i}_{j} {int(inst.p[i, j])}")
    Path(path).write_text("\n".join(lines) + "\n")


def num_missing_for(n: int, m: int, r: float) -> int:
    """Počet chýbajúcich operácií = r·n·m zaokrúhlené na celé číslo (pri ,5 nahor).

    Zistené z ich dát (npfs-mo/data/table2.csv): vo všetkých 2160 inštanciách je počet
    existujúcich operácií presne n·m − round_half_up(r·n·m).
    Počítame v celých číslach (r v percentách), aby sme sa vyhli chybám float aritmetiky
    (napr. 0.3 * 25 = 7.499999... v pohyblivej čiarke).
    """
    r_pct = round(r * 100)
    return (r_pct * n * m + 50) // 100


def generate_instance(n: int, m: int, r: float, rng: np.random.Generator,
                      pmin: int = 1, pmax: int = 99, name: str = "") -> Instance:
    """Vygeneruje inštanciu podľa postupu z článku (Sekcia 5.1):
    časy spracovania z U[pmin, pmax] (Taillard, 1990), potom presne num_missing_for(n, m, r)
    náhodne vybraných operácií nastavíme ako chýbajúce (hodnota 0)."""
    p = rng.integers(pmin, pmax + 1, size=(m, n), dtype=np.int64)
    k = num_missing_for(n, m, r)
    missing_idx = rng.choice(n * m, size=k, replace=False)
    p.flat[missing_idx] = 0
    return Instance(p=p, r=r, name=name)


def instance_name(r: float, n: int, m: int, i: int) -> str:
    """Názov súboru v štýle ich príkladu z README (napr. 0.2_10_05_02).
    Poradie polí r_n_m_i je náš predpoklad – na správnosť nemá vplyv,
    lebo n a m sa vždy čítajú z hlavičky súboru."""
    return f"{r:.1f}_{n:02d}_{m:02d}_{i:02d}"


def instance_rng(base_seed: int, r: float, n: int, m: int, i: int) -> np.random.Generator:
    """Samostatný, deterministický generátor pre každú inštanciu.
    Vďaka tomu je každá inštancia reprodukovateľná nezávisle od ostatných
    (pridanie/odobratie veľkostí nezmení už vygenerované inštancie)."""
    return np.random.default_rng([base_seed, round(r * 100), n, m, i])
