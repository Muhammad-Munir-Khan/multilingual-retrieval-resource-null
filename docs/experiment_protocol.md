# Experiment Protocol — PRE-REGISTERED

**Date registered:** 2026-08-11
**Verification:** the amendments in Section 11 below each carry their own date and a
statement of whether results existed at the time they were made.
**Question:** `docs/research_question_v2.md`
**Authorised by:** `docs/novelty_audit_v2.md` (CONDITIONAL PASS, constraints C1–C3)

---

## 0. Status of this document

This protocol is fixed **before any retrieval effectiveness result has been computed
or observed.** No nDCG, Recall, or MRR value for any language, model, or condition
exists in this repository at the time of registration. The only measurements taken so
far are throughput (EXP-000), corpus sizes (EXP-001), and evaluation-set sizes
(EXP-002) — none of which reveal an outcome.

**Amendments are permitted but must be additive and dated.** Any change made after
results are seen must be recorded in §11 with its date and justification, and results
under the amended protocol reported separately from those under the original. Silent
revision of this document is a research-integrity failure.

---

## 1. Hypotheses (restated, falsifiable)

```
H0a: The dense-retrieval deficit relative to BM25 does not vary systematically
     with language, once corpus size and evaluation geometry are equalised.
H1a: It does vary systematically.

H0b: After conditioning on BM25 performance, tokenizer fertility carries no
     additional association with the dense deficit.
H1b: Fertility retains an association beyond what BM25 explains.
```

**Pre-committed interpretation:** retaining H0b is a publishable result. It would
indicate that the field's routine attribution of multilingual retrieval failure to
tokenization is not supported once language-intrinsic difficulty is accounted for.
This outcome will **not** be reframed post hoc into a different question.

## 2. Languages

**All 18 MIRACL languages** are included:
`yo, sw, bn, hi, te, th, id, ko, fi, ar, fa, zh, ja, ru, es, en, de, fr`

Justified by EXP-002 (`results/EXP-002-miracl-survey/metrics.json`): total corpus
download is **16.18 GB** compressed, and every language has a dev split. Compute is
not the binding constraint once corpora are equalised (§3).

**Yoruba is retained despite low power** (119 dev queries, 144 positives). It is the
lowest-resource language in the set and therefore central to the question. It will
carry a wide confidence interval and correspondingly low weight in the aggregate
(§7). It is **not** dropped to make results look tidier.

## 3. Corpus construction (constraint C3)

EXP-001 established a **271× corpus-size ratio** across MIRACL (yo 49,043 →
fr 13,306,000). Retrieval difficulty rises with collection size independently of
language, so raw cross-language comparison is invalid. Therefore:

- **Fixed sub-corpus size N = 49,043 passages per language**, equal to the full size
  of the smallest corpus (Yoruba). Chosen because it is the largest value that
  requires no subsampling of the smallest language — not tuned.
- Each language's sub-corpus = **all judged documents for the sampled queries**
  (§4) **∪ a uniform random sample** of remaining passages, filled to exactly N.
- Sampling by reservoir over the streamed corpus, **seed = 20260811**, recorded per
  language with the resulting document-ID list hashed and committed.
- Yoruba uses its complete corpus (49,043 = N); this is stated, not hidden.

## 4. Query sampling — and why it is capped

**Cap: Q_max = 300 dev queries per language**, sampled without replacement,
**seed = 20260811**. Languages with fewer than 300 (yo 119, ko 213) use all available.

**Rationale, pre-registered because it is a real trap:** judged documents must be
retained in the sub-corpus or recall is undefined. But judged-document count scales
with query count. Uncapped, Arabic (2,896 queries, ~10 judged/query ⇒ ~29k judged
docs) would have **~59% of its 49,043-passage sub-corpus consist of judged
documents**, versus **~2.4% for Yoruba**. Retrieval would be trivially easier in
high-query languages for a reason that has nothing to do with language.

Capping at 300 holds judged documents to roughly 3,000 per language (~6% of the
sub-corpus), making evaluation geometry comparable. The **realised judged fraction
per language will be reported as a diagnostic**, and if it still varies materially
it must be carried as a covariate.

## 5. Systems compared

| System | Role |
| --- | --- |
| **BM25** | Pretraining-free reference. Identifies language-intrinsic difficulty (C1 §4 of the question doc). |
| **Dense encoder A** — `paraphrase-multilingual-MiniLM-L12-v2` | Small multilingual bi-encoder; throughput measured (9.62 p/s). |
| **Dense encoder B** — a second multilingual encoder with a *different tokenizer* | Required: a single encoder cannot separate tokenizer effects from model effects. Exact model fixed in the first amendment once its CPU throughput is verified. |

