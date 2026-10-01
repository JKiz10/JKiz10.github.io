#!/usr/bin/env python3
"""Builds project pages for the projects carried over from the old site.

Reads scripts/new-projects.json, cuts the site JPEGs from the photo library,
writes one page per project against the existing project template, then rebuilds
the portfolio index, every page's related projects, the sitemap and the redirects.
Safe to re-run: it overwrites what it owns and leaves everything else alone.
"""
import json
import pathlib
import re
import sys

from PIL import Image

REPO = pathlib.Path(__file__).resolve().parent.parent
ORIGIN = 'https://jenniferkizzee.com'
TEMPLATE_SLUG = 'gateway-condo'
GROUP_ORDER = ['whole-home', 'kitchens', 'bathrooms', 'vacation-homes', 'bedrooms', 'commercial']
WIDTHS = {'hero': 2000, 'cover': 800, 'g': 1400, 'p': 1400}
STOPWORDS = {'a', 'an', 'and', 'the', 'in', 'on', 'at', 'of', 'to', 'by', 'with', 'under', 'over', 'beside',
             'from', 'into', 'through', 'its', 'that', 'for', 'above', 'below', 'between', 'design', 'jennifer',
             'kizzee', 'project'}
SERVICE_LINK = {
    'kitchens': ('/houston-interior-designer/kitchen-and-bath/', 'kitchen and bath design'),
    'bathrooms': ('/houston-interior-designer/kitchen-and-bath/', 'kitchen and bath design'),
    'whole-home': ('/houston-interior-designer/whole-home-renovation/', 'whole-home renovation design'),
    'vacation-homes': ('/houston-interior-designer/whole-home-renovation/', 'whole-home renovation design'),
    'bedrooms': ('/houston-interior-designer/', 'Houston interior design'),
    'commercial': ('/houston-interior-designer/', 'Houston interior design'),
}
COMMERCIAL_LEDE = ('Selection rooms, showrooms and the spaces a business puts its clients in. The work is the '
                   'same as a house: plan it around how people actually move through it, then make it look like '
                   'someone cared.')

data = json.loads((REPO / 'scripts/new-projects.json').read_text())
template = (REPO / f'portfolio/{TEMPLATE_SLUG}/index.html').read_text(encoding='utf-8')
index_html = (REPO / 'portfolio/index.html').read_text(encoding='utf-8')


def unique_filename(slug, alt, taken):
    words = [w for w in re.findall(r'[a-z]+', alt.lower()) if w not in STOPWORDS][:5]
    base = f'{slug}-{"-".join(words)}' if words else slug
    name, n = base, 2
    while name in taken:
        name, n = f'{base}-{n}', n + 1
    taken.add(name)
    return name


def cut_jpeg(source, out, width):
    with Image.open(source) as im:
        im = im.convert('RGB')
        w = min(width, im.width)
        h = round(w * im.height / im.width)
        im.resize((w, h), Image.LANCZOS).save(out, 'JPEG', quality=84, optimize=True, progressive=True, subsampling='4:2:0')
    return w, h, im.width, im.height


def img_tag(src, alt, w, h, hero=False):
    tail = 'fetchpriority="high" decoding="async"' if hero else 'loading="lazy" decoding="async"'
    return f'<img src="{src}" alt="{alt}" width="{w}" height="{h}" {tail}>'


# ---------------------------------------------------------------- catalogue ---
def read_existing_cards():
    """Every project already on the portfolio index, with the group it sits in."""
    cards = {}
    for section in re.findall(r'<section class="band[^"]*" id="([a-z-]+)"[^>]*>(.*?)</section>', index_html, re.S):
        group, body = section
        for match in re.finditer(r'<a class="pcard" href="/portfolio/([^"]+)/">(.*?)</a>', body, re.S):
            slug, inner = match.group(1), match.group(2)
            img = re.search(r'<img[^>]*>', inner).group(0)
            cards[slug] = {
                'slug': slug, 'group': group, 'img': img,
                'meta': re.search(r'<p class="pcard__meta">(.*?)</p>', inner, re.S).group(1).strip(),
                'name': re.search(r'<h3 class="pcard__name">(.*?)</h3>', inner, re.S).group(1).strip(),
            }
    return cards


