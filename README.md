# Replikácia: IGA pre flow shop s chýbajúcimi operáciami (NPFS-MO)

Semestrálne zadanie 1 z predmetu **Metódy optimalizácie** – *Analýza a experimentálne riešenie
optimalizačnej úlohy*, **Variant A (replikácia výsledkov)**.

Tím: Lukáš, Dominik, Jano.

## Replikovaný článok

> M. Ritt, D. A. Rossit. *Effective heuristics for permutation and non-permutation flow shop
> scheduling with missing operations.* Computers & Operations Research 170 (2024), 106742.
> https://doi.org/10.1016/j.cor.2024.106742

Pôvodný kód (C++), inštancie a výsledky autorov: https://github.com/mrpritt/npfs-mo.
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
pip install -e .
```

## Spustenie

```bash
pytest                                                  # testy
python scripts/run_experiments.py --config configs/default.yaml   # experimenty -> results/
python scripts/analyze.py                               # tabuľky a grafy pre report
```

> Skripty sú zatiaľ kostra, algoritmy ešte nie sú implementované.

## Štruktúra

```
configs/            parametre experimentov (YAML)
data/instances/     problémové inštancie (2160, formát podľa H&N 2016)
data/paper_results/ výsledky autorov prepísané z článku (Tab. 3, 4, 6)
docs/PLAN.md        plán, metodológia
report/             záverečný report (LaTeX)
results/            výstupy experimentov (negenerujú sa do gitu)
scripts/            spúšťanie experimentov a analýza
src/npfsmo/         naša implementácia
tests/              testy (príklady z článku)
```
