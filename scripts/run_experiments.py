"""Spustí experimenty podľa konfigurácie a uloží výsledky do results/*.csv.

Pre každú inštanciu a seed zaznamenať: inštanciu, n, m, r, seed, variant (IGA / IGA0 / IGA+NPS-set),
sum C_j po fáze 1 a po fáze 2, čas, históriu konvergencie.

Použitie:
    python scripts/run_experiments.py --config configs/default.yaml
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/default.yaml")
    parser.parse_args()
    raise NotImplementedError("Runner ešte nie je implementovaný.")


if __name__ == "__main__":
    main()
