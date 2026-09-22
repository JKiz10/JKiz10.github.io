#!/usr/bin/env python3
"""Responsive WebP photos for jenniferkizzee.com.

    python3 scripts/build-photos.py plan     [plan.json]
    python3 scripts/build-photos.py build    [plan.json] [quality]
    python3 scripts/build-photos.py rewrite  [plan.json]

plan     finds every content photo on every page, names the layout role it is used
         in, picks the widths that role needs, and ties it to the full-size original
         listed in scripts/photo-sources.tsv.
build    writes <stem>-<width>.webp beside each JPEG, cropped to the JPEG's exact
         aspect ratio and never upscaled. The JPEGs are left alone: they stay as the
         fallback for browsers without WebP and as the og:image and schema files.
rewrite  wraps each photo <img> in <picture> with a WebP <source>, on one line, and
         rebuilds any <picture> that is already there. Running it twice changes nothing.

The originals live in assets/img/projects/<project>/, which is gitignored, so build
only runs on a machine that has the photo library.
"""
import json
import pathlib
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from html.parser import HTMLParser

from PIL import Image

REPO = pathlib.Path(__file__).resolve().parent.parent
SOURCES = REPO / 'scripts/photo-sources.tsv'
DEFAULT_PLAN = REPO / 'scripts/photo-plan.json'
DEFAULT_QUALITY = 84
PHOTO_PREFIXES = ('/assets/img/projects/', '/assets/img/team/')
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
WIDTH_SUFFIX = re.compile(r'-(800|1100|1400|2000)$')
MIN_EXTRA_WIDTH_GAIN = 150  # also offer the original's own width when it beats the biggest step by this much

# role: (candidate widths, sizes attribute; None means a single fixed candidate)
ROLES = {
    'hero': ((800, 1400, 2000), '100vw'),
    # 1400 is the cap: it matches what the site served before, so no visitor ever
    # downloads more than they used to. Only full-bleed heroes go to 2000.
    'gallery': ((800, 1100, 1400), '(max-width: 1520px) 92vw, 1408px'),
    'pair': ((800, 1100, 1400), '(max-width: 700px) 92vw, (max-width: 1520px) 46vw, 696px'),
    'person': ((800, 1100, 1400), '(max-width: 700px) 92vw, (max-width: 1100px) 45vw, 354px'),
    'feature': ((800, 1100, 1400), '(max-width: 880px) 92vw, (max-width: 1240px) 40vw, 500px'),
    'editorial': ((800, 1100, 1400), '(max-width: 880px) 100vw, 58vw'),
    'card': ((800,), None),
}
# First match wins, tested against every class on every ancestor. Pair before gallery.
ROLE_BY_CLASS = (
    ('stage__slide', 'hero'), ('proj-hero__media', 'hero'), ('gallery__pair', 'pair'), ('gallery', 'gallery'),
    ('person__media', 'person'), ('feature__media', 'feature'), ('editorial__media', 'editorial'),
    ('pcard__media', 'card'), ('project__media', 'card'),
)


class PhotoTags(HTMLParser):
    """Finds photo <img> tags with their source position, ancestor classes, and enclosing <picture>."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.tags = [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img' and (attrs.get('src') or '').startswith(PHOTO_PREFIXES):
            line, col = self.getpos()
            picture = next(((p_line, p_col) for name, _, p_line, p_col in reversed(self.stack) if name == 'picture'), None)
            self.tags.append({
                'line': line, 'col': col, 'src': attrs['src'],
                'picture': picture,
                'classes': {c for _, cls, _, _ in self.stack for c in cls.split()},
            })
        if tag not in VOID:
            line, col = self.getpos()
            self.stack.append((tag, attrs.get('class') or '', line, col))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break


def site_pages():
    return sorted(p for p in REPO.rglob('index.html')
                  if not any(part.startswith(('_', '.')) for part in p.relative_to(REPO).parts))


def stem_of(src):
    return WIDTH_SUFFIX.sub('', pathlib.PurePosixPath(src).stem)


def usable_width(source_size, aspect):
    """Widest the original can be once cropped to the site JPEG's aspect ratio."""
    (sw, sh), (aw, ah) = source_size, aspect
    return min(sw, round(sh * aw / ah))


