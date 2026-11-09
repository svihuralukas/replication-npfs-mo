"""
Spustí MIP model (src/mip.py) na zvolených inštanciách a uloží výsledky do CSV (priebežne,
s pokračovaním po prerušení). Časový limit ako v článku (Sekcia 5.3): n·m sekúnd, aspoň 30 s.

Autori MIP štartovali z riešenia 1. fázy IGA (warm start). HiGHS v scipy počiatočné riešenie
neprijíma; s --upper-bounds sa namiesto toho pridá obmedzenie ΣC ≤ najlepšie ΣC z daného CSV
(stĺpec iga_ft, napr. results/iga_ours.csv). S --redo-nonoptimal sa znova riešia len inštancie,
ktoré v --out ešte nie sú vyriešené optimálne (ich riadok sa nahradí).

Spustenie (z koreňa repozitára):
    python src/run_mip.py --instances "instances/generated/*_05_*.txt" --out results/mip.csv
    python src/run_mip.py --instances "instances/generated/*_05_*.txt" --out results/mip.csv \
        --upper-bounds results/iga_ours.csv --redo-nonoptimal
"""

from __future__ import annotations

import argparse
import csv
import glob
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from instance import read_instance   # noqa: E402
from mip import solve_mip            # noqa: E402

FIELDS = ["instance", "r", "n", "m", "mip_ft", "mip_bound", "optimal", "time", "time_limit",
          "upper_bound"]


def run_one(args) -> dict:
    path, ub = args
    inst = read_instance(path)
    limit = max(30.0, float(inst.n * inst.m))
    res = solve_mip(inst.p, upper_bound=ub, time_limit=limit)
    if res.ft is None and ub is not None:     # nič lepšie než UB sa nenašlo → riešenie s ΣC = UB
        res.ft = ub
    return dict(instance=inst.name, r=inst.r, n=inst.n, m=inst.m, mip_ft=res.ft,
                mip_bound=None if res.bound is None else round(res.bound, 3),
                optimal=int(res.optimal), time=round(res.time, 3), time_limit=limit, upper_bound=ub)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", nargs="+", required=True)
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    ap.add_argument("--out", default="results/mip.csv")
    ap.add_argument("--upper-bounds", default=None, help="CSV so stĺpcami instance, iga_ft")
    ap.add_argument("--redo-nonoptimal", action="store_true")
    args = ap.parse_args()

    ubs = {}
    if args.upper_bounds:
        with open(args.upper_bounds, newline="") as f:
            for r in csv.DictReader(f):
                ubs[r["instance"]] = min(ubs.get(r["instance"], 10**18), int(r["iga_ft"]))

    out = Path(args.out)
    rows = []
    if out.exists():
        with open(out, newline="") as f:
            rows = list(csv.DictReader(f))
    if args.redo_nonoptimal:
        rows = [r for r in rows if r["optimal"] == "1"]
    done = {r["instance"] for r in rows}
    paths = sorted(p for pat in args.instances for p in glob.glob(pat) if Path(p).stem not in done)
    print(f"hotových {len(done)}, zostáva {len(paths)} inštancií", flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f, ProcessPoolExecutor(max_workers=args.jobs) as ex:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
        f.flush()
        tasks = [(p, ubs.get(Path(p).stem)) for p in paths]
        for k, fut in enumerate(as_completed([ex.submit(run_one, t) for t in tasks]), 1):
            w.writerow(fut.result())
            f.flush()
            if k % 20 == 0 or k == len(paths):
                print(f"  {k}/{len(paths)}", flush=True)
    print("Uložené do", out)


if __name__ == "__main__":
    main()
