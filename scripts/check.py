"""Check generated pages, internal links, images, feeds, and import completeness."""
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.parse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / '_source/posts.json').read_text())
errors = []

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self.ids=set()
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if 'id' in attrs: self.ids.add(attrs['id'])
        if tag == 'a' and 'name' in attrs: self.ids.add(attrs['name'])
        for attr in ('src', 'href'):
            if attrs.get(attr): self.links.append((tag,attr,attrs[attr]))

pages = [ROOT / 'index.html', ROOT / '404.html', ROOT / 'about/index.html'] + [ROOT / x['path'] / 'index.html' for x in records]
parsed = {}
for path in pages:
    parser=Links(); text=path.read_text(); parser.feed(text); parsed[path.resolve()]=parser
    if '{{ROOT}}' in text: errors.append(f'Unexpanded root marker: {path}')
    if '<script' in text.lower(): errors.append(f'Unexpected script: {path}')

for path, parser in parsed.items():
    for tag,attr,link in parser.links:
        url=urllib.parse.urlsplit(link)
        if url.scheme or url.netloc:
            if tag=='img': errors.append(f'External image: {path.name}')
            continue
        if not url.path:
            target=path
        elif url.path.startswith('/'):
            target=ROOT / url.path.lstrip('/')
        else: target=path.parent / urllib.parse.unquote(url.path)
        if target.is_dir(): target=target/'index.html'
        target=target.resolve()
        if not target.exists(): errors.append(f'Missing target {link} in {path.relative_to(ROOT)}')
        if url.fragment and target in parsed and urllib.parse.unquote(url.fragment) not in parsed[target].ids:
            errors.append(f'Missing anchor {link} in {path.relative_to(ROOT)}')

ET.parse(ROOT/'feed.xml'); ET.parse(ROOT/'sitemap.xml')
media=json.loads((ROOT/'_source/media.json').read_text())
for name in media.values():
    if not (ROOT/name).is_file() or (ROOT/name).stat().st_size==0: errors.append(f'Missing image {name}')
assert len({x['path'] for x in records}) == len(records), 'Duplicate paths'
assert len(ET.parse(ROOT/'feed.xml').findall('.//item')) == sum(x['type']=='post' for x in records)
if errors:
    print('\n'.join(errors)); raise SystemExit(1)
print(f'PASS: {len(pages)} pages, all local links/anchors, {len(media)} images, RSS, and sitemap.')
