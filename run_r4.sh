#!/bin/bash
cd "d:/Research Work2"
# R4: does the effect generalise beyond one retrieval-trained encoder?
# Subset chosen BEFORE running to span the full resource range:
#   yo 1.1MB, sw 332MB, te 536MB, hi 2.5GB, ru 46GB, en 82GB
for L in yo sw te hi ru en; do
  echo "=== BGEM3 $L $(date +%H:%M) ==="
  PYTHONIOENCODING=utf-8 "./.venv/Scripts/python.exe" scripts/encode_and_search.py --lang $L --model BGEM3 2>&1 | grep -E "nDCG@10=|COVERAGE|Error|Traceback"
done
echo "R4 COMPLETE $(date +%H:%M)"
