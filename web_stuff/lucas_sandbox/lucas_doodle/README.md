# Lucas Doodle

A browser-based art program with a full set of drawing tools. No dependencies — open `index.html` directly in any modern browser.

## Launch

```bash
./start.sh
```

Or open `index.html` manually in your browser.

## Tools

| Key | Tool | Description |
|-----|------|-------------|
| P | Pencil | Freehand drawing. Right-click to draw in fill color. |
| E | Eraser | Erase to transparency. |
| B | Paint Bucket | Flood fill at click point with tolerance. |
| L | Line | Click and drag to draw a straight line. |
| S | Shape | Click and drag to draw a shape (Rect, Ellipse, Triangle, Star). Toggle fill on/off. |
| T | Text | Click to place a text box. Enter to commit, Shift+Enter for new line, Esc to cancel. |
| I | Eyedropper | Click anywhere on the canvas to sample that color as the stroke color. |
| A | Lasso | Freehand selection. Use the Selection panel to copy, cut, paste, or delete the region. |

## Controls

- **Stroke color** — color picker / palette (left-click a swatch)
- **Fill / BG color** — second color picker (Shift+click a swatch)
- **Brush size** — slider (1–100 px)
- **Opacity** — slider (1–100%)
- **Undo** — Ctrl+Z
- **Redo** — Ctrl+Y
- **Save PNG** — Ctrl+S or the Save PNG button (merges background + drawing layers)
- **Clear** — clears the drawing layer (undoable)
- **New** — resets the entire canvas

## Stack

- Pure HTML / CSS / JavaScript — no libraries, no build step
- Two-layer canvas (background fill + drawing layer) for clean PNG export
- Overlay canvas for live shape/line/lasso previews
