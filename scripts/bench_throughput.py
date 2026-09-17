"""
EXP-000 — CPU throughput benchmark.

Purpose: establish the *measured* compute budget for this host so that the
experimental scale (how many languages, how many passages) is derived from
evidence rather than assumed. Fills the `EVIDENCE REQUIRED` rows in
docs/environment_audit.md section 5.

This does not test any research hypothesis. It measures the instrument.

Usage:
    .venv/Scripts/python.exe scripts/bench_throughput.py [--quick]

Writes: results/EXP-000-throughput/metrics.json  (+ raw.log via shell redirect)
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "results" / "EXP-000-throughput"

# Passage length chosen to approximate MIRACL-style Wikipedia passages.
# Not tuned to flatter throughput; see NOTE in the report.
SYNTH_WORDS = 90


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "UNKNOWN"


def env_metadata() -> dict:
    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
        "machine": platform.machine(),
    }
    try:
        import os

        meta["cpu_count_logical"] = os.cpu_count()
    except Exception:
        meta["cpu_count_logical"] = None
    for pkg in ("torch", "transformers", "sentence_transformers", "datasets", "rank_bm25"):
        try:
            mod = __import__(pkg)
            meta[f"{pkg}_version"] = getattr(mod, "__version__", "unknown")
        except Exception:
            meta[f"{pkg}_version"] = "NOT_INSTALLED"
    try:
        import torch

        meta["torch_threads"] = torch.get_num_threads()
        meta["cuda_available"] = torch.cuda.is_available()
    except Exception:
        meta["torch_threads"] = None
        meta["cuda_available"] = None
    return meta


def make_passages(n: int, seed: int = 13) -> list[str]:
    """Deterministic pseudo-passages. Synthetic text is adequate here because we
    are measuring *throughput*, which depends on token count, not semantics."""
    import random

    rng = random.Random(seed)
    vocab = [f"tok{i}" for i in range(4000)]
    return [" ".join(rng.choice(vocab) for _ in range(SYNTH_WORDS)) for _ in range(n)]


def bench_bm25(passages: list[str]) -> dict:
    from rank_bm25 import BM25Okapi

    tokenized = [p.split() for p in passages]

    t0 = time.perf_counter()
    bm25 = BM25Okapi(tokenized)
    build_s = time.perf_counter() - t0

    queries = [" ".join(p.split()[:8]) for p in passages[:50]]
    t0 = time.perf_counter()
    for q in queries:
        bm25.get_scores(q.split())
    query_s = time.perf_counter() - t0

    return {
        "n_passages": len(passages),
        "index_build_s": round(build_s, 3),
        "passages_per_s_index": round(len(passages) / build_s, 1) if build_s > 0 else None,
        "n_queries": len(queries),
        "total_query_s": round(query_s, 3),
        "queries_per_s": round(len(queries) / query_s, 2) if query_s > 0 else None,
        "ms_per_query": round(1000 * query_s / len(queries), 2) if queries else None,
    }


def bench_encoder(model_name: str, passages: list[str], batch_size: int,
                  max_len: int = 256) -> dict:
    """Measure encode throughput with plain transformers + mean pooling.

    Deliberately avoids sentence-transformers: it is a convenience wrapper whose
    dependency pins conflict with the torch build that works on this host, and
    mean pooling is a few lines. Fewer dependencies, and the pooling is explicit
    rather than hidden behind a config file.
    """
    import torch
    from transformers import AutoModel, AutoTokenizer

    t0 = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()
    load_s = time.perf_counter() - t0

    def encode(batch: list[str]) -> "torch.Tensor":
        enc = tok(batch, padding=True, truncation=True,
                  max_length=max_len, return_tensors="pt")
        with torch.no_grad():
            out = model(**enc).last_hidden_state
        mask = enc["attention_mask"].unsqueeze(-1).float()
        return (out * mask).sum(1) / mask.sum(1).clamp(min=1e-9)

    chunk = passages[: min(len(passages), 256)]

    # Warm-up, excluded from the reported rate: the first pass pays lazy init.
    encode(chunk[:batch_size])

    timings = []
    for _ in range(3):
        t0 = time.perf_counter()
        for i in range(0, len(chunk), batch_size):
            encode(chunk[i:i + batch_size])
        timings.append(time.perf_counter() - t0)

    best, median = min(timings), statistics.median(timings)
    dim = getattr(model.config, "hidden_size", None)
    n_params = sum(p.numel() for p in model.parameters())

    return {
        "model": model_name,
        "embedding_dim": dim,
        "n_params_millions": round(n_params / 1e6, 1),
        "max_seq_len_used": max_len,
        "load_s": round(load_s, 2),
        "batch_size": batch_size,
        "n_encoded_per_rep": len(chunk),
        "reps": len(timings),
        "median_s": round(median, 3),
        "best_s": round(best, 3),
        "passages_per_s_median": round(len(chunk) / median, 2) if median > 0 else None,
        "passages_per_s_best": round(len(chunk) / best, 2) if best > 0 else None,
    }


def project(rate_per_s: float | None, corpus_sizes: dict[str, int]) -> dict:
    """Project wall-clock encoding time for candidate corpora.

    PROJECTION ONLY - not a measurement. Labelled as such in the artifact so it
    can never be mistaken for an experimental result.
    """
    if not rate_per_s:
        return {"note": "no rate measured"}
    out = {}
    for lang, n in corpus_sizes.items():
        hours = n / rate_per_s / 3600
        out[lang] = {"corpus_passages": n, "projected_hours": round(hours, 2)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="smaller synthetic set")
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument(
        "--models",
        nargs="*",
        default=["sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"],
    )
    args = ap.parse_args()

    n = 300 if args.quick else args.n
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    report: dict = {
        "experiment_id": "EXP-000",
        "purpose": "measure CPU throughput to fix feasible experiment scale",
        "hypothesis_tested": None,
        "environment": env_metadata(),
        "config": {"n_passages": n, "synth_words_per_passage": SYNTH_WORDS,
                   "batch_size": args.batch_size, "models": args.models},
    }

    print(f"[EXP-000] generating {n} synthetic passages ...", flush=True)
    passages = make_passages(n)

    print("[EXP-000] BM25 ...", flush=True)
    try:
        report["bm25"] = bench_bm25(passages)
        print(f"  BM25: {report['bm25']}", flush=True)
    except Exception as e:
        report["bm25"] = {"error": repr(e)}
        print(f"  BM25 FAILED: {e}", flush=True)

    report["encoders"] = []
    for mname in args.models:
        print(f"[EXP-000] encoder {mname} (downloads on first run) ...", flush=True)
        try:
            r = bench_encoder(mname, passages, args.batch_size)
            report["encoders"].append(r)
            print(f"  {r['passages_per_s_median']} passages/s (median)", flush=True)
        except Exception as e:
            report["encoders"].append({"model": mname, "error": repr(e)})
            print(f"  ENCODER FAILED: {e}", flush=True)

    # MIRACL corpus sizes are UNVERIFIED placeholders until read from the dataset
    # itself. Marked explicitly so no downstream doc treats them as fact.
    report["projection_note"] = (
        "PROJECTION ONLY, not measured. Corpus sizes below are UNVERIFIED "
        "and must be replaced with counts read from the actual MIRACL corpora."
    )
    ok = [e for e in report["encoders"] if "passages_per_s_median" in e]
    if ok:
        rate = ok[0]["passages_per_s_median"]
        report["projected_encoding_time"] = project(
            rate,
            {
                "yo_UNVERIFIED": 49_000,
                "sw_UNVERIFIED": 132_000,
                "bn_UNVERIFIED": 297_000,
                "te_UNVERIFIED": 518_000,
            },
        )

    out = OUT_DIR / "metrics.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n[EXP-000] wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
