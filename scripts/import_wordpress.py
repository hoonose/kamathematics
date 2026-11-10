"""Import public WordPress API exports. Run once; edit imported posts thereafter."""
import concurrent.futures
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OLD = 'https://kamathematics.wordpress.com'
items = []
for filename in ['/tmp/kamathematics-posts.json', '/tmp/kamathematics-pages.json']:
    response = json.loads(Path(filename).read_text())
    assert len(response['posts']) == response['found'], 'Incomplete export'
    items.extend(response['posts'])
assets = {}

class Images(HTMLParser):
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img' and attrs.get('src'):
            url = attrs['src']
            suffix = Path(urllib.parse.urlsplit(url).path).suffix.lower()
            if suffix not in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'):
                suffix = '.png'
            assets[url] = 'assets/' + hashlib.sha256(url.encode()).hexdigest()[:20] + suffix

for item in items:
    Images().feed(item['content'])

def download(pair):
    url, path = pair
    target = ROOT / path
    if target.exists():
        return
    request = urllib.request.Request(url, headers={'User-Agent': 'Kamathematics archive migration'})
    with urllib.request.urlopen(request, timeout=45) as result:
        content_type = result.headers.get('Content-Type', '')
        assert content_type.startswith('image/'), content_type
        target.write_bytes(result.read())

failures = []
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    jobs = {pool.submit(download, pair): pair for pair in assets.items()}
    for job in concurrent.futures.as_completed(jobs):
        try:
            job.result()
        except Exception as exc:
            failures.append({'asset': jobs[job][1], 'error': str(exc)})
if failures:
    print(json.dumps(failures, indent=2))
    raise SystemExit('Media import incomplete; do not publish')

known_paths = {urllib.parse.urlsplit(x['URL']).path for x in items}
id_paths = {str(x['ID']): urllib.parse.urlsplit(x['URL']).path for x in items}

class Clean(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []
    def handle_starttag(self, tag, attrs):
        out = []
        attrs = dict(attrs)
        for key, value in attrs.items():
            if key in ('srcset', 'sizes', 'style') or key.startswith('on'):
                continue
            if tag == 'img' and key == 'src':
                value = assets[value]
            if key == 'href' and value:
                parsed = urllib.parse.urlsplit(value)
                if parsed.netloc == 'kamathematics.wordpress.com':
                    if parsed.path in known_paths:
                        value = parsed.path + ('#' + parsed.fragment if parsed.fragment else '')
                    elif parsed.path == '/' and 'p' in urllib.parse.parse_qs(parsed.query):
                        value = id_paths.get(urllib.parse.parse_qs(parsed.query)['p'][0], value)
                if value.startswith('/'):
                    value = '{{ROOT}}' + value
            if tag == 'img' and key == 'src':
                value = '{{ROOT}}/' + value
            out.append(key if value is None else key + '="' + html.escape(value, quote=True) + '"')
        if tag == 'img':
            out += ['loading="lazy"', 'decoding="async"']
        self.parts.append('<' + tag + (' ' + ' '.join(out) if out else '') + '>')
    def handle_endtag(self, tag): self.parts.append('</' + tag + '>')
    def handle_data(self, data): self.parts.append(data)
    def handle_entityref(self, name): self.parts.append('&' + name + ';')
    def handle_charref(self, name): self.parts.append('&#' + name + ';')

records = []
for item in items:
    parser = Clean(); parser.feed(item['content'])
    body = ''.join(parser.parts)
    relative = urllib.parse.urlsplit(item['URL']).path.strip('/')
    source = '_source/posts/' + item['slug'] + '.html'
    (ROOT / source).write_text(body)
    records.append({
        'title': html.unescape(item['title']), 'date': item['date'],
        'modified': item['modified'], 'path': relative,
        'source': source, 'original_url': item['URL'],
        'type': item['type'], 'categories': list(item['categories']),
        'author': 'Gautam Kamath',
    })
(ROOT / '_source/posts.json').write_text(json.dumps(records, indent=2, ensure_ascii=False) + '\n')
(ROOT / '_source/media.json').write_text(json.dumps(assets, indent=2) + '\n')
print(f'Imported {len(records)} posts/pages and {len(assets)} local images (including equations).')
