#!/bin/bash
cd "$(dirname "$0")"
PORT=8100
echo "Starting Creature Collector on http://localhost:$PORT"
python3 -m http.server $PORT &
SERVER_PID=$!
sleep 2s
xdg-open "http://localhost:$PORT" 2>/dev/null || open "http://localhost:$PORT" 2>/dev/null
echo "Press Ctrl+C to stop the server."
wait $SERVER_PID
