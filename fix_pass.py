#!/usr/bin/env python3
"""fix pass — send the 5 confirmed bugs + current code to the pool for a corrected version."""
import time
from curl_cffi import requests as creq
from gen_game import call, extract_html, OUT

CUR = open(OUT, encoding="utf-8").read()

PROMPT = """Fix these 5 CONFIRMED bugs in this Galaga clone. Keep it a SINGLE self-contained HTML file
(inline CSS+JS, no external libraries), canvas 480x640.

CONFIRMED BUGS (from automated testing — fix ALL of them):

1. FORMATION INVISIBLE AT START: createEnemies() does `enemy.y -= 200` to every enemy (as a slide-in
   animation), but there is NO animation that moves them back down. Result: the entire enemy formation
   sits off-screen (negative y) at game start and is invisible; enemies only appear when they randomly
   dive. FIX: either remove the y-offset entirely (enemies spawn at gridY), or implement a real slide-in
   animation that moves them down to gridY over ~1s and then STOPS (formation stays visible thereafter).

2. NO FORMATION BOBBING: between dives the formation is completely static. FIX: the whole formation
   should bob side-to-side slowly (classic Galaga). Track a global formation offset (sin of elapsed
   time), apply it to every non-diving enemy's x as `gridX + formationBob`. Keep enemies within canvas
   bounds.

3. SCREEN SHAKE DRIFTS THE CANVAS (critical): update() ends with `ctx.translate(shakeOffset,
   shakeOffset)` but the transform is NEVER reset, so it accumulates every frame and the whole canvas
   drifts off-screen (measured e/f drift of -51px after 1.5s of shake). FIX: at the START of loop()
   (before drawing), reset the transform with `ctx.setTransform(1,0,0,1,0,0)`, THEN if shake is active
   apply `ctx.translate(shakeOffset, shakeOffset)` once. Never translate at the end of update().

4. DIVING ENEMIES DON'T RETURN TO FORMATION: only ~10/32 enemies return to their grid slot after a dive.
   FIX: when a dive ends, ALWAYS set enemy.x = enemy.gridX and enemy.y = enemy.gridY exactly, and clear
   the dive state. Make the dive path a clean sine-based loop that starts and ends exactly at the grid
   slot (parametric: x = gridX + sin(t*2pi)*amplitude, y = gridY + sin(t*pi)*diveDepth so y returns to
   gridY at t=0 and t=1).

5. WAVE / RESPAWN ROBUSTNESS: ensure when enemies.length reaches 0, the wave increments and a new
   formation spawns VISIBLY (see bug 1), with a brief pause before the next wave so the player sees it.

ALSO: fix the starfield double-movement (drawStarfield() both draws AND increments star y, and then
update() increments it AGAIN — stars move at 2x speed; make star movement happen exactly once per frame).

Here is the current code:
---CURRENT---
%s
---END---

Output ONLY the complete corrected HTML file — no markdown fences, no commentary. It must run with zero
errors and pass these checks: formation visible at start (all enemies on-screen), formation bobs,
canvas transform stays at identity after shake, diving enemies return to their exact grid slots, wave
increments and respawns visibly.
""" % CUR

t0 = time.time()
content, usage, model = call(PROMPT, max_tok=7000)
dt = time.time() - t0
if not content:
    print("FAILED (pool unavailable)")
    raise SystemExit(1)
html = extract_html(content)
open(OUT, "w", encoding="utf-8").write(html)
print(f"fix pass done: model={model} prompt_tok={usage.get('prompt_tokens')} "
      f"completion_tok={usage.get('completion_tokens')} total={usage.get('total_tokens')} "
      f"in {dt:.1f}s -> {len(html)} chars")
