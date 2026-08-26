#!/usr/bin/env bash
# Make web-ready WebP alongside the originals. Run after fetch-images.sh.
# Needs cwebp: brew install webp
set -uo pipefail
SRC="${1:-assets/img/projects}"
command -v cwebp >/dev/null || { echo "cwebp not found. Run: brew install webp"; exit 1; }
count=0
while IFS= read -r -d '' f; do
  out="${f%.*}.webp"
  [ -f "$out" ] && continue
  cwebp -q 82 -resize 2000 0 "$f" -o "$out" >/dev/null 2>&1 && { echo "  $(basename "$out")"; count=$((count+1)); }
done < <(find "$SRC" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -print0)
echo "Converted $count files."
echo "Quality is preserved deliberately. The brand rule is that photography"
echo "never gets sacrificed for page speed. Do not drop below q=80."
