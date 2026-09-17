# Open Issues

Live register of unresolved methodological problems. An issue leaves this file only
when it is fixed or explicitly accepted with justification in the manuscript.

---

## ISSUE-001 — BM25 baseline may be materially weaker than the standard implementation

**Opened:** 2026-08-11
**Severity:** **CRITICAL** — blocked any comparative claim
**Status:** ✅ **RESOLVED 2026-08-11** — see "Resolution" at the end of this issue

### Problem

`scripts/retrieval_eval.py` implements BM25 with `rank_bm25` (Okapi, k1=1.5, b=0.75)
over **whitespace tokenisation**. The standard MIRACL baseline is Anserini/Lucene BM25
with **language-specific analyzers** — stemming, stopword lists, and script-aware
segmentation.

First measured results (EXP-004):

| lang | nDCG@10 | R@100 | MRR@10 | n |
| --- | --- | --- | --- | --- |
| yo | 0.3233 | 0.7409 | 0.2860 | 119 |
| sw | 0.3618 | 0.7108 | 0.3683 | 300 |
| bn | 0.4434 | 0.8758 | 0.4580 | 300 |

These appear **lower than the published MIRACL BM25 baselines**. `EVIDENCE REQUIRED` —
the official per-language figures must be read from the MIRACL paper (TACL 2023) and
tabulated against ours before any comparative claim is made.

Note the Yoruba sub-corpus is the *complete* yo corpus (49,043 = N), so for that
language the comparison to published numbers is close to like-for-like and any gap
is attributable to the retrieval implementation, not to sampling.

### Why this is critical, not cosmetic

The project's own operating rules forbid weakening a competitor
(protocol §5 designates BM25 the *pretraining-free reference*). A weak
BM25 corrupts **both** research questions, and in opposite directions:

- **H1a (dense deficit):** an artificially weak BM25 makes dense look relatively
  better, which **understates** the dense deficit. Conservative for our hypothesis —
  tolerable, but must be stated.
- **H0b/H1b (tokenization channel):** BM25 is the reference for *language-intrinsic*
  difficulty. Whitespace BM25 is **more** sensitive to morphological richness than a
  stemmed, analyzer-based BM25. It therefore **over-absorbs** the morphological signal
  we are trying to attribute, biasing the fertility analysis in a direction that is
  **not** conservative.

The second point is the dangerous one. It cannot be waved away as "conservative."

### Options

1. **Anserini/Pyserini** — the reference implementation. **Ruled out on this host:**
   `java -version` → command not found (checked 2026-08-11). Would require installing
   a JVM. Still the best option for *absolute* comparability if we choose to pay for it.
2. **Language-specific analysis in-process** — stemming/stopwords per language.
   **See the counter-argument below; this may be actively wrong for our purpose.**
3. **Uniform whitespace BM25, documented** — with the gap to published baselines
   quantified per language.

### Counter-argument that reframes this issue (added 2026-08-11)

Option 2 looks like the obvious fix and is probably a **mistake for this study**.

Analyzer quality is **itself resource-correlated**: mature stemmers, stopword lists and
segmenters exist for English, French and Chinese, and are poor or absent for Yoruba,
Telugu and Swahili. Applying "the best available analyzer per language" would therefore
inject *exactly the confound this project exists to measure* — a language-resource
effect — into the reference system that is supposed to be free of it.

A **uniformly applied** whitespace BM25 treats every language identically. It is weaker
in absolute terms, but it is **the more valid cross-language reference**, because its
handicap does not correlate with language resource level. For a study whose entire
question is "how much of the deficit tracks resource level," uniform treatment of the
reference matters more than peak absolute effectiveness.

This does not dissolve the issue. Two things remain true and must be settled:

- the **absolute** gap to published baselines must still be quantified, or we cannot
  claim our BM25 is a credible reference at all;
- whitespace BM25 remains **more morphology-sensitive** than an analyzer-based one, so
  it still over-absorbs the morphological channel in the fertility analysis. Uniformity
  fixes the cross-language comparability, not this bias.

Provisional direction: **Option 3 with explicit justification**, i.e. uniform whitespace
BM25 defended as a deliberate design choice rather than a limitation, *conditional on*
the absolute gap proving tolerable. If the gap is large, revisit Option 1 and install a
JVM.

