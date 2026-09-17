# Environment Audit (Phase 0)

**Date of audit:** 2026-08-11
**Auditor:** Automated session (machine-inspected, not self-reported by user)
**Purpose:** Establish the verified compute envelope *before* selecting a research
question, so that feasibility constrains the science rather than the reverse.

Every row below was obtained by executing an inspection command on this machine.
Nothing in this file is estimated or assumed. Items that could not be measured are
marked `EVIDENCE REQUIRED` rather than filled with a plausible value.

---

## 1. Host

| Property | Value | How verified |
| --- | --- | --- |
| OS | Windows 11 Home 10.0.26200 | session environment |
| Primary working dir | `d:\Research Work2` | `ls` |
| Repo state at audit | empty, 0 files, no git | `find . -type f \| wc -l` → 0 |
| Free disk (D:) | 388 GB available of 443 GB | `df -h /d` |
| Shells | PowerShell 5.1, Git Bash (POSIX) | session environment |

## 2. Compute

| Property | Value | How verified |
| --- | --- | --- |
| CPU | 11th Gen Intel Core i7-1165G7 @ 2.80 GHz | `wmic cpu get Name` |
| Physical cores | 4 | `wmic cpu get NumberOfCores` |
| Logical processors | 8 | `wmic cpu get NumberOfLogicalProcessors` |
| RAM | 31.65 GiB (33,984,909,312 bytes) | `wmic computersystem get TotalPhysicalMemory` |
| **GPU** | **None available** | `nvidia-smi` → command not found |
| CUDA via PyTorch | `torch.cuda.is_available()` → `False` | executed |
| PyTorch thread default | 4 | `torch.get_num_threads()` |

**This is a thermally-limited mobile laptop CPU with no accelerator.** It is the
single most important constraint on this project.

## 3. Software stack

| Package | Version | Notes |
| --- | --- | --- |
| Python | 3.11.0 | `python --version` |
| torch | 2.1.0+**cpu** | CPU build; no CUDA |
| transformers | 4.33.0 | old release; predates many current model architectures |
| numpy | 1.26.4 | |
| scipy | 1.16.3 | |
| pandas | 3.0.2 | |
| scikit-learn | 1.7.2 | |
| matplotlib | 3.10.7 | |
| pip | 26.0.1 | installs available (network reachable) |
| git | 2.47.1.windows.2 | |
| LaTeX | MiKTeX-pdfTeX 4.23 (MiKTeX 25.12) | manuscript compilation is possible locally |
| Ollama | 0.32.6 installed, **zero models pulled** | `ollama list` → empty |

**Absent** (checked, not installed): `sentence-transformers`, `faiss-cpu`, `faiss-gpu`,
`datasets`, `rank_bm25`, `chromadb`, `langchain`, `llama-index`, `vllm`, `openai`,
`anthropic`, `statsmodels`, `accelerate`, `peft`.

All of the above are pip-installable; absence is not a blocker, only a setup step.

## 4. Model / API access

| Resource | Status | How verified |
| --- | --- | --- |
| `OPENAI_API_KEY` | unset | env check |
| `ANTHROPIC_API_KEY` | unset | env check |
| `HF_TOKEN` | unset | env check |
| `COHERE_API_KEY` | unset | env check |
| `GOOGLE_API_KEY` | unset | env check |
| Hugging Face reachability | HTTP 200 in 1.49 s | `curl` |
| Local LLM weights on disk | none | `ollama list` empty |

Public Hugging Face models can be downloaded without a token. Gated models
(e.g. Llama family) would require `HF_TOKEN` and licence acceptance.

## 5. Measured throughput

**Measured 2026-08-11 by EXP-000.** Artifact: `results/EXP-000-throughput/metrics.json`.
Script: `scripts/bench_throughput.py`. Runtime env: `.venv`, torch 2.1.0+cpu,
transformers 4.36.2, numpy 1.26.4, 4 torch threads.

| Quantity | Measured value |
| --- | --- |
| BM25 index build | **46,996 passages/s** (1,500 passages in 0.032 s) |
| BM25 query | **1.69 ms/query** (592.6 queries/s) |
| Dense encoding — `paraphrase-multilingual-MiniLM-L12-v2` | **9.47 passages/s** (median of 3 reps, warm-up excluded, batch 16, max_len 256) |
| Small-LLM decode speed (tokens/s) | EVIDENCE REQUIRED — not measured; not needed unless the design adds generation |

### 5.0 Re-measured on real data — earlier caveat corrected

The synthetic figure above was flagged as "likely pessimistic versus natural text."
**That was wrong, and the correction matters for planning.** Re-measured on real
MIRACL Yoruba passages (2026-08-11, same host and settings):

| Quantity | Real MIRACL `yo` |
| --- | --- |
| Mean tokens/passage | 88.5 |
| Median tokens/passage | 44.0 |
| p95 tokens/passage | 307 |
| **Encode rate** | **9.62 passages/s** — 1.02× the synthetic figure |

