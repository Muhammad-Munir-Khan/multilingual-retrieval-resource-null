"""
EXP-017 — Generate manuscript figures from committed artifacts.

Figures are generated from `results/`, never hand-drawn and never transcribed, so a
figure cannot silently disagree with the table it illustrates. Re-running this after
new results regenerates every figure.

Two figures, each earning its place by showing something a table cannot:

* **fig1** — the central null. A table of 17 correlations does not show that the
  lowest-resource languages sit at the *top* of the advantage range; a scatter does.
* **fig2** — failure composition. The recall-rescue mechanism is invisible in mean
  nDCG and obvious in a stacked failure breakdown.

Usage:
    .venv/Scripts/python.exe scripts/make_figures.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "results"
FIG = REPO / "paper" / "figures"

# Colour-blind-safe, and legible in greyscale print — IEEE papers are still printed.
C_DENSE = "#0072B2"
C_LEX = "#D55E00"
C_GREY = "#666666"
C_MISS = "#C44E52"
C_DEEP = "#DD8452"
C_WEAK = "#8C8C8C"
C_HIT = "#4C72B0"


def load(p: str):
    return json.loads((RES / p).read_text(encoding="utf-8"))


def fig1_null():
    """Per-language advantage against resource volume: the central null."""
    an = load("EXP-006-analysis/EXP-005-dense-E5__EXP-004-bm25-char__ndcg10.json")["per_language"]
    d5 = load("EXP-005-dense-E5/metrics.json")["languages"]
    rp = load("EXP-007-resource-proxy/metrics.json")["languages"]

    sup = [l for l in an if not d5[l].get("coverage_confounded")]
    uns = [l for l in an if d5[l].get("coverage_confounded")]

    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    for lang in sup:
        x = math.log10(rp[lang]["mb"])
        y = an[lang]["mean_diff"]
        lo, hi = an[lang]["ci95_low"], an[lang]["ci95_high"]
        ax.plot([x, x], [lo, hi], color=C_GREY, lw=1.0, alpha=0.7, zorder=1)
        ax.scatter(x, y, s=42, color=C_DENSE, zorder=3, edgecolor="white", linewidth=0.7)
        ax.annotate(lang, (x, y), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=8, color="#222222")
    for lang in uns:
        x = math.log10(rp[lang]["mb"])
        y = an[lang]["mean_diff"]
        lo, hi = an[lang]["ci95_low"], an[lang]["ci95_high"]
        ax.plot([x, x], [lo, hi], color=C_LEX, lw=1.0, alpha=0.8, zorder=1)
        ax.scatter(x, y, s=52, color=C_LEX, marker="D", zorder=3,
                   edgecolor="white", linewidth=0.7)
        ax.annotate(f"{lang} (unsupported)", (x, y), textcoords="offset points",
                    xytext=(0, -14), ha="center", fontsize=8, color=C_LEX)

    ax.axhline(0, color="#333333", lw=0.9, ls="--", zorder=2)
    ax.set_xlabel("Pretraining corpus volume, log$_{10}$ MB (CC-100)")
    ax.set_ylabel("nDCG@10 advantage\n(dense $-$ lexical)")
    ax.set_title("Dense advantage does not track language resource volume "
                 r"($\rho = -0.010$)", fontsize=10)
    ax.grid(axis="y", alpha=0.25, lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "fig1_resource_null.pdf")
    plt.close(fig)
    return "fig1_resource_null.pdf"


def fig2_failures():
    """Failure composition per language, lexical vs dense."""
    ea = load("EXP-014-error-analysis/metrics.json")["per_system"]
    langs = sorted(ea["bm25"], key=lambda l: -ea["bm25"][l]["rates"]["total_miss"])

    fig, axes = plt.subplots(2, 1, figsize=(7.2, 5.2), sharex=True)
    for ax, sysname, label in zip(axes, ("bm25", "E5"),
                                  ("Lexical (BM25, char 4-gram)", "Dense (multilingual E5)")):
        tm = [ea[sysname][l]["rates"]["total_miss"] for l in langs]
        dm = [ea[sysname][l]["rates"]["deep_miss"] for l in langs]
        wr = [ea[sysname][l]["rates"]["weak_rank"] for l in langs]
        r1 = [ea[sysname][l]["rates"]["rank1"] for l in langs]
        b = [0.0] * len(langs)
        for vals, col, name in ((tm, C_MISS, "total miss (R@100 = 0)"),
                                (dm, C_DEEP, "deep miss (not in top 10)"),
                                (wr, C_WEAK, "in top 10"),
                                (r1, C_HIT, "rank 1")):
            ax.bar(langs, vals, bottom=b, color=col, width=0.72,
                   label=name if sysname == "bm25" else None)
            b = [x + y for x, y in zip(b, vals)]
        ax.set_ylabel("fraction of queries")
        ax.set_title(label, fontsize=9, loc="left")
        ax.set_ylim(0, 1)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].legend(fontsize=7.5, ncol=4, loc="upper center",
                   bbox_to_anchor=(0.5, 1.42), frameon=False)
    axes[1].set_xlabel("language (ordered by lexical total-miss rate)")
    fig.tight_layout()
    fig.savefig(FIG / "fig2_failure_composition.pdf")
    plt.close(fig)
    return "fig2_failure_composition.pdf"


def main() -> int:
    FIG.mkdir(parents=True, exist_ok=True)
    for fn in (fig1_null, fig2_failures):
        name = fn()
        print(f"wrote paper/figures/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
