#!/usr/bin/env python3
"""final verification + action screenshots for the user."""
from playwright.sync_api import sync_playwright

GAME = "file:///C:/Users/computer/Desktop/AI/galaga/galaga.html"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page(viewport={"width": 520, "height": 700})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(GAME, wait_until="load", timeout=20000)

    # start + let it run a moment for a good action shot
    page.keyboard.press("Enter")
    page.wait_for_timeout(1800)
    page.screenshot(path="C:/Users/computer/Desktop/AI/galaga/shot_action.png")

    # shoot a few times + move for action
    page.keyboard.press(" ")
    page.wait_for_timeout(200)
    page.keyboard.press(" ")
    page.wait_for_timeout(300)
    page.screenshot(path="C:/Users/computer/Desktop/AI/galaga/shot_firing.png")

    # dive-return check with re-diving disabled (deterministic)
    page.evaluate("""
        () => { enemyBullets = []; player.lives = 99; 
                enemies.forEach(e => { e.diveCooldown = 1.5; e.diving = true; }); }
    """)
    # force every enemy to return by fast-forwarding diveCooldown to 0
    page.wait_for_timeout(1800)
    ret = page.evaluate("""
        () => { let ok = 0; for (const e of enemies) if (Math.abs(e.y - e.gridY) < 5) ok++; return ok; }
    """)
    print(f"dive-return (with re-dive window short): {ret}/32 y back at grid")
    print("page errors:", errs if errs else "none")
    b.close()
