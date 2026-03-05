# Arcane Duel

A simplified browser-based card game inspired by Magic: The Gathering. Built with pure Python stdlib and vanilla HTML/CSS/JavaScript — no dependencies.

## Running the Game

```bash
cd web_stuff/card_game
python3 app.py
```

Then open **http://localhost:8080** in your browser.

## Stack

- **Backend:** Python `http.server` (stdlib only) — serves static files on port 8080
- **Frontend:** Single `index.html` — all CSS and game logic embedded, no frameworks

## How to Play

### Turn Structure

1. **Tap lands** — click your untapped lands (green border) to add mana to your pool
2. **Play cards from hand** — click a card to play it:
   - **Lands** go straight to your battlefield (one per turn)
   - **Creatures/Spells** cost mana; valid targets pulse green when targeting is needed
   - **Targeting spells** — click a creature on the battlefield, or click the AI's info bar to target the AI player directly
3. **Attack** — click the Attack button, click your creatures to select attackers, then Confirm
   - The AI automatically assigns blockers
4. **Block** (when AI attacks) — click one of your creatures, then click the attacking AI creature to assign a block; click Done Blocking when finished
5. **End Turn** — passes to the AI

### Win Condition

Reduce your opponent to **0 life**. If a player must draw from an empty deck, they lose.

### Card Mechanics

| Mechanic | Description |
|---|---|
| **Summoning Sickness** | Creatures can't attack the turn they enter the battlefield |
| **Flying** | Can only be blocked by other creatures with Flying |
| **Temp Pump** | Buffs from Giant Growth expire at the start of your next turn |
| **Simultaneous Damage** | Attacker and blocker deal damage to each other at the same time |

### UI Cues

| Highlight | Meaning |
|---|---|
| Green border (lands) | Untapped, click to tap for mana |
| Gold glow | Selected card in hand |
| Red glow | Attacking creature |
| Blue glow | Blocking creature / selected blocker |
| Pulsing green | Valid spell target |

---

## Deck (40 cards — same for both players)

### Lands (16)

| Card | Mana |
|---|---|
| Forest | 1 |
| Mountain | 1 |
| Plains | 1 |
| Swamp | 1 |
| Island | 1 |

All lands produce 1 generic mana when tapped.

### Creatures (14)

| Card | Art | Cost | Power/Toughness | Ability |
|---|---|---|---|---|
| Goblin Scout | 🍓 | 1 | 1/1 | — |
| Forest Wolf | 🥦 | 2 | 2/2 | — |
| Iron Golem | 🥫 | 3 | 2/4 | — |
| Hill Giant | 🍔 | 3 | 3/3 | — |
| Fire Drake | 🌶 | 4 | 4/2 | Flying |
| War Elephant | 🍖 | 4 | 3/5 | — |
| Sky Serpent | 🍜 | 5 | 4/4 | Flying |
| Stone Colossus | 🎂 | 6 | 6/6 | — |

### Spells (10)

| Card | Cost | Effect |
|---|---|---|
| Lightning Bolt | 1 | Deal 3 damage to any target |
| Healing Salve | 1 | Gain 4 life |
| Dark Ritual | 1 | Add 3 mana to your pool this turn |
| Giant Growth | 1 | Target creature gets +3/+3 this turn |
| Mystic Scroll | 2 | Draw 2 cards |
| Plague Cloud | 3 | Deal 1 damage to all creatures |
| Annihilate | 3 | Destroy target creature |
| Fireball | 4 | Deal 6 damage to any target |

---

## AI Behaviour

- Taps all lands at the start of its turn
- Plays a land from hand if available
- Casts the most expensive affordable card each turn; prefers removal when the player has creatures on the field
- Attacks with all ready creatures each turn
- Assigns blockers to minimise damage: prioritises blockers that can kill the attacker and survive; falls back to trading or desperate blocks when facing lethal damage
- Flying restriction is respected when assigning blocks

---

## Files

```
card_game/
├── app.py        # Python HTTP server (port 8080)
├── index.html    # Complete game — HTML, CSS, and JavaScript
└── README.md     # This file
```
