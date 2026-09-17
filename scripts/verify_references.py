"""
EXP-015 — Verify citation metadata against primary sources.

Project rules forbid citing anything known only from a search snippet. This queries
the **arXiv API** (authoritative metadata, not a search engine) for every arXiv work
the manuscript intends to cite, and records title/authors/date exactly as returned.

Anything not on arXiv (e.g. the original BM25 paper) is listed as requiring manual
verification against the publisher record — it is not guessed.

Usage:
    .venv/Scripts/python.exe scripts/verify_references.py
"""

from __future__ import annotations

import json
import subprocess
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "EXP-015-references"

ARXIV_API = "http://export.arxiv.org/api/query?id_list="
NS = {"a": "http://www.w3.org/2005/Atom"}

# arXiv id -> why the manuscript needs it
CITE = {
    "2210.09984": "MIRACL benchmark — our dataset",
    "2605.24556": "Amharic multilingual curse — closest prior work",
    "2511.19324": "What Drives Cross-lingual Ranking — adjacent CLIR analysis",
    "2012.15613": "Rust et al., How Good is Your Tokenizer — the identification design we cannot run",
    "1911.02116": "XLM-R / CC-100 — tokenizer and resource proxy",
    "2402.05672": "multilingual-e5 — primary encoder",
    "2007.01852": "LaBSE — coverage-anchor encoder",
    "2510.09947": "STRR tokenization metric",
    "2402.03216": "BGE-M3 — tokenizer-convergence evidence",
    "2501.12835": "Moskvoretskii adaptive retrieval benchmark — retired direction, cited in framing",
}

# Not on arXiv: must be verified against the publisher record by hand.
MANUAL = {
    "Robertson et al., Okapi at TREC-3 (1995)": "BM25 formulation — NIST TREC-3 proceedings",
    "MIRACL TACL 2023 version": "doi 10.1162/tacl_a_00595 — verify against MIT Press page",
}


def fetch(arxiv_id: str) -> dict:
    url = ARXIV_API + urllib.parse.quote(arxiv_id)
    req = urllib.request.Request(url, headers={"User-Agent": "research-refcheck"})
    with urllib.request.urlopen(req, timeout=60) as r:
        root = ET.fromstring(r.read())
    e = root.find("a:entry", NS)
    if e is None:
        return {"status": "NOT_FOUND"}
    title = " ".join((e.findtext("a:title", "", NS) or "").split())
    if title.lower().startswith("error"):
        return {"status": "NOT_FOUND"}
    authors = [a.findtext("a:name", "", NS) for a in e.findall("a:author", NS)]
    return {
        "status": "VERIFIED",
        "title": title,
        "authors": authors,
        "n_authors": len(authors),
        "published": e.findtext("a:published", "", NS),
        "updated": e.findtext("a:updated", "", NS),
        "doi": e.findtext("a:doi", "", NS) or None,
        "comment": " ".join((e.findtext("{http://arxiv.org/schemas/atom}comment", "", ) or "").split()) or None,
        "primary_category": (e.find("{http://arxiv.org/schemas/atom}primary_category").get("term")
                             if e.find("{http://arxiv.org/schemas/atom}primary_category") is not None else None),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    recs = {}
    print(f"{'arxiv':<12}{'status':<11}{'yr':<6}{'n_au':<6}title")
    print("-" * 96)
    for aid, why in CITE.items():
        try:
            r = fetch(aid)
        except Exception as e:
            r = {"status": "FETCH_ERROR", "error": repr(e)}
        r["why_cited"] = why
        recs[aid] = r
        yr = (r.get("published") or "")[:4]
        t = (r.get("title") or r.get("status", ""))[:60]
        print(f"{aid:<12}{r['status']:<11}{yr:<6}{str(r.get('n_authors','')):<6}{t}")

    payload = {
        "experiment_id": "EXP-015",
        "purpose": "verify citation metadata against the arXiv API (primary), replacing SNIPPET-ONLY status",
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "source": "http://export.arxiv.org/api/query — arXiv's own metadata service",
        "arxiv_verified": recs,
        "requires_manual_verification": MANUAL,
        "note": ("arXiv metadata confirms a preprint exists with the stated title, authors and "
                 "date. It does NOT confirm peer-reviewed venue. Any claim that a work appeared "
                 "at a specific conference or journal must be checked against that venue's own "
                 "record before it goes in the bibliography."),
    }
    (OUT / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    ok = sum(1 for r in recs.values() if r["status"] == "VERIFIED")
    print(f"\nverified {ok}/{len(CITE)} via arXiv API; {len(MANUAL)} require manual publisher check")
    print(f"wrote {OUT / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
