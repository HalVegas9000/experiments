# Creature Collector

A browser-based creature collecting game. Explore an open world, find wandering creatures, catch them, and fill your collection.

## How to Play

```
./start.sh
```

Opens at `http://localhost:8100`.

## Controls

| Key | Action |
|-----|--------|
| WASD / Arrow Keys | Move |
| E | Catch nearby creature |
| 📖 Collection button | View your collection |
| 🔊 button | Mute / unmute music |

## Creatures (20 total)

| Rarity | Creatures | Catch Rate |
|--------|-----------|------------|
| Common | Blobby, Sparky, Floafy, Leafy, Muddy | 80% |
| Uncommon | Buzzy, Crysta, Twiggy, Puffin, Slimy, Rocksy | 60–65% |
| Rare | Flamey, Frosty, Glowy, Bubbly, Mossy, Starry | 40–45% |
| Legendary | Shadow, Goldie, Luminos | 15–20% |

## Features

- Scrolling overworld (1024×768 world, 640×480 viewport) with camera follow
- 7 terrain types: grass, tall grass, trees, water, rock, path, flowers, sand
- 39 creatures in the world at once, wandering with simple AI
- Each creature hand-drawn with canvas 2D animations (bobbing, flickering, spinning, etc.)
- Proximity catch prompt when near a creature
- Collection screen showing caught creatures in full colour, undiscovered as silhouettes
- Minimap in the top-right corner
- Looping chiptune background music (Web Audio API — square melody, triangle bass, sine pads)
- No dependencies — single `index.html` file
