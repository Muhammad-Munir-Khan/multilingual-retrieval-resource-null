"""
EXP-005 — Dense retrieval over the pre-registered sub-corpora.

Implements protocol §5: frozen zero-shot encoders, mean pooling, max_len 256,
exact cosine search (not ANN — the sub-corpora are small enough that approximate
search adds error for no benefit at this scale).

Two properties the protocol requires, both learned from measurement rather than
assumed:

* **Length-bucketed batching.** EXP-000 found throughput is set by the longest
  sequence in each batch, not the median (padding), so sorting by length before
  batching is a free speedup. Order is restored before saving.
* **Resumable checkpointing.** A full pass is ~25-30 h per encoder on this host.
  A laptop job of that length will be interrupted; embeddings are flushed in
  shards so an interrupted run resumes instead of restarting.

Usage:
    .venv/Scripts/python.exe scripts/encode_and_search.py --lang yo --model A
"""

from __future__ import annotations

import argparse
import gzip
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
PROC = REPO / "data" / "processed" / "miracl"
EMB = REPO / "data" / "embeddings"
RESULTS = REPO / "results"

# Protocol §5, Amendments 1 and 3. Keys are stable short names used in paths/results.
#
# `query_prefix`/`doc_prefix` are NOT cosmetic. E5 models are trained with
# "query: " / "passage: " markers; omitting them silently degrades E5 and would
# understate it - the same weak-baseline failure ISSUE-001 guarded against.
#
# `declared_languages` is the count from each model card's metadata, and `missing`
# lists which of our 18 the model does NOT declare. Protocol Amendment 3 makes
# coverage a first-class reported covariate: results for a language a model does
# not support measure coverage, not an attributable channel (ISSUE-006).
MODELS = {
    "E5": {
        "name": "intfloat/multilingual-e5-small",
        "query_prefix": "query: ", "doc_prefix": "passage: ",
        "tokenizer_family": "XLM-R-250k", "declared_languages": 94, "missing": ["yo"],
        "task": "retrieval",
    },
    "E5base": {
        "name": "intfloat/multilingual-e5-base",
        "query_prefix": "query: ", "doc_prefix": "passage: ",
        "tokenizer_family": "XLM-R-250k", "declared_languages": 94, "missing": ["yo"],
        "task": "retrieval",
    },
    "BGEM3": {
        "name": "BAAI/bge-m3",
        "query_prefix": "", "doc_prefix": "",
        "tokenizer_family": "XLM-R-250k",
        # ISSUE-010. The model card gives NO structured language list, only the prose
        # phrase "100 working languages". An earlier version of this entry asserted
        # declared_languages=100 and missing=[] on that basis; neither was verified.
        # Its base (XLM-R) declares 94 languages and does NOT list Yoruba, so coverage
        # here is genuinely undetermined and must not be reported either way.
        "declared_languages": "UNVERIFIED (card claims 100, not enumerated)",
        "missing": None,          # None = undetermined, distinct from [] = covers all
        "task": "retrieval",
    },
    "LaBSE": {
        "name": "sentence-transformers/LaBSE",
        "query_prefix": "", "doc_prefix": "",
        "tokenizer_family": "LaBSE-501k", "declared_languages": 110, "missing": [],
        "task": "bitext/similarity",
    },
    "A": {
        "name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "query_prefix": "", "doc_prefix": "",
        "tokenizer_family": "XLM-R-250k", "declared_languages": 50,
        "missing": ["yo", "sw", "te", "bn", "zh"], "task": "paraphrase/STS",
    },
    "B": {
        "name": "sentence-transformers/distiluse-base-multilingual-cased-v2",
        "query_prefix": "", "doc_prefix": "",
        "tokenizer_family": "mBERT-119k", "declared_languages": 50,
        "missing": ["yo", "sw", "te", "bn", "zh"], "task": "paraphrase/STS",
    },
}

MAX_LEN = 256
SHARD = 4096  # checkpoint granularity


