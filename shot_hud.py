import os, time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 520, "height": 700})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("file:///C:/Users/computer/Desktop/AI/galaga/galaga.html", wait_until="load", timeout=20000)
    pg.wait_for_timeout(600)
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(800)          # formation near top, HUD visible
    pg.screenshot(path="C:/Users/computer/Desktop/AI/galaga/hud_check.png")
    # also a mid-game shot
    for _ in range(8):
        pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(120)
        pg.keyboard.press(" "); pg.wait_for_timeout(120)
    pg.screenshot(path="C:/Users/computer/Desktop/AI/galaga/hud_check2.png")
    print("errors:", errs if errs else "NONE")
    b.close()
