#!/usr/bin/env bash
cd "$(dirname "$(realpath "$0")")"
PORT=8765
pkill -f "http.server $PORT" 2>/dev/null
python3 -m http.server $PORT &
sleep 2s
xdg-open "http://localhost:$PORT/index.html"
