# Lucas Fighter

A browser-based platform fighter inspired by Super Smash Bros. Single HTML file — no server, no dependencies.

## How to Play

Open `lucasfighter.html` in any modern browser, or run the startup script:

```bash
./run.sh
```

Choose **vs CPU** or **2 Players** from the mode select screen.

## Controls

| Action | Player 1 | Player 2 |
|---|---|---|
| Move | `A` / `D` | `←` / `→` |
| Jump (×2) | `W` | `↑` |
| Fast fall | `S` | `↓` |
| Light attack / Use item | `F` | `K` |
| Heavy attack / Throw item | `G` | `L` |
| Restart | `R` | `R` |
| Back to menu | `Esc` | `Esc` |

## Attacks

Attacks are context-sensitive based on what you're doing when you press the button:

| Input | On ground (still) | On ground (moving) | In air |
|---|---|---|---|
| Light (`F`/`K`) | Jab | Forward tilt | Neutral air |
| Heavy (`G`/`L`) | Forward smash | Forward smash | Neutral air |
| Light + hold `↓`/`S` | — | — | Down air |
| Light + hold `↑`/`W` | — | — | Up air |

## Items

Items spawn randomly on platforms every 9–15 seconds (max 2 at a time). Walk over an item to pick it up. Getting hit hard knocks it out of your hands.

### Bomb
- **Use** (`F`/`K`) — lob it in an arc with a 3-second fuse
- **Throw** (`G`/`L`) — hard throw forward, slightly longer fuse
- Explodes on contact with a fighter or when the fuse hits zero
- Damage scales with proximity to the blast

### Blaster
- **Use** (`F`/`K`) — fire a bullet in the direction you're facing
- **Throw** (`G`/`L`) — throw the gun itself as a projectile
- 5 shots before it disappears (ammo shown as pips on the gun)

## Mechanics

- **Damage %** — damage accumulates as a percentage; higher % means further knockback
- **Stocks** — each player starts with 3 lives
- **Blast zones** — fall off any edge to lose a stock
- **Double jump** — press jump again while airborne
- **Invincibility** — brief invincibility frames on respawn
- **CPU AI** — approaches, retreats, chases items, and chooses attacks based on your damage %

## Files

| File | Description |
|---|---|
| `lucasfighter.html` | The game (self-contained) |
| `run.sh` | Opens the game in your default browser |
