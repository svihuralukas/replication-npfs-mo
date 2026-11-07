"""Replikácia IGA pre F | skip | sum C_j podľa Ritt & Rossit (2024), doi:10.1016/j.cor.2024.106742.

Konvencie v celom balíku:
- stroje aj joby sú indexované od 0;
- inštancia má maticu procesných časov ``p`` tvaru (m, n) a masku ``present`` tvaru (m, n),
  kde ``present[i, j] == False`` znamená chýbajúcu operáciu (nie nulový čas);
- rozvrh je postupnosť pseudo-jobov ``(job, first_machine, last_machine)`` (vrátane oboch koncov),
  kompletný job ``j`` je ``(j, 0, m - 1)``. Permutácia je špeciálny prípad.
"""

PseudoJob = tuple[int, int, int]
