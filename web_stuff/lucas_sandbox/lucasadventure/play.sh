#!/usr/bin/env bash
# Start Star Quest in the default browser
GAME_DIR="$(cd "$(dirname "$0")" && pwd)"
xdg-open "$GAME_DIR/index.html"
