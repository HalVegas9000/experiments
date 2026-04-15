#!/usr/bin/env bash
cd "$(dirname "$0")"
xdg-open lucasfighter.html 2>/dev/null || \
python3 -m webbrowser "$(pwd)/lucasfighter.html"
