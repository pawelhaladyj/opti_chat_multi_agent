#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-new_design.txt}"

# Absolutna ścieżka do pliku wyjściowego (żeby go nie wciągnąć do środka)
OUT_ABS="$(cd "$(dirname "$OUT")" && pwd -P)/$(basename "$OUT")"

: > "$OUT"

find . \
  -type d \( \
    -name .git -o \
    -name .venv -o \
    -name __pycache__ -o \
    -name .pytest_cache -o \
    -name .mypy_cache -o \
    -name .ruff_cache \
  \) -prune -o \
  -type f \( \
    ! -name "*.pyc" -a \
    ! -name "*.pyo" \
  \) -print0 |
while IFS= read -r -d '' f; do
  F_ABS="$(cd "$(dirname "$f")" && pwd -P)/$(basename "$f")"
  [[ "$F_ABS" == "$OUT_ABS" ]] && continue

  printf '===== %s =====\n' "$f" >> "$OUT"
  cat -- "$f" >> "$OUT"
  printf '\n\n' >> "$OUT"
done
