#!/usr/bin/env bash
# Official ORANSight-2.0 evaluation set (prnshv/ORANBench on Hugging Face, 1,500 questions) -> exact comparison.
# 1) retrieve now (fits on the GPU next to the index_v2 build), 2) once index_v2 is built, stop the Day-2 queue,
# 3) 7B answers the official set, 4) resume the v2 experiments on the 600-question subset.
cd "$(dirname "$0")/.." || exit 1
B=bench/run_bench.py; F="Warning|warn|Loading|Fetching|it/s\]|Batches"; S=tune_200
log() { echo "[$(date +%H:%M)] $*"; }

log "retrieve oranbench idxfull (top 10; reuses the 105 questions shared with sample_500)"
.venv/bin/python $B retrieve --set oranbench --index index_full --tag idxfull -k 10 --reuse sample_500__idxfull 2>&1 | grep -vE "$F" | grep -E "reused|saved|Error|Traceback"

log "wait for index_v2"
until [ -f index_v2/chunks.json ] && ! pgrep -f "^.venv/bin/python ingest.py" >/dev/null; do sleep 15; done
pkill -f "bash bench/queue_day2b.sh"; sleep 2     # (no-op when re-run)
pkill -f "^.venv/bin/python bench/run_bench.py (retrieve|answer) --set tune_200"
while pgrep -f "^.venv/bin/python bench/run_bench.py (retrieve|answer) --set tune_200" >/dev/null; do sleep 5; done
grep -E "SKIPPED|TOTAL|Saved" results/ingest_v2.log

log "answer oranbench full corpus k=5"
.venv/bin/python $B answer --set oranbench --ctx idxfull -k 5 --tag q7b_ragfull --reuse sample_500__q7b_ragfull 2>&1 | grep -vE "$F" | tail -1
log "answer oranbench no RAG (baseline on the official set)"
.venv/bin/python $B answer --set oranbench --tag q7b_base --reuse sample_500__q7b_base 2>&1 | grep -vE "$F" | tail -1
.venv/bin/python $B score | grep -E "^set|oranbench"

# resume the experiments (index_v2 already built)
log "retrieve idxv2 (dense + rerank, top 10)"
.venv/bin/python $B retrieve --set $S --index index_v2 --tag idxv2 -k 10 2>&1 | grep -vE "$F" | tail -1
log "answer k=5";  .venv/bin/python $B answer --set $S --ctx idxv2 -k 5 --tag q7b_v2_k5 2>&1 | grep -vE "$F" | tail -1
log "answer k=8";  .venv/bin/python $B answer --set $S --ctx idxv2 -k 8 --tag q7b_v2_k8 2>&1 | grep -vE "$F" | tail -1
log "retrieve idxv2 hybrid (dense + BM25 + rerank, top 10)"
.venv/bin/python $B retrieve --set $S --index index_v2 --tag idxv2h -k 10 --hybrid 2>&1 | grep -vE "$F" | tail -1
log "answer hybrid k=5"; .venv/bin/python $B answer --set $S --ctx idxv2h -k 5 --tag q7b_v2h_k5 2>&1 | grep -vE "$F" | tail -1
log "answer hybrid k=8"; .venv/bin/python $B answer --set $S --ctx idxv2h -k 8 --tag q7b_v2h_k8 2>&1 | grep -vE "$F" | tail -1
log "done"; .venv/bin/python $B score --set $S
touch logs/queue_official.done
