#!/usr/bin/env python3
"""
Address Book – pure stdlib web server (no Flask required).
Run:  python3 app.py
Then open:  http://localhost:8080
"""

import json
import sqlite3
import re
import urllib.request
import urllib.parse
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DB = Path(__file__).parent / "contacts.db"
TEMPLATES = Path(__file__).parent / "templates"
PORT = 8080

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name  TEXT NOT NULL,
                email      TEXT,
                phone      TEXT,
                address    TEXT,
                city       TEXT,
                state      TEXT,
                zip        TEXT,
                notes      TEXT
            )
        """)


# ---------------------------------------------------------------------------
# Simple router
# ---------------------------------------------------------------------------

ROUTES = []   # list of (method, pattern, handler)

def route(method, pattern):
    def decorator(fn):
        ROUTES.append((method, re.compile(pattern), fn))
        return fn
    return decorator


def dispatch(handler, method, path):
    for m, pat, fn in ROUTES:
        if m == method:
            match = pat.fullmatch(path)
            if match:
                fn(handler, **match.groupdict())
                return
    handler.send_error(404, "Not Found")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIELDS = ["first_name", "last_name", "email", "phone",
          "address", "city", "state", "zip", "notes"]


def send_json(handler, data, status=200):
    body = json.dumps(data).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json_body(handler):
    length = int(handler.headers.get("Content-Length", 0))
    return json.loads(handler.rfile.read(length)) if length else {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DIRECTIONALS = {"N","S","E","W","Ne","Nw","Se","Sw","Nne","Nnw","Sse","Ssw","Ene","Ese","Wnw","Wsw"}

def _addr_title(s):
    """Title-case an address string, keeping directionals uppercase and ordinals lowercase."""
    result = []
    for word in s.title().split():
        if word in _DIRECTIONALS:
            result.append(word.upper())
        elif re.match(r"^\d+(St|Nd|Rd|Th)$", word):
            # e.g. "5Th" -> "5th"
            result.append(word[:-2] + word[-2:].lower())
        else:
            result.append(word)
    return " ".join(result)


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------

@route("GET", r"/")
def index(handler):
    html = (TEMPLATES / "index.html").read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(html)))
    handler.end_headers()
    handler.wfile.write(html)


@route("GET", r"/stats")
def stats(handler):
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
    send_json(handler, {"total": total})


@route("GET", r"/contacts")
def list_contacts(handler):
    qs = parse_qs(urlparse(handler.path).query)
    search = qs.get("search", [""])[0].strip()
    with get_db() as conn:
        if search:
            p = f"%{search}%"
            rows = conn.execute(
                "SELECT * FROM contacts "
                "WHERE first_name LIKE ? OR last_name LIKE ? OR email LIKE ? OR phone LIKE ? "
                "ORDER BY last_name, first_name",
                (p, p, p, p)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM contacts ORDER BY last_name, first_name"
            ).fetchall()
    send_json(handler, [dict(r) for r in rows])


@route("POST", r"/contacts")
def create_contact(handler):
    data = read_json_body(handler)
    values = [data.get(f, "") for f in FIELDS]
    with get_db() as conn:
        cur = conn.execute(
            f"INSERT INTO contacts ({','.join(FIELDS)}) VALUES ({','.join(['?']*len(FIELDS))})",
            values
        )
        new_id = cur.lastrowid
    send_json(handler, {"id": new_id}, 201)


@route("GET", r"/contacts/(?P<cid>\d+)")
def get_contact(handler, cid):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM contacts WHERE id=?", (int(cid),)).fetchone()
    if row is None:
        handler.send_error(404, "Not Found")
        return
    send_json(handler, dict(row))


@route("PUT", r"/contacts/(?P<cid>\d+)")
def update_contact(handler, cid):
    data = read_json_body(handler)
    values = [data.get(f, "") for f in FIELDS] + [int(cid)]
    with get_db() as conn:
        conn.execute(
            f"UPDATE contacts SET {', '.join(f+'=?' for f in FIELDS)} WHERE id=?",
            values
        )
    send_json(handler, {"ok": True})


@route("DELETE", r"/contacts/(?P<cid>\d+)")
def delete_contact(handler, cid):
    with get_db() as conn:
        conn.execute("DELETE FROM contacts WHERE id=?", (int(cid),))
    send_json(handler, {"ok": True})


@route("POST", r"/validate-address")
def validate_address(handler):
    data = read_json_body(handler)
    params = urllib.parse.urlencode({
        "street": data.get("address", "").strip(),
        "city":   data.get("city", "").strip(),
        "state":  data.get("state", "").strip(),
        "zip":    data.get("zip", "").strip(),
        "benchmark": "Public_AR_Current",
        "format": "json",
    })
    url = f"https://geocoding.geo.census.gov/geocoder/locations/address?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AddressBook/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        matches = result.get("result", {}).get("addressMatches", [])
        if not matches:
            send_json(handler, {"error": "Address not found or could not be verified."}, 404)
            return
        matched = matches[0].get("matchedAddress", "")
        # matchedAddress format: "123 MAIN ST, CITY, ST, ZIP"
        m_parts = [p.strip() for p in matched.split(",")]
        c = matches[0]["addressComponents"]
        send_json(handler, {
            "address": _addr_title(m_parts[0]) if m_parts else "",
            "city":    c.get("city", "").title(),
            "state":   c.get("state", ""),
            "zip":     c.get("zip", ""),
            "matched": matched,
        })
    except urllib.error.HTTPError as e:
        if e.code == 400:
            send_json(handler, {"error": "Please include city/state or ZIP to verify."}, 400)
        else:
            send_json(handler, {"error": f"Census API error {e.code}."}, 502)
    except Exception as e:
        send_json(handler, {"error": f"Validation service unavailable."}, 502)


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} – {fmt % args}")

    def _dispatch(self, method):
        path = urlparse(self.path).path
        dispatch(self, method, path)

    def do_GET(self):    self._dispatch("GET")
    def do_POST(self):   self._dispatch("POST")
    def do_PUT(self):    self._dispatch("PUT")
    def do_DELETE(self): self._dispatch("DELETE")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    server = HTTPServer(("", PORT), Handler)
    print(f"Address Book running at http://localhost:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
