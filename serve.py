#!/usr/bin/env python3
"""Dime Bags web server (Tailscale-only; mounted at /dime-bags/ under The Corner Chronicle).

  GET  /api/wallet                               -> {"balance": N, "bets": [...]}   (pretend Garden Bucks)
  POST /api/bet {date, market, option, stake}    -> places a bet on tonight's card until the lines close (10:45 PM)
Usage: serve.py <site_dir> <host> <port>
"""
import datetime as dt, os, sys

import gardenweb as gw
from gardenweb import jload, jsave, LOCK, wallet_tx

ROOT = os.path.dirname(os.path.abspath(__file__))
WALLET = os.path.join(ROOT, "private", "wallet.json")


class Handler(gw.Handler):
    ROOT = ROOT

    def get_api(self, p):
        if p == "/api/wallet":
            self.json(200, wallet_tx(lambda w: dict(w)))
            return True

    def post_api(self, p):
        if p != "/api/bet":
            return False
        req = self.body()
        date, mk, opt, stake = str(req.get("date")), str(req.get("market")), str(req.get("option")), int(req.get("stake") or 0)
        card = jload(os.path.join(ROOT, "data", "card-%s.json" % date), {})
        m = next((x for x in card.get("markets") or [] if x["id"] == mk), None)
        o = next((x for x in (m or {}).get("options") or [] if x["id"] == opt), None)
        now = dt.datetime.now().astimezone()
        if not (m and o) or stake not in (10, 25, 50, 100, 250):
            self.json(400, {"ok": False, "message": "That line isn't on tonight's card."})
            return True
        if now.date().isoformat() != date or now.strftime("%H:%M") > card.get("closes", "22:45"):
            self.json(200, {"ok": False, "message": "Lines are closed for this card — tomorrow night's card opens at 9:30 PM."})
            return True
        def place(w):
            if w["balance"] < stake:
                return False
            w["balance"] -= stake
            w["bets"].append({"date": date, "market": mk, "market_title": m["title"], "option": opt, "label": o["label"], "odds": o["odds"],
                              "stake": stake, "status": "open", "at": now.isoformat(timespec="seconds")})
            return True
        if not wallet_tx(place):
            self.json(200, {"ok": False, "message": "Not enough Garden Bucks for that one."})
            return True
        self.json(200, {"ok": True, "message": "Slip placed: %d on %s at %d-%d. Good luck!" % (stake, o["label"], o["odds"][0], o["odds"][1])})
        return True


if __name__ == "__main__":
    gw.run(Handler, sys.argv[1], sys.argv[2], int(sys.argv[3]))
