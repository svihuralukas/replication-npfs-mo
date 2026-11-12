"""
Spustí našu implementáciu na zvolených inštanciách a seedoch (paralelne) a uloží výsledky do CSV.
Jeden beh (inštancia × seed) dá naraz všetky tri varianty z článku – rovnako ako program autorov:
    IGA0         = len 1. fáza (permutačný IGA)                              – Tab. 6
    IGA+NPS-set  = 1. fáza + konštrukčná heuristika NPS-set                    – Tab. 6
    IGA          = 1. fáza + 2. fáza (local search v nepermutačnom priestore)  – Tab. 3, 4
Stĺpce sú zhodné s reference/run_authors.py (+ naše časy fáz), aby sa výsledky dali priamo porovnať.

Predvolené parametre (seedy, α, d, rozpočet iterácií) sa čítajú z config/experiment.yaml,
argumenty príkazového riadku ich prepíšu. Výsledky sa zapisujú priebežne; ak výstupný súbor
už existuje, hotové behy (inštancia, seed) sa preskočia – prerušený experiment sa dá dokončiť.

Spustenie (z koreňa repozitára):
    python src/run_experiments.py --instances "instances/generated/*.txt" --max-n 50 \
        --seeds 1 2 3 --out results/iga_ours.csv
"""

from __future__ import annotations

import argparse
import csv
import glob
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from iga import IGAParams, construct, iga                   # noqa: E402
from instance import read_instance                           # noqa: E402
from nonperm import nonperm_local_search                     # noqa: E402
from nps_set import nps_set                                  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# spoločné s reference/run_authors.py
COMMON = ["instance", "r", "n", "m", "seed", "construction_ft", "ls_ft",
          "iga0_ms", "iga0_ft", "nps0_ft", "nps_ms", "nps_ft", "iga_ms", "iga_ft",
          "iga_steps", "np_steps", "time"]
FIELDS = COMMON + ["time_phase1", "time_phase2", "time_found"]
HISTORY_FIELDS = ["instance", "seed", "iteration", "time", "ft"]


def run_one(args):
    path, seed, params = args
    inst = read_instance(path)
    p = inst.p
    t0 = time.perf_counter()
    res = iga(p, seed=seed, params=params)                    # 1. fáza → IGA0
    t1 = time.perf_counter()
    np_res = nonperm_local_search(p, res.perm)                # 2. fáza → IGA
    t2 = time.perf_counter()
    nps_ms, nps_ft = nps_set(p, res.perm)                     # ablácia IGA+NPS-set
    nps0_ft = nps_set(p, construct(p)[0])[1]                  # NPS-set z konštrukcie (kontrola)
    row = dict(instance=inst.name, r=inst.r, n=inst.n, m=inst.m, seed=seed,
               construction_ft=res.construction_ft, ls_ft=res.ls_ft,
               iga0_ms=res.ms, iga0_ft=res.ft, nps0_ft=nps0_ft, nps_ms=nps_ms, nps_ft=nps_ft,
               iga_ms=np_res.ms, iga_ft=np_res.ft, iga_steps=res.iterations,
               np_steps=np_res.steps, time=round(time.perf_counter() - t0, 6),
               time_phase1=round(t1 - t0, 6), time_phase2=round(t2 - t1, 6),
               time_found=round(res.time_found, 6))
    history = [dict(instance=inst.name, seed=seed, iteration=it, time=round(t, 6), ft=ft)
               for it, t, ft in res.history]
    return row, history


def load_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}


def done_runs(path: Path) -> set:
    if not path.exists():
        return set()
    with open(path, newline="") as f:
        return {(r["instance"], int(r["seed"])) for r in csv.DictReader(f)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "config" / "experiment.yaml"))
    ap.add_argument("--instances", nargs="+", default=None,
                    help="súbory alebo glob vzory (predvolene všetky v instances.dir z configu)")
    ap.add_argument("--seeds", nargs="+", type=int, default=None)
    ap.add_argument("--min-n", type=int, default=None, help="vynechať inštancie s menej jobmi")
    ap.add_argument("--max-n", type=int, default=None, help="vynechať inštancie s viac jobmi")
    ap.add_argument("--iter-factor", type=float, default=None)
    ap.add_argument("--sampling", choices=["uniform", "autori"], default="uniform",
                    help="výber odstránených jobov v perturbácii (src/iga.py); 'autori' len na experiment")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--out", default="results/iga_ours.csv")
    ap.add_argument("--history", default=None,
                    help="CSV s konvergenciou (predvolene <out>_history.csv)")
    args = ap.parse_args()

    cfg = load_config(Path(args.config))
    alg = cfg.get("algorithm", {})
    params = IGAParams(alpha=alg.get("alpha", IGAParams.alpha),
                       d_max=alg.get("d_max", IGAParams.d_max),
                       iter_factor=(args.iter_factor if args.iter_factor is not None
                                    else alg.get("iter_factor", IGAParams.iter_factor)),
                       sampling=args.sampling)
    seeds = args.seeds or cfg.get("experiment", {}).get("seeds", [1])
    patterns = args.instances or [str(Path(cfg.get("instances", {}).get("dir", "instances/generated"))
                                      / "*.txt")]

    paths = sorted({p for pat in patterns for p in glob.glob(pat)})
    sizes = {p: read_instance(p).p.shape for p in paths}      # (m, n)
    paths = [p for p in paths
             if (args.min_n is None or sizes[p][1] >= args.min_n)
             and (args.max_n is None or sizes[p][1] <= args.max_n)]
    # najväčšie inštancie najprv – lepšie rozloženie záťaže medzi procesy
    paths.sort(key=lambda p: -sizes[p][0] * sizes[p][1] ** 2)

    out = Path(args.out)
    hist = Path(args.history) if args.history else out.with_name(out.stem + "_history.csv")
    done = done_runs(out)
    tasks = [(p, s, params) for p in paths for s in seeds if (Path(p).stem, s) not in done]
    print(f"{len(paths)} inštancií × {len(seeds)} seedov, hotových {len(done)}, "
          f"zostáva {len(tasks)} behov, {args.jobs} procesov; {params}", flush=True)
    if not tasks:
        return

    out.parent.mkdir(parents=True, exist_ok=True)
    new_out, new_hist = not out.exists(), not hist.exists()
    t0 = time.time()
    with open(out, "a", newline="") as fo, open(hist, "a", newline="") as fh, \
            ProcessPoolExecutor(max_workers=args.jobs) as ex:
        wo = csv.DictWriter(fo, fieldnames=FIELDS)
        wh = csv.DictWriter(fh, fieldnames=HISTORY_FIELDS)
        if new_out:
            wo.writeheader()
        if new_hist:
            wh.writeheader()
        futures = [ex.submit(run_one, t) for t in tasks]
        for k, fut in enumerate(as_completed(futures), 1):
            row, history = fut.result()
            wo.writerow(row)
            wh.writerows(history)
            fo.flush()
            fh.flush()
            if k % max(1, len(tasks) // 50) == 0 or k == len(tasks):
                print(f"  {k}/{len(tasks)} hotových ({time.time() - t0:.0f} s)", flush=True)
    print("Uložené do", out, "a", hist)


if __name__ == "__main__":
    main()
