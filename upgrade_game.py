#!/usr/bin/env python3
"""upgrade_game.py — generate a MAJORLY upgraded Galaga v2 through the pool:
levels, special enemies, environments, graphics, enemy design, high-score system."""
import time
from curl_cffi import requests as creq
from gen_game import call, extract_html, OUT

CUR = open(OUT, encoding="utf-8").read()

PROMPT = """Massively upgrade this Galaga clone into a polished, feature-rich arcade game. Keep it a SINGLE
self-contained HTML file (inline CSS+JS, NO external libraries), canvas 480x640. Preserve the working
core (game loop, player movement+shooting, held-key input, screen-shake with setTransform reset, restart
clears stale bullets, squadron dive with a concurrency cap, collision, particles, starfield).

ADD ALL OF THESE FEATURES (this is the big upgrade):

1. LEVELS with distinct ENVIRONMENTS (advance every 3 waves; on level-up show "LEVEL N — <name>" splash,
   and CHANGE the background + enemy palette):
   - Level 1 "Deep Space": dark starfield (current).
   - Level 2 "Nebula": drifting purple/pink gas clouds (semi-transparent radial gradients) over stars.
   - Level 3 "Asteroid Belt": large drifting rocky asteroids in the background + a few foreground ones.
   - Level 4 "Alien Homeworld": a big planet/sun glow at the top + alien-green sky gradient.
   - Level 5+ "Void": cycles with faster enemies and a red/black theme.

2. SPECIAL ENEMIES with NEW MECHANICS (distinct SHAPE + COLOR + behavior, drawn with canvas paths, not
   plain rectangles):
   - GRUNT (red, small bug shape): basic, dives in squadrons.
   - TANK (orange, chunky 3-lobe shape): takes 3 hits (hitPoints), slow, fires a 3-way spread.
   - SHIELD (green, has a glowing ring): a shield absorbs the first 2 hits (flash on shield-break).
   - SPLITTER (magenta, two-lobed): splits into 2 small FAST grunts when destroyed.
   - FAST (cyan, dart shape): dives 2x speed, low HP.
   - BOSS (every 5 waves, large multi-part ship at top with a health bar drawn across the top): slowly
     sweeps side-to-side, fires aimed 3-bullet bursts + a radial spray, 40+ HP. Defeating it awards big
     bonus points and spawns a big explosion.

3. SPECIAL LEVELS:
   - BONUS CHALLENGE WAVE (every 4th wave): a stream of FAST enemies that only dive (no shooting), worth
     2x points, with a countdown timer; surviving clears it for a bonus.
   - BOSS WAVE (every 5th wave): only the BOSS (plus a few grunts).

4. AMAZING GRAPHICS:
   - Gradient/gas backgrounds with parallax (two background layers moving at different speeds).
   - Glow via canvas shadowBlur on bullets, the player engine flame, and explosions.
   - Animated player ship with an engine flame that flickers; subtle banking when moving.
   - Enemy idle animation (tiny hover bob + occasional wing/tentacle flick).
   - Screen-flash + big particle burst on boss death; level-transition fade.

5. BETTER ENEMY DESIGN: draw each enemy type with distinct canvas paths (bug bodies, wings, eyes, antennae,
   armor), sized ~30-40px, not rectangles. Keep the color tiers but give each a recognizable silhouette.

6. HIGH SCORE SYSTEM:
   - Persist a TOP-10 leaderboard in localStorage (name + score + level).
   - On game over, if the score makes the top 10, show a 3-letter INITIALS entry (arcade style: cursor
     over A-Z, arrows to change, Enter to lock).
   - Start screen shows the TOP-5 high scores under the title.
   - Track + show level reached on game over.

DO NOT break: player 3 lives + respawn grace flicker, score + wave + level HUD, pause (P), Enter
start/restart, high score auto-save, restart clears all per-run arrays, squadron dive cap.

Here is the current code:
---CURRENT---
%s
---END---

Output ONLY the complete upgraded HTML file — no markdown fences, no commentary. It must run with zero
errors and all new features actually working.
""" % CUR

t0 = time.time()
content, usage, model = call(PROMPT, max_tok=8000)
if not content:
    print("FAILED (pool unavailable)")
    raise SystemExit(1)
html = extract_html(content)
open(OUT, "w", encoding="utf-8").write(html)
print(f"upgrade done: model={model} total={usage.get('total_tokens')} in {time.time()-t0:.1f}s -> {len(html)} chars")
