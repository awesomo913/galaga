import json, os, time
from playwright.sync_api import sync_playwright

GALAGA = "file:///C:/Users/computer/Desktop/AI/galaga/galaga.html"
DIR = "C:/Users/computer/Desktop/AI/galaga"

errs = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 520, "height": 700})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(GALAGA, wait_until="load", timeout=20000)
    pg.wait_for_timeout(1000)

    # what globals exist?
    try:
        g = pg.evaluate("""() => ({
            isPlaying: typeof isPlaying,
            player: typeof player,
            enemies: typeof enemies,
            ctx: typeof ctx,
            loop: typeof loop,
            isPlaying_val: (typeof isPlaying !== 'undefined') ? isPlaying : 'UNDEF',
        })""")
        print("GLOBALS:", json.dumps(g))
    except Exception as e:
        print("GLOBAL EVAL ERR:", str(e)[:200])

    # press Enter to start
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(1200)
    try:
        st = pg.evaluate("() => { try { return {playing: (typeof isPlaying!=='undefined')? isPlaying : 'UNDEF', nEnemies: (typeof enemies!=='undefined')? enemies.length : 'UNDEF'} } catch(e){ return {err: String(e)} } }")
        print("AFTER ENTER:", json.dumps(st))
    except Exception as e:
        print("AFTER ENTER EVAL ERR:", str(e)[:200])

    # drive a bit
    for _ in range(10):
        pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(150)
        pg.keyboard.press(" "); pg.wait_for_timeout(150)

    pg.screenshot(path=os.path.join(DIR, "diag_latest.png"))
    print("PAGE ERRORS:", errs if errs else "NONE")
    b.close()