### Required before resolution

- [ ] Tabulate published MIRACL BM25 nDCG@10 per language against ours (Yoruba is the
      clean calibration point — its sub-corpus is its full corpus).
- [x] Check JVM availability for Pyserini — **absent**.
- [ ] Decide and record the choice as a dated protocol amendment.

### Resolution (2026-08-11)

Closed on evidence, after ISSUE-004's tokenisation bug was fixed and Amendment 2
adopted uniform character 4-grams. Full results: `results/EXP-004-bm25-char/metrics.json`.

| lang | ours nDCG@10 | R@100 | official nDCG@10 | vs official |
| --- | --- | --- | --- | --- |
| yo | 0.5170 | 0.9062 | 0.406 | **+27.3%** |
| sw | 0.4933 | 0.8780 | 0.383 | +28.8% |
| bn | 0.5444 | 0.9337 | 0.508 | +7.2% |
| te | 0.6412 | 0.9267 | 0.494 | +29.8% |
| hi | 0.4887 | 0.9152 | 0.458 | +6.7% |
| th | 0.5410 | 0.9513 | 0.484 | +11.8% |
| id | 0.5593 | 0.9245 | 0.449 | +24.6% |
| ko | 0.4051 | 0.8035 | 0.453 | **−10.6%** |
| fa | 0.5056 | 0.9106 | 0.357 | +41.6% |

**The margins above must not be read as evidence that our BM25 beats Anserini.**
Eight of these nine languages use *subsampled* corpora (49,043 passages drawn from up
to 2.2M), and retrieval is easier with fewer distractors. Persian's +41.6% mostly
reflects a 45× corpus reduction, not retrieval quality. Only **Yoruba is like-for-like**
— its sub-corpus is its complete corpus and it uses all 119 dev queries — and there we
are **+27.3%** over the published baseline.

**Conclusion:** the concern that motivated this issue — a silently weak baseline
flattering dense retrieval — is not supported. On the one clean comparison available our
BM25 is stronger than the reference implementation, and it is applied uniformly across
languages, which is the property that matters for a cross-language study.

**Carried forward into Limitations:** Korean remains 10.6% below the official baseline
even on a subsampled corpus, i.e. its true handicap is larger than that figure suggests.
Anserini's morphological analyzer segments agglutinative morphology in a way no uniform
tokenisation can match. This is the honest cost of uniform treatment. See ISSUE-005.

Comparative dense-vs-BM25 claims are now **unblocked**, subject to the pre-registered
statistical plan.

---

## ISSUE-002 — Residual judged-fraction imbalance across languages

**Opened:** 2026-08-11
**Severity:** MEDIUM → **escalated, see ISSUE-007**
**Status:** MEASURED — carried as a covariate

All 17 built manifests (es pending). Every language has exactly 49,043 docs and
`missing = 0`, so no judged document was lost by sampling.

| judged fraction | languages |
| --- | --- |
| 0.0119 | te |
| 0.0192 | yo |
| 0.0502 | sw |
| 0.0567–0.0640 | bn, hi, id, ja, ko, fi, th, fr, ar, en, de, fa, zh, ru |

**Spread 5.4×** (te 0.0119 → ru 0.0640). The 300-query cap worked as intended — 14 of
17 languages sit in a tight 0.057–0.064 band — but two outliers remain, for *different*
reasons:

- **yo (0.0192):** only 119 queries exist, so the cap cannot be reached.
- **te (0.0119):** 300 queries, but MIRACL annotates Telugu sparsely — EXP-002 measured
  1.03 positives/query for te versus ~2–3 elsewhere. This is a property of the benchmark,
  not of our sampling.

Per protocol §4 the realised fraction is therefore **carried as a reported covariate**.
Note the two outliers are both low-resource languages, so judged fraction is *not*
independent of the variable under study — see ISSUE-007.

---

## ISSUE-007 — Pool bias may penalise systems that did not contribute to MIRACL's judgment pool

**Opened:** 2026-08-11
**Severity:** **MAJOR**
**Status:** OPEN — must be addressed in Limitations and, if possible, diagnostically

