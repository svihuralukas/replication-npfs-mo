"""Fáza 2: lokálne prehľadávanie v nepermutačnom priestore (Ritt & Rossit, 2024, sekcie 3.2 a 4).

Vychádza z permutácie z fázy 1. Každý job sa vyberie (aj so všetkými jeho pseudo-jobmi)
a vloží späť jedným z troch spôsobov (Benavides & Ritt, 2015):
- straight: na pozíciu k na všetkých strojoch;
- s anticipáciou na stroji i: pozícia k na strojoch < i, pozícia k - 1 na strojoch >= i;
- s oneskorením na stroji i: pozícia k na strojoch < i, pozícia k + 1 na strojoch >= i.
Končí v prvom lokálnom minime. Počet pseudo-jobov nikdy neprekročí 2n.
"""

from npfsmo import PseudoJob
from npfsmo.instance import Instance


def nonperm_local_search(inst: Instance, perm: list[int]) -> list[PseudoJob]:
    raise NotImplementedError
