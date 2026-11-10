"""Build the blog using Python's standard library: python3 scripts/build.py."""
from datetime import datetime
from email.utils import format_datetime
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://blog.gautamkamath.com'
records = json.loads((ROOT / '_source/posts.json').read_text())
posts = sorted((x for x in records if x['type'] == 'post'), key=lambda x: x['date'], reverse=True)

class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts = []
    def handle_data(self, text): self.parts.append(text)

def plaintext(body):
    parser = Text(); parser.feed(body)
    return re.sub(r'\s+', ' ', ' '.join(parser.parts)).strip()

def date(post):
    dt = datetime.fromisoformat(post['date'])
    return f'{dt.day} {dt:%B %Y}'

def excerpt(post):
    body = (ROOT / post['source']).read_text()
    match = re.search(r'<p\b[^>]*>(.*?)</p>', body, re.S)
    text = plaintext(match[1] if match else body)
    return text if len(text) <= 230 else text[:227].rsplit(' ', 1)[0] + '…'

def page(path, title, content, description, article=None):
    target = ROOT / path / 'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    prefix = os.path.relpath(ROOT, target.parent)
    fulltitle = title + ' · Kamathematics' if title != 'Kamathematics' else title
    canonical = DOMAIN + '/' + (path.strip('/') + '/' if path else '')
    content = content.replace('{{ROOT}}', prefix)
    doc = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(fulltitle)}</title><meta name="description" content="{html.escape(description, quote=True)}">
<link rel="canonical" href="{canonical}"><meta property="og:title" content="{html.escape(fulltitle, quote=True)}">
<meta property="og:description" content="{html.escape(description, quote=True)}"><meta property="og:type" content="{'article' if article else 'website'}"><meta property="og:url" content="{canonical}">
<link rel="stylesheet" href="{prefix}/assets/style.css"><link rel="icon" href="{prefix}/assets/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="Kamathematics" href="{prefix}/feed.xml">
</head><body><a class="skip" href="#main">Skip to content</a>
<header class="site-header"><a class="wordmark" href="{prefix}/">Kamathematics</a>
<nav aria-label="Main navigation"><a href="{prefix}/">Posts</a><a href="https://www.gautamkamath.com/">Homepage</a></nav></header>
<main id="main">{content}</main>
<footer><span>© {max(x['date'][:4] for x in records)} Gautam Kamath · Kamathematics</span><div><a href="{prefix}/feed.xml">RSS</a><a href="https://www.gautamkamath.com/">Academic homepage</a></div></footer>
</body></html>'''
    target.write_text(doc)

content = '<section class="archive" aria-label="Post archive">'
for year in sorted({x['date'][:4] for x in posts}, reverse=True):
    content += f'<section class="year"><h2>{year}</h2><ul class="post-list">'
    for post in posts:
        if post['date'].startswith(year):
            dt = datetime.fromisoformat(post['date'])
            content += f'<li><time datetime="{post["date"][:10]}">{dt:%b} {dt.day}</time><a href="{{{{ROOT}}}}/{post["path"]}/">{html.escape(post["title"])}</a></li>'
    content += '</ul></section>'
content += '</section>'
page('', 'Kamathematics', content, 'The blog of Gautam Kamath.')

for item in records:
    body = (ROOT / item['source']).read_text()
    heading = f'<header class="article-header"><a class="back" href="{{{{ROOT}}}}/">← All posts</a><h1>{html.escape(item["title"])}</h1>'
    if item['type'] == 'post':
        heading += f'<p class="meta"><time datetime="{item["date"][:10]}">{date(item)}</time> <span>·</span> {html.escape(item.get("byline", item["author"]))}</p>'
    heading += '</header>'
    nav = ''
    if item['type'] == 'post':
        index = posts.index(item)
        nav = '<nav class="post-nav" aria-label="More posts">'
        for pos, label in [(index + 1, 'Older post'), (index - 1, 'Newer post')]:
            if 0 <= pos < len(posts):
                other = posts[pos]
                nav += f'<a href="{{{{ROOT}}}}/{other["path"]}/"><span>{label}</span>{html.escape(other["title"])}</a>'
        nav += '</nav>'
    page(item['path'], item['title'], '<article class="article">' + heading + '<div class="prose">' + body + '</div>' + nav + '</article>', excerpt(item), article=item)

feed = '<?xml version="1.0" encoding="utf-8"?><rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/"><channel><title>Kamathematics</title><link>' + DOMAIN + '</link><description>Essays and notes by Gautam Kamath</description><language>en</language><atom:link href="' + DOMAIN + '/feed.xml" rel="self" type="application/rss+xml"/>'
for post in posts:
    url = DOMAIN + '/' + post['path'] + '/'
    feed += '<item><title>' + escape(post['title']) + '</title><link>' + url + '</link><guid isPermaLink="true">' + url + '</guid><pubDate>' + format_datetime(datetime.fromisoformat(post['date'])) + '</pubDate><dc:creator>' + escape(post.get('byline', post['author'])) + '</dc:creator><description>' + escape((ROOT / post['source']).read_text().replace('{{ROOT}}', DOMAIN)) + '</description></item>'
feed += '</channel></rss>'
(ROOT / 'feed.xml').write_text(feed)
(ROOT / 'sitemap.xml').write_text('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>' + DOMAIN + '/' + x + '</loc></url>' for x in [''] + [p['path'] + '/' for p in records]) + '</urlset>')
(ROOT / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + DOMAIN + '/sitemap.xml\n')
page('404', 'Page not found', '<section class="intro"><p class="eyebrow">404</p><h1>Page not found.</h1><p><a href="{{ROOT}}/">Return to all posts</a></p></section>', 'Page not found')
# A GitHub Pages custom 404 uses root-relative assets and links.
notfound = (ROOT / '404/index.html').read_text().replace('../', '/')
(ROOT / '404.html').write_text(notfound)
(ROOT / '404/index.html').unlink()
(ROOT / '404').rmdir()
print(f'Built {len(posts)} posts, archive, RSS, sitemap, and 404 page.')

# Preserve old About links without maintaining a separate biography.
(ROOT / 'about').mkdir(exist_ok=True)
(ROOT / 'about/index.html').write_text('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n<title>Gautam Kamath</title><meta http-equiv="refresh" content="0; url=https://www.gautamkamath.com/">\n<link rel="canonical" href="https://www.gautamkamath.com/"><meta name="robots" content="noindex"></head>\n<body><p><a href="https://www.gautamkamath.com/">Continue to Gautam Kamath’s homepage.</a></p></body></html>\n')
