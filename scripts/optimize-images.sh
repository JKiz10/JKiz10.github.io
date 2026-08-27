#!/usr/bin/env bash
# Make web-ready WebP alongside the originals. Run after fetch-images.sh.
# Needs cwebp: brew install webp
set -uo pipefail
SRC="${1:-assets/img/projects}"
if ! command -v cwebp >/dev/null; then
  echo "cwebp not found, so no WebP can be written."
  echo ""
  echo "  brew install webp"
  echo ""
  echo "There is no fallback on this machine. sips cannot write WebP and the"
  echo "local Pillow was built without WebP support. Both were checked."
  echo "The site works without it, JPEG is the only source in every <picture>."
  exit 1
fi
count=0
while IFS= read -r -d '' f; do
  out="${f%.*}.webp"
  [ -f "$out" ] && continue
  cwebp -q 82 -resize 2000 0 "$f" -o "$out" >/dev/null 2>&1 && { echo "  $(basename "$out")"; count=$((count+1)); }
done < <(find "$SRC" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -print0)
echo "Converted $count files."
echo "Quality is preserved deliberately. The brand rule is that photography"
echo "never gets sacrificed for page speed. Do not drop below q=80."
