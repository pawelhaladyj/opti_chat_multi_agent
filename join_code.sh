#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-joined_code.txt}"

# Absolutna ścieżka do pliku wyjściowego (żeby go nie wciągnąć do środka)
OUT_ABS="$(cd "$(dirname "$OUT")" && pwd -P)/$(basename "$OUT")"

: > "$OUT"

find . -type f ! -path "./.git/*" -print0 |
while IFS= read -r -d '' f; do
  F_ABS="$(cd "$(dirname "$f")" && pwd -P)/$(basename "$f")"
  [[ "$F_ABS" == "$OUT_ABS" ]] && continue

  printf '===== %s =====\n' "$f" >> "$OUT"
  cat -- "$f" >> "$OUT"
  printf '\n\n' >> "$OUT"
done
