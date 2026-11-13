"""
Analýza hlavného experimentu na PÔVODNÝCH inštanciách Henneberg & Neufeld (2016):
naša implementácia vs. pôvodný program autorov (obe v Google Colabe, colab/povodne_instancie.ipynb)
vs. výsledky článku po inštanciách (data/authors/, stiahne src/fetch_original.py).

Vstupy (results/original/):
    iga_ours_*.csv (+ *_history.csv)        – naša implementácia (src/run_experiments.py)
    iga_authors_*.csv                       – program autorov (reference/run_authors.py)
    iga_ours-sampling-autori_*.csv          – voliteľne: naša implementácia s výberom jobov
                                              ako v programe autorov (--sampling autori)
Výstupy:
    results/original/analysis/summary.txt a *.csv
    report/tables/orig_*.tex, report/figures/orig_*.pdf

Metodika:
  * BKV = najlepšie známe hodnoty z článku (data/authors/table3-bkv.csv) – rovnaké ako v článku,
    takže relatívne odchýlky sú priamo porovnateľné s Tab. 3 a 6. Ak niektorý náš beh BKV
    prekoná, odchýlka je záporná (počet takých behov sa vypíše).
  * Pre n = 5 sú BKV optimá (MIP autorov vyriešil všetky inštancie s n = 5, Tab. 5).
  * Pre každú inštanciu sa používajú len seedy, ktoré prebehli v oboch implementáciách.
    Naša implementácia a program autorov sa porovnávajú párovo po inštanciách (priemer cez
    seedy), Wilcoxonov test + 95 % interval spoľahlivosti rozdielu (t-rozdelenie).
  * Program autorov so seedom 1 má dať presne hodnoty z článku (kontrola reprodukovateľnosti).

Spustenie (z koreňa repozitára):
    python src/fetch_original.py         # inštancie a dáta autorov (ak ešte nie sú)
    python analysis/analyze_original.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402
import pandas as pd               # noqa: E402
from scipy.stats import wilcoxon  # noqa: E402
from scipy.stats import t as t_dist   # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_results import (IMPLS, NS, VARIANTS, fig_convergence, fig_seed_box,   # noqa: E402
                             group_table, latex_table, seed_stability, summary_by_n, with_avg)

ROOT = Path(__file__).resolve().parent.parent
PAPER_COLS = {"iga": "igapols.ft", "iga0": "igapo.ft", "nps": "igapo.nps.ft"}
SAMPLING = "ours_sampling"            # naša implementácia s výberom jobov ako autori

out_lines: list[str] = []


def say(s: str = "") -> None:
    print(s)
    out_lines.append(s)


# --------------------------------------------------------------------------- načítanie

def instance_name(row) -> str:
    return f"{row.d:.1f}_{int(row.n):02d}_{int(row.m):02d}_{int(row.i):02d}"


def load_paper(data_dir: Path) -> pd.DataFrame:
    """Výsledky článku po inštanciách: BKV, IGA, IGA0, IGA+NPS-set, 2SA, časy IGA a 2SA."""
    key = ["d", "n", "m", "i"]
    t = pd.read_csv(data_dir / "table3-bkv.csv")
    for f in ("table3-iga.csv", "table6.csv", "table3-2sa.csv", "table4-iga.csv", "table4-2sa.csv"):
        t = t.merge(pd.read_csv(data_dir / f), on=key)
    t["instance"] = [instance_name(r) for r in t.itertuples()]
    t = t.rename(columns={"igapols.ft": "iga_ft", "igapo.ft": "iga0_ft", "igapo.nps.ft": "nps_ft",
                          "saf.ft": "sa_ft", "time": "time", "saf.t": "sa_time", "d": "r"})
    mip = pd.read_csv(data_dir / "table5-mip.csv")
    mip["instance"] = [instance_name(r) for r in mip.itertuples()]
    t = t.merge(mip[["instance", "mip.ft"]].rename(columns={"mip.ft": "mip_ft"}), on="instance", how="left")
    t["r"] = t["r"].round(1)
    return t.set_index("instance")


def read_many(paths: list[Path], impl: str) -> pd.DataFrame:
    if not paths:
        return pd.DataFrame()
    d = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    d = d.drop_duplicates(["instance", "seed"], keep="first").assign(impl=impl)
    d["n"], d["m"], d["r"] = d["n"].astype(int), d["m"].astype(int), d["r"].round(1)
    return d


def add_rpd(df: pd.DataFrame, bkv: pd.Series) -> pd.DataFrame:
    df = df.join(bkv.rename("bkv"), on="instance")
    for v in VARIANTS:
        df[f"rpd_{v}"] = 100 * (df[f"{v}_ft"] - df["bkv"]) / df["bkv"]
    return df


# --------------------------------------------------------------------------- štatistika

def paired(a: pd.Series, b: pd.Series) -> dict:
    """Párový rozdiel a − b: priemer, 95 % CI (t), Wilcoxon p, počty lepšie/rovnaké/horšie."""
    d = (a - b).dropna()
    half = t_dist.ppf(0.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else np.nan
    p = wilcoxon(d[d != 0]).pvalue if (d != 0).sum() > 0 else 1.0
    return dict(mean=d.mean(), lo=d.mean() - half, hi=d.mean() + half, p=p,
                better=int((d < 0).sum()), equal=int((d == 0).sum()), worse=int((d > 0).sum()), k=len(d))


def per_instance(df: pd.DataFrame, col: str) -> pd.Series:
    return df.groupby("instance")[col].mean()


def fmt_p(p: float) -> str:
    return "$<0{,}001$" if p < 0.001 else f"{p:.3f}".replace(".", "{,}")


def fmt_ci(r: dict) -> str:
    f = lambda x: f"{x + 0.0:.3f}".replace("-0.000", "0.000").replace(".", "{,}").replace("-", "$-$")  # noqa: E731
    return f"{f(r['mean'])} [{f(r['lo'])}; {f(r['hi'])}]"


# --------------------------------------------------------------------------- tabuľky

def tex_table(path: Path, caption: str, label: str, colspec: str, header: list[str], rows: list[list[str]],
              size: str = r"\small") -> None:
    lines = [r"\begin{table}[ht]", r"\centering", size, rf"\caption{{{caption}}}", rf"\label{{{label}}}",
             rf"\begin{{tabular}}{{{colspec}}}", r"\toprule", *[h + r" \\" for h in header], r"\midrule"]
    for row in rows:
        if row == ["MIDRULE"]:
            lines.append(r"\midrule")
        else:
            lines.append(" & ".join(row) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compact_by_n(path: Path, by_n: dict) -> None:
    rows = []
    for n in NS + ["priemer"]:
        if n == "priemer":
            rows.append(["MIDRULE"])
        cells = [str(n)]
        for t_o, t_a, t_p in by_n.values():
            for t in (t_o, t_a, t_p):
                x = t.mean() if n == "priemer" else t.get(f"n{n}", np.nan)
                cells.append("" if pd.isna(x) else f"{x:.2f}")
        rows.append(cells)
    tex_table(path,
              caption=r"Pôvodné inštancie: priemerná relatívna odchýlka od BKV článku v \% podľa počtu "
                      r"jobov $n$ (priemer cez $r$, $m$, 30 inštancií v skupine a seedy). N = naša "
                      r"implementácia, A = program autorov (obe seedy 1--10), Č = článok (seed 1).",
              label="tab:orig_rpd_by_n", colspec="r" + "|rrr" * len(by_n),
              header=[" & " + " & ".join(rf"\multicolumn{{3}}{{c}}{{{v}}}" for v in by_n),
                      "$n$ & " + " & ".join(["N & A & Č"] * len(by_n))], rows=rows)


# --------------------------------------------------------------------------- grafy

def fig_rpd_by_n(df: pd.DataFrame, paper: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    colors = {"iga0": "#c0504d", "nps": "#e1a33b", "iga": "#4f81bd"}
    pg = {v: group_table(paper, f"rpd_{v}").mean() for v in VARIANTS}
    for v, vname in VARIANTS.items():
        ax.plot(NS, [pg[v][f"n{n}"] for n in NS], ":", marker="s", color=colors[v], alpha=.6,
                label=f"{vname} – článok")
        for impl, ls, mk in (("authors", "--", "^"), ("ours", "-", "o")):
            y = group_table(df[df.impl == impl], f"rpd_{v}").mean().reindex([f"n{n}" for n in NS])
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


def fig_time_vs_paper(df: pd.DataFrame, paper: pd.DataFrame, path: Path) -> None:
    """Ako Obr. 4 článku: čas na inštanciu, článok (i7-13700) na osi x, naše behy na osi y."""
    fig, ax = plt.subplots(figsize=(4.6, 3.8))
    marks = {"ours": ("o", "#4f81bd"), "authors": ("^", "#9bbb59")}
    for impl, (mk, c) in marks.items():
        t = df[df.impl == impl].groupby("instance")["time"].mean()
        x = paper.loc[t.index, "time"]
        ax.scatter(x, t, s=5, marker=mk, color=c, alpha=.45, label=IMPLS[impl] + " (Colab)")
    lim = [paper["time"].min() / 2, df["time"].max() * 2]
    ax.plot(lim, lim, "k-", lw=.8, label="rovnaký čas")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("čas IGA v článku [s]")
    ax.set_ylabel("čas nášho behu [s]")
    ax.grid(alpha=.3, which="both", lw=.3)
    ax.legend(fontsize=7, markerscale=2)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# --------------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "results" / "original"))
    ap.add_argument("--data", default=str(ROOT / "data" / "authors"))
    ap.add_argument("--outdir", default=None, help="predvolene <results>/analysis")
    ap.add_argument("--texdir", default=str(ROOT / "report" / "tables"))
    ap.add_argument("--figdir", default=str(ROOT / "report" / "figures"))
    ap.add_argument("--time-seeds", nargs="+", type=int, default=[6, 7, 8, 9, 10],
                    help="seedy, z ktorých sa počítajú časy (všetky bežali na rovnakom type runtime)")
    args = ap.parse_args()

    res = Path(args.results)
    outdir = Path(args.outdir) if args.outdir else res / "analysis"
    texdir, figdir = Path(args.texdir), Path(args.figdir)
    for d in (outdir, texdir, figdir):
        d.mkdir(parents=True, exist_ok=True)

    paper = load_paper(Path(args.data))
    files = sorted(res.glob("*.csv"))
    ours = read_many([p for p in files if p.name.startswith("iga_ours_") and "history" not in p.name], "ours")
    auth = read_many([p for p in files if p.name.startswith("iga_authors_")], "authors")
    samp = read_many([p for p in files if p.name.startswith("iga_ours-sampling-autori_")
                      and "history" not in p.name], SAMPLING)
    hist_files = [p for p in files if p.name.startswith("iga_ours_") and p.name.endswith("_history.csv")]

    # ---------------- 1. reprodukovateľnosť článku: program autorov, seed 1 = hodnoty z článku
    a1 = auth[auth.seed == 1].set_index("instance")
    say(f"Program autorov, seed 1: {len(a1)} inštancií")
    for v, vname in VARIANTS.items():
        same = (a1[f"{v}_ft"] == paper.loc[a1.index, f"{v}_ft"])
        say(f"  {vname}: rovnaké ΣC ako v článku na {same.sum()} z {len(same)} inštancií")
    say()

    # ---------------- spoločné behy, rpd voči BKV článku
    cols = [c for c in auth.columns if c in ours.columns]
    df = pd.concat([ours[cols + ["time_phase1", "time_phase2"]], auth[cols]], ignore_index=True)
    common = df.groupby(["instance", "seed"])["impl"].nunique()
    common = common[common == 2].index
    df = df.set_index(["instance", "seed"]).loc[common].reset_index()
    df = add_rpd(df, paper["bkv"])
    pp = add_rpd(paper.reset_index()[["instance", "r", "n", "m", "iga_ft", "iga0_ft", "nps_ft"]],
                 paper["bkv"])
    pp["sa_rpd"] = 100 * (paper["sa_ft"].values - paper["bkv"].values) / paper["bkv"].values
    seeds = df.groupby("n")["seed"].unique().map(lambda s: sorted(int(x) for x in s))
    say(f"Spoločné behy: {df.instance.nunique()} inštancií, {len(df) // 2} behov na implementáciu")
    for n, s in seeds.items():
        say(f"  n = {n}: seedy {s}")
    for impl in IMPLS:
        d = df[df.impl == impl]
        say(f"  {IMPLS[impl]}: behov lepších než BKV článku {int((d[[f'rpd_{v}' for v in VARIANTS]] < 0).any(axis=1).sum())}")
    n5 = paper[paper.n == 5]
    say(f"  n = 5: MIP článku = BKV na {(n5.mip_ft == n5.bkv).sum()} z {len(n5)} inštancií (BKV sú optimá)")
    say()

    # ---------------- kvalita po skupinách a po n (Tab. 3 a 6 článku)
    by_n = {}
    for v, vname in VARIANTS.items():
        t_o = group_table(df[df.impl == "ours"], f"rpd_{v}")
        t_a = group_table(df[df.impl == "authors"], f"rpd_{v}")
        t_p = group_table(pp, f"rpd_{v}")
        for name, t in (("ours", t_o), ("authors", t_a), ("paper", t_p)):
            with_avg(t).round(3).to_csv(outdir / f"rpd_{v}_{name}.csv")
        latex_table(texdir / f"orig_rpd_{v}.tex", {IMPLS["ours"]: t_o, IMPLS["authors"]: t_a, "článok": t_p},
                    caption=f"Pôvodné inštancie, {vname}: priemerná relatívna odchýlka od BKV článku v \\% "
                            f"po skupinách (naša implementácia a program autorov: priemer cez seedy 1--10; "
                            f"článok: seed 1).", label=f"tab:orig_rpd_{v}")
        by_n[vname] = (t_o.mean(), t_a.mean(), t_p.mean())
        say(f"{vname}: priemerná rpd po n (naša | autori | článok)")
        for n in NS:
            say(f"  n = {n:3d}: {t_o[f'n{n}'].mean():5.2f} | {t_a[f'n{n}'].mean():5.2f} | {t_p[f'n{n}'].mean():5.2f}")
        say(f"  celkovo:  {t_o.values.mean():5.2f} | {t_a.values.mean():5.2f} | {t_p.values.mean():5.2f}")
    t_sa = group_table(pp, "sa_rpd")
    say("2SA (článok, Tab. 3): " + ", ".join(f"n={n}: {t_sa[f'n{n}'].mean():.2f}" for n in NS))
    compact_by_n(texdir / "orig_rpd_by_n.tex", by_n)
    say()

    # ---------------- zlepšenie oproti IGA0 (Tab. 6 vs Tab. 3)
    say("Zlepšenie oproti IGA0 [p. b.] (naša | autori | článok):")
    for v in ("iga", "nps"):
        imp = {k: group_table(d, "rpd_iga0") - group_table(d, f"rpd_{v}")
               for k, d in (("ours", df[df.impl == "ours"]), ("authors", df[df.impl == "authors"]), ("paper", pp))}
        say(f"  {VARIANTS[v]}: " + ", ".join(
            f"n={n}: {imp['ours'][f'n{n}'].mean():.2f} | {imp['authors'][f'n{n}'].mean():.2f} | "
            f"{imp['paper'][f'n{n}'].mean():.2f}" for n in NS))
        say(f"    celkovo {imp['ours'].values.mean():.2f} | {imp['authors'].values.mean():.2f} | "
            f"{imp['paper'].values.mean():.2f}")
    for impl in IMPLS:
        d = df[df.impl == impl]
        say(f"  {IMPLS[impl]}: 2. fáza zlepšila IGA0 v {(d.iga_ft < d.iga0_ft).mean():.1%} behov, "
            f"NPS-set v {(d.nps_ft < d.iga0_ft).mean():.1%}; IGA lepšie než IGA+NPS-set v "
            f"{(d.iga_ft < d.nps_ft).mean():.1%}, horšie v {(d.iga_ft > d.nps_ft).mean():.1%}")
    say()

    # ---------------- n = 5: odchýlka od optima (BKV článku = optimum)
    d5 = df[df.n == 5]
    rows = []
    for (r, m), g in d5.groupby(["r", "m"]):
        go, ga = g[g.impl == "ours"], g[g.impl == "authors"]
        gp = pp[(pp.n == 5) & (pp.r == r) & (pp.m == m)]
        rows.append([f"{r:.1f}", str(m), f"{go.rpd_iga.mean():.2f}", f"{ga.rpd_iga.mean():.2f}",
                     f"{gp.rpd_iga.mean():.2f}", f"{(go.rpd_iga == 0).mean():.0%}".replace("%", r"\,\%"),
                     f"{(gp.rpd_iga == 0).mean():.0%}".replace("%", r"\,\%")])
    go, ga, gp = d5[d5.impl == "ours"], d5[d5.impl == "authors"], pp[pp.n == 5]
    rows += [["MIDRULE"], ["spolu", "", f"{go.rpd_iga.mean():.2f}", f"{ga.rpd_iga.mean():.2f}",
                           f"{gp.rpd_iga.mean():.2f}", f"{(go.rpd_iga == 0).mean():.0%}".replace("%", r"\,\%"),
                           f"{(gp.rpd_iga == 0).mean():.0%}".replace("%", r"\,\%")]]
    tex_table(texdir / "orig_opt_n5.tex",
              caption=r"Pôvodné inštancie s $n=5$: odchýlka IGA od optima v \% a podiel behov, v ktorých "
                      r"IGA optimum našlo (optimá z MIP autorov). N = naša, A = program autorov, Č = článok.",
              label="tab:orig_opt_n5", colspec="ll|rrr|rr",
              header=[r" & & \multicolumn{3}{c|}{odchýlka [\%]} & \multicolumn{2}{c}{optimum}",
                      "$r$ & $m$ & N & A & Č & N & Č"], rows=rows)
    say(f"n = 5, IGA od optima: naša {go.rpd_iga.mean():.2f} %, autori {ga.rpd_iga.mean():.2f} %, "
        f"článok {gp.rpd_iga.mean():.2f} %; optimum v {(go.rpd_iga == 0).mean():.0%} | "
        f"{(ga.rpd_iga == 0).mean():.0%} | {(gp.rpd_iga == 0).mean():.0%} behov")
    say()

    # ---------------- naša vs. program autorov: párové porovnanie po n
    say("Naša − autori, rpd [p. b.], pár = inštancia (priemer cez seedy): priemer [95 % CI], Wilcoxon p")
    rows = []
    stats = {}
    present = [n for n in NS if n in set(df.n)]
    for n in present + ["spolu"]:
        d = df if n == "spolu" else df[df.n == n]
        cells = [str(n)]
        for v in ("iga0", "nps", "iga"):
            st = paired(per_instance(d[d.impl == "ours"], f"rpd_{v}"), per_instance(d[d.impl == "authors"], f"rpd_{v}"))
            stats[(n, v)] = st
            cells += [fmt_ci(st), fmt_p(st["p"])]
        if n == "spolu":
            rows.append(["MIDRULE"])
        rows.append(cells)
        say(f"  n = {n}: " + "; ".join(
            f"{VARIANTS[v]} {stats[(n, v)]['mean']:.4f} [{stats[(n, v)]['lo']:.4f}; {stats[(n, v)]['hi']:.4f}] "
            f"p = {stats[(n, v)]['p']:.3g} (lepšie {stats[(n, v)]['better']}, rovnaké {stats[(n, v)]['equal']}, "
            f"horšie {stats[(n, v)]['worse']})" for v in ("iga0", "nps", "iga")))
    tex_table(texdir / "orig_tests.tex",
              caption=r"Pôvodné inštancie: rozdiel priemernej relatívnej odchýlky naša implementácia $-$ "
                      r"program autorov v p.\,b.\ (pár = inštancia, priemer cez seedy 1--10) s 95\,\% "
                      r"intervalom spoľahlivosti a $p$-hodnota Wilcoxonovho testu. Kladný rozdiel = naša "
                      r"implementácia je horšia.",
              label="tab:orig_tests", colspec="r|rr|rr|rr", size=r"\scriptsize",
              header=[r" & \multicolumn{2}{c|}{IGA0} & \multicolumn{2}{c|}{IGA+NPS-set} & \multicolumn{2}{c}{IGA}",
                      r"$n$ & rozdiel [95\,\% CI] & $p$ & rozdiel [95\,\% CI] & $p$ & rozdiel [95\,\% CI] & $p$"],
              rows=rows)
    say()

    # ---------------- experiment: výber jobov ako v programe autorov
    if not samp.empty:
        sm = add_rpd(samp, paper["bkv"])
        say("Naša implementácia s výberom jobov ako autori (--sampling autori) − program autorov:")
        rows = []
        for n in sorted(sm.n.unique()):
            ds = sm[sm.n == n]
            s_seeds = set(ds.seed)
            da = df[(df.impl == "authors") & (df.n == n) & df.seed.isin(s_seeds)]
            do = df[(df.impl == "ours") & (df.n == n) & df.seed.isin(s_seeds)]
            cells = [str(n)]
            for v in ("iga0", "iga"):
                st_u = paired(per_instance(do, f"rpd_{v}"), per_instance(da, f"rpd_{v}"))
                st_s = paired(per_instance(ds, f"rpd_{v}"), per_instance(da, f"rpd_{v}"))
                cells += [fmt_ci(st_u), fmt_p(st_u["p"]), fmt_ci(st_s), fmt_p(st_s["p"])]
                say(f"  n = {n}, {VARIANTS[v]}: rovnomerný výber {st_u['mean']:.4f} [{st_u['lo']:.4f}; "
                    f"{st_u['hi']:.4f}] p = {st_u['p']:.3g} | výber ako autori {st_s['mean']:.4f} "
                    f"[{st_s['lo']:.4f}; {st_s['hi']:.4f}] p = {st_s['p']:.3g}")
            rows.append(cells)
        tex_table(texdir / "orig_sampling.tex",
                  caption=r"Vplyv výberu odstránených jobov v perturbácii: rozdiel rpd naša implementácia "
                          r"$-$ program autorov v p.\,b.\ (95\,\% CI, Wilcoxon $p$) s rovnomerným výberom "
                          r"(ako v článku) a s výberom, ktorý napodobňuje program autorov.",
                  label="tab:orig_sampling", colspec="r|rr|rr|rr|rr", size=r"\scriptsize\setlength{\tabcolsep}{2pt}",
                  header=[r" & \multicolumn{4}{c|}{IGA0} & \multicolumn{4}{c}{IGA}",
                          r" & \multicolumn{2}{c|}{rovnomerný} & \multicolumn{2}{c|}{ako autori} & "
                          r"\multicolumn{2}{c|}{rovnomerný} & \multicolumn{2}{c}{ako autori}",
                          r"$n$ & rozdiel & $p$ & rozdiel & $p$ & rozdiel & $p$ & rozdiel & $p$"], rows=rows)
        say()

    # ---------------- štatistiky rpd a stabilita medzi seedmi
    s = summary_by_n(df)
    s.round(3).to_csv(outdir / "rpd_summary_by_n.csv", index=False)
    st = seed_stability(df)
    st.round(3).to_csv(outdir / "seed_stability.csv", index=False)
    rows = []
    for n in present:
        cells = [str(n)]
        for impl in IMPLS:
            x = s[(s.impl == impl) & (s.variant == "IGA") & (s.n == n)].iloc[0]
            cells += [f"{x['mean']:.2f}", f"{x['median']:.2f}", f"{x['std']:.2f}", f"{x['min']:.2f}",
                      f"{x['max']:.2f}"]
        stab = st[(st.impl == "ours") & (st.n == n)].iloc[0]
        cells += [f"{stab.std_over_seeds:.2f}", f"{stab.n_seed_mean_min:.2f}--{stab.n_seed_mean_max:.2f}"]
        rows.append(cells)
    tex_table(texdir / "orig_rpd_stats.tex",
              caption=r"Pôvodné inštancie, IGA: štatistiky relatívnej odchýlky od BKV v \% cez všetky behy "
                      r"(inštancie $\times$ seedy 1--10); záporné minimum znamená beh lepší než BKV článku. "
                      r"Stabilita: priemerná smerodajná odchýlka rpd jednej inštancie cez seedy a rozsah "
                      r"priemeru cez 360 inštancií pri jednotlivých seedoch (naša implementácia).",
              label="tab:orig_rpd_stats", colspec="r|rrrrr|rrrrr|rr", size=r"\scriptsize\setlength{\tabcolsep}{3pt}",
              header=[r" & \multicolumn{5}{c|}{naša (Python)} & \multicolumn{5}{c|}{autori (C++)} & "
                      r"\multicolumn{2}{c}{stabilita (naša)}",
                      r"$n$ & priemer & medián & sm.\,odch. & min & max & priemer & medián & sm.\,odch. & min & "
                      r"max & sm.\,odch. & priemer seedu"], rows=rows)
    say("Štatistiky rpd IGA po n (priemer, medián, sm. odch., min, max):")
    for impl in IMPLS:
        say(f"  {IMPLS[impl]}")
        for _, row in s[(s.impl == impl) & (s.variant == "IGA")].iterrows():
            say(f"    n = {row.n:3d}: {row['mean']:.2f}, {row['median']:.2f}, {row['std']:.2f}, "
                f"{row['min']:.2f}, {row['max']:.2f}")
    say("Stabilita medzi seedmi (IGA), sm. odchýlka rpd inštancie | rozsah priemerov seedov:")
    for impl in IMPLS:
        x = st[st.impl == impl].set_index("n")
        say(f"  {IMPLS[impl]}: " + ", ".join(
            f"n={n}: {x.loc[n, 'std_over_seeds']:.2f} | {x.loc[n, 'n_seed_mean_min']:.2f}–{x.loc[n, 'n_seed_mean_max']:.2f}"
            for n in x.index))
    say()

    # ---------------- časy (Tab. 4 a Obr. 4 článku) – len zo seedov, ktoré bežali na rovnakom
    # type runtime (results/original/info_session*.txt: seedy 1–5 pre n <= 50 bežali na 2 vCPU)
    dt = df[df.seed.isin(args.time_seeds)]
    say(f"Časy zo seedov {args.time_seeds} ({len(dt) // 2} behov na implementáciu)")
    t_o = group_table(dt[dt.impl == "ours"], "time", index=("m",))
    t_a = group_table(dt[dt.impl == "authors"], "time", index=("m",))
    t_p = group_table(paper.reset_index(), "time", index=("m",))
    latex_table(texdir / "orig_time.tex", {IMPLS["ours"]: t_o, IMPLS["authors"]: t_a, "článok": t_p},
                caption="Pôvodné inštancie: priemerný čas behu IGA v sekundách (obe fázy). Naše behy: "
                        "Google Colab (Xeon 2,2\\,GHz, 12 vCPU, 12 paralelných behov), seedy "
                        + ", ".join(map(str, args.time_seeds)) + "; článok: Core i7-13700, seed 1.",
                label="tab:orig_time", index_names=("$m$",), fmt="{:.2f}")
    say("Priemerný čas IGA [s] po n (naša | autori | článok) a pomer naša/článok:")
    for n in NS:
        o, a, p_ = t_o[f"n{n}"].mean(), t_a[f"n{n}"].mean(), t_p[f"n{n}"].mean()
        say(f"  n = {n:3d}: {o:7.2f} | {a:7.2f} | {p_:7.2f}   ({o / p_:.1f}×, autori {a / p_:.1f}×)")
    ours_t = dt[dt.impl == "ours"]
    share2 = (ours_t.time_phase2 / ours_t.time).groupby(ours_t.n).mean()
    say("  podiel 2. fázy na našom čase: " + ", ".join(f"n={n}: {share2[n]:.0%}" for n in share2.index))
    say()

    # ---------------- grafy
    fig_rpd_by_n(df, pp, figdir / "orig_rpd_by_n.pdf")
    fig_time_vs_paper(dt, paper, figdir / "orig_time_scatter.pdf")
    fig_seed_box(df, figdir / "orig_seed_box.pdf")
    if hist_files:
        hist = pd.concat([pd.read_csv(p) for p in hist_files], ignore_index=True)
        fig_convergence(hist.drop_duplicates(["instance", "seed", "iteration"]), df,
                        figdir / "orig_convergence.pdf")

    (outdir / "summary.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print("Uložené do", outdir, figdir, texdir)


if __name__ == "__main__":
    main()
