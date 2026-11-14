# Pôvod jednotlivých častí riešenia

Zadanie vyžaduje, aby bolo zrejmé, čo vytvorili autori článku, čo pochádza z externých zdrojov
a čo sme vytvorili alebo upravili my. Tento súbor priebežne dopĺňame.

## Od autorov článku (Ritt & Rossit, 2024)

- Formulácia problému, reprezentácia pomocou pseudo-jobov, algoritmus IGA (obe fázy),
  hodnoty parametrov (`d = min{8, 0.8n}`, `α = 0.234375`, `15000/n` iterácií),
  metrika relatívnej odchýlky od najlepších známych hodnôt.
- Výsledky v `data/paper_results/` sú prepísané z tabuliek 3, 4 a 6 článku.
- **Pôvodné inštancie** Henneberg & Neufeld (2016) a výsledky článku po inštanciách (BKV, IGA,
  IGA0, IGA+NPS-set, časy, MIP) z repozitára autorov (commit `24b5d23`, zverejnené na našu
  žiadosť 11. 11. 2026). Nie sú v našom gite, sťahuje ich `src/fetch_original.py` do
  `instances/original/` a `data/authors/`.
- Pôvodný C++ kód: https://github.com/mrpritt/npfs-mo. Použitie:
  - **ako referencia:** skompilovaný program `npfsmo` spúšťame na našich inštanciách
    (`reference/run_authors.py`, `reference/make_eval_fixture.py`); jeho výstupy sú v
    `reference/*.csv`, `results/colab/iga_authors_*`, `results/original/iga_authors_*` a `tests/data/`.
    Jeho kód nie je súčasťou nášho riešenia ani skopírovaný.
  - **na doplnenie detailov, ktoré článok neuvádza** (štartovacie riešenie, ⌈0.8n⌉, pravidlo pre
    zhodu pri vkladaní, local search po pozíciách, limit + 1 iterácií; v 2. fáze poradie
    kandidátov a prijatie celého kroku; výber medzery v NPS-set) – zoznam v hlavičkách
    `src/iga.py`, `src/nonperm.py`, `src/nps_set.py`. Implementácia je napísaná
    nanovo v Pythone.
  - **MIP model** (`src/mip.py`) podľa Sekcie 3.3 článku, riešený solverom HiGHS (scipy) namiesto CPLEX-u.
  - **formát inštancií** podľa ich `instance.cpp` (aby ich program čítal naše inštancie).
  - **výber odstránených jobov ako v ich `random.hpp` (`sample_floyd`)** – voliteľný režim
    `--sampling autori` v `src/iga.py`, len na doplnkový experiment; predvolene vyberáme
    rovnomerne, ako hovorí článok.
- Výsledky po inštanciách (`npfs-mo/data/table2.csv`) sme použili na zistenie, koľko operácií
  v originálnych inštanciách chýba, a na porovnanie našich inštancií s originálmi.

## Z iných zdrojov

- Vlastné inštancie (predbežný experiment) generujeme podľa postupu Henneberg & Neufeld (2016)
  a Taillard (1993): procesné časy z U[1, 99], podiel chýbajúcich operácií r ∈ {0.2, 0.3, 0.4}.
- Vkladanie s anticipáciou/oneskorením: Benavides & Ritt (2015, 2018).
- Heuristika NPS-set: Pugazhendhi et al. (2003).
- Solver HiGHS (Huangfu & Hall, 2018) cez `scipy.optimize.milp`; Numba (Lam et al., 2015).
- Knižnice: pozri `requirements.txt`.

## Naša práca

- generátor a loader inštancií, stiahnutie a kontrola pôvodných inštancií
- výpočet ΣC<sub>j</sub> s chýbajúcimi operáciami
- implementácia IGA (fáza 1 a 2) a NPS-set v Pythone, vrátane zrýchlenia 2. fázy (prefixy, orezanie)
- spúšťanie programu autorov cez Docker, overenie presnej zhody
- spúšťanie experimentov (lokálne aj Colab notebooky), analýza a grafy
- report

## Použitie nástrojov generatívnej AI

Pri práci sme používali nástroje generatívnej AI ako asistenta pri programovaní, analýze aj písaní:

- **Kód a repozitár:** štruktúra repozitára a README, generátor a loader inštancií, výpočet ΣC,
  implementácia IGA a NPS-set, testy zhody s programom autorov, čítanie C++ kódu autorov
  (napr. výber jobov v perturbácii), skripty na stiahnutie inštancií a beh programu autorov,
  Colab notebooky a Docker postup.
- **Analýza:** skripty na štatistické vyhodnotenie (Wilcoxonov test, intervaly spoľahlivosti),
  tabuľky a grafy.
- **Report:** návrh a úprava textu, interpretácia výsledkov, LaTeX úpravy.
- **Kontrola:** review pull requestov, nezávislé prepočty výsledkov, overenie reprodukovateľnosti
  a kontrola, či čísla, tabuľky a grafy v reporte sedia s dátami a s článkom.

Návrhy AI sme vždy kontrolovali: spúšťaním testov, porovnaním s článkom a s programom autorov
a vzájomným review. Niektoré tvrdenia navrhnuté AI sa pri review ukázali ako nepresné (napr.
formulácia rozdielu voči programu autorov) a opravili sme ich. Rozhodnutia o postupe experimentov
a interpretácii výsledkov robil tím a za obsah zodpovedáme my.
