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
- **4 × 3 grid of rooms** (15 rooms total, 5 cols × 3 rows), each connected to its neighbours by door openings in the walls
- **Goal:** collect all 12 stars scattered across the rooms
- **3 hearts** — lose one on enemy contact or projectile hit, respawn with iframes
- **Minimap** (bottom-right): green = current room, gold = room has uncollected stars, cyan = sword is here, dark = unvisited

### Sword
- Spawns in a **random room** each playthrough (any room except the start room)
- Walk over it to pick it up
- **Space** to swing — rectangular hitbox in the facing direction kills any enemy it touches
- **Deflects octopus projectiles** if you swing into them
- **Deals 2 damage** to the boss per hit
- Sword icon shown in HUD while held; flashes during swing animation

### Bow
- Spawns in a **random room** each playthrough (not start, not sword room)
- Walk over it to pick it up
- **E** to fire an arrow in the facing direction
- Arrows kill regular enemies in one hit, deal 1 damage to the boss
- 18-frame cooldown between shots

### Hidden health potion
- Spawns in a **random room** each playthrough (not start, not sword, not bow room)
- Walk over it to restore 1 heart
- Unlocks the "Bottoms Up" achievement (boss-room potions do not count)

### Enemies

| Type | Behaviour |
|---|---|
| **Red patrol demon** | Moves back and forth along one axis (x or y); kills on contact |
| **Purple octopus** | Stationary; eyes track the player; fires ink-blob projectiles on a timer; glows as it charges up |
| **Green beetle** | Chases the player; rotated to always face them |

- All regular enemies die in one sword hit or one arrow
- Projectiles are removed when they hit a wall or go off-screen

### Boss — Shadow Warlord
Unlocked when all 12 stars are collected. Accessible via a new south door in the centre-bottom room (room 2,2). Boss room has a dark lava-stone floor.

- **15 HP** — sword deals 2 damage per hit, arrow deals 1; brief invincibility frames after each hit
- **3 attacks (phase-gated)**:
  - **Minion spawn** (all phases): Roars and spawns 2–3 patrol demons (capped at 4 live at once); faster in later phases
  - **Projectile burst** (all phases): Fires 8–12 red orbs equally spaced in all directions
  - **Laser beam** (phase 2+, HP ≤ 10): Eye charges up with a dashed warning line, then fires a wide glowing beam toward the player — stay out of its path
- **Phase scaling**: At ≤ 10 HP (phase 2) boss speeds up and unlocks the laser; at ≤ 5 HP (phase 3) moves faster, spawns 3 minions, fires 12 orbs, laser fires more often; cracks appear on body
- **Health potions**: Occasionally drop in the boss room during the fight (max 2 active at once); do NOT count toward the "Bottoms Up" achievement
- **Art**: Large bat wings with membrane ribs, crown of 5 horns (centre tallest), 3 tracking eyes (centre eye glows orange when charging laser), pulsing dark aura
- **HP bar** shown at bottom of HUD when in the boss room

### Secret room
- A **cracked wall** glows faintly purple on the west wall of the left-middle room (gx=0, gy=1)
- **Shoot it with an arrow** in the crack zone to break it open — a passage appears to the west
- The secret room has a **mystic purple stone floor** with drifting sparkles
- Inside is a **wizard hat** — walk over it to collect it
- The hat renders on the player sprite for the rest of the run
- Unlocks the secret "What a Find!" achievement (hidden as `🔒 / ???` until discovered)
- Secret room shown on the minimap (purple cell) once the wall is broken

### Achievements (M key to open menu)

| Icon | Title | Condition |
|---|---|---|
| ⚔ | Armed & Dangerous | Found the sword |
| 🏹 | Sharpshooter | Found the bow |
| ★ | Star Collector | Collected all 12 stars |
| 🧪 | Bottoms Up | Drank the hidden health potion (main area only) |
| 🔒→🎩 | What a Find! | Found the secret hat *(hidden until unlocked)* |
| 💀 | Exterminator | Cleared every main-area room of enemies |
| 👑 | Warlord Slayer | Defeated the Shadow Warlord |

