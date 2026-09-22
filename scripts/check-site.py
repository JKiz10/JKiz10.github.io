#!/usr/bin/env python3
"""Static checks for jenniferkizzee.com. Run before every push:

    python3 scripts/check-site.py

Lists every failure and exits 1 if there are any. Per page: a canonical that
matches the page's own URL, one h1, unique title and description, no em dashes,
a real src plus alt, width and height on every image, links and schema URLs that
resolve without a redirect, JSON-LD that parses, the favicon set, and one shared
?v= number for site.css and site.js. Sitewide: sitemap.xml and _redirects are
checked against the pages on disk.
"""
import collections
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

try:
    from PIL import Image
except ImportError:  # Pillow only sharpens the favicon checks; everything else runs without it
    Image = None

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).parent.parent).resolve()
ORIGIN = 'https://jenniferkizzee.com'
FILE_EXT = re.compile(r'\.[A-Za-z0-9]{2,5}$')
ASSET_LINK = re.compile(r'/assets/(css/site\.css|js/site\.js)\?v=(\d+)"')
FAVICON_TAGS = (
    '<link rel="icon" href="/favicon.ico" sizes="32x32">',
    '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
    '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
)
MIN_INBOUND_PAGES = 3
failures = []


def fail(message):
    failures.append(message)


def is_skipped(path):
    return any(part.startswith('_git-broken') or part == '.git' for part in path.relative_to(ROOT).parts)


def url_path_of(page):
    folder = page.parent.relative_to(ROOT).as_posix()
    return '/' if folder == '.' else f'/{folder}/'


def split_suffix(value):
    cut = re.search(r'[?#]', value)
    return (value[:cut.start()], value[cut.start():]) if cut else (value, '')


pages = {url_path_of(p): p for p in sorted(ROOT.rglob('index.html')) if not is_skipped(p)}
html_of = {path: page.read_text(encoding='utf-8') for path, page in pages.items()}


def problem_with(url, check_anchor=True):
    """None when a root-relative URL serves a 200 directly, otherwise the reason it will not.
    JSON-LD @id fragments name graph nodes, not page anchors, so schema URLs skip that part."""
    path, suffix = split_suffix(url)
    if FILE_EXT.search(path):
        return None if (ROOT / path.lstrip('/')).is_file() else 'file does not exist'
    if not path.endswith('/'):
        return 'no trailing slash, so it redirects'
    if path not in pages:
        return 'no such page'
    if check_anchor and suffix.startswith('#') and len(suffix) > 1 and f'id="{suffix[1:]}"' not in html_of[path]:
        return f'anchor {suffix} does not exist on {path}'
    return None


def check_images(path, html):
    for tag in re.findall(r'<img\b[^>]*>', html):
        counts['images'] += 1
        src = re.search(r'\ssrc="([^"]*)"', tag)
        if not src or not src.group(1).strip():
            fail(f'{path}: <img> with no src: {tag[:100]}')
            continue
        if 'data-src' in tag:
            fail(f'{path}: <img> still carries data-src: {src.group(1)}')
        if not all(re.search(p, tag) for p in (r'\salt="', r'\swidth="\d+"', r'\sheight="\d+"')):
            fail(f'{path}: <img> missing alt, width or height: {src.group(1)}')
        srcset = re.search(r'\ssrcset="([^"]*)"', tag)
        candidates = [c.strip().split()[0] for c in srcset.group(1).split(',')] if srcset else []
        for url in [src.group(1), *candidates]:
            if url.startswith('/') and (reason := problem_with(url)):
                fail(f'{path}: image {url}: {reason}')

    for block in re.findall(r'<picture>.*?</picture>', html, re.S):
        if '<img' not in block:
            fail(f'{path}: <picture> with no <img> fallback')
        for source in re.findall(r'<source\b[^>]*>', block):
            counts['webp sources'] += 1
            srcset = re.search(r'\ssrcset="([^"]+)"', source)
            if not srcset:
                fail(f'{path}: <source> with no srcset')
                continue
            candidates = [c.strip().split() for c in srcset.group(1).split(',')]
            if any(len(c) > 1 for c in candidates) and ' sizes="' not in source:
                fail(f'{path}: <source> uses width descriptors without sizes')
            for candidate in candidates:
                if reason := problem_with(candidate[0]):
                    fail(f'{path}: source {candidate[0]}: {reason}')


def check_urls(path, html):
    for href in re.findall(r'href="(/(?!/)[^"]*)"', html):
        counts['internal links'] += 1
        if reason := problem_with(href):
            fail(f'{path}: link {href}: {reason}')
        target = split_suffix(href)[0]
        if target in pages and target != path:
            inbound[target].add(path)
    for match in re.finditer(r'https://jenniferkizzee\.com(/[^"\'\s<>]*)?', html):
        counts['absolute URLs'] += 1
        if reason := problem_with(match.group(1) or '', check_anchor=False):
            fail(f'{path}: {match.group(0)}: {reason}')