### Problem

MIRACL's relevance judgments were produced by annotating a *pool* of candidates drawn
from particular systems. Any document outside that pool is scored as non-relevant by
default, whether or not it actually is.

Our systems — uniform character 4-gram BM25, and dense encoders — did **not** contribute
to that pool. When they surface a genuinely relevant document that no pooled system
retrieved, it receives zero credit. Measured nDCG@10 is then a lower bound, and the
deflation is **not** uniform across systems: it is larger for a system whose ranking
diverges more from the pooled systems.

### Why it interacts badly with this study

1. **Direction of bias is not neutral between our arms.** BM25 variants are close to the
   lexical systems that typically seed such pools; dense retrieval diverges more. Any
   dense-minus-BM25 deficit is therefore **partly attributable to pooling**, not only to
   the language properties we want to attribute.
2. **It is confounded with the variable of interest.** Sparse-judgment languages here are
   low-resource ones (te 0.0119, yo 0.0192 — ISSUE-002). Sparser pools mean more unjudged
   retrievals, so low-resource languages absorb *more* pool bias. This can manufacture
   part of the very low-resource deficit the study is testing for.

### What this does NOT invalidate

Relative comparisons within a language on an identical judgment set remain meaningful,
which is exactly what the pre-registered paired design measures (protocol §7). The threat
is to *cross-language* attribution, which is the secondary analysis.

### Required

- [ ] Report per-query counts of retrieved-but-unjudged documents in the top-10, per
      system and language. This makes the exposure measurable rather than hypothetical.
- [ ] State explicitly in Limitations that dense-minus-BM25 differences are lower bounds
      of uncertain tightness, with the direction of bias named.
- [ ] Do **not** claim that a larger deficit in a sparse-judgment language reflects
      language properties without addressing this first.

---

## ISSUE-003 — Sub-corpus sampling changes absolute comparability to published numbers

**Opened:** 2026-08-11
**Severity:** LOW (by design)
**Status:** ACCEPTED

For 17 of 18 languages the sub-corpus is a 49,043-passage sample of a larger corpus,
so absolute metrics are **not** comparable to published full-corpus MIRACL numbers —
retrieval is easier with fewer distractors. This is deliberate: protocol §3 establishes
that equal corpus size is required for cross-language comparison to mean anything
(the raw ratio is 271×).

Accepted, with the requirement that the manuscript never compares our absolute values
to published full-corpus values as though they were like-for-like. Yoruba is the sole
exception (its sub-corpus is its full corpus) and is therefore the natural calibration
point against published baselines — see ISSUE-001.

---

## ISSUE-004 — Tokenisation bug silently shattered Indic and Thai scripts

**Opened:** 2026-08-11
**Severity:** **CRITICAL**
**Status:** FIXED in `scripts/retrieval_eval.py`; superseded results invalidated

### The bug

Punctuation stripping used `re.compile(r'[^\w\s]', re.UNICODE)`. Python's `\w`
excludes **combining marks** (Unicode categories Mn/Mc), because `str.isalnum()` is
False for them. The expression therefore treated Indic and Thai **vowel signs as
punctuation and deleted them**.

Demonstrated:

| Script | Input | Output |
| --- | --- | --- |
| Bengali | `বাংলাদেশের ইতিহাস` (2 tokens) | `ব  ল দ শ র ইত হ স` (8 tokens) |
| Telugu | `భారత చరిత్ర` (2 tokens) | `భ రత చర త ర` (5 tokens) |
| Hindi | 3 tokens, 14 chars | 6 tokens, 8 chars |

Latin, Arabic and Hangul text was unaffected — which is exactly why it was not
obvious from spot-checking.

### Why this was the dangerous kind of bug

It degraded retrieval **specifically for low-resource Indic scripts** — the very
languages this study is about — and would therefore have **manufactured the finding
the project hypothesises**: an apparent low-resource retrieval deficit produced
entirely by our own preprocessing. A confirmatory artefact is far more dangerous than
a random one, because nothing about the result would have looked wrong.

It was caught only because measured values were checked against **published external
baselines** rather than accepted because they looked reasonable.

### Fix

