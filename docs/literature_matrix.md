# Literature Matrix

**Started:** 2026-08-11
**Status:** IN PROGRESS.

- **Part I (§A–§G)** — adaptive retrieval gating. **CLOSED**: direction retired after the
  novelty audit failed. Retained as the evidence record for that decision.
- **Part II (§H–§K)** — multilingual retrieval degradation (current direction v2).

## Verification policy

Search-engine snippets are treated as *discovery only*, never as evidence.
A row is marked `VERIFIED` only where the arXiv abstract page, publisher page, or
PDF was actually retrieved in-session and the metadata read directly.

| Code | Meaning |
| --- | --- |
| `VERIFIED` | Primary source fetched this session; title/authors/date read directly |
| `SNIPPET-ONLY` | Known only from search results — **must be verified before citation** |
| `EVIDENCE REQUIRED` | Needed for the argument but not yet located |

**No entry in this file may be cited in the manuscript while marked `SNIPPET-ONLY`.**

**Update 2026-08-12 (EXP-015):** the ten works the manuscript actually intends to cite
have been verified against the **arXiv API** — arXiv's own metadata service, not a search
engine — and their titles, author lists and dates recorded in
`results/EXP-015-references/metrics.json`. Generated bibliography: `paper/references.bib`.

A distinction that matters and is enforced in the generated file: **arXiv metadata proves
a preprint exists with the stated metadata. It does not prove a peer-reviewed venue.**
Four entries carry a claimed published venue (MIRACL→TACL 2023, Rust et al.→ACL 2021,
XLM-R→ACL 2020, LaBSE→ACL 2022); each is marked `REQUIRES VENUE VERIFICATION` in the bib
and must be checked against the publisher record before that venue is asserted. Two works
are not on arXiv at all (Robertson et al. BM25; the TACL version of MIRACL) and are
flagged for manual verification.

Remaining `SNIPPET-ONLY` entries below are retained as **discovery context only** — they
document how the field was surveyed and which directions were retired. They are not
cited.

---

## A. Directly competing work (the novelty threat set)

### A1. Moskvoretskii et al. — Adaptive Retrieval Without Self-Knowledge? Bringing Uncertainty Back Home

- **Status:** `VERIFIED` (arXiv abs page fetched 2026-08-11)
- **arXiv:** 2501.12835 [cs.CL]; submitted 2025-01-22, revised 2025-02-21
- **Authors:** V. Moskvoretskii, M. Lysyuk, M. Salnikov, N. Ivanov, S. Pletenev,
  D. Galimzianova, N. Krayko, V. Konovalov, I. Nikishina, A. Panchenko
- **Artifacts:** code/data at `s-nlp/AdaRAGUE` (GitHub) — `EVIDENCE REQUIRED`: confirm repo live
- **What it does:** comprehensive comparison of **35 adaptive retrieval methods**
  (8 recent adaptive approaches + 27 uncertainty-estimation techniques), across
  **6 datasets**, **10 metrics** spanning QA performance, self-knowledge, efficiency.
- **Key finding (verbatim from abstract):** "uncertainty estimation techniques often
  outperform complex pipelines in terms of efficiency and self-knowledge, while
  maintaining comparable QA performance."
- **Threat to us:** **SEVERE.** This closes the gap "nobody has fairly compared
  adaptive retrieval methods." Any proposal to benchmark adaptive retrieval methods
  is pre-empted. It also pre-empts "simple uncertainty baselines are underrated."
- **What it does NOT appear to do:** report the hardware its efficiency measurements
  were taken on, or test whether the efficiency ordering is hardware-regime dependent.
  `EVIDENCE REQUIRED` — must read the full paper's efficiency section before relying
  on this.

### A2. Wang, Wei, Ling — Retrieval as a Decision: Training-Free Adaptive Gating for Efficient RAG (TARG)

