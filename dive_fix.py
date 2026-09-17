#!/usr/bin/env python3
"""dive-rate fix — cap concurrent divers so the formation holds its grid shape."""
import time
from curl_cffi import requests as creq
from gen_game import call, extract_html, OUT

CUR = open(OUT, encoding="utf-8").read()

PROMPT = """Fix ONE gameplay bug in this Galaga clone. Keep it a SINGLE self-contained HTML file (inline
CSS+JS, no external libraries), canvas 480x640.

CONFIRMED BUG — TOO MANY ENEMIES DIVE SIMULTANEOUSLY:
The dive trigger is `Math.random() < 0.01 * (1 + wave/10)` per enemy per frame. With 32 enemies at
60fps that is ~19 dive-starts per SECOND, and since each dive lasts ~2s, the ENTIRE formation is diving
at once — the grid never holds its shape, enemies overlap and fly through each other, and it looks like
chaos instead of Galaga's orderly formation.

FIX — SQUADRON DIVE, AUTHENTIC GALAGA:
- Track a global `diversActive` count and a `squadronCooldown` timer.
- Only allow a dive to START when diversActive < 4 (scale the cap up slightly with wave, max ~6).
- When a dive starts, increment diversActive; when it ends (diveCooldown hits 0), decrement it.
- Add a `squadronCooldown` (~1.5-2.5s) between dive squadrons: when a dive triggers, start a small group
  (2-4 adjacent enemies) together, then wait squadronCooldown before allowing the next group. This gives
  the classic Galaga rhythm: formation holds steady, then a small squadron peels off and loops down.
- Keep the dive path (sine loop returning to gridX/gridY), the dive shot, and the wave-based speed-up.

DO NOT break: formation visible at start, formation bobbing, screen shake transform reset, restart clears
stale bullets, wave increment + clear pause, player boundary clamp, held-key movement, scoring/highscore,
3 lives, particles, starfield.

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
print(f"dive-rate fix done: total={usage.get('total_tokens')} in {time.time()-t0:.1f}s -> {len(html)} chars")
