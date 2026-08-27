# Handoff to Claude Code

> **Status as of 2026-08-26.** Photography is downloaded, 723 photos across 31
> projects, gitignored under `assets/img/projects/*/`. Recognition (hub, awards,
> press), `/jennifer-kizzee` and `/team` are built and verified.
> `/recognition/industry` was deliberately held, see README.
> Read `README.md` for what is on disk, what is still open and what must not be
> published. The rest of this file is the original brief and is kept for context.

Paste the block below as your first message in Claude Code, run from the repo root.
Everything Claude Code needs is either in this prompt or in the files it points at.

---

I'm continuing a website rebuild for Jennifer Kizzee Design (JKD), a full-service
residential interior design firm in League City, TX serving Greater Houston.
Founded 2016 by Jennifer Kizzee. Team of nine. This repo replaces their current
site at jenniferkizzee.com, which runs on Showit plus WordPress. We build the
whole site here first, then move the domain over.

## Read these before you touch anything

1. `../CLAUDE.md` one directory up, in the "Jennifer Kizzee Design" folder. That
   is the JKD Brand Operating System and it is the authority on color, type,
   logo usage, photo rules and voice. It overrides your defaults and it
   overrides anything in this repo.
2. `./CLAUDE.md` in this repo. The subset of those rules that bite on a website,
   plus the per-page checklist.
3. `./README.md`. Structure, deploy steps, current status.

## What already exists

- `index.html` and `houston-interior-designer/index.html`, both complete
- `assets/css/site.css`, the entire design system, brand tokens at the top
- `assets/js/site.js`, nav toggle, marquee, analytics hooks
- `assets/brand/`, ten logo SVGs in every colorway
- `assets/img/team/`, four real headshots, optimized, WebP alongside
- `robots.txt`, `sitemap.xml`, `_headers`, `_redirects`
- `scripts/fetch-images.sh` and `scripts/optimize-images.sh`

Plain HTML, CSS and JS. No build step, no framework, no npm. Cloudflare Pages
serves the repo root directly. Keep it that way.

## The rules that break a deliverable

1. Real JKD project photos only. Never stock, never AI-generated. If there is no
   real photo for a slot, leave the slot with the filename it needs and say so.
   Do not ship a placeholder and call it finished.
2. No em dashes anywhere. Commas, periods, line breaks.
3. Never set "Jennifer Kizzee Design" as styled text. Use a logo SVG from
   `assets/brand/`. A page's h1 is a descriptive service headline, never the
   firm name.
4. Gold `#B59556` is rare. Monogram, diamonds, hairline accents. Never a large
   fill or a full-width band.
5. Linen `#EAE3DF` is the default ground. Not white, not gray.
6. Deep Gray `#373737` plus Steel Blue `#3A5476` on Linen is the dominant pair.
7. Photos are full-bleed with sharp corners. No radius, border, frame, shadow,
   gradient or color wash. A neutral darkening scrim is allowed only where type
   sits on the image.
8. In a multi-element layout, photos appear two ways only: full-bleed
   background, or a clean left-side vertical rectangle with text on the right.
   Never a thin horizontal banner strip.
9. Never publish rates. No hourly figures, no package prices, anywhere. Route
   cost questions to Jennifer or Javan.
10. Voice is first-person plural. We, our, us. Warm, short, specific. Never open
    with a question. No "stunning", "gorgeous", "excited to announce". Name the
    room and the color instead.

## Two open blockers

**Photography.** The brand folder's photo library was lost. The photos are still
on the live Showit site. Run `bash scripts/fetch-images.sh` from a normal
terminal. It walks all 32 project pages, pulls every image at 2400px and files
them by project. Then `bash scripts/optimize-images.sh`. Rename what you use
descriptively, for example `vue-point-01.jpg` becomes
`vue-point-living-room-01.jpg`. Case studies cannot be built until this runs.

**The display font.** The brand face is Modny Light (Monotype). The license in
the brand folder is a desktop EULA and may not cover webfont embedding, so the
stack currently falls back to Cormorant Garamond, which is the fallback the
Brand OS itself specifies. `Modny Light` is already first in the stack and there
is a commented `@font-face` block at the top of `site.css`. Do not self-host it
until someone confirms a web license.

