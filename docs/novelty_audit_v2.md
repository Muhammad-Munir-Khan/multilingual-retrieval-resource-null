# Novelty Audit v2 — Multilingual Retrieval Degradation

**Date:** 2026-08-11
**Subject:** `docs/research_question_v2.md`
**Method:** Hostile. Same protocol that retired v1.

# VERDICT: CONDITIONAL PASS — proceed to method design, under binding constraints

Unlike v1, the closest prior work does **not** already answer this question, and the
gap is named in the prior work's own limitations rather than asserted by us. But the
pass is conditional: three constraints below are binding, and violating any of them
returns this question to the failed state.

---

## 1. The blocking check, now resolved

The v1 audit left one BLOCKING item: **read Goworek et al. (arXiv 2511.19324) §5 in
full.** Done — PDF pp. 11–16 read directly (`VERIFIED`).

**What §5 "Linguistic Factors" actually does (Table 8):** Spearman correlations
between **linguistic similarity** and retrieval performance across **language pairs**,
for five feature families — *geographic, syntax, phonology, inventory, genealogical*
(lang2vec/URIEL-style typological vectors).

**Why this does not pre-empt us:**

| Dimension | Goworek et al. | This work |
| --- | --- | --- |
| Task | **CLIR** — query in language A, document in language B | **Monolingual retrieval within** a low-resource language |
| Predictors | **Pair-relative** typological *similarity* between two languages | **Language-intrinsic** properties: tokenizer fertility, STRR, pretraining volume |
| Datasets | CLIRMatrix, mMARCO, Large-Scale CLIR | MIRACL (cited by them as [44], not used) |
| Goal | Compare four *interventions* (translation, contrastive alignment, reranking, ANN) | **Decompose a deficit** into tokenization vs representation channels |

Typological *distance between two languages* and *how badly a tokenizer fragments one
language* are different quantities. Neither fertility nor pretraining volume appears
among their predictors.

**Their stated limitations actively support our framing (verbatim, p.14):**

- "the limited number of typologically distant and low-resource languages makes it
  difficult to fully characterise model behaviour in under-represented linguistic
  settings";
- "the linguistic analyses rely on aggregate typological resources and broad similarity
  metrics, **which may not capture all structural properties that are relevant**";
- future work should "extend these analyses to broader language coverage ...
  particularly for low-resource and typologically distant languages."

**A useful corroboration, not a threat:** their Table 8 shows **BM25 correlates strongly
with typological features** (geographic 80.5, syntax 74.3, genealogical 63.7 on
CLIRMatrix), while dense encoders correlate more weakly. This independently supports our
stated assumption that BM25 tracks language-intrinsic structural difficulty — and equally
confirms our caveat that BM25 **absorbs part of the tokenization channel**, making our
estimate conservative. Prior evidence supports the identification logic *and* its
limitation. Both must be reported.

## 2. The ten hostile questions

1. **Closest paper?** Alemneh, Mekonnen & de Rijke (2605.24556) — Amharic only.
2. **Second?** Goworek et al. (2511.19324) — CLIR, pair-relative typology. Cleared above.
3. **Third?** Rust et al. (ACL 2021) — the gold-standard disentanglement, for NLU, via retraining.
4. **Actually different?** Yes. No located work relates *language-intrinsic tokenization
   and resource measures* to *monolingual retrieval deficit* across multiple low-resource
   languages.
5. **Scientifically meaningful?** Yes, conditionally. The field routinely attributes
   multilingual retrieval failure to tokenization. That attribution is currently
   **asserted, not measured**, and is confounded with data scarcity.
6. **Merely engineering?** No — the contribution is measurement plus a decomposition
   under stated assumptions. But it is **not** a new method, and must never be sold as one.
7. **Exact combination tested?** Not located.
8. **Same hypothesis tested?** For NLU by Rust et al.; **not for retrieval**.
9. **Which paper rejects us?** 2605.24556 if our multi-language result adds nothing beyond
   "Amharic generalises"; Rust et al. if we overclaim causality. Both are avoidable by us.
