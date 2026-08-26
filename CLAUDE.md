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
