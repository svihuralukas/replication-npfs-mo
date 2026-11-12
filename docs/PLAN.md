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
| 5 | IGA fáza 2 (anticipácia/oneskorenie) | `src/nonperm.py` | ✅ presná zhoda s kódom autorov (86 inštancií) |
| 6 | Ablácia IGA+NPS-set | `src/nps_set.py` | ✅ presná zhoda s kódom autorov |
| 7 | Runner, config, logovanie (čas, konvergencia, seed) | `src/run_experiments.py` | ✅ všetky varianty, resume |
| 8 | Referenčný beh C++ kódu autorov na našich inštanciách | `reference/run_authors.py` | ✅ (aj cez Docker, `reference/README.md`) |
| 8b | Presné optimá pre n = 5 (MIP, HiGHS) | `src/mip.py`, `src/run_mip.py` | ✅ |
| 9 | Predbežný experiment na našich inštanciách | `results/`, `reference/iga_authors.csv`, `results/colab/` | ✅ seedy 1–10 pre všetky n |
| 10 | Štatistiky, tabuľky, grafy, porovnanie s článkom | `analysis/analyze_results.py` | ✅ |
| 10b | **Hlavný experiment na pôvodných inštanciách** (zverejnené 11. 11. 2026) | `src/fetch_original.py`, `colab/povodne_instancie.ipynb`, `analysis/analyze_original.py`, `results/original/` | pripravené, čaká na beh v Colabe |
| 11 | Report (6–10 strán) | `report/main.tex` | doplniť výsledky na pôvodných inštanciách, skontrolovať tímom |
| 12 | Príprava na obhajobu | | |

## Metodológia experimentov

**Inštancie.** Hlavný experiment beží na **pôvodných** 2160 inštanciách Henneberg & Neufeld (2016),
ktoré autori na našu žiadosť zverejnili 11. 11. 2026 (`src/fetch_original.py` ich stiahne z ich
repozitára na pevnom commite spolu s výsledkami článku po inštanciách). Predtým sme pracovali
s vlastnými inštanciami vygenerovanými rovnakým postupom (n ∈ {5, 10, 20, 30, 50, 100},
m ∈ {5, 10, 20, 30}, U[1, 99], r ∈ {0.2, 0.3, 0.4}, 30 inštancií na skupinu, `instances/README.md`);
tento predbežný experiment ostáva v reporte ako doplnok (presná zhoda s programom autorov, MIP pre n = 5).

**Parametre** (podľa článku, sekcia 5.1): `d = min{8, ⌈0.8n⌉}`, `α = 0.234375`,
teplota `T = α · p̄ / 10`, rozpočet `15000/n` iterácií fázy 1. Sú v `config/experiment.yaml` a `src/iga.py` (`IGAParams`).

**Opakovania.** Autori použili jediný seed (1). My: seedy 1–10 na všetkých inštanciách, naša
implementácia aj pôvodný program autorov. Pôvodné inštancie: všetko v Google Colabe
(`colab/README.md`). Vlastné inštancie: notebook (i5-6300U, 4 paralelné behy) pre n ≤ 50
a seedy 1–3 pre n = 100, seedy 4–10 pre n = 100 v Colabe (`results/colab/`).
Uvádzame priemer, medián, smerodajnú odchýlku, minimum a maximum.

**BKV.** Pôvodné inštancie: najlepšie známe hodnoty z článku (`data/authors/table3-bkv.csv`),
takže odchýlky sú priamo porovnateľné s Tab. 3 a 6; pre n = 5 sú to optimá. Vlastné inštancie:
najlepšia hodnota zo všetkých našich behov a z MIP pre n = 5 (`results/mip.csv`, HiGHS,
356 z 360 inštancií optimálne).

**Metrika.** Relatívna odchýlka `(v − b)/b` v percentách od BKV, ako v článku.
Ďalej sledujeme čas behu, konvergenciu (ΣC<sub>j</sub> po iteráciách) a stabilitu medzi seedmi.

**Experimenty.**
1. IGA na všetkých skupinách, porovnanie s IGA a 2SA v Tab. 3 a s časmi v Tab. 4.
2. Ablácie IGA0 (len fáza 1) a IGA+NPS-set, porovnanie s Tab. 6.
3. *(voliteľne)* Vplyv rozpočtu (napr. 5× viac iterácií, ako IGA<sup>+</sup> v Tab. 5).

**Známe rozdiely oproti článku** (dokumentujeme v reporte):
- Python + numba namiesto C++, iný hardvér, takže časy nie sú priamo porovnateľné.
- Iný generátor náhodných čísel (NumPy PCG64 namiesto `std::mt19937`).
- Výber odstránených jobov v perturbácii: článok hovorí o náhodnom výbere, my vyberáme rovnomerne;
  program autorov (`sample_floyd` v `random.hpp`) vyberá posledné pozície o niečo zriedkavejšie.
  S 10 seedmi na vlastných inštanciách je naša implementácia pri n ≥ 30 horšia o ~0,01–0,03 p. b.
  (Wilcoxon p < 0,05); session 4 v Colabe overuje, či to spôsobuje práve tento výber
  (`--sampling autori`).

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

2. fáza (`ENPSolution::insert_all_ft`, `shift_step`):

- krok berie joby podľa **indexu** jobu 0..n-1 (nie podľa pozície),
- vybratý job sa vloží vždy na najlepšie z kandidátnych miest, aj keď je výsledok horší ako pred
  vybratím; až na konci kroku sa porovná ΣC – ak nie je ostro lepšie, celý krok sa zahodí,
- kandidáti sa vyhodnocujú v pevnom poradí a pri zhode (ΣC, potom Cmax) vyhráva prvý:
  pre k = n..1 straight(k) a anticipácie na strojoch m..2; potom pre k = n..2 oneskorenia
  na strojoch 2..m (presné definície v hlavičke `src/nonperm.py`),
- štart z najlepšej permutácie 1. fázy, stop v prvom lokálnom minime.

NPS-set (`PSolution::evaluateNPSset`, `holes.cpp`): medzera s najmenším začiatkom, do ktorej sa
operácia zmestí po čase pripravenosti jobu, t. j. najskorší prípustný začiatok operácie.

## Vyriešené otázky

- Formát inštancií: rovnaký ako H&N / autorov, pozri `instances/README.md`.
- C++ kód autorov sa dá skompilovať (Boost, CMake, CPLEX netreba; treba `-DBOOST_ROOT=/usr`).
- V originálnych inštanciách chýba presne round_half_up(r·n·m) operácií (zistené z ich `table2.csv`).
- Pôvodné inštancie autori zverejnili 11. 11. 2026 (commit `24b5d23`); pomenovanie `r_n_m_i.txt` je rovnaké ako naše.
- Termín odovzdania a obhajoby: doplniť.
