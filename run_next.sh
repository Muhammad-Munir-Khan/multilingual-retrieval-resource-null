#!/bin/bash
cd "d:/Research Work2"
echo "=== LaBSE yo (decisive coverage test) $(date +%H:%M) ==="
PYTHONIOENCODING=utf-8 "./.venv/Scripts/python.exe" scripts/encode_and_search.py --lang yo --model LaBSE 2>&1 | grep -E "docs,|nDCG@10=|COVERAGE|Error|Traceback"
echo "=== E5 no-prefix ablation on te (closes ISSUE-008) $(date +%H:%M) ==="
PYTHONIOENCODING=utf-8 "./.venv/Scripts/python.exe" scripts/encode_and_search.py --lang te --model E5 --no-prefix 2>&1 | grep -E "nDCG@10=|Error|Traceback"
echo "=== LaBSE sw/te (low-resource anchor) $(date +%H:%M) ==="
for L in sw te; do
  PYTHONIOENCODING=utf-8 "./.venv/Scripts/python.exe" scripts/encode_and_search.py --lang $L --model LaBSE 2>&1 | grep -E "nDCG@10=|Error|Traceback"
done
echo "NEXT-QUEUE COMPLETE $(date +%H:%M)"
