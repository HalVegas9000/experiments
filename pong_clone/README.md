# Pong Clone

A single-player Pong game for Linux, written in Python using SDL2 (via ctypes).
No pip, no external Python packages — only the SDL2 runtime library is required.

## Requirements

- Python 3 (standard library only)
- SDL2 runtime: `sudo apt install libsdl2-2.0-0`

## Run

```bash
python3 pong.py
```

## Controls

| Key | Action |
|-----|--------|
| `↑` / `↓` | Move your paddle (right side) |
| `Space` | Pause / unpause |
| `R` | Restart game |
| `Esc` | Quit |

First to **7 points** wins.

## Sound Effects

All sounds are procedurally generated as sine-wave PCM at startup (no audio files needed):

| Event | Sound |
|-------|-------|
| Game start / restart | 3-note ascending arpeggio (C–E–G) |
| Ball hits paddle | Short 660 Hz click |
| You score | Ascending sweep (rewarding ding) |
| AI scores | Descending sweep (low boop) |
| You win the match | 5-note triumphant fanfare |
| You lose the match | 4-note descending sad tones |

## Architecture

| File | Purpose |
|------|---------|
| `pong.py` | Single-file game — everything lives here |

### Key classes

- **`SoundEngine`** — opens SDL2 audio device, pre-generates all PCM buffers, exposes `play(name)`
- **`PongGame`** — main game loop, state machine (`start → play → pause → win/lose`)
- **`AI`** — tracks ball with intentional imperfection: ~25% chance of a mistake every 1.7–3.7 s, lasting 0.3–1.1 s (wrong direction or freeze)
- **`Ball`** — floating-point position/velocity; speeds up 0.35 px/frame per paddle hit, capped at 13 px/frame
- **`Paddle`** — simple rect with clamp
- **`SoundEngine`** — SDL2 audio queue (non-blocking, sounds mix automatically)

### Rendering

No SDL2_ttf or image libraries used. Everything is drawn with `SDL_RenderFillRect`:

- **Scores** — 7-segment style large digits
- **Overlay text** — built-in 5×7 pixel bitmap font (uppercase A–Z, 0–9, punctuation)
- **Paddles / ball** — plain rectangles

### SDL2 usage

SDL2 is accessed entirely through Python's `ctypes` — no pygame, no bindings package.
The game uses: `SDL_RenderFillRect`, `SDL_QueueAudio`, `SDL_PollEvent`, vsync via `SDL_RENDERER_PRESENTVSYNC`.

## Possible next features

- Two-player mode (second paddle on keyboard, e.g. W/S keys)
- Difficulty selector (easy / medium / hard AI)
- Wall bounce sound effect
- Particle effects on score
- High score persistence
- Fullscreen toggle (`F` key)
- Ball trail / visual polish
