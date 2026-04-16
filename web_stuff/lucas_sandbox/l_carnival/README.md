# Duck Hunt Carnival

A browser-based carnival duck shooting game.

## How to play

```
./start.sh
```

Starts a local server on port 8099 and opens the game automatically.

## Controls

- **Mouse** — aim (crosshair cursor)
- **Click** — shoot

## Rules

- 10 ducks per round — shoot as many as you can
- 3 shots per clip, auto-reloads after 0.5s
- 5 ducks can escape before game over
- Rounds get faster and busier as you progress

## Targets

| Target | Points | Notes |
|--------|--------|-------|
| Duck | 100 + (round × 50) | 3 colour variants across 3 lanes |
| Duck with top hat | 100 + (round × 50) | Hat flies off when shot |
| UFO | 1000 | Rare (1/50 chance), moves faster, missing it doesn't count as a miss |

## Bonus

+500 points if you hit 80% or more of the ducks in a round.

## Stack

Single HTML file — no dependencies, runs in any modern browser via Python's built-in HTTP server.
