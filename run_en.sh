#!/bin/bash
cd "d:/Research Work2"
# S2: English is the resource extreme opposite Yoruba. With yo/sw/te already done,
# adding en spans the full range and answers the audit's "least representative pair"
# objection. te was completed before reprioritising; hi and ru are deferred as
# mid-range and least informative for this question.
echo "=== BGEM3 en $(date +%H:%M) ==="
PYTHONIOENCODING=utf-8 "./.venv/Scripts/python.exe" scripts/encode_and_search.py --lang en --model BGEM3 2>&1 | grep -E "nDCG@10=|shard 1[12]|COVERAGE|Error"
echo "S2 COMPLETE $(date +%H:%M)"
