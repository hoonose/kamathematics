# Kamathematics

Gautam Kamath's blog, migrated from WordPress.com and hosted on GitHub Pages.

## Publishing

The site is static HTML, CSS, and locally stored images. It needs no paid hosting,
plugins, analytics, cookies, or browser-side JavaScript. GitHub Pages serves the
`main` branch from `/ (root)`. The custom domain is `blog.gautamkamath.com`.

1. Edit a post in `_source/posts/`, or add a new HTML body there.
2. For a new post, add its title, ISO date, path, source, author, type (`post`),
   and categories to `_source/posts.json`. Existing dated paths must stay stable.
3. Put any images in `assets/`. Use `{{ROOT}}/assets/filename` for image URLs,
   and `{{ROOT}}/YYYY/MM/DD/post-slug/` for internal links.
4. Run `python3 scripts/build.py` and `python3 scripts/check.py`.
5. Commit source and generated pages, then push to `main`.

The owner can simply provide a draft to their coding assistant and ask it to
prepare, preview, and publish the post. No manual HTML editing is required.

## Local preview

Run `python3 -m http.server 8001 --bind 127.0.0.1` in this directory, then visit
`http://localhost:8001/`. Ctrl-C stops the preview. Opening `index.html` directly
also works because navigation and asset URLs are relative.

## Migration

- 22 published posts (June 2019–June 2026), plus the About page.
- Original publication dates, titles, body text, guest-post credits, and paths retained.
- 187 local images, including the original equation images and their LaTeX alt text.
- RSS contains full post bodies. Sitemap and custom 404 included.
- Comments, likes, subscriptions, trackers, and WordPress interface elements omitted.
- `_source/media.json` records original image URLs and local destinations.
- The original WordPress site remains available; it has not been modified.

`scripts/import_wordpress.py` is the one-time import utility. Do not rerun it
over editorial changes. It expects the public API exports in `/tmp` and needs
network access. Normal publishing is completely offline until Git push.

## Domain setup

In this repository's Settings → Pages, select **Deploy from a branch**, **main**,
and **/(root)**. Set the custom domain to **blog.gautamkamath.com**.

In Namecheap Advanced DNS, add a **CNAME Record** with Host **blog**, Value
**hoonose.github.io**, TTL **Automatic**. Preserve existing `@`, `www`, and mail
records. Once GitHub verifies DNS and issues the certificate, enable **Enforce
HTTPS**. Do not change the main website's CNAME file.

After the new blog is verified online, update the academic homepage's Blog link.
Redirecting old WordPress URLs or adding a moved notice is a separate step.
