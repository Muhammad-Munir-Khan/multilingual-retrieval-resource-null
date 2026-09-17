#!/bin/bash
cd "d:/Research Work2"
for L in zh ru es en de fr yo; do
  echo "=== $L $(date +%H:%M) ==="
  PYTHONIOENCODING=utf-8 "./.venv/Scripts/python.exe" scripts/encode_and_search.py --lang $L --model E5 2>&1 | grep -E "nDCG@10=|COVERAGE|Error|Traceback"
done
echo "SWEEP-REST COMPLETE $(date +%H:%M)"
