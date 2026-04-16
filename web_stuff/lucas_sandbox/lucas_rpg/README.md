# Lucas Quest

A browser-based RPG built with vanilla HTML5 Canvas and the Web Audio API — no dependencies, no build step.

## Running the game

```bash
bash start.sh
```

This starts a local HTTP server on port 8095 and opens the game in your browser automatically. Or just open `index.html` directly in any modern browser.

## Controls

| Key | Action |
|-----|--------|
| Arrow Keys / WASD | Move |
| Enter / Space | Confirm / Interact with NPCs |
| Esc | Cancel / Close dialog |
| M | Toggle background music |

## World

### Overworld
A scrolling 40×30 tile world with a camera that follows the player. Features grass, water, mountains, trees, flowers, roads, and a sand desert.

- **Town** (northwest) — walled village with an Inn and a Shop
- **Dungeon** (southeast, past the sand) — dark stone area with a staircase leading to the boss
- **Mountain Cave** (north, look for the dark arch in the mountains) — crystal cavern with a boss at the back

### NPCs
Talk to anyone by walking adjacent and pressing Enter.

| NPC | Location | Service |
|-----|----------|---------|
| Inn Keeper | Inside town | Rest to restore full HP & MP — 10 gold |
| Merchant | Inside town | Buy Potions — 20 gold each |
| Elder | Town square | Lore hints |
| Guard | Town square | Directions |

## Enemies

| Enemy | HP | Location | Notes |
|-------|----|----------|-------|
| Slime | 12 | Overworld grass | Easiest fight |
| Goblin | 18 | Overworld / Dungeon | |
| Skeleton | 22 | Dungeon | |
| Cave Drake | 40 | Dungeon | Breathes fire every 4 turns |
| Cave Bat | 40 | Mountain Cave | Dive-bombs every 3 turns |
| Crystal Fiend | 50 | Mountain Cave | High DEF; chips your DEF by 1 every 4 turns |
| **Stone Golem** | 120 | Mountain Cave boss | Rock Smash (2× damage) every 4 turns |
| **Dark Lord** | 80 | Dungeon boss | Dark Bolt (1.8× damage) every 5 turns |

Random encounters trigger on grass, sand, and dungeon floors. Bosses are guaranteed fights triggered by walking into their area.

## Turn-Based Combat

Each turn choose one of four actions:

- **Attack** — physical strike, scales with ATK vs enemy DEF
- **Magic** — Fireball costs 4 MP, deals ~2× ATK damage
- **Item** — use a Potion (+15 HP) or Ether (+8 MP) from your inventory
- **Run** — 60% base escape chance (lower against high-DEF enemies)

Defeating enemies earns XP and gold. Level up to raise ATK, DEF, MaxHP, and MaxMP.

## Progression

Starting stats: 20 HP · 10 MP · 5 ATK · 2 DEF · 3 Potions

| Level | XP needed | Gains per level |
|-------|-----------|----------------|
| 1→2 | 20 | +8 MaxHP, +4 MaxMP, +3 ATK, +1 DEF |
| 2→3 | 32 | (same) |
| 3→4 | 51 | (same) |
| … | ×1.6 | (same) |

### Treasure chests
| Location | Contents |
|----------|----------|
| Inn (inside) | 25 gold |
| Shop (inside) | 1 Potion |
| Dungeon room | 50 gold |
| Dungeon room | 1 Ether |
| After Golem | 150 gold + Crystal Shard |
| After Dark Lord | 200 gold + Hero Medal |

## Technical Notes

- **Rendering** — HTML5 Canvas 2D, 640×480, pixel-art style sprites drawn entirely with `fillRect` / `arc` calls
- **Audio** — Web Audio API oscillators only (square wave melody, triangle bass, sine kick). Starts on first user interaction to satisfy browser autoplay policy
- **Maps** — Overworld is 40×30 tiles with a smooth lerp camera. Boss room and Cave are 20×15 (fits the screen exactly, no camera needed)
- **Save state** — none; progress resets on page refresh
