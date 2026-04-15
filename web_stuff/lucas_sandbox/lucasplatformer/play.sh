#!/bin/bash
cd "$(dirname "$0")"
echo "Starting Lucas Platformer..."
xdg-open index.html 2>/dev/null || firefox index.html 2>/dev/null || google-chrome index.html 2>/dev/null || chromium-browser index.html 2>/dev/null
