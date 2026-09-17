# Novelty Audit — Adaptive Retrieval Gating Economics

**Date:** 2026-08-11
**Method:** Hostile. The objective was to *disprove* the novelty of our own candidate
contribution, not to defend it.

# VERDICT: NOVELTY NOT ESTABLISHED — DO NOT PROCEED WITH THIS QUESTION

This triggers stop conditions from the project protocol §48:
*"the closest prior work already solves the same problem"* and
*"novelty cannot be established."*

Per §18, the correct response is to **redesign the research question**, not to
proceed while describing the work as novel.

---

## 1. The candidate contribution under audit

From `docs/research_question.md` (provisional):

> Adaptive retrieval gates calibrate their threshold against a target retrieval
> *rate*, not against *cost*. Because a draft-based gate spends generation compute to
> save retrieval compute, the cost-optimal threshold depends on the deployment's
> generation:retrieval cost ratio. Published thresholds are therefore mis-set off
> their (undisclosed) evaluation regime, and the policy ordering may invert.

## 2. Closest prior work

### Closest — Qian et al., *When Should Active RAG Retrieve? A Budget-Aware Evaluation of Utility, Calibration, and Cost*

- **Status:** `VERIFIED` (arXiv HTML fetched 2026-08-11)
- **arXiv:** 2607.24010v1, submitted **2026-07-27** — two weeks before this audit
- **Authors:** Pin Qian, Su Wang, Chong Peng, Junxian You, Lifei Liu, Haoran Yu,
  Yihang Chen, Xiaochong Jiang

This paper independently makes essentially our argument. Point-by-point:

| Our intended claim | Their prior coverage | Survives? |
| --- | --- | --- |
| Gates pay a pre-decision cost that retrieval-rate budgets ignore | Cost decomposition (Eq. 3) separates pre-decision trigger cost `C_pre`, skip cost, and use cost, **varying by router family**. Figure 1 shows "evidence-usage budgets do not fully determine deployment cost because trigger families pay different pre-decision costs." | **NO** |
| The field should calibrate/report against cost, not rate alone | Conclusion recommends reporting "cost decompositions rather than only retrieval rates." | **NO** |
| Thresholds do not transfer off their calibration set | Measured: "Nominal 50% budget thresholds violate targets in **28.6%–65.7%** of random splits." | **NO** |
| Simple uncertainty baselines are competitive | "Simple uncertainty baselines rival learned utility routers." Independently corroborated by Moskvoretskii et al. (2501.12835). | **NO** |
| Cost-aware accounting changes conclusions | "Trigger costs vary substantially; cost-aware accounting changes conclusions." | **NO** |

They also evaluate **seven trigger families** across three multi-hop QA datasets using
**1.5B–3.1B open instruction models** — precisely the model class this hardware can run.
They ran part of their evaluation CPU-only. Our hardware advantage is not an advantage.

### Second closest — Wang, Wei & Ling, TARG (arXiv 2511.09803)

Occupies the training-free gating-signal lane. Confirmed: calibrates τ via the dev-set
empirical CDF to hit retrieval budget ρ, and discloses no hardware. Our observation
about its non-disclosure is correct but is now merely a supporting remark, not a
contribution.

### Third closest — Moskvoretskii et al. (arXiv 2501.12835)

35 adaptive retrieval methods, 6 datasets, 10 metrics including efficiency, public code.
Closes the benchmarking lane.

### Fourth — the fallback axes, also occupied

| Fallback we considered | Occupied by |
| --- | --- |
| "Measure real wall-clock/energy on disclosed hardware" | *Energy-Efficient On-Device RAG on a Mobile NPU* (2606.11257) — reports a 120-query batch at **19 min NPU / 76 min CPU / 127 min GPU**, i.e. exactly the hardware-regime contrast we planned to supply |
| "Energy cost of RAG techniques" | *On the Effectiveness of Proposed Techniques to Reduce Energy Consumption in RAG Systems: A Controlled Experiment* (2601.02522) |
| "Diagnose where inference energy goes" | *Where Do the Joules Go?* (2601.22076) |
| Generic "efficiency metrics mislead" | *The Efficiency Misnomer*, ICLR 2022 (2110.12894) |

