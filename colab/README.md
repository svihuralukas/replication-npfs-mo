# Doplnenie seedov 4–10 pre n = 100 v Google Colabe

Na notebooku máme pre n = 100 len seedy 1–3 (jeden beh n = 100, m = 30 trvá asi minútu,
7 ďalších seedov pre obe implementácie by trvalo ~10 h). Notebook
[`n100_seedy.ipynb`](n100_seedy.ipynb) dobehne zvyšné seedy v Colabe – našu implementáciu
aj pôvodný C++ program autorov – a výsledky ukladá na Google Drive.

**Otvoriť v Colabe:**
https://colab.research.google.com/github/svihuralukas/replication-npfs-mo/blob/main/colab/n100_seedy.ipynb
(kým nie je PR #1 zlúčený do `main`, použi
https://colab.research.google.com/github/svihuralukas/replication-npfs-mo/blob/etapa-2-faza2-npsset/colab/n100_seedy.ipynb;
notebook sám klonuje `main` a ak tam 2. etapa ešte nie je, použije vetvu PR)

## Postup

1. Otvor odkaz vyššie (prihlásený do Google účtu s Colab Pro).
2. **Runtime → Change runtime type → CPU** (GPU ani TPU netreba – kód beží len na procesore;
   ak je k dispozícii *High-RAM*, zapni ho – zvyčajne dá viac jadier a notebook ich využije sám).
3. V prvej bunke nastav `SEEDS` – **každá session iné seedy**, napr.:

   | session | `SEEDS` |
   |---|---|
   | 1 | `[4, 5]` |
   | 2 | `[6, 7]` |
   | 3 | `[8, 9]` |
   | 4 | `[10]` |

   Koľko session naraz Colab Pro dovolí, závisí od aktuálnych limitov účtu – ak len jednu,
   daj do nej viac seedov (napr. `[4, 5, 6, 7]`) a zvyšok spusti ďalšiu noc.
4. **Runtime → Run all.** Na začiatku vyskočí okno na povolenie prístupu k Google Drive – potvrď.
5. Počkaj, kým prebehne bunka 4 (**Kontrola prostredia**, ~3 min). Musí vypísať
   `Prostredie je v poriadku.` Ak vypíše `NEZHODA` alebo chybu, nič ďalej nespúšťaj a pošli mi výstup.
6. Bunka 5 je hlavný beh. Nechaj **kartu prehliadača otvorenú a počítač zapnutý** (Colab Pro
   pri zatvorenej karte runtime po čase odpojí). Ak sa runtime odpojí, stačí znova **Run all**
   s rovnakými `SEEDS` – hotové behy sa preskočia.

## Odhad času

Na štandardnom CPU runtime (2 vCPU) približne **3 h na jeden seed** (naša implementácia ~1,5 h
+ program autorov ~1,5 h; namerané v simulácii Colabu – Ubuntu 22.04, 2 CPU). Session so
`SEEDS = [4, 5]` teda ~6 h, čo sa zmestí do noci. S High-RAM (viac jadier) úmerne rýchlejšie.
Prípravné bunky 1–4 trvajú spolu ~5 min. Priebeh vidno vo výstupe bunky 5 (`k/360 hotových`).

## Výstupy (na Google Drive, priečinok `npfs-mo-colab/`)

| súbor | obsah |
|---|---|
| `iga_ours_colab_s4-5.csv` | naša implementácia, 360 riadkov na seed (rovnaké stĺpce ako `results/iga_ours.csv`) |
| `iga_ours_colab_s4-5_history.csv` | konvergencia 1. fázy |
| `iga_authors_colab_s4-5.csv` | program autorov (rovnaké stĺpce ako `reference/iga_authors.csv`) |
| `info_s4-5.txt` | čas začiatku/konca, model CPU, počet jadier |

Bunka 6 vypíše, koľko riadkov je hotových pre každý seed (cieľ: 360 v oboch súboroch).

## Ráno

Stiahni celý priečinok `npfs-mo-colab` z Drive a skopíruj súbory do **`results/colab/`**
v repozitári. Potom:

```bash
python analysis/analyze_results.py      # automaticky pridá results/colab/*_colab_*.csv
```

Behy z Colabu sa započítajú do kvality riešení (BKV, rpd, testy). **Časy** (Tab. 4, graf časov)
ostávajú len z notebooku, aby sa nemiešal rôzny hardvér.

## Prečo sa dá výsledkom z Colabu veriť

- Rozpočet algoritmu je daný počtom iterácií, nie časom – iný procesor mení len čas behu.
- Bunka 4 pred hlavným behom overí, že naša implementácia aj program autorov dajú v Colabe
  **presne rovnaké** ΣC ako na notebooku (seed 2, dve inštancie) a že prechádzajú testy 2. fázy
  a NPS-set.
- Program autorov sa kompiluje z rovnakého commitu (`bde1bc3`). Colab má Boost 1.74 a ich CMake
  chce ≥ 1.75, preto ho kompilujeme priamo cez `g++`; overené v Ubuntu 22.04 – výsledky sú bit
  po bite rovnaké ako z buildu cez CMake.
