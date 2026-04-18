# Lucas Chess

A browser-based chess game with 2-player and CPU modes, featuring a custom **Piece Shop** with special fairy chess pieces.

## How to Run

```bash
./start.sh
```

Opens at `http://localhost:8110`. Or just open `index.html` directly in a browser.

## Modes

| Mode | Description |
|------|-------------|
| 2 Players | Pass-and-play on the same screen |
| vs CPU | Minimax AI with alpha-beta pruning, CPU plays Black |

**CPU Difficulty:** Easy (depth 1) · Medium (depth 2) · Hard (depth 3)

## Standard Rules Supported

- All legal moves with check validation
- Castling (kingside & queenside)
- En passant
- Pawn promotion (choose piece via modal)
- Checkmate & stalemate detection
- 50-move draw rule
- Move hints (green dots), last-move highlight, check highlight (red king)
- Undo (undoes 2 half-moves in CPU mode)

## Piece Shop

Spend your turn to swap any of your non-King, non-Pawn pieces for a custom piece. Click a shop card, then click the piece on the board you want to replace.

| Piece | Emoji | Movement |
|-------|-------|----------|
| The Frog | 🐸 | Jumps exactly 2 squares in any direction (including diagonals). Leaps over pieces. Takes by landing. |
| The Man | 🧍 | Moves 1 square in any direction. Cannot jump. Takes by landing. |
| The Alien | 👽 | **Zaps** any adjacent enemy without moving (stays in place). Also **teleports** to the square just vacated by the opponent's last move. |
| The Mole | 🐭 | Teleports to any empty square. Cannot capture. Acts as a wall, blocking enemy movement. |
| The Robot | 🤖 | Slides 1–3 squares in any direction (like a short-range Queen). Blocked by pieces. Takes by landing. |

Custom pieces show a small white or dark dot indicator to distinguish ownership since emoji don't support CSS colour.

## File Structure

```
lucas_chess/
├── index.html   # entire game (HTML + CSS + JS, no dependencies)
└── start.sh     # launches server on port 8110 and opens browser
```
