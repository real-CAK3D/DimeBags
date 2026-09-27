#!/usr/bin/env python3
"""DIME BAGS — the Garden's betting sheet (pretend Garden Bucks only).

  build_tips.py card     tonight's card: odds from the Garden's own history (run 21:30)
  build_tips.py settle   settle last night's card from the morning's payroll/usage/extras (run after The Double Wide)
  build_tips.py build    reprint the pages

Markets: Player of the Game, tokens over/under, a clean sheet (no failed shifts), a machine going dark, CHRONIC grading an A.
Odds use the history in The Double Wide's data files, with sensible starting guesses while the history is short.
"""
import datetime as dt, glob, json, os, statistics, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")
sys.path.insert(0, ROOT)
import pubkit as pk   # noqa: E402
import flipbook as fb   # noqa: E402
from pubkit import e   # noqa: E402

fb.CSS_FILE = "tip-sheet.css"
DWD = os.path.join(pk.DW, "site", "data")
GRADE = {"A": 3.0, "B": 2.0, "C": 1.4, "D": 1.0, "F": 0.4}
FRACTIONS = [(1, 5), (1, 4), (1, 3), (2, 5), (1, 2), (4, 7), (4, 6), (4, 5), (10, 11), (1, 1), (6, 5), (6, 4), (7, 4), (2, 1), (9, 4), (5, 2),
             (3, 1), (7, 2), (4, 1), (9, 2), (5, 1), (6, 1), (7, 1), (8, 1), (10, 1), (12, 1), (14, 1), (16, 1), (20, 1), (25, 1), (33, 1), (50, 1)]
MARGIN = 1.10   # the bookie's cut


def odds_for(p):
    p = min(max(p * MARGIN, 0.02), 0.95)
    target = (1 - p) / p
    return min(FRACTIONS, key=lambda f: abs(f[0] / f[1] - target))


def payroll_files(n=14):
    return [pk.load(f) for f in sorted(glob.glob(os.path.join(DWD, "payroll-20*.json")))[-n:]]


def usage_totals(n=7):
    return [pk.load(f).get("total") or 0 for f in sorted(glob.glob(os.path.join(DWD, "usage-20*.json")))[-n:]]


def card(date):
    pays = payroll_files()
    score, seen = {}, {}
    for p in pays:
        for r in p.get("rows") or []:
            if r.get("jobs"):
                score[r["agent"]] = score.get(r["agent"], 0) + GRADE.get(r.get("grade"), 1.0)
                seen[r["agent"]] = seen.get(r["agent"], 0) + 1
    wins = {}
    for d in sorted(glob.glob(os.path.join(ROOT, "data", "results-*.json"))):
        w = pk.load(d).get("potg")
        if w:
            wins[w] = wins.get(w, 0) + 1
    strength = {a: (score[a] / seen[a]) ** 2 * (1 + 0.5 * wins.get(a, 0)) for a in score}
    total = sum(strength.values()) or 1
    potg = sorted(({"id": a, "label": a, "p": v / total} for a, v in strength.items()), key=lambda o: -o["p"])[:10]
    tok = [t for t in usage_totals() if t]
    line = round((statistics.median(tok) if tok else 5e6) / 1e5) / 10   # millions, one decimal
    clean_hist = [all(r.get("grade") != "F" for r in p.get("rows") or [] if r.get("jobs")) for p in pays]
    p_clean = (sum(clean_hist) + 1.2) / (len(clean_hist) + 2)
    chron = [r.get("grade") == "A" for p in pays for r in p.get("rows") or [] if r.get("agent") == "CHRONIC" and r.get("jobs")]
    p_chron = (sum(chron) + 0.8) / (len(chron) + 2)
    markets = [
        {"id": "potg", "title": "Player of the Game", "desc": "Who takes Employee of the Day on tomorrow morning's Payroll?", "options": potg},
        {"id": "tokens", "title": "Tokens Over/Under %.1fM" % line, "desc": "Total tokens burned across the Garden tomorrow — settles the morning after, from the Token Average's close.",
         "line": line * 1e6, "options": [{"id": "over", "label": "Over %.1fM" % line, "p": 0.5}, {"id": "under", "label": "Under %.1fM" % line, "p": 0.5}]},
        {"id": "clean", "title": "Clean Sheet", "desc": "Every relay shift tonight finishes without an F on the payroll.",
         "options": [{"id": "yes", "label": "Yes — a clean night", "p": p_clean}, {"id": "no", "label": "No — somebody drops the ball", "p": 1 - p_clean}]},
        {"id": "dark", "title": "Lights Out", "desc": "A Garden machine goes dark long enough for an Extra! Extra! before the morning paper.",
         "options": [{"id": "yes", "label": "Yes — an Extra prints", "p": 0.15}, {"id": "no", "label": "No — all quiet", "p": 0.85}]},
        {"id": "chronic", "title": "CHRONIC Grades an A", "desc": "Prop bet: CHRONIC's sorting shift earns an A on tomorrow's payroll.",
         "options": [{"id": "yes", "label": "Yes", "p": p_chron}, {"id": "no", "label": "No", "p": 1 - p_chron}]},
    ]
    for m in markets:
        for o in m["options"]:
            o["odds"] = list(odds_for(o["p"]))
    c = {"date": date, "closes": "22:45", "markets": markets}
    pk.save(os.path.join(ROOT, "data", "card-%s.json" % date), c)
    return c


