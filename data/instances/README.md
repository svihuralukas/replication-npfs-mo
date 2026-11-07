# Inštancie

Sem patrí všetkých 2160 inštancií (~4 MB textu). Ukladajú sa ako obyčajné textové súbory, nie zip.

Inštancie generujeme podľa Henneberg & Neufeld (2016) a Taillard (1993):

- n ∈ {5, 10, 20, 30, 50, 100}, m ∈ {5, 10, 20, 30}
- procesné časy z U[1, 99]
- podiel chýbajúcich operácií r ∈ {0.2, 0.3, 0.4}
- 30 inštancií na každú kombináciu (n, m, r), spolu 72 × 30 = 2160

## Treba doplniť

- **Formát súboru:** čo je v hlavičke, ako sú zapísané chýbajúce operácie, či sú riadky stroje alebo joby.
- **Pomenovanie súborov:** pre porovnanie, autori používajú napr. `0.2_10_05_02.txt`.
- **Generátor:** skript a príkaz, ktorým sa dajú inštancie zregenerovať, vrátane použitého seedu.
- **Rozdiely oproti originálnym inštanciám H&N,** ak nejaké sú.
