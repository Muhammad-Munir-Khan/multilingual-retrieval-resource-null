"""
EXP-011 — Tokenizer fertility and STRR per language per tokenizer family.

Supplies the predictors for H0b/H1b (protocol §8), which until now had no computed
evidence at all.

Two measures, because one of them breaks on a third of our languages:

* **fertility (tokens per whitespace word)** — the standard definition, but it is
  meaningless for zh/ja/th, which have no whitespace word boundaries. A "word" in
  those languages is an entire clause, so fertility is inflated by orthography
  rather than by tokenization quality. Reported, and flagged.
* **tokens per character** — well defined for every script, so it is the measure
  that can actually be compared across all 18 languages.

Using the whitespace-word measure across unsegmented scripts would repeat exactly
the mistake ISSUE-005 caught in BM25: letting an orthographic convention
masquerade as a linguistic property.

Sampling is deterministic (seed 20260811) and 2,000 documents per language, which
is ample for a ratio statistic and keeps this cheap enough to run beside the
encoder sweep.
"""

from __future__ import annotations

import gzip
import json
import random
import subprocess
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROC = REPO / "data" / "processed" / "miracl"
OUT = REPO / "results" / "EXP-011-fertility"

SEED = 20260811
N_DOCS = 2000

LANGS = ["yo", "sw", "bn", "hi", "te", "th", "id", "ko", "fi",
         "ar", "fa", "zh", "ja", "ru", "es", "en", "de", "fr"]

# No whitespace word boundaries: the per-word measure is not interpretable here.
UNSEGMENTED = {"zh", "ja", "th"}

TOKENIZERS = {
    "XLM-R-250k": "intfloat/multilingual-e5-small",
    "mBERT-119k": "bert-base-multilingual-cased",
    "LaBSE-501k": "sentence-transformers/LaBSE",
}


def sample_docs(lang: str, n: int = N_DOCS) -> list[str]:
    texts = []
    with gzip.open(PROC / lang / "subcorpus.jsonl.gz", "rt", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            t = (r.get("title", "") + " " + r.get("text", "")).strip()
            if t:
                texts.append(t)
    rng = random.Random(SEED)
    return rng.sample(texts, min(n, len(texts)))


def measure(tok, texts: list[str]) -> dict:
    n_words = n_tokens = n_single = n_chars = 0
    for t in texts:
        # Normalise the same way retrieval does, so the measures describe the
        # text the systems actually see.
        s = unicodedata.normalize("NFKC", t)
        words = s.split()
        n_words += len(words)
        n_chars += sum(len(w) for w in words)
        for w in words:
            k = len(tok.tokenize(w))
            n_tokens += k
            if k == 1:
                n_single += 1
    return {
        "n_words": n_words,
        "n_chars": n_chars,
        "n_subword_tokens": n_tokens,
        "fertility_tokens_per_word": round(n_tokens / n_words, 4) if n_words else None,
        "strr_single_token_rate": round(n_single / n_words, 4) if n_words else None,
        "tokens_per_char": round(n_tokens / n_chars, 4) if n_chars else None,
    }


def main() -> int:
    from transformers import AutoTokenizer

    OUT.mkdir(parents=True, exist_ok=True)
    toks = {}
    for fam, name in TOKENIZERS.items():
        print(f"loading {fam} ({name})", flush=True)
        toks[fam] = AutoTokenizer.from_pretrained(name)

    results: dict[str, dict] = {}
    print(f"\n{'lang':<5}{'family':<13}{'fert/word':>11}{'STRR':>8}{'tok/char':>10}")
    print("-" * 47)
    for lang in LANGS:
        if not (PROC / lang / "subcorpus.jsonl.gz").exists():
            print(f"{lang:<5} not built, skipping", flush=True)
            continue
        texts = sample_docs(lang)
        results[lang] = {"n_docs_sampled": len(texts),
                         "whitespace_word_measure_valid": lang not in UNSEGMENTED,
                         "families": {}}
        for fam, tok in toks.items():
            m = measure(tok, texts)
            results[lang]["families"][fam] = m
            flag = "  [word measure invalid]" if lang in UNSEGMENTED else ""
            print(f"{lang:<5}{fam:<13}{m['fertility_tokens_per_word']:>11.3f}"
                  f"{m['strr_single_token_rate']:>8.3f}{m['tokens_per_char']:>10.4f}{flag}",
                  flush=True)

    payload = {
        "experiment_id": "EXP-011",
        "purpose": "tokenizer fertility / STRR predictors for H0b/H1b (protocol §8)",
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "seed": SEED,
        "n_docs_per_language": N_DOCS,
        "tokenizers": TOKENIZERS,
        "caveat": (
            "fertility_tokens_per_word is NOT interpretable for zh/ja/th, which lack "
            "whitespace word boundaries; a 'word' there is a clause. tokens_per_char is "
            "well defined for every script and is the cross-language comparable measure. "
            "Using the per-word measure across unsegmented scripts would repeat the "
            "orthography-as-linguistics error caught in ISSUE-005."
        ),
        "languages": results,
    }
    (OUT / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
