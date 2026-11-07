# Plán práce

Variant A – replikácia výsledkov článku Ritt & Rossit (2024) [`RittRossit2024`].
Na obhajobe musí **každý rozumieť celému riešeniu**: kódu, nastaveniu experimentov aj
interpretácii výsledkov.

## Fázy

| # | Fáza | Výstup | Termín |
|---|------|--------|--------|
| 0 | Schválenie článku a rozsahu experimentov vyučujúcim | e-mail / konzultácia | |
| 1 | Analýza problému (formulácia, typ, premenné, obmedzenia, fitness) | report sekcie 2–3 | |
| 2 | Inštancie: generátor, formát, loader, nahratie do `data/instances/` | `instance.py`, dáta | |
| 3 | Výpočet ΣC<sub>j</sub> s chýbajúcimi operáciami + testy z Obr. 1 a 3 | `evaluate.py` | |
| 4 | IGA fáza 1 (permutačný priestor) | `iga.py` | |
| 5 | IGA fáza 2 (pseudo-joby, anticipácia/oneskorenie) | `nonperm.py` | |
| 6 | Ablácia IGA+NPS-set | `nps_set.py` | |
| 7 | Runner, config, logovanie (čas, konvergencia, seed) | `scripts/run_experiments.py` | |
| 8 | Referenčný beh C++ kódu autorov na našich inštanciách (ak sa podarí skompilovať) | `results/reference/` | |
| 9 | Experimenty | `results/` | |
| 10 | Štatistiky, tabuľky, grafy, porovnanie s článkom | `scripts/analyze.py` | |
| 11 | Report (6–10 strán) | `report/main.tex` | |
| 12 | Príprava na obhajobu | | |

## Metodológia experimentov

**Inštancie.** Generujeme ich rovnako ako Henneberg & Neufeld (2016):
n ∈ {5, 10, 20, 30, 50, 100}, m ∈ {5, 10, 20, 30}, procesné časy U[1, 99],
podiel chýbajúcich operácií r ∈ {0.2, 0.3, 0.4}, 30 inštancií na skupinu, spolu 2160.
Generátor a seed musia byť zdokumentované v `data/instances/README.md`.

Pozor: najlepšie známe hodnoty (BKV) z článku platia len pre **originálne** inštancie H&N.
Pre férové porovnanie s Tab. 3 a 6 preto použijeme aj podmnožinu originálnych inštancií
z https://github.com/mrpritt/npfs-mo. Na našich inštanciách bude BKV najlepšia hodnota
zo všetkých našich behov (prípadne aj z behu C++ kódu autorov).

**Parametre** (podľa článku, sekcia 5.1): `d = min{8, 0.8n}`, `α = 0.234375`,
teplota `T = α · p̄ / 10`, rozpočet `15000/n` iterácií fázy 1. Sú v `configs/default.yaml`.

**Opakovania.** Autori použili jediný seed (1). My spustíme každý experiment s 10 seedmi
(1–10) a uvedieme priemer, medián, smerodajnú odchýlku, minimum a maximum.

**Metrika.** Relatívna odchýlka `(v − b)/b` v percentách od BKV, ako v článku.
Ďalej sledujeme čas behu, konvergenciu (ΣC<sub>j</sub> po iteráciách) a stabilitu medzi seedmi.

**Experimenty.**
1. IGA na všetkých skupinách, porovnanie s IGA a 2SA v Tab. 3 a s časmi v Tab. 4.
2. Ablácie IGA0 (len fáza 1) a IGA+NPS-set, porovnanie s Tab. 6.
3. *(voliteľne)* Vplyv rozpočtu (napr. 5× viac iterácií, ako IGA<sup>+</sup> v Tab. 5).

**Známe rozdiely oproti článku** (dokumentujeme v reporte):
- Python + numba namiesto C++, iný hardvér, takže časy nie sú priamo porovnateľné.
- Ak bude výpočet príliš pomalý, zmenšíme výber inštancií (napr. n ≤ 50 alebo menej inštancií
  na skupinu) a zdokumentujeme to.
- Zrýchlenie podľa Duan et al. (2013) implementujeme len ak bude čas.

## Otvorené otázky

- Formát našich inštancií: zhoduje sa s formátom H&N / autorov?
- Podarí sa skompilovať C++ kód autorov (Boost, CMake; CPLEX netreba)?
- Termín odovzdania a obhajoby: doplniť.
