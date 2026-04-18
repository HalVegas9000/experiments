#!/bin/bash
cd "$(dirname "$0")"

PORT=8765
URL="http://localhost:$PORT"

# Kill any existing server on that port
fuser -k ${PORT}/tcp 2>/dev/null

python3 -m http.server $PORT &>/tmp/lucas_puz.log &
SERVER_PID=$!

echo "Lucas Jigsaw running at $URL (PID $SERVER_PID)"
echo "Press Ctrl+C to stop."

sleep 1
xdg-open "$URL" 2>/dev/null || open "$URL" 2>/dev/null || echo "Open $URL in your browser."

trap "kill $SERVER_PID 2>/dev/null; echo 'Server stopped.'" EXIT
wait $SERVER_PID
