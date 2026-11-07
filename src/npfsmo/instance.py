"""Problémové inštancie (Henneberg & Neufeld, 2016; generovanie podľa Taillard, 1993).
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class Instance:
    name: str
    p: np.ndarray        # (m, n) procesné časy, pri chýbajúcej operácii ľubovoľná hodnota
    present: np.ndarray  # (m, n) bool, False = chýbajúca operácia

    @property
    def m(self) -> int:
        return self.p.shape[0]

    @property
    def n(self) -> int:
        return self.p.shape[1]

    def as_zero_time(self) -> "Instance":
        """Rovnaká inštancia, kde sú chýbajúce operácie nahradené operáciami s nulovým časom.

        Slúži na porovnanie z Obr. 1 a Viet 2–3 článku (zero-time != missing).
        """
        raise NotImplementedError


def load_instance(path: str | Path) -> Instance:
    """Načíta inštanciu zo súboru. TODO: formát podľa nášho generátora / H&N."""
    raise NotImplementedError
