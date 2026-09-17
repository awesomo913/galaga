import json, time
from curl_cffi import requests as creq

POOL = "http://127.0.0.1:8689/v1/chat/completions"

CURRENT_HUD = '''            ctx.fillStyle = '#fff';
            ctx.font = '24px Arial';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'top';
            ctx.fillText(`Score: ${player.score}`, 10, 10);
            ctx.fillText(`High Score: ${player.highScore}`, 10, 40);
            ctx.fillText(`Wave: ${player.wave}`, 10, 70);
            ctx.fillText(`Level: ${player.level}`, 10, 100);
            ctx.fillStyle = '#0ff';
            for (let i = 0; i < player.lives; i++) {
                ctx.beginPath();
                ctx.moveTo(10 + i * 30, 110);
                ctx.lineTo(10 + i * 30 + 20, 110);
                ctx.lineTo(10 + i * 30 + 10, 110 - 10);
                ctx.closePath();
                ctx.fill();
                ctx.beginPath();
                ctx.moveTo(10 + i * 30 + 10 - 5, 110 - 10);
                ctx.lineTo(10 + i * 30 + 10 + 5, 110 - 10);
                ctx.lineTo(10 + i * 30 + 10, 110 - 10 - 5);
                ctx.closePath();
                ctx.fillStyle = '#fff';
                ctx.fill();
            }'''

PROMPT = f"""You are fixing the HUD of an HTML5 canvas Galaga game. The HUD text currently overlaps the enemy formation because it is drawn with no background.

Here is the current HUD drawing block (inside the main render loop, `player` has .score/.highScore/.wave/.level/.lives):

---CURRENT---
{CURRENT_HUD}
---END---

Rewrite this block so it:
1. Draws a semi-transparent dark strip (fillStyle 'rgba(0,0,0,0.6)', fillRect 0,0 to canvas.width, ~135px tall) BEFORE drawing any text, so enemies never show through the HUD.
2. Uses font '18px Arial' with tighter line spacing (lines at y = 8, 28, 48, 68).
3. Keeps the four text lines (Score, High Score, Wave, Level) and the lives ship icons, but moves the lives icons to y = 88.
4. Keeps the cyan '#0ff' ship-icon style for lives, with white nose-cone.
5. Changes NOTHING else — return ONLY the replacement JavaScript block, no markdown fences, no commentary."""

payload = {"model": "openai/gpt-oss-120b",
           "messages": [{"role": "user", "content": PROMPT}],
           "temperature": 0.3, "max_tokens": 1500}

for attempt in range(3):
    try:
        r = creq.post(POOL, json=payload, impersonate="chrome", timeout=300)
        r.raise_for_status()
        m = r.json()["choices"][0]["message"]
        out = (m.get("content") or "").strip() or (m.get("reasoning") or "").strip()
        print("=== REPLACEMENT BLOCK ===")
        print(out)
        break
    except Exception as e:
        print(f"attempt {attempt+1} failed: {str(e)[:150]}")
        time.sleep(15)
