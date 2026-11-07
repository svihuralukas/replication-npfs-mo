"""
Spustí PÔVODNÝ program autorov (npfsmo, C++) na zvolených inštanciách a seedoch
a uloží všetky medzivýsledky do CSV. Slúži ako referencia pre porovnanie s našou
implementáciou na rovnakých inštanciách.

Spúšťa sa v Linuxe/WSL z priečinka projekt/:
    python3 reference/run_authors.py --instances "instances/generated/*.txt" \
        --seeds 1 2 3 4 5 --out reference/authors_results.csv

Výstup (jeden riadok = jedna inštancia × seed):
    construction_ft  ΣC po konštrukcii (deterministické)
    ls_ft            ΣC po prvom shift local search (deterministické)
    iga0_ms/ft       výsledok 1. fázy (IGA v permutačnom priestore) = ablácia IGA0
    nps_ft           IGA0 + konštrukčná heuristika NPS-set = ablácia IGA+NPS-set
    iga_ms/ft        finálny výsledok po 2. fáze (non-permutation local search) = IGA
    iga_steps        počet vykonaných iterácií IGA
    time             celkový čas behu (s)

Formát výstupu npfsmo (npfsmo.cpp): riadok INFO obsahuje 7 trojíc (Cmax ΣC čas):
konštrukcia, konštrukcia-SO, local search, local search-SO, IGA, IGA-SO, NP local search
(SO = najlepšie riešenie podľa sekundárneho kritéria, nepoužívame).
Riadok NPSSET obsahuje dvojice (Cmax ΣC) NPS-set pre konštrukciu, IGA a IGA-SO.
"""

from __future__ import annotations

import argparse
import csv
import glob
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

FIELDS = ["instance", "r", "n", "m", "seed", "construction_ft", "ls_ft",
          "iga0_ms", "iga0_ft", "nps_ft", "iga_ms", "iga_ft", "iga_steps", "time"]


def parse_header(path: str):
    tok = Path(path).read_text().split()[:7]
    return float(tok[6]), int(tok[3]), int(tok[1])        # r, n, m


def run_one(args):
    binary, path, seed, iterfactor = args
    out = subprocess.run(
        [binary, "--flowtime", "--timelimit", "-1", "--iterfactor", str(iterfactor),
         "--npfs", "--seed", str(seed), path],
        capture_output=True, text=True, check=True).stdout
    lines = {l.split()[0]: l.split() for l in out.splitlines() if l.strip()}
    # INFO <názov> + 7 trojíc; názov môže obsahovať medzery (npfsmo nahrádza "_" medzerou),
    # preto berieme posledných 21 čísel
    info = [float(x) for x in lines["INFO"][-21:]]
    trip = [info[k:k + 3] for k in range(0, len(info), 3)]
    npsset = [int(x) for x in lines["NPSSET"][1:]]
    stat = lines["STAT"]
    r, n, m = parse_header(path)
    return dict(instance=Path(path).stem, r=r, n=n, m=m, seed=seed,
                construction_ft=int(trip[0][1]), ls_ft=int(trip[2][1]),
                iga0_ms=int(trip[4][0]), iga0_ft=int(trip[4][1]),
                nps_ft=npsset[3],
                iga_ms=int(trip[6][0]), iga_ft=int(trip[6][1]),
                iga_steps=int(stat[2]), time=float(stat[3]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--npfsmo", default="../npfs-mo/build/npfsmo")
    ap.add_argument("--instances", nargs="+", required=True, help="súbory alebo glob vzory")
    ap.add_argument("--seeds", nargs="+", type=int, default=[1])
    ap.add_argument("--iterfactor", type=float, default=0.1)
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--out", default="reference/authors_results.csv")
    args = ap.parse_args()

    paths = sorted({p for pat in args.instances for p in glob.glob(pat)})
    tasks = [(args.npfsmo, p, s, args.iterfactor) for p in paths for s in args.seeds]
    print(f"{len(paths)} inštancií × {len(args.seeds)} seedov = {len(tasks)} behov")

    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        rows = list(ex.map(run_one, tasks, chunksize=4))

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print("Uložené do", args.out)


if __name__ == "__main__":
    main()
