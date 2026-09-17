#!/usr/bin/env python3
"""gen_game.py — generate code THROUGH the Groq pool (:8688) and track token usage.

Usage:
  python gen_game.py                 # generate the full Galaga game from a strong spec
  python gen_game.py --fix           # send current game + errors back for a fix pass
"""
import json, os, sys, time, argparse
from curl_cffi import requests as creq

ROTATOR = "http://127.0.0.1:8688/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"
OUT = "C:/Users/computer/Desktop/AI/galaga/galaga.html"

SPEC = """Build a complete, polished GALAGA-style arcade shooter as a SINGLE self-contained HTML file
(inline CSS + JS, NO external libraries). Classic portrait arcade layout.

REQUIREMENTS:
- Canvas ~480x640, centered, dark space background with a scrolling starfield.
- Player ship at the bottom (cyan/white, drawn with canvas paths). Move with LEFT/RIGHT arrow keys,
  shoot with SPACE (with a short cooldown ~250ms). Fire a red/white laser bullet.
- Enemy formation: a grid of alien ships (e.g. 8 columns x 4 rows) near the top, using classic
  Galaga color tiers (bottom row red, then orange, then green, top row cyan). The whole formation
  bobs side-to-side slowly.
- GALAGA SIGNATURE DIVE: periodically a few enemies peel off the formation and swoop down toward the
  player on a curved/looping path (use sine-based parametric path), firing at the player on the way
  down, then return to formation. Enemies who dive multiple times get faster.
- Collision detection (AABB or distance-based): player bullet hits enemy -> enemy explodes (particle
  burst) + score; enemy bullet hits player -> lose a life; enemy body hits player -> lose a life.
- Score (100-400 pts per enemy, higher for top tiers), HIGH SCORE persisted in localStorage, 3 lives,
  WAVE counter that increments when all enemies are cleared, and each new wave is denser/faster.
- Lives shown as small ship icons, score + high score + wave shown top-left.
- Enemy bullets (yellow/white), player has a brief respawn grace period (invincibility flicker) after
  losing a life.
- Explosion particle effects, screen shake on death, and simple Web Audio API sound effects
  (laser, explosion, dive) — guard audio so it works even if sound is blocked.
- Start screen ("GALAGA — press ENTER to start") and GAME OVER screen (shows final score, high score,
  "press ENTER to restart").
- Keyboard: LEFT/RIGHT move, SPACE shoot, ENTER start/restart. Also support A/D to move for
  convenience. P pauses.
- Keep the whole game in ONE <canvas> and a game loop using requestAnimationFrame with delta-time.
- Write clean, well-organized JavaScript. Make it actually RUN correctly the first time — no syntax
  errors, all functions defined, no undefined variables.

Output ONLY the complete HTML file, nothing else (no markdown fences, no commentary)."""

def call(prompt, max_tok=4096, system=None):
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    payload = {"model": MODEL, "messages": msgs, "temperature": 0.8, "max_tokens": max_tok}
    for attempt in range(4):
        try:
            r = creq.post(ROTATOR, json=payload, impersonate="chrome", timeout=300)
            if r.status_code == 200:
                j = r.json()
                m = j["choices"][0]["message"]
                content = (m.get("content") or "").strip()
                usage = j.get("usage", {})
                return content, usage, j.get("model", MODEL)
            else:
                time.sleep(3 * (attempt + 1))
        except Exception as e:
            time.sleep(3 * (attempt + 1))
    return None, {}, MODEL

def extract_html(text):
    # strip markdown fences if the model wrapped it
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        t = t.rsplit("```", 1)[0]
    # ensure it starts with something html-ish
    return t.strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--rounds", type=int, default=1)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    if args.fix:
        cur = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else "(none)"
        err = sys.stdin.read() if not sys.stdin.isatty() else ""
        prompt = (f"Here is the current Galaga game HTML. It has bugs.\n\n"
                  f"ERRORS REPORTED:\n{err}\n\n"
                  f"CURRENT CODE:\n{cur[:30000]}\n\n"
                  f"Fix ALL the errors and output the complete corrected HTML file "
                  f"(no markdown fences, no commentary).")
    else:
        prompt = SPEC

    for i in range(args.rounds):
        t0 = time.time()
        content, usage, model = call(prompt, max_tok=4096)
        dt = time.time() - t0
        if not content:
            print("GENERATION FAILED (pool unavailable/rate-limited)")
            sys.exit(1)
        html = extract_html(content)
        open(OUT, "w", encoding="utf-8").write(html)
        pt = usage.get("prompt_tokens", "?")
        ct = usage.get("completion_tokens", "?")
        tt = usage.get("total_tokens", "?")
        print(f"[round {i+1}] model={model} prompt_tok={pt} completion_tok={ct} total={tt} in {dt:.1f}s")
        print(f"  -> wrote {len(html)} chars to {OUT}")

if __name__ == "__main__":
    main()
