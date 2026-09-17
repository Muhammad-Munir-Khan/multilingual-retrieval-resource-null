# Hostile Reviewer Audit — Round 1

**Date:** 2026-08-12
**Stance:** adversarial. The objective is to reject the paper, not to improve it.
**Subject:** `paper/manuscript.tex` at commit `6c2889e`

Severity: `CRITICAL` (must fix or withdraw) · `MAJOR` · `MINOR` · `SUGGESTION`

---

| ID | Sev | Location | Finding |
| --- | --- | --- | --- |
| R1 | **CRITICAL** | Title, Abstract, §Results, §Conclusion | The central null is **underpowered and overclaimed** |
| R2 | **MAJOR** | §Results, §Limitations | H0b's association is weaker than presented |
| R3 | **MAJOR** | Table~\ref{tab:main}, §Discussion | Chinese is pooled into the primary estimate despite a broken reference |
| R4 | **MAJOR** | throughout | Primary conclusions rest on **one** retrieval-trained encoder |
| R5 | MINOR | §Experimental Design | No comparison against MIRACL's own mDPR baseline |
| R6 | MINOR | title block | Affiliation missing; wrong document class for target venue |
| R7 | SUGGESTION | §Discussion | The most interesting case (Yoruba) is left unexplained |

---

## R1 — CRITICAL: the headline null is underpowered

**Finding.** The paper's title asserts that dense retrieval "Does Not Degrade with
Language Resource Level", and the abstract states "*no* association" on the strength of
$\rho = -0.010$ at $k = 17$.

**Evidence against.** The 95% confidence interval on that correlation is
**$[-0.488, +0.473]$**, a width of 0.961. At $k=17$ the study can only resolve
$|\rho| \gtrsim 0.5$:

| true $\rho$ | 95% CI at $k{=}17$ | excludes 0? |
| --- | --- | --- |
| 0.3 | $[-0.211, +0.682]$ | no |
| 0.4 | $[-0.100, +0.739]$ | no |
| 0.5 | $[+0.025, +0.791]$ | yes |

A true moderate association of $\rho = 0.4$ would be **undetectable** in this design.
The paper therefore reports *absence of evidence* and phrases it as *evidence of
absence*. This is the single most attackable claim in the manuscript, and the reviewer
is right.

**Aggravating.** The project's own protocol demotes cross-language correlations to
"descriptive", yet the title and abstract elevate one of them to the paper's main claim.
The manuscript contradicts its own registered analysis plan.

**Fix.** Two changes, both required:

1. **Stop resting the claim on the correlation.** A stronger and better-powered argument
   is already in the data: the three lowest-resource languages show advantages of
   $+0.2594$ (sw), $+0.2873$ (te) and $+0.2096$ (bn) — comparable to or larger than
   high-resource languages such as en ($+0.2163$) and es ($+0.2255$). A degradation
   account predicts the opposite ordering. That per-language pattern rests on paired
   bootstrap CIs that *do* exclude zero, and does not depend on a $k{=}17$ correlation.
2. **Report the CI and the power limit explicitly**, and soften the title.

**Verification.** CI recomputed by Fisher $z$; per-language values from
`results/EXP-006-analysis/`.

## R2 — MAJOR: H0b's association is weaker than presented

**Finding.** $\rho = +0.532$ is presented as a substantive finding, but its 95% CI is
$[+0.069, +0.806]$ — the lower bound is close to zero. The partial correlation
($+0.376$) is not accompanied by any interval at all, and dropping unsegmented scripts
moves it to $+0.292$.

**Fix.** Report the interval, state that the lower bound is near zero, and describe the
association as *detected but imprecisely estimated* rather than established.

## R3 — MAJOR: Chinese contaminates the primary estimate

**Finding.** The paper itself reports that the lexical reference retrieves nothing
relevant for **51.3%** of Chinese queries, then includes Chinese in the pre-registered
$k{=}17$ pooled estimate, where it is the largest single effect ($+0.5191$).

A reviewer will ask why a comparison the authors describe as "broken" is inside the
headline number.

**Fix.** Keep $k{=}17$ as the registered primary — changing it after seeing results is
worse — but report the $k{=}16$ estimate ($+0.2464$) *beside* it in the abstract rather
than only in a sensitivity table, and state plainly that the conclusion does not depend
on Chinese.

## R4 — MAJOR: single-encoder generalisation

**Finding.** All primary conclusions come from one retrieval-trained encoder
(multilingual E5 small). LaBSE was run on three languages and is not retrieval-trained.
The paper's claims are about "dense multilingual retrieval" in general.

**Fix.** Either narrow every general claim to the tested encoder, or run a second
retrieval-trained encoder. Given EXP-012, a second such encoder would share the
tokenizer but differ in training — which tests generalisation of the *effect* even
though it cannot isolate tokenization. **This is the single most valuable additional
experiment available.**

## R5 — MINOR: no mDPR comparison

MIRACL ships an mDPR baseline. The paper compares only against its own BM25. Positioning
would be stronger with the published dense baseline, at least on the languages where
sub-corpus sampling makes comparison meaningful.

## R6 — MINOR: submission mechanics

Affiliation is a placeholder; the draft uses `IEEEtran` rather than IEEE Access's own
class. Both are known and recorded, but both are desk-rejection risks.

## R7 — SUGGESTION: the interesting case is unexplained

Yoruba is the only failure and the paper says its cause is an open question. That is
honest, but a reviewer may see the most interesting result being left unresolved. A
targeted analysis of *what* E5 retrieves for Yoruba queries would strengthen it
substantially and costs no new encoding.

---

## Verdict

**Not ready for submission.** R1 alone would justify rejection: the title makes a claim
the design cannot support. R1–R3 are fixable by rewriting against evidence already
collected. R4 needs one more experiment.

The underlying work is sound; the **framing overreaches what the statistics support**.
