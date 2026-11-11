# Replikácia: IGA pre flow shop s chýbajúcimi operáciami (NPFS-MO)

Semestrálne zadanie 1 z predmetu **Metódy optimalizácie** – *Analýza a experimentálne riešenie
optimalizačnej úlohy*, **Variant A (replikácia výsledkov)**.

Tím: Lukáš, Dominik, Jano.

## Replikovaný článok

> M. Ritt, D. A. Rossit. *Effective heuristics for permutation and non-permutation flow shop
> scheduling with missing operations.* Computers & Operations Research 170 (2024), 106742.
> https://doi.org/10.1016/j.cor.2024.106742

Pôvodný kód (C++) a výsledky autorov po inštanciách: https://github.com/mrpritt/npfs-mo
(samotné inštancie tam nie sú, pozri [instances/README.md](instances/README.md)).
Metóda, parametre aj referenčné výsledky v tomto repozitári pochádzajú z uvedeného článku.
Implementácia v `src/` je **naša vlastná** (Python), napísaná podľa opisu v článku.
Podrobne, čo je od koho, je v [ATTRIBUTION.md](ATTRIBUTION.md); všetky referencie sú v
[CITATION.bib](CITATION.bib).

## Problém v skratke

Flow shop s *n* jobmi a *m* strojmi, kde niektoré joby niektoré operácie vynechávajú (*missing
operations*, nie operácie s nulovým časom). Minimalizuje sa celkový čas dokončenia
ΣC<sub>j</sub> (v notácii F | skip | ΣC<sub>j</sub>). Riešenia môžu byť nepermutačné (iné poradie
jobov na rôznych strojoch), reprezentované pomocou *pseudo-jobov*.

Metóda autorov (IGA) má dve fázy:
1. **Iterated greedy** v permutačnom priestore (destrukcia/rekonštrukcia, shift local search,
   Metropolisovo akceptačné kritérium).
2. **Lokálne prehľadávanie v nepermutačnom priestore** – vkladanie *straight*, *s anticipáciou*
   a *s oneskorením*.

Plán práce a metodológia: [docs/PLAN.md](docs/PLAN.md).

## Príprava prostredia

Python 3.10–3.13.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
```

Referenčný C++ program autorov (voliteľné, len na porovnanie; v Linuxe alebo vo WSL):

```bash
git clone https://github.com/mrpritt/npfs-mo ../npfs-mo     # vedľa tohto repozitára
sudo apt install build-essential cmake libboost-program-options-dev libboost-timer-dev \
    libboost-system-dev libboost-chrono-dev libboost-filesystem-dev
cd ../npfs-mo && git submodule update --init
cmake -DCMAKE_BUILD_TYPE=Release -DBOOST_ROOT=/usr -S src -B build   # -DBOOST_ROOT je nutné
cmake --build build -j4
./build/npfsmo --flowtime --timelimit -1 --iterfactor 0.1 --npfs ../<tento-repo>/tests/fig3.txt
# v riadku INFO musí byť na konci ΣC = 1191 (optimum z Obr. 3 článku)
```

## Spustenie

Všetko z koreňa repozitára:

```bash
python -m pytest tests/                    # testy (142), vrátane zhody s kódom autorov
python src/generate_instances.py           # vygeneruje 2160 inštancií do instances/generated/
python src/compare_instances.py            # porovnanie s originálnymi inštanciami (vyžaduje ../npfs-mo)

# 2. etapa – plné experimenty: IGA0, IGA+NPS-set a IGA naraz (parametre z config/experiment.yaml);
# priebežný zápis, prerušený beh sa po opätovnom spustení dokončí
python src/run_experiments.py --seeds 1 2 3 --out results/iga_ours.csv
python src/run_experiments.py --seeds 4 5 6 7 8 9 10 --max-n 50 --out results/iga_ours.csv
# to isté s programom autorov (Linux/WSL alebo Docker – reference/README.md)
python3 reference/run_authors.py --instances "instances/generated/*.txt" --seeds 1 2 3 --out reference/iga_authors.csv
python3 reference/run_authors.py --instances "instances/generated/*.txt" --seeds 4 5 6 7 8 9 10 --max-n 50 \
    --out reference/iga_authors.csv
# seedy 4–10 pre n = 100 v Google Colabe: colab/README.md (výsledky do results/colab/)
python src/run_mip.py --instances "instances/generated/*_05_[0-9][0-9]_[0-9][0-9].txt" --out results/mip.csv  # optimá n = 5

python analysis/verify_exact.py            # presná zhoda deterministických častí s programom autorov
python analysis/analyze_results.py         # tabuľky, štatistiky, grafy → results/analysis, report/
# PDF reportu: cd report && latexmk -pdf main.tex  (babel slovak – v Linuxe balík texlive-lang-czechslovak)

# 1. etapa (IGA0, results/iga0_check_*.csv) vznikla staršou verziou runnera (commit 56c39a8)
python analysis/compare_iga0.py            # porovnanie + Wilcoxonov test
```

## Stav

| Časť | Súbor | Stav |
|---|---|---|
| Generátor a načítanie inštancií | `src/instance.py`, `src/generate_instances.py` | hotové, overené voči dátam autorov |
| Výpočet C, C<sub>max</sub>, ΣC<sub>j</sub> | `src/evaluate.py` | hotové, zhoda s kódom autorov (Obr. 1, Obr. 3, 14 inštancií) |
| IGA fáza 1 (IGA0) | `src/iga.py` | hotové, konštrukcia a local search presne ako autori (144 inšt.), IGA0 štatisticky bez rozdielu (Wilcoxon p = 0,81) |
| IGA fáza 2 (non-permutation) | `src/nonperm.py` | hotové, z permutácie autorov presne ten istý rozvrh (86 inštancií zo všetkých 72 skupín) |
| NPS-set | `src/nps_set.py` | hotové, presná zhoda s kódom autorov (86 inštancií + konštrukcia na všetkých) |
| MIP (optimá pre n = 5) | `src/mip.py` | hotové, HiGHS namiesto CPLEX-u; Obr. 3 → 1191 |
| Konfigurácia experimentov, plné experimenty | `config/experiment.yaml`, `results/`, `reference/iga_authors.csv` | hotové: seedy 1–10 pre n ≤ 50, 1–3 pre n = 100 |
| Analýza | `analysis/analyze_results.py`, `results/analysis/` | hotové |
| Report | `report/main.tex` | návrh, treba skontrolovať tímom |

## Štruktúra

```
analysis/           analýza výsledkov (porovnania, štatistiky, grafy)
config/             parametre (generovanie inštancií, experimenty)
data/paper_results/ výsledky autorov prepísané z článku (Tab. 3, 4, 6)
docs/PLAN.md        plán, metodológia
instances/          inštancie: generated/ (naše), original/ (H&N, ak ich dostaneme)
reference/          spúšťanie programu autorov a jeho výsledky na našich inštanciách
report/             záverečný report (LaTeX)
results/            výsledky našich experimentov (CSV, sú v gite)
src/                naša implementácia (instance, evaluate, iga, nonperm, nps_set, mip, run_experiments)
tests/              testy (príklady z článku, zhoda s kódom autorov, hrubá sila)
```