- **Status:** `VERIFIED` (arXiv abs + HTML v2 fetched 2026-08-11)
- **arXiv:** 2511.09803; v1 2025-11-12, v2 2026-04-14
- **Authors:** Yufeng Wang, Lu Wei, Haibin Ling
- **Method:** single-shot gate. Generates a short **no-context draft**, computes
  uncertainty from prefix logits — mean token entropy, top-1/top-2 margin via a
  monotone link, or small-N variance across stochastic prefixes — retrieves only
  above a threshold. Threshold set from the empirical CDF on a dev split to hit a
  target retrieval rate.
- **Datasets:** NQ-Open, TriviaQA, PopQA, MuSiQue, ASQA.
- **Baselines:** Always-RAG, Never-RAG (per abstract).
- **Reported result:** matches/improves EM/F1 while reducing retrieval 70–90% and
  cutting end-to-end latency vs Always-RAG.
- **Cost model (verbatim, §3.3):**
  `E[T(τ)] = T_draft + (1−π(τ))E[T_out(0)] + π(τ)(T_ctx + E[T_out(1)])`
  — i.e. cost is accounted in **LM tokens**.
- **Latency reporting (verbatim):** "Δ latency is the added seconds per query relative
  to the Never-RAG baseline on the same dataset/hardware".
- **Hardware disclosure:** **NONE FOUND.** No GPU type, CPU spec, or serving
  infrastructure stated in main text or appendix (fetched HTML v2). Only
  "all runs use batch size 1 and identical decoding parameters across modes".
- **Stated limitation (verbatim):** "We heavily scoped our evaluation to English
  open-domain QA over Wikipedia." Hardware sensitivity is **not** listed as a
  limitation or future direction.
- **Threat to us:** **SEVERE** for any "new training-free gating signal" proposal.
  **This is the paper a reviewer would cite to reject a gating-signal contribution.**
- **Opening it leaves:** its efficiency claim is stated in tokens and in Δ-seconds on
  undisclosed hardware. Whether the latency conclusion survives a different
  generation:retrieval cost ratio is untested by this paper.

### A3. RAG-QPP — Adaptive Query Performance Prediction for RAG

- **Status:** `SNIPPET-ONLY` — **must verify before any citation**
- **Claimed venue:** ACM Transactions on Information Systems; claimed DOI
  `10.1145/3827605` — **UNVERIFIED, do not cite until resolved**
- **What it reportedly does:** predicts query difficulty from a 12-dimensional
  **post-retrieval** feature set (semantic similarity, lexical, score-distribution
  signals); explicitly generator-independent, requiring no model-internal signals
  such as perplexity or token-level uncertainty.
- **Threat to us:** **HIGH.** This substantially occupies "use cheap retrieval-side
  signals instead of LLM-internal signals." A proposal framed as *"retrieval-side
  gating avoids the LLM forward pass"* is largely pre-empted.
- **Action:** verify metadata and read the efficiency section. Determine whether it
  quantifies the *hardware-regime* dependence or only asserts post-retrieval features
  are cheaper.

### A4. Dong, Qin, Shah, Wang — Know Before You Fetch: Calibrated Retrieval-Budget Allocation for RAG

- **Status:** `VERIFIED` (PDF fetched 2026-08-11)
- **arXiv:** 2606.29959v1, submitted 2026-06-30
- **What it does:** predicts a per-query retrieval *budget* (how many documents)
  rather than a binary retrieve/skip decision.
- **Cost model:** treats retrieval quantity as the primary expense — more documents
  ⇒ more context tokens ⇒ higher cost. Standard RAG economics.
- **Datasets:** TriviaQA, NQ, MS MARCO, PopQA; Qwen and Llama variants.
- **Threat to us:** **MODERATE.** Occupies "how much to retrieve." Does not appear to
  question the underlying cost accounting itself.

---

## B. Foundational / earlier adaptive retrieval

All `SNIPPET-ONLY` — verify before citing. Listed to establish lineage.