def settle(date):
    """Settle the card for `date` (last night) using the morning's files (report day = date)."""
    c = pk.load(os.path.join(ROOT, "data", "card-%s.json" % date))
    if not c:
        return None
    nxt = (dt.date.fromisoformat(date) + dt.timedelta(days=1)).isoformat()
    pay = pk.load(os.path.join(DWD, "payroll-%s.json" % nxt))
    use = pk.load(os.path.join(DWD, "usage-%s.json" % (dt.date.fromisoformat(nxt) + dt.timedelta(days=1)).isoformat())) or {}
    res = {"date": date}
    if pay:
        res["potg"] = (pay.get("employee_of_the_day") or {}).get("agent")
        rows = [r for r in pay.get("rows") or [] if r.get("jobs")]
        res["clean"] = "yes" if rows and all(r.get("grade") != "F" for r in rows) else "no"
        ch = next((r for r in rows if r.get("agent") == "CHRONIC"), None)
        res["chronic"] = "yes" if ch and ch.get("grade") == "A" else "no"
    if use.get("total"):
        line = next(m["line"] for m in c["markets"] if m["id"] == "tokens")
        res["tokens"] = "over" if use["total"] > line else "under"
        res["tokens_total"] = use["total"]
    start = dt.datetime.fromisoformat(date + "T21:30:00").astimezone()
    extras = [pk.load(f) for f in glob.glob(os.path.join(pk.GARDEN, "extra-extra", "data", "*.json"))]
    dark = [x for x in extras if x.get("kind") == "outage" and start <= dt.datetime.fromisoformat(x["at"]) <= start + dt.timedelta(hours=10)]
    res["dark"] = "yes" if dark else "no"
    pk.save(os.path.join(ROOT, "data", "results-%s.json" % date), res)
    # pay out CAK3D's slips
    wallet = pk.load(os.path.join(ROOT, "private", "wallet.json"), {"balance": 1000, "bets": []})
    won = lost = 0
    for b in wallet["bets"]:
        if b.get("status") != "open" or b.get("date") != date or b["market"] not in res:
            continue
        if b["option"] == res[b["market"]]:
            pay_out = round(b["stake"] + b["stake"] * b["odds"][0] / b["odds"][1])
            b.update(status="won", payout=pay_out)
            wallet["balance"] += pay_out
            won += pay_out - b["stake"]
        else:
            b.update(status="lost", payout=0)
            lost += b["stake"]
    pk.save(os.path.join(ROOT, "private", "wallet.json"), wallet)
    if won or lost:
        pk.notify("🏇 Dime Bags settled", "Last night: %s%d Garden Bucks. Balance: %d." % ("+" if won >= lost else "-", abs(won - lost), wallet["balance"]), "/dime-bags/")
    return res


