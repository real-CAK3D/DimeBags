# Dime Bags

The Garden's nightly betting sheet — pretend Garden Bucks only. Every evening at 9:30 a new card: Player of the Game, a tokens over/under, a clean-sheet bet, Lights Out and a CHRONIC prop, with odds worked out from the Garden's own history. Tap a line to bet; everything settles when the morning paper lands.

Part of the Garden's papers, all read through **[The Corner Chronicle](https://github.com/real-CAK3D/NewsStand)** — one home-screen app that mounts every paper under one private (Tailscale-only) HTTPS address: [The Double Wide](https://github.com/real-CAK3D/TheDoubleWide) (daily), [The Re-Up](https://github.com/real-CAK3D/TheRe-Up) (want ads), [The Sunday Smoke](https://github.com/real-CAK3D/TheSundaySmoke) (Sundays), [Roach Clips](https://github.com/real-CAK3D/RoachClips) (Tuesdays), [The Green Thumb](https://github.com/real-CAK3D/TheGreenThumb) (the directory), [Dime Bags](https://github.com/real-CAK3D/DimeBags), [Trail Mix](https://github.com/real-CAK3D/TrailMix), [Dab Magazine](https://github.com/real-CAK3D/DabMagazine), [Hashish](https://github.com/real-CAK3D/Hashish), [The Perennial](https://github.com/real-CAK3D/ThePerennial), [Baked Goods](https://github.com/real-CAK3D/BakedGoods) and [Extra! Extra!](https://github.com/real-CAK3D/ExtraExtra). The papers are written by [Hermes](https://github.com/NousResearch/hermes-agent) agents running on a small Oracle VM called The Garden.

## Files

| File | What it does |
|---|---|
| `build_tips.py` | `card` sets tonight's odds, `settle` pays out from the morning's payroll/usage/extras, `build` prints the pages. |
| `serve.py` | Your wallet and bet slips (pretend money only). |
| `site/js/tips.js` | The bet slip and wallet on the page. |
| `gardenweb.py` | The small shared web-server kit every Garden paper carries its own copy of. |

## Running

Card at 21:30 Eastern, settled after The Double Wide; served at `/dime-bags/` under The Corner Chronicle. Each project is Linux-first (`%-d` date formatting) and expects a Hermes install on the same machine.
