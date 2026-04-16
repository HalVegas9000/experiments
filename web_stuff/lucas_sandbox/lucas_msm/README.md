# My Humming Monsters

A browser-based monster music game inspired by My Singing Monsters. Each monster you unlock adds a new musical layer to the island's song. Single HTML file — no server, no dependencies.

## How to Play

Open `lucas_msm.html` in any modern browser, or run the startup script:

```bash
./run.sh
```

Click **Start Island** to begin. Your first monster (Noggin) is free. Earn coins over time and spend them in the shop at the bottom to unlock more monsters.

## Monsters

Each monster plays a unique instrument in the song loop (100 BPM, G major):

| Monster | Instrument | Cost |
|---|---|---|
| **Noggin** | Drums (kick, snare, hi-hat) | Free |
| **Mammott** | Bass hum with vibrato | 🪙 40 |
| **Toe Jammer** | Plucked bass line | 🪙 80 |
| **Tweedle** | High-pitched melody | 🪙 120 |
| **Potbelly** | Mid-range melody | 🪙 180 |
| **Furcorn** | Chord stabs (G / Em / C / D) | 🪙 260 |
| **Dandidoo** | Flute-like twinkling melody | 🪙 360 |
| **Bowgart** | Deep cello bowing | 🪙 500 |

## Mechanics

- **Coins** — each monster earns coins per second passively; more monsters = faster income
- **Music** — all layers are synced to a 2-bar lookahead scheduler so nothing drifts out of time
- **Animations** — monsters bob and glow to the beat with floating note particles
- **Mute** — toggle the 🔊 button in the top-right corner

## Files

| File | Description |
|---|---|
| `lucas_msm.html` | The game (self-contained) |
| `run.sh` | Opens the game in your default browser |
