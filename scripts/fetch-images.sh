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
# HOW SHOWIT ACTUALLY SERVES IMAGES
# The page HTML contains no <img> tags and no static.showit.co URLs. Showit
# renders client side from an inline JSON blob, where every photo appears as
#     "key":"<hash>/236843/<filename>.jpg"
# and the CDN URL is built as
#     https://static.showit.co/<WIDTH>/<key>
# An earlier version of this script grepped for full static.showit.co URLs in
# the HTML. Those are not there, so it downloaded nothing. Fixed 2026-08-26.
#
#   cd "path/to/JKD-Website"
#   bash scripts/fetch-images.sh
#
# Re-run with WIDTH=3000 for larger files. Already-downloaded files are skipped,
# so re-running is cheap and safe.
# ---------------------------------------------------------------------------
set -uo pipefail

OUT="${OUT:-assets/img/projects}"
WIDTH="${WIDTH:-2400}"
SITE="https://jenniferkizzee.com"
CDN="https://static.showit.co"
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
  branstetter-kitchen ambrose-kitchen blue-heron-bathroom
)

total=0
failed=0

for slug in "${PAGES[@]}"; do
  echo ""
  echo "=== $slug ==="
  html=$(curl -sS -A "$UA" --max-time 40 "$SITE/$slug" 2>/dev/null) || { echo "  could not load page"; continue; }

  # Every photo is an object key inside the inline Showit JSON.
  keys=$(printf '%s' "$html" \
    | grep -oE '"key":"[A-Za-z0-9_-]+/[0-9]+/[^"]+\.(jpg|jpeg|png|webp)"' \
    | sed -E 's/^"key":"//; s/"$//' \
    | sort -u)

  [ -z "$keys" ] && { echo "  no images found"; continue; }

  mkdir -p "$OUT/$slug"
  manifest="$OUT/$slug/_manifest.tsv"
  [ -f "$manifest" ] || printf 'file\tsource_filename\tshowit_key\n' > "$manifest"

  # Sort by source filename so numbering follows the order the site itself uses.
  sorted=$(printf '%s\n' "$keys" | awk -F/ '{print $NF"\t"$0}' | sort -f | cut -f2-)

  n=0
  while IFS= read -r key; do
    [ -z "$key" ] && continue
    # Showit hashes are base64url and may begin with "-", which basename
    # would read as an option flag. Strip the path in pure shell instead.
    base="${key##*/}"

    # Brand marks and third-party badges. We already hold these as SVG.
    case "$base" in
      *jennifer-kizzee-primary*|*jennifer-kizzee-secondary*|*jennifer-kizzee-tertiary*) continue;;
      *monogram*|*logo*|*badge*|asid_*|nkba_*|screenshot_*) continue;;
    esac

    n=$((n+1))
    ext="${base##*.}"
    dest=$(printf "%s/%s/%s-%02d.%s" "$OUT" "$slug" "$slug" "$n" "$ext")

    if [ -f "$dest" ]; then echo "  have  ${dest##*/}"; continue; fi

    if curl -sSf -A "$UA" --max-time 90 -o "$dest" "$CDN/$WIDTH/$key" 2>/dev/null; then
      echo "  saved ${dest##*/}  <- $base"
      printf '%s\t%s\t%s\n' "${dest##*/}" "$base" "$key" >> "$manifest"
      total=$((total+1))
    else
      echo "  FAILED $base"
      rm -f "$dest"
      failed=$((failed+1))
    fi
  done <<< "$sorted"
done

echo ""
echo "==========================================="
echo "Downloaded $total files into $OUT   (failures: $failed)"
echo ""
echo "Each project folder carries a _manifest.tsv mapping the local filename"
echo "back to the original Showit filename and key, so renaming stays traceable."
echo ""
echo "Next:"
echo "  1. bash scripts/optimize-images.sh    (make WebP alongside)"
echo "  2. Copy the keepers back into the brand folder's _Best Photography/"
echo "  3. Rename the ones you use by room and project, e.g."
echo "       vue-point-01.jpg -> vue-point-living-room-01.jpg"
echo "     Descriptive filenames are Priority 10 of the search work list."
echo "==========================================="
