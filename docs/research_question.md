# Research Question (Phase 1 — PROVISIONAL)

**Date:** 2026-08-11
**Status:** ❌ **RETIRED 2026-08-11 — FAILED NOVELTY AUDIT.**

> This question did **not** survive `docs/novelty_audit.md`. It is superseded in
> substance by Qian et al., arXiv 2607.24010 (submitted 2026-07-27), which
> independently makes the rate-vs-cost calibration argument, quantifies threshold
> transfer failure, and evaluates seven trigger families at the same model scale.
>
> The document is retained **deliberately and unaltered below** as a record of a
> rejected hypothesis (protocol §11, §27: failed directions stay in the record).
> Nothing below should be read as an active research plan.

---

## 1. Problem

Adaptive retrieval gating decides, per query, whether a RAG system should retrieve at
all. The dominant family of methods (verified: TARG, arXiv 2511.09803) obtains that
decision by first generating a short **no-context draft** with the LLM and computing an
uncertainty score from its logits.

Such a gate therefore **spends generation compute in order to save retrieval compute.**

The field reports the resulting savings in units that hide this exchange rate:

- token counts (TARG §3.3 cost model is an expected-token equation);
- retrieval-call counts ("70–90% reduction");
- Δ wall-clock seconds relative to a baseline, on hardware that TARG **does not disclose**
  anywhere in its text or appendix (verified by fetching the paper).

Whether spending generation to save retrieval is profitable depends on the ratio between
the cost of a generated token and the cost of a retrieval call. That ratio is not a
property of the *method*; it is a property of the *deployment*. It differs by orders of
magnitude between:

- **Regime G** — GPU-served generation, remote/managed vector search over the network;
- **Regime C** — CPU-served generation on commodity hardware, local sparse/dense index.

In Regime G, generated tokens are fast and retrieval may cost a network round trip. In
Regime C, generated tokens are slow and a local BM25 lookup is nearly free. A gate that
pays tokens to avoid lookups is being evaluated on its best possible terms in Regime G.

**No located work measures where the break-even lies, or tests whether the published
efficiency ordering of gating policies survives a change of regime.**

## 2. Research question

> Does the efficiency advantage reported for draft-based adaptive retrieval gating over
> always-retrieve RAG depend on the deployment cost regime — specifically on the ratio of
> per-token generation cost to per-query retrieval cost — strongly enough that the ordering
> of gating policies by end-to-end cost **inverts** between a GPU-served/remote-retrieval
> regime and a CPU-served/local-retrieval regime, at matched answer quality?

## 3. Hypotheses

```
H0: The end-to-end cost ordering of retrieval policies
    {Always-RAG, Never-RAG, draft-based gate, retrieval-side gate}
    is invariant to the generation:retrieval cost ratio. The latency and
    compute savings reported for draft-based gating persist under CPU-served
    generation with a local index.

H1: The ordering is regime-dependent. There exists a measurable break-even
    value of the generation:retrieval cost ratio below which draft-based
    gating yields no end-to-end saving, or a net loss, relative to
    always-retrieve at matched answer quality.
```

H1 is falsifiable by direct measurement: if the gate still wins on this machine, H1 fails
for the regime that most favours it, and the result is reported as such.

**Pre-registered commitment:** the outcome is reported whichever way it falls. A null
result (H0 retained) is a publishable and honest finding about the robustness of existing
claims, and will not be reframed post hoc into a different question.

## 4. Why this machine is the right instrument

`docs/environment_audit.md` records the verified envelope: no GPU, i7-1165G7 (4c/8t),
31.65 GiB RAM, CPU-only PyTorch. Under most research questions this would be a crippling
limitation. Here it is the **experimental condition of interest** — this hardware sits at
the extreme end of the regime axis being studied, where generation is expensive and local
retrieval is cheap. The constraint is the instrument, not a compromise.

This is the honest reason this question was selected: it is one of the few questions in a
saturated area that this hardware can answer *better* than a GPU cluster could.

## 5. Scope

**In scope**
- English open-domain QA (dataset selection pending; candidates NQ-Open, TriviaQA, PopQA).
- Small open-weight generators (1B–3B, quantized, served via Ollama) — the realistic
  Regime-C generator class.
- Local retrieval: BM25 (sparse) and a small dense encoder (MiniLM/BGE-small class).
- Policies: Always-RAG, Never-RAG, a reimplemented draft-based uncertainty gate, and a
  retrieval-side (post-retrieval feature) gate.
- Cost measured as **wall-clock latency and component-resolved compute on disclosed
  hardware**, not as token proxies alone.

**Explicitly out of scope**
- Any training or fine-tuning (infeasible on this hardware; would invalidate the
  training-free framing).
- Multilingual and multimodal retrieval.
- Multi-turn agentic loops (cost compounds beyond the feasible budget).
- Claiming a new state-of-the-art gating *signal* — that lane is occupied (TARG) and will
  not be contested.

## 6. Expected contribution type

Primarily **empirical + methodological (evaluation validity)**, with a small **analytical**
component:

1. *Analytical* — a cost model for adaptive retrieval gating parameterised by measurable
   hardware quantities, yielding an explicit break-even condition.
2. *Empirical* — measurement of the real parameter values on disclosed commodity hardware,
   and a test of whether the policy ordering inverts.
3. *Methodological* — a reporting recommendation: what an adaptive-retrieval paper must
   disclose for its efficiency claim to be interpretable.

Deliberately **not** claimed: a novel gating signal, a new benchmark, or state-of-the-art
QA accuracy.

## 7. Known risks to this question

| Risk | Severity | Mitigation |
| --- | --- | --- |
| A reviewer calls the result "obvious engineering" | **HIGH** | The claim only becomes non-obvious if the ordering actually inverts and the break-even is quantified. If measurement shows no inversion, do not inflate — report the null. |
| Prior art exists in efficient-NLP on proxy-vs-wall-clock reporting | **HIGH** | Dedicated search is required in the novelty audit (`docs/literature_matrix.md` §G.3). This is the most likely source of rejection. |
| Reimplementing TARG faithfully without disclosed hyperparameters | **MEDIUM** | Reimplementation will be documented as such and clearly labelled a reimplementation, never as the authors' own numbers. |
| Small-model answer quality too low for the "matched quality" comparison to be meaningful | **MEDIUM** | Pilot measurement required before committing the design. |
| CPU generation too slow for an adequate evaluation-set size | **MEDIUM** | Throughput must be benchmarked first (`environment_audit.md` §5 is currently EVIDENCE REQUIRED); eval-set size then follows from the measured budget, not from a wish. |

## 8. Gate before proceeding

This question may **not** advance to methodology or implementation until:

- [ ] `docs/literature_matrix.md` §G actions 1–4 are complete;
- [ ] a dedicated search for hardware-regime/proxy-metric prior art has been run;
- [ ] `docs/novelty_audit.md` exists and the question has survived it;
- [ ] CPU throughput has been measured, so that the experiment scale is grounded in
      evidence rather than assumption.
