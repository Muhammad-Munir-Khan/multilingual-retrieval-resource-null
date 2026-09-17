"""
EXP-018 — Upgrade bibliography entries to their verified published versions.

`scripts/verify_references.py` emits every work as an arXiv preprint, because arXiv
metadata proves a preprint exists but not that a peer-reviewed version does. Four
entries carried `REQUIRES VENUE VERIFICATION`. Each has now been checked against the
ACL Anthology record (HTTP 200, title read from the page), so they are upgraded to
their published form.

One difference this caught: MIRACL's published title is *not* its arXiv title.

    arXiv : "Making a MIRACL: Multilingual Information Retrieval Across a
             Continuum of Languages"
    TACL  : "MIRACL: A Multilingual Retrieval Dataset Covering 18 Diverse Languages"

Citing the arXiv title while claiming the TACL venue would have been a fabricated
bibliographic record of exactly the kind the project rules prohibit.

Usage:
    .venv/Scripts/python.exe scripts/upgrade_bib_venues.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIB = REPO / "paper" / "references.bib"
REFS = REPO / "results" / "EXP-015-references" / "metrics.json"

# Verified 2026-08-12 against aclanthology.org (each returned HTTP 200 and the
# title was read from the page, not assumed).
VERIFIED = {
    "rust2020": {
        "key": "rust2021",
        "entry": "inproceedings",
        "title": "How Good is Your Tokenizer? On the Monolingual Performance of "
                 "Multilingual Language Models",
        "booktitle": "Proceedings of the 59th Annual Meeting of the Association for "
                     "Computational Linguistics",
        "year": "2021",
        "url": "https://aclanthology.org/2021.acl-long.243/",
    },
    "conneau2019": {
        "key": "conneau2020",
        "entry": "inproceedings",
        "title": "Unsupervised Cross-lingual Representation Learning at Scale",
        "booktitle": "Proceedings of the 58th Annual Meeting of the Association for "
                     "Computational Linguistics",
        "year": "2020",
        "url": "https://aclanthology.org/2020.acl-main.747/",
    },
    "feng2020": {
        "key": "feng2022",
        "entry": "inproceedings",
        "title": "Language-agnostic BERT Sentence Embedding",
        "booktitle": "Proceedings of the 60th Annual Meeting of the Association for "
                     "Computational Linguistics",
        "year": "2022",
        "url": "https://aclanthology.org/2022.acl-long.62/",
    },
    "zhang2022": {
        "key": "zhang2023",
        "entry": "article",
        # NOTE: differs from the arXiv title. Verified from the TACL record.
        "title": "MIRACL: A Multilingual Retrieval Dataset Covering 18 Diverse Languages",
        "journal": "Transactions of the Association for Computational Linguistics",
        "year": "2023",
        "url": "https://aclanthology.org/2023.tacl-1.63/",
    },
}


def main() -> int:
    refs = json.loads(REFS.read_text(encoding="utf-8"))["arxiv_verified"]
    authors = {}
    for aid, r in refs.items():
        if r.get("status") == "VERIFIED":
            first = r["authors"][0].split()[-1].lower()
            first = "".join(c for c in first if c.isalpha())
            authors[f"{first}{r['published'][:4]}"] = (" and ".join(r["authors"]), aid)

    text = BIB.read_text(encoding="utf-8")
    out = [
        "% references.bib",
        "% arXiv metadata from scripts/verify_references.py (EXP-015).",
        "% Published venues verified against aclanthology.org by",
        "% scripts/upgrade_bib_venues.py (EXP-018) - each returned HTTP 200 and the",
        "% title was read from the page.",
        "%",
        "% Entries still given as preprints have no verified published version.",
        "",
    ]
    for old_key, v in VERIFIED.items():
        au, aid = authors[old_key]
        out.append(f"@{v['entry']}{{{v['key']},")
        out.append(f"  title  = {{{v['title']}}},")
        out.append(f"  author = {{{au}}},")
        if v["entry"] == "inproceedings":
            out.append(f"  booktitle = {{{v['booktitle']}}},")
        else:
            out.append(f"  journal = {{{v['journal']}}},")
        out.append(f"  year   = {{{v['year']}}},")
        out.append(f"  url    = {{{v['url']}}},")
        out.append("}")
        out.append("")

    # Carry over the preprint-only entries unchanged.
    keep = [k for k in authors if k not in VERIFIED]
    for k in keep:
        au, aid = authors[k]
        r = refs[aid]
        out.append(f"% {r['why_cited']}")
        out.append(f"@misc{{{k},")
        out.append(f"  title  = {{{r['title']}}},")
        out.append(f"  author = {{{au}}},")
        out.append(f"  year   = {{{r['published'][:4]}}},")
        out.append(f"  eprint = {{{aid}}},")
        out.append("  archivePrefix = {arXiv},")
        if r.get("primary_category"):
            out.append(f"  primaryClass = {{{r['primary_category']}}},")
        out.append("}")
        out.append("")

    out.append("% Not on arXiv - manual publisher verification still required:")
    out.append("%   Robertson et al., Okapi at TREC-3 (1995) - BM25 formulation")
    BIB.write_text("\n".join(out), encoding="utf-8")

    print(f"upgraded {len(VERIFIED)} entries to published versions")
    print("key renames:", {k: v["key"] for k, v in VERIFIED.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