| Work | arXiv | Mechanism | Note |
| --- | --- | --- | --- |
| Self-RAG | — | trained reflection tokens judging retrieval necessity | requires fine-tuning; limits off-the-shelf use |
| FLARE | — | triggers retrieval on low-probability tokens during decoding | active/iterative |
| Adaptive-RAG | 2403.14403 | routes by predicted question complexity (none/single/multi-step) | classifier-based routing |
| SKR | — | KNN prober over self-knowledge | |
| SeaKR | 2406.19215 | self-aware knowledge retrieval | |
| Probing-RAG | 2410.13339 | self-probing for selective retrieval | |

## C. Adjacent / recent (2026) — crowding evidence

All `SNIPPET-ONLY`.

| Work | arXiv | Relevance |
| --- | --- | --- |
| L-RAG: Entropy-Based Lazy Loading | 2601.06551 | entropy-gated context loading |
| QuCo-RAG | 2512.19134 | uncertainty from pre-training corpus |
| Stop-RAG | 2510.14337 | value-based stopping for iterative RAG |
| FAIR-RAG | 2510.22344 | faithful adaptive iterative refinement |
| RAGRouter-Bench | 2602.00296 | benchmark for adaptive RAG routing |
| How You Ask Matters! | 2604.10745 | adaptive RAG robustness to query variations |
| BalanceRAG | 2605.20084 | joint risk calibration, cascaded RAG |
| RAG Performance Prediction for QA | 2604.07985 | performance prediction |

## D. Conformal / risk-control for RAG (occupied)

All `SNIPPET-ONLY`. Establishes that "statistical guarantees for RAG" is taken.

| Work | arXiv / venue | Note |
| --- | --- | --- |
| C-RAG: Certified Generation Risks | 2402.03181 | conformal risk control for RAG |
| Conformal factuality for RAG response quality | SIGIR '25, doi 10.1145/3726302.3730244 | group-conditional coverage |
| ToolChain-CRC | 2606.18467 | conformal risk control under retrieval/tool drift |
| Certified Domain-Consistency | 2607.14157 | per-domain conformal risk guarantees |

---

## E. Saturation assessment (honest)

Framings that are **already occupied** and should NOT be pursued as primary novelty:

1. ~~Propose a new training-free uncertainty gating signal~~ → TARG (A2), L-RAG, QuCo-RAG.
2. ~~Fairly benchmark adaptive retrieval methods~~ → Moskvoretskii (A1), RAGRouter-Bench.
3. ~~Use cheap retrieval-side signals instead of LLM internals~~ → RAG-QPP (A3).
4. ~~Decide how many documents to retrieve~~ → Know Before You Fetch (A4).
5. ~~Statistical/conformal guarantees for RAG~~ → Section D.
6. ~~Robustness of adaptive RAG to query phrasing~~ → 2604.10745.

**This area is heavily saturated.** Any contribution must survive all of the above.

## E2. Efficiency-reporting methodology prior art (CRITICAL — constrains our framing)

Searched 2026-08-11 specifically to *attack* our own candidate gap. It partially landed.

| Work | Source | Claim | Threat |
| --- | --- | --- | --- |
| **The Efficiency Misnomer** | ICLR 2022, arXiv 2110.12894 | `SNIPPET-ONLY` — cost indicators (parameters, FLOPs, throughput, wall-clock) disagree with one another; conclusions flip depending on which is chosen; gives reporting recommendations. Documented example: width scaling looks better under FLOPs/params, depth scaling looks better under wall-clock/throughput. | **SEVERE** |
| **The Framework Tax** | arXiv 2302.06117 | `SNIPPET-ONLY` — inference efficiency measured in NLP research diverges from deployment reality due to framework/system overhead. | **HIGH** |
| Cost-Governed RAG | arXiv 2607.12188 | `SNIPPET-ONLY` — per-tenant cost attribution unifying retrieval and generation cost in multi-tenant RAG. | **MODERATE — must verify** |

**Consequence — a framing we must now abandon:**

