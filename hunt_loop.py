#!/usr/bin/env python3
"""
hunt_loop.py — 5-hour autonomous bug-hunt + upgrade loop for the Galaga game
(and the arcade roster), driven by the free Groq pool.

Loop (per iteration):
  1. STABILITY TEST  — load galaga.html headless, start, drive it ~30s with random
     input, capture page errors + basic invariants.
  2. If errors/broken invariants -> FIX pass (send the failure + code to the pool).
  3. If clean -> UPGRADE pass (cycle through a feature list to keep improving).
  4. Log to hunt_log.txt, persist state, sleep, repeat until 5h deadline.

Pool calls go DIRECT to keys (the rotator round-robin lands on token-cooled keys for
big requests). Each call tries up to N keys. Rate-limited -> sleep + retry next loop.
"""
import json, os, re, time, random, subprocess
from curl_cffi import requests as creq

GALAGA = "C:/Users/computer/Desktop/AI/galaga/galaga.html"
DIR = "C:/Users/computer/Desktop/AI/galaga"
LOGF = os.path.join(DIR, "hunt_log.txt")
STATEF = os.path.join(DIR, "hunt_state.json")
KEYSF = "C:/Users/computer/Desktop/AI/free-keys/free-keys.json"
MODEL = "llama-3.3-70b-versatile"
HOURS = 5

FEATURES = [
    "Fix the HUD overlap: move score/high-score/level/lives into a clear top bar with a semi-transparent background strip so the enemy formation never overlaps the text.",
    "Add POWERUPS that drop from destroyed enemies: weapon upgrade (double/triple shot), shield pickup (absorb one hit), and a screen-clearing bomb. Player picks them up by flying over them.",
    "Add a combo/score MULTIPLIER: destroying enemies in quick succession builds a combo meter that multiplies points, shown as a flash on screen.",
    "Improve the BOSS fight: give it 3 distinct attack phases (aimed bursts, radial spray, and a sweeping beam) that cycle as its health drops, plus a death sequence with a big multi-stage explosion.",
    "Add a subtle screen-space particle trail behind the player's engine and behind diving enemies, and a muzzle flash when firing.",
    "Add difficulty curve polish: enemies get slightly faster and fire more often each level, and the formation starts lower each level.",
    "Add sound polish: a distinct rising-pitch sound for the level-up splash and a low rumble during boss fights (all guarded in try/catch, audio after first gesture).",
    "Add a PAUSE overlay with 'P to resume' and a small controls legend (arrows/WASD move, space shoot, P pause) on the start screen.",
    "Add a brief invincibility + slow-motion effect (0.3s timeScale dip) when the player respawns after losing a life.",
    "Add a BONUS CHALLENGE wave every 4th wave: a stream of fast non-shooting enemies worth 2x points with a countdown, and a 'BONUS +N' reward banner if cleared.",
]

def log(m):
    line = f"[{time.strftime('%H:%M:%S')}] {m}"
    try:
        with open(LOGF, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line, flush=True)

def stability_test():
    """Load + drive the game headless, return (errors, broken_invariants)."""
    try:
        from playwright.sync_api import sync_playwright
        errs = []
        broken = []
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            pg = b.new_page(viewport={"width": 520, "height": 700})
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto("file:///C:/Users/computer/Desktop/AI/galaga/galaga.html",
                    wait_until="load", timeout=20000)
            pg.keyboard.press("Enter")
            pg.wait_for_timeout(500)
            s = pg.evaluate("() => ({playing: isPlaying, enemies: enemies.length})")
            if not s["playing"]:
                broken.append("game did not start on ENTER")
            # drive random input ~25s
            for _ in range(25):
                k = random.choice(["ArrowLeft", "ArrowRight", " ", " "])
                pg.keyboard.press(k)
                pg.wait_for_timeout(random.randint(500, 1000))
            # invariants
            inv = pg.evaluate("""() => {
                const m = ctx.getTransform();
                return {drift: (Math.abs(m.e) > 1 || Math.abs(m.f) > 1),
                        liveLives: player.lives >= 0};
            }""")
            if inv["drift"]:
                broken.append("canvas transform drift (screen shake not reset)")
            if not inv["liveLives"]:
                broken.append("player lives went negative")
            pg.screenshot(path=os.path.join(DIR, "hunt_latest.png"))
            b.close()
        return errs, broken
    except Exception as e:
        return [f"test harness error: {str(e)[:200]}"], []

