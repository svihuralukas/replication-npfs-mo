# Behy v Google Colabe

| Notebook | Inštancie | Čo počíta | Výsledky |
|---|---|---|---|
| [`povodne_instancie.ipynb`](povodne_instancie.ipynb) | pôvodné H&N (od autorov) | **hlavný experiment**: naša implementácia aj program autorov, všetky n, seedy 1–10 | [`results/original/`](../results/original/) |
| [`n100_seedy.ipynb`](n100_seedy.ipynb) | vlastné vygenerované | predbežný experiment: seedy 4–10 pre n = 100 | [`results/colab/`](../results/colab/) |

Oba notebooky si samy naklonujú tento repozitár, nainštalujú balíky, skompilujú pôvodný program
autorov (commit `bde1bc3`) a pred hlavným behom overia, že prostredie dáva presne rovnaké výsledky
ako referenčné behy. Výsledky sa zapisujú priebežne na Google Drive; po odpojení runtime stačí
znova **Run all**, hotové behy sa preskočia.

## Hlavný experiment – `povodne_instancie.ipynb`

https://colab.research.google.com/github/svihuralukas/replication-npfs-mo/blob/main/colab/povodne_instancie.ipynb

1. **Runtime → Change runtime type → CPU** (GPU ani TPU netreba). Notebook využije všetky vCPU
   runtime, s *High-RAM* ich býva viac.
2. **Runtime → Run all** a povoliť prístup ku Google Drive.
3. Bunka 4 (**Kontrola prostredia**, ~3 min) musí vypísať `Prostredie je v poriadku.` Overuje
   testy, to, že program autorov so seedom 1 dá **presne hodnoty z článku**, a to, že naša
   implementácia dá rovnaké výsledky ako na našom počítači.
4. Bunka 5 je hlavný beh, bunka 6 vypíše počty hotových behov na seed.

Experiment je rozdelený na štyri časti (`SESSION` v prvej bunke; predvolene všetky jedna po druhej):

| časť | n | seedy | čo beží | trvanie pri 12 vCPU |
|---|---|---|---|---|
| 1 | 5–50 | 1–10 | naša implementácia + program autorov | ~0,6 h |
| 2 | 100 | 1–5 | naša implementácia + program autorov | ~2 h |
| 3 | 100 | 6–10 | naša implementácia + program autorov | ~2 h |
| 4 | 30–100 | 1–10 | naša implementácia s výberom jobov ako v programe autorov (`--sampling autori`) | ~2,2 h |

Časti sa dajú pustiť aj vo viacerých runtime naraz (napr. `SESSION = [1, 4]` a `SESSION = [2, 3]`).
Výstupy na Drive (priečinok `npfs-mo-povodne/`) sa skopírujú do `results/original/`:

| súbor | obsah |
|---|---|
| `iga_ours_session<k>.csv` (+ `_history.csv`) | naša implementácia (stĺpce ako `results/iga_ours.csv`), priebeh 1. fázy |
| `iga_authors_session<k>.csv` | program autorov (stĺpce ako `reference/iga_authors.csv`) |
| `iga_ours-sampling-autori_session4.csv` | naša implementácia s výberom jobov ako autori |
| `info_session<k>.txt` | čas začiatku a konca, CPU, počet vCPU |

Potom:

```bash
python src/fetch_original.py          # pôvodné inštancie a výsledky článku po inštanciách
python analysis/analyze_original.py   # results/original/analysis/, report/tables/orig_*.tex, report/figures/orig_*.pdf
```

**Náš beh (12. – 13. 11. 2026):** Intel Xeon 2,2 GHz. Časť 1 začala na runtime s 2 vCPU,
po jeho odpojení pokračovala na runtime s 12 vCPU (seedy 1–5 dobehli na 2 vCPU, seedy 6–10
na 12 vCPU); časti 2–4 bežali celé na 12 vCPU (`results/original/info_session*.txt`). Kvalitu
riešení to neovplyvní (rozpočet je počet iterácií), časy v reporte sú preto len zo seedov 6–10,
ktoré bežali všetky na rovnakom type runtime.

## Predbežný experiment – `n100_seedy.ipynb`

Na vlastných vygenerovaných inštanciách (`instances/generated/`) bežali na notebooku seedy
1–10 pre n ≤ 50 a 1–3 pre n = 100. Seedy 4–10 pre n = 100 dobehli týmto notebookom v Colabe
(11. 11. 2026, 4 runtime po 12 vCPU, Xeon 2,2 GHz; `SEEDS` v prvej bunke: `[4, 5]`, `[6, 7]`,
`[8, 9]`, `[10]`). Výsledky sú v [`results/colab/`](../results/colab/) a
`analysis/analyze_results.py` ich načíta automaticky; do kvality riešení sa započítavajú,
časy v tomto experimente sú len z notebooku.
