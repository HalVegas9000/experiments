# Lucas TV

A browser-based retro CRT TV simulator with 8 curated YouTube channels.

## Features

- Old-school wood-grain cabinet with rounded CRT screen
- Scanline overlay and glare highlight for authentic CRT look
- Static noise animation on channel switch and power on
- 8 channel buttons with active glow indicator
- Red power button with on/off state
- Dual antennas, volume/brightness knobs (decorative)
- Green indicator light

## Controls

| Input | Action |
|-------|--------|
| Channel buttons | Switch channel |
| Keys `1`–`8` | Switch channel |
| `P` | Toggle power |
| Power button | Toggle power |

## Channels

| Channel | Video ID |
|---------|----------|
| CH 1 | YQa2-DY7Y_Q |
| CH 2 | oUtx8Rr3vTk |
| CH 3 | 6D3tVfqzYis |
| CH 4 | Z3CewJFEsEo |
| CH 5 | 68CFHGpQD5w |
| CH 6 | Bloiue3mSuA |
| CH 7 | 0EytSWiKrFg |
| CH 8 | hQWbFnAeDAo |

## Running

```bash
./start.sh
```

Opens at `http://localhost:8765`. Requires Python 3 (stdlib only).

> YouTube embeds require HTTP — opening `index.html` directly as a `file://` URL will not work.
