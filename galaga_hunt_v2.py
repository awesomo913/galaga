#!/usr/bin/env python3
"""
galaga_hunt_v2.py — 5-hour autonomous Galaga improvement loop, burned on Mistral.

Each iteration:
  1. Read the current galaga.html
  2. Pick the next feature from the queue
  3. Ask Mistral (via the furnace pool, PINNED to mistral) for surgical find/replace
     patches implementing that feature, returned as strict JSON
  4. Apply patches (all-or-nothing; exact or whitespace-normalized match)
  5. Verify in headless Chromium: no page errors + game object ready
  6. Keep on success (save + backup), revert on failure
  7. Accumulate tokens, write state + log every iteration (resumable)

Usage: python galaga_hunt_v2.py [--hours 5] [--port 8689]
"""
import json, os, sys, time, re, shutil, argparse, traceback

GAME = "C:/Users/computer/Desktop/AI/galaga/galaga.html"
BACKUP_DIR = "C:/Users/computer/Desktop/AI/galaga/backups"
STATE = "C:/Users/computer/Desktop/AI/galaga/hunt_state_v2.json"
LOG = "C:/Users/computer/Desktop/AI/galaga/hunt_v2.log"
POOL = "http://127.0.0.1:8689/v1/chat/completions"
PROVIDER = "nvidia"
MODEL = "deepseek-ai/deepseek-v4-flash-0731"

FEATURES = [
    {"name": "combo", "prompt": "Add a combo/score multiplier system: when the player destroys enemies within 1.5 seconds of each other, increment a combo counter; each kill awards score * combo; combo resets after 1.5s without a kill. Draw the combo count in the HUD top strip."},
    {"name": "boss", "prompt": "Add a boss fight: on every 5th wave, spawn ONE large boss enemy (wide, ~20 HP) that moves side-to-side in a sine pattern near the top and periodically fires a spread of 3 bullets downward. Draw a boss health bar across the top of the screen. Boss awards a large score bonus when destroyed."},
    {"name": "bonus_wave", "prompt": "Add a bonus wave: on every 4th wave, spawn a formation of fast-moving enemies that move quickly and are worth double points. Show a 'BONUS WAVE' banner briefly when it starts."},
    {"name": "difficulty", "prompt": "Add a difficulty curve: enemy descent speed, fire rate, and enemy bullet speed should scale up gradually as the wave number increases (e.g. multiply by 1 + wave*0.06). Keep wave 1 feeling unchanged."},
    {"name": "trails", "prompt": "Add visual polish: draw a fading engine trail behind the player ship and a short trail behind each enemy. Use existing particle-like drawing; do not break movement."},
    {"name": "screenshake", "prompt": "Increase the screen-shake intensity on player death and add a brief shake when a boss is destroyed (shakeDuration already exists; wire stronger values into those events)."},
    {"name": "sound", "prompt": "Add procedural sound effects using the Web Audio API (no external assets): a short laser blip on player shoot, a lower explosion noise on enemy death, and a rising chime on powerup pickup. Guard with a try/catch and an AudioContext created on first user input."},
    {"name": "shield_visual", "prompt": "Draw a visible shield bubble (a translucent cyan circle/outline) around the player ship while the shield powerup is active, so the player can see when they are protected."},
    {"name": "starfield", "prompt": "Add a parallax scrolling starfield background: 60+ small stars at 2-3 depths scrolling downward slowly behind the gameplay, giving a sense of depth. Draw them before enemies."},
    {"name": "powerup_magnet", "prompt": "Improve powerup feel: make powerups drift slowly toward the player when within ~120px (a magnet effect), and slightly increase the drop rate if it is currently under 15%."},
]

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_state():
    if os.path.exists(STATE):
        try:
            return json.load(open(STATE, encoding="utf-8"))
        except Exception:
            pass
    return {"started": time.time(), "iters": 0, "tokens": 0, "successes": 0,
            "failures": 0, "last_feature": -1,
            "features": {f["name"]: {"successes": 0, "fails": 0} for f in FEATURES}}

