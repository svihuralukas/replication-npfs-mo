# Inštancie

## Pôvodné inštancie (hlavný experiment) – `original/`

Autori použili 2160 inštancií Henneberg & Neufeld (2016). Na začiatku projektu v ich repozitári
(https://github.com/mrpritt/npfs-mo) boli len kód a výsledky po inštanciách, nie samotné inštancie.
Požiadali sme o ne autorov a tí ich **11. 11. 2026 zverejnili** (commit `24b5d23`). Hlavný
experiment preto beží na nich – zadanie žiada použiť dáta z článku, ak sú dostupné.

```bash
python src/fetch_original.py      # → instances/original/*.txt a data/authors/*.csv
```

Skript stiahne inštancie aj výsledky článku po inštanciách z pevného commitu a skontroluje, že
počet operácií, počet pseudo jobov a priemerný čas operácie sedia s ich `table2.csv`. Súbory nie sú
v našom gite (patria autorom), skript ich vždy stiahne rovnaké. Formát je rovnaký ako nižšie
(hlavička je rozdelená na tri riadky), pomenovanie `{r}_{n}_{m}_{i}.txt` tiež
(`instances/Readme.org` autorov). Inštancia z Obr. 3 článku je `0.2_05_05_00.txt` (= `tests/fig3.txt`).

## Vlastné inštancie (predbežný experiment) – `generated/`

Kým pôvodné inštancie neboli dostupné, generovali sme vlastné rovnakým postupom. Aby bolo
porovnanie férové, spúšťali sme na nich aj **pôvodný C++ program autorov**
(`reference/run_authors.py`) – obe implementácie tak riešili presne tie isté dáta. Tento
experiment ostáva v repozitári aj v reporte ako doplnok (presná zhoda s programom autorov,
optimá MIP pre n = 5).

### Generovanie

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

Generované inštancie sú v gite (`instances/generated/`, ~14 MB), aby všetci pracovali s rovnakými súbormi.
Dajú sa aj kedykoľvek presne zopakovať generátorom.

### Formát súboru

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

### Pomenovanie súborov

`{r}_{n:02d}_{m:02d}_{i:02d}.txt`, napr. `0.3_20_10_05.txt` (r = 0.3, n = 20, m = 10, inštancia 5).
Poradie polí r_n_m_i je rovnaké ako v pôvodných inštanciách; n a m sa vždy čítajú z hlavičky.

### Porovnanie s originálmi

```bash
python src/compare_instances.py --table2 data/authors/table2.csv
```

Porovnáva priemerný čas operácie, počet existujúcich operácií a počet pseudo jobov
po skupinách s originálmi (`results/instance_comparison.csv`):

- počet existujúcich operácií sa zhoduje vo všetkých 72 skupinách,
- priemerný počet pseudo jobov sa líši najviac o 4,5 %, priemerný čas operácie najviac o 3,7 %
  (náhodný rozptyl pri 30 inštanciách v skupine); oboje zodpovedá aj Propozícii 1 článku.

Inštancia z Obr. 3 článku (originál H&N „00“, r = 0.2, n = m = 5) je v `tests/fig3.txt`.