def odds_txt(o):
    return "%d-%d" % tuple(o["odds"]) if o["odds"][1] != 1 else "%d-1" % o["odds"][0]


def build():
    cards = sorted(glob.glob(os.path.join(ROOT, "data", "card-*.json")))
    c = pk.load(cards[-1]) if cards else card(dt.date.today().isoformat())
    date = c["date"]
    d = dt.date.fromisoformat(date)
    no = (d - dt.date(2026, 9, 27)).days + 1
    res_files = sorted(glob.glob(os.path.join(ROOT, "data", "results-*.json")))
    last = pk.load(res_files[-1]) if res_files else {}
    rows = []
    for m in c["markets"]:
        opts = "".join('<button type="button" class="tip-opt" data-m="%s" data-o="%s" data-odds="%d/%d" data-label="%s"><span>%s</span><b>%s</b></button>'
                       % (e(m["id"]), e(o["id"]), o["odds"][0], o["odds"][1], e(o["label"]), e(o["label"]), odds_txt(o)) for o in m["options"])
        rows.append('<div class="tip-mkt"><div class="tip-mh"><b>%s</b><span>%s</span></div><div class="tip-opts">%s</div></div>' % (e(m["title"]), e(m["desc"]), opts))
    fav = c["markets"][0]["options"][0] if c["markets"][0]["options"] else None
    long_ = c["markets"][0]["options"][-1] if c["markets"][0]["options"] else None
    picks = ('<div class="box tip-picks">%s<div><h2>The Bookie\'s Picks</h2><p><b>Lock of the night:</b> %s at %s — the chalk is chalk for a reason.</p>'
             '<p><b>Value play:</b> %s at %s. Long shots win sometimes; that\'s why they call it gambling.</p>'
             '<p><b>Tokens:</b> I\'m leaning <b>%s</b> the line. The PC\'s been thirsty lately.</p><p class="small">— Disco Stu, Sports Desk. Pretend money only; no real bets, ever.</p></div></div>'
             % (fb.mug("Disco Stu", "mug"), e(fav["label"]) if fav else "—", odds_txt(fav) if fav else "", e(long_["label"]) if long_ else "—",
                odds_txt(long_) if long_ else "", "over" if (usage_totals(2) or [0])[-1] > c["markets"][1]["line"] else "under"))
    names = {"potg": "Player of the Game", "tokens": "Tokens O/U", "clean": "Clean Sheet", "dark": "Lights Out", "chronic": "CHRONIC grades an A"}
    results = "".join('<tr><td>%s</td><td><b>%s</b></td></tr>' % (e(names.get(k, k)), e(v if k != "tokens" else "%s (%s)" % (v, fb._k(last.get("tokens_total")))))
                      for k, v in last.items() if k in names) if last else ""
    seal = '<a class="seal" href="/" aria-label="Back to The Corner Chronicle">%s</a>' % fb.SEAL
    pages = [
        fb.page("Dime Bags", ('<div class="gum"><span>OFFICIAL CARD · GARDEN LEAGUE · PRETEND MONEY ONLY</span></div>'
                                  '<div class="pc-top">%s<div class="ear">No. %s<br>%s<br><b>%s</b><br>%s</div></div>'
                                  '<div class="flag"><div class="est">THE GARDEN LEAGUE · LEWISTON, ME</div><h1>Dime<br>Bags</h1><div class="motto">Tonight\'s lines · last night\'s results</div></div>'
                                  '<div class="pc-band"><span>ODDS</span><span>PICKS</span><span>RESULTS</span></div>'
                                  '<div class="pc-teaser"><div class="kicker">Tonight\'s favorite</div><b>%s</b></div><div class="pc-open">Lines close at 10:45 PM ›</div>')
                % (seal, no, d.strftime("%a"), d.strftime("%b %-d"), d.strftime("%Y"), e("%s at %s" % (fav["label"], odds_txt(fav))) if fav else "—"), " hardcover"),
        fb.page("Tonight's Card", '<div class="tip-card"><h2 class="tip-h">Tonight\'s Card — %s</h2><p class="small">Tap a line to bet Garden Bucks (pretend money). Lines close at 10:45 PM; everything settles when the morning paper lands.</p>%s</div>'
                % (e(d.strftime("%A, %B %-d")), "".join(rows))),
        fb.page("The Bookie's Picks", picks),
        fb.page("Your Slips", '<div class="box tip-wallet"><h2>Your Wallet</h2><div id="tip-wallet">Loading…</div></div>'),
        fb.page("Last Night's Results", '<div class="box"><h2>Last Night\'s Results</h2>%s</div>'
                % (('<p class="small">Card of %s</p><table class="agate"><tbody>%s</tbody></table>' % (e(pk.nice(last.get("date", ""))), results)) if results else '<p class="small">Nothing settled yet — the first card settles tomorrow morning.</p>')),
        fb.page("Back Page", ('<div class="gum"><span>DIME BAGS · GARDEN LEAGUE</span></div><div class="pb-body">%s<h2 class="pb-title">Dime Bags</h2>'
                              '<p>Odds set by Disco Stu from the Garden\'s own history.<br>Pretend Garden Bucks only — nothing real is ever wagered.</p>%s'
                              '<p class="pb-code">%s · No. %s</p><p><a href="../archive.html">Back issues ›</a></p></div>')
                % (seal, fb.back_codes("https://github.com/real-CAK3D/DimeBags", "DimeBags"), date, no), " hardcover back"),
    ]
    html = fb.book(pages, date=date, no=no, lists={}, paper="Dime Bags", motto="Tonight's lines · last night's results",
                   gum="OFFICIAL CARD · GARDEN LEAGUE · PRETEND MONEY ONLY", price="PRICE: ONE DIME", delivered="ODDS BY DISCO STU",
                   flap="Dime Bags · pretend money only", body_class="pub-tip", est="THE GARDEN LEAGUE · LEWISTON, ME",
                   scripts='<script>window.TIP_DATE = "%s";</script><script src="js/tips.js"></script>' % date)
    os.makedirs(os.path.join(SITE, "issues"), exist_ok=True)
    open(os.path.join(SITE, "issues", date + ".html"), "w").write(html)
    open(os.path.join(SITE, "index.html"), "w").write(html.replace('href="../', 'href="').replace('src="../', 'src="'))
    eds = pk.issues(SITE)
    pk.archive_page(SITE, os.path.join(ROOT, fb.CSS_FILE), "pub-tip", "Dime Bags", "every card", "".join(
        '<li><a href="issues/%s.html">%s</a></li>' % (x, pk.nice(x)) for x in eds), "🏇")
    pk.latest(SITE, "Dime Bags", date, "Favorite: %s at %s" % (fav["label"], odds_txt(fav)) if fav else "Tonight's card", "issues/%s.html" % date, eds[:10])
    pk.sync_portraits(SITE)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    today = dt.datetime.now().astimezone().date()
    if cmd == "card":
        card(today.isoformat())
        build()
        pk.notify("💰 Tonight's lines are up", "Dime Bags: pick your Player of the Game before 10:45 PM.", "/dime-bags/")
    elif cmd == "settle":   # last night's card, plus the night before (its token total only lands a day later)
        for back in (2, 1):
            print("settled:", settle((today - dt.timedelta(days=back)).isoformat()))
        build()
    else:
        build()
    print("dime bags built")