catalogue = read_existing_cards()
if len(catalogue) < 16:  # 16 before this script has ever run, 32 after; both are fine
    sys.exit(f'ABORT: expected at least 16 cards on the portfolio index, found {len(catalogue)}')

# ------------------------------------------------------------------- images ---
source_rows = []
taken_names = set()
for slug, project in data.items():
    library = REPO / 'assets/img/projects' / slug
    files = {}
    for number, role, alt in project['photos']:
        source = library / f'{slug}-{number}.jpg'
        name = unique_filename(slug, alt, taken_names)
        suffix = '-hero' if role == 'hero' else '-cover' if role == 'cover' else ''
        out = REPO / 'assets/img/projects' / f'{name}{suffix}.jpg'
        w, h, sw, sh = cut_jpeg(source, out, WIDTHS[role])
        files[(number, role)] = (f'/assets/img/projects/{out.name}', alt, w, h)
        source_rows.append(f'assets/img/projects/{out.name}\t{source.relative_to(REPO).as_posix()}\t{w}\t{h}\t{sw}\t{sh}\t0.0')
    project['files'] = {f'{number}|{role}': value for (number, role), value in files.items()}
    hero = project['files'][f'{project["photos"][0][0]}|hero']
    cover = project['files'][f'{project["photos"][1][0]}|cover']
    catalogue[slug] = {
        'slug': slug, 'group': project['group'], 'name': project['name'], 'meta': project['type'],
        'img': img_tag(cover[0], cover[1], cover[2], cover[3]),
    }
    project['hero'], project['cover'] = hero, cover

sources = REPO / 'scripts/photo-sources.tsv'
existing = sources.read_text()
fresh = [row for row in source_rows if row.split('\t')[0] not in existing]
sources.write_text(existing + ('\n'.join(fresh) + '\n' if fresh else ''))

# --------------------------------------------------------- related projects ---
ordered = [slug for group in GROUP_ORDER for slug in sorted(s for s, c in catalogue.items() if c['group'] == group)]
related_of = {slug: [ordered[(i + step) % len(ordered)] for step in (1, 2, 3)] for i, slug in enumerate(ordered)}


def related_grid(slug):
    cards = '\n'.join(
        f'''        <a class="pcard" href="/portfolio/{other}/">
          <div class="pcard__media">{catalogue[other]["img"]}</div>
          <p class="pcard__meta">{catalogue[other]["meta"]}</p>
          <h3 class="pcard__name">{catalogue[other]["name"]}</h3>
        </a>''' for other in related_of[slug])
    return f'<div class="grid grid--3 mt-lg">\n{cards}\n      </div>'


# ---------------------------------------------------------------- the pages ---
OLD_TITLE = 'Condo Renovation | Houston Interior Designer'
OLD_DESC = re.search(r'<meta name="description" content="([^"]*)"', template).group(1)

