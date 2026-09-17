import os, time
from playwright.sync_api import sync_playwright

errs = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 520, "height": 700})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("file:///C:/Users/computer/Desktop/AI/galaga/galaga.html", wait_until="load", timeout=20000)
    pg.wait_for_timeout(800)

    # powerup system present?
    check = pg.evaluate("""() => ({
        spawnPowerup: typeof spawnPowerup,
        updatePowerups: typeof updatePowerups,
        drawPowerups: typeof drawPowerups,
        weaponTimer: (typeof player !== 'undefined') ? player.weaponTimer : 'no-player',
        shield: (typeof player !== 'undefined') ? player.shield : 'no-player',
        powerupsLen: (typeof powerups !== 'undefined') ? powerups.length : 'no-powerups',
    })""")
    print("POWERUP SYSTEM:", check)

    # manually spawn one of each + verify pickup logic
    res = pg.evaluate("""() => {
        powerups.length = 0;
        spawnPowerup(player.x, player.y);   // spawn on top of player -> should be picked up next update
        const before = powerups.length;
        // force a pickup by placing a shield powerup at player pos
        powerups.push({type:'shield', x: player.x, y: player.y, w:16, h:16, speed:2, t:0});
        updatePowerups();
        return {before: before, afterSpawn: powerups.length, shieldAfter: player.shield};
    }""")
    print("SPAWN/PICKUP TEST:", res)

    # start game + drive so enemies die and powerups can drop
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(300)
    for _ in range(30):
        pg.keyboard.press(" "); pg.wait_for_timeout(150)
    # check powerups array may have entries now
    n = pg.evaluate("() => powerups.length")
    print("powerups after 30 shots:", n)
    pg.screenshot(path="C:/Users/computer/Desktop/AI/galaga/powerup_test.png")
    print("PAGE ERRORS:", errs if errs else "NONE")
    b.close()
