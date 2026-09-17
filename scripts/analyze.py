"""
EXP-006 — Statistical analysis, implementing the pre-registered plan (protocol §7).

Primary evidence: paired, within-language comparison of dense vs BM25 on identical
queries and identical sub-corpora, with a bootstrap CI over queries.

Aggregation: DerSimonian-Laird random-effects meta-analysis across languages,
weighting by inverse variance. This is the mechanism that lets Yoruba stay in the
study despite having only 119 queries - it receives low weight automatically rather
than being dropped by hand.

The cross-language regression on fertility is deliberately NOT implemented as a
significance test. Protocol §7 demotes it to descriptive: n=18 with collinear
predictors is underpowered, and reporting a p-value there would invite exactly the
causal reading constraint C1 forbids.

Usage:
    .venv/Scripts/python.exe scripts/analyze.py --dense EXP-005-dense-A
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"

SEED = 20260811          # protocol §7
N_BOOT = 10_000          # protocol §7
METRIC = "ndcg@10"       # protocol §6 primary
SECONDARY = ("recall@100", "mrr@10")


def load_per_query(exp: str, lang: str) -> dict | None:
    p = RESULTS / exp / f"per_query_{lang}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def paired_bootstrap(diff: np.ndarray, rng: np.random.Generator) -> dict:
    """Bootstrap over queries. `diff` is per-query (dense - bm25)."""
    n = len(diff)
    idx = rng.integers(0, n, size=(N_BOOT, n))
    means = diff[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {
        "n_queries": int(n),
        "mean_diff": float(diff.mean()),
        "ci95_low": float(lo),
        "ci95_high": float(hi),
        "boot_se": float(means.std(ddof=1)),
        # A CI excluding zero is reported as such. It is NOT relabelled
        # "significant" - protocol §7 reserves inference for the pooled estimate.
        "ci_excludes_zero": bool(lo > 0 or hi < 0),
    }


def dersimonian_laird(y: np.ndarray, v: np.ndarray) -> dict:
    """Random-effects pooling. y = effects, v = their variances."""
    k = len(y)
    if k == 0:
        return {}
    w = 1.0 / v
    fixed = float((w * y).sum() / w.sum())
    Q = float((w * (y - fixed) ** 2).sum())
    df = k - 1
    denom = w.sum() - (w ** 2).sum() / w.sum()
    tau2 = max(0.0, (Q - df) / denom) if denom > 0 else 0.0

    ws = 1.0 / (v + tau2)
    pooled = float((ws * y).sum() / ws.sum())
    se = float(np.sqrt(1.0 / ws.sum()))
    i2 = float(max(0.0, (Q - df) / Q)) if Q > 0 else 0.0

    return {
        "k_languages": int(k),
        "pooled_effect": pooled,
        "se": se,
        "ci95_low": pooled - 1.96 * se,
        "ci95_high": pooled + 1.96 * se,
        "tau2": tau2,
        "Q": Q,
        "df": df,
        "I2": i2,
        "heterogeneity_note": (
            "High I2 means the effect differs across languages, which is itself the "
            "H1a finding rather than a nuisance. Do not read the pooled value alone."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dense", required=True, help="e.g. EXP-005-dense-A")
    ap.add_argument("--bm25", default="EXP-004-bm25-char")
    ap.add_argument("--metric", default=METRIC)
    args = ap.parse_args()

    rng = np.random.default_rng(SEED)
    bm25_dir = RESULTS / args.bm25
    if not bm25_dir.exists():
        print(f"missing {bm25_dir}")
        return 1

    langs = sorted(p.stem.replace("per_query_", "")
                   for p in bm25_dir.glob("per_query_*.json"))

    per_lang, ys, vs, used = {}, [], [], []
    for lang in langs:
        b = load_per_query(args.bm25, lang)
        d = load_per_query(args.dense, lang)
        if not b or not d:
            continue
        # Pair strictly on query id. Any mismatch means the two systems were not
        # run on the same evaluation set, which would invalidate the pairing.
        qids = sorted(set(b) & set(d))
        if not qids:
            continue
        if len(qids) != len(b) or len(qids) != len(d):
            print(f"[{lang}] WARNING query-set mismatch: bm25={len(b)} dense={len(d)} "
                  f"common={len(qids)} - pairing on the intersection", flush=True)

        diff = np.array([d[q][args.metric] - b[q][args.metric] for q in qids])
        r = paired_bootstrap(diff, rng)
        r["bm25_mean"] = float(np.mean([b[q][args.metric] for q in qids]))
        r["dense_mean"] = float(np.mean([d[q][args.metric] for q in qids]))
        per_lang[lang] = r

        ys.append(r["mean_diff"])
        vs.append(max(r["boot_se"] ** 2, 1e-12))
        used.append(lang)

    if not used:
        print("no language has both BM25 and dense results yet - nothing to pool")
        return 0

    pooled = dersimonian_laird(np.array(ys), np.array(vs))

    out = {
        "experiment_id": "EXP-006",
        "metric": args.metric,
        "bm25_source": args.bm25,
        "dense_source": args.dense,
        "seed": SEED,
        "n_bootstrap": N_BOOT,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "per_language": per_lang,
        "pooled_random_effects": pooled,
        "interpretation_guard": (
            "Associational only. Encoders differ in training data and objective as "
            "well as tokenizer, so no causal attribution is licensed (constraint C1)."
        ),
    }
    out_dir = RESULTS / "EXP-006-analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    # The filename must encode the BM25 reference as well as the dense system.
    # It previously did not, so running a sensitivity analysis against a different
    # n-gram order silently overwrote the pre-registered primary. The artifact
    # recorded `bm25_source` internally, which is how the overwrite was eventually
    # detected, but detection after the fact is not the same as prevention.
    fname = f"{args.dense}__{args.bm25}__{args.metric.replace('@', '')}.json"
    (out_dir / fname).write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"\n{args.metric}: dense ({args.dense}) - BM25 ({args.bm25})\n")
    print(f"{'lang':<5}{'bm25':>8}{'dense':>8}{'diff':>9}{'ci95':>20}{'n':>6}")
    print("-" * 56)
    for lang in used:
        r = per_lang[lang]
        ci = f"[{r['ci95_low']:+.3f},{r['ci95_high']:+.3f}]"
        print(f"{lang:<5}{r['bm25_mean']:>8.4f}{r['dense_mean']:>8.4f}"
              f"{r['mean_diff']:>+9.4f}{ci:>20}{r['n_queries']:>6}")
    print("-" * 56)
    print(f"pooled (random effects, k={pooled['k_languages']}): "
          f"{pooled['pooled_effect']:+.4f} "
          f"[{pooled['ci95_low']:+.4f}, {pooled['ci95_high']:+.4f}]")
    print(f"tau2={pooled['tau2']:.5f}  I2={pooled['I2']:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
