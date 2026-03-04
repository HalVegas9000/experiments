#!/usr/bin/env python3
"""
ADVENTURE CLONE
A tribute to the Atari 2600 classic.
Uses tkinter (stdlib) for graphics + WAV sound via aplay/paplay.
"""

import tkinter as tk
import math, random, struct, wave, io, os, tempfile, subprocess, threading, time

# ── Constants ─────────────────────────────────────────────────────────────────
W, H = 1024, 768
TILE = 64
COLS = W // TILE   # 16
ROWS = H // TILE   # 12
FPS_MS = 1000 // 60

PLAYER_SIZE = 18
BORDER = TILE      # width of border walls

GAP_HALF = int(1.5 * TILE)  # half of a 3-tile exit gap

# ── Colours ───────────────────────────────────────────────────────────────────
def rgb(r, g, b): return f'#{r:02x}{g:02x}{b:02x}'

C_BLACK   = rgb(0,   0,   0)
C_WHITE   = rgb(255, 255, 255)
C_RED     = rgb(200,  30,  30)
C_GREEN   = rgb( 30, 180,  30)
C_YELLOW  = rgb(220, 200,  20)
C_ORANGE  = rgb(220, 120,  20)
C_PURPLE  = rgb(150,  30, 200)
C_CYAN    = rgb( 30, 200, 200)
C_GRAY    = rgb(120, 120, 120)
C_DKGRAY  = rgb( 40,  40,  40)
C_BROWN   = rgb(120,  70,  20)
C_SILVER  = rgb(180, 180, 220)
C_PLAYER  = rgb(255, 255,  80)

# ── Sound (WAV via aplay/paplay) ──────────────────────────────────────────────
SAMPLE_RATE = 22050

