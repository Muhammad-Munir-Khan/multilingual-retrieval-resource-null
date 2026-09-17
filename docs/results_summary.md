# Results Summary — Tier 1

**Date:** 2026-08-12 (updated after Round 1 reviewer audit)
**Status:** Tier 1 complete. Robustness complete. R4 generalisation test running.
**Every number here traces to a committed artifact under `results/`.**

This document reports what was measured. Interpretation is separated from
observation, and claims that the evidence does not support are listed explicitly in
§7 so they cannot drift into the manuscript.

---

## 1. What was run

| Experiment | Content | Artifact |
| --- | --- | --- |
| EXP-003 | 18 equal-size sub-corpora, N=49,043 each, seeded and hashed | `results/EXP-003-subcorpora/` |
| EXP-004 | BM25, uniform character 4-grams, all 18 languages | `results/EXP-004-bm25-char/` |
| EXP-005 | E5 (`multilingual-e5-small`) dense retrieval, all 18 languages | `results/EXP-005-dense-E5/` |
| EXP-006 | Paired bootstrap + random-effects pooling | `results/EXP-006-analysis/` |
| EXP-007 | CC-100 pretraining-resource proxy | `results/EXP-007-resource-proxy/` |
| EXP-008 | BM25-only covariate structure | `results/EXP-008-bm25-covariates/` |
| EXP-011 | Tokenizer fertility / STRR / tokens-per-char, 3 families | `results/EXP-011-fertility/` |

## 2. Primary result — dense vs BM25, paired within language

**Languages the encoder declares support for (k=17):**

> pooled **+0.2627** nDCG@10, 95% CI **[+0.2240, +0.3013]**, τ²=0.00620, **I²=94.0%**

Every one of the 17 has a positive difference with a CI excluding zero.

**Reported separately — encoder does not declare support (k=1):**

> **yo −0.0676**, 95% CI **[−0.1584, +0.0260]**

| lang | BM25 | E5 | diff | 95% CI | n |
| --- | --- | --- | --- | --- | --- |
| zh | 0.1922 | 0.7112 | +0.5191 | [+0.476, +0.561] | 300 |
| ko | 0.4051 | 0.7406 | +0.3355 | [+0.286, +0.386] | 213 |
| ja | 0.4657 | 0.7913 | +0.3256 | [+0.286, +0.364] | 300 |
| fr | 0.4096 | 0.7061 | +0.2965 | [+0.260, +0.333] | 300 |
| th | 0.5410 | 0.8374 | +0.2964 | [+0.255, +0.337] | 300 |
| te | 0.6412 | 0.9285 | +0.2873 | [+0.243, +0.332] | 300 |
| ru | 0.5189 | 0.7991 | +0.2803 | [+0.242, +0.319] | 300 |
| de | 0.4856 | 0.7460 | +0.2604 | [+0.221, +0.299] | 300 |
| sw | 0.4933 | 0.7527 | +0.2594 | [+0.215, +0.304] | 300 |
| fa | 0.5056 | 0.7397 | +0.2340 | [+0.193, +0.274] | 300 |
| ar | 0.6238 | 0.8547 | +0.2309 | [+0.198, +0.264] | 300 |
| es | 0.5963 | 0.8218 | +0.2255 | [+0.193, +0.260] | 300 |
| en | 0.5904 | 0.8067 | +0.2163 | [+0.182, +0.250] | 300 |
| bn | 0.5444 | 0.7541 | +0.2096 | [+0.172, +0.247] | 300 |
| id | 0.5593 | 0.7364 | +0.1771 | [+0.139, +0.216] | 300 |
| hi | 0.4887 | 0.6608 | +0.1720 | [+0.130, +0.214] | 300 |
| fi | 0.6999 | 0.8465 | +0.1466 | [+0.111, +0.183] | 300 |
| **yo** | 0.5170 | 0.4494 | **−0.0676** | [−0.158, +0.026] | 119 |

## 3. H1a — resource dependence: **NULL**

| association | ρ (Spearman) |
| --- | --- |
| (dense − BM25) vs log CC-100 volume, k=17 | **−0.010** |
| BM25 alone vs log CC-100 volume, k=18 (EXP-008) | −0.059 |

Across a **~76,000× span** of pretraining volume (yo 1.1 MB → en 82 GB), neither
BM25's effectiveness nor the dense-over-BM25 advantage tracks how much data a
language contributed.

**H0a is retained.** Per protocol §1 this was pre-committed as a publishable
outcome and is reported as the finding, not reframed.

## 4. H0b — tokenization channel: **not retained, with the opposite sign**

