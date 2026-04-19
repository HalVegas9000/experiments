#!/bin/bash
cd "$(dirname "$0")"
PORT=8766
echo "Starting Lucas Monopoly at http://localhost:$PORT"
xdg-open "http://localhost:$PORT/monopoly.html" &
python3 -m http.server $PORT
