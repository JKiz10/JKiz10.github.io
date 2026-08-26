# jenniferkizzee.com

The new Jennifer Kizzee Design website. Plain HTML, CSS and JS. No build step.
Deploys to Cloudflare Pages as-is.

## Status

| Page | State |
|---|---|
| `/` Home | Built. Waiting on photography. |
| `/houston-interior-designer` | Built. Waiting on photography. |
| Everything else | Not built yet. See the audit for the full architecture. |

**This site is not shippable until the real photography is in.** JKD brand rule
1 is real project photos only, never stock, never AI, and never a placeholder
shipped as finished work. Every photo slot in the HTML names the exact file it
is waiting for. See "Photography" below.

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

The brand folder's photo library was lost. The photos are still on the live
Showit site.

    bash scripts/fetch-images.sh          # pull them down at 2400px
    bash scripts/optimize-images.sh       # make WebP alongside

Run these in your own Terminal. Claude's sandbox cannot reach
jenniferkizzee.com or static.showit.co.

After downloading, rename the files you use by project and room:

    vue-point-01.jpg  ->  vue-point-living-room-01.jpg

Descriptive filenames and accurate alt text are Priority 10 of the search
work list. Then copy the keepers back into the brand folder's
`_Best Photography/` so the library is restored.

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

- Photography (blocking)
- The remaining ~38 pages
- Finish `_redirects` from a real crawl of the old site
- Contact form, and the analytics hook in `site.js`
- Confirm ASID and NKBA membership before those logos go anywhere
