#!/bin/bash
cd "$(dirname "$0")"
PORT=8765
echo "Starting Texas Hold'em Poker at http://localhost:$PORT"
xdg-open "http://localhost:$PORT/poker.html" &
python3 -m http.server $PORT
