# Lucas Platformer

A web-based fantasy RPG platformer built with HTML5 Canvas and the Web Audio API — no dependencies, just open `index.html` in a browser.

## How to Play

```bash
./play.sh
```

Or open `index.html` directly in any modern browser.

### Controls

| Key | Action |
|---|---|
| Arrow Keys / WASD | Move & jump |
| Space | Jump |
| M | Open achievement menu |
| R | Restart |

## Features

- **2 levels** of platforming across stone ruins and ancient dungeons
- **Knight hero** with animated armour, cape, and sword
- **Enemies**
  - Slimes — bounce back and forth, stomp to kill
  - Skeletons — patrol platforms, stomp to kill
  - Enemies turn at walls and ledges
  - Breaking a cracked stone block kills any enemy standing on it
- **Blocks**
  - Cracked stone — smash from below, shatters with rock burst particles
  - Rune blocks — strike from below to pop out a gem
- **Gems** — collect for points, bob in place, some hidden near blocks
- **Ancient stone pillars** as level landmarks and obstacles
- **Magic portal** goal — step inside to clear the level
- **Parallax background** — star field, distant mountains, rolling hills
- **Procedural background music** — 8-bar D minor RPG theme with melody, bass, chord pads, and reverb; generated entirely by the Web Audio API, loops seamlessly
- **Achievement system** — unlocks saved to localStorage, toast notifications on unlock, view all via `M`

## Achievements

| Achievement | Condition |
|---|---|
| Gem Hoarder | Collect 25 gems |
| Thorough Explorer | Collect all gems in Level 1 |
| Monster Slayer | Defeat 5 enemies |
| Exterminator | Defeat 10 enemies |
| First Step | Complete Level 1 |

## Tech Stack

- Pure HTML5 / JavaScript — no frameworks, no build step
- Canvas 2D API for all rendering (pixel-art style sprites drawn in code)
- Web Audio API for procedurally generated music and sound
- `localStorage` for achievement persistence
