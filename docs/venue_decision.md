# Venue Decision

**Date:** 2026-08-12
**Deferred until now deliberately** — `docs/novelty_audit_v2.md` required the
contribution's strength to be established before a venue was chosen, so the paper would
not be shaped to fit a template picked too early.

---

## Recommendation: **IEEE Access** (primary), **IEEE/ACM TASLP** (alternative)

With one caveat the author must decide on: **IEEE Access charges a US$2,160 APC.**

---

## What this paper actually is

Being honest about the product determines the venue. This is **not** a new method, model,
or benchmark. It is a **measurement and methodology study** whose contributions are:

1. **H1a null** — the dense-over-BM25 advantage does not track pretraining resource
   volume (ρ = −0.010 across a ~76,000× span, 17 languages, robust to exclusions).
2. **H0b rejected with the sign reversed** — fragmentation predicts dense doing
   *relatively better*, because it damages the lexical system more (ρ(BM25, tokens/char)
   = −0.565).
3. **Pool bias measured and shown to be confounded with the study variable** — unjudged
   top-10 documents range 2.00 (en) to 9.01 (te), ρ = −0.660 against resource volume.
4. **Tokenizer effects in multilingual retrieval are close to unstudiable
   observationally** — every retrieval-trained multilingual encoder surveyed shares an
   XLM-R-derived vocabulary (EXP-012).
5. **Corpus-size control is a validity requirement, not a convenience** — MIRACL spans a
   271× size ratio, so raw cross-language comparison conflates language with collection
   size.
6. **Error analysis** — the dense advantage is *recall rescue* (7–26% of queries), not
   reranking.

Items 3–5 are contributions to **benchmark methodology**. They are arguably more novel
than 1–2 and are what a reviewer is least likely to have seen elsewhere.

## Candidates assessed

| Venue | Scope fit | Receptive to null results? | Cost | Verdict |
| --- | --- | --- | --- | --- |
| **IEEE Access** | Broad, all IEEE fields | **Yes** — empirical and measurement studies are in scope | **US$2,160** + tax | **Primary** |
| **IEEE/ACM TASLP** | Explicitly covers "document indexing and retrieval" and language modeling; emphasises reproducibility | Possible, but expects methodological novelty | **No APC** for standard publication | **Alternative** |
| IEEE TKDE | Data/knowledge engineering | Weaker fit — this is IR/NLP, not data engineering | No APC | Rejected on fit |

### Why IEEE Access is the primary target

- **Scope genuinely fits.** A measurement study correcting methodological assumptions is
  squarely publishable there; it does not need to claim state of the art.
- **Null results are placeable.** The central finding is a null, and top-tier venues
  systematically disfavour nulls. IEEE Access does not require a performance win.
- **Reported acceptance ~27% post-desk-review** (official figure), with desk rejection
  driven mainly by scope misfit and framing — both controllable here.
- **Reproducibility is our strongest asset** and is rewarded rather than assumed: full
  pipeline, fixed seeds, SHA-256-hashed corpus samples, a pre-registered protocol with
  four dated amendments, and every figure traceable to a committed artifact.

### Why TASLP is the alternative, not the primary

Its scope covers retrieval and it explicitly encourages publishing code and data to make
results reproducible, which suits this work. But it expects **methodological novelty**,
and this study's scale is modest by that journal's standards — 2 encoder families,
18 languages, 49,043 passages each, CPU-only. A null result at that scale is a hard sell
against papers proposing new architectures.

It is the right target **if the APC is prohibitive**, accepting a higher bar and a slower
review.

## The cost, stated plainly

Verified from IEEE Access's own page (2026-08-12):

- **US$2,160 per article**, plus applicable local taxes, no page limit.
- 5% discount for IEEE members; **20%** for members who are also Society members.
- A discount exists for authors in **low-income countries as classified by the World
  Bank**. `EVIDENCE REQUIRED` — whether the author's country qualifies must be checked
  against the current World Bank classification and IEEE's eligibility wording; it is
  **not** assumed here.
- **No general waiver** for unfunded authors.

For a sole, independent author without institutional funding this is a material sum, and
it is the author's decision, not mine. TASLP costs nothing to submit.

## Decision required from the author

1. **IEEE Access** (pay APC, better odds, faster) **or TASLP** (free, harder, slower)?
2. If IEEE Access — check IEEE membership status for the 5%/20% discount, and the
   low-income-country eligibility.

## Before submission, whichever is chosen

- [ ] Verify the venue's **current** template, page limit, and reference style from its
      own author pages — not from memory or a third-party summary.
