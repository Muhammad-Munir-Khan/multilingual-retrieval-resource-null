"""
EXP-020 — Export derived analysis values that appear in the manuscript.

`scripts/verify_numbers.py` found three values printed in the paper that had been
computed inline during analysis and never written to an artifact: the per-language
differential pool exposure, and the I-squared values in the robustness table. A number
that exists only in a terminal scroll cannot be traced, which breaks the
claim-evidence chain even though the number is correct.

This recomputes them from committed inputs and writes them out, so every figure in
the manuscript resolves to a file.

Usage:
    .venv/Scripts/python.exe scripts/export_derived.py
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "results"
OUT = RES / "EXP-020-derived"

sys.path.insert(0, str(REPO / "scripts"))
from analyze import dersimonian_laird  # noqa: E402


def load(p: str):
    return json.loads((RES / p).read_text(encoding="utf-8"))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    an = load("EXP-006-analysis/EXP-005-dense-E5__EXP-004-bm25-char__ndcg10.json")["per_language"]
    bm = load("EXP-004-bm25-char/metrics.json")["languages"]
    e5 = load("EXP-005-dense-E5/metrics.json")["languages"]

    sup = [l for l in an if not e5[l].get("coverage_confounded")]

    # 1. Differential pool exposure (dense unjudged@10 minus lexical unjudged@10).
    exposure = {}
    for l in sup:
        ub = bm[l]["aggregate"]["mean_unjudged_in_top10"]
        ue = e5[l]["aggregate"]["mean_unjudged_in_top10"]
        exposure[l] = {"bm25_unjudged_top10": ub, "dense_unjudged_top10": ue,
                       "differential": round(ue - ub, 4)}
    diffs = [v["differential"] for v in exposure.values()]

    # 2. Pooled estimates under each exclusion set (the robustness table).
    def pool(langs):
        y = np.array([an[l]["mean_diff"] for l in langs])
        v = np.array([max(an[l]["boot_se"] ** 2, 1e-12) for l in langs])
        p = dersimonian_laird(y, v)
        return {"k": len(langs),
                "pooled": round(p["pooled_effect"], 4),
                "ci95_low": round(p["ci95_low"], 4),
                "ci95_high": round(p["ci95_high"], 4),
                "I2_percent": round(100 * p["I2"], 1),
                "tau2": round(p["tau2"], 5)}

    sets = {
        "all_supported": sup,
        "excluding_zh": [l for l in sup if l != "zh"],
        "excluding_zh_ko_ja": [l for l in sup if l not in ("zh", "ko", "ja")],
    }
    robustness = {k: pool(v) for k, v in sets.items()}

    payload = {
        "experiment_id": "EXP-020",
        "purpose": ("export derived values that appear in the manuscript but were "
                    "computed inline and never persisted (found by verify_numbers.py)"),
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "differential_pool_exposure": {
            "definition": "dense mean unjudged@10 minus lexical mean unjudged@10",
            "per_language": exposure,
            "mean": round(sum(diffs) / len(diffs), 4),
            "min": round(min(diffs), 4),
            "max": round(max(diffs), 4),
            "n_languages_dense_higher": sum(1 for d in diffs if d > 0),
            "n_languages": len(diffs),
        },
        "robustness_pooling": robustness,
    }
    (OUT / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("differential exposure: mean %.4f  min %.4f  max %.4f  dense-higher in %d/%d"
          % (payload["differential_pool_exposure"]["mean"],
             payload["differential_pool_exposure"]["min"],
             payload["differential_pool_exposure"]["max"],
             payload["differential_pool_exposure"]["n_languages_dense_higher"],
             payload["differential_pool_exposure"]["n_languages"]))
    for k, v in robustness.items():
        print(f"  {k:<22} k={v['k']:<3} pooled {v['pooled']:+.4f} I2 {v['I2_percent']}%")
    print(f"wrote {OUT / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
