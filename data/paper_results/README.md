# Výsledky autorov

Hodnoty sú ručne prepísané z článku Ritt & Rossit (2024), doi:10.1016/j.cor.2024.106742.
Riadky s priemermi sú vynechané, dajú sa dopočítať.

| Súbor | Zdroj | Obsah |
|-------|-------|-------|
| `table3_2sa.csv`, `table3_iga.csv` | Tab. 3 | relatívna odchýlka od BKV v %, 2SA (Henneberg & Neufeld, 2016) a IGA |
| `table4_time.csv` | Tab. 4 | priemerný čas výpočtu v sekundách (i7-13700, C++) |
| `table6_iga0.csv`, `table6_iga_npsset.csv` | Tab. 6 | ablácie IGA0 a IGA+NPS-set, relatívna odchýlka v % |

Stĺpce: `r` je podiel chýbajúcich operácií, `m` počet strojov, `nX` počet jobov.
Každá bunka je priemer cez 30 inštancií skupiny pri seede 1.

Detailné výsledky po inštanciách aj najlepšie známe hodnoty sú v repozitári autorov:
https://github.com/mrpritt/npfs-mo (priečinok `data/`).

Kontrola: priemery stĺpcov IGA v Tab. 3 vychádzajú 1.3, 2.1, 1.1, 0.7, 0.4, 0.8.
