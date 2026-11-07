"""
Spustí našu implementáciu na zvolených inštanciách a seedoch (paralelne) a uloží výsledky do CSV.
Stĺpce sú zhodné s reference/run_authors.py, aby sa výsledky dali priamo porovnať.

Spustenie (z priečinka projekt/):
    python src/run_experiments.py --instances "instances/generated/*_0[0-1].txt" \
        --seeds 1 2 3 4 5 --max-n 50 --out results/iga0_results.csv

Zatiaľ beží 1. fáza (IGA0); 2. fáza a NPS-set pribudnú v kroku 5.
"""

from __future__ import annotations

import argparse
import csv
import glob
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from iga import IGAParams, iga          # noqa: E402
from instance import read_instance      # noqa: E402

FIELDS = ["instance", "r", "n", "m", "seed", "construction_ft", "ls_ft",
          "iga0_ms", "iga0_ft", "iga_steps", "time", "time_found"]


def run_one(args):
    path, seed, iter_factor = args
    inst = read_instance(path)
    res = iga(inst.p, seed=seed, params=IGAParams(iter_factor=iter_factor))
    return dict(instance=inst.name, r=inst.r, n=inst.n, m=inst.m, seed=seed,
                construction_ft=res.construction_ft, ls_ft=res.ls_ft,
                iga0_ms=res.ms, iga0_ft=res.ft, iga_steps=res.iterations,
                time=round(res.time, 6), time_found=round(res.time_found, 6))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", nargs="+", required=True, help="súbory alebo glob vzory")
    ap.add_argument("--seeds", nargs="+", type=int, default=[1])
    ap.add_argument("--max-n", type=int, default=None, help="vynechať inštancie s viac jobmi")
    ap.add_argument("--iter-factor", type=float, default=0.1)
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--out", default="results/iga0_results.csv")
    args = ap.parse_args()

    paths = sorted({p for pat in args.instances for p in glob.glob(pat)})
    if args.max_n:
        paths = [p for p in paths if read_instance(p).n <= args.max_n]
    # najväčšie inštancie najprv – lepšie rozloženie záťaže medzi procesy
    paths.sort(key=lambda p: -read_instance(p).p.size)
    tasks = [(p, s, args.iter_factor) for p in paths for s in args.seeds]
    print(f"{len(paths)} inštancií × {len(args.seeds)} seedov = {len(tasks)} behov, {args.jobs} procesov")

    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        for k, row in enumerate(ex.map(run_one, tasks), 1):
            rows.append(row)
            if k % max(1, len(tasks) // 20) == 0 or k == len(tasks):
                print(f"  {k}/{len(tasks)} hotových ({time.time() - t0:.0f} s)", flush=True)

    rows.sort(key=lambda r: (r["instance"], r["seed"]))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print("Uložené do", args.out)


if __name__ == "__main__":
    main()
