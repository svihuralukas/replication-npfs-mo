# Replikácia: IGA pre flow shop s chýbajúcimi operáciami (NPFS-MO)

Semestrálne zadanie 1 z predmetu **Metódy optimalizácie** – *Analýza a experimentálne riešenie
optimalizačnej úlohy*, **Variant A (replikácia výsledkov)**.

Tím: Lukáš Švihura, Dominik Keil, Ján Hrbál.

## Replikovaný článok

> M. Ritt, D. A. Rossit. *Effective heuristics for permutation and non-permutation flow shop
> scheduling with missing operations.* Computers & Operations Research 170 (2024), 106742.
> https://doi.org/10.1016/j.cor.2024.106742

Pôvodný kód (C++), inštancie a výsledky autorov po inštanciách: https://github.com/mrpritt/npfs-mo
(inštancie autori zverejnili na našu žiadosť 11. 11. 2026, pozri [instances/README.md](instances/README.md)).
Metóda, parametre aj referenčné výsledky v tomto repozitári pochádzajú z uvedeného článku.
Implementácia v `src/` je **naša vlastná** (Python), napísaná podľa opisu v článku.
Podrobne, čo je od koho, je v [ATTRIBUTION.md](ATTRIBUTION.md); literatúra reportu je v
[report/references.bib](report/references.bib).

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

Všetko z koreňa repozitára.

```bash
python -m pytest tests/                    # testy (143), vrátane zhody s kódom autorov
```

### Hlavný experiment: pôvodné inštancie autorov

```bash
python src/fetch_original.py               # inštancie H&N + výsledky článku po inštanciách (z repozitára autorov)
```

Experiment (naša implementácia aj program autorov, všetky n, seedy 1–10) bežal v Google Colabe:
[colab/README.md](colab/README.md), notebook `colab/povodne_instancie.ipynb`. To isté lokálne
(Linux/WSL alebo Docker pre program autorov, `reference/README.md`):

```bash
python src/run_experiments.py --instances "instances/original/*.txt" --seeds 1 2 3 4 5 6 7 8 9 10     --out results/original/iga_ours_local.csv
python3 reference/run_authors.py --instances "instances/original/*.txt" --seeds 1 2 3 4 5 6 7 8 9 10     --out results/original/iga_authors_local.csv
# doplnkový experiment: výber jobov v perturbácii ako v programe autorov (src/iga.py)
python src/run_experiments.py --instances "instances/original/*.txt" --min-n 30 --sampling autori     --seeds 1 2 3 4 5 6 7 8 9 10 --out results/original/iga_ours-sampling-autori_local.csv

python analysis/analyze_original.py        # tabuľky a grafy → results/original/analysis, report/
```

### Predbežný experiment: vlastné inštancie

```bash
python src/generate_instances.py           # vygeneruje 2160 inštancií do instances/generated/
python src/compare_instances.py --table2 data/authors/table2.csv   # porovnanie s originálmi

# IGA0, IGA+NPS-set a IGA naraz (parametre z config/experiment.yaml);
# priebežný zápis, prerušený beh sa po opätovnom spustení dokončí
python src/run_experiments.py --seeds 1 2 3 --out results/iga_ours.csv
python src/run_experiments.py --seeds 4 5 6 7 8 9 10 --max-n 50 --out results/iga_ours.csv
# to isté s programom autorov (Linux/WSL alebo Docker – reference/README.md)
python3 reference/run_authors.py --instances "instances/generated/*.txt" --seeds 1 2 3 --out reference/iga_authors.csv
python3 reference/run_authors.py --instances "instances/generated/*.txt" --seeds 4 5 6 7 8 9 10 --max-n 50     --out reference/iga_authors.csv
# seedy 4–10 pre n = 100 v Google Colabe: colab/README.md (výsledky v results/colab/)
python src/run_mip.py --instances "instances/generated/*_05_[0-9][0-9]_[0-9][0-9].txt" --out results/mip.csv  # optimá n = 5

python analysis/verify_exact.py            # presná zhoda deterministických častí s programom autorov
python analysis/analyze_results.py         # tabuľky, štatistiky, grafy → results/analysis, report/

# prvá kontrola IGA0 (results/iga0_check_*.csv) vznikla staršou verziou runnera (commit 56c39a8)
python analysis/compare_iga0.py            # porovnanie + Wilcoxonov test
```

