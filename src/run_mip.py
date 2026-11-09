"""
Spustí MIP model (src/mip.py) na zvolených inštanciách a uloží výsledky do CSV (priebežne,
s pokračovaním po prerušení). Časový limit ako v článku (Sekcia 5.3): n·m sekúnd, aspoň 30 s.

Spustenie (z koreňa repozitára):
    python src/run_mip.py --instances "instances/generated/*_05_*.txt" --out results/mip.csv
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

FIELDS = ["instance", "r", "n", "m", "mip_ft", "mip_bound", "optimal", "time", "time_limit"]


def run_one(path: str) -> dict:
    inst = read_instance(path)
    limit = max(30.0, float(inst.n * inst.m))
    res = solve_mip(inst.p, time_limit=limit)
    return dict(instance=inst.name, r=inst.r, n=inst.n, m=inst.m, mip_ft=res.ft,
                mip_bound=None if res.bound is None else round(res.bound, 3),
                optimal=int(res.optimal), time=round(res.time, 3), time_limit=limit)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", nargs="+", required=True)
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    ap.add_argument("--out", default="results/mip.csv")
    args = ap.parse_args()

    out = Path(args.out)
    done = set()
    if out.exists():
        with open(out, newline="") as f:
            done = {r["instance"] for r in csv.DictReader(f)}
    paths = sorted(p for pat in args.instances for p in glob.glob(pat) if Path(p).stem not in done)
    print(f"hotových {len(done)}, zostáva {len(paths)} inštancií", flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    new = not out.exists()
    with open(out, "a", newline="") as f, ProcessPoolExecutor(max_workers=args.jobs) as ex:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for k, fut in enumerate(as_completed([ex.submit(run_one, p) for p in paths]), 1):
            row = fut.result()
            w.writerow(row)
            f.flush()
            if k % 20 == 0 or k == len(paths):
                print(f"  {k}/{len(paths)}", flush=True)
    print("Uložené do", out)


if __name__ == "__main__":
    main()
