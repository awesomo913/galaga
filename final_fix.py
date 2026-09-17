#!/usr/bin/env python3
"""final fix — restart must clear stale bullets/particles so the respawned player
isn't instantly hit by leftover enemy fire."""
import time
from curl_cffi import requests as creq
from gen_game import call, extract_html, OUT

CUR = open(OUT, encoding="utf-8").read()

PROMPT = """Fix ONE remaining confirmed bug (plus a small polish) in this Galaga clone. Keep it a SINGLE
self-contained HTML file (inline CSS+JS, no external libraries), canvas 480x640.

CONFIRMED BUG — RESTART DOESN'T CLEAR STALE PROJECTILES:
The ENTER/restart handler resets lives/score/wave and calls createEnemies(), but it does NOT clear
`enemyBullets`, `playerBullets`, or `particles`. Leftover enemy bullets from the previous game keep
moving and instantly hit the freshly-respawned player, dropping lives immediately (measured: player
respawned with lives=1 instead of 3). FIX: in the ENTER restart branch, clear enemyBullets = [],
playerBullets = [], particles = [] (and any other per-run arrays) BEFORE createEnemies().

POLISH — WAVE CLEAR BREATHING ROOM:
When the last enemy is destroyed, add a ~0.8s pause showing "WAVE CLEARED" (or the next wave number)
before createEnemies() spawns the next formation, so the player sees the transition. During this pause,
skip the enemies.length===0 -> wave++ -> createEnemies() immediate respawn (use a waveClearTimer).

DO NOT break anything that already works: formation is visible at start, formation bobs, screen shake
resets the transform (setTransform(1,0,0,1,0,0) at frame start), diving enemies return to grid slots via
the sine loop, player boundary clamp, held-key movement, scoring/highscore/localStorage, 3 lives.

Here is the current code:
---CURRENT---
%s
---END---

Output ONLY the complete corrected HTML file — no markdown fences, no commentary.
""" % CUR

t0 = time.time()
content, usage, model = call(PROMPT, max_tok=6500)
if not content:
    print("FAILED")
    raise SystemExit(1)
html = extract_html(content)
open(OUT, "w", encoding="utf-8").write(html)
print(f"final fix done: total={usage.get('total_tokens')} in {time.time()-t0:.1f}s -> {len(html)} chars")
