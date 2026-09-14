# jenniferkizzee.com, working rules

The brand system lives one folder up in `../CLAUDE.md`. Read it before
designing or writing anything. It wins over anything in this file.

## The rules that bite most often on this site

1. **Real JKD project photos only.** Never stock, never AI. If there is no real
   photo for a slot, leave the slot and say so. Do not ship a placeholder and
   call it done.
2. **No em dashes anywhere.** Commas, periods, line breaks.
3. **Never set "Jennifer Kizzee Design" as styled text.** Use a logo file from
   `assets/brand/`. The `<h1>` on a page is a descriptive service headline, not
   the firm name.
4. **Gold `#B59556` is rare.** Monogram, diamonds, hairline accents. Never a
   large fill or a full band.
5. **Linen `#EAE3DF` is the default ground.** Not white, not gray.
6. **Dominant pair is Deep Gray `#373737` + Steel Blue `#3A5476` on Linen.**
7. **Photos are full-bleed with sharp corners.** No radius, no border, no frame,
   no shadow, no gradient or color wash over a photo. A scrim is allowed only
   where type sits on the image and only as neutral darkening.
8. **Photos appear two ways only in a multi-element layout:** full-bleed
   background, or a clean left-side vertical rectangle with text on the right.
   Never a thin horizontal banner strip.
9. **Never publish rates.** No hourly figures, no package prices, anywhere.
   Route cost questions to Jennifer or Javan.
10. **Voice is first-person plural.** We, our, us. Warm, short, specific.
    Never open with a question. No "stunning", "gorgeous", "excited to
    announce". Name the room and the color instead.

## Color tokens

Defined once in `assets/css/site.css`. Never redefine or approximate.

## Type

Display: Modny Light, falling back to Cormorant Garamond. Uppercase.
Labels and buttons: Inter, uppercase, tracking `.26em` to `.34em`.
Body: Inter, normal case, weight 300.

## Every new page needs

- A unique `<title>` under 60 characters, with the service and the city
- A unique meta description
- A canonical URL
- One `<h1>`, descriptive, never the word "Menu"
- JSON-LD: `WebPage`, `BreadcrumbList`, plus `Service`, `FAQPage` or
  `CreativeWork` as it applies. It must match the visible copy exactly.
- A row added to `sitemap.xml`
- Real alt text on every image, naming the room, the project and the city
- URLs that end in a slash everywhere: links, canonical, `og:url`, JSON-LD and
  `sitemap.xml`. `/portfolio/`, never `/portfolio`. GitHub Pages and Cloudflare
  both serve a folder page at the slash and redirect the bare form, so a missing
  slash costs every visitor and crawler a redirect.
- A real `src` on every `<img>`. Defer with `loading="lazy"`, never `data-src`,
  which crawlers and link previews read as an empty image.
- The favicon set in the head: `favicon.ico`, `favicon.svg`, `apple-touch-icon.png`

## Changing site.css or site.js

Bump the `?v=` number on the `site.css` and `site.js` links in every page.
Browsers and the CDN keep serving the old file otherwise.

## Before pushing

    python3 scripts/check-site.py
    node scripts/check-stage.mjs

Both must pass. `check-site.py` needs no browser and covers every page, the
sitemap, `_redirects` and the favicon set. `check-stage.mjs` drives headless
Google Chrome through the rotating homepage hero, so run it whenever the
homepage, `site.css` or `site.js` changes.