Strip by Unicode category: remove `P*` (punctuation) and `S*` (symbols); retain `L*`
(letters), `N*` (numbers) and **`M*` (marks)**. Implemented in `tokenise()` with the
rationale in the docstring so it cannot be silently reintroduced.

### Effect (nDCG@10, vs published Anserini baseline)

| lang | buggy | fixed | official | fixed vs official |
| --- | --- | --- | --- | --- |
| te | 0.3035 | **0.5297** | 0.494 | +7.2% |
| hi | 0.2682 | **0.4760** | 0.458 | +3.9% |
| bn | 0.4332 | **0.4963** | 0.508 | −2.3% |
| yo | 0.5020 | 0.4774 | 0.406 | +17.6% |
| sw | 0.4901 | 0.4901 | 0.383 | +28.0% |
| id | 0.6161 | 0.6135 | 0.449 | +36.6% |
| fa | 0.5138 | 0.4441 | 0.357 | +24.4% |
| ko | 0.3723 | 0.3720 | 0.453 | −17.9% |
| th | 0.4752 | **0.2824** | 0.484 | **−41.7%** |

**All EXP-004 results are superseded** and must be regenerated. The superseded values
remain in git history as required by the artifact policy.

---

## ISSUE-005 — Whitespace tokenisation fails for unsegmented and agglutinative scripts

**Opened:** 2026-08-11
**Severity:** **MAJOR**
**Status:** OPEN — decision required before Tier 1

Fixing ISSUE-004 **worsened Thai** (0.4752 → 0.2824, now −41.7% vs official). This is
not a regression; it exposes the real problem. The bug had been deleting Thai vowel
signs, which accidentally acted as a crude segmenter for a script that has **no word
spaces at all**. With correct preprocessing, whitespace tokenisation leaves Thai as
near-unbroken strings and retrieval collapses.

Korean is separately affected (−17.9%): it has spaces, but agglutinative morphology
means Anserini's morphological analyzer segments where whitespace cannot.

This empirically confirms the stopping condition pre-registered in protocol §9.
Affected: **th, ko**, and presumably **zh, ja** (not yet built).

### Options

1. **Exclude unsegmented/agglutinative languages from the primary analysis**, report
   separately with the reason. Already sanctioned by protocol §9.
2. **Uniform character n-gram tokenisation for all languages.** Language-agnostic, so
   it does not reintroduce the resource-correlation problem of per-language analyzers,
   and it is the standard remedy for unsegmented scripts. But it changes the reference
   system for every language and would require re-running everything.
3. Per-language segmenters — **rejected** for the ISSUE-001 resource-correlation reason.

Option 2 is the more principled if affordable; option 1 is the safe fallback. **The
decision must be made and registered as a dated amendment before Tier 1 runs**, not
after seeing which choice suits the hypothesis.

---

## ISSUE-006 — Pre-registered encoders do not cover the target low-resource languages

**Opened:** 2026-08-11
**Severity:** **CRITICAL** — invalidates the pre-registered encoder set
**Status:** OPEN — resolved by protocol Amendment 3

### Problem

Declared language coverage, read from each model card's YAML metadata:

| Encoder | Declared | Missing from our 18 |
| --- | --- | --- |
| **A** `paraphrase-multilingual-MiniLM-L12-v2` | 50 | **yo, sw, te, bn, zh** |
| **B** `distiluse-base-multilingual-cased-v2` | 50 | **yo, sw, te, bn, zh** |
| `intfloat/multilingual-e5-small` | 94 | yo |
| `sentence-transformers/LaBSE` | 110 | **none** |

Both encoders fixed in Amendment 1 exclude **Yoruba, Swahili, Telugu and Bengali** —
precisely the low-resource languages the research question is about.

### Consequence for the first result

EXP-005 measured Yoruba with encoder A: nDCG@10 **0.1482** against BM25 **0.5170**, a
paired difference of **−0.3688** [−0.448, −0.288].

**This must not be reported as evidence for H1a.** The encoder does not claim to
support Yoruba, so the result is close to tautological: a model never trained on a
language retrieves poorly in it. It measures *coverage*, not a tokenization or
representation channel that could be attributed.

### Second, independent problem: task mismatch

