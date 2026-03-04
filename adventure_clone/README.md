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
| Dragon Tower | Yorgle lurks; corner-tower layout, open in all directions |
| Throne Room | **Locked** (Yellow Key required); connects to Golden Castle (N) and Crypt of Ages (S) |
| Crypt of Ages | Enchanted Chalice; Grundle the green dragon |

## Items

| Item | Description |
|------|-------------|
| Magic Sword | Carry it to kill dragons on contact, or press S to strike at range |
| Blue Key | Unlocks the Dark Dungeon |
| Red Key | Unlocks the Forgotten Shrine |
| Yellow Key | Unlocks the Throne Room |
| Magic Bridge | Drop next to a wall (SPACE) to create a passage through it |
| Enchanted Chalice | Bring this to the Golden Castle to win |

### Locked Doors

Locked exits are shown as colour-coded doors matching the required key. Once you
pass through a door with the correct key, it unlocks **permanently** — no need to
carry the key again on return visits. The door graphic disappears to show the
passage is open.

### Magic Bridge

The bridge lets you pass through interior walls:

1. Press **Space** near it to pick it up (it ignores auto-pickup so it stays put until grabbed manually)
2. Carry it to a wall and press **Space** to drop it in place — icon looks like `] [`
3. Pick up a different item, then walk through the wall where the bridge sits
4. Press **Space** near the bridge again to retrieve and reuse it

Especially useful for reaching items that spawn inside enclosed wall sections.

## Enemies

| Enemy | Color | HP | Behaviour |
|-------|-------|----|-----------|
| Grundle Bat (×2) | Purple | 1 | Chases player, steals carried item on contact, flees to another room, randomly drops after a few seconds |
| Yorgle | Yellow | 3 | Slow dragon; chases and kills on contact (sword required to survive) |
| Grundle | Green | 2 | Medium-speed dragon |
| Rhindle | Red | 1 | Fast dragon |

Bats always spawn far from your entry point when you enter their room.

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
