# Plán práce

Variant A – replikácia výsledkov článku Ritt & Rossit (2024) [`RittRossit2024`].
Na obhajobe musí **každý rozumieť celému riešeniu**: kódu, nastaveniu experimentov aj
interpretácii výsledkov.

## Fázy

| # | Fáza | Výstup | Stav |
|---|------|--------|------|
| 0 | Schválenie článku a rozsahu experimentov vyučujúcim | e-mail / konzultácia | |
| 1 | Analýza problému (formulácia, typ, premenné, obmedzenia, fitness) | report sekcie 2–3 | |
| 2 | Inštancie: generátor, formát, loader | `src/instance.py`, `src/generate_instances.py` | ✅ |
| 3 | Výpočet ΣC<sub>j</sub> s chýbajúcimi operáciami + testy z Obr. 1 a 3 | `src/evaluate.py` | ✅ |
| 4 | IGA fáza 1 (permutačný priestor) | `src/iga.py` | ✅ |
| 5 | IGA fáza 2 (anticipácia/oneskorenie) | `src/nonperm.py` | rozpracované |
| 6 | Ablácia IGA+NPS-set | `src/nps_set.py` | |
| 7 | Runner, config, logovanie (čas, konvergencia, seed) | `src/run_experiments.py` | čiastočne (IGA0) |
| 8 | Referenčný beh C++ kódu autorov na našich inštanciách | `reference/run_authors.py` | ✅ skompilované a overené |
| 9 | Experimenty | `results/` | |
| 10 | Štatistiky, tabuľky, grafy, porovnanie s článkom | `analysis/` | |
| 11 | Report (6–10 strán) | `report/main.tex` | |
| 12 | Príprava na obhajobu | | |

## Metodológia experimentov

**Inštancie.** Generujeme ich rovnako ako Henneberg & Neufeld (2016):
n ∈ {5, 10, 20, 30, 50, 100}, m ∈ {5, 10, 20, 30}, procesné časy U[1, 99],
podiel chýbajúcich operácií r ∈ {0.2, 0.3, 0.4}, 30 inštancií na skupinu, spolu 2160.
Generátor, formát a seed sú zdokumentované v `instances/README.md`.

Pozor: najlepšie známe hodnoty (BKV) z článku platia len pre **originálne** inštancie H&N.
Tie v repozitári autorov **nie sú** (je tam kód a výsledky po inštanciách, nie inštancie),
autorov sme o ne požiadali. Dovtedy porovnávame na našich inštanciách, na ktorých spúšťame
aj pôvodný C++ program autorov – obe implementácie tak riešia tie isté dáta. BKV na našich
inštanciách = najlepšia hodnota zo všetkých behov (naších aj autorov). S Tab. 3 a 6 článku
porovnávame priemery po skupinách.

**Parametre** (podľa článku, sekcia 5.1): `d = min{8, ⌈0.8n⌉}`, `α = 0.234375`,
teplota `T = α · p̄ / 10`, rozpočet `15000/n` iterácií fázy 1. Sú v `config/experiment.yaml` a `src/iga.py` (`IGAParams`).

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

## Detaily doplnené z kódu autorov

Článok niektoré detaily neuvádza; prevzali sme ich z pôvodnej implementácie
(`npfs-mo/src/npfsmo.cpp`, `heuristics.cpp`) a overili presnou zhodou výsledkov:

- štartovacie riešenie: joby podľa celkového času spracovania zostupne (pri zhode menší index),
  potom postupné vkladanie na najlepšiu pozíciu,
- d = min(8, ⌈0.8n⌉),
- najlepšia pozícia pri vkladaní: min ΣC, potom min C<sub>max</sub>; pri úplnej zhode vyhráva
  najzadnejšia pozícia (autori skúmajú pozície od konca),
- shift local search berie joby podľa **pozícií** 1..n, nie podľa indexov jobov,
- vykoná sa limit + 1 iterácií (cyklus končí, až keď počet krokov prekročí limit).

## Vyriešené otázky

- Formát inštancií: rovnaký ako H&N / autorov, pozri `instances/README.md`.
- C++ kód autorov sa dá skompilovať (Boost, CMake, CPLEX netreba; treba `-DBOOST_ROOT=/usr`).
- V originálnych inštanciách chýba presne round_half_up(r·n·m) operácií (zistené z ich `table2.csv`).
- Termín odovzdania a obhajoby: doplniť.