- Popup notification appears on screen when an achievement unlocks
- Secret achievements show as `🔒 / ??? / ???` in the menu until earned

### Audio (Web Audio API — no files)
All sounds synthesised with oscillators. Starts on first keypress (browser autoplay policy).

| Event | Sound |
|---|---|
| Collect star | Bright 4-note ascending arpeggio |
| Pick up sword | Rising frequency sweep + shimmer |
| Pick up bow | Short rising sweep + bell |
| Pick up hat | Rising sweep + two shimmer tones |
| Kill enemy | Low crunch |
| Player takes damage | Sharp buzz |
| Player dies | Descending sad melody |
| Win | 5-note victory fanfare |
| Achievement unlock | 4-note ascending chime |
| Octopus shoots | Soft bloop |
| Projectile hits wall | Short pop |
| Arrow fires | Bowstring twang |
| Wall breaks | Three-layer crunch |

**Background music:** 8-bar A-minor loop (64-step), 120 BPM. Three pitched voices — square melody, sine harmony counter-melody (thirds/sixths above), triangle bass — plus kick drum (beats 1 & 3) and hi-hat (every 8th note). Fades in on first keypress, fades out on death/win, restarts on R.

**Boss music:** 4-bar D-minor loop, 150 BPM. Sawtooth melody, triangle bass, kick + snare (white-noise AudioBuffer) + hi-hat. Crossfades in/out on boss room entry/exit.

---

## Code structure (all in `index.html`)

| Section | What it does |
|---|---|
| Constants | `W`, `H`, `WALL`, `DOOR_W`, grid size, door centre helpers |
| `ACHIEVS` | Achievement definitions — `id`, `icon`, `title`, `desc`, optional `secret: true` |
| Audio (`getAC`, `tone`, `sweep`, `sfx*`) | Lazy AudioContext + all sfx + background music scheduler |
| Room templates (`TEMPLATES`) | 15 static room definitions: star positions, enemy specs |
| `buildRooms()` | Deep-clones templates into live room objects each reset |
| Game state | `rooms`, `curRoom`, `player`, `sword`, `bow`, `potion`, `hat`, `bossRoom`, `secretRoom`, `projectiles`, `particles` |
| `wallRects(room)` | Returns collision rectangles for a room's walls (respects door gaps) |
| `attackHitbox()` | Returns the sword-swing rect in front of the player |
| `beginTrans(dir)` | Room routing including boss room and secret room special cases |
| `updateBoss()` | Boss AI: movement, 3 attacks, phase scaling, potion drops |
| `update()` | Main logic: input → movement → transitions → sword/bow → enemies → projectiles → pickups → stars → particles |
| `draw()` | Render order: floor → walls → items → enemies → projectiles → cracked wall → particles → attack arc → player → HUD → minimap → overlay |
| `reset()` | Rebuilds rooms, resets player, picks random sword/bow/potion rooms, inits boss + secret room |

### Special rooms
| Room | Details |
|---|---|
| `bossRoom` | `{gx:2, gy:3}` (virtual, south of grid); dark lava-stone floor; unlocks when all stars collected |
| `secretRoom` | `{gx:-1, gy:1}` (virtual, west of grid); purple mystic floor; unlocks by shooting cracked wall |

---

## Possible next steps

- [ ] More room variety — interior walls / obstacles to navigate around
- [ ] Locked doors that require a key item to open
- [ ] Player health upgrades (extra heart containers)
- [ ] Damage number pop-ups
- [ ] Win/death screen jingle instead of just a fanfare
- [ ] Touch/mobile controls (on-screen d-pad + attack button)
- [ ] Room-specific floor textures (dungeon stone, grass, water)
- [ ] Save high score / fastest completion time to localStorage
