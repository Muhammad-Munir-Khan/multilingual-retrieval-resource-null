"""
Retrieval + evaluation over the pre-registered sub-corpora.

Implements the metrics fixed in docs/experiment_protocol.md section 6:
  nDCG@10 (primary), Recall@100, MRR@10.

Per-query scores are always written, because the pre-registered statistical plan
(section 7) requires a paired bootstrap over queries and cannot run on aggregates.

BM25 uses **character 4-grams** as its primary tokenisation (protocol Amendment 2),
applied uniformly to every language. Word tokenisation is retained as a robustness
check via --tok word, but it collapses on unsegmented scripts (th, zh, ja) for a
purely orthographic reason, which would contaminate the language-intrinsic difficulty
reference this system exists to provide.

Usage:
    .venv/Scripts/python.exe scripts/retrieval_eval.py --langs yo sw          # char (primary)
    .venv/Scripts/python.exe scripts/retrieval_eval.py --langs yo sw --tok word  # robustness
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import subprocess
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROC = REPO / "data" / "processed" / "miracl"
RESULTS = REPO / "results"

# Scripts without whitespace word boundaries: BM25 whitespace tokenisation is not
# defensible here. Flagged, not silently included.
UNSEGMENTED = {"zh", "ja", "th"}

K_NDCG = 10
K_RECALL = 100
K_MRR = 10
TOPK = 100


def load_lang(lang: str):
    d = PROC / lang
    docs = []
    with gzip.open(d / "subcorpus.jsonl.gz", "rt", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            docs.append((str(r["docid"]), (r.get("title", "") + " " + r.get("text", "")).strip()))

    queries = []
    for line in (d / "queries.tsv").read_text(encoding="utf-8").strip().split("\n"):
        p = line.split("\t")
        if len(p) >= 2:
            queries.append((p[0], p[1]))

    qrels: dict[str, dict[str, int]] = {}
    for line in (d / "qrels.tsv").read_text(encoding="utf-8").strip().split("\n"):
        p = line.split("\t")
        if len(p) >= 4:
            qrels.setdefault(p[0], {})[p[2]] = int(p[3])
    return docs, queries, qrels


CHAR_NGRAM_N = 4  # protocol Amendment 2; standard CLIR default, not tuned per language


def normalise(s: str) -> str:
    """Uniform, language-agnostic normalisation.

    Applied identically to every language *by design*. Per-language analyzers were
    rejected because analyzer quality is itself resource-correlated (mature stemmers
    exist for English and Chinese, not for Yoruba or Telugu), which would inject the
    very confound this study measures into its own reference system. See
    docs/open_issues.md ISSUE-001.

    Punctuation is stripped by **Unicode category**, not by the `\\w` class.
    `[^\\w\\s]` looks equivalent but is not: Python's `\\w` excludes combining marks
    (categories Mn/Mc), so it deletes Indic and Thai vowel signs and shatters those
    scripts into fragments. That bug is ISSUE-004. Categories P* (punctuation) and
    S* (symbols) are removed; L* (letters), N* (numbers) and M* (marks) are kept.
    """
    s = unicodedata.normalize("NFKC", s).casefold()
    return "".join(" " if unicodedata.category(c)[0] in ("P", "S") else c for c in s)


def tokenise_word(s: str) -> list[str]:
    """Whitespace tokenisation. Robustness check only — fails on unsegmented scripts."""
    return normalise(s).split()


def tokenise_char(s: str, n: int = CHAR_NGRAM_N) -> list[str]:
    """Character n-grams within whitespace-delimited units. **Primary tokenisation.**

    Adopted in protocol Amendment 2 because it is *script-agnostic*: Thai and Chinese
    have no word spaces, so whitespace tokenisation does not fail on them for any
    linguistic reason — it fails for a purely orthographic one, which would contaminate
    the language-intrinsic difficulty reference this system is supposed to provide.

    Still uniform across languages, so it does not reintroduce the resource-correlation
    problem that ruled out per-language analyzers.
    """
    out: list[str] = []
    for w in normalise(s).split():
        if len(w) <= n:
            out.append(w)
        else:
            out.extend(w[i:i + n] for i in range(len(w) - n + 1))
    return out


TOKENISERS = {"char": tokenise_char, "word": tokenise_word}


def dcg(gains: list[int]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def evaluate(ranked_ids: list[str], rel: dict[str, int]) -> dict:
    """Metrics for one query. `rel` maps docid -> graded relevance."""
    positives = {d for d, r in rel.items() if r > 0}

    gains = [rel.get(d, 0) for d in ranked_ids[:K_NDCG]]
    ideal = sorted((r for r in rel.values() if r > 0), reverse=True)[:K_NDCG]
    idcg = dcg(ideal)
    ndcg = (dcg(gains) / idcg) if idcg > 0 else 0.0

    top_r = ranked_ids[:K_RECALL]
    recall = (len(positives & set(top_r)) / len(positives)) if positives else 0.0

    mrr = 0.0
    for i, d in enumerate(ranked_ids[:K_MRR], start=1):
        if rel.get(d, 0) > 0:
            mrr = 1.0 / i
            break

    # ISSUE-007 exposure. MIRACL judgments come from pooling particular systems;
    # ours did not contribute. A document we surface that no pooled system
    # retrieved is scored non-relevant by default, so nDCG is a lower bound and
    # the deflation is larger for systems that diverge more from the pool.
    # Counting unjudged retrievals makes that exposure measurable per system and
    # language instead of a hypothetical caveat.
    unjudged_10 = sum(1 for d in ranked_ids[:K_NDCG] if d not in rel)
    unjudged_100 = sum(1 for d in ranked_ids[:K_RECALL] if d not in rel)

    return {"ndcg@10": ndcg, "recall@100": recall, "mrr@10": mrr,
            "n_positives": len(positives),
            "unjudged_in_top10": unjudged_10,
            "unjudged_in_top100": unjudged_100}


def run_bm25(docs, queries, tok_name: str, ngram: int = CHAR_NGRAM_N):
    from rank_bm25 import BM25Okapi

    tk = (lambda s: tokenise_char(s, ngram)) if tok_name == "char" else TOKENISERS[tok_name]
    doc_ids = [d for d, _ in docs]
    t0 = time.perf_counter()
    bm25 = BM25Okapi([tk(t) for _, t in docs])
    index_s = time.perf_counter() - t0

    runs = {}
    t0 = time.perf_counter()
    for qid, qtext in queries:
        scores = bm25.get_scores(tk(qtext))
        top = sorted(range(len(scores)), key=lambda i: -scores[i])[:TOPK]
        runs[qid] = [doc_ids[i] for i in top]
    search_s = time.perf_counter() - t0
    return runs, {"index_s": round(index_s, 2), "search_s": round(search_s, 2)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", default="bm25", choices=["bm25"])
    ap.add_argument("--tok", default="char", choices=["char", "word"],
                    help="char = primary (protocol Amendment 2); word = robustness check")
    ap.add_argument("--ngram", type=int, default=CHAR_NGRAM_N,
                    help="character n-gram size. n=4 is the pre-registered primary; other "
                         "values are the sensitivity check required by Amendment 2 and are "
                         "NOT used to select a better-performing n.")
    ap.add_argument("--langs", nargs="+", required=True)
    args = ap.parse_args()

    exp = f"EXP-004-bm25-{args.tok}"
    if args.tok == "char" and args.ngram != CHAR_NGRAM_N:
        exp = f"EXP-013-bm25-char-n{args.ngram}"   # sensitivity, kept separate from primary
    out_dir = RESULTS / exp
    out_dir.mkdir(parents=True, exist_ok=True)

    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    all_lang = {}

    for lang in args.langs:
        if not (PROC / lang / "subcorpus.jsonl.gz").exists():
            print(f"[{lang}] not built, skipping", flush=True)
            continue
        docs, queries, qrels = load_lang(lang)
        runs, timing = run_bm25(docs, queries, args.tok, args.ngram)

        per_query = {}
        for qid, _ in queries:
            per_query[qid] = evaluate(runs.get(qid, []), qrels.get(qid, {}))

        n = len(per_query)
        agg = {m: round(sum(v[m] for v in per_query.values()) / n, 4)
               for m in ("ndcg@10", "recall@100", "mrr@10")} if n else {}
        if n:
            agg["mean_unjudged_in_top10"] = round(
                sum(v["unjudged_in_top10"] for v in per_query.values()) / n, 3)
            agg["mean_unjudged_in_top100"] = round(
                sum(v["unjudged_in_top100"] for v in per_query.values()) / n, 2)

        rec = {
            "lang": lang,
            "system": args.system,
            "tokenisation": args.tok,
            "char_ngram_n": args.ngram if args.tok == "char" else None,
            "n_queries": n,
            "n_docs": len(docs),
            "aggregate": agg,
            "timing": timing,
            "unsegmented_script": lang in UNSEGMENTED,
            "flag": ("word tokenisation is not defensible for this script; char n-grams "
                     "are the primary tokenisation (Amendment 2)")
                    if (lang in UNSEGMENTED and args.tok == "word") else None,
        }
        all_lang[lang] = rec
        (out_dir / f"per_query_{lang}.json").write_text(
            json.dumps(per_query, indent=1), encoding="utf-8")

        flag = ("  [FLAGGED: unsegmented script + word tok]"
                if (lang in UNSEGMENTED and args.tok == "word") else "")
        print(f"[{lang}] nDCG@10={agg.get('ndcg@10')} R@100={agg.get('recall@100')} "
              f"MRR@10={agg.get('mrr@10')} (n={n}){flag}", flush=True)

    agg_path = out_dir / "metrics.json"
    prev = {}
    if agg_path.exists():
        prev = json.loads(agg_path.read_text(encoding="utf-8")).get("languages", {})
    prev.update(all_lang)
    agg_path.write_text(json.dumps({
        "experiment_id": exp,
        "system": args.system,
        "tokenisation": args.tok,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit,
        "metrics_definition": {"ndcg": f"@{K_NDCG}", "recall": f"@{K_RECALL}",
                               "mrr": f"@{K_MRR}", "topk_retrieved": TOPK},
        "languages": prev,
    }, indent=2), encoding="utf-8")
    print(f"\nwrote {agg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
