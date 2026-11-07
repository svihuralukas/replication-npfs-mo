"""
Vygeneruje celú sadu inštancií podľa config/instances.yaml.

Spustenie (z priečinka projekt/):
    python src/generate_instances.py
    python src/generate_instances.py --config config/instances.yaml
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from instance import generate_instance, instance_name, instance_rng, write_instance


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="config/instances.yaml")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    count = 0
    for r in cfg["r_values"]:
        for n in cfg["n_values"]:
            for m in cfg["m_values"]:
                for i in range(cfg["instances_per_group"]):
                    name = instance_name(r, n, m, i)
                    rng = instance_rng(cfg["base_seed"], r, n, m, i)
                    inst = generate_instance(n, m, r, rng, cfg["p_min"], cfg["p_max"], name)
                    write_instance(inst, out / f"{name}.txt")
                    count += 1

    print(f"Vygenerovaných {count} inštancií do {out}/")


if __name__ == "__main__":
    main()