def save_state(s):
    json.dump(s, open(STATE, "w", encoding="utf-8"))

def call_mistral(html, feature):
    prompt = (
        "You are improving a single-file HTML5 canvas Galaga-style game. Below is the "
        "complete current HTML source. Implement ONE specific feature and return a JSON "
        "object containing a list of surgical find/replace patches.\n\n"
        f"FEATURE TO IMPLEMENT: {feature}\n\n"
        "RULES:\n"
        '1. Return ONLY a JSON object of the form {"patches": [{"find": "<exact existing code>", "replace": "<new code>"}, ...]}\n'
        "2. Each \"find\" MUST be an exact verbatim substring of the current HTML (copy it "
        "character-for-character including whitespace and indentation). Never invent a snippet "
        "that is not present — if unsure, pick a smaller unique snippet you can actually see.\n"
        "3. \"replace\" must be complete, valid JavaScript/HTML that keeps surrounding code intact.\n"
        "4. Make the MINIMAL change that implements the feature. Do not rewrite unrelated code.\n"
        "5. Preserve existing variable names, function signatures, and game logic. Do not break anything.\n"
        "6. No markdown fences, no commentary, just the JSON.\n\n"
        "GAME HTML:\n" + html
    )
    import urllib.request
    body = json.dumps({"model": MODEL, "provider": PROVIDER, "max_tokens": 2600,
                       "temperature": 0.2,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(POOL, data=body,
                                 headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=300)
    d = json.loads(r.read().decode())
    text = d["choices"][0]["message"]["content"]
    usage = (d.get("usage") or {})
    inp = usage.get("prompt_tokens", 0)
    out = usage.get("completion_tokens", 0)
    return text, inp + out

def extract_json(text):
    # strip code fences if present
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    # find first { and last }
    s = t.find("{")
    e = t.rfind("}")
    if s == -1 or e == -1 or e <= s:
        return None
    try:
        obj = json.loads(t[s:e + 1])
        return obj
    except Exception:
        return None

def norm(s):
    return re.sub(r"\s+", " ", s).strip()

def apply_patches(html, patches):
    """All-or-nothing. Returns (new_html, applied_count) or (None, missing_idx)."""
    new = html
    applied = 0
    for i, p in enumerate(patches):
        f = p.get("find")
        r = p.get("replace")
        if f is None or r is None:
            return None, i
        if f in new:
            new = new.replace(f, r, 1)
            applied += 1
            continue
        # whitespace-normalized match
        target = norm(f)
        idx = None
        # find by scanning lines: try to locate the normalized block
        lines = new.split("\n")
        norm_lines = [norm(x) for x in lines]
        nf = target.split(" ")
        # simple approach: join-normalize whole file won't let us replace reliably;
        # instead attempt per-line sequential match
        matched = False
        # Build a normalized token sequence and try to match the normalized find
        # across the raw text using a sliding approach is expensive; fall back to
        # line-based: try to find a run of consecutive lines whose normalized concat
        # equals the normalized find.
        f_lines = [norm(x) for x in f.split("\n")]
        for start in range(len(lines) - len(f_lines) + 1):
            if norm_lines[start:start + len(f_lines)] == f_lines:
                # replace that run of original lines with replace
                orig_run = "\n".join(lines[start:start + len(f_lines)])
                new = new.replace(orig_run, r, 1)
                matched = True
                applied += 1
                break
        if not matched:
            return None, i
    return new, applied

def verify():
    """Return (ok, detail). Loads GAME in headless Chromium, checks page errors + game ready."""
    from playwright.sync_api import sync_playwright
    errors = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(viewport={"width": 520, "height": 720})
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        pg.goto("file:///" + GAME.replace("\\", "/"))
        pg.wait_for_timeout(800)
        try:
            state = pg.evaluate("({ready: typeof isPlaying !== 'undefined' && typeof enemies !== 'undefined' && typeof player !== 'undefined', enemies: (typeof enemies !== 'undefined' ? enemies.length : -1)})")
        except Exception as e:
            errors.append("evaluate failed: " + str(e))
            state = {"ready": False, "enemies": -1}
        b.close()
    if errors:
        return False, "page_errors: " + "; ".join(errors[:3])
    if not state.get("ready"):
        return False, "game not ready"
    return True, f"ready, enemies={state.get('enemies')}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=5.0)
    ap.add_argument("--max-iters", type=int, default=0)
    args = ap.parse_args()

    os.makedirs(BACKUP_DIR, exist_ok=True)
    s = load_state()
    if s["iters"] == 0:
        s["started"] = time.time()
    deadline = s["started"] + args.hours * 3600

    log(f"=== galaga_hunt_v2 START: {args.hours}h budget, provider={PROVIDER}, model={MODEL} ===")
    log(f"resuming at iter {s['iters']}, tokens {s['tokens']}, successes {s['successes']}")

    browser_error_streak = 0
    while True:
        if time.time() >= deadline:
            log("TIME BUDGET REACHED — exiting.")
            break
        if args.max_iters and s["iters"] >= args.max_iters:
            log("MAX ITERS reached — exiting.")
            break

        # pick next feature (round-robin, skip ones with recent failures)
        s["last_feature"] = (s["last_feature"] + 1) % len(FEATURES)
        feat = FEATURES[s["last_feature"]]

        html = open(GAME, encoding="utf-8").read()

        s["iters"] += 1
        log(f"--- iter {s['iters']} [{feat['name']}] size={len(html)}B ---")

        try:
            text, toks = call_mistral(html, feat["prompt"])
            s["tokens"] += toks
        except Exception as e:
            s["tokens"] += 0
            log(f"  pool call failed: {type(e).__name__}: {str(e)[:120]} — backing off 30s")
            save_state(s)
            time.sleep(30)
            continue

        obj = extract_json(text)
        if not obj or "patches" not in obj:
            s["features"][feat["name"]]["fails"] += 1
            s["failures"] += 1
            log(f"  bad JSON from model (got {len(text)} chars) — skipping")
            save_state(s)
            continue

        patches = obj["patches"]
        if not patches:
            s["features"][feat["name"]]["fails"] += 1
            s["failures"] += 1
            log("  empty patch list — skipping")
            save_state(s)
            continue

        new_html, res = apply_patches(html, patches)
        if new_html is None:
            s["features"][feat["name"]]["fails"] += 1
            s["failures"] += 1
            log(f"  patch {res} 'find' did not match — reverting (no change applied)")
            save_state(s)
            continue

        # backup then write candidate
        ts = time.strftime("%H%M%S")
        bak = os.path.join(BACKUP_DIR, f"galaga_{ts}_{feat['name']}.html")
        shutil.copy(GAME, bak)
        open(GAME, "w", encoding="utf-8").write(new_html)

        ok, detail = verify()
        if ok:
            s["features"][feat["name"]]["successes"] += 1
            s["successes"] += 1
            browser_error_streak = 0
            log(f"  OK  [{feat['name']}] {len(patches)} patches, +{toks} tok, {detail}")
        else:
            s["features"][feat["name"]]["fails"] += 1
            s["failures"] += 1
            browser_error_streak += 1
            shutil.copy(bak, GAME)  # revert
            log(f"  FAIL [{feat['name']}] {detail} — reverted to backup")
            if browser_error_streak >= 3:
                log("  3 consecutive verify failures — sleeping 60s to cool down")
                browser_error_streak = 0
                time.sleep(60)
        save_state(s)

    log(f"=== DONE. iters={s['iters']} tokens={s['tokens']} successes={s['successes']} "
        f"failures={s['failures']} ===")
    save_state(s)

if __name__ == "__main__":
    main()
