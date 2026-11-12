# Behy v Google Colabe

| Notebook | Inštancie | Čo počíta | Stav |
|---|---|---|---|
| [`povodne_instancie.ipynb`](povodne_instancie.ipynb) | **pôvodné** H&N (zverejnené autormi 11. 11. 2026) | **hlavný experiment**: naša implementácia aj program autorov, všetky n, seedy 1–10 | treba spustiť |
| [`n100_seedy.ipynb`](n100_seedy.ipynb) | naše vygenerované | doplnenie seedov 4–10 pre n = 100 (predbežný experiment) | hotové, výsledky v `results/colab/` |

Oba notebooky si samy naklonujú tento repozitár (vetva `main`), nainštalujú balíky, skompilujú
pôvodný program autorov (commit `bde1bc3`) a pred hlavným behom overia, že prostredie dáva
presne rovnaké výsledky ako náš notebook. Výsledky sa zapisujú priebežne na Google Drive.

## Hlavný experiment – `povodne_instancie.ipynb`

**Otvoriť v Colabe:**
https://colab.research.google.com/github/svihuralukas/replication-npfs-mo/blob/main/colab/povodne_instancie.ipynb
(kým nie je PR s pôvodnými inštanciami zlúčený do `main`, použi
https://colab.research.google.com/github/svihuralukas/replication-npfs-mo/blob/etapa-3-povodne-instancie/colab/povodne_instancie.ipynb;
notebook sám klonuje `main` a ak tam ešte nie je `src/fetch_original.py`, použije vetvu PR)

1. Otvor odkaz (prihlásený do Google účtu s Colab Pro).
2. **Runtime → Change runtime type → CPU**, ak sa dá, zapni *High-RAM* (viac jadier; notebook ich využije sám).
   GPU ani TPU netreba.
3. Predvolene (`SESSION = [1, 2, 3, 4]`) beží všetko v jednom runtime jedna session po druhej,
   spolu ~8 h pri 12 vCPU. Ak chceš session rozdeliť do viacerých runtime naraz, nastav v prvej
   bunke v každom iné, napr. `SESSION = [1, 4]` a `SESSION = [2, 3]`:

   | `SESSION` | n | seedy | čo beží | odhad pri 12 vCPU |
   |---|---|---|---|---|
   | 1 | 5–50 | 1–10 | naša + program autorov | ~1,2 h |
   | 2 | 100 | 1–5 | naša + program autorov | ~2 h |
   | 3 | 100 | 6–10 | naša + program autorov | ~2 h |
   | 4 | 30–100 | 1–10 | naša s výberom jobov ako v programe autorov (`--sampling autori`) | ~2,5 h |

   Odhady sú z behov v `results/colab/` (12 vCPU Xeon 2,2 GHz: 2 seedy pre n = 100 v oboch
   implementáciách za 49 min). Pri 2 vCPU je to asi 6× dlhšie. Session môžu bežať naraz, ak to
   účet dovolí; inak jedna po druhej. Session 4 je doplnkový experiment (vysvetlenie malého
   rozdielu medzi implementáciami) – ak by nebol čas, hlavné výsledky sú v session 1–3.
4. **Runtime → Run all**, potvrď prístup ku Google Drive.
5. Počkaj na bunku 4 (**Kontrola prostredia**, ~3 min). Musí vypísať `Prostredie je v poriadku.`
   Kontroluje aj to, že program autorov so seedom 1 dá **presne hodnoty z článku**. Ak vypíše
   `NEZHODA` alebo chybu, nič ďalej nespúšťaj.
6. Bunka 5 je hlavný beh. Nechaj kartu prehliadača otvorenú. Ak sa runtime odpojí, stačí znova
   **Run all** s rovnakým `SESSION` – hotové behy sa preskočia.
7. Bunka 6 vypíše počty behov na seed (session 1: 1800, session 2 a 3: 360, session 4: 1080).

### Výstupy (Google Drive, priečinok `npfs-mo-povodne/`)

| súbor | obsah |
|---|---|
| `iga_ours_session<k>.csv` (+ `_history.csv`) | naša implementácia (stĺpce ako `results/iga_ours.csv`), konvergencia 1. fázy |
| `iga_authors_session<k>.csv` | program autorov (stĺpce ako `reference/iga_authors.csv`) |
| `iga_ours-sampling-autori_session4.csv` | naša implementácia s výberom jobov ako autori |
| `info_session<k>.txt` | čas začiatku/konca, CPU, počet jadier |

### Potom

Stiahni celý priečinok `npfs-mo-povodne` z Drive a skopíruj súbory do **`results/original/`**. Potom:

```bash
python src/fetch_original.py          # pôvodné inštancie a výsledky článku po inštanciách
python analysis/analyze_original.py   # tabuľky report/tables/orig_*.tex, grafy report/figures/orig_*.pdf
```

Časy v tomto experimente sú z Colabu (obe implementácie na rovnakom type runtime); s článkom
sa porovnávajú len orientačne (iný procesor, paralelné behy).

## Predbežný experiment – `n100_seedy.ipynb` (hotové)

Na našich vygenerovaných inštanciách (`instances/generated/`) sme na notebooku spustili seedy
1–10 pre n ≤ 50 a 1–3 pre n = 100. Seedy 4–10 pre n = 100 dobehli týmto notebookom v Colabe
(4 session, 11. 11. 2026, 12 vCPU Xeon 2,2 GHz); výsledky sú v [`results/colab/`](../results/colab/)
a `analysis/analyze_results.py` ich načíta automaticky. Behy z Colabu sa započítavajú do kvality
riešení, časy v tomto experimente sú len z notebooku.

Notebook je v repozitári kvôli reprodukovateľnosti; znova ho spúšťať netreba.
