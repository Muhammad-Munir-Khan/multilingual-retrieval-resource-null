# Hostile Reviewer Audit — Round 2

**Date:** 2026-08-13
**Subject:** `paper/manuscript.tex` at commit `0370561` (7 pages)
**Stance:** adversarial. Round 1 found a CRITICAL overclaim; this round assumes more
remain.

---

## Round 1 disposition

| ID | Round 1 finding | Status |
| --- | --- | --- |
| R1 | Headline null underpowered and overclaimed | **FIXED** — claim rebased on the per-language pattern; CI and power limit now stated in abstract, results and limitations |
| R2 | H0b association presented as stronger than it is | **FIXED** — interval reported, described as detected not established |
| R3 | Chinese pooled into the primary despite a broken reference | **FIXED** — $k{=}16$ estimate now in the abstract beside $k{=}17$ |
| R4 | Single-encoder generalisation | **SUBSTANTIALLY ADDRESSED** — second family on two languages; limitation reworded honestly |
| R5 | No comparison to published dense baseline | **FIXED** — calibration section; also inverted the Yoruba reading |
| R6 | Affiliation missing, wrong document class | **OPEN — author** |
| R7 | Yoruba unexplained | **FIXED** — failure analysis added; fragmentation ruled out |

---

## New findings

| ID | Sev | Finding |
| --- | --- | --- |
| S1 | **MAJOR** | The paper measures a benchmark defect but offers practitioners nothing to do about it |
| S2 | **MAJOR** | Generalisation rests on two languages, and they are not the informative pair |
| S3 | MINOR | Primary inference is a single metric on a single cutoff |
| S4 | MINOR | The pre-registration is claimed but not independently verifiable by a reviewer |
| S5 | SUGGESTION | The contribution is under-sold relative to what was actually measured |

### S1 — MAJOR: pool bias is diagnosed, not addressed

The paper shows unjudged-document rates ranging 2.00 (en) to 9.01 (te) and correlating
$\rho = -0.660$ with resource volume, then states this threatens cross-language
attribution — and stops.

A reviewer will ask the obvious question: *so what should be done?* Options exist and
none is discussed — condition on judged-set density, report bpref or another
pool-robust measure, or restrict cross-language claims to languages above a judgment
density threshold. Measuring a problem and leaving it is a weaker contribution than
measuring it and bounding its effect.

**Fix.** Either compute one pool-robust measure alongside nDCG@10 for the
cross-language analysis, or state explicitly which conclusions would change under
plausible pool-bias correction. The first is affordable — it needs no new retrieval,
only re-scoring existing runs.

### S2 — MAJOR: the generalisation pair is weak

BGE-M3 was run on Swahili and Yoruba: both low-resource, and one of them
(Yoruba) is the single anomalous language in the study. That is the least
representative possible pair for a claim about generality. The pre-declared subset
included English and Russian precisely to span the range, and they were not reached.

The paper is honest that the sweep is partial, but a reviewer will note that the two
languages completed are the two that most flatter a "dense works even in hard cases"
reading.

**Fix.** Run English. It is the resource extreme opposite Yoruba, and one language
would change this from "two low-resource languages" to "the range is spanned". This is
the single highest-value remaining experiment.

### S3 — MINOR: single metric, single cutoff

Primary inference is nDCG@10 alone. Recall@100 and MRR@10 are computed and reported
descriptively but never used inferentially. For a paper whose thesis is that
measurement choices change conclusions, resting inference on one cutoff is
uncomfortable — particularly since Recall@100 tells a visibly different story in
places (Hindi's prefix ablation raised Recall@100 while barely moving nDCG@10).

**Fix.** Report the pooled estimate under Recall@100 as a robustness line. Costs
nothing; the per-query values already exist.

### S4 — MINOR: pre-registration is asserted

The paper says the analysis plan was fixed before results existed. That is true and
the repository proves it, but a reviewer reading only the PDF has to take it on trust.

**Fix.** State the verifiable form: the protocol and its amendments are in the released
repository with commit history, and each amendment records whether results existed when
it was made.

### S5 — SUGGESTION: undersold

The paper leads with a null. Its more transferable findings are arguably the
methodological ones: that collection size must be equalised (271$\times$ range), that
judgment density is confounded with resource level, and that tokenizer effects are
currently unstudiable because the field converged on one vocabulary. Those constrain
how *anyone* runs such a study.

---

## Verdict

**Closer, but not ready.** No CRITICAL findings remain. S1 and S2 are both fixable
with work already affordable — S2 needs one encoder run, S1 needs only re-scoring.

The paper no longer overclaims. The remaining weaknesses are of scope and of
follow-through, not of honesty.