| association (k=17, E5's XLM-R tokenizer) | ρ |
| --- | --- |
| (dense − BM25) vs tokens-per-character | +0.532 |
| **partial, conditioning on BM25** | **+0.376** |
| segmented scripts only (k=14) | +0.332 (partial +0.292) |
| BM25 alone vs tokens-per-character | **−0.565** |
| collinearity: tokens-per-char vs log resource | −0.390 |

Fragmentation does carry information about the gap beyond what BM25 explains, so
H0b is not retained. **But the direction is opposite to the standard account.**
The field attributes multilingual dense-retrieval failure to over-segmentation.
Here, heavier fragmentation predicts dense performing *relatively better*, and the
mechanism is visible in the same table: fragmentation damages the **lexical**
system (ρ = −0.565), widening the dense advantage rather than shrinking it.

## 5. The single most informative observation

> ⚠️ **OPEN QUESTION, NOT A FINDING — see ISSUE-009 (resolved).** The coverage
> explanation below is **neither refuted nor supported**. LaBSE, the only encoder here
> declaring Yoruba, scored 0.2290 on yo *and* 0.2983 on sw — losing to BM25 on a
> language it fully covers. It is a uniformly weak retriever on this benchmark
> (a bitext/similarity model, not retrieval-trained), so it cannot test coverage at all.
> A valid test needs a **retrieval-trained** encoder that declares Yoruba; none of the
> four encoders in this study is both. Treat the paragraphs below as a hypothesis
> consistent with the data, not an established result.

**Yoruba is the only language where dense retrieval fails, and it is the only
language E5 does not declare support for.** Its CI includes zero, so even that
failure is not clearly distinguishable from no difference.

What predicts dense retrieval breaking down in this study is **declared coverage**,
not how low-resource a language is. Telugu (536 MB CC-100) and Swahili (332 MB) are
both far lower-resource than many languages here and both show large *positive*
dense advantages (+0.287, +0.259).

This was argued in ISSUE-006 **before** these numbers existed, and the pipeline
flagged the Yoruba run automatically rather than pooling it.

## 5b. Error analysis — how the systems differ (EXP-014)

Failure categories from per-query metrics: `total_miss` (Recall@100 = 0, a recall
failure no reranker can repair) versus `deep_miss` (relevant found but ranked below
10, an ordering failure that *is* repairable).

**The dense advantage is overwhelmingly recall rescue, not reranking.** Across the 16
languages other than Yoruba, E5 rescues **7–26%** of queries from a miss category and
breaks **0–3%**. E5 nearly eliminates `total_miss` everywhere.

**Two languages behave qualitatively differently:**

- **zh** — BM25 `total_miss` = **0.513**. On half of all Chinese queries our reference
  retrieves nothing relevant in the top 100. This is not a weak baseline, it is a broken
  one, and it means the +0.519 Chinese "dense advantage" is mostly reference collapse.
- **yo** — the only language where dense **breaks more than it rescues** (0.227 vs
  0.143), and the only one where E5's `total_miss` (**0.210**) *exceeds* BM25's (0.084).
  Yoruba is a **recall** failure for the dense system, not a mild ranking decline. That
  is a different mechanism from what the aggregate suggested.

## 5c. Robustness of the primary result

| language set | pooled | I² | ρ vs log resource |
| --- | --- | --- | --- |
| all supported (k=17) | +0.2627 [+0.2240, +0.3013] | 94.0% | −0.010 |
| excluding zh (k=16) | +0.2464 [+0.2201, +0.2726] | 86.4% | −0.038 |
| excluding zh, ko, ja (k=14) | +0.2348 [+0.2101, +0.2594] | 82.9% | −0.101 |

The pooled effect stays within **+0.235 to +0.263** and the **H1a null holds in every
variant**. The headline does not depend on the languages where our reference is
weakest. Dropping zh/ko/ja also reduces I² from 94% to 83%, confirming those three
carry much of the between-language heterogeneity.

Per protocol, **k=17 remains the pre-registered primary**; these are reported as
sensitivity analyses, not as a re-selected headline.

## 6. Measurement-validity findings

These concern the benchmark rather than the systems, and matter independently.

**Pool bias is real and correlates with the variable under study (EXP-008).**
Unjudged documents in the top-10 range from **2.00 (en) to 9.01 (te)**, with
ρ = **−0.660** against log resource volume. Low-resource languages have most of
their ranked list scored non-relevant by default. Telugu has 9 of 10 top-ranked
documents unjudged. See ISSUE-007.

Mitigating for the primary result: on Telugu the exposure is nearly identical
across systems (BM25 9.01, E5 8.66), so the *paired* difference is not obviously
driven by differential pool exposure. The threat is to cross-language attribution.

**Uniform character 4-grams cost Chinese heavily.** BM25 zh nDCG@10 = 0.1922 versus
~0.48 for the published analyzer-based baseline. Meaningful units in Chinese are
1–2 characters. Per Amendment 2, `n` is **not** tuned per language, because that
would reintroduce exactly the resource-correlated treatment the uniform design
exists to avoid. See ISSUE-005.

## 7. Claims the evidence does NOT support

| Claim | Why not |
| --- | --- |
| "Dense retrieval underperforms in low-resource languages" | Contradicted: k=17 all positive, ρ = −0.010 vs resource |
| "Tokenizer fragmentation explains dense retrieval failure" | Sign is opposite; fragmentation hurts BM25 more |
| Any causal attribution | Constraint C1. Encoders differ in training data and objective as well as tokenizer |
| "zh/ko show dense is much better" | Both are languages where *our* BM25 is most handicapped |
| Generalisation beyond `multilingual-e5-small` | One encoder family so far; LaBSE and A/B outstanding |

## 7b. Post-audit corrections (Round 1)

The hostile audit (`docs/reviewer_audit.md`) and the completed robustness runs
changed four things. Recording them here because each one weakened or reframed a
claim that had already been written up.

**1. The headline was overclaimed (R1, CRITICAL).** The resource-level null rested on
$ho = -0.010$ at $k{=}17$, whose 95% CI is $[-0.488, +0.473]$. The design can only
resolve $|ho| \gtrsim 0.5$, so a true moderate association would have been invisible.
The claim now rests on the **per-language pattern** instead: the three lowest-resource
languages (sw, te, bn) show advantages of $+0.2594$, $+0.2873$, $+0.2096$ — comparable
to or larger than English ($+0.2163$) and Spanish ($+0.2255$), each with a paired CI
excluding zero. A degradation account predicts the reverse ordering.

**2. The registered $n{=}4$ is not optimal.** Full sweep: mean nDCG@10 of 0.4219
($n{=}2$), **0.5363** ($n{=}3$), 0.5154 ($n{=}4$), 0.4811 ($n{=}5$). $n{=}3$ is best in
12 of 18 languages. $n{=}4$ is retained because changing a registered parameter after
seeing results is the failure pre-registration prevents. **The conclusion survives the
strongest reference**: against $n{=}3$ the pooled advantage is $+0.2403$
$[+0.2082, +0.2724]$.

**3. Fragmentation does not explain Yoruba (EXP-016).** Its 27 broken queries have mean
fertility 2.028 against an all-query mean of 1.951, and the 14 queries *both* systems
miss have the **lowest** fertility (1.858). The tempting tokenization explanation is not
supported at query level.

**4. Calibration inverts the Yoruba reading (EXP-005/R5).** On the one like-for-like
comparison available, our dense system reproduces the published dense baseline almost
exactly (0.4494 vs published mDPR 0.444), while our lexical reference is far stronger
than the published one (0.5170 vs 0.406). Published BM25/mDPR shows dense *winning* on
Yoruba. So Yoruba is **not** evidence that dense retrieval is unusually bad there — it
is evidence that a uniform character $n$-gram reference is unusually *good* there.

## 7c. Generalisation to a second encoder family (R4, in progress)

BGE-M3 — a different model family, also retrieval-trained — on identical collections
and queries:

| lang | BM25 | E5 | BGE-M3 | E5 − BM25 | BGE-M3 − BM25 |
| --- | --- | --- | --- | --- | --- |
| sw | 0.4933 | 0.7527 | 0.7778 | +0.2594 | **+0.2845** |
| yo | 0.5170 | 0.4494 | 0.7074 | −0.0676 | **+0.1904** |

This addresses `reviewer_audit` **R4**, the paper's largest open weakness: every primary
conclusion previously rested on a single retrieval-trained encoder. The dense advantage
reproduces in a second family.

**The Yoruba row changes what can be said about Yoruba.** E5 loses there; BGE-M3 wins by
+0.1904 on the same collection and queries. Yoruba is therefore *not* a language where
dense retrieval cannot work — it is one where the particular encoder we happened to run
first does not.

**What this does not establish (ISSUE-010).** BGE-M3's declared coverage of Yoruba is
*undetermined*: its model card enumerates no language list, and its base (XLM-R, 94
languages) does not list Yoruba. So this cannot be read as confirming the coverage
hypothesis. If BGE-M3 in fact does not declare Yoruba, the result argues the **opposite**
— that declared coverage does not determine performance.

Remaining: hi, ru, en (~10 h at ~3 h/language for a 568M-parameter encoder on CPU).

## 8. Robustness still outstanding

- LaBSE (covers all 18 incl. yo) — **the decisive test of the coverage explanation**
- `--no-prefix` ablation (ISSUE-008)
- Encoders A/B for the tokenizer difference-in-differences (Amendment 1)
- BM25 word-tokenisation robustness run
- char n-gram sensitivity, n ∈ {2,3,5}
- Error analysis / failure categorisation

## 9. Statistical caveats carried throughout

- All cross-language correlations are **descriptive** at k≤18 (protocol §7). No
  p-values are attached to them and none licenses a causal reading.
- **I² = 94.0%** — between-language variation is large and real. It is *not*
  explained by resource volume. The pooled value must not be read alone.
- Dropping unsegmented scripts weakens the H0b association from +0.532 to +0.332;
  zh, ja and th are influential.
- Yoruba contributes only 119 queries and is down-weighted automatically by the
  random-effects model rather than excluded by hand.