- [ ] Verify the venue's **supplementary AI policy**. The IEEE baseline is already
      verified (`docs/ai_use_log.md`); societies may add requirements.
- [ ] Resolve the four outstanding author responsibilities (`docs/authorship.md`) — the
      drafted Acknowledgments asserts they were done.
- [ ] Supply the affiliation.

## Note on fit beyond IEEE

Stated for completeness, since recommending only within a constraint without naming it
would be misleading: the natural homes for this work are **SIGIR, ECIR, ACL, or EMNLP**,
where multilingual IR and benchmark-methodology papers are core business and null results
with strong measurement are more readily reviewed by specialists. The project brief
targets IEEE, so the recommendation above is made within that constraint — but the author
should know the constraint has a cost in reviewer fit.

## Addendum: target changed to IJACSA (2026-09-15)

The author has redirected the submission target to the **International Journal of
Advanced Computer Science and Applications (IJACSA)**, superseding the IEEE Access /
TASLP recommendation above. This section records the change and what it resets;
it does not retroactively justify it — the reasoning above for IEEE Access still
stands as the analysis that was done, it is simply no longer the chosen path.

**Verified from IJACSA's own pages (2026-09-15):** scope covers AI/ML/data
science/computational intelligence/network security; double-blind peer review;
~15% acceptance rate (self-reported); monthly publication; open access under
CC BY 4.0; an APC applies to accepted manuscripts (amount not stated on the
guidelines page — verify before submission); main body capped at 10 pages
excluding references/tables/figures; accepts .docx/.doc/.pdf/LaTeX, with
official Word and LaTeX templates provided; the LaTeX template uses
`\documentclass[conference, letterpaper]{IEEEtran}` (two-column, IEEE-style
numbered `[1]` citations) — a different class configuration from this
manuscript's current `[journal]` option. No more than 25% self-reuse of
previously published material is permitted; submissions are screened with
iThenticate. **Submission itself requires an anonymized PDF** (author names,
affiliations, and identifying information removed) for double-blind review —
this is a new constraint IEEE Access did not impose the same way.

This resets or re-opens several items:

- [ ] The `[journal]` IEEEtran option and current header block must change to
      the IJACSA-provided `[conference, letterpaper]` template (see
      `research_editing/revised/` for the converted draft).
- [ ] Abstract must fit IJACSA's stated 150–250 word guidance; the current
      abstract is denser than that and needs author sign-off on what to trim
      (see `research_editing/analysis/ijacsa-compliance.md`).
- [ ] A separate **anonymized submission copy** is required (author name,
      affiliation footnote, ORCID, and the acknowledgment's authorship
      attribution stripped) alongside the normal archival copy — this did not
      exist as a requirement under IEEE Access.
- [ ] The APC amount and any low-income-country waiver eligibility for IJACSA
      specifically must be verified from IJACSA's own submission portal;
      `EVIDENCE REQUIRED` until then. Do not assume the IEEE Access figure
      above applies.
- [ ] `docs/authorship.md`'s outstanding items (affiliation, final author
      responsibilities) still apply and are not satisfied by this change.
- [ ] IJACSA's AI-use disclosure policy has not been separately verified
      against the current wording in the manuscript's Acknowledgment section
      (verified only for IEEE in `docs/ai_use_log.md`); re-check before
      submission.

## Addendum 2: target changed again, to IJIMAI (2026-09-15)

The author has redirected the submission target a second time, to the
**International Journal of Interactive Multimedia and Artificial Intelligence
(IJIMAI)**, superseding the IJACSA addendum above. As before, this records the
change; it does not re-argue it.

