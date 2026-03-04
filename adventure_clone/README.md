# Adventure Clone

A tribute to the Atari 2600 classic **Adventure**, built in pure Python 3
using only the standard library (tkinter for graphics, aplay for sound).
No pip installs required.

## Requirements

- Python 3 with tkinter: `sudo apt-get install python3-tk`
- `aplay` for sound (from `alsa-utils`, standard on most Linux distros)
- A graphical display (X11 or Wayland with XWayland)

## Run

```
python3 adventure.py
```

## Controls

| Key | Action |
|-----|--------|
| Arrow keys or WASD | Move |
| S | Attack with sword (also kills dragon on contact if carrying sword) |
| Space | Drop current item — or pick up the Magic Bridge from the floor |
| R | Respawn after death / Restart after winning |
| Esc | Quit |

## Objective

Find the **Enchanted Chalice** hidden in the Crypt of Ages and carry it back
to the **Golden Castle** (your starting room).

## Rooms (11 total)

| Room | Notable contents |
|------|-----------------|
| Golden Castle | Start here; win by returning with the Chalice |
| Hall of Mists | Bat territory; connects east/west/south |
| Crystal Cave | Blue Key |
| Dark Dungeon | **Locked** (Blue Key required); Magic Sword |
| Serpent Lair | Red Key; Yorgle the yellow dragon |
| Forgotten Shrine | **Locked** (Red Key required); Yellow Key |
| Maze of Thorns | Bat territory; winding wall maze |
| Swamp Chamber | Magic Bridge; crossroads room |
| Dragon Tower | Yorgle lurks here |
| Throne Room | **Locked** (Yellow Key required) |
| Crypt of Ages | Enchanted Chalice; Grundle the green dragon |

## Items

| Item | Description |
|------|-------------|
| Magic Sword | Carry it to kill dragons on contact, or press S to strike |
| Blue Key | Unlocks the Dark Dungeon |
| Red Key | Unlocks the Forgotten Shrine |
| Yellow Key | Unlocks the Throne Room |
| Magic Bridge | Drop it next to a wall (SPACE) to create a passage through it |
| Enchanted Chalice | Bring this to the Golden Castle to win |

### Magic Bridge

The bridge lets you pass through walls:

1. Pick it up with **Space** (it ignores auto-pickup so it stays put until grabbed manually)
2. Carry it to a wall and press **Space** to drop it in place
3. Pick up a different item, then walk through the wall where the bridge sits
4. Press **Space** near the bridge again to retrieve and reuse it

This is especially useful for reaching items that spawn inside enclosed wall sections.

## Enemies

| Enemy | Color | HP | Behaviour |
|-------|-------|----|-----------|
| Grundle Bat (×2) | Purple | 1 | Chases player, steals carried item on contact, flees to another room |
| Yorgle | Yellow | 3 | Slow dragon; chases and kills on contact (unless you have sword) |
| Grundle | Green | 2 | Medium dragon |
| Rhindle | Red | 1 | Fast dragon |

Bats spawn far from your entry point when you enter their room, giving you time to react.
Bats will randomly drop stolen items after a few seconds.

## Sound Effects

All sounds are procedurally generated WAV files played via `aplay`:

| Sound | Trigger |
|-------|---------|
| Pickup | Grabbing an item |
| Drop | Dropping an item |
| Portal | Passing through a room exit |
| Wall bump | Blocked by a locked door |
| Monster | Enemy enters the room |
| Bat steal | Bat takes your item |
| Sword hit | Hitting a dragon |
| Death | Player or enemy dies |
| Victory | Returning the Chalice |
