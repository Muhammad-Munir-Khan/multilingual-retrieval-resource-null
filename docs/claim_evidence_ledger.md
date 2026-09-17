# Claim–Evidence Ledger

Every claim this project makes, and what backs it. A claim without traceable evidence
does not enter the manuscript.

**Updated 2026-08-12.** Findings now exist. Section H records them with the evidence
each rests on, and Section F still lists what the evidence does **not** support.

Evidence codes: `ARTIFACT` = committed file under `results/`; `SOURCE` = external
primary source; `TEST` = known-answer verification; `NONE` = unsupported.

---

## A. Environment and feasibility

| ID | Claim | Type | Evidence | Verified | Location |
| --- | --- | --- | --- | --- | --- |
| A1 | No GPU is available; all work is CPU-only | infrastructural | `nvidia-smi` absent; `torch.cuda.is_available()` False | ✅ | `docs/environment_audit.md` |
| A2 | Dense encoding runs at ~9.6 passages/s here | empirical | `ARTIFACT` EXP-000 | ✅ | `results/EXP-000-throughput/metrics.json` |
| A3 | Dense encoding costs ~5,000× BM25 indexing on this host | empirical | `ARTIFACT` EXP-000 | ✅ | same |
| A4 | Full MIRACL (77.2M passages) is infeasible here (~2,265 h/encoder) | derived | `ARTIFACT` EXP-001 + A2 | ✅ | `results/EXP-001-corpus-sizes/metrics.json` |
| A5 | MIRACL corpora span a 271× size ratio (yo 49,043 → fr 13,306,000) | empirical | `ARTIFACT` EXP-001, raw API response committed | ✅ | same |
| A6 | Yoruba corpus is 49,043 passages | empirical | API **and** independent stream count agree | ✅ | EXP-001 + EXP-003 manifest |
| A7 | All 18 languages are obtainable; 16.18 GB total | empirical | `ARTIFACT` EXP-002 | ✅ | `results/EXP-002-miracl-survey/metrics.json` |

## B. Design decisions

| ID | Claim | Type | Evidence | Verified | Location |
| --- | --- | --- | --- | --- | --- |
| B1 | Equal-size sub-corpora are required for valid cross-language comparison | methodological | Argument from A5; retrieval difficulty scales with collection size | ✅ reasoning | `docs/experiment_protocol.md` §3 |
| B2 | Query count must be capped or judged-document fraction confounds languages | methodological | Derived from EXP-002: uncapped Arabic ≈59% judged vs Yoruba ≈2.4% | ✅ | protocol §4 |
| B3 | The 300-cap works in practice | empirical | Measured judged fractions: yo 1.92%, sw 5.02% | ✅ | EXP-003 manifests |
| B4 | Per-language analyzers would inject the confound under study | methodological | Argument: analyzer quality is resource-correlated | ⚠️ reasoning only, no measurement | `docs/open_issues.md` ISSUE-001 |
| B5 | Char 4-grams beat word tokenisation on every language tested | empirical | 5 languages measured vs published baselines | ✅ | protocol Amendment 2 |
| B6 | Two model pairs share a tokenizer exactly, enabling partial separation | empirical | Vocab sizes 250,002 / 250,002 and 119,547 / 119,547 | ✅ | Amendment 1 |
| B7 | Tokenizer fertility varies materially across families | empirical | yo: XLM-R 2.828 / mBERT 2.514 / LaBSE 1.994 | ✅ | Amendment 1 |

## C. Implementation correctness

| ID | Claim | Type | Evidence | Verified | Location |
| --- | --- | --- | --- | --- | --- |
| C1 | Length-bucketing preserves embedding↔docid alignment | correctness | `TEST` — 300 passages, max diff 1.7e-07, 0/300 misaligned, permutation non-trivial | ✅ | commit `216f5c6` |
| C2 | Random-effects pooling is implemented correctly | correctness | `TEST` — homogeneous → τ²=0, pooled exact; heterogeneous → I²=98% | ✅ | commit `a662a44` |
| C3 | Bootstrap CIs behave correctly | correctness | `TEST` — null contains 0; real effect excludes 0 | ✅ | same |
| C4 | Sub-corpus sampling is reproducible | correctness | SHA-256 of doc-ID list per language in manifests | ✅ | `data/processed/*/manifest.json` |
| C5 | No judged document is lost by sampling | correctness | `missing=0` for every language built so far | ✅ | EXP-003 manifests |

## D. Calibration against external baselines