**Verification status — materially weaker than the IJACSA pass, and this must
be read before submitting.** `ijimai.org` returned **HTTP 403 to every direct
fetch attempt** from this environment (WebFetch and a plain `curl` with a
browser user-agent both blocked — behavior consistent with Cloudflare bot
protection, not a problem specific to one tool). The official Word template
(authoritative per IJIMAI's own guidelines) and the official LaTeX template
could **not** be downloaded, unlike the IJACSA pass where the real template
zip was pulled and compiled directly. What follows was reconstructed from two
independent secondary sources that agree with each other, not from the
primary template files:

1. IJIMAI's own **Author Guidelines page**, read through a third-party
   read-only proxy (`r.jina.ai`) since direct access was blocked. This
   surfaced real content — including the actual template download URLs — but
   is not the same as reading the source HTML directly, and cannot be spot-
   checked further from here.
2. IJIMAI's **official Typst template**, hosted publicly on GitHub
   (`github.com/pammacdotnet/IJIMAI`) and on the Typst package registry —
   accessible because GitHub isn't behind the same block. This is source code,
   not a summary, so its structural claims are higher-confidence than (1).

**What the two sources agree on (higher confidence):**
- Mandatory sections beyond the usual body: **CRediT Authorship Contribution
  Statement**, **Data Statement**, **Declaration of Conflicts of Interest**,
  and **Acknowledgment**, in that order at the end of the paper.
- A dedicated **AI-use disclosure** is required (separate from grammar-check
  tools, which are exempted).
- **Diamond open access — no APC** (this is the reason the author gave for
  the switch, and it is corroborated by an independent third-party aggregator
  as well, though that aggregator is not a primary source either).
- Page length: "standard... 8 pages," hard cap "12 pages... without the
  potential annexes."
- References "numbered consecutively by order of appearance" — compatible
  with the numbered-citation IEEEtran style already used, no change needed.
- Submission accepts Word (authoritative), LaTeX, or Typst; LaTeX/Typst
  submissions go in as a compiled PDF, not source, at initial submission.

**What is genuinely unverified and must be checked by the author before
submission** (not assumed, not guessed at):
- The **actual page layout** the official Word/LaTeX template enforces
  (column count, margins, fonts, exact section-heading styling). The revised
  draft uses a generic two-column IEEEtran layout as a stand-in — this is a
  reasonable default, not a confirmed match.
- Current **impact factor / indexing claims** (a third-party aggregator states
  IF≈2.4, Scopus/SCIE indexing) — not verified against Clarivate/Scopus
  directly.
- **Scope fit.** IJIMAI's stated scope leans toward multimedia/AI techniques,
  ANNs, evolutionary computation, fuzzy logic; this paper is a multilingual
  IR measurement study with no multimedia component. It is plausibly in
  scope as general AI/CS work — IJIMAI publishes broadly in practice — but
  this is the author's judgment call to make in the cover letter, not
  something this review can certify.
- Peer review process/timeline and any editorial desk-reject criteria — not
  stated in what could be retrieved.

Given the verification gap, **the author should still obtain the real Word
template directly (a normal browser visit from the author's own machine will
very likely not hit the same block this sandboxed environment did) and run a
final formatting pass against it before submission** — treat
`research_editing/revised-ijimai/manuscript.tex` as a structurally-informed
draft, not a verified camera-ready match.

### Update, same day: the author obtained the real templates

The author downloaded both official templates directly from ijimai.org from
their own machine (confirming the guess above — the block was specific to
this sandboxed environment, not the files themselves) and supplied them:
`template_IJIMAI_18_12_2025-OTH.docx` (the authoritative Word template) and
`template_IJIMAI_Latex-OTH.zip` (containing `ijimai_article.cls`, `ijimai.bst`,
the required Libertinus font files, and the UNIR logo asset). This
supersedes nearly everything in the verification-gap note above.

`research_editing/revised-ijimai/manuscript.tex` was rebuilt directly on
these real assets (not reconstructed from secondary sources) and **compiles
successfully with LuaLaTeX** (bibtex + `ijimai.bst`), producing a 7-page PDF
using the actual required Libertinus fonts, the actual UNIR logo, and the
actual title/abstract/keywords box layout — verified visually against the
rendered PDF, not just checked for compiler exit code. The Word `.docx` was
read directly (extracted from its underlying XML, since the site block also
affects tooling that would render it) to confirm the exact mandatory
end-matter section order and wording, which is now implemented exactly:
**CRediT Authorship Contribution Statement → Data Statement → Declaration of
Conflicts of Interest → Acknowledgment (with Funding folded in, matching the
template's own placement)**, all using the CRediT role list and "No conflict
of interest exists" / "This research did not receive funding" phrasing given
verbatim in the official template.

**What remains open — now genuinely a content gap, not a verification gap:**
- A **required author biography with photo** (180–250 words) — cannot be
  written by an editor; commented out in the `.tex` file with a `[AUTHOR TO
  SUPPLY]` marker rather than fabricated.
- Funding, competing-interest, and CRediT role-list lines are drafted using
  the template's own suggested "none to declare" phrasing but marked
  `[AUTHOR TO CONFIRM]` — do not submit without checking these are actually
  true.
- Affiliation placeholder, unchanged from the original manuscript.
- xelatex specifically failed in this environment with an unrelated,
  reproducible MiKTeX CLI argument-parsing error unconnected to the
  manuscript content; lualatex (also a compatible engine per the class file)
  compiled cleanly and was used instead. Not expected to be an issue on the
  author's own machine, but worth knowing if xelatex is attempted there too.