def crop_to_aspect(im, aspect):
    aw, ah = aspect
    w, h = im.size
    if w / h > aw / ah:
        new_w = round(h * aw / ah)
        return im.crop(((w - new_w) // 2, 0, (w - new_w) // 2 + new_w, h))
    new_h = round(w * ah / aw)
    return im.crop((0, (h - new_h) // 2, w, (h - new_h) // 2 + new_h))


def offsets(html):
    return [0] + [m.end() for m in re.finditer('\n', html)]


def plan(plan_file):
    sources = {}
    for row in SOURCES.read_text().splitlines()[1:]:
        committed, source = row.split('\t')[:2]
        if source:
            sources['/' + committed] = source
    photos, tags = {}, []
    for page in site_pages():
        parser = PhotoTags()
        parser.feed(page.read_text(encoding='utf-8'))
        for tag in parser.tags:
            role = next((r for cls, r in ROLE_BY_CLASS if cls in tag['classes']), None)
            if role is None:
                sys.exit(f'{page}: no layout role for {tag["src"]} (ancestor classes {sorted(tag["classes"])})')
            stem = stem_of(tag['src'])
            with Image.open(REPO / tag['src'].lstrip('/')) as im:
                aspect = im.size
            source = sources.get(tag['src'], tag['src'].lstrip('/'))  # team photos have no separate original
            with Image.open(REPO / source) as im:
                source_size = im.size
            entry = photos.setdefault(stem, {
                'folder': str(pathlib.PurePosixPath(tag['src']).parent).lstrip('/'),
                'source': source, 'aspect': list(aspect), 'source_size': list(source_size),
                'widths': set(), 'roles': set(),
            })
            targets = ROLES[role][0]
            widest = usable_width(source_size, aspect)
            chosen = [w for w in targets if w <= widest]
            if not chosen or (chosen[-1] < targets[-1] and widest - chosen[-1] >= MIN_EXTRA_WIDTH_GAIN):
                chosen.append(widest)
            entry['widths'].update(chosen)
            entry['roles'].add(role)
            tags.append({'page': page.relative_to(REPO).as_posix(), 'line': tag['line'], 'col': tag['col'],
                         'picture': tag['picture'], 'role': role, 'stem': stem})
    for entry in photos.values():
        entry['widths'], entry['roles'] = sorted(entry['widths']), sorted(entry['roles'])
    plan_file.write_text(json.dumps({'photos': photos, 'tags': tags}, indent=1))
    by_role = {r: sum(1 for t in tags if t['role'] == r) for r in ROLES}
    print(f'{len(tags)} photo tags on {len({t["page"] for t in tags})} pages, {len(photos)} distinct photos, '
          f'{sum(len(p["widths"]) for p in photos.values())} WebP files to build')
    print('tags by role:', {k: v for k, v in by_role.items() if v})


def build_one(job):
    stem, photo, quality = job
    with Image.open(REPO / photo['source']) as original:
        base = crop_to_aspect(original.convert('RGB'), photo['aspect'])
    aw, ah = photo['aspect']
    written = 0
    for width in photo['widths']:
        out = REPO / photo['folder'] / f'{stem}-{width}.webp'
        base.resize((width, round(width * ah / aw)), Image.LANCZOS).save(out, 'WEBP', quality=quality, method=6)
        written += out.stat().st_size
    return len(photo['widths']), written


def build(plan_file, quality):
    photos = json.loads(plan_file.read_text())['photos']
    with ProcessPoolExecutor() as pool:
        results = list(pool.map(build_one, [(stem, photo, quality) for stem, photo in sorted(photos.items())]))
    print(f'{sum(n for n, _ in results)} WebP files at quality {quality}, {sum(b for _, b in results) / 1048576:.1f} MB total')


def picture_for(tag, photo, img_markup):
    widths = photo['widths']
    url = lambda w: f'/{photo["folder"]}/{tag["stem"]}-{w}.webp'
    sizes = ROLES[tag['role']][1]
    if sizes is None:
        fixed = max((w for w in widths if w <= ROLES[tag['role']][0][-1]), default=min(widths))
        source = f'<source type="image/webp" srcset="{url(fixed)}">'
    else:
        source = f'<source type="image/webp" srcset="{", ".join(f"{url(w)} {w}w" for w in widths)}" sizes="{sizes}">'
    return f'<picture>{source}{img_markup}</picture>'


def rewrite(plan_file):
    data = json.loads(plan_file.read_text())
    by_page = {}
    for tag in data['tags']:
        by_page.setdefault(tag['page'], []).append(tag)
    wrapped = rebuilt = 0
    for rel, tags in sorted(by_page.items()):
        path = REPO / rel
        html = path.read_text(encoding='utf-8')
        starts = offsets(html)
        for tag in sorted(tags, key=lambda t: (t['line'], t['col']), reverse=True):
            at = starts[tag['line'] - 1] + tag['col']
            if not html.startswith('<img', at):
                sys.exit(f'{rel}:{tag["line"]}: expected <img at column {tag["col"]}, found {html[at:at + 20]!r}')
            img = html[at:html.index('>', at) + 1]
            if tag['picture']:
                p_line, p_col = tag['picture']
                start = starts[p_line - 1] + p_col
                end = html.index('</picture>', at) + len('</picture>')
                rebuilt += 1
            else:
                start, end = at, at + len(img)
                wrapped += 1
            html = html[:start] + picture_for(tag, data['photos'][tag['stem']], img) + html[end:]
        path.write_text(html, encoding='utf-8')
    print(f'{wrapped} photos newly wrapped in <picture>, {rebuilt} existing ones rebuilt, across {len(by_page)} pages')


if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    plan_file = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PLAN
    if command == 'plan':
        plan(plan_file)
    elif command == 'build':
        build(plan_file, int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_QUALITY)
    elif command == 'rewrite':
        rewrite(plan_file)
    else:
        sys.exit(__doc__)
