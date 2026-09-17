import os, subprocess
from playwright.sync_api import sync_playwright
from PIL import Image

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 520, "height": 700})
    pg.on("pageerror", lambda e: print("PAGEERR", e))
    pg.goto("file:///C:/Users/computer/Desktop/AI/galaga/galaga.html", wait_until="load", timeout=20000)
    pg.wait_for_timeout(600)
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(800)
    pg.screenshot(path="C:/Users/computer/Desktop/AI/galaga/hud_solid.png")
    b.close()

# objective pixel check
im = Image.open("C:/Users/computer/Desktop/AI/galaga/hud_solid.png").convert("RGB")
W, H = im.size
def avg(region):
    px = list(im.crop(region).getdata())
    return tuple(sum(c[i] for c in px)//len(px) for i in range(3))

# strip region (0,0)-(W,135): should be near-uniform dark (no bright enemy colors)
strip_avg = avg((0, 0, W, 135))
# a band just below the strip (135-200): enemies should be visible here (brighter/varied)
below_avg = avg((0, 140, W, 200))
print(f"canvas {W}x{H}")
print(f"HUD strip avg color: {strip_avg}  (expect near-black ~(10,10,20))")
print(f"below-strip avg:     {below_avg}  (expect brighter = enemies visible)")
# count bright pixels in strip (text = white) vs colored enemy pixels
bright = sum(1 for c in im.crop((0,0,W,135)).getdata() if sum(c) > 400)
print(f"bright(white-text) pixels in strip: {bright}  (should be >0 = text present)")