for slug, project in data.items():
    name, group = project['name'], project['group']
    url = f'{ORIGIN}/portfolio/{slug}/'
    title = f'{project["title"]} | Jennifer Kizzee Design'
    hero_src, hero_alt, hero_w, hero_h = project['hero']
    page = template

    schema = {
        '@context': 'https://schema.org',
        '@graph': [
            {'@type': 'WebPage', '@id': f'{url}#webpage', 'url': url, 'name': title,
             'description': project['description'], 'isPartOf': {'@id': f'{ORIGIN}/#website'},
             'about': {'@id': f'{ORIGIN}/#organization'}, 'primaryImageOfPage': ORIGIN + hero_src, 'inLanguage': 'en-US'},
            {'@type': 'BreadcrumbList', '@id': f'{url}#breadcrumb', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{ORIGIN}/'},
                {'@type': 'ListItem', 'position': 2, 'name': 'Portfolio', 'item': f'{ORIGIN}/portfolio/'},
                {'@type': 'ListItem', 'position': 3, 'name': name, 'item': url}]},
            {'@type': 'CreativeWork', '@id': f'{url}#project', 'name': name,
             'creator': {'@id': f'{ORIGIN}/#organization'}, 'url': url, 'image': ORIGIN + hero_src,
             'about': project['type'], 'inLanguage': 'en-US',
             'material': [m.strip() for m in project['materials'].split(',')]},
        ],
    }
    page = re.sub(r'<script type="application/ld\+json">.*?</script>',
                  '<script type="application/ld+json">\n' + json.dumps(schema, indent=1, ensure_ascii=False) + '\n</script>',
                  page, count=1, flags=re.S)
    page = page.replace(OLD_TITLE, title).replace(OLD_DESC, project['description'])
    page = page.replace(f'{ORIGIN}/portfolio/{TEMPLATE_SLUG}/', url)
    page = page.replace(f'{ORIGIN}/assets/img/projects/gateway-condo-primary-bedroom-hero.jpg', ORIGIN + hero_src)
    page = re.sub(r'<div class="proj-hero__media">.*?</div>',
                  f'<div class="proj-hero__media">\n      {img_tag(hero_src, hero_alt, hero_w, hero_h, hero=True)}\n    </div>',
                  page, count=1, flags=re.S)
    page = page.replace('<p class="eyebrow eyebrow--light">The Woodlands, TX &middot; Complete home renovation</p>',
                        f'<p class="eyebrow eyebrow--light">{project["type"]}</p>')

    facts = '\n'.join(f'        <div>\n          <dt>{label}</dt>\n          <dd>{value}</dd>\n        </div>'
                      for label, value in (('Project type', project['type']), ('Rooms', project['rooms']),
                                           ('Materials', project['materials']), ('Style', project['style'])))
    intro = ('<div class="wrap--narrow" style="padding:0;margin:0">\n'
             + '\n'.join(f'        <p>{para}</p>' for para in project['copy'])
             + f'\n      </div>\n      <dl class="proj-facts mt-lg">\n{facts}\n      </dl>')
    page = re.sub(r'<div class="wrap--narrow" style="padding:0;margin:0">.*?</dl>', intro, page, count=1, flags=re.S)

    gallery, pair = [], []
    for number, role, alt in project['photos']:
        if role in ('hero', 'cover'):
            continue
        src, alt_text, w, h = project['files'][f'{number}|{role}']
        portrait = ' class="portrait"' if h > w and role != 'p' else ''
        tag = f'<figure{portrait}>{img_tag(src, alt_text, w, h)}</figure>'
        if role == 'p':
            pair.append(tag)
            if len(pair) == 2:
                gallery.append('        <div class="gallery__pair">\n          ' + '\n          '.join(pair) + '\n        </div>')
                pair = []
        else:
            gallery.append('        ' + tag)
    if pair:
        gallery.append('        ' + pair[0])
    page = re.sub(r'<div class="gallery" data-reveal>.*?\n      </div>',
                  '<div class="gallery" data-reveal>\n' + '\n'.join(gallery) + '\n      </div>', page, count=1, flags=re.S)
    page = re.sub(r'\n  <section class="band band--tight band--linen" aria-labelledby="press-gateway-condo".*?\n  </section>\n',
                  '\n', page, count=1, flags=re.S)
    # rename before the related cards go in, or their file names get rewritten too
    page = page.replace(TEMPLATE_SLUG, slug).replace('Gateway Condo', name)
    page = re.sub(r'<div class="grid grid--3 mt-lg">.*?\n      </div>', related_grid(slug), page, count=1, flags=re.S)
    service_url, service_text = SERVICE_LINK[group]
    page = re.sub(r'(<div class="wrap wrap--narrow proj-links">.*?)<a class="link-underline" href="[^"]*" data-cta="proj-service">[^<]*</a>',
                  lambda m: m.group(1) + f'<a class="link-underline" href="{service_url}" data-cta="proj-service">{service_text}</a>',
                  page, count=1, flags=re.S)

    folder = REPO / 'portfolio' / slug
    folder.mkdir(exist_ok=True)
    (folder / 'index.html').write_text(page, encoding='utf-8')

