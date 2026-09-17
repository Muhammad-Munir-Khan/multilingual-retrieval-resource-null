"""
EXP-003 — Build equal-size MIRACL sub-corpora per the pre-registered protocol.

Implements docs/experiment_protocol.md sections 3 and 4:
  - Q_max = 300 dev queries per language, sampled without replacement, seed 20260811
  - N = 49,043 passages per language
  - sub-corpus = all judged docs for sampled queries, plus a uniform random fill
  - document-ID list hashed and recorded so the sample is verifiable

Streams each corpus shard from the Hugging Face CDN and never holds a full corpus
in memory: judged documents are kept unconditionally, everything else goes through
reservoir sampling. Resumable - a language whose manifest already exists is skipped.

Usage:
    .venv/Scripts/python.exe scripts/build_subcorpora.py --langs yo sw
    .venv/Scripts/python.exe scripts/build_subcorpora.py --all
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import random
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "miracl"
PROC = REPO / "data" / "processed" / "miracl"
OUT_DIR = REPO / "results" / "EXP-003-subcorpora"

HF = "https://huggingface.co"
API = f"{HF}/api/datasets"
CORPUS = "miracl/miracl-corpus"

# Pre-registered constants. Changing these requires a dated protocol amendment.
SEED = 20260811
Q_MAX = 300
N_PASSAGES = 49_043

LANGS = ["yo", "sw", "bn", "hi", "te", "th", "id", "ko", "fi",
         "ar", "fa", "zh", "ja", "ru", "es", "en", "de", "fr"]


def get(url: str, timeout: int = 120, retries: int = 4) -> bytes:
    """Fetch with retries. A truncated shard download killed the Spanish build
    (IncompleteRead, 52.6 MB of 83.3 MB), so transient network failures must not
    cost a whole language on a 16 GB job."""
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "research-build"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            expected = r.headers.get("Content-Length")
            if expected and len(data) != int(expected):
                raise IOError(f"short read: {len(data)} of {expected}")
            return data
        except Exception as e:  # noqa: BLE001 - retry any transport failure
            last = e
            if attempt < retries - 1:
                wait = 3 * (attempt + 1)
                print(f"    retry {attempt+1}/{retries-1} after {e!r}; waiting {wait}s",
                      flush=True)
                time.sleep(wait)
    raise IOError(f"failed after {retries} attempts: {last!r}")


def shard_urls(lang: str) -> list[str]:
    tree = json.loads(get(f"{API}/{CORPUS}/tree/main/miracl-corpus-v1.0-{lang}").decode())
    files = sorted(f["path"] for f in tree if f.get("type") == "file"
                   and f["path"].endswith(".jsonl.gz"))
    return [f"{HF}/datasets/{CORPUS}/resolve/main/{p}" for p in files]


def load_eval(lang: str) -> tuple[list[tuple[str, str]], dict[str, dict[str, int]]]:
    """Return (sampled_queries, qrels_for_sampled). Queries capped at Q_MAX."""
    tpath = RAW / lang / "topics.dev.tsv"
    qpath = RAW / lang / "qrels.dev.tsv"
    if not tpath.exists() or not qpath.exists():
        raise FileNotFoundError(f"{lang}: run scripts/survey_miracl.py first")

    topics = []
    for line in tpath.read_text(encoding="utf-8").strip().split("\n"):
        parts = line.split("\t")
        if len(parts) >= 2:
            topics.append((parts[0].strip(), parts[1].strip()))

    # Deterministic query sample. Sorted first so the sample does not depend on
    # file ordering.
    topics.sort(key=lambda x: x[0])
    rng = random.Random(SEED)
    if len(topics) > Q_MAX:
        topics = sorted(rng.sample(topics, Q_MAX), key=lambda x: x[0])
    qids = {q for q, _ in topics}

    qrels: dict[str, dict[str, int]] = {}
    for line in qpath.read_text(encoding="utf-8").strip().split("\n"):
        p = line.split("\t")
        if len(p) < 4:
            continue
        qid, docid, rel = p[0].strip(), p[2].strip(), p[3].strip()
        if qid in qids:
            try:
                qrels.setdefault(qid, {})[docid] = int(rel)
            except ValueError:
                continue
    return topics, qrels


def build(lang: str, force: bool = False) -> dict:
    out_lang = PROC / lang
    manifest_path = out_lang / "manifest.json"
    if manifest_path.exists() and not force:
        print(f"[{lang}] already built, skipping", flush=True)
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    topics, qrels = load_eval(lang)
    judged = {d for m in qrels.values() for d in m}
    print(f"[{lang}] {len(topics)} queries, {len(judged)} judged docs", flush=True)

    rng = random.Random(SEED)
    kept: dict[str, dict] = {}          # judged docs, always retained
    reservoir: list[dict] = []          # random fill
    n_seen = 0                          # non-judged docs streamed
    total_docs = 0

    urls = shard_urls(lang)
    budget = N_PASSAGES - len(judged)
    if budget < 0:
        raise RuntimeError(f"{lang}: judged docs ({len(judged)}) exceed N={N_PASSAGES}")

    for i, url in enumerate(urls, 1):
        print(f"[{lang}] shard {i}/{len(urls)}", flush=True)
        blob = get(url, timeout=600)
        with gzip.open(io.BytesIO(blob), "rt", encoding="utf-8") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                total_docs += 1
                did = d.get("docid")
                rec = {"docid": did, "title": d.get("title", ""), "text": d.get("text", "")}
                if did in judged:
                    kept[did] = rec
                    continue
                # Reservoir sampling over the non-judged stream.
                n_seen += 1
                if len(reservoir) < budget:
                    reservoir.append(rec)
                else:
                    j = rng.randrange(n_seen)
                    if j < budget:
                        reservoir[j] = rec

    missing = sorted(judged - set(kept))
    sub = list(kept.values()) + reservoir
    sub.sort(key=lambda r: str(r["docid"]))

    out_lang.mkdir(parents=True, exist_ok=True)
    with gzip.open(out_lang / "subcorpus.jsonl.gz", "wt", encoding="utf-8") as fh:
        for r in sub:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    ids = [str(r["docid"]) for r in sub]
    id_hash = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()

    with open(out_lang / "queries.tsv", "w", encoding="utf-8") as fh:
        for qid, text in topics:
            fh.write(f"{qid}\t{text}\n")
    with open(out_lang / "qrels.tsv", "w", encoding="utf-8") as fh:
        for qid, m in sorted(qrels.items()):
            for did, rel in sorted(m.items()):
                fh.write(f"{qid}\t0\t{did}\t{rel}\n")

    manifest = {
        "lang": lang,
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "seed": SEED,
        "q_max": Q_MAX,
        "n_target": N_PASSAGES,
        "n_actual": len(sub),
        "n_queries": len(topics),
        "n_judged_docs_expected": len(judged),
        "n_judged_docs_found": len(kept),
        "n_judged_docs_missing": len(missing),
        "missing_judged_sample": missing[:20],
        "judged_fraction": round(len(kept) / len(sub), 4) if sub else None,
        "corpus_total_docs_streamed": total_docs,
        "corpus_shards": len(urls),
        "docid_sha256": id_hash,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[{lang}] n={len(sub)} judged_frac={manifest['judged_fraction']} "
          f"missing={len(missing)} sha={id_hash[:12]}", flush=True)
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", nargs="*", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    langs = LANGS if args.all else (args.langs or ["yo"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifests = []
    for lang in langs:
        try:
            manifests.append(build(lang, force=args.force))
        except Exception as e:
            print(f"[{lang}] FAILED: {e!r}", file=sys.stderr, flush=True)
            manifests.append({"lang": lang, "error": repr(e)})

    agg_path = OUT_DIR / "metrics.json"
    prev = []
    if agg_path.exists():
        prev = json.loads(agg_path.read_text(encoding="utf-8")).get("languages", [])
    by_lang = {m["lang"]: m for m in prev}
    by_lang.update({m["lang"]: m for m in manifests})
    agg_path.write_text(json.dumps({
        "experiment_id": "EXP-003",
        "purpose": "equal-size sub-corpora per pre-registered protocol s3-s4",
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "languages": sorted(by_lang.values(), key=lambda m: m["lang"]),
    }, indent=2), encoding="utf-8")
    print(f"\nwrote {agg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
