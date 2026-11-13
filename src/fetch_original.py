"""
Stiahne pôvodné inštancie Henneberg & Neufeld (2016) a výsledky autorov po inštanciách
z repozitára autorov (https://github.com/mrpritt/npfs-mo) na pevnom commite a skontroluje ich.

    instances/original/*.txt   2160 inštancií (formát a pomenovanie v instances/README.md)
    data/authors/*.csv         výsledky článku po inštanciách (BKV, IGA, IGA0, IGA+NPS-set, časy, ...)

Súbory nie sú v našom repozitári (patria autorom), skript ich vždy stiahne z toho istého commitu.

Spustenie (z koreňa repozitára):
    python src/fetch_original.py
"""

from __future__ import annotations

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from instance import read_instance       # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
COMMIT = "24b5d234f0b7844ef7c8bb6ee2fb42df6b55c7ab"     # 2026-11-11 „Add Henneberg and Neufeld benchmark instances“
URL = f"https://github.com/mrpritt/npfs-mo/archive/{COMMIT}.zip"


def instance_path(r: float, n: int, m: int, i: int) -> Path:
    return ROOT / "instances" / "original" / f"{r:.1f}_{n:02d}_{m:02d}_{i:02d}.txt"


def main() -> None:
    inst_dir, data_dir = ROOT / "instances" / "original", ROOT / "data" / "authors"
    print("Sťahujem", URL)
    with urllib.request.urlopen(URL) as resp:
        z = zipfile.ZipFile(io.BytesIO(resp.read()))
    for d in (inst_dir, data_dir):
        d.mkdir(parents=True, exist_ok=True)       # existujúce súbory sa prepíšu
    prefix = f"npfs-mo-{COMMIT}/"
    for name in z.namelist():
        rel = name[len(prefix):]
        if rel.startswith("instances/") and rel.endswith(".txt"):
            (inst_dir / Path(rel).name).write_bytes(z.read(name))
        elif rel.startswith("data/") and rel.endswith(".csv"):
            (data_dir / Path(rel).name).write_bytes(z.read(name))

    # kontrola: všetky inštancie z table2.csv autorov existujú a sedí počet operácií,
    # počet pseudo jobov aj priemerný čas operácie
    t2 = pd.read_csv(data_dir / "table2.csv")
    bad = 0
    for row in t2.itertuples():
        inst = read_instance(instance_path(row.d, row.n, row.m, row.i))
        ok = ((inst.n, inst.m) == (row.n, row.m) and int(inst.present.sum()) == row.effops
              and inst.num_pseudo_jobs() == row.pj and round(inst.p[inst.present].mean()) == row._5)
        bad += not ok
    n_files = len(list(inst_dir.glob("*.txt")))
    print(f"{n_files} inštancií v {inst_dir}, {len(list(data_dir.glob('*.csv')))} CSV v {data_dir}")
    if n_files != 2160 or bad:
        sys.exit(f"CHYBA: {bad} inštancií nesedí s table2.csv autorov")
    print("Kontrola voči table2.csv autorov: OK")


if __name__ == "__main__":
    main()
