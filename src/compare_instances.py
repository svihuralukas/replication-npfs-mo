"""
Porovná štatistiky našich vygenerovaných inštancií s pôvodnými inštanciami autorov
(npfs-mo/data/table2.csv: priemerný čas operácie, počet existujúcich operácií,
počet pseudo jobov pre každú inštanciu).

Slúži ako dôkaz, že naše inštancie sú "porovnateľnou náhradou" pôvodných.

Spustenie (z priečinka projekt/):
    python src/compare_instances.py --table2 ../npfs-mo/data/table2.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from instance import read_instance


def our_stats(inst_dir: Path) -> pd.DataFrame:
    rows = []
    for f in sorted(inst_dir.glob("*.txt")):
        inst = read_instance(f)
        pres = inst.present
        rows.append(dict(
            d=inst.r, n=inst.n, m=inst.m,
            avg_t=inst.p[pres].mean(),
            effops=int(pres.sum()),
            pj=inst.num_pseudo_jobs(),
        ))
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", default="instances/generated")
    ap.add_argument("--table2", default="../npfs-mo/data/table2.csv")
    ap.add_argument("--out", default="results/instance_comparison.csv")
    args = ap.parse_args()

    ours = our_stats(Path(args.instances))
    theirs = pd.read_csv(args.table2).rename(columns={"avg.t": "avg_t"})

    keys = ["d", "n", "m"]
    cols = ["avg_t", "effops", "pj"]
    g_ours = ours.groupby(keys)[cols].mean().add_suffix("_ours")
    g_theirs = theirs.groupby(keys)[cols].mean().add_suffix("_theirs")
    cmp = g_ours.join(g_theirs, how="inner").reset_index()

    # Očakávaný počet pseudo jobov podľa Propozície 1: n((1-r)^2 + r(1-r)m)
    cmp["pj_expected"] = cmp["n"] * ((1 - cmp["d"]) ** 2 + cmp["d"] * (1 - cmp["d"]) * cmp["m"])

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    cmp.to_csv(args.out, index=False)

    pd.set_option("display.width", 160)
    print(cmp.round(2).to_string(index=False))
    print()
    print("Počet existujúcich operácií sa zhoduje vo všetkých skupinách:",
          bool((cmp["effops_ours"] == cmp["effops_theirs"]).all()))
    rel_pj = (cmp["pj_ours"] / cmp["pj_theirs"] - 1).abs()
    rel_t = (cmp["avg_t_ours"] / cmp["avg_t_theirs"] - 1).abs()
    print(f"Max. relatívny rozdiel priemerného počtu pseudo jobov: {rel_pj.max():.1%}")
    print(f"Max. relatívny rozdiel priemerného času operácie:     {rel_t.max():.1%}")
    print(f"Uložené do {args.out}")


if __name__ == "__main__":
    main()
