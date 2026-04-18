# Lucas Jigsaw Puzzle

A browser-based jigsaw puzzle game — no dependencies, single HTML file.

## How to Play

1. Run `./start.sh` to launch the server and open the game in your browser.
2. Pick a grid size and an image from the dropdowns, or upload your own photo.
3. Drag pieces from the tray on the right onto the board.
4. Pieces snap into place when dropped close enough to the correct slot.
5. Complete the puzzle to see your solve time.

## Features

- **Interlocking tab shapes** — bezier-curve jigsaw tabs on every shared edge, consistent between adjacent pieces
- **5 procedural images** — Mountains, Ocean, Forest, Sunset, Space (no external assets needed)
- **Upload your own photo** — auto-cropped to square and sliced up
- **Grid sizes** — 3×3 (Easy), 4×4 (Medium), 5×5 (Hard), 6×6 (Expert)
- **Ghost overlay** — faint reference image on the board to guide placement
- **Win screen** — shows your total solve time

## Files

| File | Purpose |
|------|---------|
| `index.html` | Entire game (HTML + CSS + JS, self-contained) |
| `start.sh` | Starts a local HTTP server and opens the browser |

## Running

```bash
./start.sh
```

Runs on `http://localhost:8765`. Press Ctrl+C to stop the server.