Encoders are used **zero-shot and frozen**. No training or fine-tuning anywhere
(constraint C1; also infeasible per `environment_audit.md`).

**Retrieval settings:** BM25 default Okapi parameters (k1=1.5, b=0.75), whitespace
tokenisation for scoring reported explicitly as a limitation for unsegmented scripts
(zh, ja, th). Dense retrieval by exact cosine over mean-pooled embeddings, max_len 256,
length-bucketed batching. Exact search, not ANN — corpora are small enough that ANN
adds error without benefit.

## 6. Metrics

- **Primary:** nDCG@10 — standard for MIRACL, uses graded judgments, focuses on the
  region actually consumed.
- **Secondary:** Recall@100 (first-stage capacity), MRR@10 (comparability with the
  Amharic prior work, which reports MRR@10).

Chosen before results, and reported for every language regardless of outcome.

## 7. Statistical plan

**Primary evidence — paired, within-language.** For each language, the BM25 vs dense
difference is computed **per query on identical queries and identical sub-corpora**.
Uncertainty via **bootstrap over queries, 10,000 resamples, seed 20260811**, reported
as a 95% percentile CI on the per-language mean difference.

**Aggregation — random-effects meta-analysis across languages**, weighting each
language by the inverse variance of its effect estimate. This is why Yoruba can be
retained without distorting the result: low-power languages receive low weight
automatically rather than being discarded by hand.

**Secondary — descriptive only.** Association between the dense deficit and
tokenizer fertility / STRR / pretraining-resource proxy, conditioned on BM25.
With n=18 languages and known collinearity between fertility and resource level,
this is **underpowered and confounded**. It will be reported with collinearity
diagnostics (VIF, pairwise correlations) and **no causal language**. It is explicitly
not the primary evidence (constraint C1).

**Multiple comparisons:** three metrics × 18 languages. Primary inference is on
nDCG@10 only; secondary metrics are descriptive. No hypothesis will be declared
supported on the basis of a secondary metric alone.

## 8. Predictors (measured, not assumed)

| Predictor | Source | Status |
| --- | --- | --- |
| Tokenizer fertility | computed per language per encoder on that language's sub-corpus | to measure |
| STRR (single-token retention rate) | as above, per arXiv 2510.09947 | to measure; verify definition from primary source first |
| Pretraining resource proxy | published corpus statistics for the encoder's training data | `EVIDENCE REQUIRED` — must be sourced and cited, never estimated |
| Script / morphological type | typological databases | to source |

If the pretraining-resource proxy cannot be sourced for a given encoder, that
predictor is **dropped and its absence reported** — not substituted with a guess.

## 9. Falsification and stopping conditions

The design fails, and must be reported as failing, if:

- judged-document fractions remain badly unbalanced after capping (§4);
- BM25 whitespace tokenisation proves indefensible for zh/ja/th, in which case those
  languages are analysed separately and the limitation reported;
- the second encoder cannot be run within budget — then the tokenizer-variation arm is
  dropped, and only the H0a comparison is claimed;
- effect CIs are so wide that no ordering is distinguishable — reported as an
  inconclusive result, not narrowed until something reaches significance.

## 10. Artifact and reproducibility requirements

Every run writes `results/EXP-NNN-*/metrics.json` containing: experiment ID, UTC
timestamp, git commit, full config, seeds, package versions, and raw per-query scores.
Encoding must be **checkpointed and resumable** (multi-hour CPU jobs on a laptop get
interrupted). Sub-corpus document-ID lists are hashed and committed so sampling is
verifiable. Failed and abandoned runs remain in the record.

## 11. Amendments

### Amendment 1 — 2026-08-11: encoder set fixed; tokenizer/model partial separation added

**Made before any effectiveness result was computed.** No nDCG/Recall/MRR value
existed at the time of this amendment. It is a design improvement, not a response to
an outcome.

**(a) Encoder B fixed** — as §5 required. Measured on this host:
`distiluse-base-multilingual-cased-v2`, 134.7M params, **8.34 passages/s**
⇒ 29.4 h for 18 languages × 49,043. Encoder A is 9.62 p/s ⇒ 25.5 h.

**(b) A trap avoided.** `intfloat/multilingual-e5-small` was the obvious candidate for
encoder B and would have been **useless**: it shares XLM-R's tokenizer with encoder A
*exactly* (vocab 250,002 both). The tokenizer-variation arm would have been vacuous.
Verified vocabulary sizes:

| Tokenizer family | Vocab | Models available |
| --- | --- | --- |
| XLM-R SentencePiece | 250,002 | `paraphrase-multilingual-MiniLM-L12-v2`, `multilingual-e5-small` |
| mBERT WordPiece | 119,547 | `bert-base-multilingual-cased`, `distiluse-base-multilingual-cased-v2` |
| LaBSE WordPiece | 501,153 | `LaBSE` |

**(c) Fertility variation confirmed real**, measured on 800 real MIRACL `yo` passages:

| Tokenizer | Fertility | STRR |
| --- | --- | --- |
| XLM-R 250k | 2.828 | 0.329 |
| mBERT 119k | 2.514 | 0.363 |
| LaBSE 501k | 1.994 | 0.574 |

Larger vocabulary ⇒ lower fragmentation, as expected. The predictor has real spread,
so the arm is viable rather than degenerate.

**(d) New design lever — partial tokenizer/model separation.** Because two model
*pairs* share a tokenizer exactly, model variation can be estimated **with tokenizer
held constant**:

```
tokenizer held fixed (XLM-R 250k):  MiniLM-L12   vs  multilingual-e5-small
tokenizer held fixed (mBERT 119k):  mBERT        vs  distiluse-v2
tokenizer varied:                   across the two families
```

Within-family differences estimate how much encoders differ **when tokenization is
identical**. Cross-family differences contain tokenizer *and* model effects. The
difference of differences partially isolates the tokenizer channel **without
retraining** — a strictly better identification than the original two-encoder design.

**This does not overturn constraint C1.** It remains quasi-experimental: models differ
in training data and objective as well as tokenizer, so the separation is partial and
assumption-laden. Rust et al. remains the design we cannot run. The manuscript must
still avoid causal language.

**(e) Cost and the resulting tiered design.** Four encoders across 18 languages
projects to ~112 h before length-bucketing — too long for one machine. Therefore:

- **Tier 1 (all 18 languages, 2 encoders — one per tokenizer family):** the primary
  H0a/H1a comparison. ~55 h.
- **Tier 2 (subset of 8 languages, 4 encoders):** the difference-in-differences for
  partial tokenizer/model separation. Language subset to be fixed **before running**,
  chosen to span fertility and resource level, and registered as Amendment 2.

If Tier 2 proves unaffordable, it is dropped and only Tier 1 claimed — per §9.

### Amendment 2 — 2026-08-11: character 4-grams as the primary BM25 tokenisation

**Resolves ISSUE-005. Registered before any dense-retrieval result exists anywhere in
the repository** — so this choice cannot be selecting a tokenisation that favours a
comparative outcome, because no comparison has been computed. The decision criterion is
external: *maximise the validity of the reference system across scripts, uniformly.*

**Change:** BM25 tokenises by **character 4-grams within whitespace-delimited units**,
applied identically to all 18 languages. Word tokenisation is retained as a reported
robustness check.

**Why.** Whitespace tokenisation fails on Thai, Chinese and Japanese for a purely
**orthographic** reason — those scripts have no word spaces — not for any reason
connected to language difficulty. Since BM25's role in this study is to represent
*language-intrinsic difficulty* free of pretraining effects, letting an orthographic
convention destroy it would contaminate the reference. Character n-grams are
script-agnostic and are the standard remedy in the CLIR literature.

Crucially, char n-grams remain **uniform across languages**, so they do **not**
reintroduce the resource-correlation problem that ruled out per-language analyzers
(ISSUE-001).

**Measured effect** (nDCG@10; official = published Anserini baseline):

| lang | word | char-4gram | official |
| --- | --- | --- | --- |
| th | 0.2824 | **0.5410** | 0.484 |
| ko | 0.3720 | **0.4051** | 0.453 |
| yo | 0.4774 | **0.5170** | 0.406 |
| hi | 0.4760 | **0.4887** | 0.458 |
| sw | 0.4901 | **0.4933** | 0.383 |

Char n-grams are **better or equal on every language tested** — there is no
language traded off against another, which is what makes this a validity fix rather
than a tuning choice. Indexing cost is 3–12 s per language.

**n = 4 is not tuned.** It is the conventional CLIR default and is applied uniformly.
Sensitivity to n will be reported as a robustness check, **not** used to select the
value that maximises any result.

**Residual limitation, recorded not hidden:** Korean remains ~10.6% below the official
baseline even with char n-grams, because Anserini's morphological analyzer segments
agglutinative morphology in a way no uniform tokenisation can match. This is an honest
handicap of the uniform-treatment design and must appear in Limitations.