> ~~"Efficiency claims in adaptive retrieval are hardware-dependent and proxy metrics
> mislead."~~

This is **The Efficiency Misnomer's** thesis, published in 2022. Restating it for RAG
would be an incremental domain transfer and a reviewer would reject it on exactly that
basis. **It must not be the contribution.**

## F. The one opening identified so far

Across A1–A4 the efficiency claims are expressed in **tokens**, **retrieval-call
counts**, or **Δ seconds on undisclosed hardware**. The verified TARG evidence shows:

- cost accounted in LM tokens (§3.3 equation);
- latency reported only as a delta "on the same dataset/hardware";
- **no hardware disclosed anywhere in the paper**;
- hardware sensitivity absent from the limitations.

A draft-based gate spends **generation** compute in order to save **retrieval**
compute. Whether that exchange is profitable depends on the ratio of those two costs,
which varies by orders of magnitude between deployment regimes (GPU-served generation
with a remote vector service vs. CPU-served generation with a local sparse index).
No located work measures where that break-even lies or tests whether the published
ordering survives it.

### F1. Sharpened after the §E2 search — what actually survives

The generic "efficiency metrics mislead" claim is dead (§E2). What survives is a
narrower and structurally different point that the Efficiency Misnomer does **not**
make:

- **Efficiency Misnomer** is about *measurement*: comparing fixed models under
  different cost indicators changes which model looks better. The models themselves
  are unchanged.
- **A retrieval gate is not a model — it is a decision rule with a free parameter.**
  Its threshold τ determines behaviour. The cost-optimal τ is a *function of* the
  generation:retrieval cost ratio.

Verified from TARG (§A2): the threshold is calibrated from the dev-set empirical CDF
to **hit a target retrieval rate π(τ) = ρ**. That is calibration against a *rate*, not
against a *cost*. Targeting a retrieval rate is cost-optimal only if end-to-end cost is
linear in the retrieval rate with a coefficient that does not change across
deployments — which is precisely what varies between regimes.

So the candidate claim is not "the metric is misleading" but:

> **The field calibrates the gating threshold against the wrong objective.** Retrieval
> rate is a proxy for cost that is only faithful within the regime it was tuned in;
> a threshold calibrated to a retrieval-rate budget is therefore mis-set whenever the
> deployment's cost ratio differs from the evaluation's — and no adaptive-retrieval
> paper located so far discloses the cost ratio it was tuned under.

This is a claim about **policy optimality**, not about measurement hygiene. It admits
a constructive fix (calibrate τ against measured expected cost) and a falsifiable
prediction (the cost-optimal τ, and the policy ordering, shift with the ratio).

**This remains a hypothesis about a gap, not an established gap.** Outstanding checks
before it may be called novel:

1. Has anyone done **cost-aware threshold calibration** for retrieval gating?
   `EVIDENCE REQUIRED` — highest-priority search.
2. Does Cost-Governed RAG (§E2) already parameterise this trade-off? `EVIDENCE REQUIRED`.
3. Does the Moskvoretskii benchmark (§A1) already vary the cost model? `EVIDENCE REQUIRED`.
4. Prior art in the general cost-sensitive-learning / Neyman-Pearson literature will
   almost certainly contain the underlying decision-theory result. The contribution can
   therefore **not** be the decision theory itself — only its application, the empirical
   measurement, and the demonstration that the field's current practice diverges from it.
   This must be stated plainly in the paper rather than glossed over.

---

## G. Next literature actions

1. `EVIDENCE REQUIRED` — verify RAG-QPP (A3) metadata and DOI; read efficiency section.
2. `EVIDENCE REQUIRED` — read A1's full efficiency methodology; does it disclose hardware?
3. `EVIDENCE REQUIRED` — search the efficient-NLP literature on wall-clock vs proxy-metric
   reporting; this is where the closest *methodological* prior art will be, and it is the
   most likely source of a novelty rejection.
