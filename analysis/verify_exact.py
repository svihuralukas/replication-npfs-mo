"""
Presné overenie deterministických častí našej implementácie proti pôvodnému programu autorov.

1. 2. fáza a NPS-set: z permutácie, ktorú našiel program autorov (seed 1), musí naša
   implementácia dať presne ten istý výsledok (ΣC, Cmax, pri 2. fáze aj celý rozvrh).
   Vstup: reference/authors_phase2_check.json (jedna inštancia z každej zo 72 skupín,
   reference/make_eval_fixture.py --glob "*_15.txt") a tests/data/authors_solutions.json.
2. Konštrukcia, prvý local search a NPS-set z konštrukcie: musia sa zhodovať na všetkých
   inštanciách z plných behov (results/iga_ours.csv vs reference/iga_authors.csv).

Spustenie (z koreňa repozitára):
    python analysis/verify_exact.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from instance import read_instance          # noqa: E402
from nonperm import nonperm_local_search    # noqa: E402
from nps_set import nps_set                 # noqa: E402


def check_fixture(paths: list[Path]) -> pd.DataFrame:
    rows = []
    for path in paths:
        for name, a in json.loads(path.read_text()).items():
            p = read_instance(ROOT / "instances" / "generated" / f"{name}.txt").p
            res = nonperm_local_search(p, a["perm"])
            nps = nps_set(p, a["perm"])
            rows.append(dict(instance=name, source=path.name,
                             perm_ft=a["perm_ft"], authors_ft=a["final_ft"], ours_ft=res.ft,
                             phase2_same_value=(res.ms, res.ft) == (a["final_ms"], a["final_ft"]),
                             phase2_same_schedule=bool(np.array_equal(res.orders, np.array(a["orders"]))),
                             authors_nps_ft=a["nps_ft"], ours_nps_ft=nps[1],
                             nps_same_value=nps == (a["nps_ms"], a["nps_ft"])))
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", nargs="+", default=[str(ROOT / "reference" / "authors_phase2_check.json"),
                                                       str(ROOT / "tests" / "data" / "authors_solutions.json")])
    ap.add_argument("--ours", default=str(ROOT / "results" / "iga_ours.csv"))
    ap.add_argument("--authors", default=str(ROOT / "reference" / "iga_authors.csv"))
    ap.add_argument("--out", default=str(ROOT / "results" / "exact_check.csv"))
    args = ap.parse_args()

    fx = check_fixture([Path(f) for f in args.fixtures if Path(f).exists()])
    fx.to_csv(args.out, index=False)
    print(f"2. fáza z permutácie autorov: rovnaká hodnota {fx.phase2_same_value.sum()}/{len(fx)}, "
          f"rovnaký rozvrh {fx.phase2_same_schedule.sum()}/{len(fx)}")
    print(f"NPS-set z permutácie autorov: rovnaká hodnota {fx.nps_same_value.sum()}/{len(fx)}")
    print(f"  (2. fáza zlepšila permutáciu v {(fx.authors_ft < fx.perm_ft).sum()} z {len(fx)} prípadov)")

    if Path(args.ours).exists() and Path(args.authors).exists():
        keys = ["construction_ft", "ls_ft", "nps0_ft"]
        o = pd.read_csv(args.ours).groupby("instance")[keys].first()
        a = pd.read_csv(args.authors).groupby("instance")[keys].first()
        j = o.join(a, lsuffix="_ours", rsuffix="_auth", how="inner")
        for k in keys:
            same = (j[f"{k}_ours"] == j[f"{k}_auth"]).sum()
            print(f"{k}: zhoda na {same}/{len(j)} inštanciách")
    print("Uložené do", args.out)


if __name__ == "__main__":
    main()
