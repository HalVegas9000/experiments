# Texas Hold'em Poker

A browser-based Texas Hold'em poker game. Play against two AI opponents (Bot Alice and Bot Bruno) in a full no-limit hold'em experience.

## How to Play

```bash
./start.sh
```

Opens the game at `http://localhost:8765/poker.html`.

Or open `poker.html` directly in any browser — no server required.

## Rules

Standard Texas Hold'em:

1. Each player is dealt 2 hole cards
2. **Pre-Flop** — first betting round
3. **Flop** — 3 community cards revealed, betting round
4. **Turn** — 4th community card, betting round
5. **River** — 5th community card, final betting round
6. **Showdown** — best 5-card hand from 7 cards wins the pot

## Actions

| Button | Description |
|--------|-------------|
| Fold   | Give up your hand |
| Check  | Pass (only when no bet to call) |
| Call   | Match the current bet |
| Raise  | Enter an amount and raise |
| All-In | Bet all your chips |

## Hand Rankings (high to low)

1. Straight Flush
2. Four of a Kind
3. Full House
4. Flush
5. Straight
6. Three of a Kind
7. Two Pair
8. One Pair
9. High Card

## AI Opponents

- **Bot Alice** — slightly aggressive, uses pot odds and hand strength
- **Bot Bruno** — more conservative, occasional bluffs

Each player starts with **$1,000**. The game resets if everyone goes broke.
