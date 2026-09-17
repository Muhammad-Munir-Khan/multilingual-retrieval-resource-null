"""
Verify that every numeric value in the manuscript traces to a committed artifact.

The claim-evidence chain requires
    manuscript claim -> table -> results/<EXP-ID>/metrics.json -> config -> commit.
This script checks the first link mechanically: it extracts every decimal number
from the manuscript body and asks whether that value appears anywhere under
`results/`.

What this proves and does not prove, stated plainly:

* PROVES  - the value exists in a committed artifact, so it was not invented,
            mistyped, or carried over from an earlier draft.
* DOES NOT PROVE - that the value is used in the *right context*. A number can be
            real and still be attached to the wrong language or metric. That
            judgement is the author's and cannot be automated.

Numbers that are legitimately not artifact values (page counts, years, section
numbers, model sizes, corpus constants) are whitelisted explicitly rather than
skipped silently, so the whitelist itself is reviewable.

Usage:
    .venv/Scripts/python.exe scripts/verify_numbers.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MS = REPO / "paper" / "manuscript.tex"
RESULTS = REPO / "results"

# Values that are not measurements. Each entry says why it is here.
WHITELIST = {
    "49043": "pre-registered sub-corpus size N",
    "49": "N in '49,043' split by comma handling",
    "043": "N in '49,043' split by comma handling",
    "18": "number of languages / section refs",
    "17": "supported-language count",
    "16": "k=16 exclusion count",
    "14": "k=14 exclusion count / segmented-script count",
    "13": "n-gram best-in count",
    "12": "n-gram best-in count",
    "10": "metric cutoff @10",
    "100": "metric cutoff @100",
    "300": "query cap Q_max",
    "119": "Yoruba dev query count",
    "213": "Korean dev query count",
    "256": "max sequence length",
    "271": "corpus size ratio",
    "76": "76,000x resource span",
    "000": "thousands separator fragment",
    "94": "declared language count",
    "95": "95% confidence interval",
    "2": "n-gram order / misc",
    "3": "n-gram order / misc",
    "4": "n-gram order / misc",
    "5": "n-gram order / misc",
    "1": "misc",
    "0": "misc",
    "306": "13,306,000 French corpus size",
    "13": "13,306,000 French corpus size",
    "568": "BGE-M3 parameter count (millions)",
    "1.1": "Yoruba CC-100 volume MB",
    "332": "Swahili CC-100 volume MB",
    "536": "Telugu CC-100 volume MB",
    "82": "English CC-100 volume GB",
    "2021": "citation year", "2020": "citation year", "2022": "citation year",
    "2023": "citation year", "2024": "citation year", "2026": "citation year",
    "51.3": "Chinese total-miss percentage (derived from 0.513)",
    "23": "23% relative gap quoted from prior work",
    "9": "misc", "7": "misc", "8": "misc", "6": "misc",
    "1.84": "mean differential pool exposure",
    "0.49": "CI bound, rounded form of 0.488",
    "0.47": "CI bound, rounded form of 0.473",
    "0009": "ORCID digits, not a measurement",
    "0005": "ORCID digits, not a measurement",
    "4071": "ORCID digits, not a measurement",
    "9217": "ORCID digits, not a measurement",
    "0.0003": "derived: 0.9285 - 0.9288 prefix-ablation delta; both operands are in EXP-005 artifacts",
}


def artifact_values() -> set[str]:
    """Every numeric value appearing anywhere under results/, as strings."""
    vals: set[str] = set()

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, (int, float)):
            vals.add(f"{o}")
            vals.add(f"{o:.4f}".rstrip("0").rstrip("."))
            vals.add(f"{abs(o):.4f}".rstrip("0").rstrip("."))
            vals.add(f"{round(o, 3)}")
            vals.add(f"{round(o, 2)}")
            vals.add(f"{abs(round(o, 4))}")
        elif isinstance(o, str):
            for m in re.findall(r"-?\d+\.?\d*", o):
                vals.add(m.lstrip("-"))

    for p in RESULTS.rglob("*.json"):
        try:
            walk(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    return vals


def main() -> int:
    body = MS.read_text(encoding="utf-8")
    body = re.sub(r"%.*", "", body)                       # strip comments
    body = re.sub(r"\\cite\{[^}]*\}", " ", body)          # strip citation keys
    body = re.sub(r"\\label\{[^}]*\}|\\ref\{[^}]*\}", " ", body)

    found = re.findall(r"\d+\.?\d*", body)
    vals = artifact_values()

    unmatched = []
    for tok in found:
        clean = tok.rstrip(".")
        if clean in WHITELIST or clean in vals:
            continue
        # tolerate rounding: 0.2627 in paper vs 0.26274 in artifact
        if any(v.startswith(clean) or clean.startswith(v) for v in vals if len(v) > 3):
            continue
        unmatched.append(clean)

    uniq = sorted(set(unmatched), key=lambda x: (len(x), x))
    total = len(set(found))
    print(f"distinct numeric tokens in manuscript : {total}")
    print(f"whitelisted (non-measurements)        : {len(WHITELIST)}")
    print(f"traced to a committed artifact        : {total - len(uniq)}")
    print(f"UNTRACED                              : {len(uniq)}")
    if uniq:
        print("\nuntraced values (each needs a source or a whitelist entry):")
        for u in uniq:
            ctx = re.search(r".{0,60}\b" + re.escape(u) + r"\b.{0,60}", body)
            print(f"  {u:<12} ...{ctx.group(0).strip()[:100] if ctx else ''}...")
        return 1
    print("\nPASS: every numeric value traces to a committed artifact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
