"""
Vytvorí testovacie dáta z PÔVODNÉHO programu autorov (npfsmo), aby sme mohli overiť,
že naša účelová funkcia (src/evaluate.py) počíta rovnako ako ich kód.

Pre vybrané inštancie spustí npfsmo, uloží ich nájdené riešenia (permutačné aj
non-permutation) a hodnoty ΣC, ktoré k nim vypočítal ich program.
Výstup: tests/data/authors_solutions.json (test potom beží aj bez ich programu, napr. na Windows).

Spúšťa sa v Linuxe/WSL z priečinka projekt/ (vyžaduje skompilovaný npfsmo):
    python3 reference/make_eval_fixture.py --npfsmo ../npfs-mo/build/npfsmo
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
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

        ps_lines = ps.read_text().splitlines()
        of = int(re.search(r"of=(\d+)", ps_lines[0]).group(1))   # ich ΣC permutácie
        perm = [int(x) for x in ps_lines[1].split()]

        orders = [[int(x) for x in line.split()] for line in s.read_text().splitlines() if line.strip()]
    return dict(perm=perm, perm_ft=of, orders=orders, final_ms=final_ms, final_ft=final_ft)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--npfsmo", default="../npfs-mo/build/npfsmo")
    ap.add_argument("--instances", default="instances/generated")
    ap.add_argument("--out", default="tests/data/authors_solutions.json")
    args = ap.parse_args()

    data = {}
    for name in INSTANCES:
        data[name] = run_npfsmo(args.npfsmo, Path(args.instances) / f"{name}.txt")
        print(name, "perm ΣC =", data[name]["perm_ft"], " final ΣC =", data[name]["final_ft"])

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(data, indent=1))
    print("Uložené do", args.out)


if __name__ == "__main__":
    main()