def check_head(path, html):
    canonical = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    og_url = re.search(r'<meta property="og:url" content="([^"]+)"', html)
    if not canonical or canonical.group(1) != ORIGIN + path:
        fail(f'{path}: canonical is {canonical.group(1) if canonical else None}, expected {ORIGIN + path}')
    if og_url and canonical and og_url.group(1) != canonical.group(1):
        fail(f'{path}: og:url {og_url.group(1)} differs from the canonical')
    title = re.search(r'<title>(.*?)</title>', html, re.S)
    description = re.search(r'<meta name="description" content="([^"]*)"', html)
    titles[title.group(1).strip() if title else None] += 1
    descriptions[description.group(1) if description else None] += 1
    for tag in FAVICON_TAGS:
        if tag not in html:
            fail(f'{path}: missing {tag}')
    linked = dict(ASSET_LINK.findall(html))
    for asset in ('css/site.css', 'js/site.js'):
        if asset not in linked:
            fail(f'{path}: {asset} is not linked with a ?v= number')
        else:
            asset_versions[asset].add(linked[asset])
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not blocks:
        fail(f'{path}: no JSON-LD')
    for block in blocks:
        counts['JSON-LD blocks'] += 1
        try:
            json.loads(block)
        except json.JSONDecodeError as err:
            fail(f'{path}: JSON-LD does not parse: {err}')


def check_sitemap():
    locs = re.findall(r'<loc>([^<]+)</loc>', (ROOT / 'sitemap.xml').read_text(encoding='utf-8'))
    loc_paths = []
    for loc in locs:
        if not loc.startswith(ORIGIN + '/'):
            fail(f'sitemap: {loc} is not on {ORIGIN}')
            continue
        loc_paths.append(loc[len(ORIGIN):])
        if reason := problem_with(loc[len(ORIGIN):]):
            fail(f'sitemap: {loc}: {reason}')
    if sorted(loc_paths) != sorted(pages):
        fail(f'sitemap lists {len(loc_paths)} URLs for {len(pages)} pages: '
             f'missing {sorted(set(pages) - set(loc_paths))}, extra {sorted(set(loc_paths) - set(pages))}')


def check_redirects():
    for number, line in enumerate((ROOT / '_redirects').read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        parts = line.split()
        if len(parts) != 3 or not parts[2].isdigit():
            fail(f'_redirects:{number}: malformed rule: {line}')
            continue
        source, target, _code = parts
        counts['redirect rules'] += 1
        if reason := problem_with(target):
            fail(f'_redirects:{number}: {source} -> {target}: {reason}')
        if '*' not in source and source.rstrip('/') + '/' in pages:
            fail(f'_redirects:{number}: source {source} is a live page and would be redirected away')


def check_favicon_files():
    for name in ('favicon.ico', 'favicon.svg', 'apple-touch-icon.png'):
        if not (ROOT / name).is_file():
            fail(f'{name} is missing from the site root')
            return
    try:
        view_box = ET.parse(ROOT / 'favicon.svg').getroot().get('viewBox')
        if not view_box:
            fail('favicon.svg has no viewBox')
    except ET.ParseError as err:
        fail(f'favicon.svg does not parse: {err}')
    if Image is None:
        print('note: Pillow is not installed, so favicon bitmap sizes were not checked')
        return
    ico_sizes = sorted(Image.open(ROOT / 'favicon.ico').info.get('sizes', set()))
    if ico_sizes != [(16, 16), (32, 32), (48, 48)]:
        fail(f'favicon.ico holds {ico_sizes}, expected 16, 32 and 48')
    touch = Image.open(ROOT / 'apple-touch-icon.png')
    if touch.size != (180, 180) or touch.mode != 'RGB':
        fail(f'apple-touch-icon.png is {touch.size} {touch.mode}, expected (180, 180) with no transparency')


counts = collections.Counter()
titles = collections.Counter()
descriptions = collections.Counter()
inbound = collections.defaultdict(set)
asset_versions = collections.defaultdict(set)

for page_path, page_html in html_of.items():
    check_head(page_path, page_html)
    if len(re.findall(r'<h1\b', page_html)) != 1:
        fail(f'{page_path}: expected exactly one h1')
    if '—' in page_html or '&mdash;' in page_html:
        fail(f'{page_path}: contains an em dash')
    check_images(page_path, page_html)
    check_urls(page_path, page_html)

for text, count in titles.items():
    if count > 1:
        fail(f'duplicate title x{count}: {text}')
for text, count in descriptions.items():
    if count > 1:
        fail(f'duplicate description x{count}: {text}')
for page_path in pages:
    if len(inbound[page_path]) < MIN_INBOUND_PAGES:
        fail(f'{page_path}: only {len(inbound[page_path])} other pages link here')
for asset, versions in asset_versions.items():
    if len(versions) > 1:
        fail(f'{asset} is linked with different ?v= numbers across pages: {sorted(versions)}')

check_sitemap()
check_redirects()
check_favicon_files()

print(f'{len(pages)} pages | ' + ' | '.join(f'{key}: {value}' for key, value in sorted(counts.items())))
if failures:
    print(f'{len(failures)} FAILURES')
    for message in failures:
        print(f'  {message}')
    sys.exit(1)
print('0 failures')
