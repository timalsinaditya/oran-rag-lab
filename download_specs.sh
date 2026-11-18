#!/usr/bin/env bash
# Download the O-RAN ALLIANCE specifications used by this project (180 files -> 166 indexed specs).
#
#   ./download_specs.sh                      # all IDs in catalog/user_ids.txt -> docs_full/
#   ./download_specs.sh 1150 158             # only these IDs
#   DEST=my_docs ./download_specs.sh         # other target folder
#
# By downloading you accept the O-RAN ALLIANCE terms of use (https://www.o-ran.org/specifications).
# Resumable: IDs already recorded in $DEST/.downloaded are skipped, so just re-run after an interruption.
# Zip archives (YANG models etc.) are unpacked. One request every ~1 s to be polite to the server.
set -u
cd "$(dirname "$0")" || exit 1
DEST=${DEST:-docs_full}
URL="https://specifications.o-ran.org/download?id="
mkdir -p "$DEST"; DONE="$DEST/.downloaded"; touch "$DONE"
for t in curl unzip file; do command -v $t >/dev/null || { echo "missing tool: $t"; exit 1; }; done

if [ $# -gt 0 ]; then ids="$*"; else ids=$(cat catalog/user_ids.txt); fi
total=$(echo $ids | wc -w); n=0; ok=0; skip=0; fail=0

for id in $ids; do
  n=$((n + 1))
  if grep -qx "$id" "$DONE"; then skip=$((skip + 1)); continue; fi
  tmp=$(mktemp -d)
  if (cd "$tmp" && curl -sfL --retry 3 --retry-delay 5 -OJ "$URL$id") && f=$(ls "$tmp") && [ -n "$f" ]; then
    kind=$(file -b "$tmp/$f")
    case "$kind" in
      Zip*)  if [[ "$f" == *.zip ]]; then unzip -oq "$tmp/$f" -d "$DEST" && msg="unzipped $f"
             else mv "$tmp/$f" "$DEST/" && msg="$f"; fi ;;           # .docx files are zip containers too
      HTML*) msg=""; ;;
      *)     mv "$tmp/$f" "$DEST/" && msg="$f" ;;
    esac
    if [ -n "$msg" ]; then echo "[$n/$total] id=$id -> $msg"; echo "$id" >> "$DONE"; ok=$((ok + 1))
    else echo "[$n/$total] id=$id -> got an HTML page instead of a file (open ${URL}$id in a browser)"; fail=$((fail + 1)); fi
  else
    echo "[$n/$total] id=$id -> download failed"; fail=$((fail + 1))
  fi
  rm -rf "$tmp"; sleep 1
done
echo "done: $ok downloaded, $skip already present, $fail failed -> $DEST/"
[ "$fail" -eq 0 ] || echo "re-run the script to retry the failed IDs"