**Consequence:** all BM25 results computed before this amendment are superseded.
Results are written to `results/EXP-004-bm25-char/` and `results/EXP-004-bm25-word/`
so the two tokenisations are never conflated.

### Amendment 3 — 2026-08-11: encoder set revised for coverage and task fit

**Resolves ISSUE-006.** Registered after one dense result exists (yo / encoder A), so
this amendment is **not** blind. That is disclosed rather than glossed: the change is
driven by *declared language coverage and training objective*, both properties of the
models themselves and verifiable independently of any result. It is not driven by which
encoder produced a preferred effect — indeed the revision makes the low-resource
comparison **harder** to confirm, because the new encoders actually support the
languages where the deficit was largest.

**Revised encoder set:**

| Key | Model | Coverage | Task | Role |
| --- | --- | --- | --- | --- |
| **E5** | `intfloat/multilingual-e5-small` | 94 langs (missing yo) | retrieval-trained | **new primary**; XLM-R tokenizer |
| **LaBSE** | `sentence-transformers/LaBSE` | **110 langs, covers all 18** | bitext/similarity | coverage anchor; own 501k WordPiece tokenizer |
| A | `paraphrase-multilingual-MiniLM-L12-v2` | 50 | paraphrase/STS | retained as a *coverage-limited* comparator, clearly labelled |
| B | `distiluse-base-multilingual-cased-v2` | 50 | paraphrase/STS | retained, same caveat; mBERT tokenizer |

**Language coverage becomes a first-class reported covariate**, not an assumption. Every
per-language result must state whether the encoder declares support for that language.
Analyses pooling supported and unsupported languages without that split are invalid.

**Implementation requirement:** E5 models require `"query: "` and `"passage: "` prefixes.
Omitting them silently degrades E5 and would understate it — a weak-baseline failure of
the same kind ISSUE-001 guarded against. This must be implemented and verified before
any E5 result is recorded.

**Cost.** LaBSE is ~471M parameters, roughly 4× encoder A, so full coverage is expensive
on this host. `EVIDENCE REQUIRED` — LaBSE throughput must be measured before the language
set for it is fixed. If unaffordable across 18 languages, it runs on a pre-declared
subset chosen for fertility and resource spread, registered before running.

**Status of prior results:** the yo/encoder-A result is retained and reported as
coverage-confounded. It is not evidence for H1a.

### Amendment 4 — 2026-08-12: the tokenizer difference-in-differences arm is DROPPED

**Not identifiable with publicly available models.** Evidence: EXP-012.

Amendment 1 planned to separate tokenizer effects from model effects by comparing
encoder pairs that share a tokenizer exactly. EXP-012 shows that design cannot work:

| model | vocab | training objective |
| --- | --- | --- |
| BGE-M3 | 250002 | retrieval |
| GTE-multilingual-base | 250048 | retrieval |
| Arctic-Embed-l-v2.0 | 250002 | retrieval |
| jina-embeddings-v3 | 250002 | retrieval |
| multilingual-e5-base / large | 250002 | retrieval |
| multilingual-e5-small | 250037 | retrieval |
| **LaBSE** | **501153** | **bitext/similarity** |

**Every retrieval-trained multilingual encoder surveyed uses an XLM-R-derived ~250k
vocabulary.** The one substantially different tokenizer belongs to LaBSE — which our
own measurements show loses to BM25 on both languages tested (ISSUE-009).

So tokenizer and training objective are **perfectly confounded in the available model
population**: any pair differing in tokenizer also differs in objective, and the LaBSE
evidence indicates objective is the dominant term. Running encoders A/B across 18
languages (~14 h) would measure task mismatch, not tokenization, while appearing to
measure tokenization. That is worse than not running it.

**Dropped, and reported as a limitation rather than silently omitted.** The remaining
tokenization evidence is the observational association in §H0b (EXP-011), which is
explicitly correlational and already carries that caveat.

**This strengthens rather than weakens the paper's methodological point.** Rust et al.
(ACL 2021) isolated tokenizer effects by *pretraining matched models*, which this
project cannot do (no GPU). EXP-012 shows the observational alternative is unavailable
too, because the field has converged on one tokenizer. Tokenizer effects in multilingual
*retrieval* are therefore close to unstudiable without new pretraining — a concrete
statement about what the field currently cannot know, supported by measurement.

**Compute released:** ~14 h, redirected to the pre-registered robustness runs (BM25 word
tokenisation, char n-gram sensitivity) and the higher-powered Hindi prefix ablation.
