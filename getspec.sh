#!/usr/bin/env bash
# Usage: ./getspec.sh <id> [<id> ...]   e.g. ./getspec.sh 1150 158
# Downloads O-RAN specs (by the id in the download?id=N link) into docs/, unzips zips.
set -e
cd "$(dirname "$0")/${DEST:-docs}"
for id in "$@"; do
  tmp=$(mktemp -d)
  (cd "$tmp" && curl -sfL -OJ "https://specifications.o-ran.org/download?id=$id")
  f=$(ls "$tmp")
  kind=$(file -b "$tmp/$f"); [[ "$f" == *.zip ]] || kind="${kind/Zip/File}"
  case "$kind" in
    Zip*)  unzip -oq "$tmp/$f" -d . && echo "id=$id -> unzipped $f" ;;
    HTML*) echo "id=$id -> got an HTML page, not a spec (open it in the browser)";;
    *)     mv "$tmp/$f" . && echo "id=$id -> $f" ;;
  esac
  rm -rf "$tmp"
done
[ -n "$QUIET" ] || ls -1 .
