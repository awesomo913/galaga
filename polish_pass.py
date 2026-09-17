#!/usr/bin/env python3
"""polish pass — send the current game + a targeted improvement list back through
the pool. Each pass = more tokens through the pool = more of the theory tested."""
import time
from curl_cffi import requests as creq
from gen_game import call, extract_html, OUT

CUR = open(OUT, encoding="utf-8").read()

PROMPT = """Improve this working Galaga clone into a POLISHED, authentic arcade experience. Keep it a
SINGLE self-contained HTML file (inline CSS+JS, no external libraries), canvas 480x640.

Here is the current code:
---CURRENT---
%s
---END---

Fix and improve ALL of the following (these are real defects in the current code):

1. GALAGA SIGNATURE DIVE: replace the straight-line swoop with a proper looping dive. When an enemy
   dives, it should follow a curved parametric path (e.g. bezier/sine arc) from its formation slot,
   loop down toward the player, fire a shot at the apex, then curve back UP to rejoin its exact
   formation slot. Track each enemy's home slot (gridX, gridY) so it returns precisely. Multiple
   enemies can dive simultaneously (2-4 per wave), faster in later waves.

2. SMOOTH per-frame movement: move the player in the game loop from a held-keys state (leftHeld /
   rightHeld booleans set on keydown/keyup), NOT per keydown event. Clamp player x to [0, canvasW-w].
   Call e.preventDefault() on arrows/space so the page never scrolls.

3. SCREEN SHAKE: add a small shake offset applied to the canvas transform for ~200ms when the player
   dies (and a tiny one on enemy kill).

4. AUDIO fix: don't create AudioContext until the first user gesture (ENTER). Resume it then. Build a
   tiny oscillator-based beep helper for laser (short square sweep down), explosion (noise burst),
   and dive (descending sine). Guard every audio call in try/catch so it never crashes with sound off.

5. FIX collision splice bug: when splicing playerBullets/enemies/enemyBullets inside a loop, iterate
   BACKWARDS (i from len-1 down to 0) so no element is skipped after a splice.

6. Add a brief formation entry animation when a new wave spawns (enemies slide in from the top).

7. ENTER during play should NOT restart the game (remove that); only P toggles pause while playing.
   Show "PAUSED" text overlay when paused.

8. Keep score/highscore (localStorage), 3 lives, wave counter, lives icons, starfield, start + game
   over screens. Increase enemy fire rate slightly each wave for difficulty.

Output ONLY the complete corrected HTML file — no markdown fences, no commentary. It must run with
zero errors immediately.
""" % CUR

t0 = time.time()
content, usage, model = call(PROMPT, max_tok=6000)
dt = time.time() - t0
if not content:
    print("FAILED (pool unavailable)")
    raise SystemExit(1)
html = extract_html(content)
open(OUT, "w", encoding="utf-8").write(html)
print(f"polish pass done: model={model} "
      f"prompt_tok={usage.get('prompt_tokens')} completion_tok={usage.get('completion_tokens')} "
      f"total={usage.get('total_tokens')} in {dt:.1f}s -> {len(html)} chars")
