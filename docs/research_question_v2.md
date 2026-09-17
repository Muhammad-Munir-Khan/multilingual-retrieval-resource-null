# Research Question v2 — Multilingual Retrieval Degradation

**Date:** 2026-08-11
**Supersedes:** `research_question.md` (v1, retired — failed novelty audit)
**Status:** PROVISIONAL — must pass a second novelty audit before implementation.

---

## 1. Problem

Zero-shot multilingual dense retrievers underperform badly on low-resource,
morphologically rich, non-Latin-script languages. Two explanations circulate, usually
together and rarely separated:

- **(T) Tokenization channel** — multilingual tokenizers allocate vocabulary toward
  high-resource languages, over-segmenting low-resource text (high *fertility*), which
  fragments the representation.
- **(P) Pretraining/representation channel** — those same languages have little
  pretraining and little retrieval supervision, so the encoder's representations are
  simply weaker.

**These two are confounded.** Languages with high fertility are largely the same
languages with scarce pretraining data. Attributing the gap to either channel without
separating them is not supported by the evidence normally presented.

This confound is explicit in the closest prior work. Alemneh, Mekonnen & de Rijke
(*The Multilingual Curse at the Retrieval Layer: Evidence from Amharic*,
arXiv 2605.24556, 2026-05-23) — `VERIFIED` — report a 23% relative MRR@10 gap between
the best zero-shot multilingual retriever (0.653) and a monolingual Amharic ColBERT
(0.803), and state:

- their evidence is **"limited to Amharic"**, with no comparable-magnitude testing
  across other underrepresented languages;
- they do **not** experimentally isolate tokenization, citing over-segmentation as
  background rather than testing it;
- they treat tokenizer and pretraining distribution as **"intertwined factors rather
  than separable variables."**

## 2. Research question

> Across typologically diverse low-resource languages, how much of the zero-shot
> multilingual dense-retrieval deficit is associated with the **tokenization channel**
> versus the **pretraining/representation channel**, and does the single-language
> finding reported for Amharic generalise in magnitude to other under-represented
> languages?

## 3. Hypotheses

```
H0a: The Amharic-scale retrieval deficit does not generalise; the
     dense-vs-monolingual/lexical gap is not systematically larger for
     low-resource languages once corpus and query difficulty are accounted for.

H1a: The deficit generalises across low-resource languages, with magnitude
     varying systematically by language properties.

H0b: After conditioning on a lexical (pretraining-free) reference, tokenizer
     fertility carries no additional association with dense retrieval deficit.

H1b: Fertility retains an association with the dense deficit beyond what the
     lexical reference explains, indicating a tokenization channel distinct
     from general linguistic difficulty.
```

## 4. Identification strategy — and its honest limits

**The design cannot deliver strict causal identification, and the paper must not claim
it.** Rust et al. (*How Good is Your Tokenizer?*, ACL 2021, arXiv 2012.15613) achieved
clean separation by **pretraining new models with matched data and different
tokenizers**. That requires training and is impossible on this hardware
(`docs/environment_audit.md`: no GPU). Any claim of causal disentanglement here would
be unsupportable.

What the design *can* support is a **decomposition under stated assumptions**:

**BM25 as a pretraining-free reference.** BM25 has **no pretrained parameters**. Its
performance in a language is affected by morphological richness and lexical sparsity,
but **not** by how much text the language contributed to an encoder's pretraining
corpus. This asymmetry is the identifying leverage:

| Observation | Reading |
| --- | --- |
| BM25 and dense both degrade together | Consistent with general linguistic/task difficulty |
| Dense degrades while BM25 holds up | Consistent with a representation/pretraining channel |
| Degradation tracks fertility after conditioning on BM25 | Consistent with a tokenization channel |

**Assumptions this rests on (must be stated in the manuscript):**

1. BM25 difficulty is a valid proxy for language-intrinsic retrieval difficulty. This
   is imperfect — BM25 is itself harmed by morphological richness, which correlates
   with fertility. It therefore **absorbs part of the tokenization channel**, making
   our tokenization estimate *conservative* rather than unbiased.