def load_corpus(lang: str):
    ids, texts = [], []
    with gzip.open(PROC / lang / "subcorpus.jsonl.gz", "rt", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            ids.append(str(r["docid"]))
            texts.append((r.get("title", "") + " " + r.get("text", "")).strip())
    return ids, texts


def load_eval(lang: str):
    queries = []
    for line in (PROC / lang / "queries.tsv").read_text(encoding="utf-8").strip().split("\n"):
        p = line.split("\t")
        if len(p) >= 2:
            queries.append((p[0], p[1]))
    qrels: dict[str, dict[str, int]] = {}
    for line in (PROC / lang / "qrels.tsv").read_text(encoding="utf-8").strip().split("\n"):
        p = line.split("\t")
        if len(p) >= 4:
            qrels.setdefault(p[0], {})[p[2]] = int(p[3])
    return queries, qrels


class Encoder:
    def __init__(self, model_name: str):
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

    def encode(self, batch: list[str]) -> np.ndarray:
        enc = self.tok(batch, padding=True, truncation=True,
                       max_length=MAX_LEN, return_tensors="pt")
        with self.torch.no_grad():
            out = self.model(**enc).last_hidden_state
        mask = enc["attention_mask"].unsqueeze(-1).float()
        emb = (out * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
        emb = self.torch.nn.functional.normalize(emb, p=2, dim=1)
        return emb.cpu().numpy().astype(np.float32)

    def token_lengths(self, texts: list[str]) -> list[int]:
        return [len(self.tok(t, truncation=True, max_length=MAX_LEN)["input_ids"])
                for t in texts]


def encode_corpus(enc: Encoder, lang: str, key: str, texts: list[str],
                  batch_size: int, doc_prefix: str = "") -> np.ndarray:
    """Encode with length bucketing and shard-level resume."""
    out_dir = EMB / key / lang
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / "corpus.npy"
    if final.exists():
        print(f"[{lang}/{key}] embeddings present, loading", flush=True)
        return np.load(final)

    # Bucket by token length so batches are homogeneous (EXP-000 padding finding).
    lens = enc.token_lengths(texts)
    order = np.argsort(np.array(lens), kind="stable")

    n = len(texts)
    n_shards = (n + SHARD - 1) // SHARD
    t_start = time.perf_counter()
    for s in range(n_shards):
        shard_path = out_dir / f"shard_{s:05d}.npy"
        if shard_path.exists():
            continue
        idx = order[s * SHARD:(s + 1) * SHARD]
        vecs = []
        for i in range(0, len(idx), batch_size):
            vecs.append(enc.encode([doc_prefix + texts[j] for j in idx[i:i + batch_size]]))
        np.save(shard_path, np.vstack(vecs))
        done = (s + 1) * SHARD
        rate = min(done, n) / (time.perf_counter() - t_start)
        eta = (n - min(done, n)) / rate / 60 if rate > 0 else 0
        print(f"[{lang}/{key}] shard {s+1}/{n_shards}  {rate:.1f} p/s  ETA {eta:.0f} min",
              flush=True)

    # Reassemble in bucketed order, then invert the permutation to restore
    # original document order. Getting this wrong silently misaligns every
    # embedding with its docid, so it is asserted below.
    parts = [np.load(out_dir / f"shard_{s:05d}.npy") for s in range(n_shards)]
    shuffled = np.vstack(parts)
    assert shuffled.shape[0] == n, f"expected {n} vectors, got {shuffled.shape[0]}"
    restored = np.empty_like(shuffled)
    restored[order] = shuffled

    np.save(final, restored)
    for s in range(n_shards):
        (out_dir / f"shard_{s:05d}.npy").unlink(missing_ok=True)
    return restored


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True)
    ap.add_argument("--model", default="A", choices=sorted(MODELS))
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--no-prefix", action="store_true",
                    help="ablate the model's query/doc prefixes (EXP-009 control). "
                         "Uses a separate cache and results key so it never "
                         "contaminates the primary run.")
    args = ap.parse_args()

    # Reuse the metric implementation rather than duplicating it: two copies of an
    # nDCG function is how results quietly stop agreeing with each other.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from retrieval_eval import TOPK, evaluate

    lang, key = args.lang, args.model
    cfg = dict(MODELS[key])
    if args.no_prefix:
        if not (cfg["query_prefix"] or cfg["doc_prefix"]):
            print(f"[{lang}/{key}] --no-prefix is a no-op: this model uses no prefixes")
            return 1
        cfg["query_prefix"] = cfg["doc_prefix"] = ""
        key = f"{key}-noprefix"
    model_name = cfg["name"]
    # missing == None means coverage is undetermined (ISSUE-010), which is NOT the
    # same as "covers everything". Treat it as unknown and say so.
    miss = cfg.get("missing")
    supported = None if miss is None else (lang not in miss)
    if supported is False:
        print(f"[{lang}/{key}] NOTE: {model_name} does not declare support for "
              f"'{lang}'. Result measures COVERAGE, not an attributable channel "
              f"(ISSUE-006). Recording it flagged.", flush=True)

    if not (PROC / lang / "subcorpus.jsonl.gz").exists():
        print(f"[{lang}] not built — run build_subcorpora.py first")
        return 1

    ids, texts = load_corpus(lang)
    queries, qrels = load_eval(lang)
    print(f"[{lang}/{key}] {len(ids)} docs, {len(queries)} queries, model={model_name}",
          flush=True)

    enc = Encoder(model_name)
    t0 = time.perf_counter()
    doc_emb = encode_corpus(enc, lang, key, texts, args.batch_size, cfg["doc_prefix"])
    encode_s = time.perf_counter() - t0

    q_emb = np.vstack([enc.encode([cfg["query_prefix"] + q[1]]) for q in queries])

    # Exact cosine search. Vectors are L2-normalised, so a dot product is cosine.
    t0 = time.perf_counter()
    sims = q_emb @ doc_emb.T
    top_idx = np.argpartition(-sims, kth=min(TOPK, sims.shape[1] - 1), axis=1)[:, :TOPK]
    rows = np.arange(sims.shape[0])[:, None]
    top_idx = top_idx[rows, np.argsort(-sims[rows, top_idx], axis=1)]
    search_s = time.perf_counter() - t0

    per_query = {}
    for qi, (qid, _) in enumerate(queries):
        ranked = [ids[j] for j in top_idx[qi]]
        per_query[qid] = evaluate(ranked, qrels.get(qid, {}))

    n = len(per_query)
    agg = {m: round(sum(v[m] for v in per_query.values()) / n, 4)
           for m in ("ndcg@10", "recall@100", "mrr@10")}
    agg["mean_unjudged_in_top10"] = round(
        sum(v["unjudged_in_top10"] for v in per_query.values()) / n, 3)
    agg["mean_unjudged_in_top100"] = round(
        sum(v["unjudged_in_top100"] for v in per_query.values()) / n, 2)

    exp = f"EXP-005-dense-{key}"
    out_dir = RESULTS / exp
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"per_query_{lang}.json").write_text(
        json.dumps(per_query, indent=1), encoding="utf-8")

    agg_path = out_dir / "metrics.json"
    prev = {}
    if agg_path.exists():
        prev = json.loads(agg_path.read_text(encoding="utf-8")).get("languages", {})
    prev[lang] = {
        "lang": lang, "model_key": key, "model": model_name,
        "declares_language_support": ("UNDETERMINED" if supported is None else supported),
        "coverage_confounded": ("UNDETERMINED" if supported is None else (not supported)),
        "declared_languages": cfg["declared_languages"],
        "tokenizer_family": cfg["tokenizer_family"],
        "model_task": cfg["task"],
        "query_prefix": cfg["query_prefix"], "doc_prefix": cfg["doc_prefix"],
        "n_queries": n, "n_docs": len(ids), "embedding_dim": int(doc_emb.shape[1]),
        "max_len": MAX_LEN, "batch_size": args.batch_size,
        "aggregate": agg,
        "timing": {"encode_s": round(encode_s, 1), "search_s": round(search_s, 2)},
    }
    agg_path.write_text(json.dumps({
        "experiment_id": exp,
        "model": model_name,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "languages": prev,
    }, indent=2), encoding="utf-8")

    print(f"[{lang}/{key}] nDCG@10={agg['ndcg@10']} R@100={agg['recall@100']} "
          f"MRR@10={agg['mrr@10']}  encode={encode_s/60:.1f} min"
          + ("" if supported is True else
             "  [COVERAGE UNDETERMINED - ISSUE-010]" if supported is None else
             "  [COVERAGE-CONFOUNDED]"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
