"""
Vytvorí testovacie dáta z PÔVODNÉHO programu autorov (npfsmo), aby sme mohli overiť,
že naša účelová funkcia (src/evaluate.py) počíta rovnako ako ich kód.

Pre vybrané inštancie spustí npfsmo, uloží ich nájdené riešenia (permutačné aj
non-permutation) a hodnoty ΣC, ktoré k nim vypočítal ich program:
    perm, perm_ft       permutácia z 1. fázy (vstup 2. fázy aj NPS-set) a jej ΣC
    orders              finálny nepermutačný rozvrh po 2. fáze (riadok = stroj)
    final_ms, final_ft  jeho Cmax a ΣC
    nps_ms, nps_ft      NPS-set aplikovaný na perm (ablácia IGA+NPS-set)
    nps0_ft             NPS-set aplikovaný na štartovaciu konštrukciu (deterministické)
Výstup: tests/data/authors_solutions.json (test potom beží aj bez ich programu, napr. na Windows).
S --glob sa dá vytvoriť väčšia sada na overenie (reference/authors_phase2_check.json).

Spúšťa sa v Linuxe/WSL z priečinka projekt/ (vyžaduje skompilovaný npfsmo):
    python3 reference/make_eval_fixture.py --npfsmo ../npfs-mo/build/npfsmo
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

INSTANCES = [
    "0.2_05_05_00", "0.3_05_10_01", "0.4_05_20_02",
    "0.2_10_05_03", "0.3_10_10_04", "0.4_10_20_05",
    "0.2_20_05_06", "0.3_20_10_07", "0.4_20_30_08",
    "0.2_30_20_09", "0.3_50_10_10", "0.4_50_30_11",
    "0.2_100_05_12", "0.3_100_20_13",
]


def run_npfsmo(binary: str, inst: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        ps, s = Path(tmp) / "ps.txt", Path(tmp) / "s.txt"
        out = subprocess.run(
            [binary, "--flowtime", "--timelimit", "-1", "--iterfactor", "0.1", "--npfs",
             "--psolution", str(ps), "--solution", str(s), str(inst)],
            capture_output=True, text=True, check=True).stdout
        info = next(l for l in out.splitlines() if l.startswith("INFO")).split()
        # INFO <inštancia> (Cmax ΣC čas)... ; posledná trojica = finálne non-permutation riešenie
        final_ms, final_ft = int(info[-3]), int(info[-2])
        # NPSSET: (Cmax ΣC) pre konštrukciu, výsledok IGA (= perm) a IGA-SO
        npsset = [int(x) for x in next(l for l in out.splitlines() if l.startswith("NPSSET")).split()[1:]]

        ps_lines = ps.read_text().splitlines()
        of = int(re.search(r"of=(\d+)", ps_lines[0]).group(1))   # ich ΣC permutácie
        perm = [int(x) for x in ps_lines[1].split()]

        orders = [[int(x) for x in line.split()] for line in s.read_text().splitlines() if line.strip()]
    return dict(perm=perm, perm_ft=of, orders=orders, final_ms=final_ms, final_ft=final_ft,
                nps_ms=npsset[2], nps_ft=npsset[3], nps0_ft=npsset[1])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--npfsmo", default="../npfs-mo/build/npfsmo")
    ap.add_argument("--instances", default="instances/generated")
    ap.add_argument("--glob", default=None, help="namiesto pevného zoznamu: inštancie podľa vzoru")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--out", default="tests/data/authors_solutions.json")
    args = ap.parse_args()

    names = (sorted(Path(x).stem for x in glob.glob(str(Path(args.instances) / args.glob)))
             if args.glob else INSTANCES)
    paths = [Path(args.instances) / f"{name}.txt" for name in names]
    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        sols = list(ex.map(run_npfsmo, [args.npfsmo] * len(paths), paths))
    data = {}
    for name, sol in zip(names, sols):
        data[name] = sol
        print(name, "perm ΣC =", sol["perm_ft"], " final ΣC =", sol["final_ft"], " NPS-set ΣC =", sol["nps_ft"])

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(data, indent=1))
    print("Uložené do", args.out)


if __name__ == "__main__":
    main()
