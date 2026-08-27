# jenniferkizzee.com

The new Jennifer Kizzee Design website. Plain HTML, CSS and JS. No build step.
Deploys to Cloudflare Pages as-is.

## Status

| Page | State |
|---|---|
| `/` Home | Built. Hero photo slot still empty. |
| `/houston-interior-designer` | Built. One photo slot still empty. |
| `/recognition` | Built. 15 awards and 12 features, every row linked to its source. |
| `/recognition/awards` | Built. |
| `/recognition/press` | Built. |
| `/jennifer-kizzee` | Built. Real headshot in place. |
| `/team` | Built. 5 of 7 headshots in place, 2 slots named and empty. |
| `/recognition/industry` | Held. See "Recognition" below. |
| Everything else | Not built yet. See the audit for the full architecture. |

**Photography is downloaded.** `assets/img/projects/` now holds 723 real JKD
project photos across 31 projects, pulled from the live Showit site. They are
gitignored, see "Photography" below. Nothing has been selected or renamed yet,
so the home and service page photo slots are still empty. JKD brand rule 1 is
real project photos only, never stock, never AI, and never a placeholder
shipped as finished work. Every photo slot in the HTML names the exact file it
is waiting for.

## Recognition

Three pages, built from verified evidence only. Every row carries the year, the
organization, two sentences of context and an outbound link. No logo wall.

`/recognition/industry` was deliberately not built. Once ASID, NKBA and the
vendor partnerships are set aside as unconfirmed, the only remaining items are
the Houzz Pro profile, the Cambria partner spotlight, Tile Club and the Tile
Trends podcast, all of which are press and already live on `/recognition/press`.
Build it when Jennifer confirms the affiliations that would actually fill it.

**Not published, on purpose:**
- The Perigold citation. The URL is now a category page with no mention of Jennifer.
- ASID and NKBA membership. Both logos are on the current live site, neither
  directory lists the firm. They do not carry over until Jennifer confirms.
- Visual Comfort, Daltile and Fabricut as partnerships, same reason.
- The name of the Cambria Style Spring 2025 cover project. Cambria describes it
  only as a three-story condo in southern Texas and names no project.

## Local preview

    cd JKD-Website
    python3 -m http.server 8080

Then open http://localhost:8080

## Deploy to Cloudflare Pages

1. Push this folder to a GitHub repo.
2. Cloudflare dashboard, Workers & Pages, Create, Pages, Connect to Git.
3. Build settings:
   - Framework preset: **None**
   - Build command: *(leave empty)*
   - Build output directory: `/`
4. Deploy. You get a `*.pages.dev` preview URL.
5. Do **not** point jenniferkizzee.com at it until the redirect map in
   `_redirects` is finished. The current site ranks second for "Houston
   interior designer for renovations" and a botched cutover loses that.

`_headers` and `_redirects` are Cloudflare Pages files and take effect
automatically.

## Photography

The brand folder's photo library was lost. The photos were still on the live
Showit site, and `scripts/fetch-images.sh` has now pulled them down.

    bash scripts/fetch-images.sh          # pull at 2400px, safe to re-run
    bash scripts/optimize-images.sh       # make WebP alongside

**What is on disk now:** 723 photos across 31 project folders, about 380MB.
Each folder carries a `_manifest.tsv` mapping the local filename back to the
original Showit filename and key, so renaming stays traceable.

**Two bugs were fixed in the fetch script on 2026-08-26.** It had never worked.

1. It grepped the page HTML for `https://static.showit.co/<width>/...` URLs.
   Those do not exist. Showit renders client side from an inline JSON blob where
   each photo is `"key":"<hash>/236843/<file>.jpg"`, and the CDN URL is built as
   `https://static.showit.co/<WIDTH>/<key>`.
2. `basename` was reading Showit hashes that begin with `-` as option flags.

**Resolution is uneven.** The CDN serves `min(requested, original)`, and plenty
of the source uploads are small. Of the 723:

| Bucket | Count |
|---|---|
| 2400px and up | 167 |
| 2000 to 2399 | 96 |
| 1600 to 1999 | 192 |
| 1200 to 1599 | 104 |
| under 1200 | 148 |

Only **115 are landscape and 2000px or wider**, which is the pool for a
full-bleed hero. 452 are portrait and 1600px or taller, which suits the
left-rectangle feature slot. Seven projects have no landscape hero candidate at
all: alexandria, crescent-bath, gentleman-s-retreat, heights-primary-bath,
holcombe-condo, longwood, pine-lodge. Holcombe Condo tops out at 1024px on every
frame, which matters because `/houston-interior-designer` is waiting on a tall
Holcombe photo.

`assets/img/projects/*/` is **gitignored**. It is a working archive, not a
deploy artifact. Curated, renamed files belong at the top level of
`assets/img/projects/` and those are committed, because the pages reference them:

    assets/img/projects/vue-point/vue-point-01.jpg     archive, ignored
    assets/img/projects/vue-point-living-room-01.jpg   shipped, committed

Descriptive filenames and accurate alt text are Priority 10 of the search
work list. Copy the keepers back into the brand folder's `_Best Photography/`
so the library is restored.

`optimize-images.sh` needs `cwebp`, which is not installed on this machine.
`brew install webp` first. There is no other WebP writer here: `sips` cannot
write it and the local Pillow was built without WebP support.

## Fonts

The brand display face is **Modny Light** (Monotype). The license in the brand
folder is a **desktop** EULA, which typically does not cover webfont embedding.
Until a web license is confirmed, the stack falls back to Cormorant Garamond,
which is the web fallback the Brand Operating System specifies.

To switch once licensing is confirmed:
1. Convert `assets/fonts/ModnyLight.otf` to `.woff2`
2. Uncomment the `@font-face` block at the top of `assets/css/site.css`

Nothing else needs to change. `Modny Light` is already first in the stack.

## Structure

    /                          index.html
    /houston-interior-designer/index.html
    /assets/css/site.css       the entire design system
    /assets/js/site.js         nav toggle, marquee, tracking hooks
    /assets/brand/             logo SVGs, all colorways
    /assets/img/team/          real headshots
    /assets/img/projects/      populated by fetch-images.sh
    /_headers                  Cloudflare security and cache headers
    /_redirects                old URL map, INCOMPLETE
    /robots.txt                every legitimate AI and search crawler allowed
    /sitemap.xml               add every page as it goes live

## Still to do

- Select and rename hero photography, then fill the open photo slots
- `brew install webp`, then run `optimize-images.sh`
- Case studies, service pages, areas, process, testimonials, journal, contact, careers
- Finish `_redirects` from a real crawl of the old site
- Contact form, and the analytics hook in `site.js`
- Confirm ASID and NKBA membership before those logos go anywhere
- Two team headshots: Summer Lewis has none anywhere. A second portrait exists
  on the live site as `mik_silk.jpg` and is probably Mikalah Dunn, but the
  filename is not proof, so it has not been published under her name.
- Delete `_git-broken-DELETE-ME/` once you have looked at it. It is gitignored.
