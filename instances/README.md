# Inštancie

## Prečo vlastné inštancie

Autori použili 2160 inštancií od Henneberg & Neufeld (2016). V ich repozitári
(https://github.com/mrpritt/npfs-mo) sú kód a výsledky po inštanciách (`data/*.csv`),
ale **samotné súbory inštancií tam nie sú**. Preto ich generujeme sami rovnakým postupom
(a autorov sme požiadali o originály – ak prídu, vložia sa do `original/`).

Aby bolo porovnanie férové, spúšťame na našich inštanciách aj **pôvodný C++ program
autorov** (`reference/run_authors.py`) – obe implementácie tak riešia presne tie isté dáta.

## Generovanie

```bash
python src/generate_instances.py          # parametre v config/instances.yaml
```

- n ∈ {5, 10, 20, 30, 50, 100}, m ∈ {5, 10, 20, 30}, r ∈ {0.2, 0.3, 0.4}, 30 inštancií na
  skupinu, spolu 72 × 30 = 2160 (rovnako ako v článku, Sekcia 5.1),
- časy spracovania z U[1, 99] (Taillard, 1990),
- **presne round_half_up(r · n · m) operácií chýba**, náhodne rozmiestnených.
  Zistené z dát autorov (`npfs-mo/data/table2.csv`): vo všetkých 2160 originálnych
  inštanciách je počet existujúcich operácií presne n·m − round_half_up(r·n·m).
  Nejde teda o to, že každá operácia chýba s pravdepodobnosťou r.
- seed: `base_seed: 2026` v `config/instances.yaml`; každá inštancia má vlastný generátor
  odvodený z (base_seed, r, n, m, i), takže sa dá zregenerovať nezávisle od ostatných.
  Na inom počítači vzniknú bit po bite rovnaké súbory.

Generované inštancie nie sú v gite (`.gitignore`), dajú sa kedykoľvek presne zopakovať.

## Formát súboru

Rovnaký ako originály H&N, ktoré číta program autorov (`npfs-mo/src/instance.cpp`, `read_hn`):

```
numberMachines 5 numberJobs 5 missing Operations 0.2
t_0_0 79
t_0_1 60
...
t_4_4 44
```

`t_i_j` = čas spracovania jobu j na stroji i (od 0). **Hodnota 0 = chýbajúca operácia**
(nie operácia s nulovým časom). Riadky idú stroj po stroji.

## Pomenovanie súborov

`{r}_{n:02d}_{m:02d}_{i:02d}.txt`, napr. `0.3_20_10_05.txt` (r = 0.3, n = 20, m = 10, inštancia 5).
Poradie polí r_n_m_i je náš predpoklad podľa príkladu `0.2_10_05_02.txt` z README autorov;
na výpočet nemá vplyv, n a m sa vždy čítajú z hlavičky.

## Porovnanie s originálmi

```bash
python src/compare_instances.py --table2 ../npfs-mo/data/table2.csv
```

Porovnáva priemerný čas operácie, počet existujúcich operácií a počet pseudo jobov
po skupinách s originálmi (`results/instance_comparison.csv`):

- počet existujúcich operácií sa zhoduje vo všetkých 72 skupinách,
- priemerný počet pseudo jobov sa líši najviac o 4,5 %, priemerný čas operácie najviac o 3,7 %
  (náhodný rozptyl pri 30 inštanciách v skupine); oboje zodpovedá aj Propozícii 1 článku.

Inštancia z Obr. 3 článku (originál H&N „00“, r = 0.2, n = m = 5) je v `tests/fig3.txt`.
