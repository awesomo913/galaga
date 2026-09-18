# Galaga (AI Build Pipeline)

> The scripts that generated, tested, and kept improving an AI-built Galaga-style arcade shooter — not the game file itself.

This repo is the tooling around an AI-generated Galaga clone, not the game's HTML file. `gen_game.py` sends a detailed spec to a language model (over a local Groq-compatible pool) to generate a single self-contained `galaga.html` — canvas-based, classic enemy-formation-and-dive gameplay, powerups, score/wave tracking. The rest of the scripts form an autonomous hunt loop: load the game headless, drive it with random input, catch errors or broken invariants, send failures back for an AI fix pass, and otherwise cycle through a feature list to keep polishing it — logging every round to `hunt_log.txt`.

## Features
- **Spec-to-game generation** (`gen_game.py`): one prompt produces a full playable HTML5/canvas shooter (formation, dive attacks, powerups, particle FX, Web Audio sound, localStorage high score).
- **Headless verification** (`verify_game.py`, `harden_test.py`): loads the generated game in Playwright, checks for console errors and expected game state.
- **Autonomous hunt loop** (`hunt_loop.py`): a multi-hour fix-then-upgrade cycle — stability test, AI fix pass on failure, AI feature-upgrade pass on success — driven entirely by a free model pool.
- **Targeted patch scripts** (`hud_fix.py`, `dive_fix.py`, `powerup_gen.py`, etc.): one-off AI-assisted fixes for specific bugs found during hunting.
- **Screenshot + diagnostic tooling** (`screenshot_game.py`, `diag_now.py`) for visually checking the game's current state.

## Stack
Python 3.11, `curl_cffi` for pooled model calls, Playwright for headless browser testing. The generated game itself is a single self-contained HTML5 file (inline JS/CSS, Canvas 2D, Web Audio, no external libraries).

## Getting started
**Requirements**
- Python 3.11, `curl_cffi`, Playwright (`playwright install chromium`)
- A local model pool reachable at `127.0.0.1:8688` (OpenAI-compatible `/v1/chat/completions`)

**Run**
```bash
pip install curl_cffi playwright
python gen_game.py            # generate the game from spec
python verify_game.py         # headless smoke test
python hunt_loop.py           # 5-hour autonomous fix/upgrade loop
```
The generated game lands at `galaga.html` next to these scripts — open it directly in a browser to play.

## Status
**Unmaintained / archived**. Published as-is — fork it, adapt it. No support or guarantees.

## License
[MIT](LICENSE) — free to use, fork, and build on.
