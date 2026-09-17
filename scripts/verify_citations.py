"""
Verify the manuscript's citations against the bibliography.

Checks three things a reviewer would check:
  1. every \\cite key in the manuscript exists in references.bib
  2. every bib entry is actually cited (no padding)
  3. how many entries are published versions vs preprint-only

It does not re-verify the bibliographic metadata itself; that was done against the
arXiv API (EXP-015) and the ACL Anthology (EXP-018).

Usage:
    .venv/Scripts/python.exe scripts/verify_citations.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MS = REPO / "paper" / "manuscript.tex"
BIB = REPO / "paper" / "references.bib"


def main() -> int:
    ms = MS.read_text(encoding="utf-8")
    bib = BIB.read_text(encoding="utf-8")

    ms_nocomment = re.sub(r"(?<!\\)%.*", "", ms)
    cited = sorted({k.strip()
                    for grp in re.findall(r"\\cite\{([^}]*)\}", ms_nocomment)
                    for k in grp.split(",")})
    entries = re.findall(r"@(\w+)\s*\{\s*([^,]+),", bib)
    keys = {k.strip(): typ.lower() for typ, k in entries}

    missing = [c for c in cited if c not in keys]
    unused = [k for k in keys if k not in cited]
    published = [k for k, t in keys.items() if t in ("inproceedings", "article")]
    preprint = [k for k, t in keys.items() if t == "misc"]

    print(f"citations in manuscript      : {len(cited)}")
    print(f"entries in references.bib    : {len(keys)}")
    print(f"  published (venue verified) : {len(published)}  {sorted(published)}")
    print(f"  preprint only              : {len(preprint)}  {sorted(preprint)}")
    print()
    print(f"cited but missing from bib   : {missing or 'none'}")
    print(f"in bib but never cited       : {unused or 'none'}")

    ok = not missing and not unused
    print()
    print("PASS: bibliography and citations are consistent" if ok
          else "FAIL: bibliography and citations disagree")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
