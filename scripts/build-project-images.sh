#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Turn curated picks from the raw archive into web-sized files the site ships.
#
# The raw archive lives in assets/img/projects/<project>/ and is gitignored.
# This script reads a picks file and writes renamed, resized JPEGs to the TOP
# level of assets/img/projects/, which IS committed and IS what the pages use.
#
# Picks file format, tab separated, one per line, comments with # ignored:
#   <project>\t<source-file>\t<role>\t<output-name>
# role is one of: hero, gallery, cover
#
#   bash scripts/build-project-images.sh picks.tsv
#
# Widths per role are set below. Never ship a source image far beyond its
# rendered size, but never sacrifice the photography either. Quality stays 72.
# ---------------------------------------------------------------------------
set -uo pipefail

PICKS="${1:?usage: build-project-images.sh <picks.tsv>}"
SRC="assets/img/projects"
OUT="assets/img/projects"
Q=72

W_hero=2000
W_gallery=1400
W_cover=800

made=0; skipped=0; missing=0

while IFS=$'\t' read -r proj file role name; do
  case "${proj:-}" in ''|\#*) continue;; esac
  [ -z "${name:-}" ] && continue

  in="$SRC/$proj/$file"
  if [ ! -f "$in" ]; then echo "  MISSING $in"; missing=$((missing+1)); continue; fi

  case "$role" in
    hero)    w=$W_hero;;
    gallery) w=$W_gallery;;
    cover)   w=$W_cover;;
    *) echo "  unknown role '$role' for $name"; continue;;
  esac

  out="$OUT/$name"
  if [ -f "$out" ]; then echo "  have    $name"; skipped=$((skipped+1)); continue; fi

  # Never upscale. If the source is narrower than the target, keep it as is.
  sw=$(sips -g pixelWidth "$in" 2>/dev/null | awk '/pixelWidth/{print $2}')
  [ -z "$sw" ] && { echo "  UNREADABLE $in"; missing=$((missing+1)); continue; }
  if [ "$sw" -lt "$w" ]; then w=$sw; fi

  if sips --resampleWidth "$w" -s format jpeg -s formatOptions "$Q" "$in" --out "$out" >/dev/null 2>&1; then
    dim=$(sips -g pixelWidth -g pixelHeight "$out" | awk '/pixelWidth/{a=$2}/pixelHeight/{b=$2}END{print a"x"b}')
    printf "  built   %-52s %-10s %s\n" "$name" "$dim" "$(du -h "$out" | cut -f1)"
    made=$((made+1))
  else
    echo "  FAILED  $name"; missing=$((missing+1))
  fi
done < "$PICKS"

echo ""
echo "built $made, already had $skipped, problems $missing"
echo "Output is at the top level of $OUT and IS committed."
echo "WebP is not generated here. sips cannot write it and cwebp is not installed."
echo "Run 'brew install webp' then scripts/optimize-images.sh if you want WebP."