def pool_gen(prompt, max_tok=7000):
    """Direct-key generation with multi-key retry."""
    d = json.load(open(KEYSF, encoding="utf-8"))
    keys = [(x["email"], x["key"]) for x in d["groq"]]
    random.shuffle(keys)
    payload = {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
               "temperature": 0.8, "max_tokens": max_tok}
    for i, (email, key) in enumerate(keys):
        if i >= 50:
            break
        try:
            r = creq.post("https://api.groq.com/openai/v1/chat/completions",
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                          json=payload, impersonate="chrome", timeout=300)
            if r.status_code == 200:
                j = r.json()
                c = (j["choices"][0]["message"].get("content") or "").strip()
                u = j.get("usage", {})
                return c, u.get("total_tokens", 0), email
        except Exception:
            pass
        time.sleep(1)
    return None, 0, None

def extract_html(text):
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        t = t.rsplit("```", 1)[0]
    t = t.strip()
    # validate completeness — a truncated (max_tokens) generation silently breaks the game
    if not t.endswith("</html>") or "</script>" not in t:
        log(f"  !! REJECTED truncated/broken generation (len={len(t)}, ends={'</html>' if t.endswith('</html>') else 'INCOMPLETE'})")
        return None
    return t

def main():
    deadline = time.time() + HOURS * 3600
    state = {"iters": 0, "fixes": 0, "upgrades": 0, "tokens": 0, "feat_idx": 0}
    if os.path.exists(STATEF):
        try:
            state = json.load(open(STATEF, encoding="utf-8"))
        except Exception:
            pass
    log(f"=== HUNT LOOP start: {HOURS}h, state={json.dumps(state)} ===")

    while time.time() < deadline:
        state["iters"] += 1
        cur = open(GALAGA, encoding="utf-8").read()
        errs, broken = stability_test()
        problems = [e for e in errs] + broken

        if problems:
            log(f"[iter {state['iters']}] FOUND {len(problems)} problem(s): {problems[:3]}")
            prompt = (f"Fix these CONFIRMED bugs in this Galaga game (single self-contained HTML file, "
                      f"inline CSS+JS, no external libraries, canvas 480x640):\n\n"
                      f"BUGS:\n" + "\n".join(f"- {p}" for p in problems[:6]) + "\n\n"
                      f"Keep ALL existing features (levels/environments, grunt/tank/shield/splitter/fast/boss, "
                      f"boss health bar, high-score leaderboard with initials, squadron dive cap, screen shake "
                      f"with setTransform reset, restart clears stale bullets).\n\n"
                      f"Here is the current code:\n---CURRENT---\n{cur}\n---END---\n\n"
                      f"Output ONLY the complete corrected HTML file — no markdown fences, no commentary.")
            content, tok, email = pool_gen(prompt)
            html = extract_html(content) if content else None
            if html:
                import shutil
                shutil.copy(GALAGA, GALAGA + ".bak")
                open(GALAGA, "w", encoding="utf-8").write(html)
                state["fixes"] += 1
                state["tokens"] += tok
                log(f"  fixed via {email} (+{tok} tok)")
            else:
                log("  fix pass failed (pool rate-limited or truncated) — retry next loop")
        else:
            feat = FEATURES[state["feat_idx"] % len(FEATURES)]
            state["feat_idx"] += 1
            log(f"[iter {state['iters']}] clean — upgrade: {feat[:60]}...")
            prompt = (f"Upgrade this Galaga game (single self-contained HTML file, inline CSS+JS, no external "
                      f"libraries, canvas 480x640). Do this ONE improvement without breaking anything:\n\n"
                      f"IMPROVEMENT: {feat}\n\n"
                      f"Here is the current code:\n---CURRENT---\n{cur}\n---END---\n\n"
                      f"Output ONLY the complete upgraded HTML file — no markdown fences, no commentary.")
            content, tok, email = pool_gen(prompt)
            html = extract_html(content) if content else None
            if html:
                import shutil
                shutil.copy(GALAGA, GALAGA + ".bak")
                open(GALAGA, "w", encoding="utf-8").write(html)
                state["upgrades"] += 1
                state["tokens"] += tok
                log(f"  upgraded via {email} (+{tok} tok)")
            else:
                log("  upgrade failed (pool rate-limited or truncated) — retry next loop")

        json.dump(state, open(STATEF, "w", encoding="utf-8"))
        time.sleep(120)  # pace: ~2 min between iterations (gentle on rate limits)

    log(f"=== HUNT LOOP end: {json.dumps(state)} ===")

if __name__ == "__main__":
    main()