def _make_wave_bytes(samples):
    """Convert list of int16 samples to WAV bytes."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))
    return buf.getvalue()

def _gen_sweep(f0, f1, dur, vol=0.4):
    n = int(SAMPLE_RATE * dur)
    phase = 0.0
    out = []
    for i in range(n):
        t = i / n
        freq = f0 + (f1 - f0) * t
        phase += 2 * math.pi * freq / SAMPLE_RATE
        v = math.sin(phase) * vol * (1 - t**0.4)
        out.append(max(-32767, min(32767, int(v * 32767))))
    return _make_wave_bytes(out)

def _gen_chord(freqs, dur, vol=0.35):
    n = int(SAMPLE_RATE * dur)
    out = []
    for i in range(n):
        t = i / n
        v = sum(math.sin(2*math.pi*f*i/SAMPLE_RATE) for f in freqs) / len(freqs)
        out.append(max(-32767, min(32767, int(v * vol * (1 - t**0.3) * 32767))))
    return _make_wave_bytes(out)

def _gen_noise(dur, vol=0.5):
    n = int(SAMPLE_RATE * dur)
    out = [max(-32767, min(32767, int(random.uniform(-1,1)*vol*(1-i/n)*32767))) for i in range(n)]
    return _make_wave_bytes(out)

def _gen_square(freq, dur, vol=0.3):
    n = int(SAMPLE_RATE * dur)
    out = []
    for i in range(n):
        v = (1.0 if math.sin(2*math.pi*freq*i/SAMPLE_RATE) > 0 else -1.0)
        out.append(int(v * vol * (1 - i/n) * 32767))
    return _make_wave_bytes(out)

# Pre-build sound data in temp files
_SFX_DATA = {}
_SFX_FILES = {}

def _build_sounds():
    _SFX_DATA['pickup']  = _gen_sweep(300, 800, 0.15)
    _SFX_DATA['drop']    = _gen_sweep(600, 200, 0.12)
    _SFX_DATA['unlock']  = _gen_chord([523, 659, 784], 0.25)
    _SFX_DATA['monster'] = _gen_sweep(80, 40, 0.3, 0.5)
    _SFX_DATA['bite']    = _gen_noise(0.18, 0.6)
    _SFX_DATA['death']   = _gen_sweep(400, 50, 0.6, 0.5)
    _SFX_DATA['victory'] = _gen_chord([523, 659, 784, 1047], 0.8)
    _SFX_DATA['bat']     = _gen_sweep(600, 1200, 0.08, 0.2)
    _SFX_DATA['wall']    = _gen_square(80, 0.06)
    _SFX_DATA['portal']  = _gen_sweep(200, 900, 0.18)
    for name, data in _SFX_DATA.items():
        fd, path = tempfile.mkstemp(suffix='.wav')
        os.write(fd, data); os.close(fd)
        _SFX_FILES[name] = path

def _find_player():
    for cmd in ['aplay', 'paplay', 'play']:
        if subprocess.run(['which', cmd], capture_output=True).returncode == 0:
            return cmd
    return None

_PLAYER_CMD = None

def play_sfx(name):
    global _PLAYER_CMD
    if _PLAYER_CMD is None:
        _PLAYER_CMD = _find_player() or ''
    if not _PLAYER_CMD or name not in _SFX_FILES:
        return
    path = _SFX_FILES[name]
    def _play():
        subprocess.run([_PLAYER_CMD, '-q', path] if _PLAYER_CMD == 'aplay'
                       else [_PLAYER_CMD, path],
                       capture_output=True)
    threading.Thread(target=_play, daemon=True).start()

# ── World Map ─────────────────────────────────────────────────────────────────
# walls: list of (x1,y1,x2,y2) in pixels
# exits: dict  dir -> room_id
# items: list of item_id strings initially here
# lock:  item_id key required to enter, or None

def _wall(gx, gy, gw, gh):
    """Grid-coord wall → pixel rect tuple (x1,y1,x2,y2)."""
    return (gx*TILE, gy*TILE, (gx+gw)*TILE, (gy+gh)*TILE)

ROOM_DEFS = {
    0: dict(name='Golden Castle',   bg='#3c3c14',
            walls=[_wall(3,3,2,1),_wall(11,3,2,1),_wall(6,6,4,1),_wall(3,8,2,1),_wall(11,8,2,1)],
            exits=dict(E=1, W=5, S=9), items=[], lock=None),
    1: dict(name='Hall of Mists',   bg='#142840',
            walls=[_wall(2,4,1,4),_wall(13,4,1,4),_wall(5,2,6,1)],
            exits=dict(W=0, E=2, S=6), items=[], lock=None),
    2: dict(name='Crystal Cave',    bg='#1e3250',
            walls=[_wall(4,3,1,6),_wall(11,3,1,6),_wall(5,3,6,1),_wall(5,9,6,1)],
            exits=dict(W=1, N=3), items=['blue_key'], lock=None),
    3: dict(name='Dark Dungeon',    bg='#0f0f19',
            walls=[_wall(1,5,5,1),_wall(10,5,5,1),_wall(6,2,1,3),_wall(9,2,1,3),_wall(6,8,1,2),_wall(9,8,1,2)],
            exits=dict(S=2, W=4), items=['sword'], lock='blue_key'),
    4: dict(name='Serpent Lair',    bg='#192814',
            walls=[_wall(3,2,10,1),_wall(3,9,10,1),_wall(3,2,1,7),_wall(12,2,1,7),_wall(6,5,4,2)],
            exits=dict(E=3, S=7), items=['red_key'], lock=None),
    5: dict(name='Forgotten Shrine',bg='#321e32',
            walls=[_wall(2,3,3,1),_wall(11,3,3,1),_wall(7,5,2,3),_wall(2,8,12,1)],
            exits=dict(E=0, N=8), items=['yellow_key'], lock='red_key'),
    6: dict(name='Maze of Thorns',  bg='#1e140a',
            walls=[_wall(2,2,1,3),_wall(5,2,1,3),_wall(8,2,1,3),_wall(11,2,1,3),
                   _wall(2,7,1,3),_wall(5,7,1,3),_wall(8,7,1,3),_wall(11,7,1,3),
                   _wall(3,5,2,1),_wall(7,5,2,1),_wall(10,4,2,2)],
            exits=dict(N=1, E=7), items=[], lock=None),
    7: dict(name='Swamp Chamber',   bg='#142314',
            walls=[_wall(1,4,4,1),_wall(11,4,4,1),_wall(1,7,4,1),_wall(11,7,4,1),
                   _wall(6,2,4,2),_wall(6,8,4,2)],
            exits=dict(W=6, N=4, E=10), items=['bridge'], lock=None),
    8: dict(name='Dragon Tower',    bg='#3c140a',
            walls=[_wall(1,1,2,2),_wall(13,1,2,2),   # corner towers top
                   _wall(1,9,2,2),_wall(13,9,2,2),   # corner towers bottom
                   _wall(6,4,4,1),_wall(6,7,4,1)],   # interior barriers
            exits=dict(S=5, E=9), items=[], lock=None),
    9: dict(name='Throne Room',     bg='#32280a',
            walls=[_wall(3,3,2,2),_wall(11,3,2,2),_wall(3,7,2,2),_wall(11,7,2,2),
                   _wall(6,1,4,1),_wall(6,10,4,1)],
            exits=dict(W=8, N=0, S=10), items=[], lock='yellow_key'),
   10: dict(name='Crypt of Ages',   bg='#191923',
            walls=[_wall(2,2,12,1),_wall(2,9,12,1),_wall(2,2,1,7),_wall(13,2,1,7),_wall(5,5,6,2)],
            exits=dict(W=7, N=9), items=['chalice'], lock=None),
}

ITEM_DEFS = {
    'chalice':    dict(name='Enchanted Chalice', color=C_YELLOW),
    'sword':      dict(name='Magic Sword',        color=C_SILVER),
    'blue_key':   dict(name='Blue Key',           color='#5078ff'),
    'red_key':    dict(name='Red Key',            color='#ff5050'),
    'yellow_key': dict(name='Yellow Key',         color='#ffdc32'),
    'bridge':     dict(name='Magic Bridge',       color='#00e0c0'),
}

ENEMY_DEFS = {
    'bat':     dict(name='Grundle Bat',  color='#a03cc8', speed=2.8, lethal=False, steals=True,  hp=1, rooms=[1,7]),
    'yorgle':  dict(name='Yorgle',       color='#dcb414', speed=1.5, lethal=True,  steals=False, hp=3, rooms=[8,4]),
    'grundle': dict(name='Grundle',      color='#28b43c', speed=1.9, lethal=True,  steals=False, hp=2, rooms=[3,10]),
    'rhindle': dict(name='Rhindle',      color='#dc2828', speed=2.3, lethal=True,  steals=False, hp=1, rooms=[9,2]),
}

# ── Utility ───────────────────────────────────────────────────────────────────
def clamp(v, lo, hi): return max(lo, min(hi, v))
def dist(ax, ay, bx, by): return math.hypot(ax-bx, ay-by)

def rect_collide(ax1,ay1,ax2,ay2, bx1,by1,bx2,by2):
    return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1

def safe_spawn(room_id, half_w=20, half_h=20):
    """Return (x, y) guaranteed not to overlap any wall in the given room."""
    rd = ROOM_DEFS[room_id]
    border = build_border_walls(rd['exits'])
    all_walls = border + rd['walls']
    margin = TILE + 10
    for _ in range(200):
        x = random.randint(margin, W - margin)
        y = random.randint(margin, H - margin)
        if not any(rect_collide(x-half_w, y-half_h, x+half_w, y+half_h,
                                wx1, wy1, wx2, wy2)
                   for wx1,wy1,wx2,wy2 in all_walls):
            return x, y
    # Fallback: room centre (should only trigger on pathological layouts)
    return W // 2, H // 3

# ── Game Objects ──────────────────────────────────────────────────────────────
class Item:
    def __init__(self, iid, room_id):
        self.id = iid
        self.room_id = room_id
        self.x, self.y = safe_spawn(room_id, half_w=12, half_h=12)
        self.carried_by = None   # None | 'player' | enemy_instance

    def bounds(self, sz=18):
        return (self.x-sz//2, self.y-sz//2, self.x+sz//2, self.y+sz//2)


class Enemy:
    def __init__(self, eid, room_id):
        self.id = eid
        d = ENEMY_DEFS[eid]
        self.name   = d['name']
        self.color  = d['color']
        self.speed  = d['speed']
        self.lethal = d['lethal']
        self.steals = d['steals']
        self.hp     = d['hp']
        self.max_hp = d['hp']
        self.room_id = room_id
        self.x, self.y = safe_spawn(room_id, half_w=24, half_h=18)
        ang = random.uniform(0, 2*math.pi)
        self.dx = math.cos(ang) * self.speed
        self.dy = math.sin(ang) * self.speed
        self.alive = True
        self.flash_until = 0
        self.carried_item = None
        self.frame = 0
        self.frame_t = 0
        self.just_entered = True
        self.flee_timer = 0.0          # counts down after stealing; then bat changes room
        self.drop_timer = random.uniform(4, 9)  # next random-drop countdown

    def bounds(self):
        if 'bat' in self.id:
            return (self.x-22, self.y-14, self.x+22, self.y+14)
        return (self.x-22, self.y-14, self.x+30, self.y+16)

    def update(self, walls, px, py, dt):
        if not self.alive: return
        self.frame_t += 1
        if self.frame_t % 15 == 0: self.frame ^= 1

        fleeing = self.steals and self.carried_item is not None

        # AI movement
        if fleeing:
            # Flee away from player at higher speed; ignore interior walls
            ang = math.atan2(self.y - py, self.x - px)
            spd = self.speed * 1.5
            self.dx = math.cos(ang) * spd
            self.dy = math.sin(ang) * spd
        elif self.steals:
            # Chase player to steal
            ang = math.atan2(py - self.y, px - self.x)
            self.dx = math.cos(ang) * self.speed
            self.dy = math.sin(ang) * self.speed
        else:
            # Dragon: chase if close, else wander
            d = dist(self.x, self.y, px, py)
            if d < 240:
                ang = math.atan2(py - self.y, px - self.x)
                self.dx = math.cos(ang) * self.speed
                self.dy = math.sin(ang) * self.speed
            elif random.random() < 0.012:
                ang = random.uniform(0, 2*math.pi)
                self.dx = math.cos(ang) * self.speed
                self.dy = math.sin(ang) * self.speed

        nx = self.x + self.dx
        ny = self.y + self.dy
        bx1,by1,bx2,by2 = self.bounds()

        if not fleeing:
            # Normal wall collision
            for wx1,wy1,wx2,wy2 in walls:
                if rect_collide(nx+(bx1-self.x), by1, nx+(bx2-self.x), by2, wx1,wy1,wx2,wy2):
                    self.dx = -self.dx; nx = self.x; break
            for wx1,wy1,wx2,wy2 in walls:
                if rect_collide(bx1, ny+(by1-self.y), bx2, ny+(by2-self.y), wx1,wy1,wx2,wy2):
                    self.dy = -self.dy; ny = self.y; break

        if nx < 30 or nx > W-30: self.dx = -self.dx; nx = self.x
        if ny < 30 or ny > H-30: self.dy = -self.dy; ny = self.y

        self.x, self.y = nx, ny

        # Timers (bats only)
        if self.steals and self.carried_item:
            self.flee_timer -= dt
            self.drop_timer -= dt

        if self.carried_item:
            self.carried_item.x = int(self.x)
            self.carried_item.y = int(self.y - 20)

    def drop_item(self):
        if self.carried_item:
            item = self.carried_item
            item.x, item.y = int(self.x), int(self.y)
            item.carried_by = None
            self.carried_item = None
            return item
        return None


class Player:
    def __init__(self):
        self.x = W // 2
        self.y = H // 3   # avoid room-0 interior wall at y=240
        self.speed = 4.5
        self.room_id = 0
        self.carrying = None
        self.last_dx = 0.0   # most recent movement direction
        self.last_dy = 0.0
        self.alive = True
        self.death_timer = 0
        self.invincible = 0.0   # seconds

    def bounds(self):
        s = PLAYER_SIZE // 2
        return (self.x-s, self.y-s, self.x+s, self.y+s)

    def move(self, dx, dy, walls, passages=()):
        """passages: list of (bx, by) where a bridge is placed, opening gaps in walls."""
        if dx or dy: self.last_dx, self.last_dy = dx, dy
        if dx and dy: dx *= 0.707; dy *= 0.707
        nx = self.x + dx * self.speed
        ny = self.y + dy * self.speed
        s = PLAYER_SIZE // 2
        pad = TILE // 2          # how close bridge must be to wall edge
        reach = TILE * 1.5       # how close player must be to bridge to use it

        def bridge_opens(test_x, test_y, wx1, wy1, wx2, wy2):
            for bx, by in passages:
                if (wx1-pad <= bx <= wx2+pad and wy1-pad <= by <= wy2+pad):
                    if math.hypot(test_x - bx, test_y - by) < reach:
                        return True
            return False

        # X
        collide = False
        for wx1,wy1,wx2,wy2 in walls:
            if rect_collide(nx-s, self.y-s, nx+s, self.y+s, wx1,wy1,wx2,wy2):
                if not bridge_opens(nx, self.y, wx1, wy1, wx2, wy2):
                    collide = True; break
        if not collide: self.x = nx

        # Y
        collide = False
        for wx1,wy1,wx2,wy2 in walls:
            if rect_collide(self.x-s, ny-s, self.x+s, ny+s, wx1,wy1,wx2,wy2):
                if not bridge_opens(self.x, ny, wx1, wy1, wx2, wy2):
                    collide = True; break
        if not collide: self.y = ny

        self.x = clamp(self.x, PLAYER_SIZE, W - PLAYER_SIZE)
        self.y = clamp(self.y, PLAYER_SIZE, H - PLAYER_SIZE)


# ── Room helper ────────────────────────────────────────────────────────────────
def build_border_walls(exits):
    """Return pixel-rect wall segments for the border with exit gaps cut out."""
    cx, cy = W//2, H//2
    gap = 3*TILE  # gap width
    walls = []

    # Top border
    if 'N' in exits:
        walls.append((0, 0, cx-gap//2, TILE))
        walls.append((cx+gap//2, 0, W, TILE))
    else:
        walls.append((0, 0, W, TILE))

    # Bottom border
    if 'S' in exits:
        walls.append((0, H-TILE, cx-gap//2, H))
        walls.append((cx+gap//2, H-TILE, W, H))
    else:
        walls.append((0, H-TILE, W, H))

    # Left border
    if 'W' in exits:
        walls.append((0, 0, TILE, cy-gap//2))
        walls.append((0, cy+gap//2, TILE, H))
    else:
        walls.append((0, 0, TILE, H))

    # Right border
    if 'E' in exits:
        walls.append((W-TILE, 0, W, cy-gap//2))
        walls.append((W-TILE, cy+gap//2, W, H))
    else:
        walls.append((W-TILE, 0, W, H))

    return walls

def get_exit_portal(px, py, exits):
    """Return direction string if player is in an exit portal, else None."""
    s = PLAYER_SIZE // 2
    cx, cy = W//2, H//2
    gap = 3*TILE
    # N portal: top strip
    if 'N' in exits and py - s < TILE and cx-gap//2 < px < cx+gap//2:
        return 'N'
    if 'S' in exits and py + s > H-TILE and cx-gap//2 < px < cx+gap//2:
        return 'S'
    if 'W' in exits and px - s < TILE and cy-gap//2 < py < cy+gap//2:
        return 'W'
    if 'E' in exits and px + s > W-TILE and cy-gap//2 < py < cy+gap//2:
        return 'E'
    return None


# ── Canvas Drawing ─────────────────────────────────────────────────────────────
class Renderer:
    """Wraps a tk.Canvas and provides draw helpers."""
    def __init__(self, canvas):
        self.c = canvas

    def clear(self):
        self.c.delete('all')

    def fill(self, color):
        self.c.create_rectangle(0, 0, W, H, fill=color, outline='')

    def rect(self, x1,y1,x2,y2, fill='', outline=''):
        self.c.create_rectangle(x1,y1,x2,y2, fill=fill, outline=outline)

    def poly(self, pts, fill='', outline=''):
        flat = [v for pt in pts for v in pt]
        self.c.create_polygon(flat, fill=fill, outline=outline, smooth=False)

    def line(self, x1,y1,x2,y2, fill='white', width=2):
        self.c.create_line(x1,y1,x2,y2, fill=fill, width=width)

    def circle(self, cx,cy,r, fill='', outline=''):
        self.c.create_oval(cx-r,cy-r,cx+r,cy+r, fill=fill, outline=outline)

    def text(self, x, y, s, color='white', size=12, bold=False, anchor='center'):
        weight = 'bold' if bold else 'normal'
        self.c.create_text(x, y, text=s, fill=color, font=('Courier', size, weight),
                           anchor=anchor)

    # ── Shapes ────────────────────────────────────────────────────────────────
    def draw_player(self, x, y):
        s = PLAYER_SIZE // 2
        self.rect(x-s, y-s, x+s, y+s, fill=C_PLAYER, outline='#a0a000')
        # tiny eye
        self.rect(x+s-5, y-s+3, x+s-2, y-s+6, fill=C_BLACK)

    def draw_item(self, iid, x, y):
        c = ITEM_DEFS[iid]['color']
        if iid == 'chalice':
            sz = 22
            self.poly([(x-sz//3,y-sz//2),(x+sz//3,y-sz//2),
                       (x+sz//4,y),(x+sz//2,y+sz//2),(x-sz//2,y+sz//2),(x-sz//4,y)],
                      fill=c, outline='#a09000')
            self.line(x,y-sz//2, x,y-sz//2+5, fill='white', width=2)
        elif iid == 'sword':
            sz = 30
            self.line(x, y-sz//2, x, y+sz//3, fill=c, width=3)
            self.line(x-sz//3, y+sz//6, x+sz//3, y+sz//6, fill=C_BROWN, width=3)
            self.line(x, y+sz//6, x, y+sz//2, fill=C_BROWN, width=3)
        elif 'key' in iid:
            sz = 18
            self.circle(x, y-sz//4, sz//4, fill=c, outline='#000000')
            self.circle(x, y-sz//4, sz//8, fill=C_BLACK)
            self.line(x, y, x, y+sz//2, fill=c, width=3)
            self.line(x, y+sz//4, x+sz//5, y+sz//4, fill=c, width=3)
            self.line(x, y+sz//3, x+sz//5, y+sz//3, fill=c, width=3)
        elif iid == 'bridge':
            # ] [ — left bracket serifs point LEFT (outward), right bracket serifs point RIGHT
            bar  = 28   # distance of each vertical bar from centre
            h    = 24   # half bracket height
            arm  = 16   # serif arm length (pointing outward)
            lk   = 5    # line width
            # Left bracket ]  — bar at x-bar, serifs extend further LEFT
            self.line(x-bar,       y-h,   x-bar,       y+h,   fill=c, width=lk)
            self.line(x-bar,       y-h,   x-bar-arm,   y-h,   fill=c, width=lk)
            self.line(x-bar,       y+h,   x-bar-arm,   y+h,   fill=c, width=lk)
            # Right bracket [ — bar at x+bar, serifs extend further RIGHT
            self.line(x+bar,       y-h,   x+bar,       y+h,   fill=c, width=lk)
            self.line(x+bar,       y-h,   x+bar+arm,   y-h,   fill=c, width=lk)
            self.line(x+bar,       y+h,   x+bar+arm,   y+h,   fill=c, width=lk)

    def draw_dragon(self, x, y, color, frame):
        f = frame % 2
        # Body
        self.rect(x-18, y-10, x+18, y+10, fill=color, outline='')
        # Head
        self.rect(x+14, y-14, x+30, y+2, fill=color, outline='')
        # Eye
        self.rect(x+24, y-11, x+28, y-7, fill=C_RED, outline='')
        # Jaw
        if f == 0:
            self.rect(x+14, y+2, x+30, y+10, fill=color, outline='')
        else:
            self.rect(x+14, y+4, x+30, y+9, fill=color, outline='')
            self.line(x+15, y+4, x+29, y+4, fill='white', width=1)
        # Tail
        self.poly([(x-18,y),(x-28,y-6),(x-34,y+2),(x-28,y+8)], fill=color)
        # Legs
        self.rect(x-10, y+10, x-2, y+20, fill=color, outline='')
        self.rect(x+2,  y+10, x+10, y+20, fill=color, outline='')
        # Wing
        if f == 0:
            self.poly([(x-5,y-10),(x-20,y-28),(x+10,y-10)], fill=color)
        else:
            self.poly([(x-5,y-10),(x-15,y-22),(x+10,y-10)], fill=color)

    def draw_bat(self, x, y, color, frame):
        f = frame % 2
        self.circle(x, y, 6, fill=color, outline='')
        self.circle(x-3, y-2, 2, fill=C_RED)
        self.circle(x+3, y-2, 2, fill=C_RED)
        if f == 0:
            lw = [(x,y-3),(x-22,y-14),(x-16,y+2)]
            rw = [(x,y-3),(x+22,y-14),(x+16,y+2)]
        else:
            lw = [(x,y-3),(x-18,y-8),(x-14,y+4)]
            rw = [(x,y-3),(x+18,y-8),(x+14,y+4)]
        self.poly(lw, fill=color)
        self.poly(rw, fill=color)

    def draw_walls(self, walls):
        for wx1,wy1,wx2,wy2 in walls:
            self.rect(wx1,wy1,wx2,wy2, fill=C_GRAY, outline=C_WHITE)

    def draw_enemy(self, enemy):
        if not enemy.alive: return
        now = time.time()
        color = 'white' if enemy.flash_until > now else enemy.color
        x, y = int(enemy.x), int(enemy.y)
        if 'bat' in enemy.id:
            self.draw_bat(x, y, color, enemy.frame)
        else:
            self.draw_dragon(x, y, color, enemy.frame)
        # HP bar
        if enemy.hp < enemy.max_hp:
            bw = 30
            bx = x - bw//2; by = y - 32
            self.rect(bx, by, bx+bw, by+4, fill=C_RED)
            filled = int(bw * enemy.hp / enemy.max_hp)
            if filled > 0:
                self.rect(bx, by, bx+filled, by+4, fill=C_GREEN)


# ── Message Queue ──────────────────────────────────────────────────────────────
class MsgQueue:
    def __init__(self):
        self.msgs = []   # [(text, color, expire_time)]

    def add(self, text, color=C_WHITE, duration=2.5):
        self.msgs.append((text, color, time.time() + duration))

    def tick(self):
        now = time.time()
        self.msgs = [(t,c,e) for t,c,e in self.msgs if e > now]

    def draw(self, r):
        if not self.msgs:
            return
        text, color, _ = self.msgs[-1]
        r.text(W//2, H//2 - 30, text, color=color, size=14, bold=True)


# ── Main Game ──────────────────────────────────────────────────────────────────
class Game:
    def __init__(self, root):
        self.root = root
        root.title('ADVENTURE  —  Pygame-free Clone')
        root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=W, height=H, bg='black',
                                highlightthickness=0)
        self.canvas.pack()
        self.renderer = Renderer(self.canvas)

        self.keys = set()
        # Bind to root so focus is never an issue
        root.bind('<KeyPress>',   self._key_down)
        root.bind('<KeyRelease>', self._key_up)
        root.focus_force()

        _build_sounds()

        self.reset()
        self.last_time = time.time()
        self._loop()

    def reset(self):
        self.player = Player()
        self.room_id = 0
        self.deaths = 0
        self.won = False
        self.win_time = None

        # Items
        self.items = {}
        for rid, rd in ROOM_DEFS.items():
            for iid in rd['items']:
                self.items[iid] = Item(iid, rid)

        # Enemies
        self.enemies = [
            Enemy('bat',     1),
            Enemy('bat',     7),
            Enemy('yorgle',  8),
            Enemy('grundle', 3),
            Enemy('rhindle', 9),
        ]

        self.msgs = MsgQueue()
        self.msgs.add('Find the Enchanted Chalice! Bring it to the Golden Castle!',
                      C_YELLOW, 5.0)

    # ── Input ─────────────────────────────────────────────────────────────────
    def _key_down(self, e):
        self.keys.add(e.keysym.lower())
        if e.keysym.lower() == 'space':
            self._drop_or_grab_bridge()
        if e.keysym.lower() == 's':
            self._attack()
        if e.keysym.lower() == 'r':
            self.reset()
        if e.keysym == 'Escape':
            self.root.destroy()

    def _key_up(self, e):
        self.keys.discard(e.keysym.lower())

    # ── Actions ────────────────────────────────────────────────────────────────
    def _drop_or_grab_bridge(self):
        """SPACE: drop current item, or pick up a nearby bridge from the floor."""
        p = self.player
        if not p.alive: return
        if p.carrying:
            item = p.carrying
            item.x, item.y = int(p.x), int(p.y)
            item.room_id = self.room_id
            item.carried_by = None
            p.carrying = None
            play_sfx('drop')
            self.msgs.add(f'Dropped {ITEM_DEFS[item.id]["name"]}', C_GRAY)
        else:
            # Pick up a bridge that's on the floor nearby
            for item in self._floor_items():
                if item.id == 'bridge' and dist(item.x, item.y, p.x, p.y) < PLAYER_SIZE + 24:
                    p.carrying = item
                    item.carried_by = 'player'
                    play_sfx('pickup')
                    self.msgs.add('Picked up Magic Bridge', C_YELLOW)
                    break

    def _attack(self):
        p = self.player
        if not p.alive: return
        if p.carrying and p.carrying.id == 'sword':
            reach = 42
            px1,py1,px2,py2 = p.x-reach, p.y-reach, p.x+reach, p.y+reach
            for e in self._room_enemies():
                ex1,ey1,ex2,ey2 = e.bounds()
                if rect_collide(px1,py1,px2,py2, ex1,ey1,ex2,ey2):
                    e.hp -= 1
                    e.flash_until = time.time() + 0.15
                    play_sfx('bite')
                    if e.hp <= 0:
                        e.alive = False
                        dropped = e.drop_item()
                        if dropped:
                            dropped.room_id = self.room_id
                        play_sfx('death')
                        self.msgs.add(f'{e.name} defeated!', C_GREEN)
        else:
            self.msgs.add('You need the Magic Sword!', C_RED, 1.5)

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _floor_items(self):
        return [i for i in self.items.values()
                if i.room_id == self.room_id and i.carried_by is None
                and i != self.player.carrying]

    def _room_enemies(self):
        return [e for e in self.enemies if e.room_id == self.room_id and e.alive]

    def _room_def(self):
        return ROOM_DEFS[self.room_id]

    # ── Main Loop ──────────────────────────────────────────────────────────────
    def _loop(self):
        now = time.time()
        dt = min(now - self.last_time, 0.05)
        self.last_time = now

        self._update(dt)
        self._draw()
        self.root.after(FPS_MS, self._loop)

    def _update(self, dt):
        p = self.player
        rd = self._room_def()

        if self.won:
            return

        if not p.alive:
            p.death_timer += dt
            if p.death_timer >= 2.0:
                self._respawn()
            return

        if p.invincible > 0:
            p.invincible -= dt

        # Movement  (WASD or arrow keys; S alone = attack, not move)
        dx = dy = 0
        k = self.keys
        if 'left'  in k or 'a' in k: dx -= 1
        if 'right' in k or 'd' in k: dx += 1
        if 'up'    in k or 'w' in k: dy -= 1
        if 'down'  in k:             dy += 1

        border_walls = build_border_walls(rd['exits'])
        all_walls = border_walls + rd['walls']

        # Collect placed bridges in this room as wall passages
        passages = [(i.x, i.y) for i in self._floor_items() if i.id == 'bridge']

        if dx or dy:
            p.move(dx, dy, all_walls, passages=passages)

        # Auto-pickup: touch an item to grab it; swap if already carrying
        # (bridge is excluded — pick it up manually with SPACE)
        drop_dist = PLAYER_SIZE + 18   # must exceed pickup radius to avoid re-grab loop
        for item in self._floor_items():
            if item.id == 'bridge': continue
            if dist(item.x, item.y, p.x, p.y) < PLAYER_SIZE + 10:
                if p.carrying:
                    old = p.carrying
                    # Drop behind the player (opposite to movement direction)
                    mdx, mdy = p.last_dx, p.last_dy
                    mag = math.hypot(mdx, mdy) or 1
                    old.x = int(p.x - (mdx / mag) * drop_dist)
                    old.y = int(p.y - (mdy / mag) * drop_dist)
                    old.room_id = self.room_id
                    old.carried_by = None
                    play_sfx('drop')
                p.carrying = item
                item.carried_by = 'player'
                item.room_id = self.room_id
                play_sfx('pickup')
                self.msgs.add(f'Got {ITEM_DEFS[item.id]["name"]}', C_YELLOW)
                break

        # Portal
        direction = get_exit_portal(p.x, p.y, rd['exits'])
        if direction:
            self._change_room(direction, rd)

        # Update enemies in current room
        for e in self._room_enemies():
            if e.just_entered:
                play_sfx('monster')
                e.just_entered = False
            e.update(all_walls, p.x, p.y, dt)

            # Bat steals from player on contact
            if e.steals and e.carried_item is None and p.carrying:
                ex1,ey1,ex2,ey2 = e.bounds()
                px1,py1,px2,py2 = p.bounds()
                if rect_collide(px1,py1,px2,py2, ex1,ey1,ex2,ey2):
                    e.carried_item = p.carrying
                    p.carrying.carried_by = e
                    p.carrying = None
                    e.flee_timer = 2.5   # flee for 2.5 s then jump rooms
                    e.drop_timer = random.uniform(4, 9)
                    play_sfx('bat')
                    self.msgs.add(f'{e.name} stole your item!', C_RED)

            # Dragon contact: sword kills dragon, otherwise player dies
            if p.invincible <= 0 and e.lethal:
                ex1,ey1,ex2,ey2 = e.bounds()
                px1,py1,px2,py2 = p.bounds()
                if rect_collide(px1,py1,px2,py2, ex1,ey1,ex2,ey2):
                    if p.carrying and p.carrying.id == 'sword':
                        e.hp -= 1
                        e.flash_until = time.time() + 0.2
                        play_sfx('bite')
                        p.invincible = 0.6   # brief pause before next hit
                        if e.hp <= 0:
                            e.alive = False
                            dropped = e.drop_item()
                            if dropped:
                                dropped.room_id = self.room_id
                            play_sfx('death')
                            self.msgs.add(f'{e.name} slain!', C_GREEN)
                    else:
                        self._die()
                        return

        # Bat: flee to adjacent room after timer, random item drop
        for e in self.enemies:
            if not e.alive or not e.steals or e.carried_item is None:
                continue
            # Random drop
            if e.drop_timer <= 0:
                if random.random() < 0.35:
                    dropped = e.drop_item()
                    if dropped:
                        dropped.room_id = e.room_id
                        dropped.x, dropped.y = safe_spawn(e.room_id, 12, 12)
                        if e.room_id == self.room_id:
                            self.msgs.add(
                                f'The bat dropped {ITEM_DEFS[dropped.id]["name"]}!', C_WHITE)
                e.drop_timer = random.uniform(4, 9)
            # Change room after flee timer
            if e.flee_timer <= 0:
                exits = ROOM_DEFS[e.room_id]['exits']
                target = random.choice(list(exits.values()))
                e.room_id = target
                e.x, e.y = safe_spawn(target, 22, 16)
                if e.carried_item:
                    e.carried_item.room_id = target
                e.flee_timer = 999  # don't re-trigger until next steal

        self.msgs.tick()

        # Win condition
        if p.carrying and p.carrying.id == 'chalice' and self.room_id == 0:
            self.won = True
            self.win_time = time.time()
            play_sfx('victory')
            self.msgs.add('YOU WIN! The Chalice is yours!', C_YELLOW, 999)

    def _change_room(self, direction, rd):
        target_id = rd['exits'][direction]
        target_rd = ROOM_DEFS[target_id]
        lock = target_rd.get('lock')

        if lock:
            p = self.player
            if not (p.carrying and p.carrying.id == lock):
                needed = ITEM_DEFS[lock]['name']
                self.msgs.add(f'Locked! Need {needed}', C_RED, 1.5)
                play_sfx('wall')
                if direction == 'N': self.player.y += 12
                elif direction == 'S': self.player.y -= 12
                elif direction == 'E': self.player.x -= 12
                elif direction == 'W': self.player.x += 12
                return

        play_sfx('portal')
        p = self.player
        if p.carrying:
            p.carrying.room_id = target_id
        self.room_id = target_id

        mx = W // 2; my = H // 2
        mg = TILE + PLAYER_SIZE + 6
        if direction == 'N':   p.x, p.y = mx, H - mg
        elif direction == 'S': p.x, p.y = mx, mg
        elif direction == 'E': p.x, p.y = mg, my
        elif direction == 'W': p.x, p.y = W - mg, my

        for e in self.enemies:
            if e.room_id == target_id and e.alive:
                e.just_entered = True
                # Reposition bats to the far side of the room from the player
                if e.steals:
                    ex, ey = safe_spawn(target_id, 22, 16)
                    # Keep trying until we find a spot at least 300px away
                    for _ in range(30):
                        if math.hypot(ex - p.x, ey - p.y) >= 300:
                            break
                        ex, ey = safe_spawn(target_id, 22, 16)
                    e.x, e.y = ex, ey

    def _die(self):
        p = self.player
        if p.invincible > 0: return
        play_sfx('death')
        p.alive = False
        p.death_timer = 0
        self.deaths += 1
        if p.carrying:
            p.carrying.carried_by = None
            p.carrying = None
        self.msgs.add('You were eaten!  R = respawn', C_RED, 99)

    def _respawn(self):
        p = self.player
        p.alive = True
        p.death_timer = 0
        p.invincible = 2.5
        p.carrying = None
        self.room_id = 0
        p.x, p.y = W//2, H//3

    # ── Drawing ────────────────────────────────────────────────────────────────
    def _draw(self):
        r = self.renderer
        rd = self._room_def()
        r.clear()
        r.fill(rd['bg'])

        border_walls = build_border_walls(rd['exits'])
        r.draw_walls(border_walls)
        r.draw_walls(rd['walls'])

        # Floor items
        for item in self._floor_items():
            r.draw_item(item.id, int(item.x), int(item.y))

        # Enemies
        for e in self._room_enemies():
            r.draw_enemy(e)

        # Player
        p = self.player
        if p.alive or int(p.death_timer * 8) % 2 == 0:
            r.draw_player(int(p.x), int(p.y))
            if p.carrying:
                r.draw_item(p.carrying.id, int(p.x), int(p.y) - PLAYER_SIZE - 8)

        # Room name
        r.text(W//2, 6, rd['name'], color=C_WHITE, size=11, anchor='n')

        # HUD
        if p.carrying:
            name = ITEM_DEFS[p.carrying.id]['name']
            r.text(8, H-10, f'Carrying: {name}', color=C_YELLOW, size=12, anchor='sw')

        r.text(W//2, H-10, 'ARROWS=move  S=attack  SPACE=drop/grab bridge', color=C_GRAY, size=10)
        r.text(W-8, 8, f'Deaths: {self.deaths}', color=C_GRAY, size=11, anchor='ne')

        # Messages
        self.msgs.draw(r)

        # Death overlay
        if not p.alive:
            r.rect(W//4, H//2-50, 3*W//4, H//2+60, fill='#800000', outline=C_RED)
            r.text(W//2, H//2-20, 'EATEN!', color=C_RED, size=28, bold=True)
            r.text(W//2, H//2+20, 'Press R to respawn', color=C_WHITE, size=14)

        # Win overlay
        if self.won:
            t = time.time() - (self.win_time or 0)
            flash = C_YELLOW if int(t*3)%2==0 else C_ORANGE
            r.rect(W//6, H//2-70, 5*W//6, H//2+70, fill='#404000', outline=C_YELLOW)
            r.text(W//2, H//2-40, 'YOU WIN!', color=flash, size=32, bold=True)
            r.text(W//2, H//2+5,  'The Enchanted Chalice is yours!', color=C_WHITE, size=14)
            r.text(W//2, H//2+35, f'Deaths: {self.deaths}    Press R to play again', color=C_GRAY, size=12)


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    root = tk.Tk()
    root.configure(bg='black')
    game = Game(root)
    root.mainloop()
