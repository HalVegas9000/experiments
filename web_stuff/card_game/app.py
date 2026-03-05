#!/usr/bin/env python3
import http.server
import socketserver
import os

PORT = 8080

os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} - {args[0]} {args[1]}")

with socketserver.TCPServer(('', PORT), Handler) as httpd:
    print(f'Arcane Duel running at http://localhost:{PORT}')
    print('Press Ctrl+C to stop.')
    httpd.serve_forever()