Real text is *much* shorter than the synthetic passages, yet throughput is
unchanged. The reason is **padding**: batches pad to the longest sequence present,
and with p95 = 307 tokens the batch cost is set by its longest member, not its
median. Median length is therefore nearly irrelevant at batch 16.

**Consequence — a free speedup that must be used:** length-sorted (bucketed)
batching would cut encoding cost substantially by keeping batches homogeneous.
This should be implemented before any full run. Corpus passages also exceed the
model's 512-token limit in the tail (one observed at 1,568 tokens), so the
truncation length is an explicit, reportable design parameter.

### 5.1 The binding constraint

Dense encoding is roughly **5,000× more expensive than BM25 indexing** on this host.
BM25 is effectively free; **the dense encoder is the entire compute budget.**

Projected single-pass encoding time at 9.47 passages/s (**projection, not
measurement** — and corpus sizes are `UNVERIFIED` pending counts read from the real
corpora):

| Corpus size | Projected time, one model, one pass |
| --- | --- |
| 49k passages | ~1.4 h |
| 132k passages | ~3.9 h |
| 297k passages | ~8.7 h |
| 518k passages | ~15.2 h |
| 2M passages | ~59 h |

### 5.2 Design consequences (binding)

1. **Full-corpus MIRACL on high-resource languages is out of reach.** Arabic, Persian,
   Japanese, Russian, English (millions of passages) would each cost days per model.
   The experiment must not be designed as if they were available.
2. **The feasible language set is the small-corpus tail** — which is fortunate, because
   that tail *is* the low-resource population the research question is about. The
   constraint and the question point the same way.
3. **Every added encoder multiplies total cost**, so the number of encoders is a
   first-class budget decision, not an afterthought.
4. Encoding must be **checkpointed and resumable**; a multi-hour CPU job on a laptop
   will be interrupted.
5. If corpora must be subsampled, the subsampling protocol must be fixed in advance and
   documented, since it changes retrieval difficulty and therefore comparability.

---

## 6. Feasibility implications for research-question selection

Derived from the facts above. These are engineering judgements, flagged as such.

**Tractable on this machine:**
- Sparse retrieval (BM25) over corpora up to O(10^6) passages.
- Dense retrieval with *small* encoders (22M–110M params, e.g. MiniLM / BGE-small
  class) — CPU inference is slow but batch-parallel and embarrassingly resumable.
- Reranking with small cross-encoders over a bounded candidate set (top-50/100).
- Any experiment whose cost is dominated by *retrieval and scoring* rather than
  *long-form generation*.
- Full statistical analysis, error analysis, figure and table generation, LaTeX build.

**Marginal — feasible only with tight budgeting:**
- Generation with 1B–3B parameter quantized local models via Ollama. Feasible per-query,
  but the per-item cost must be measured before committing to an evaluation-set size.
- Multi-turn agentic loops (each turn multiplies generation cost).

**Not tractable locally:**
- Any model training or fine-tuning beyond trivial scale.
- 7B+ generation across thousands of evaluation items.
- Experiments requiring frontier-model API calls, unless a paid key is provided.

**Consequence:** a research question centred on *retrieval quality, retrieval
efficiency, or evaluation methodology* is defensible here. A question requiring
large-scale generation from large models is **not**, unless additional budget or
hardware is supplied. Designing the latter and then quietly under-running the
experiments would violate the project's evidence rules.

---

## 7. Open blockers requiring the human author

1. Research direction is not yet defined.
2. Compute/API budget beyond this laptop is unknown.
3. Target IEEE venue and deadline are unknown.

These are recorded in the session report and must be resolved before Phase 1
(research-question definition) can be completed honestly.

### 5.3 Measured feasibility of the planned design

Using the **real-text** rate (9.62 passages/s) and EXP-001 verified corpus sizes:

| Scenario | Cost per encoder |
| --- | --- |
| Yoruba full corpus (49,043) | **85 minutes** |
| 50k passages x 12 languages | **17.3 hours** |
| Full MIRACL (77.2M) | ~2,230 hours — remains infeasible |

**The equal-size sub-corpus design is feasible on this laptop** at roughly 17 h per
encoder, before the length-bucketing speedup. Two encoders is realistic across a few
overnight runs; the encoder count remains the main budget lever.

### 5.4 Evaluation-set size — a power concern, not a compute one

MIRACL `yo` dev (downloaded and parsed 2026-08-11):

- corpus: **49,043** passages — exactly matches the EXP-001 API count (independent
  cross-validation of the size source);
- dev queries: **119**;
- qrels lines: **1,188**, of which **144** are positive judgments (~10 judged docs/query).

119 queries is a **small evaluation set**. Per-language metric estimates will carry wide
confidence intervals, and this — not compute — is the binding limit on how confidently
any single language can be characterised. Query counts per language must be tabulated
before the language set is fixed, and confidence intervals reported throughout.