# rebuild the related grid on the sixteen pages that were already here
for slug in catalogue:
    if slug in data:
        continue
    path = REPO / 'portfolio' / slug / 'index.html'
    html = path.read_text(encoding='utf-8')
    html = re.sub(r'<div class="grid grid--3 mt-lg">.*?\n      </div>', related_grid(slug), html, count=1, flags=re.S)
    path.write_text(html, encoding='utf-8')

# ------------------------------------------------------------------- index ---
def index_grid(group):
    cards = '\n'.join(
        f'''        <a class="pcard" href="/portfolio/{slug}/">
          <div class="pcard__media">{catalogue[slug]["img"]}</div>
          <p class="pcard__meta">{catalogue[slug]["meta"]}</p>
          <h3 class="pcard__name">{catalogue[slug]["name"]}</h3>
        </a>''' for slug in sorted(s for s, c in catalogue.items() if c['group'] == group))
    return f'<div class="grid grid--3 mt-lg">\n{cards}\n      </div>'


for group in GROUP_ORDER[:-1]:
    pattern = re.compile(r'(<section class="band[^"]*" id="' + group + r'"[^>]*>.*?)<div class="grid grid--3 mt-lg">.*?\n      </div>', re.S)
    if not pattern.search(index_html):
        sys.exit(f'ABORT: no {group} section on the portfolio index')
    index_html = pattern.sub(lambda m: m.group(1) + index_grid(group), index_html, count=1)

if 'id="commercial"' not in index_html:
    bedrooms = re.search(r'\n  <section class="band[^"]*" id="bedrooms".*?\n  </section>\n', index_html, re.S).group(0)
    commercial = (bedrooms.replace('id="bedrooms"', 'id="commercial"').replace('h-bedrooms', 'h-commercial')
                  .replace('band--white', 'band--linen'))
    commercial = re.sub(r'(<h2 id="h-commercial"[^>]*>)[^<]*</h2>', r'\1Commercial</h2>', commercial)
    commercial = re.sub(r'<p class="lede">.*?</p>', f'<p class="lede">{COMMERCIAL_LEDE}</p>', commercial, count=1, flags=re.S)
    commercial = re.sub(r'<div class="grid grid--3 mt-lg">.*?\n      </div>', index_grid('commercial'), commercial, count=1, flags=re.S)
    index_html = index_html.replace(bedrooms, bedrooms + commercial)
(REPO / 'portfolio/index.html').write_text(index_html, encoding='utf-8')

# --------------------------------------------------------- sitemap, redirects ---
sitemap = REPO / 'sitemap.xml'
xml = sitemap.read_text(encoding='utf-8')
sample = re.search(r'\s*<url><loc>' + re.escape(ORIGIN) + r'/portfolio/vue-point/</loc>[^\n]*', xml).group(0).strip()
new_urls = [sample.replace('/portfolio/vue-point/', f'/portfolio/{slug}/') for slug in data if f'/portfolio/{slug}/</loc>' not in xml]
lines = re.findall(r'\s*<url>.*?</url>', xml, re.S)
head, tail = xml.split(lines[0].strip(), 1)[0], xml.rsplit(lines[-1].strip(), 1)[1]
everything = sorted({line.strip() for line in lines} | set(new_urls), key=lambda l: re.search(r'<loc>([^<]+)', l).group(1))
sitemap.write_text(head + '\n  '.join(everything) + tail, encoding='utf-8')

redirects = REPO / '_redirects'
rules = []
for line in redirects.read_text(encoding='utf-8').split('\n'):
    match = re.match(r'^(/\S+)(\s+)(\S+)(\s+)(\d{3})\s*$', line)
    if match and match.group(1).lstrip('/') in data:
        slug = match.group(1).lstrip('/')
        target = f'/portfolio/{slug}/'
        pad = max(1, len(match.group(2)) + len(match.group(3)) - len(target))
        rules.append(f'{match.group(1)}{match.group(2)}{target}{" " * pad}{match.group(5)}')
    else:
        rules.append(line)
redirects.write_text('\n'.join(rules), encoding='utf-8')

print(f'{len(data)} project pages written, {len(fresh)} photos cut, index rebuilt with {len(catalogue)} projects')
print('sitemap:', len(everything), 'urls | redirects updated for', sum(1 for s in data), 'old project URLs')
