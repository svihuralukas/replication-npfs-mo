# Výsledky hlavného experimentu (pôvodné inštancie)

Behy z Google Colabu (`colab/povodne_instancie.ipynb`, 12. – 13. 11. 2026), jeden riadok = inštancia × seed.

| súbor | obsah |
|---|---|
| `iga_ours_session1.csv` | naša implementácia, n = 5–50, seedy 1–10 (18 000 behov) |
| `iga_ours_session2.csv`, `iga_ours_session3.csv` | naša implementácia, n = 100, seedy 1–5 a 6–10 (2 × 1800) |
| `iga_authors_session{1,2,3}.csv` | pôvodný program autorov, to isté rozdelenie |
| `iga_ours-sampling-autori_session4.csv` | naša implementácia s výberom jobov ako v programe autorov (`--sampling autori`), n = 30–100, seedy 1–10 |
| `*_history.csv` | priebeh najlepšieho ΣC v 1. fáze (iterácia, čas, ΣC) |
| `info_session*.txt` | čas začiatku a konca, CPU, počet vCPU |
| `analysis/` | výstupy `analysis/analyze_original.py` (`summary.txt` = všetky čísla v reporte) |

Stĺpce sú opísané v `src/run_experiments.py` a `reference/run_authors.py`.

Hardvér: Intel Xeon 2,2 GHz. Seedy 1–5 časti 1 (n ≤ 50) bežali na runtime s 2 vCPU, všetko
ostatné na 12 vCPU s 12 paralelnými behmi. Na kvalitu riešení to vplyv nemá (rozpočet je počet
iterácií); časy v reporte sú preto len zo seedov 6–10.

```bash
python src/fetch_original.py        # inštancie a výsledky článku (ak ešte nie sú)
python analysis/analyze_original.py
```
