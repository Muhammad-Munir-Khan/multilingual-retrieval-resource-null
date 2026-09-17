#!/bin/bash
cd "d:/Research Work2"
ALL="yo sw bn hi te th id ko fi ar fa zh ja ru es en de fr"
echo "=== E5 no-prefix ablation on hi (higher-powered ISSUE-008) $(date +%H:%M) ==="
PYTHONIOENCODING=utf-8 "./.venv/Scripts/python.exe" scripts/encode_and_search.py --lang hi --model E5 --no-prefix 2>&1 | grep -E "nDCG@10=|Error|Traceback"
echo "=== BM25 word tokenisation, all 18 (pre-registered robustness) $(date +%H:%M) ==="
PYTHONIOENCODING=utf-8 "./.venv/Scripts/python.exe" scripts/retrieval_eval.py --tok word --langs $ALL 2>&1 | grep -E "nDCG@10=|FLAGGED"
for N in 2 3 5; do
  echo "=== BM25 char n=$N sensitivity, all 18 $(date +%H:%M) ==="
  PYTHONIOENCODING=utf-8 "./.venv/Scripts/python.exe" scripts/retrieval_eval.py --tok char --ngram $N --langs $ALL 2>&1 | grep -E "nDCG@10="
done
echo "ROBUSTNESS COMPLETE $(date +%H:%M)"