### Report

`report/` je samostatný (main.tex, references.bib, tables/, figures/), dá sa nahrať do Overleafu.
Lokálne: `cd report && latexmk -pdf main.tex` (babel slovak – v Linuxe balík texlive-lang-czechslovak).

## Hlavné výsledky

Pôvodné inštancie H&N, naša implementácia aj program autorov so seedmi 1–10
(`results/original/analysis/summary.txt`, report `report/main.tex`):

| | naša (Python) | program autorov (C++) | článok |
|---|---|---|---|
| priemerná odchýlka od BKV: IGA0 | 2,36 % | 2,35 % | 2,36 % |
| IGA+NPS-set | 1,89 % | 1,88 % | 1,89 % |
| IGA | 1,04 % | 1,04 % | 1,05 % |
| IGA pri n = 5 od optima | 1,27 % | 1,27 % | 1,27 % |

- Program autorov so seedom 1 dá na všetkých 2160 inštanciách presne hodnoty z článku.
- Naša implementácia dá pri n = 5 vo všetkých 3600 behoch a pri n = 10 v 3592 z 3600 behov presne hodnotu IGA z článku
  (program autorov s inými seedmi než 1 v 3591 z 3600).
- Rozdiel naša − program autorov (IGA, pár = inštancia): 0,004 p. b., 95 % CI [−0,003; 0,011], Wilcoxon p = 0,17.

## Overenie po častiach

| Časť | Súbor | Stav |
|---|---|---|
| Generátor a načítanie inštancií | `src/instance.py`, `src/generate_instances.py` | hotové, overené voči dátam autorov |
| Výpočet C, C<sub>max</sub>, ΣC<sub>j</sub> | `src/evaluate.py` | hotové, zhoda s kódom autorov (Obr. 1, Obr. 3, 14 inštancií) |
| IGA fáza 1 (IGA0) | `src/iga.py` | hotové, konštrukcia a local search presne ako autori (144 inšt.), IGA0 štatisticky bez rozdielu (Wilcoxon p = 0,81) |
| IGA fáza 2 (non-permutation) | `src/nonperm.py` | hotové, z permutácie autorov presne ten istý rozvrh (86 inštancií zo všetkých 72 skupín) |
| NPS-set | `src/nps_set.py` | hotové, presná zhoda s kódom autorov (86 inštancií + konštrukcia na všetkých) |
| MIP (optimá pre n = 5) | `src/mip.py` | hotové, HiGHS namiesto CPLEX-u; Obr. 3 → 1191 |
| Predbežný experiment (vlastné inštancie) | `config/experiment.yaml`, `results/`, `reference/iga_authors.csv`, `results/colab/` | hotové: seedy 1–10 pre všetky n |
| Hlavný experiment (pôvodné inštancie) | `src/fetch_original.py`, `colab/povodne_instancie.ipynb`, `results/original/` | hotové: seedy 1–10 pre všetky n, obe implementácie |
| Analýza | `analysis/analyze_original.py` (pôvodné), `analysis/analyze_results.py` (vlastné) | hotové |
| Report | `report/main.tex` | hotové |

## Štruktúra

```
analysis/           analýza výsledkov (porovnania, štatistiky, grafy)
config/             parametre (generovanie inštancií, experimenty)
data/paper_results/ výsledky autorov prepísané z článku (Tab. 3, 4, 6)
data/authors/       výsledky článku po inštanciách (sťahuje src/fetch_original.py, nie je v gite)
instances/          inštancie: original/ (H&N, sťahuje src/fetch_original.py), generated/ (naše)
reference/          spúšťanie programu autorov a jeho výsledky na našich inštanciách
report/             záverečný report (LaTeX)
results/            výsledky experimentov (CSV, sú v gite): original/ hlavný, ostatné predbežný
src/                naša implementácia (instance, evaluate, iga, nonperm, nps_set, mip, run_experiments)
tests/              testy (príklady z článku, zhoda s kódom autorov, hrubá sila)
```
