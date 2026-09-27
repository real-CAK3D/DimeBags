"""Small helpers every Garden paper project carries its own copy of: loading JSON, plain (non-flipbook) pages, the rack's
latest.json, issue listings and portraits copied from The Double Wide."""
import datetime as dt, glob, html, json, os, re, shutil, subprocess

HERMES = os.path.expanduser("~/.hermes")
GARDEN = os.path.join(HERMES, "garden")
DW = os.path.join(GARDEN, "doublewide")
PY = os.path.join(HERMES, "hermes-agent/venv/bin/python")
e = lambda s: html.escape(str(s or ""))


def load(p, default=None):
    try:
        return json.load(open(p))
    except Exception:
        return {} if default is None else default


def save(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(obj, open(p + ".tmp", "w"), ensure_ascii=False, indent=1)
    os.replace(p + ".tmp", p)


def nice(day, fmt="%A, %B %-d, %Y"):
    try:
        return dt.date.fromisoformat(day).strftime(fmt)
    except Exception:
        return day


def issues(site, folder="issues", pattern=r"\d{4}-\d{2}(-\d{2})?(T\d{4})?"):
    d = os.path.join(site, folder)
    if not os.path.isdir(d):
        return []
    return sorted((f[:-5] for f in os.listdir(d) if f.endswith(".html") and re.fullmatch(pattern, f[:-5])), reverse=True)


def sync_portraits(site):
    os.makedirs(os.path.join(site, "img"), exist_ok=True)
    for f in glob.glob(os.path.join(DW, "site", "img", "*.png")):
        dest = os.path.join(site, "img", os.path.basename(f))
        if not os.path.exists(dest) or os.path.getmtime(dest) < os.path.getmtime(f):
            shutil.copy2(f, dest)


def latest(site, paper, date, title, url="", issues_=None, **extra):
    save(os.path.join(site, "latest.json"), dict({"paper": paper, "date": date, "title": title, "url": url, "issues": issues_ or []}, **extra))


def shell(title, body, css_path, cls, theme="#2a1a10"):
    css = open(css_path).read()
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s</title><link rel="manifest" href="/manifest.webmanifest"><meta name="theme-color" content="%s">'
            '<link rel="icon" href="/icons/icon-192.png"><link href="https://fonts.googleapis.com/css2?family=Rye&family=Abril+Fatface&family=Bangers'
            '&family=Luckiest+Guy&family=Oswald:wght@400;600;700&family=Old+Standard+TT:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">'
            '<style>%s</style><script src="/app.js" defer></script></head><body class="%s">%s</body></html>' % (e(title), theme, css, cls, body))


def topbar(title, sub, home_icon="📰"):
    return ('<header class="stand-top"><a class="stand-home ns-home" href="/" aria-label="The Corner Chronicle" title="The Corner Chronicle">🏠</a>'
            '<a class="stand-home" href="./" aria-label="Latest issue">%s</a><div><h1>%s</h1><div class="stand-sub">%s</div></div>'
            '<a class="stand-home" href="archive.html" aria-label="Back issues">🗂</a></header>' % (home_icon, e(title), e(sub)))


def notify(title, body, url):
    subprocess.run([PY, os.path.join(GARDEN, "newsstand", "notify.py"), title, body, url], check=False, timeout=120)


def archive_page(site, css_path, cls, paper, sub, items_html, icon="📰"):
    body = ('%s<main class="paper"><div class="box arch"><h2>%s</h2><ul class="archive">%s</ul></div></main>'
            % (topbar("Back Issues", sub, icon), e(paper), items_html or "<li>None yet.</li>"))
    open(os.path.join(site, "archive.html"), "w").write(shell("%s — Back Issues" % paper, body, css_path, "stand " + cls))
