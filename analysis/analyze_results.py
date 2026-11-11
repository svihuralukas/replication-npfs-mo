"""
Analýza plných experimentov 2. etapy: naša implementácia vs. pôvodný program autorov
na rovnakých inštanciách a porovnanie s tabuľkami článku (Tab. 3, 4, 6).

Vstupy:
    results/iga_ours.csv (+ _history.csv)   – src/run_experiments.py
    reference/iga_authors.csv               – reference/run_authors.py
    data/paper_results/*.csv                – tabuľky z článku
Výstupy:
    results/analysis/*.csv                  – tabuľky (rovnaké rozloženie ako v článku) a súhrny
    results/analysis/summary.txt            – textový súhrn so štatistickými testami
    report/figures/*.pdf                    – grafy pre report
    report/tables/*.tex                     – tabuľky pre report

Metodika (ako v článku, Sekcia 5.1):
  * BKV inštancie = najmenšie ΣC zo VŠETKÝCH našich experimentov (obe implementácie, všetky
    seedy, všetky varianty). Článok zbiera BKV aj z 2SA, MIP a IGA+ – tie nespúšťame, preto
    sú naše BKV slabšie a odchýlky systematicky menšie (rozdiel vysvetľujeme v reporte).
  * Relatívna odchýlka rpd = 100 · (v − BKV) / BKV, priemer cez inštancie skupiny a seedy.
  * Pre každú inštanciu sa používajú len seedy, ktoré prebehli v OBOCH implementáciách.
  * Seedy medzi implementáciami nie sú párové (iné generátory náhodných čísel) – párujeme
    inštancie (priemer cez seedy), Wilcoxonov test so znamienkovými poradiami.
  * Behy z Google Colabu (results/colab/*_colab_*.csv, colab/README.md) sa pridajú ku kvalite
    riešení; časy (Tab. 4, graf časov) sa počítajú len z behov na našom notebooku, aby sa
    nemiešal hardvér.

Spustenie (z koreňa repozitára):
    python analysis/analyze_results.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402
import pandas as pd               # noqa: E402
from scipy.stats import spearmanr, wilcoxon   # noqa: E402
from scipy.stats import t as t_dist           # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NS = [5, 10, 20, 30, 50, 100]
MS = [5, 10, 20, 30]
RS = [0.2, 0.3, 0.4]
VARIANTS = {"iga0": "IGA0", "nps": "IGA+NPS-set", "iga": "IGA"}
PAPER = {"iga": "table3_iga.csv", "iga0": "table6_iga0.csv", "nps": "table6_iga_npsset.csv"}
IMPLS = {"ours": "naša (Python)", "authors": "autori (C++)"}

out_lines: list[str] = []


def say(s: str = "") -> None:
    print(s)
    out_lines.append(s)


# --------------------------------------------------------------------------- načítanie

def load(ours_paths: list[Path], authors_paths: list[Path]) -> pd.DataFrame:
    """Prvý súbor v zozname je hlavný (náš notebook, source = local), ďalšie sú z Colabu."""
    def read(paths, impl):
        return pd.concat([pd.read_csv(p).assign(impl=impl, source="local" if k == 0 else "colab")
                          for k, p in enumerate(paths)], ignore_index=True)
    ours = read(ours_paths, "ours")
    auth = read(authors_paths, "authors")
    cols = [c for c in auth.columns if c in ours.columns]
    df = pd.concat([ours[cols + ["time_phase1", "time_phase2"]], auth[cols]], ignore_index=True)
    df = df.drop_duplicates(["instance", "seed", "impl"], keep="first")
    # len seedy, ktoré prebehli v oboch implementáciách
    seeds = df.groupby(["instance", "seed"])["impl"].nunique()
    common = seeds[seeds == 2].index
    df = df.set_index(["instance", "seed"]).loc[common].reset_index()
    df["n"] = df["n"].astype(int)
    df["m"] = df["m"].astype(int)
    df["r"] = df["r"].round(1)
    return df


def add_rpd(df: pd.DataFrame, mip: pd.DataFrame | None) -> pd.DataFrame:
    bkv = df.melt(id_vars="instance", value_vars=["iga0_ft", "nps_ft", "iga_ft"])
    bkv = bkv.groupby("instance")["value"].min().rename("bkv")
    if mip is not None:                       # aj neoptimálne riešenie MIP je prípustné → do BKV
        m = mip.dropna(subset=["mip_ft"]).set_index("instance")["mip_ft"]
        bkv = pd.concat([bkv, m.reindex(bkv.index)], axis=1).min(axis=1).rename("bkv")
    df = df.join(bkv, on="instance")
    for v in VARIANTS:
        df[f"rpd_{v}"] = 100 * (df[f"{v}_ft"] - df["bkv"]) / df["bkv"]
    return df


# --------------------------------------------------------------------------- tabuľky

def group_table(df: pd.DataFrame, col: str, index=("r", "m")) -> pd.DataFrame:
    """Priemer stĺpca po skupinách v rozložení článku: riadky (r, m), stĺpce n5..n100."""
    t = df.groupby(list(index) + ["n"])[col].mean().unstack("n")
    t = t.reindex(columns=NS)
    t.columns = [f"n{n}" for n in NS]
    return t


def paper_table(variant: str) -> pd.DataFrame:
    t = pd.read_csv(ROOT / "data" / "paper_results" / PAPER[variant])
    t["r"] = t["r"].round(1)
    return t.set_index(["r", "m"])


def with_avg(t: pd.DataFrame) -> pd.DataFrame:
    avg = pd.DataFrame([t.mean()], index=pd.MultiIndex.from_tuples([("priemer", "")], names=t.index.names)
                       if isinstance(t.index, pd.MultiIndex) else ["priemer"])
    return pd.concat([t, avg])


def latex_table(path: Path, tables: dict[str, pd.DataFrame], caption: str, label: str,
                index_names=("$r$", "$m$"), fmt="{:.1f}") -> None:
    """Viac tabuliek vedľa seba (napr. naša | autori | článok) v jednom tabular-e."""
    names = list(tables)
    first = with_avg(tables[names[0]])
    nidx = len(index_names)
    cols = "l" * nidx + ("|" + "r" * len(NS)) * len(names)
    lines = [r"\begin{table}[ht]", r"\centering", r"\scriptsize", r"\setlength{\tabcolsep}{3pt}",
             rf"\caption{{{caption}}}", rf"\label{{{label}}}", rf"\begin{{tabular}}{{{cols}}}", r"\toprule",
             " & " * (nidx - 1) + " & " + " & ".join(rf"\multicolumn{{{len(NS)}}}{{c}}{{{n}}}" for n in names) + r" \\",
             " & ".join(index_names) + " & " + " & ".join([" & ".join(str(n) for n in NS)] * len(names)) + r" \\",
             r"\midrule"]
    full = {k: with_avg(v) for k, v in tables.items()}
    for idx in first.index:
        idx_t = idx if isinstance(idx, tuple) else (idx,)
        if idx_t[0] == "priemer":
            lines.append(r"\midrule")
        cells = [str(x) for x in idx_t]
        for k in names:
            row = full[k].loc[idx] if idx in full[k].index else pd.Series(index=full[k].columns, dtype=float)
            cells += ["" if pd.isna(x) else fmt.format(x) for x in row.values]
        lines.append(" & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compact_table(path: Path, by_n: dict) -> None:
    """Súhrnná tabuľka po n: pre každý variant stĺpce naša | autori | článok."""
    lines = [r"\begin{table}[ht]", r"\centering", r"\small",
             r"\caption{Priemerná relatívna odchýlka od BKV v \% podľa počtu jobov $n$ (priemer cez "
             r"$r$, $m$, inštancie a seedy). N = naša implementácia, A = program autorov (obe na našich "
             r"inštanciách), Č = článok (originálne inštancie, seed 1, iné BKV).}",
             r"\label{tab:rpd_by_n}",
             r"\begin{tabular}{r" + "|rrr" * len(by_n) + "}", r"\toprule",
             " & " + " & ".join(rf"\multicolumn{{3}}{{c}}{{{v}}}" for v in by_n) + r" \\",
             "$n$ & " + " & ".join(["N & A & Č"] * len(by_n)) + r" \\", r"\midrule"]
    for n in NS + ["priemer"]:
        cells = [str(n)]
        for t_o, t_a, t_p in by_n.values():
            for t in (t_o, t_a, t_p):
                x = t.mean() if n == "priemer" else t.get(f"n{n}", np.nan)
                cells.append("" if pd.isna(x) else f"{x:.2f}")
        if n == "priemer":
            lines.append(r"\midrule")
        lines.append(" & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- analýzy

def summary_by_n(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for impl in IMPLS:
        d = df[df.impl == impl]
        for v, vname in VARIANTS.items():
            g = d.groupby("n")[f"rpd_{v}"]
            s = pd.DataFrame({"mean": g.mean(), "median": g.median(), "std": g.std(),
                              "min": g.min(), "max": g.max()})
            s["impl"], s["variant"] = impl, vname
            rows.append(s.reset_index())
    return pd.concat(rows)[["impl", "variant", "n", "mean", "median", "std", "min", "max"]]


def seed_stability(df: pd.DataFrame) -> pd.DataFrame:
    """Variabilita medzi seedmi: smerodajná odchýlka rpd IGA cez seedy pre každú inštanciu
    (priemer cez inštancie) a rozptyl priemeru skupiny pri jednotlivých seedoch."""
    rows = []
    for impl in IMPLS:
        d = df[df.impl == impl]
        per_inst = d.groupby(["n", "instance"])["rpd_iga"].agg(["std", "min", "max"])
        per_inst["range"] = per_inst["max"] - per_inst["min"]
        by_seed = d.groupby(["n", "seed"])["rpd_iga"].mean().groupby("n").agg(["min", "max", "std"])
        s = pd.DataFrame({"std_over_seeds": per_inst["std"].groupby("n").mean(),
                          "range_over_seeds": per_inst["range"].groupby("n").mean(),
                          "n_seed_mean_min": by_seed["min"], "n_seed_mean_max": by_seed["max"],
                          "seeds": d.groupby("n")["seed"].nunique()})
        s["impl"] = impl
        rows.append(s.reset_index())
    return pd.concat(rows)


def wilcoxon_line(a: pd.Series, b: pd.Series, what: str) -> None:
    diff = a - b
    better, equal, worse = (diff < 0).sum(), (diff == 0).sum(), (diff > 0).sum()
    if (diff != 0).sum() > 0:
        p = wilcoxon(a, b, zero_method="wilcox").pvalue
        verdict = "rozdiel NIE JE" if p >= 0.05 else "rozdiel JE"
        say(f"  {what}: lepšie {better}, rovnaké {equal}, horšie {worse}; Wilcoxon p = {p:.3g} "
            f"({verdict} významný na hladine 0,05)")
    else:
        say(f"  {what}: všetky rovnaké ({equal})")


# --------------------------------------------------------------------------- grafy

def fig_rpd_by_n(df: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    colors = {"iga0": "#c0504d", "nps": "#e1a33b", "iga": "#4f81bd"}
    for v, vname in VARIANTS.items():
        paper = paper_table(v).mean()
        ax.plot(NS, [paper[f"n{n}"] for n in NS], ":", marker="s", color=colors[v], alpha=.6,
                label=f"{vname} – článok")
        for impl, ls, mk in (("authors", "--", "^"), ("ours", "-", "o")):
            y = df[df.impl == impl].groupby("n")[f"rpd_{v}"].mean().reindex(NS)
            ax.plot(NS, y.values, ls, marker=mk, color=colors[v], label=f"{vname} – {IMPLS[impl]}")
    ax.set_xscale("log")
    ax.set_xticks(NS, [str(n) for n in NS])
    ax.set_xlabel("počet jobov n")
    ax.set_ylabel("priemerná rel. odchýlka od BKV [%]")
    ax.grid(alpha=.3)
    ax.legend(fontsize=6.5, ncol=3, loc="upper center", bbox_to_anchor=(.5, -.2))
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_time(df: pd.DataFrame, path: Path) -> None:
    df = df[df.source == "local"]
    t = df.groupby(["instance", "impl"])["time"].mean().unstack("impl")
    n = df.groupby("instance")["n"].first().reindex(t.index)
    fig, ax = plt.subplots(figsize=(4.2, 3.8))
    sc = ax.scatter(t["authors"], t["ours"], c=np.log10(n), s=6, cmap="viridis", alpha=.7)
    lim = [t.min().min() / 1.5, t.max().max() * 1.5]
    ax.plot(lim, lim, "k-", lw=.8)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("čas autori (C++) [s]")
    ax.set_ylabel("čas naša implementácia [s]")
    cb = fig.colorbar(sc, ax=ax, ticks=np.log10(NS))
    cb.ax.set_yticklabels([str(x) for x in NS])
    cb.set_label("n")
    ax.grid(alpha=.3, which="both", lw=.3)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_convergence(hist: pd.DataFrame, df: pd.DataFrame, path: Path) -> None:
    """Priebeh najlepšieho ΣC 1. fázy (rel. odchýlka od BKV) počas iterácií, priemer cez
    inštancie a seedy, pre r = 0.3, m = 20 a rôzne n."""
    ours = df[df.impl == "ours"]
    bkv = ours.groupby("instance")["bkv"].first()
    meta = ours.groupby("instance")[["n", "m", "r", "iga_steps"]].first()
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    grid = np.linspace(0, 1, 101)
    for n in NS:
        insts = meta[(meta.n == n) & (meta.m == 20) & (meta.r == 0.3)].index
        h = hist[hist.instance.isin(insts)]
        if h.empty:
            continue
        curves = []
        for (inst, seed), g in h.groupby(["instance", "seed"]):
            x = g["iteration"].values / meta.loc[inst, "iga_steps"]
            y = 100 * (g["ft"].values - bkv[inst]) / bkv[inst]
            idx = np.searchsorted(x, grid, side="right") - 1
            curves.append(y[np.clip(idx, 0, None)])
        ax.plot(100 * grid, np.mean(curves, axis=0), label=f"n = {n}")
    ax.set_xlabel("podiel rozpočtu iterácií 1. fázy [%]")
    ax.set_ylabel("najlepšie ΣC: rel. odchýlka od BKV [%]")
    ax.set_ylim(bottom=0)
    ax.grid(alpha=.3)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_seed_box(df: pd.DataFrame, path: Path) -> None:
    """Rozdelenie priemernej rpd IGA pri jednotlivých seedoch (priemer cez inštancie danej n)."""
    fig, ax = plt.subplots(figsize=(6, 3.2))
    data, pos, cols = [], [], []
    for k, n in enumerate(NS):
        for off, impl, c in ((-.18, "ours", "#4f81bd"), (.18, "authors", "#9bbb59")):
            s = df[(df.impl == impl) & (df.n == n)].groupby("seed")["rpd_iga"].mean()
            data.append(s.values)
            pos.append(k + off)
            cols.append(c)
    bp = ax.boxplot(data, positions=pos, widths=.3, patch_artist=True, showfliers=True)
    for patch, c in zip(bp["boxes"], cols):
        patch.set_facecolor(c)
    ax.set_xticks(range(len(NS)), [str(n) for n in NS])
    ax.set_xlabel("počet jobov n")
    ax.set_ylabel("rpd IGA, priemer cez inštancie [%]")
    ax.legend(bp["boxes"][:2], [IMPLS["ours"], IMPLS["authors"]], fontsize=7)
    ax.grid(alpha=.3, axis="y")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# --------------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", default=str(ROOT / "results" / "iga_ours.csv"))
    ap.add_argument("--history", default=str(ROOT / "results" / "iga_ours_history.csv"))
    ap.add_argument("--authors", default=str(ROOT / "reference" / "iga_authors.csv"))
    ap.add_argument("--mip", default=str(ROOT / "results" / "mip.csv"))
    ap.add_argument("--colab", default=str(ROOT / "results" / "colab"),
                    help="priečinok s výsledkami z Colabu (iga_ours_colab_*.csv, iga_authors_colab_*.csv)")
    ap.add_argument("--outdir", default=str(ROOT / "results" / "analysis"))
    args = ap.parse_args()

    outdir = Path(args.outdir)
    figdir, texdir = ROOT / "report" / "figures", ROOT / "report" / "tables"
    for d in (outdir, figdir, texdir):
        d.mkdir(parents=True, exist_ok=True)

    mip = pd.read_csv(args.mip) if Path(args.mip).exists() else None
    colab = Path(args.colab)
    c_ours = sorted(p for p in colab.glob("iga_ours_colab_*.csv") if "history" not in p.name)
    c_auth = sorted(colab.glob("iga_authors_colab_*.csv"))
    c_hist = sorted(colab.glob("iga_ours_colab_*_history.csv"))
    df = add_rpd(load([Path(args.ours)] + c_ours, [Path(args.authors)] + c_auth), mip)
    if c_ours or c_auth:
        say(f"Behy z Colabu: {len(c_ours)} + {len(c_auth)} súborov, "
            f"{(df.source == 'colab').sum() // 2} spoločných behov")
    df.groupby("instance")["bkv"].first().to_csv(outdir / "bkv.csv")
    n_inst = df.instance.nunique()
    seeds = df.groupby("n")["seed"].unique().map(lambda s: sorted(int(x) for x in s))
    say(f"Inštancií: {n_inst}, behov: {len(df) // 2} na implementáciu")
    for n, s in seeds.items():
        say(f"  n = {n}: seedy {s}")
    say()

    # ---------------- tabuľky po skupinách vs. článok
    by_n = {}
    for v, vname in VARIANTS.items():
        t_o = group_table(df[df.impl == "ours"], f"rpd_{v}")
        t_a = group_table(df[df.impl == "authors"], f"rpd_{v}")
        t_a1 = group_table(df[(df.impl == "authors") & (df.seed == 1)], f"rpd_{v}")
        t_p = paper_table(v)
        for name, t in (("ours", t_o), ("authors", t_a), ("authors_seed1", t_a1)):
            with_avg(t).round(3).to_csv(outdir / f"rpd_{v}_{name}.csv")
        latex_table(texdir / f"rpd_{v}.tex", {IMPLS["ours"]: t_o, IMPLS["authors"]: t_a, "článok": t_p},
                    caption=f"{vname}: priemerná relatívna odchýlka od BKV v \\% po skupinách "
                            f"(naša implementácia a program autorov na našich inštanciách, "
                            f"všetky seedy; článok – originálne inštancie, seed 1).",
                    label=f"tab:rpd_{v}")
        rho_o = spearmanr(t_o.values.ravel(), t_p.loc[t_o.index].values.ravel(), nan_policy="omit")[0]
        rho_a = spearmanr(t_a.values.ravel(), t_p.loc[t_a.index].values.ravel(), nan_policy="omit")[0]
        rho_oa = spearmanr(t_o.values.ravel(), t_a.values.ravel(), nan_policy="omit")[0]
        by_n[vname] = (t_o.mean(), t_a.mean(), t_p.mean())
        say(f"{vname}: priemerná rpd po n (naša | autori | článok)")
        for n in NS:
            say(f"  n = {n:3d}: {t_o[f'n{n}'].mean():5.2f} | {t_a[f'n{n}'].mean():5.2f} | "
                f"{t_p[f'n{n}'].mean():5.2f}")
        say(f"  celkovo:  {t_o.values.mean():5.2f} | {t_a.values.mean():5.2f} | {t_p.values.mean():5.2f}")
        say(f"  Spearman ρ 72 skupín: naša–článok {rho_o:.2f}, autori–článok {rho_a:.2f}, "
            f"naša–autori {rho_oa:.2f}")
        say()

    compact_table(texdir / "rpd_by_n.tex", by_n)

    # ---------------- MIP (n = 5): odchýlka od optima je priamo porovnateľná s článkom,
    # lebo autori vyriešili všetky inštancie s n = 5 optimálne (Tab. 5, BKV = optimum)
    if mip is not None:
        mm = mip.set_index("instance")
        say(f"MIP (HiGHS): {len(mm)} inštancií, optimálne vyriešených {int(mm.optimal.sum())}, "
            f"priemerný čas {mm.time.mean():.1f} s, max {mm.time.max():.1f} s")
        opt = mm[mm.optimal == 1].index
        d5 = df[df.instance.isin(opt)]
        if len(d5):
            say("  IGA na inštanciách s dokázaným optimom – rel. odchýlka od optima [%] "
                "(naša | autori | článok Tab. 5 n = 5):")
            p_iga = paper_table("iga")
            for (r, m_), g in d5.groupby(["r", "m"]):
                go, ga = g[g.impl == "ours"], g[g.impl == "authors"]
                say(f"    r = {r}, m = {m_:2d}: {go.rpd_iga.mean():.2f} | {ga.rpd_iga.mean():.2f} | "
                    f"{p_iga.loc[(r, m_), 'n5']:.1f}   (optimum v {(go.iga_ft == go.bkv).mean():.0%} "
                    f"| {(ga.iga_ft == ga.bkv).mean():.0%} behov, {g.instance.nunique()} inšt.)")
            say(f"    spolu: {d5[d5.impl == 'ours'].rpd_iga.mean():.2f} | "
                f"{d5[d5.impl == 'authors'].rpd_iga.mean():.2f} | {p_iga['n5'].mean():.2f}")
        say()

    # ---------------- prínos 2. fázy a NPS-set (rozdiely nezávisia od voľby BKV tak silno)
    say("Zlepšenie oproti IGA0 v percentuálnych bodoch rpd (naša | autori | článok):")
    p0, p_iga, p_nps = paper_table("iga0"), paper_table("iga"), paper_table("nps")
    for v, pt in (("iga", p_iga), ("nps", p_nps)):
        imp_o = group_table(df[df.impl == "ours"], "rpd_iga0") - group_table(df[df.impl == "ours"], f"rpd_{v}")
        imp_a = group_table(df[df.impl == "authors"], "rpd_iga0") - group_table(df[df.impl == "authors"], f"rpd_{v}")
        imp_p = p0 - pt
        with_avg(imp_o).round(3).to_csv(outdir / f"improvement_{v}_ours.csv")
        latex_table(texdir / f"improvement_{v}.tex",
                    {IMPLS["ours"]: imp_o, IMPLS["authors"]: imp_a, "článok": imp_p.loc[imp_o.index]},
                    caption=f"Zlepšenie {VARIANTS[v]} oproti IGA0 (rozdiel priemerných relatívnych "
                            f"odchýlok v percentuálnych bodoch).", label=f"tab:improvement_{v}")
        say(f"  {VARIANTS[v]}: " + ", ".join(
            f"n={n}: {imp_o[f'n{n}'].mean():.2f} | {imp_a[f'n{n}'].mean():.2f} | {imp_p[f'n{n}'].mean():.2f}"
            for n in NS))
        say(f"    celkovo {imp_o.values.mean():.2f} | {imp_a.values.mean():.2f} | {imp_p.values.mean():.2f}")
    say()

    # ---------------- podiel inštancií, kde 2. fáza / NPS-set zlepšili
    for impl in IMPLS:
        d = df[df.impl == impl]
        say(f"{IMPLS[impl]}: 2. fáza zlepšila IGA0 v {(d.iga_ft < d.iga0_ft).mean():.1%} behov, "
            f"NPS-set v {(d.nps_ft < d.iga0_ft).mean():.1%}; IGA lepšie než IGA+NPS-set v "
            f"{(d.iga_ft < d.nps_ft).mean():.1%}, horšie v {(d.iga_ft > d.nps_ft).mean():.1%}")
    say()

    # ---------------- časy (Tab. 4)
    loc = df[df.source == "local"]                      # časy len z jedného počítača
    t_time_o = group_table(loc[loc.impl == "ours"], "time", index=("m",))
    t_time_a = group_table(loc[loc.impl == "authors"], "time", index=("m",))
    paper_t = pd.read_csv(ROOT / "data" / "paper_results" / "table4_time.csv")
    paper_t = paper_t[paper_t.method == "IGA"].drop(columns="method").set_index("m")
    with_avg(t_time_o).round(3).to_csv(outdir / "time_ours.csv")
    with_avg(t_time_a).round(3).to_csv(outdir / "time_authors.csv")
    latex_table(texdir / "time.tex", {IMPLS["ours"]: t_time_o, IMPLS["authors"]: t_time_a, "článok": paper_t},
                caption="Priemerný čas behu IGA v sekundách (obe fázy). Naše behy: 4 paralelné procesy "
                        "na jednom počítači; článok: Core i7-13700.", label="tab:time", index_names=("$m$",),
                fmt="{:.2f}")
    say("Priemerný čas IGA [s] po n (naša | autori | článok):")
    for n in NS:
        say(f"  n = {n:3d}: {t_time_o[f'n{n}'].mean():6.2f} | {t_time_a[f'n{n}'].mean():6.2f} | "
            f"{paper_t[f'n{n}'].mean():6.2f}")
    ours = loc[loc.impl == "ours"]
    share2 = (ours.time_phase2 / ours.time).groupby(ours.n).mean()
    say("  podiel 2. fázy na našom čase: " + ", ".join(f"n={n}: {share2[n]:.0%}" for n in share2.index))
    say()

    # ---------------- štatistiky po n a stabilita medzi seedmi
    s = summary_by_n(df)
    s.round(3).to_csv(outdir / "rpd_summary_by_n.csv", index=False)
    st = seed_stability(df)
    st.round(3).to_csv(outdir / "seed_stability.csv", index=False)
    say("Štatistiky rpd IGA po n (priemer, medián, sm. odch., min, max cez inštancie × seedy):")
    for impl in IMPLS:
        say(f"  {IMPLS[impl]}")
        for _, row in s[(s.impl == impl) & (s.variant == "IGA")].iterrows():
            say(f"    n = {row.n:3d}: {row['mean']:.2f}, {row['median']:.2f}, {row['std']:.2f}, "
                f"{row['min']:.2f}, {row['max']:.2f}")
    say("Stabilita medzi seedmi (IGA): priemerná sm. odchýlka rpd jednej inštancie cez seedy:")
    for impl in IMPLS:
        x = st[st.impl == impl].set_index("n")
        say(f"  {IMPLS[impl]}: " + ", ".join(f"n={n}: {x.loc[n, 'std_over_seeds']:.2f}" for n in x.index))
    say()

    # ---------------- štatistické testy
    say("Wilcoxonov test, naša vs. autori (pár = inštancia, priemer ΣC cez spoločné seedy):")
    per_inst = df.groupby(["instance", "impl"])[[f"{v}_ft" for v in VARIANTS]].mean().unstack("impl")
    for v, vname in VARIANTS.items():
        wilcoxon_line(per_inst[(f"{v}_ft", "ours")], per_inst[(f"{v}_ft", "authors")], vname)
    # nevýznamný test zhodu nedokazuje – preto aj veľkosť rozdielu s 95 % intervalom spoľahlivosti
    say("Rozdiel priemernej rpd naša − autori [p. b.] (pár = inštancia), 95 % interval spoľahlivosti (t):")
    per_rpd = df.groupby(["instance", "impl"])[[f"rpd_{v}" for v in VARIANTS]].mean().unstack("impl")
    for v, vname in VARIANTS.items():
        d = per_rpd[(f"rpd_{v}", "ours")] - per_rpd[(f"rpd_{v}", "authors")]
        half = t_dist.ppf(0.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d))
        say(f"  {vname}: {d.mean():.4f} [{d.mean() - half:.4f}; {d.mean() + half:.4f}]")
    say("Wilcoxonov test, prínos 2. fázy a NPS-set v našej implementácii (pár = beh):")
    ours = df[df.impl == "ours"]
    wilcoxon_line(ours.iga_ft, ours.iga0_ft, "IGA vs IGA0")
    wilcoxon_line(ours.nps_ft, ours.iga0_ft, "IGA+NPS-set vs IGA0")
    wilcoxon_line(ours.iga_ft, ours.nps_ft, "IGA vs IGA+NPS-set")
    say()

    # ---------------- grafy
    fig_rpd_by_n(df, figdir / "rpd_by_n.pdf")
    fig_time(df, figdir / "time_scatter.pdf")
    fig_seed_box(df, figdir / "seed_box.pdf")
    if Path(args.history).exists():
        hist = pd.concat([pd.read_csv(p) for p in [Path(args.history)] + c_hist], ignore_index=True)
        fig_convergence(hist.drop_duplicates(["instance", "seed", "iteration"]), df, figdir / "convergence.pdf")

    (outdir / "summary.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print("Uložené do", outdir, figdir, texdir)


if __name__ == "__main__":
    main()
