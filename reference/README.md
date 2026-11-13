# Referenčné behy pôvodného programu autorov

Pôvodný C++ program autorov (`npfsmo`, https://github.com/mrpritt/npfs-mo) spúšťame na tých
istých inštanciách a s tými istými seedmi ako našu implementáciu. Slúži na overenie našej
implementácie (presná zhoda deterministických častí, štatistická zhoda náhodných). Na pôvodných
inštanciách so seedom 1 dáva presne hodnoty z článku. Tento priečinok obsahuje behy na vlastných
inštanciách (predbežný experiment); behy na pôvodných inštanciách sú v `results/original/`.

| Súbor | Obsah | Vytvoril |
|---|---|---|
| `iga0_check_authors.csv` | prvá kontrola: 120 inštancií × seedy 1–5, porovnávalo sa len IGA0 | `run_authors.py` |
| `iga_authors.csv` | predbežný experiment (IGA0, IGA+NPS-set, IGA), všetky vlastné inštancie | `run_authors.py` |
| `authors_phase2_check.json` | permutácia z 1. fázy, finálny rozvrh 2. fázy a NPS-set pre 72 inštancií (`*_15`, jedna z každej skupiny), seed 1 | `make_eval_fixture.py --glob "*_15.txt"` |

Stĺpce CSV sú opísané v hlavičke `run_authors.py`; sú rovnaké ako v `results/iga_ours.csv`.

## Spustenie cez Docker (Windows bez WSL distribúcie, Linux, macOS)

```bash
# obraz s kompilátorom a Boostom
docker build -t npfsmo-build - <<'EOF'
FROM ubuntu:24.04
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential cmake python3 libboost-program-options-dev libboost-timer-dev \
    libboost-system-dev libboost-chrono-dev libboost-filesystem-dev && rm -rf /var/lib/apt/lists/*
EOF

# kód autorov vedľa tohto repozitára a kompilácia
git clone https://github.com/mrpritt/npfs-mo ../npfs-mo && (cd ../npfs-mo && git submodule update --init)
docker run --rm -v "$(pwd)/../npfs-mo:/npfs-mo" npfsmo-build bash -c \
    "cd /npfs-mo && cmake -DCMAKE_BUILD_TYPE=Release -DBOOST_ROOT=/usr -S src -B build && cmake --build build -j4"

# behy (z koreňa repozitára); v Git Bash na Windows treba pred príkaz dať MSYS_NO_PATHCONV=1
docker run --rm -v "$(pwd)/../npfs-mo:/npfs-mo" -v "$(pwd):/proj" -w /proj npfsmo-build \
    python3 reference/run_authors.py --npfsmo /npfs-mo/build/npfsmo \
    --instances "instances/generated/*.txt" --seeds 1 2 3 --out reference/iga_authors.csv
```

V WSL/Linuxe s nainštalovanými balíkmi stačí postup z hlavného `README.md`.