4. Verify all Section B foundational entries (Self-RAG, FLARE, Adaptive-RAG) properly.

---

# PART II — Multilingual Retrieval Degradation (direction v2)

Opened 2026-08-11 after the adaptive-retrieval direction was retired.

## H. Closest prior work

### H1. Alemneh, Mekonnen & de Rijke — The Multilingual Curse at the Retrieval Layer: Evidence from Amharic

- **Status:** `VERIFIED` (arXiv HTML fetched 2026-08-11)
- **arXiv:** 2605.24556v1, submitted 2026-05-23
- **Setup:** Amharic Passage Retrieval Dataset V2 (68K query–passage pairs from AMNEWS,
  XL-SUM, Amharic Wikipedia, AmQA). Four paradigms: dense bi-encoder, late interaction
  (ColBERT), learned sparse (SPLADE), cross-encoder reranking. 5 zero-shot multilingual
  retrievers (E5, Arctic Embed, mGTE, EmbeddingGemma, Harrier), 2 fine-tuned, 8
  monolingual Amharic retrievers, BM25.
- **Headline:** ColBERT-Base-Amharic MRR@10 **0.803** vs best zero-shot
  (Snowflake Arctic Embed) **0.653** — 23% relative gap.
- **Stated limitations (verbatim / near-verbatim):**
  1. "the empirical evidence is limited to Amharic" — no comparable-magnitude testing
     across other underrepresented languages;
  2. weakly supervised, source-aligned positives, one labelled passage per query;
  3. only two multilingual models fine-tuned;
  4. "RAG implications are inferred from retrieval metrics rather than measured in an
     end-to-end generation pipeline."
- **Critically for us:** establishes the phenomenon but **does not experimentally
  isolate tokenization**, and treats tokenizer and pretraining distribution as
  "intertwined factors rather than separable variables."
- **Threat:** **MODERATE** — it is the paper we extend, and it names our opening in its
  own limitations. It is also the paper a reviewer will ask us to beat, so our
  multi-language result must be substantive, not a re-run.

### H2. Rust et al. — How Good is Your Tokenizer? On the Monolingual Performance of Multilingual Language Models

- **Status:** `SNIPPET-ONLY` — verify before citing. ACL 2021; arXiv 2012.15613.
- **Why decisive:** it is the **methodological gold standard** for our confound. It
  disentangles tokenizer quality from pretraining data size by **training new monolingual
  models on equally sized datasets with different tokenizers**, across 9 typologically
  diverse languages and 5 tasks. Finds tokenizer quality matters roughly as much as data
  size.
- **Threat:** **HIGH but bounded.** It covers NLU tasks, not retrieval. Its design
  requires pretraining, which is impossible on our hardware.
- **Consequence for us:** we **cannot** claim causal disentanglement. Rust et al. must be
  cited explicitly as the design we cannot run, and our contribution framed as an
  associational decomposition under stated assumptions. Failing to do this would be the
  single most likely cause of rejection.

### H3. Goworek, Macmillan-Scott & Özyiğit — What Drives Cross-lingual Ranking?

- **Status:** `VERIFIED` (PDF pp.1–4 read directly, 2026-08-11)
- **arXiv:** 2511.19324v1, 24 Nov 2025. The Alan Turing Institute.
- **Task:** **CLIR** — cross-lingual retrieval, queries in one language, documents in
  another. **Not** monolingual retrieval within a low-resource language.
- **Datasets:** CLIRMatrix, mMARCO, Large-Scale CLIR. **MIRACL is cited ([44]) but not
  used as a dataset.**
- **Models:** BM25 + XLM-R, Nomic-embed, multilingual-E5, mmBERT, LaBSE.
- **Interventions studied (4):** document translation (NLLB-200), contrastive alignment
  at word/phrase/query–document level, cross-encoder reranking with easy/hard negatives,
  ANN efficiency.
- **Findings:** CLIR-trained dense models consistently beat lexical matching and derive
  little benefit from document translation; gains over lexical and translated baselines
  "are most pronounced for low-resource and cross-script pairs."
