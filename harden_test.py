#!/usr/bin/env python3
"""harden_test.py — comprehensive Galaga bug probe. Each check reports PASS/FAIL
with evidence, plus screenshots at key moments. Feeds the fix loop."""
import json
from playwright.sync_api import sync_playwright

GAME = "file:///C:/Users/computer/Desktop/AI/galaga/galaga.html"
results = []
shots = {}
errors = []

def check(name, ok, detail=""):
    results.append({"name": name, "ok": ok, "detail": detail})
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}  {detail}")

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page(viewport={"width": 520, "height": 700})
    page.on("pageerror", lambda e: errors.append(f"PAGEERROR: {e}"))
    page.goto(GAME, wait_until="load", timeout=20000)
    page.wait_for_timeout(500)

    # 1. load, no errors
    check("loads without page errors", len(errors) == 0, "; ".join(errors[:3]))
    check("canvas present", page.evaluate("!!document.getElementById('canvas')"))
    shots["start_screen"] = "C:/Users/computer/Desktop/AI/galaga/harden_01_start.png"
    page.screenshot(path=shots["start_screen"])

    # 2. start
    page.keyboard.press("Enter")
    page.wait_for_timeout(400)
    s = page.evaluate("() => ({playing:isPlaying, enemies:enemies.length, wave:player.wave, lives:player.lives})")
    check("starts on ENTER", s["playing"] and s["enemies"] == 32, str(s))

    # 3. formation visible (enemies should be on-screen: y >= 0)
    ys = page.evaluate("() => enemies.map(e => e.y)")
    visible = sum(1 for y in ys if 0 <= y <= 640)
    check("enemy formation is ON-SCREEN at start", visible >= 28,
          f"{visible}/32 enemies have on-screen y (min y={min(ys):.0f})")
    shots["after_start"] = "C:/Users/computer/Desktop/AI/galaga/harden_02_started.png"
    page.screenshot(path=shots["after_start"])

    # 4. formation bobbing / movement between dives
    x0 = page.evaluate("() => enemies[0].x")
    page.wait_for_timeout(1200)
    x1 = page.evaluate("() => enemies[0].x")
    check("formation moves (bob) between dives", x0 != x1, f"x {x0:.0f} -> {x1:.0f}")

    # 5. player boundary clamp
    page.keyboard.down("ArrowLeft")
    page.wait_for_timeout(1500)
    page.keyboard.up("ArrowLeft")
    xl = page.evaluate("() => player.x")
    check("player clamps to left edge (x>=0)", xl >= -0.01, f"x={xl:.1f}")
    page.keyboard.down("ArrowRight")
    page.wait_for_timeout(1500)
    page.keyboard.up("ArrowRight")
    xr = page.evaluate("() => player.x")
    check("player clamps to right edge (x<=450)", xr <= 450.01, f"x={xr:.1f}")

    # 6. shooting produces a bullet
    page.keyboard.press(" ")
    page.wait_for_timeout(150)
    nb = page.evaluate("() => playerBullets.length")
    check("space fires a bullet", nb >= 1, f"bullets={nb}")

    # 7. canvas transform accumulation (screen-shake bug): check identity after kill
    #    force a kill to trigger shake, then read the transform matrix
    page.evaluate("() => { shakeDuration = 0.8; }")
    for _ in range(30):
        page.wait_for_timeout(50)
    mat = page.evaluate("() => { const m = ctx.getTransform(); return [m.a, m.b, m.c, m.d, m.e, m.f]; }")
    drifted = abs(mat[4]) > 1 or abs(mat[5]) > 1
    check("canvas transform resets (no drift after shake)", not drifted,
          f"transform e={mat[4]:.2f} f={mat[5]:.2f}")

    # 8. enemy dive returns to formation (y must return to gridY; bob only affects x)
    page.evaluate("() => { enemyBullets = []; player.lives = 3; enemies.forEach(e => { e.diveCooldown = 1.5; e.diving = true; }); }")
    page.wait_for_timeout(2500)
    back = page.evaluate("() => { let ok = 0; for (const e of enemies) if (Math.abs(e.y - e.gridY) < 5) ok++; return ok; }")
    check("diving enemies return to formation (y==gridY)", back >= 28, f"{back}/32 returned y to grid")

    # 9. wave increments when all enemies cleared (isolated, safe state)
    page.evaluate("() => { enemyBullets = []; playerBullets = []; player.lives = 3; player.y = 590; isPlaying = true; enemies = []; }")
    page.wait_for_timeout(500)
    wv = page.evaluate("() => player.wave")
    check("wave increments when cleared", wv >= 1, f"wave={wv}")

    # 10. game over + restart clears stale bullets and resets lives to 3
    page.evaluate("() => { player.lives = 0; isPlaying = false; }")
    page.wait_for_timeout(200)
    shots["game_over"] = "C:/Users/computer/Desktop/AI/galaga/harden_03_gameover.png"
    page.screenshot(path=shots["game_over"])
    page.keyboard.press("Enter")
    page.wait_for_timeout(150)
    s2 = page.evaluate("() => ({playing:isPlaying, lives:player.lives, score:player.score, ebullets:enemyBullets.length})")
    check("restart resets lives to 3 + clears stale bullets", s2["playing"] and s2["lives"] == 3 and s2["ebullets"] == 0, str(s2))

    b.close()

print("\n=== SUMMARY ===")
npass = sum(1 for r in results if r["ok"])
print(f"{npass}/{len(results)} checks passed")
json.dump({"results": results, "shots": shots, "errors": errors},
          open("C:/Users/computer/Desktop/AI/galaga/harden_results.json", "w"), indent=2)
