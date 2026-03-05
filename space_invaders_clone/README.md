# Hal Invaders

A Space Invaders clone written in pure Python using tkinter. No external dependencies required.

## Requirements

- Python 3.x
- tkinter (`sudo apt-get install python3-tk`)
- `aplay` (part of `alsa-utils`, standard on most Linux desktops)

## Run

```bash
python3 hal_invaders.py
```

## Controls

| Key | Action |
|-----|--------|
| `LEFT` / `A` | Move left |
| `RIGHT` / `D` | Move right |
| `SPACE` | Fire |
| `Q` / `Esc` | Quit |

## Features

- **1024×768** window with pixel-art sprites at 4× scale
- **5×11 invader grid** — three alien types, two-frame animation, colour-coded by row
- **Classic dum-dum march music** — four bass notes that cycle and speed up as invaders are eliminated
- **Invaders get faster** as their numbers drop
- **Four destructible shield bunkers** — each block takes two hits; fast bullets use swept collision so nothing is indestructible
- **UFO mystery ship** flies across the top with a warbling sound and drops slow orange bombs
- **Explosions** — expanding burst with radiating sparks on every kill
- **Multi-level** — clear the grid and a fresh wave appears; lives and score carry over
- **Hi-score** tracking across rounds

## Alien Roster

| Sprite | Name | Points |
|--------|------|--------|
| Squid (top row) | ZORBAX | 30 |
| Crab (middle rows) | GRUNTLE | 20 |
| Octopus (bottom rows) | SQUORK | 10 |
| UFO | BOB | 50–300 (random) |

## Sound

All sounds are synthesised at startup and written to a temporary directory — no audio files are bundled. Playback uses `aplay`.

| Sound | Description |
|-------|-------------|
| Player laser | High-to-low frequency sweep |
| Enemy laser | Square-wave buzz |
| UFO bomb | Low square-wave thud |
| Explosion | Noise burst with decay |
| Player death | Descending sweep + noise |
| March steps | Four low square-wave pulses |
| UFO engine | Warbling multi-tone loop |