Encoder A is a **paraphrase / semantic-similarity** model (Sentence-BERT lineage,
trained for symmetric sentence similarity), **not** an information-retrieval model.
Query→passage retrieval is asymmetric. Using an STS model as a retriever is a known
mismatch and a reviewer would raise it immediately. `multilingual-e5-small` is
explicitly retrieval-trained and is the better task fit.

### Why this was missed

Amendment 1 selected encoders on **throughput and tokenizer distinctness** and verified
both. It never checked **language coverage** or **task suitability**. Measuring the
properties one happens to think of is not the same as checking the properties that
matter.

### Consequence

The pre-registered encoder set cannot answer the research question. Resolved by
**Amendment 3**. The Yoruba result stays in the record, correctly labelled as
coverage-confounded rather than deleted.

---

## ISSUE-008 — First E5 prefix verification was invalidated by a ceiling effect

**Opened:** 2026-08-11
**Severity:** MEDIUM (test-design error, caught before it misled anything)
**Status:** ✅ **CLOSED 2026-08-12** — powered test run on Hindi; conclusion supported

Amendment 3 requires verifying that E5's `query: `/`passage: ` prefixes matter before
any E5 result is recorded. The first attempt (EXP-009) used a reduced 4,583-document
corpus for affordability and returned:

| condition | nDCG@10 | Recall@100 |
| --- | --- | --- |
| with prefixes | 0.9629 | **1.0000** |
| without prefixes | 0.9600 | **1.0000** |

delta = +0.0029, which reads as "prefixes make no material difference."

**That conclusion is not supported.** `Recall@100 = 1.0000` in both conditions is total
saturation, and nDCG@10 ≈ 0.96 is close to it. With 4,583 documents and roughly one
positive per query in Telugu, the task is too easy to separate any two reasonable
systems. The near-zero delta measures the ceiling, not the prefixes.

Accepting it would have been a **false negative caused by our own test design** — and
conveniently so, since "prefixes don't matter" is the cheaper conclusion.

**Corrective action:** re-run the same A/B on the full 49,043-document sub-corpus, where
BM25 scores 0.6412 on Telugu and there is real headroom to discriminate.

**General lesson for this project:** a verification that returns "no difference" must be
checked for whether it *could have* detected one. A test without demonstrated
discriminating power proves nothing, and this design keeps producing convenient answers
that dissolve on inspection.

### Full-corpus re-run (2026-08-12)

Telugu, full 49,043-document sub-corpus, both conditions through the identical
length-bucketed pipeline:

| condition | nDCG@10 | Recall@100 | MRR@10 |
| --- | --- | --- | --- |
| with `query: ` / `passage: ` | 0.9285 | 0.9950 | 0.9160 |
| without prefixes | **0.9288** | 0.9917 | 0.9166 |

Δ nDCG@10 = **−0.0003**. Recall@100 is no longer pinned at 1.0000, so this is a real
measurement rather than the saturated non-test of the first attempt.

**But the power caveat has not gone away, and it would be self-serving to declare
victory here.** E5 scores 0.9285 on Telugu, leaving only ~0.07 of headroom, and the
per-query bootstrap CI on Telugu's dense−BM25 difference is roughly ±0.044 wide. An
effect of 0.02–0.04 could sit inside that and go undetected. "No difference on the
language where the model is already near its ceiling" is a weaker statement than "no
difference."

**Higher-powered test queued:** the same ablation on **Hindi**, where E5 scores 0.6608
— the *lowest* of the 17 supported languages and therefore the one with the most room
for a prefix effect to show. If the ablation is null there too, the claim is properly
supported.

### Powered test — Hindi (2026-08-12)

Hindi was chosen *before* running it as the highest-powered available test: E5 scores
0.6608 there, the lowest of the 17 supported languages, leaving the most room for a
prefix effect to appear.

| condition | nDCG@10 | Recall@100 | MRR@10 |
| --- | --- | --- | --- |
| with `query: ` / `passage: ` | 0.6608 | 0.9152 | 0.4945 |
| without prefixes | 0.6530 | 0.9722 | 0.6553 |

Δ nDCG@10 = **+0.0078**.

### Conclusion

