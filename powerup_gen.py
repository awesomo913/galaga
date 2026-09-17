import json, time
from curl_cffi import requests as creq

POOL = "http://127.0.0.1:8689/v1/chat/completions"

PROMPT = """You are adding a POWERUP system to a working HTML5 canvas Galaga game (single self-contained HTML file, inline CSS+JS, no external libraries, canvas 480x640, runs at 60fps with `requestAnimationFrame`).

The game already has these globals: `player` (object with .x/.y/.w/.h/.speed/.cooldown/.lives/.score/.highScore/.wave/.level), `enemies` (array), `enemyBullets`, `playerBullets`, `particles` (arrays), `ctx` (2d context), `checkAABB(a,b)` (returns bool), `createParticles(x,y)`, `shakeDuration`, `gracePeriod`.

Add THREE powerup types that drop from destroyed enemies:
- 'weapon' (red 'W'): double shot for 8 seconds
- 'shield' (cyan 'S'): absorb the next hit
- 'bomb' (orange 'B'): instantly clear all enemies and enemy bullets on pickup

Return ONLY these clearly-labeled sections (plain JS, no markdown fences, no commentary):

SECTION A — declarations (add these variables near the other arrays):
- a `powerups` array
- `player.weaponTimer` (number, seconds remaining)
- `player.shield` (boolean)

SECTION B — three functions:
1. `spawnPowerup(x, y)` — randomly pick 'weapon'/'shield'/'bomb', push {type, x, y, w:16, h:16, speed:2, t:0} to `powerups`.
2. `updatePowerups()` — move each powerup down by its speed, remove if past bottom; on overlap with `player` (use checkAABB), apply the effect and remove it: weapon -> weaponTimer=8; shield -> player.shield=true; bomb -> enemies.length=0 AND enemyBullets.length=0 plus createParticles(player.x,player.y) and shakeDuration=0.5.
3. `drawPowerups()` — draw each powerup as a small glowing rounded square (16x16) with its letter centered ('W' red for weapon, 'S' cyan for shield, 'B' orange for bomb), with a subtle pulsing size via its .t timer (increment .t in update).

SECTION C — the modified firing code. Current firing (inside handleKeydown on space):
```
if (player.cooldown <= 0) {
    let bullet = { x: player.x + player.w / 2, y: player.y, w: 5, h: 5, speed: 5 };
    playerBullets.push(bullet);
    player.cooldown = 0.5;
}
```
Rewrite so when `player.weaponTimer > 0`, it fires TWO bullets offset by +8 and -8 in x instead of one. Also decrement `player.weaponTimer` by 1/60 each frame (you can note this goes in the update loop).

SECTION D — the modified player-hit handling. Current (enemy bullet hits player):
```
player.lives--;
gracePeriod = 2;
createParticles(player.x, player.y);
shakeDuration = 0.5;
```
Rewrite so if `player.shield` is true, instead: set `player.shield = false`, createParticles, shakeDuration = 0.3, and do NOT decrement lives (absorbed).

SECTION E — integration notes (one line each, describe where to insert): call `updatePowerups()` and `drawPowerups()` in the render/update loop, and call `spawnPowerup(enemy.x, enemy.y)` with ~12% probability whenever an enemy is destroyed (use `if (Math.random() < 0.12) spawnPowerup(enemy.x, enemy.y)` in every enemy-death branch).

Output ONLY the five labeled sections. Do not output the whole game."""

payload = {"model": "openai/gpt-oss-120b",
           "messages": [{"role": "user", "content": PROMPT}],
           "temperature": 0.4, "max_tokens": 3000}

for attempt in range(3):
    try:
        r = creq.post(POOL, json=payload, impersonate="chrome", timeout=300)
        r.raise_for_status()
        m = r.json()["choices"][0]["message"]
        out = (m.get("content") or "").strip() or (m.get("reasoning") or "").strip()
        print(out)
        break
    except Exception as e:
        print(f"attempt {attempt+1} failed: {str(e)[:150]}")
        time.sleep(15)