- **Stated contribution incl.:** "quantifies retrieval biases and typological correlations
  across language pairs."
- **Threat:** **MAJOR.** Adjacent — it does relate language properties to retrieval
  outcomes and compares lexical vs dense across many languages. Differentiators: different
  task (CLIR vs monolingual), different datasets, and interventions rather than a
  tokenization/pretraining decomposition.
- `EVIDENCE REQUIRED` — **Section 5's linguistic-factor analysis must be read in full**
  before our novelty claim is finalised. If it already regresses performance on fertility
  or resource level, our §H1-derived opening narrows sharply.

### H4. Huang et al. — Disentangled Contrastive Learning for Zero-Shot Multilingual Dense Retrieval

- **Status:** `VERIFIED` (arXiv HTML fetched 2026-08-11)
- **arXiv:** 2608.02189v1, submitted 2026-08-03
- **"Disentangled" here means representation disentanglement** — splitting embeddings into
  semantic and language-specific subspaces. **Not** confound disentanglement.
- Method paper; requires fine-tuning (MS MARCO + WikiMatrix, 4 epochs / 60K steps).
  Evaluated on mMARCO (14 langs) and MIRACL (18 langs).
- **Threat:** **LOW on substance, HIGH on terminology.** We must not use "disentangle"
  without distinguishing our usage, or reviewers will conflate the two.

## I. Supporting / contextual

| Work | ID | Status | Relevance |
| --- | --- | --- | --- |
| MIRACL (Zhang et al.) | 2210.09984; TACL 2023 | `SNIPPET-ONLY` | Our benchmark. 18 languages, 10 families, human qrels. Ships BM25 / mDPR / hybrid baselines — so the basic lexical-vs-dense comparison already exists per-language and is **not** itself a contribution. |
| Amharic passage retrieval embeddings | 2505.19356 | `SNIPPET-ONLY` | Reports fertility ↔ retrieval association: fertility 13.80 → MRR@10 0.019; fertility 1.46 → MRR@10 0.775. Strong motivating evidence; single language. |
| Beyond Fertility: STRR | 2510.09947 | `SNIPPET-ONLY` | Proposes Single-Token Retention Rate as a tokenization metric complementing fertility. Adopt as a second predictor. |
| BGE-M3 / M3-Embedding | 2402.03216 | `SNIPPET-ONLY` | Strong multilingual encoder; reported as relatively stable across languages. Candidate model — but check CPU feasibility, it is large. |
| NoMIRACL | project-miracl/nomiracl | `SNIPPET-ONLY` | Hallucination eval under first-stage retrieval errors, 18 languages. Relevant if we ever touch answer-level effects. |

## J. Saturation assessment for v2

Occupied — do **not** claim as contribution:
1. ~~Showing multilingual retrievers underperform on low-resource languages~~ → H1, MIRACL.
2. ~~Comparing BM25 vs dense per language~~ → MIRACL baselines.
3. ~~Proposing a better multilingual retriever~~ → H4, BGE-M3, Arctic-Embed 2.0.
4. ~~Causal tokenizer-vs-data disentanglement via retraining~~ → H2 (and infeasible here).
5. ~~Fertility as a tokenization quality metric~~ → STRR paper, Rust et al.

Materially **less saturated** than Part I: the closest work (H1) is single-language and
names our opening in its own limitations. But H3 is close enough that it must be read in
full before we commit.

## K. Next literature actions (blocking)

1. **BLOCKING** — read H3 Section 5 in full. Does it already regress retrieval on
   fertility / resource level? This single check can shrink or confirm our gap.
2. Verify H2 (Rust et al.) metadata from the ACL Anthology primary source.
3. Verify MIRACL TACL metadata and record per-language corpus sizes (needed to fix the
   feasible language set).
4. Verify the 2505.19356 fertility numbers against the paper, not the snippet.