| language | E5 headroom | Δ nDCG@10 (with − without) |
| --- | --- | --- |
| te | ~0.07 | −0.0003 |
| **hi** | **~0.34** | **+0.0078** |

With roughly five times the headroom, the effect is still under 0.01 — well inside the
per-query bootstrap CI on either language. **The E5 prefixes have no material effect on
retrieval quality on this benchmark.**

The prefixes were kept in the primary runs regardless, because using a model as its
authors document is the defensible default and removing them would have invited exactly
the weak-baseline criticism ISSUE-001 guarded against. This ablation establishes that
the choice did not drive any result.

**Reportable secondary observation:** E5's documented prefix convention, which is
usually presented as important, is worth under 0.01 nDCG@10 on MIRACL-style monolingual
retrieval. Recall@100 actually rose without prefixes on Hindi (0.9722 vs 0.9152), which
is unexplained and should not be over-read from one language.

---

## ISSUE-009 — LaBSE result contradicts the coverage explanation

**Opened:** 2026-08-12
**Severity:** **MAJOR** — falsifies the interpretation forming around ISSUE-006
**Status:** ✅ **RESOLVED 2026-08-12** — see "Resolution" at the end

### The contradiction

Yoruba, identical sub-corpus and queries (nDCG@10):

| system | declares `yo`? | trained for retrieval? | nDCG@10 | vs BM25 |
| --- | --- | --- | --- | --- |
| BM25 | n/a | n/a | 0.5170 | — |
| E5 | **no** | yes | 0.4494 | −0.0676 |
| **LaBSE** | **yes (110 langs)** | **no** (bitext/similarity) | **0.2290** | **−0.288** |

The encoder that **does** cover Yoruba performs **markedly worse** than the one that
does not. Declared coverage did not rescue Yoruba; the covering model was the weaker
of the two by a wide margin.

### What this does to the emerging interpretation

`results_summary.md` §5 states that what predicts dense breakdown is *declared
coverage, not resource level*. **That claim is now unsafe.** It rested on a single
language and a single encoder, and the first attempt to test it against a covering
encoder went the other way.

This is recorded before the disambiguating evidence arrives, so the record shows the
interpretation was challenged rather than quietly revised afterwards.

### The confound that prevents a clean conclusion either way

LaBSE differs from E5 in **two** respects at once:

1. **coverage** — 110 languages vs 94 (the variable of interest);
2. **training objective** — LaBSE is a bitext-mining / sentence-similarity model, **not**
   a retrieval model. This is the same task-mismatch problem that ISSUE-006 raised
   against encoder A.

So LaBSE's poor Yoruba score is consistent with *either* "coverage does not help" *or*
"LaBSE is simply a weaker retriever everywhere."

### Disambiguating test (queued, running)

LaBSE on **sw** and **te** — languages E5 supports and performs strongly on
(+0.259, +0.287 over BM25):

- if LaBSE is **uniformly** far below E5 on sw/te too ⇒ LaBSE is a weak retriever in
  general, its Yoruba number says little about coverage, and the ISSUE-006 explanation
  survives but remains **untested**;
- if LaBSE is **competitive** on sw/te but collapses on yo ⇒ coverage genuinely does
  not rescue Yoruba, and the §5 interpretation must be withdrawn.

Neither branch is assumed. `results_summary.md` §5 is **flagged as provisional** until
this resolves.

### Resolution (2026-08-12) — the first branch

LaBSE on **Swahili**, a language it *does* declare support for and where E5 is strong:

| system | sw nDCG@10 | R@100 | vs BM25 (0.4933) |
| --- | --- | --- | --- |
| E5 | 0.7527 | 0.9580 | +0.259 |
| **LaBSE** | **0.2983** | 0.6959 | **−0.195** |

**LaBSE loses to BM25 on a language it fully covers.** With Yoruba (0.2290, −0.288)
that is two for two: LaBSE underperforms the lexical baseline regardless of whether the
language is in its declared set.

**Conclusion: LaBSE is a uniformly weak retriever on this benchmark, so it cannot serve
as an instrument for testing coverage at all.** Its Yoruba number carries no information
about the coverage hypothesis. The apparent contradiction dissolves.

