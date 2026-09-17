#!/bin/bash
cd "d:/Research Work2"
for L in sw bn hi th ko id fa ar fi ja zh ru es en de fr yo; do
  echo "=== $L $(date +%H:%M) ==="
  PYTHONIOENCODING=utf-8 "./.venv/Scripts/python.exe" scripts/encode_and_search.py --lang $L --model E5 2>&1 | grep -E "nDCG@10=|COVERAGE|not built"
done
echo "SWEEP COMPLETE $(date +%H:%M)"
