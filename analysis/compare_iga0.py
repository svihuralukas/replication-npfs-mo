"""
Porovnanie našej 1. fázy (IGA0) s 1. fázou pôvodného programu autorov na ROVNAKÝCH inštanciách.

Vstupy:
    results/iga0_check_ours.csv        – src/run_experiments.py
    reference/iga0_check_authors.csv   – reference/run_authors.py
Spustenie (z priečinka projekt/):
    python analysis/compare_iga0.py

Čo sa porovnáva:
  1. deterministické časti (konštrukcia, prvý local search) – musia sedieť presne,
  2. kvalita IGA0: relatívna odchýlka od najlepšej známej hodnoty (BKV) v %,
     BKV = najmenšie ΣC zo všetkých behov (naše aj autorov, vrátane ich finálneho
     non-permutation riešenia) – rovnako ako v článku: (v - b) / b,
  3. Wilcoxonov párový test na priemeroch cez seedy (pár = jedna inštancia).
Seedy sa medzi implementáciami NEpárujú – generátory náhodných čísel sú rôzne.
"""

from __future__ import annotations

import argparse

import pandas as pd
from scipy.stats import wilcoxon


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", default="results/iga0_check_ours.csv")
    ap.add_argument("--authors", default="reference/iga0_check_authors.csv")
    ap.add_argument("--out", default="results/iga0_check_summary.csv")
    args = ap.parse_args()

    ours = pd.read_csv(args.ours)
    auth = pd.read_csv(args.authors)

    # 1. deterministické časti
    det = ours.merge(auth, on=["instance", "seed"], suffixes=("_ours", "_auth"))
    same_c = (det["construction_ft_ours"] == det["construction_ft_auth"]).mean()
    same_ls = (det["ls_ft_ours"] == det["ls_ft_auth"]).mean()
    print(f"Zhoda konštrukcie: {same_c:.0%}, zhoda prvého local search: {same_ls:.0%} "
          f"({len(det)} behov)\n")

    # 2. BKV a relatívne odchýlky
    bkv = pd.concat([ours[["instance", "iga0_ft"]].rename(columns={"iga0_ft": "v"}),
                     auth[["instance", "iga0_ft"]].rename(columns={"iga0_ft": "v"}),
                     auth[["instance", "iga_ft"]].rename(columns={"iga_ft": "v"})]
                    ).groupby("instance")["v"].min().rename("bkv")
    for df in (ours, auth):
        df["rpd"] = 100 * (df["iga0_ft"] - df["instance"].map(bkv)) / df["instance"].map(bkv)

    keys = ["instance", "r", "n", "m"]
    per_inst = (ours.groupby(keys)[["iga0_ft", "rpd", "time"]].mean().add_suffix("_ours")
                .join(auth.groupby(keys)[["iga0_ft", "rpd", "time"]].mean().add_suffix("_auth"))
                .reset_index())

    by_n = per_inst.groupby("n").agg(
        instances=("instance", "count"),
        rpd_ours=("rpd_ours", "mean"), rpd_auth=("rpd_auth", "mean"),
        time_ours=("time_ours", "mean"), time_auth=("time_auth", "mean"))
    print("Priemerná relatívna odchýlka IGA0 od BKV [%] a čas [s] (priemer cez inštancie a 5 seedov):")
    print(by_n.round(3).to_string())
    print(f"\nCelkovo: naše {per_inst['rpd_ours'].mean():.3f} %, autori {per_inst['rpd_auth'].mean():.3f} %")

    # 3. štatistický test
    diff = per_inst["iga0_ft_ours"] - per_inst["iga0_ft_auth"]
    better, equal, worse = (diff < 0).sum(), (diff == 0).sum(), (diff > 0).sum()
    print(f"\nPriemer cez seedy – naše lepšie: {better}, rovnaké: {equal}, horšie: {worse} inštancií")
    nz = diff[diff != 0]
    if len(nz) > 0:
        stat, pval = wilcoxon(per_inst["iga0_ft_ours"], per_inst["iga0_ft_auth"], zero_method="wilcox")
        print(f"Wilcoxonov párový test: p = {pval:.3f} "
              f"({'rozdiel NIE JE' if pval >= 0.05 else 'rozdiel JE'} štatisticky významný na úrovni 0,05)")

    by_n.to_csv(args.out)
    print("\nUložené do", args.out)


if __name__ == "__main__":
    main()
