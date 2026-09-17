"""
EXP-002 — Survey MIRACL per-language evaluation-set size and download volume.

Purpose: fix the language set on evidence BEFORE the protocol is pre-registered.
EXP-000/001 established that compute is not the binding limit once corpora are
subsampled to equal size; the binding limits are (a) number of dev queries, which
sets statistical power, and (b) corpus download volume.

Downloads only small TSVs (topics/qrels). Corpus byte sizes come from the HF API,
so nothing large is fetched here.

Usage:
    .venv/Scripts/python.exe scripts/survey_miracl.py

Writes: results/EXP-002-miracl-survey/metrics.json
"""

from __future__ import annotations

import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "results" / "EXP-002-miracl-survey"
RAW_DIR = REPO / "data" / "raw" / "miracl"

HF = "https://huggingface.co"
API = f"{HF}/api/datasets"
CORPUS = "miracl/miracl-corpus"
MAIN = "miracl/miracl"

# All 18 MIRACL languages.
LANGS = ["yo", "sw", "bn", "hi", "te", "th", "id", "ko", "fi",
         "ar", "fa", "zh", "ja", "ru", "es", "en", "de", "fr"]

ENCODE_RATE = 9.62  # passages/s, measured on real MIRACL text (EXP-000 re-measure)


def get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "research-survey"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_json(url: str):
    return json.loads(get(url).decode("utf-8"))


def corpus_bytes(lang: str) -> tuple[int, int]:
    """(total_compressed_bytes, n_shards) for a language corpus."""
    try:
        tree = get_json(f"{API}/{CORPUS}/tree/main/miracl-corpus-v1.0-{lang}")
    except Exception:
        return -1, -1
    files = [f for f in tree if f.get("type") == "file"]
    return sum(f.get("size") or 0 for f in files), len(files)


def fetch_tsv(url: str, dest: Path) -> str | None:
    try:
        data = get(url, timeout=90)
    except Exception:
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return data.decode("utf-8", errors="replace")


def survey_lang(lang: str) -> dict:
    rec: dict = {"lang": lang}

    nbytes, shards = corpus_bytes(lang)
    rec["corpus_compressed_bytes"] = nbytes
    rec["corpus_shards"] = shards
    rec["corpus_gb"] = round(nbytes / 1e9, 2) if nbytes > 0 else None

    topics = fetch_tsv(
        f"{HF}/datasets/{MAIN}/resolve/main/miracl-v1.0-{lang}/topics/topics.miracl-v1.0-{lang}-dev.tsv",
        RAW_DIR / lang / "topics.dev.tsv",
    )
    qrels = fetch_tsv(
        f"{HF}/datasets/{MAIN}/resolve/main/miracl-v1.0-{lang}/qrels/qrels.miracl-v1.0-{lang}-dev.tsv",
        RAW_DIR / lang / "qrels.dev.tsv",
    )

    if topics:
        lines = [l for l in topics.strip().split("\n") if l.strip()]
        rec["dev_queries"] = len(lines)
    else:
        rec["dev_queries"] = None

    if qrels:
        rows = [l.split("\t") for l in qrels.strip().split("\n") if l.strip()]
        pos = [r for r in rows if r[-1].strip() not in ("0", "")]
        rec["qrels_lines"] = len(rows)
        rec["positive_judgments"] = len(pos)
        if rec["dev_queries"]:
            rec["judged_per_query"] = round(len(rows) / rec["dev_queries"], 2)
            rec["positives_per_query"] = round(len(pos) / rec["dev_queries"], 2)
    else:
        rec["qrels_lines"] = rec["positive_judgments"] = None

    return rec


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    print(f"{'lang':<5}{'dev_q':>7}{'pos':>7}{'pos/q':>7}{'corpus_GB':>11}{'shards':>8}")
    print("-" * 45)
    for lang in LANGS:
        r = survey_lang(lang)
        records.append(r)
        print(f"{lang:<5}{str(r['dev_queries'] or '-'):>7}"
              f"{str(r['positive_judgments'] or '-'):>7}"
              f"{str(r.get('positives_per_query') or '-'):>7}"
              f"{str(r['corpus_gb'] if r['corpus_gb'] is not None else '-'):>11}"
              f"{str(r['corpus_shards'] if r['corpus_shards'] > 0 else '-'):>8}", flush=True)

    ok = [r for r in records if r["dev_queries"]]
    out = {
        "experiment_id": "EXP-002",
        "purpose": "fix language set on evidence before pre-registering the protocol",
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "encode_rate_passages_per_s": ENCODE_RATE,
        "languages": records,
        "summary": {
            "n_languages_with_dev": len(ok),
            "min_dev_queries": min(r["dev_queries"] for r in ok) if ok else None,
            "max_dev_queries": max(r["dev_queries"] for r in ok) if ok else None,
            "total_corpus_gb": round(
                sum(r["corpus_compressed_bytes"] for r in records
                    if r["corpus_compressed_bytes"] > 0) / 1e9, 2),
        },
    }
    (OUT_DIR / "metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("\nsummary:", json.dumps(out["summary"], indent=2))
    print(f"wrote {OUT_DIR / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
