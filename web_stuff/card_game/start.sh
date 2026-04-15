#!/usr/bin/env bash
cd "$(dirname "$0")"
xdg-open http://localhost:8080 &
python3 app.py
