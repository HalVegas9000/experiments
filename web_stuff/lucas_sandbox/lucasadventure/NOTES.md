# Star Quest — Dev Notes

Single-file browser game (`index.html`). No dependencies, no build step — just open in a browser.

## How to run

```
open index.html
```
or serve from any static file server. Arrow keys / WASD to move.

---

## Current features

### Core gameplay
- **4 × 3 grid of rooms** (12 rooms total), each connected to its neighbours by door openings in the walls
- **Goal:** collect all 10 stars scattered across the rooms
- **3 hearts** — lose one on enemy contact or projectile hit, respawn with iframes
- **Minimap** (bottom-right): green = current room, gold = room has uncollected stars, cyan = sword is here, dark = unvisited

### Sword
- Spawns in a **random room** each playthrough (any room except the start room)
- Walk over it to pick it up
- **Space** to swing — rectangular hitbox in the facing direction kills any enemy it touches
- **Deflects octopus projectiles** if you swing into them
- Sword icon shown in HUD while held; flashes during swing animation

### Enemies

| Type | Behaviour |
|---|---|
| **Red patrol demon** | Moves back and forth along one axis (x or y); kills on contact |
| **Purple octopus** | Stationary; eyes track the player; fires ink-blob projectiles on a timer; glows as it charges up |

- All enemies die in one sword hit
- Projectiles are removed when they hit a wall or go off-screen

### Audio (Web Audio API — no files)
All sounds synthesised with oscillators. Starts on first keypress (browser autoplay policy).

| Event | Sound |
|---|---|
| Collect star | Bright 4-note ascending arpeggio |
| Pick up sword | Rising frequency sweep + shimmer |
| Kill enemy | Low crunch |
| Player takes damage | Sharp buzz |
| Player dies | Descending sad melody |
| Win | 5-note victory fanfare |
| Octopus shoots | Soft bloop |
| Projectile hits wall | Short pop |

**Background music:** 4-bar A-minor loop (square melody + triangle bass, 120 BPM). Fades in on first keypress, fades out on death/win, restarts on R.

---

## Code structure (all in `index.html`)

| Section | What it does |
|---|---|
| Constants | `W`, `H`, `WALL`, `DOOR_W`, grid size, door centre helpers |
| Audio (`getAC`, `tone`, `sweep`, `sfx*`) | Lazy AudioContext + all sfx + background music scheduler |
| Room templates (`TEMPLATES`) | 12 static room definitions: star positions, enemy specs |
| `buildRooms()` | Deep-clones templates into live room objects each reset |
| Game state | `rooms`, `curRoom`, `player`, `sword`, `projectiles`, `particles` |
| `wallRects(room)` | Returns collision rectangles for a room's walls (respects door gaps) |
| `attackHitbox()` | Returns the sword-swing rect in front of the player |
| `update()` | Main logic: input → movement → transitions → sword → enemies → projectiles → stars → particles |
| `draw()` | Render order: floor → walls → sword item → enemies → projectiles → particles → attack arc → player → HUD → minimap → overlay |
| `reset()` | Rebuilds rooms, resets player, picks random sword room, restarts music |

---

## Possible next steps

- [ ] More room variety — interior walls / obstacles to navigate around
- [ ] Enemy that chases the player (pathfinding or simple seek)
- [ ] Locked doors that require a key item to open
- [ ] Player health upgrades (extra heart containers)
- [ ] Boss room — larger, tougher enemy guarding a reward
- [ ] Damage number pop-ups
- [ ] Win/death screen jingle instead of just a fanfare
- [ ] Touch/mobile controls (on-screen d-pad + attack button)
- [ ] Room-specific floor textures (dungeon stone, grass, water)
- [ ] Save high score / fastest completion time to localStorage
