"""
EXP-014 — Error analysis / failure categorisation (protocol §, master workflow).

Aggregate metrics say *how much* systems differ. They do not say *how* they fail,
and the protocol requires failure categorisation rather than means alone.

Categories are defined from per-query metrics that already exist, so this costs no
new retrieval:

| category | condition | reading |
| --- | --- | --- |
| `total_miss` | Recall@100 == 0 | nothing relevant surfaced at all |
| `deep_miss` | Recall@100 > 0 but nDCG@10 == 0 | found it, ranked it below 10 |
| `weak_rank` | nDCG@10 > 0 and MRR@10 < 1 | in the top 10, not at rank 1 |
| `rank1` | MRR@10 == 1 | relevant document first |

`total_miss` and `deep_miss` are qualitatively different failures. The first is a
recall failure the reranker cannot repair; the second is purely an ordering failure
and *is* repairable downstream. Reporting them together as "low nDCG" hides that.

Usage:
    .venv/Scripts/python.exe scripts/error_analysis.py
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
OUT = RESULTS / "EXP-014-error-analysis"

SYSTEMS = {
    "bm25": "EXP-004-bm25-char",
    "E5": "EXP-005-dense-E5",
    "LaBSE": "EXP-005-dense-LaBSE",
}


def categorise(m: dict) -> str:
    if m["recall@100"] == 0:
        return "total_miss"
    if m["ndcg@10"] == 0:
        return "deep_miss"
    if m["mrr@10"] < 1.0:
        return "weak_rank"
    return "rank1"


def load(exp: str, lang: str) -> dict | None:
    p = RESULTS / exp / f"per_query_{lang}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    langs = sorted(p.stem.replace("per_query_", "")
                   for p in (RESULTS / SYSTEMS["bm25"]).glob("per_query_*.json"))

    per_system: dict[str, dict] = {}
    for sys_name, exp in SYSTEMS.items():
        rows = {}
        for lang in langs:
            d = load(exp, lang)
            if not d:
                continue
            cats = {"total_miss": 0, "deep_miss": 0, "weak_rank": 0, "rank1": 0}
            for m in d.values():
                cats[categorise(m)] += 1
            n = len(d)
            rows[lang] = {"n": n, "counts": cats,
                          "rates": {k: round(v / n, 4) for k, v in cats.items()}}
        per_system[sys_name] = rows

    # Paired transition analysis: what actually changed per query, BM25 -> E5.
    transitions: dict[str, dict] = {}
    for lang in langs:
        b, e = load(SYSTEMS["bm25"], lang), load(SYSTEMS["E5"], lang)
        if not b or not e:
            continue
        qs = sorted(set(b) & set(e))
        t: dict[str, int] = {}
        rescued = broke = 0
        for q in qs:
            cb, ce = categorise(b[q]), categorise(e[q])
            t[f"{cb}->{ce}"] = t.get(f"{cb}->{ce}", 0) + 1
            if cb in ("total_miss", "deep_miss") and ce in ("weak_rank", "rank1"):
                rescued += 1
            if cb in ("weak_rank", "rank1") and ce in ("total_miss", "deep_miss"):
                broke += 1
        transitions[lang] = {
            "n": len(qs),
            "rescued_by_dense": rescued,
            "broken_by_dense": broke,
            "rescued_rate": round(rescued / len(qs), 4) if qs else None,
            "broken_rate": round(broke / len(qs), 4) if qs else None,
            "net_rate": round((rescued - broke) / len(qs), 4) if qs else None,
            "transitions": dict(sorted(t.items(), key=lambda kv: -kv[1])),
        }

    payload = {
        "experiment_id": "EXP-014",
        "purpose": "failure categorisation and paired BM25->E5 transitions",
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "category_definitions": {
            "total_miss": "Recall@100 == 0 — recall failure, not repairable by reranking",
            "deep_miss": "Recall@100 > 0 and nDCG@10 == 0 — ordering failure, repairable",
            "weak_rank": "nDCG@10 > 0 and MRR@10 < 1 — in top 10, not first",
            "rank1": "MRR@10 == 1",
        },
        "per_system": per_system,
        "bm25_to_E5_transitions": transitions,
    }
    (OUT / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"{'lang':<5}| {'BM25 total/deep':>16} | {'E5 total/deep':>14} | "
          f"{'rescued':>8}{'broken':>8}{'net':>8}")
    print("-" * 70)
    for lang in langs:
        if lang not in transitions:
            continue
        b = per_system["bm25"][lang]["rates"]
        e = per_system["E5"][lang]["rates"]
        t = transitions[lang]
        print(f"{lang:<5}| {b['total_miss']:>7.3f}/{b['deep_miss']:<8.3f} | "
              f"{e['total_miss']:>6.3f}/{e['deep_miss']:<7.3f} | "
              f"{t['rescued_rate']:>8.3f}{t['broken_rate']:>8.3f}{t['net_rate']:>+8.3f}")
    print(f"\nwrote {OUT / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
