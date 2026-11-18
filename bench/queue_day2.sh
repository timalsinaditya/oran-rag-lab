#!/usr/bin/env bash
# Day 2 experiment queue (7B generator, 600-question tuning subset bench/sets/tune_200.jsonl).
#   idxfull : 166 specs, 800/120 chunks (same chunking as the lab index)          -> q7b_ragfull
#   idxv2   : 166 specs, 400/60 chunks + header/footer/line-number strip + "[spec | section]" prefix
# Each retrieval saves the top 10 so different k can be tested without re-retrieving.
cd "$(dirname "$0")/.." || exit 1
B=bench/run_bench.py; F="Warning|warn|Loading|Fetching|it/s\]|Batches"
log() { echo "[$(date +%H:%M)] $*"; }

S=tune_200      # 600-question tuning subset (200/level of sample_500); the winner is re-run on all 1,500

# wait for the full-corpus index build, then replace its 1,500-question retrieval with the tuning subset
until [ -f index_full/chunks.json ] && ! pgrep -f "^.venv/bin/python ingest.py" >/dev/null; do sleep 20; done
sleep 10; pkill -f "^.venv/bin/python bench/run_bench.py retrieve --set sample_500 --index index_full"
while pgrep -f "^.venv/bin/python bench/run_bench.py" >/dev/null; do sleep 5; done

log "retrieve idxfull (800/120 chunks, top 10)"
.venv/bin/python $B retrieve --set $S --index index_full --tag idxfull -k 10 2>&1 | grep -vE "$F" | tail -1
log "answer full corpus k=5"; .venv/bin/python $B answer --set $S --ctx idxfull -k 5 --tag q7b_ragfull 2>&1 | grep -vE "$F" | tail -1

log "build index_v2"
CHUNK_TOKENS=400 OVERLAP=60 STRIP_HF=1 PREFIX=1 DOCS_DIR=docs_full INDEX_DIR=index_v2 \
  .venv/bin/python ingest.py 2>&1 | grep -vE "$F|Ignoring wrong" > results/ingest_v2.log
grep -E "SKIPPED|TOTAL|Saved" results/ingest_v2.log

log "retrieve idxv2 (dense + rerank, top 10)"
.venv/bin/python $B retrieve --set $S --index index_v2 --tag idxv2 -k 10 2>&1 | grep -vE "$F" | tail -1
log "answer k=5";  .venv/bin/python $B answer --set $S --ctx idxv2 -k 5 --tag q7b_v2_k5 2>&1 | grep -vE "$F" | tail -1
log "answer k=8";  .venv/bin/python $B answer --set $S --ctx idxv2 -k 8 --tag q7b_v2_k8 2>&1 | grep -vE "$F" | tail -1

log "retrieve idxv2 hybrid (dense + BM25 + rerank, top 10)"
.venv/bin/python $B retrieve --set $S --index index_v2 --tag idxv2h -k 10 --hybrid 2>&1 | grep -vE "$F" | tail -1
log "answer hybrid k=5"; .venv/bin/python $B answer --set $S --ctx idxv2h -k 5 --tag q7b_v2h_k5 2>&1 | grep -vE "$F" | tail -1
log "answer hybrid k=8"; .venv/bin/python $B answer --set $S --ctx idxv2h -k 8 --tag q7b_v2h_k8 2>&1 | grep -vE "$F" | tail -1

log "done"; .venv/bin/python $B score --set $S
