# Food Battles

A browser-based card game inspired by Magic: The Gathering, with a food theme. Built with pure Python stdlib and vanilla HTML/CSS/JavaScript — no dependencies.

## Running the Game

```bash
cd web_stuff/card_game
python3 app.py
```

Then open **http://localhost:8080** in your browser.

## Stack

- **Backend:** Python `http.server` (stdlib only) — serves static files on port 8080
- **Frontend:** Single `index.html` — all CSS, game logic, and sound synthesis embedded, no frameworks
- **Sound:** Web Audio API — all sound effects synthesized in JS, no audio files needed

## How to Play

### Turn Structure

1. **Tap energy cards** — click your untapped Energy cards (green border) to add calories to your pool
2. **Play cards from hand** — click a card to play it:
   - **Energy** cards go straight to your battlefield (one per turn)
   - **Creatures/Spells** cost calories; valid targets pulse green when targeting is needed
   - **Targeting spells** — click a creature on the battlefield, or click Burger Bot's info bar to target them directly
3. **Attack** — click the Attack button, click your creatures to select attackers, then Confirm
   - Burger Bot automatically assigns blockers
4. **Block** (when Burger Bot attacks) — click one of your creatures, then click an attacking creature to assign a block; click Done Blocking when finished
5. **End Turn** — passes to Burger Bot

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
| Green border (energy cards) | Untapped, click to tap for 1 calorie |
| Gold glow | Selected card in hand |
| Red glow | Attacking creature |
| Blue glow | Blocking creature / selected blocker |
| Pulsing green | Valid spell target |

### Sound Effects

All sounds are synthesized via the Web Audio API (no audio files). Sound triggers on first user interaction.

| Action | Sound |
|---|---|
| Tap energy card | Bubble pop |
| Play creature | Squishy boing |
| Cast spell | Sparkling arpeggio |
| Declare attack | Low dramatic thud |
| Damage dealt | Impact smack |
| Creature destroyed | Deflating descend |
| Assign block | Shield clunk |
| Your turn starts | Double chime |
| Victory | Happy major fanfare |
| Defeat | Sad descending trombone |

---

## Deck (40 cards — same for both players)

### Energy (16)

| Card | Calories |
|---|---|
| Energy 🔋 | 1 |

All Energy cards produce 1 calorie when tapped.

### Creatures (14)

| Card | Art | Cost | Power/Toughness | Ability |
|---|---|---|---|---|
| Strawberry | 🍓 | 1 | 1/1 | — |
| Broccoli | 🥦 | 2 | 2/2 | — |
| Tin Can | 🥫 | 3 | 2/4 | — |
| Burger | 🍔 | 3 | 3/3 | — |
| Hot Pepper | 🌶 | 4 | 4/2 | Flying |
| Drumstick | 🍖 | 4 | 3/5 | — |
| Ramen | 🍜 | 5 | 4/4 | Flying |
| Birthday Cake | 🎂 | 6 | 6/6 | — |

### Spells (10)

| Card | Cost | Effect |
|---|---|---|
| Lightning Bolt | 1 | Deal 3 damage to any target |
| Healing Salve | 1 | Gain 4 life |
| Dark Ritual | 1 | Add 3 calories to your pool this turn |
| Giant Growth | 1 | Target creature gets +3/+3 this turn |
| Mystic Scroll | 2 | Draw 2 cards |
| Plague Cloud | 3 | Deal 1 damage to all creatures |
| Annihilate | 3 | Destroy target creature |
| Fireball | 4 | Deal 6 damage to any target |

---

## AI Behaviour (Burger Bot)

- Taps all energy cards at the start of its turn
- Plays an energy card from hand if available
- Casts the most expensive affordable card each turn; prefers removal when the player has creatures on the field
- Attacks with all ready creatures each turn
- Assigns blockers to minimise damage: prioritises blockers that can kill the attacker and survive; falls back to trading or desperate blocks when facing lethal damage
- Flying restriction is respected when assigning blocks

---

## Files

```
card_game/
├── app.py        # Python HTTP server (port 8080)
├── index.html    # Complete game — HTML, CSS, JavaScript, and sound synthesis
└── README.md     # This file
```