## Verified evidence, already researched. Do not invent anything beyond this.

**Awards.** Best of Houzz, fifteen wins across nine years:
2026 Design and Service, 2025 Service, 2024 Design, 2023 Design and Service,
2022 Design and Service, 2021 Design and Service, 2020 Service,
2019 Design and Service, 2018 Design and Service.
Verifiable at the Houzz profile, and Business of Home published the 2018 to 2023
record on 4 April 2023 with Jennifer quoted by name.

**Press, all confirmed:**
- Cambria partner spotlight, plus the Cambria Style Spring 2025 cover story
- Business of Home, 4 April 2023
- Houzz Magazine, 2026 bathroom storage feature naming Jennifer
- Houzz Pro Learn business profile, use the pro.houzz.com URL not the old one
- Tile Club interview, plus a Tile Trends podcast appearance
- Voyage Houston interview, date unconfirmed
- Metropolitan Builder, "Dialogue With a Designer", August 2023, PDF reprint exists

**Do not publish:** the Perigold citation. The linked URL is now a category page
with no mention of Jennifer. Also do not present ASID or NKBA membership, or
Visual Comfort, Daltile and Fabricut as partnerships, until Jennifer confirms
them. Neither ASID nor NKBA lists the firm in their public directories.

**Reviews:** 52 Houzz reviews at 5.0 average.

**Canonical NAP, use verbatim everywhere:**
Jennifer Kizzee Design, 2116 Sedona Dr, League City, TX 77573, 832-304-7134,
info@jenniferkizzee.com

**Canonical service area, use verbatim everywhere:** Houston, Bay Area Houston,
Pasadena, Pearland, League City, Texas City, Friendswood, Alvin, Dickinson,
La Marque, Seabrook, Santa Fe, Webster, Bacliff, Nassau Bay, San Leon, Kemah,
Clear Lake Shores.

## Build order

Next up, and neither is blocked by photography:

1. `/recognition` hub, plus `/recognition/awards`, `/recognition/press`,
   `/recognition/industry`. One row per item: name, year, organization,
   category, winning project linked to its case study, two sentences, and an
   outbound verification link. Never a logo wall. This is the single biggest
   opportunity on the site. Of the Houston firms we checked, only Laura U
   presents awards as dated linked text.
2. `/jennifer-kizzee`, founder and principal designer page, then `/team`.
   Jennifer's optimized headshot is already in `assets/img/team/`.

Then, once photography lands:

3. `/portfolio` rebuilt as a case study index, plus 12 to 15 written case
   studies at `/portfolio/[slug]`. Each one needs location, project type,
   services, style, the challenge, the solution, key decisions, named materials,
   builder collaboration, the testimonial for that project, awards it won, press
   it appeared in, related projects, and a CTA. Retain large premium
   photography. Add text around the images, never instead of them.
4. Four service pages under `/houston-interior-designer/`: `full-service`,
   `whole-home-renovation`, `new-construction`, `kitchen-and-bath`
5. `/areas-we-serve` hub plus city pages, but only for cities where a real
   project exists. A location page with no project behind it is a thin page.
6. `/process`, `/testimonials` with each quote linked to its project,
   `/journal`, `/contact`, `/careers`

## Every new page needs

- A unique title under 60 characters carrying the service and the city
- A unique meta description around 155 characters
- A canonical URL
- Exactly one h1, descriptive, never the word "Menu"
- JSON-LD matching the visible copy exactly: WebPage and BreadcrumbList always,
  plus Service, FAQPage or CreativeWork as it applies
- A row added to `sitemap.xml`
- Real alt text on every image naming the room, project and city
- Header and footer copied from an existing page so navigation stays identical

## Verify before you call a page done

- Every JSON-LD block parses
- Zero em dashes
- One h1, no heading is the word "Menu"
- No image missing alt text
- No horizontal scroll at 390px
- Render it and actually look at it

## Deploy

Cloudflare Pages, framework preset None, build command empty, output directory
`/`. `_headers` and `_redirects` apply automatically. Do not point
jenniferkizzee.com at it until `_redirects` is finished from a real crawl of the
old site. The current site ranks second for "Houston interior designer for
renovations" and a botched cutover loses that.

Start by reading the three files above, then confirm the plan before building.