## 3. The ten hostile questions

1. **Closest existing paper?** Qian et al. 2607.24010.
2. **Second / third?** TARG 2511.09803; Moskvoretskii 2501.12835.
3. **Is our method actually different?** Only in residue: hardware-parameterised
   sensitivity of the cost ratio, which 2607.24010 holds as fixed constants and names
   in its limitations ("omits deployment-side latency, dollar, and energy costs").
4. **Is the difference scientifically meaningful?** Marginally. It converts a stated
   limitation of a two-week-old paper into a variable. That is a *future-work paragraph*,
   not a contribution.
5. **Merely an engineering combination?** Largely yes — instantiating a published cost
   model on measured hardware constants.
6. **Has the exact combination been tested?** The decomposition yes; the hardware sweep
   not located. But see (4).
7. **Has the same hypothesis been tested?** Yes in substance — cost-aware accounting
   changing conclusions is their reported finding.
8. **What paper would a reviewer cite to reject us?** 2607.24010, decisively. Also
   2606.11257 for the hardware-regime measurement.
9. **What experiment would falsify our contribution?** Re-running 2607.24010's cost
   decomposition with two hardware constant-sets. If the ordering is stable, we have
   nothing; if it inverts, we have their Figure 1 with a different x-axis.
10. **Honest scale of contribution?** Incremental. Not sufficient for a strong IEEE
    submission on its own.

## 4. Required audit table

| Existing Work | Similarity | Difference | Scientific Importance | Risk |
| --- | --- | --- | --- | --- |
| Qian et al. 2607.24010 | **Very high** — same problem, same framing, same model scale | We would vary hardware cost constants they fix | Low-moderate | **CRITICAL** |
| TARG 2511.09803 | High — the gate we would study | We do not propose a signal | Low | **CRITICAL** for signal claims |
| Moskvoretskii 2501.12835 | High — efficiency + self-knowledge comparison | Different cost axis | Low | **MAJOR** |
| On-Device RAG NPU 2606.11257 | Moderate-high — hardware regime energy/latency | Different task framing | Moderate | **MAJOR** |
| Efficiency Misnomer 2110.12894 | Moderate — methodological ancestor | Domain-specific instance | Low | **MAJOR** |

## 5. Why this was not caught earlier

It was — this is the audit working as designed. The saturation was flagged in
`literature_matrix.md` §E before any implementation, and no code, experiment, or
manuscript text was written against the unverified claim. **Cost of the error: zero
experiments.** That is the intended outcome of auditing before building.

## 6. What is NOT salvageable

- A new gating signal → TARG.
- A benchmark/comparison of adaptive retrieval → Moskvoretskii, RAGRouter-Bench.
- Rate-vs-cost calibration critique → Qian et al.
- Threshold transfer failure → Qian et al. (quantified).
- Hardware/energy regime measurement for RAG → 2606.11257, 2601.02522.

## 7. Recommended correction

Do **not** proceed with adaptive retrieval gating. The sub-field is absorbing new
entrants faster than a single-author CPU-only project can contest it: the decisive
competing paper appeared **two weeks** before this audit, and three of the five
occupied lanes were filled within the last eight months.

Structural lesson to carry into redesign: in a lane this hot, *"propose a method"* and
*"benchmark the methods"* contributions are consumed almost immediately. Durable
contributions under our constraints are more likely to be:

- a rigorous **failure-mechanism** study (why a method breaks, not that it does);
- work in a **genuinely under-served condition** where the crowd is not looking;
- a careful **negative or replication** result on a widely assumed claim.

The redesign must additionally satisfy the hard constraint in
`docs/environment_audit.md`: CPU-only, small open models, no API budget.

**Next action:** re-run Phase 1 on a new candidate direction, then re-enter this audit
*before* any implementation. No experiment is authorised until a question passes here.
