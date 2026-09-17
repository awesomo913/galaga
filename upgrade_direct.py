#!/usr/bin/env python3
"""upgrade_direct.py — generate the Galaga v2 upgrade via DIRECT key calls (bypass
rotator round-robin), trying each responsive key until one serves the big request."""
import json, time
from curl_cffi import requests as creq
from gen_game import extract_html, OUT

CUR = open(OUT, encoding="utf-8").read()

PROMPT = open("upgrade_game.py", encoding="utf-8").read()
# extract the prompt string (between PROMPT = """ and """ % CUR)
import re
m = re.search(r'PROMPT = """(.*?)""" % CUR', PROMPT, re.S)
prompt = m.group(1) % CUR

KEYSF = "C:/Users/computer/Desktop/AI/free-keys/free-keys.json"
d = json.load(open(KEYSF, encoding="utf-8"))
keys = [(x["email"], x["key"]) for x in d["groq"]]

def gen_direct(key, prompt, max_tok=8000):
    payload = {"model": "llama-3.3-70b-versatile",
               "messages": [{"role": "user", "content": prompt}],
               "temperature": 0.85, "max_tokens": max_tok}
    try:
        r = creq.post("https://api.groq.com/openai/v1/chat/completions",
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                      json=payload, impersonate="chrome", timeout=300)
        if r.status_code == 200:
            j = r.json()
            return j["choices"][0]["message"].get("content", "").strip(), j.get("usage", {})
        return None, None
    except Exception:
        return None, None

# try keys round-robin (skip the probe/poisoned), up to 30 attempts
content = usage = None
used = None
for i, (email, key) in enumerate(keys):
    if i >= 40:
        break
    t0 = time.time()
    content, usage = gen_direct(key, prompt)
    if content:
        used = email
        print(f"generated via {email} in {time.time()-t0:.1f}s total_tok={usage.get('total_tokens')}")
        break
    else:
        print(f"  {email[:28]:<28} no-go (retry next key)")
    time.sleep(1)

if not content:
    print("FAILED — all keys rate-limited for the big request")
    raise SystemExit(1)

html = extract_html(content)
open(OUT, "w", encoding="utf-8").write(html)
print(f"-> wrote {len(html)} chars to {OUT}")
