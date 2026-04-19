#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
xdg-open "$DIR/index.html" 2>/dev/null || open "$DIR/index.html" 2>/dev/null || echo "Open $DIR/index.html in your browser."
