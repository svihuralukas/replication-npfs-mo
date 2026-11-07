# Pôvod jednotlivých častí riešenia

Zadanie vyžaduje, aby bolo zrejmé, čo vytvorili autori článku, čo pochádza z externých zdrojov
a čo sme vytvorili alebo upravili my. Tento súbor priebežne dopĺňame.

## Od autorov článku (Ritt & Rossit, 2024)

- Formulácia problému, reprezentácia pomocou pseudo-jobov, algoritmus IGA (obe fázy),
  hodnoty parametrov (`d = min{8, 0.8n}`, `α = 0.234375`, `15000/n` iterácií),
  metrika relatívnej odchýlky od najlepších známych hodnôt.
- Výsledky v `data/paper_results/` sú prepísané z tabuliek 3, 4 a 6 článku.
- Pôvodný C++ kód: https://github.com/mrpritt/npfs-mo. *(Ak z neho niečo použijeme alebo ho
  spustíme ako referenciu, uvedieme to tu.)*

## Z iných zdrojov

- Generovanie inštancií podľa Henneberg & Neufeld (2016) a Taillard (1993),
  procesné časy z U[1, 99], podiel chýbajúcich operácií r ∈ {0.2, 0.3, 0.4}.
- Vkladanie s anticipáciou/oneskorením: Benavides & Ritt (2015, 2018).
- Heuristika NPS-set: Pugazhendhi et al. (2003).
- Knižnice: pozri `requirements.txt`.

## Naša práca

- generátor a loader inštancií
- výpočet ΣC<sub>j</sub> s chýbajúcimi operáciami
- implementácia IGA (fáza 1 a 2) a NPS-set v Pythone
- spúšťanie experimentov, analýza a grafy
- report

## Použitie nástrojov generatívnej AI

*Doplní tím: ktoré nástroje, na čo a v akom rozsahu.*
