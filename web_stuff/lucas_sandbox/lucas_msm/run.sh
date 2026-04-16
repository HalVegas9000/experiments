#!/usr/bin/env bash
cd "$(dirname "$0")"
xdg-open lucas_msm.html 2>/dev/null || \
python3 -m webbrowser "$(pwd)/lucas_msm.html"