2. Query and corpus difficulty are comparable across languages. MIRACL is
   language-parallel in construction but **not** in topic or difficulty; this is a
   threat to validity and must be reported, not assumed away.
3. Resource-level proxies (published pretraining corpus statistics) are approximate.

**Statistical power is a first-order risk.** MIRACL covers 18 languages; a feasible
subset is smaller. A cross-language regression with strongly collinear predictors
(fertility ↔ resource level) at n≈10–18 is **underpowered and collinear**. Therefore:

> Cross-language regression is **descriptive support only**. It must not be presented
> as the primary evidence, and no p-value from it should carry a causal claim.

**Primary evidence must instead be within-language and paired**, where each language
serves as its own control (paired tests across languages, not a regression over 18
points). Candidate paired interventions — feasibility to be established before
committing:

- lexical-unit interventions (morphological segmentation, stemming) applied to the
  **BM25** side, where the manipulation is interpretable and standard;
- comparison across multiple encoders whose fertility for a given language differs.

**Known threat to the intervention on the dense side:** pre-segmenting text before a
frozen encoder pushes input off-distribution. Any resulting degradation may reflect
distribution shift rather than fertility. This confound is **not currently solved**,
and the dense-side intervention will not be claimed as clean evidence unless it is.
`EVIDENCE REQUIRED`.

## 5. Feasibility (grounded in the verified envelope)

- **Data:** MIRACL and Mr. TyDi verified public and **not gated** (`gated: False`,
  HTTP 200, checked 2026-08-11). No HF token required — important, since none is set.
- **No annotation needed.** Both ship human relevance judgments. This is essential:
  the author has no native expertise in the target languages and **no annotator
  access**, so the design must never require new relevance judgments or qualitative
  reading of passages.
- **Compute:** restrict to small-corpus MIRACL languages (Yoruba, Swahili, Bengali,
  Telugu, Thai, Hindi class). BM25 is cheap; dense encoding is the cost driver.
  `EVIDENCE REQUIRED` — actual CPU encoding throughput must be measured before the
  language set is fixed. The language set follows from the measured budget, not the wish.
- **No training** anywhere in the design.

## 6. Scope

**In:** zero-shot retrieval only; public benchmarks with existing qrels; small
multilingual encoders; BM25; tokenizer statistics (fertility, and STRR per
arXiv 2510.09947); retrieval metrics (nDCG@10, Recall@100, MRR@10).

**Out:** training/fine-tuning of any kind; new annotation; end-to-end RAG answer
quality (the 1.5B-class generator available here is too weak in these languages for a
meaningful answer-level claim — a limitation to state, not to hide); qualitative error
analysis requiring native fluency.

## 7. Contribution type

**Empirical + analytical.** Explicitly *not* a new method, model, or benchmark.

1. Multi-language measurement testing whether the Amharic-scale deficit generalises —
   directly answering a limitation the Amharic authors state.
2. A decomposition, under stated assumptions, separating tokenization-associated from
   representation-associated deficit.
3. A negative-result-tolerant design: if the deficit does not generalise, or if
   fertility carries no signal beyond BM25, that is reported as the finding.

## 8. Risks

| Risk | Severity | Handling |
| --- | --- | --- |
| Reviewer demands causal identification | **HIGH** | Do not claim it. State the Rust et al. design as the gold standard we cannot run, and frame ours as an associational decomposition. |
| n≈10–18 languages underpowered/collinear | **HIGH** | Demote regression to descriptive; make paired within-language tests primary. |
| Dense-side segmentation intervention confounded by distribution shift | **HIGH** | Unsolved. Do not use as clean evidence until resolved. |
| "Replication + extension" seen as thin | **MEDIUM** | Decomposition is the substantive part; generalisation alone is insufficient. |
| CPU encoding too slow for enough languages | **MEDIUM** | Measure throughput first; cut language count, never cut controls. |
| Terminology collision with "disentangled" retrieval papers (2608.02189) | **LOW** | Cite and distinguish explicitly — theirs is representation disentanglement via training. |

## 9. Gate

No implementation until this passes `docs/novelty_audit.md` (second run) **and** CPU
throughput is measured.
