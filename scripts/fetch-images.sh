#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Pull JKD's own project photography off the live Showit site.
#
# WHY THIS EXISTS
# The brand folder's photo library was lost (see 99 Recovery Notes). The photos
# still live on jenniferkizzee.com, served from the Showit CDN. This script
# collects them at the largest size the CDN will serve, names them by project,
# and drops them into the new site's asset folder.
#
# RUN THIS IN YOUR OWN TERMINAL on the Mac, not through Claude. Claude's
# sandbox proxy blocks jenniferkizzee.com and static.showit.co.
#
#   cd "path/to/JKD-Website"
#   bash scripts/fetch-images.sh
#
# Then re-run with WIDTH=3000 if you want larger files.
# ---------------------------------------------------------------------------
set -uo pipefail

OUT="${OUT:-assets/img/projects}"
WIDTH="${WIDTH:-2400}"
SITE="https://jenniferkizzee.com"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"

mkdir -p "$OUT"

PAGES=(
  takoma-park-md pebble-brook holcombe-condo collective-washroom gateway-condo
  vue-point longwood pine-lodge markee-oaks alexandria gentleman-s-retreat
  crescent-bath fox-run-modern-bath heights-primary-bath pinewold-kitchen
  rockpoint-project starfish-vacation-home pool-envy-commercial silver-moon-project
  sunstream-bath jenn-s-kitchen marrelli-project mountain-falls-primary-bath
  evergreen-suite-bedroom fox-run-modern-kitchen knoll-kitchen
  crystal-beach-vacation-home emma-lane-guest-house evergreen-suite-bathroom
  branstetter-kitchen ambrose-kitchen
)

total=0
for slug in "${PAGES[@]}"; do
  echo ""
  echo "=== $slug ==="
  html=$(curl -sS -A "$UA" --max-time 30 "$SITE/$slug" 2>/dev/null) || { echo "  could not load page"; continue; }

  # Showit serves images as https://static.showit.co/<width>/<hash>/<site>/<file>
  urls=$(printf '%s' "$html" \
    | grep -oE 'https://static\.showit\.co/[0-9]+/[A-Za-z0-9_-]+/[0-9]+/[^"'"'"' )]+\.(jpg|jpeg|png|webp)' \
    | sed -E "s#static\.showit\.co/[0-9]+/#static.showit.co/${WIDTH}/#" \
    | sort -u)

  [ -z "$urls" ] && { echo "  no images found"; continue; }

  mkdir -p "$OUT/$slug"
  n=0
  while IFS= read -r u; do
    [ -z "$u" ] && continue
    base=$(basename "$u")
    # skip logo and brand marks, we already have those as SVG
    case "$base" in
      *jennifer-kizzee-primary*|*jennifer-kizzee-secondary*|*jennifer-kizzee-tertiary*|*monogram*|*logo*|*badge*) continue;;
    esac
    n=$((n+1))
    ext="${base##*.}"
    dest=$(printf "%s/%s/%s-%02d.%s" "$OUT" "$slug" "$slug" "$n" "$ext")
    if [ -f "$dest" ]; then echo "  have  $(basename "$dest")"; continue; fi
    if curl -sS -A "$UA" --max-time 60 -o "$dest" "$u"; then
      echo "  saved $(basename "$dest")  <- $base"
      total=$((total+1))
    else
      echo "  FAILED $base"; rm -f "$dest"
    fi
  done <<< "$urls"
done

echo ""
echo "==========================================="
echo "Downloaded $total files into $OUT"
echo ""
echo "Next:"
echo "  1. bash scripts/optimize-images.sh    (make WebP + resize)"
echo "  2. Copy the keepers back into the brand folder's _Best Photography/"
echo "  3. Rename the ones you use by room and project, e.g."
echo "       vue-point-01.jpg -> vue-point-living-room-01.jpg"
echo "     Descriptive filenames are Priority 10 of the search work list."
echo "==========================================="
