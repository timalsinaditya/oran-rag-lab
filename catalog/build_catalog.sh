#!/usr/bin/env bash
# Build catalog.csv (id,status,filename,bytes) for O-RAN spec IDs WITHOUT downloading files.
# --max-filesize 1 makes curl abort right after reading headers (0 body bytes transferred).
# Resumable: IDs already in the CSV are skipped. Throttled to ~1 request/second.
# Usage: ./build_catalog.sh [first_id] [last_id]
cd "$(dirname "$0")"
OUT=catalog.csv; FIRST=${1:-1}; LAST=${2:-1176}
[ -f $OUT ] || echo "id,status,filename,bytes" > $OUT
for id in $(seq $FIRST $LAST); do
  grep -q "^$id," $OUT && continue
  h=$(curl -sL --max-filesize 1 -D - -o /dev/null --max-time 30 "https://specifications.o-ran.org/download?id=$id" | tr -d '\r')
  status=$(echo "$h" | grep -E '^HTTP' | tail -1 | awk '{print $2}')
  name=$(echo "$h" | grep -io 'filename=[^;]*' | tail -1 | cut -d= -f2)
  size=$(echo "$h" | grep -i '^content-length' | tail -1 | awk '{print $2}')
  echo "$id,${status:-ERR},${name},${size}" >> $OUT
  sleep 1
done
echo "done: $(grep -c ',200,.' $OUT) files found"
