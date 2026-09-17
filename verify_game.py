#!/usr/bin/env python3
"""verify_game.py — load galaga.html headless, capture console errors, simulate
start, and screenshot. Verifies the game runs without crashing."""
import sys
from playwright.sync_api import sync_playwright

GAME = "file:///C:/Users/computer/Desktop/AI/galaga/galaga.html"

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page(viewport={"width": 520, "height": 700})
    page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: errors.append(f"PAGEERROR: {e}"))
    page.goto(GAME, wait_until="load", timeout=20000)
    page.wait_for_timeout(800)

    # check canvas + initial state
    state = page.evaluate("""() => ({
        canvas: !!document.getElementById('canvas'),
        isPlaying,
        lives: player.lives,
        enemies: enemies.length,
        wave: player.wave
    })""")
    print("initial state:", state)

    # press ENTER to start
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    state2 = page.evaluate("""() => ({ isPlaying, enemies: enemies.length, wave: player.wave, lives: player.lives })""")
    print("after ENTER:", state2)

    # simulate shooting + movement for a few frames
    for _ in range(10):
        page.keyboard.press("ArrowLeft")
        page.keyboard.press(" ")
        page.wait_for_timeout(100)
    state3 = page.evaluate("""() => ({ bullets: playerBullets.length, ebullets: enemyBullets.length, x: Math.round(player.x) })""")
    print("after input:", state3)

    page.screenshot(path="C:/Users/computer/Desktop/AI/galaga/galaga_shot.png")
    print("screenshot saved")

    if errors:
        print("\nCONSOLE/PAGE ERRORS:")
        for e in errors[:20]:
            print("  ", e)
    else:
        print("\nno console errors")

    b.close()
