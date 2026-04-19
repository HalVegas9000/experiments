# Lucas Monopoly

A full browser-based Monopoly game. Play against CPU opponent HAL across a complete 40-space board with properties, cards, houses, hotels, trading, and jail.

## How to Play

```bash
./start.sh
```

Opens the game at `http://localhost:8766/monopoly.html`.

Or open `monopoly.html` directly in any browser — no server required.

## Features

- **Full 40-space board** — all standard Monopoly spaces with correct color bands
- **All 8 color groups** — Brown, Light Blue, Pink, Orange, Red, Yellow, Green, Dark Blue
- **Railroads & Utilities** — correct rent scaling (1–4 RRs, 4×/10× dice for utilities)
- **Chance & Community Chest** — complete shuffled decks of 16 cards each
- **Houses & Hotels** — build on monopolies, shown on board in real time
- **Mortgage system** — mortgage for cash, unmortgage at 110%
- **Jail** — roll for doubles, pay $50 fine, or use Get Out of Jail Free card
- **Free Parking pot** — taxes and fines accumulate and are collected on landing
- **Property trading** — propose property + cash trades with HAL; live accept/decline preview
- **Bankruptcy** — auto-liquidates assets; game ends when a player goes bust

## Actions

| Button | When Available | Description |
|--------|---------------|-------------|
| 🎲 Roll Dice | Your turn | Roll and move |
| 🏠 Build Houses | After rolling, on a monopoly | Add houses/hotels to your color sets |
| 🏦 Mortgage | Anytime | Mortgage or unmortgage owned properties |
| 🤝 Propose Trade | Anytime (both solvent) | Offer properties and cash to HAL |
| ➡️ End Turn | After resolving your space | Pass to HAL |

Click any space on the board to see its full rent table and ownership info.

## CPU Opponent — HAL

- Buys properties aggressively when affordable
- Builds houses evenly across monopolies when it has the cash
- Evaluates trades using property value, built equity, and monopoly completion bonuses
- Pays jail fines if cash is high; otherwise rolls for doubles

## Starting Money

Both players start with **$1,500**. Pass GO to collect **$200**.
