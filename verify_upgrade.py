#!/usr/bin/env python3
"""verify upgraded features: levels, boss, special enemies, high score."""
from playwright.sync_api import sync_playwright

GAME = "file:///C:/Users/computer/Desktop/AI/galaga/galaga.html"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page(viewport={"width": 520, "height": 700})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(GAME, wait_until="load", timeout=20000)

    # start + action screenshot
    page.keyboard.press("Enter")
    page.wait_for_timeout(1500)
    page.screenshot(path="C:/Users/computer/Desktop/AI/galaga/up_01_game.png")

    # check what's in the game state
    state = page.evaluate("""() => ({
        level: (typeof level !== 'undefined') ? level : 'n/a',
        wave: player.wave,
        enemyTypes: [...new Set(enemies.map(e => e.type))],
        hasBoss: enemies.some(e => e.type === 'boss'),
        highScores: (typeof highScores !== 'undefined') ? highScores.length : 'n/a',
        levelNames: (typeof LEVELS !== 'undefined') ? LEVELS.length : (typeof levels !== 'undefined' ? Object.keys(levels).length : 'n/a'),
    })""")
    print("game state:", state)

    # trigger a boss wave (if the game uses wave-based boss spawn, set wave=5 and clear enemies)
    page.evaluate("() => { enemyBullets = []; playerBullets = []; player.lives = 99; enemies = []; player.wave = 4; }")
    page.wait_for_timeout(1500)
    boss_state = page.evaluate("""() => ({
        wave: player.wave,
        hasBoss: enemies.some(e => e.type === 'boss'),
        bossHealth: (typeof bossHealth !== 'undefined') ? bossHealth : 'n/a',
        enemyTypes: [...new Set(enemies.map(e => e.type))],
    })""")
    print("after forcing wave 5:", boss_state)
    page.screenshot(path="C:/Users/computer/Desktop/AI/galaga/up_02_boss.png")

    # check special enemy mechanics: tank takes 3 hits
    page.evaluate("""() => {
        enemies = []; player.wave = 0;
        const t = { type:'tank', x:200, y:300, w:34, h:30, gridX:200, gridY:300, health:3, diving:false, diveCooldown:0, diveFireCooldown:0 };
        enemies.push(t);
        // simulate 3 player bullets hitting it
        for (let n = 0; n < 4; n++) {
            playerBullets.push({x:200, y:290, w:5, h:5});
            checkCollisions();
        }
    }""")
    tank = page.evaluate("() => ({ enemies: enemies.length, score: player.score })")
    print("tank after 3-4 hits (should be destroyed + score):", tank)

    print("page errors:", errs if errs else "none")
    b.close()