| ID | Claim | Type | Evidence | Verified | Location |
| --- | --- | --- | --- | --- | --- |
| D1 | Our BM25 is not a weak baseline for space-delimited scripts | empirical | vs published Anserini: yo +17.6%, sw +28.0%, te +7.2%, hi +3.9%, bn −2.3% | ✅ | ISSUE-001, Amendment 2 |
| D2 | Korean remains ~10.6% below the official baseline | empirical | char 4-gram 0.4051 vs official 0.453 | ✅ | Amendment 2 — **must appear in Limitations** |
| D3 | The published baselines used for calibration are genuine | `SOURCE` | Pyserini 2CR page fetched | ✅ | `castorini.github.io/pyserini/2cr/miracl.html` |

## E. Corrections made to our own work

| ID | Claim | Type | Evidence | Verified |
| --- | --- | --- | --- | --- |
| E1 | `[^\w\s]` deleted Indic/Thai combining marks, shattering those scripts | correctness bug | Demonstrated: Bengali 2→8 tokens; category check Mn/Mc `isalnum()` False | ✅ ISSUE-004 |
| E2 | The bug would have inflated the apparent low-resource deficit | inference | Fixing it raised te 0.3035→0.5297, hi 0.2682→0.4760 | ✅ ISSUE-004 |
| E3 | EXP-000's "synthetic is pessimistic" caveat was wrong | correction | Real text 9.62 p/s vs synthetic 9.47 p/s (1.02×) | ✅ `environment_audit.md` §5.0 |

## H. Research findings (post-audit)

| ID | Claim | Evidence | Strength |
| --- | --- | --- | --- |
| H1 | Dense beats lexical in all 17 supported languages | `ARTIFACT` EXP-006; every paired CI excludes zero | **Strong** |
| H2 | Pooled advantage +0.2627 [+0.2240, +0.3013] | `ARTIFACT` EXP-006, random-effects | **Strong** |
| H3 | Result is not an artefact of a weak reference | Survives the strongest reference (n=3): +0.2403 [+0.2082, +0.2724] | **Strong** |
| H4 | Advantage does not track resource volume | Per-language pattern: sw/te/bn +0.2594 / +0.2873 / +0.2096 vs en +0.2163 | **Moderate** — the supporting correlation is underpowered (CI [-0.488, +0.473]) |
| H5 | Fragmentation predicts the gap, opposite sign | rho = +0.532 [+0.069, +0.806], partial +0.376 | **Moderate** — lower CI bound near zero; weakens to +0.332 without unsegmented scripts |
| H6 | Mechanism: fragmentation hurts lexical more | rho(BM25, tokens/char) = -0.565 | **Moderate** |
| H7 | Advantage is recall rescue, not reranking | `ARTIFACT` EXP-014: rescues 7–26%, breaks 0–3% | **Strong** |
| H8 | Pool bias confounded with resource level | rho = -0.660; unjudged@10 from 2.00 (en) to 9.01 (te) | **Strong** |
| H9 | Tokenizer effects not observationally isolable | `ARTIFACT` EXP-012: all retrieval encoders share XLM-R vocab | **Strong** |
| H10 | Pipeline reproduces published dense baseline | Yoruba like-for-like: ours 0.4494 vs published mDPR 0.444 | **Strong** |
| H11 | Yoruba reflects a strong reference, not weak dense | Our lexical 0.5170 vs published 0.406; our dense matches published | **Moderate** |

### Claims retired during the work

| Retired claim | Why |
| --- | --- |
| "Coverage explains dense breakdown" | Challenged by LaBSE (ISSUE-009), then by calibration (H11). Now an open question, not a finding. |
| "Dense retrieval fails on Yoruba" | H10/H11: our dense matches published mDPR there. Restated as "the one language where we cannot demonstrate an advantage". |
| "n=4 is the conservative choice" | Full sweep shows n=3 is stronger. Corrected. |
| "Efficiency claims are hardware-dependent" (v1 direction) | Pre-empted by prior work; whole direction retired before any experiment. |

## F. Claims NOT yet supported — do not write these

| Claim | Status |
| --- | --- |
| Dense retrievers underperform BM25 in low-resource languages | **CONTRADICTED** — 17/17 positive |
| Tokenizer fertility explains dense failure | **CONTRADICTED** — sign is opposite; and EXP-016 shows it does not explain Yoruba at query level |
| Declared coverage explains dense breakdown | **OPEN QUESTION** — no valid test exists among available encoders |
| Generalisation beyond the tested encoder family | **PENDING** — R4 (BGE-M3) running |
| Any causal attribution to tokenization | **PROHIBITED by constraint C1 regardless of results** |
| Our approach is novel | **CONDITIONAL** — `novelty_audit_v2.md` conditional pass, C1–C3 binding |

## G. Dangerous words requiring evidence before use

`first`, `best`, `state-of-the-art`, `significant`, `robust`, `generalizable`,
`efficient`, `causal`, `because`, `explains`, `due to`.

None are currently licensed. "Significant" is reserved for the pooled random-effects
estimate and may never describe a per-language CI (protocol §7).
