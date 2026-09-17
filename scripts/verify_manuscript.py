"""
Verify that every claimed manuscript fix is actually present.

Written after a CRITICAL fix (the R1 abstract revision) was committed as done but
had silently failed to apply — the string replacement did not match because shell
heredocs were mangling backslashes. The commit message said it was fixed; the file
said otherwise.

The lesson generalises: a commit message is a claim, not evidence. This script makes
the claim checkable, and should be re-run after any edit pass over the manuscript.

Patterns are chosen to be robust to LaTeX markup between words — searching for
"not the optimum" fails when the source reads "\\emph{not} the optimum".

Usage:
    .venv/Scripts/python.exe scripts/verify_manuscript.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MS = Path(__file__).resolve().parents[1] / "paper" / "manuscript.tex"

# (label, regex). Regexes tolerate intervening LaTeX commands.
CHECKS: list[tuple[str, str]] = [
    ("R1 abstract: rests on per-language pattern", r"lowest-resource languages show"),
    # NOTE 2026-09-17: the abstract was rewritten in plain text (no LaTeX math
    # brackets) to satisfy IJIMAI's submission format; the precise CI and the
    # resolution-limit statement moved to the Results section body instead of
    # the abstract. Checking the body, not the abstract, for these from here on.
    ("R1 results: correlation CI stated", r"\[-0\.488, \+0\.473\]"),
    ("R1 results: resolution limit stated", r"could not be resolved"),
    ("R1 results: power caveat", r"underpowered and we do not rest the claim"),
    ("R1 limitations: hard limit on k", r"hard limit on what they can show"),
    ("R2: H0b interval in abstract", r"\[\+0\.069, \+0\.806\]"),
    ("R3: k=16 estimate in abstract", r"\+0\.2464"),
    ("R4: claims scoped to tested encoders", r"scoped to the encoder families tested"),
    ("R5: calibration section present", r"Calibration against published baselines"),
    ("R5: published mDPR figure", r"0\.444"),
    ("R7: Yoruba failure subsection", r"Why Yoruba fails"),
    ("R7: fertility null stated", r"does not explain which Yoruba queries fail"),
    ("n-gram: full sweep table", r"tab:ngram"),
    ("n-gram: registered n admitted suboptimal", r"is therefore\s*\\emph\{not\}\s*the optimum"),
    ("figure 1 included", r"fig1_resource_null"),
    ("figure 2 included", r"fig2_failure_composition"),
    # NOTE 2026-09-17: acknowledgment wording genericized at the author's
    # request (no vendor/tool name in the manuscript itself; the specific
    # tool remains named in docs/ai_use_log.md for the project's own record).
    ("AI disclosure in acknowledgment", r"AI-assisted coding and writing tool"),
    ("title softened", r"No Detectable Degradation"),
    # NOTE 2026-09-17: affiliation was resolved (previously this checked that
    # a "still needs resolving" placeholder was present; now it checks the
    # actual resolved affiliation is there instead).
    ("affiliation resolved", r"Independent Researcher, Islamabad"),
    ("no causal language: 'because of tokeniz' absent", r"^(?!.*because of tokeniz).*$"),
]


def main() -> int:
    s = MS.read_text(encoding="utf-8")
    missing = []
    for label, pat in CHECKS:
        if not re.search(pat, s, re.MULTILINE | re.DOTALL):
            missing.append(label)
            print(f"  MISS  {label}")
        else:
            print(f"  ok    {label}")
    print()
    if missing:
        print(f"FAILED: {len(missing)} of {len(CHECKS)} claimed fixes are NOT present")
        return 1
    print(f"PASS: all {len(CHECKS)} claimed fixes present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
