# Reproducibility Record

**Last updated:** 2026-08-11

Everything here was read off the machine that produced the results. No value is
copied from documentation or assumed from a package's nominal version.

---

## 1. Hardware

| Property | Value |
| --- | --- |
| CPU | 11th Gen Intel Core i7-1165G7 @ 2.80 GHz |
| Cores / threads | 4 physical / 8 logical |
| RAM | 31.65 GiB (33,984,909,312 bytes) |
| GPU | **none** — `nvidia-smi` not found; `torch.cuda.is_available()` → `False` |
| OS | Windows 11 Home 10.0.26200 |
| Disk | D: 443 GB total, 388 GB free at project start |

All results are CPU-only. This is a thermally limited mobile CPU; wall-clock timings
should not be treated as representative of server hardware.

## 2. Software

Runtime is the project virtual environment `.venv`, **not** the system Python.
Exact pinned set in `requirements.txt`.

| Package | Version | Note |
| --- | --- | --- |
| Python | 3.11.0 | |
| torch | **2.1.0+cpu** | pinned deliberately — see §2.1 |
| numpy | **1.26.4** | pinned `<2` — see §2.1 |
| transformers | 4.36.2 | |
| rank_bm25 | 0.2.2 | |
| git | 2.47.1.windows.2 | |
| LaTeX | MiKTeX-pdfTeX 4.23 (MiKTeX 25.12) | manuscript builds locally |

### 2.1 Two pins that are not arbitrary

- **torch 2.1.0+cpu.** torch 2.13.0+cpu installs cleanly on this host but fails at
  import with `ImportError: DLL load failed while importing _C` (missing VC runtime).
  2.1.0 is the newest verified-working build here. Reproducing on another machine may
  permit a newer torch; the pin records a host limitation, not a scientific requirement.
- **numpy < 2.** numpy 2.4.6 breaks torch 2.1.0 with
  `Failed to initialize NumPy: _ARRAY_API not found`, because that torch was built
  against the numpy 1.x ABI.

`sentence-transformers` is deliberately **not** used: its dependency pins conflict with
the only torch build that loads here, and mean pooling is a few explicit lines.

### 2.2 Absent tooling

- **No JVM** (`java -version` → not found), so Anserini/Pyserini cannot run here. This
  drove the ISSUE-001 decision to use a uniform in-process BM25.
- `ruflo` and `ponytail` are **not installed** (verified via `which`).

## 3. Determinism

| Element | Value |
| --- | --- |
| Master seed | **20260811** |
| Corpus reservoir sampling | seed 20260811, per language |
| Query sampling (cap 300) | seed 20260811, sorted before sampling so the sample does not depend on file order |
| Bootstrap | seed 20260811, 10,000 resamples |

Encoder inference is deterministic: models run in `eval()` mode under `torch.no_grad()`
with no dropout and no sampling.

**Verification of sampling:** each language's `manifest.json` stores a SHA-256 of its
sorted document-ID list. A rebuild that reproduces the hash reproduces the sample
exactly. This is why the sub-corpora themselves are not committed.

## 4. Data provenance

| Artifact | Source | Verified |
| --- | --- | --- |
| MIRACL corpus | `miracl/miracl-corpus` (HF) | public, `gated: False` |
| MIRACL topics/qrels | `miracl/miracl` (HF) | public, `gated: False` |
| Corpus sizes | HF datasets-server `/size` API; raw response committed at `results/EXP-001-corpus-sizes/raw_hf_size_response.json` | cross-validated: API says yo = 49,043; streaming the actual shard counted 49,043 |
| Published BM25 baselines | `castorini.github.io/pyserini/2cr/miracl.html` | used for calibration only, never as our own result |

No HF token is required and none is set.

## 5. Pipeline order

```
scripts/survey_miracl.py        EXP-002  eval-set sizes + corpus volumes
scripts/build_subcorpora.py     EXP-003  equal-size sub-corpora (seeded, hashed)
scripts/retrieval_eval.py       EXP-004  BM25 (char 4-gram primary, word robustness)
scripts/encode_and_search.py    EXP-005  dense retrieval
scripts/analyze.py              EXP-006  bootstrap + random-effects pooling
scripts/bench_throughput.py     EXP-000  instrument calibration only
```

Every script writes `results/<EXP-ID>/metrics.json` carrying the git commit, UTC
timestamp, seeds, and full config.

## 6. Known non-determinism and drift risks

1. **Hugging Face model weights are fetched by name, not by revision hash.** If upstream
   re-uploads a checkpoint, embeddings change silently. Revision SHAs are now **recorded**
   (EXP-010, `results/EXP-010-model-revisions/metrics.json`) so any rerun can confirm it
   used the same checkpoints:

   | key | model | revision | upstream last modified |
   | --- | --- | --- | --- |
   | E5 | `intfloat/multilingual-e5-small` | `614241f622f5` | 2026-04-02 |
   | LaBSE | `sentence-transformers/LaBSE` | `836121a0533e` | 2025-03-06 |
   | A | `paraphrase-multilingual-MiniLM-L12-v2` | `e8f8c211226b` | 2026-01-28 |
   | B | `distiluse-base-multilingual-cased-v2` | `bfe45d0732ca` | 2025-03-06 |

   **Recorded, not yet enforced.** The loader still resolves by name, so this detects
   drift after the fact rather than preventing it. Passing `revision=` to
   `from_pretrained` would close it properly.
2. Floating-point reduction order can differ across BLAS builds; observed effect in the
   bucketing validation was ≤ 1.7e-07, far below any reported precision.
3. Wall-clock timings vary with thermal throttling and background load. Several runs
   here shared 4 cores, so timings are **not** clean benchmarks and are reported as
   feasibility figures only.

## 7. Rebuilding from scratch

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/survey_miracl.py
.venv/Scripts/python.exe scripts/build_subcorpora.py --all      # ~16 GB download
.venv/Scripts/python.exe scripts/retrieval_eval.py --langs <langs>
.venv/Scripts/python.exe scripts/encode_and_search.py --lang <l> --model A
.venv/Scripts/python.exe scripts/analyze.py --dense EXP-005-dense-A
```

Encoding is resumable: shards already present are skipped, so an interrupted multi-hour
run continues rather than restarting.

## 8. Operational lesson: run jobs sequentially on this host

Measured 2026-08-11 while three CPU-bound jobs ran concurrently (dense encoding,
BM25 char n-gram indexing, corpus download/sampling):

- memory was **not** the constraint — 18.4 GB of 32.4 GB free, no swapping;
- all three processes advanced, but each far slower than alone.

The cause is thread oversubscription: this host has **4 physical cores**, and torch
defaults to 4 threads *per process*. Three such processes demand ~3× the available
parallelism, so they interleave rather than scale.

**Consequence for the Tier 1 run (~55 h):** run encoders **sequentially**, one language
and one model at a time. Parallel launches do not shorten wall-clock here and make
per-run timings uninterpretable as benchmarks. Any timing reported in the manuscript
must come from a run that had the machine to itself, and must say so.

A second, smaller lesson: background jobs were launched piped through `tail`, which
buffers until EOF and hid their progress entirely. Long runs should be launched without
that pipe so progress is observable.
