#!/usr/bin/env bash
# Day 2 queue (7B): full-corpus run on all 1,500, then experiments on the 600-question subset (tune_200).
#   idxfull : 166 specs, 800/120 chunks (same chunking as the lab index)          -> q7b_ragfull
#   idxv2   : 166 specs, 400/60 chunks + header/footer/line-number strip + "[spec | section]" prefix
# Each retrieval saves the top 10 so different k can be tested without re-retrieving.
cd "$(dirname "$0")/.." || exit 1
B=bench/run_bench.py; F="Warning|warn|Loading|Fetching|it/s\]|Batches"
log() { echo "[$(date +%H:%M)] $*"; }

S=tune_200      # 600-question tuning subset (200/level of sample_500); the winner is re-run on all 1,500

# 1) confirm the full-corpus setup on all 1,500 questions (ORANSight-2.0 protocol)
log "retrieve sample_500 idxfull (top 10)"
.venv/bin/python $B retrieve --set sample_500 --index index_full --tag idxfull -k 10 2>&1 | grep -vE "$F" | tail -1
log "answer sample_500 full corpus k=5"
.venv/bin/python $B answer --set sample_500 --ctx idxfull -k 5 --tag q7b_ragfull 2>&1 | grep -vE "$F" | tail -1
.venv/bin/python $B score | grep -E "^set|sample_500"

# 2) chunking / k / hybrid experiments on the 600-question subset
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