10. **Falsifying experiment?** Fertility carries no association with the dense deficit once
    BM25 is conditioned on. **That is a real possible outcome and would be reported as the
    finding.**

## 3. Audit table

| Existing Work | Similarity | Difference | Importance | Risk |
| --- | --- | --- | --- | --- |
| Alemneh et al. 2605.24556 | High — same phenomenon | Single language; no isolation of tokenization | High | **MAJOR** |
| Goworek et al. 2511.19324 | Moderate — links language properties to retrieval | CLIR; pair-relative typology; interventions not decomposition | Moderate | **MODERATE** (was MAJOR; downgraded after reading §5) |
| Rust et al. ACL 2021 | Moderate — same confound | NLU not retrieval; requires retraining | High | **MAJOR** if we overclaim |
| MIRACL (TACL 2023) | Moderate — ships BM25/mDPR baselines | Per-language baselines exist; comparing them is not a contribution | Low | **MINOR** |
| Huang et al. 2608.02189 | Low on substance | Representation disentanglement via training | Low | **MINOR** (terminology only) |

## 4. Binding constraints of the conditional pass

**C1 — Never claim causal identification.** Rust et al. is the design we cannot run.
The manuscript must state this explicitly and frame results as associational. Violating
C1 is the single most likely cause of rejection.

**C2 — Generalisation alone is insufficient.** "The Amharic gap also appears in Yoruba
and Swahili" is a replication, not a contribution. The decomposition must carry the paper.

**C3 — Corpus size must be controlled.** Newly measured (EXP-001,
`results/EXP-001-corpus-sizes/metrics.json`): MIRACL corpora span a **271× ratio**
(Yoruba 49,043 → French 13,306,000 passages). Retrieval difficulty rises with collection
size independently of language. **Comparing raw nDCG@10 across MIRACL languages therefore
conflates language difficulty with collection size** — a confound that would invalidate
the central comparison.

Equal-size sampled sub-corpora are consequently a **validity requirement, not merely a
compute concession**. Protocol must be fixed in advance: retain all judged documents for
evaluated queries, fill to a fixed N by random sample under a recorded seed, and report
the protocol in full.

## 5. Feasibility, now measured rather than assumed

From EXP-000 (9.47 passages/s) and EXP-001 (verified sizes):

- Full MIRACL = 77,220,838 passages ⇒ **~2,265 h per encoder (~94 days). Infeasible.**
- Six smallest languages in full ⇒ ~60 h per encoder. Still impractical for multiple encoders.
- **Equal-size sub-corpora make the study feasible *and* more valid at once.** At 50k
  passages per language, 12 languages ⇒ ~17.6 h per encoder.

Feasibility and validity point the same way. This is the strongest structural argument
for the design and should be stated plainly in the paper, not hidden as a limitation.

## 6. Residual risks carried forward

| Risk | Severity | Status |
| --- | --- | --- |
| n≈12 languages underpowered for multi-predictor regression | **HIGH** | Unresolved. Regression stays descriptive; paired within-language tests must be primary. |
| Dense-side segmentation intervention confounded by distribution shift | **HIGH** | Unresolved. Not to be used as clean evidence. |
| Fertility ↔ resource-level collinearity | **HIGH** | Inherent. Report collinearity diagnostics; do not present partial effects as clean. |
| Sub-corpus sampling alters difficulty | **MEDIUM** | Mitigated by fixed pre-registered protocol + seed; must be reported. |
| Contribution judged incremental | **MEDIUM** | Depends on C2 being honoured. |

## 7. Verdict

**CONDITIONAL PASS.** Proceed to method design (Phase 5) under C1–C3.

Not authorised yet: any claim of novelty in the manuscript, and any experiment beyond
pilot scale, until the method design fixes the sampling protocol, the language set, the
encoder set, and the statistical plan **in advance of seeing results**.