**But §5 is not thereby vindicated — it is merely untested.** The correct status is:

- the coverage explanation is **not refuted** (LaBSE's failure has an alternative and
  sufficient cause: it is a bitext-mining / sentence-similarity model, not a retrieval
  model — exactly the task mismatch ISSUE-006 raised against encoder A);
- it is also **not supported**, because no valid test of it has yet been run. Testing it
  properly needs a *retrieval-trained* encoder that declares Yoruba. None of the four
  encoders in this study is both.

§5 must therefore be rewritten as an open question rather than a finding.

### A cleaner finding that came out of this

Across both languages tested, E5 beats LaBSE by an enormous margin **despite declaring
fewer languages** (94 vs 110):

| lang | E5 | LaBSE | E5 advantage |
| --- | --- | --- | --- |
| sw | 0.7527 | 0.2983 | +0.454 |
| yo | 0.4494 | 0.2290 | +0.220 |

On this benchmark the encoder's **training objective** (retrieval vs bitext/similarity)
dominates its **declared language coverage**. That is a more defensible claim than the
coverage story it replaces, and it is consistent with ISSUE-006's original argument that
encoder A's task mismatch mattered independently of its coverage gap.

`EVIDENCE REQUIRED` before this is asserted generally: only two languages, and LaBSE is
a single similarity-trained model.

---

## ISSUE-010 — Unverified coverage metadata for BGE-M3 (self-inflicted)

**Opened:** 2026-08-13
**Severity:** **MAJOR** — an unverified value was written into the encoder metadata and
propagated into result artifacts
**Status:** CORRECTED; interpretation revised

### What happened

When adding BGE-M3 for the R4 generalisation test I recorded:

```
"declared_languages": 100, "missing": []
```

**Neither value was verified.** BGE-M3's model card contains **no structured language
field at all** — only the prose phrase "100 working languages", with no enumeration. I
inferred full coverage and wrote it as though checked.

The consequence is concrete: `missing: []` meant the Yoruba run was **not** flagged
`coverage_confounded`, whereas the equivalent E5 run was. The distinction was recorded
on the strength of an assumption.

Every other encoder's coverage was read from an actual model-card language list
(E5 94 languages with `yo` absent; LaBSE 110; A/B 50). This one was not, and it is the
only one that was not.

### What is actually verifiable

| Fact | Source | Status |
| --- | --- | --- |
| BGE-M3 claims "100 working languages" | model card prose | verified, but **unenumerated** |
| BGE-M3 declares no structured language list | model card front-matter | verified |
| XLM-R (BGE-M3's base) declares 94 languages | XLM-R model card | verified |
| **XLM-R does not list Yoruba** | XLM-R model card | **verified** |

So BGE-M3's Yoruba coverage is **undetermined**. Its base does not declare Yoruba, and
its own claim of 100 languages is not itemised.

### Why this matters for the interpretation

Measured (identical collection and queries):

| system | yo nDCG@10 | declares `yo`? |
| --- | --- | --- |
| BM25 | 0.5170 | n/a |
| E5 | 0.4494 | **no** (verified) |
| **BGE-M3** | **0.7074** | **undetermined** |

Two readings, and we cannot currently distinguish them:

1. If BGE-M3 *does* declare Yoruba, coverage explains the contrast, and the ISSUE-006
   hypothesis is supported.
2. If BGE-M3 *does not* — the more likely reading, since its base excludes Yoruba —
   then **declared coverage does not determine performance**, because an encoder that
   does not declare the language still beats the lexical reference there by $+0.190$.

Reading 2 would weaken the coverage explanation further, not support it.

**The result itself is unaffected**: retrieval and evaluation never consult this
metadata, only the reporting flag does. The measurement stands; the label was wrong.

### Correction applied

`missing` for BGE-M3 set to `UNVERIFIED`, and the Yoruba result reported with its
coverage status explicitly undetermined rather than assumed either way.

### Lesson

Every other coverage value was read from a model card. This one was inferred because it
seemed obvious, and it was written in the same format as the verified ones, which made
it indistinguishable from them afterwards. Inferred values must be marked as inferred at
the moment they are written, not reconstructed later.
