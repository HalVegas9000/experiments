#!/usr/bin/env python3
"""
Hal Invaders
Controls: LEFT/RIGHT or A/D — move | SPACE — fire | Q/Esc — quit
"""

import tkinter as tk
import math, random, struct, wave, os, subprocess, threading, tempfile

# ── Window / Layout ────────────────────────────────────────────────────
W, H       = 1024, 768
PANEL_H    = 48          # top HUD bar height
GROUND_Y   = H - 62      # green ground line y
PLAYER_Y   = GROUND_Y - 22  # player cannon centre y
LIVES_Y    = H - 30      # lives icons row y

# ── Invader Grid ───────────────────────────────────────────────────────
ROWS, COLS   = 5, 11
CW, CH       = 68, 52    # cell spacing (px)
SCALE        = 4         # pixel-art scale factor
INV_W        = 11 * SCALE  # 44 px sprite display width
INV_H        = 8  * SCALE  # 32 px sprite display height
GRID_X0      = (W - COLS * CW) // 2 + CW // 2
GRID_Y0      = PANEL_H + 72

# ── Colours ────────────────────────────────────────────────────────────
BG         = "#000010"
P_COL      = "#00ff88"   # player green
HUD_COL    = "#00ffff"   # HUD cyan
GND_COL    = "#00ff88"   # ground line
SHD_COL    = "#00cc44"   # shield green
PB_COL     = "#ffff33"   # player bullet
EB_COL     = "#ff3333"   # enemy bullet
UFO_COL    = "#ff44ff"   # UFO magenta
EXP_COLS   = ["#ff8800","#ffdd00","#ffffff","#ff4400","#cc0000"]
INV_COLS   = ["#ff44aa","#ff8822","#ffee22","#22ccff","#9944ff"]
INV_PTS    = [30, 20, 20, 10, 10]

# ── Alien names by type ────────────────────────────────────────────────
_NAMES = {
    'C': ["ZORBAX", "ZZEEP", "GLEEP-9", "SKRONK", "FNORL", "QUAZBOT",
          "BLEEPTOR", "WUMPLE", "YIBBLE", "SNARF", "ZILCH THE WISE"],
    'B': ["GRUNTLE", "SNORFAX", "MOOGAR", "BLEEZAK", "SPLORCH",
          "FUMPLE JR", "KLUGNOR", "DRIBZOR", "SNUGG", "BLORPLE", "ZILNOX"],
    'A': ["SQUORK", "FLIBBLE", "DRIZZAX", "MOOGLES", "PLONK",
          "KRUNGLE", "BLARGLE", "WOBLOR", "GURP", "FUMZOR", "SNEEPLY"],
}
_UFO_NAMES = ["BOB", "SUPREME OVERLORD", "CAPT. ZARKON", "THE BOSS",
              "MEGA ZORG", "URGLE", "ZORBLON THE ANCIENT"]

UFO_BOMB_COL  = "#ff8800"   # orange UFO bomb
UFO_BOMB_SPD  = 3           # px/frame (slower than normal enemy bullets)
UFO_BOMB_RATE = 130         # frames between UFO bomb drops

# ── Power-up ───────────────────────────────────────────────────────────
PU_COL        = "#00ffff"   # cyan power-up
PU_GLOW       = "#003344"   # dark glow behind it
PU_SPAWN_MIN  = 500         # min frames between power-up spawns
PU_SPAWN_MAX  = 950         # max frames between power-up spawns
PU_DURATION   = 10000       # ms the double-fire effect lasts
PU_DRIFT      = 0.5         # px/frame the power-up drifts downward
PU_BLINK_RATE = 24          # frames per blink cycle when low on time

# ── Physics / Timing ───────────────────────────────────────────────────
LOOP_MS    = 16          # ~60 fps
PSPD       = 7           # player px/frame
PBSPD      = 15          # player bullet px/frame
EBSPD      = 5           # enemy bullet px/frame
MAX_PB     = 1           # max simultaneous player bullets
MAX_EB     = 4           # max simultaneous enemy bullets
MBASE_MS   = 850         # march interval at 55 invaders
MMIN_MS    = 65          # march interval at 1 invader
MSTEP_PX   = 8           # px sideways per march step
DROP_PX    = 26          # px drop when reversing

# ── Sound Generation ──────────────────────────────────────────────────
_TMPDIR = tempfile.mkdtemp(prefix="si_")

def _write_wav(path, samples, rate=22050):
    with wave.open(path, 'w') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate)
        f.writeframes(struct.pack(f'<{len(samples)}h', *samples))

def _sine(f, dur, rate=22050, vol=16000):
    n = int(rate * dur)
    return [int(vol * math.sin(2 * math.pi * f * i / rate)) for i in range(n)]

def _square(f, dur, rate=22050, vol=8000):
    n = int(rate * dur); p = rate / max(f, 1)
    return [vol if (i % p) < p / 2 else -vol for i in range(n)]

def _noise(dur, rate=22050, vol=10000):
    return [random.randint(-vol, vol) for _ in range(int(rate * dur))]

def _sweep(f0, f1, dur, rate=22050, vol=16000):
    n = int(rate * dur)
    return [int(vol * math.sin(2 * math.pi * (f0 + (f1 - f0) * i / n) * i / rate))
            for i in range(n)]

def _fade(s):
    n = len(s)
    return [int(x * (1 - i / n)) for i, x in enumerate(s)]

def _clamp(s):
    return [max(-32767, min(32767, x)) for x in s]

def _mix(a, b):
    mn = min(len(a), len(b))
    return [a[i] + b[i] for i in range(mn)]

def gen_sounds():
    snd = {}
    # Player laser: high-freq sweep down
    snd['shoot']  = _clamp(_fade(_sweep(1300, 250, 0.13)))
    # Enemy laser: buzzy square wave
    snd['eshoot'] = _clamp(_fade(_square(280, 0.20)))
    # Explosion: noise burst
    snd['boom']   = _clamp(_fade(_noise(0.30, vol=14000)))
    # Player death: descending sweep + noise
    snd['pdie']   = _clamp(_fade(_mix(_sweep(800, 60, 0.55), _noise(0.55, vol=6000))))
    # UFO: warbling tone
    ufo_s = []
    for j in range(12):
        ufo_s += _square(280 + j * 25, 0.035, vol=5500)
    snd['ufo']    = _clamp(ufo_s)
    # Level-up fanfare
    snd['win']    = _clamp(_sine(880,0.08) + _sine(1100,0.08) + _sine(1320,0.12) + _sine(1760,0.20))
    # UFO hit
    snd['ufohit'] = _clamp(_fade(_mix(_sweep(1200,200,0.3), _noise(0.3, vol=8000))))
    # UFO bomb drop: low descending wobble
    snd['ufobomb'] = _clamp(_fade(_square(180, 0.22, vol=7000)))
    # Power-up collect: bright ascending arpeggio
    snd['powerup'] = _clamp(
        _sine(880, 0.07) + _sine(1100, 0.07) + _sine(1320, 0.07) + _sine(1760, 0.12))
    # 4 march steps (classic low "dum dum dum dum")
    for i, freq in enumerate([160, 130, 100, 120]):
        snd[f'march{i}'] = _clamp(_fade(_square(freq, 0.07)))
    # Write all to tmp files
    paths = {}
    for name, samples in snd.items():
        p = os.path.join(_TMPDIR, f'{name}.wav')
        _write_wav(p, samples)
        paths[name] = p
    return paths

def play_snd(paths, name):
    p = paths.get(name)
    if not p:
        return
    def _go():
        subprocess.run(['aplay', '-q', p],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    threading.Thread(target=_go, daemon=True).start()

# ── Pixel-Art Invader Patterns (11 wide × 8 tall) ─────────────────────
# '#' = coloured pixel, '.' = transparent (background colour)

_SQUID_0 = [     # Type C — top row  30 pts  Frame 0
    "...##.##...",
    "....###....",
    ".#########.",
    "##.#####.##",
    "###########",
    ".###.#.###.",
    "..#.....#..",
    ".#.......#.",
]
_SQUID_1 = [     # Type C  Frame 1
    "...##.##...",
    "....###....",
    ".#########.",
    "##.#####.##",
    "###########",
    ".###.#.###.",
    ".#.......#.",
    "..#.....#..",
]
_CRAB_0 = [      # Type B — mid rows  20 pts  Frame 0
    ".#.......#.",
    "..#.....#..",
    ".#########.",
    "##.#.#.#.##",
    "###########",
    ".#########.",
    "..#.....#..",
    ".#.......#.",
]
_CRAB_1 = [      # Type B  Frame 1
    "..#.....#..",
    ".#.......#.",
    ".#########.",
    "##.#.#.#.##",
    "###########",
    ".#########.",
    ".#.......#.",
    "..#.....#..",
]
_OCTO_0 = [      # Type A — bot rows  10 pts  Frame 0
    "....###....",
    ".#.#####.#.",
    "###########",
    "##.#####.##",
    "###########",
    ".#.#.#.#.#.",
    "#.#.....#.#",
    ".#.......#.",
]
_OCTO_1 = [      # Type A  Frame 1
    "....###....",
    ".#.#####.#.",
    "###########",
    "##.#####.##",
    "###########",
    ".#.#.#.#.#.",
    ".#.......#.",
    "#.#.....#.#",
]

_INV_FRAMES = {
    'C': [_SQUID_0, _SQUID_1],
    'B': [_CRAB_0,  _CRAB_1],
    'A': [_OCTO_0,  _OCTO_1],
}
_ROW_TYPE = ['C', 'B', 'B', 'A', 'A']


def _make_sprite(pattern, color, bg=BG, scale=SCALE):
    """Build a tk.PhotoImage from an 11×8 pixel-art pattern."""
    rows = len(pattern)
    cols = len(pattern[0])
    img = tk.PhotoImage(width=cols * scale, height=rows * scale)
    for ry, row in enumerate(pattern):
        px = []
        for ch in row:
            c = color if ch == '#' else bg
            px.extend([c] * scale)
        row_str = '{' + ' '.join(px) + '}'
        for sy in range(scale):
            img.put(row_str, to=(0, ry * scale + sy))
    return img


def gen_sprites():
    """Pre-generate all PhotoImage sprites. Call after Tk root exists."""
    sprites = {}  # sprites[row_idx][frame] = PhotoImage
    for row in range(ROWS):
        itype = _ROW_TYPE[row]
        color = INV_COLS[row]
        sprites[row] = [
            _make_sprite(_INV_FRAMES[itype][0], color),
            _make_sprite(_INV_FRAMES[itype][1], color),
        ]
    # UFO sprite (16 wide × 6 tall)
    ufo_pat = [
        "....######....",
        "..##########..",
        ".############.",
        "##.##.##.##.##",
        ".############.",
        "...#..##..#...",
    ]
    sprites['ufo'] = _make_sprite(ufo_pat, UFO_COL)
    return sprites


# ── Shield bunker shape ────────────────────────────────────────────────
# 11 wide × 7 tall, '#' = block (each block is 6×6 px)
_BUNKER = [
    "..#######..",
    ".#########.",
    "###########",
    "###########",
    "###########",
    "####...####",
    "###.....###",
]
BLOCK = 5  # shield block size in px


# ══════════════════════════════════════════════════════════════════════
#  GAME CLASS
# ══════════════════════════════════════════════════════════════════════

class SpaceInvaders:
    def __init__(self, root):
        self.root = root
        root.title("Hal Invaders")
        root.resizable(False, False)
        root.configure(bg="black")

        self.canvas = tk.Canvas(root, width=W, height=H, bg=BG,
                                highlightthickness=0)
        self.canvas.pack()

        # Generate assets (sounds first, sprites after Tk root exists)
        self.sounds  = gen_sounds()
        self.sprites = gen_sprites()

        # Persistent canvas item refs that survive between frames
        self._hud_score_id = None
        self._hud_hi_id    = None
        self._hud_level_id = None

        # Key state
        self.keys = set()
        root.bind('<KeyPress>',   self._key_dn)
        root.bind('<KeyRelease>', self._key_up)
        root.bind('<Escape>', lambda e: root.quit())
        root.bind('q',        lambda e: root.quit())

        self.state           = 'intro'
        self.hiscore         = 0
        self._loop_id        = None
        self._march_after    = None
        self._march_note_idx = 0

        self._show_intro()

    # ── Input ──────────────────────────────────────────────────────────
    def _key_dn(self, e):
        k = e.keysym.lower()
        self.keys.add(k)
        if k == 'space':
            if self.state == 'intro':
                self.new_game()
            elif self.state == 'playing':
                self._fire_player()
            elif self.state in ('gameover', 'win'):
                self._show_intro()

    def _key_up(self, e):
        self.keys.discard(e.keysym.lower())

    # ── Intro screen ───────────────────────────────────────────────────
    def _show_intro(self):
        self.state = 'intro'
        if self._loop_id:
            self.root.after_cancel(self._loop_id)
            self._loop_id = None
        if self._march_after:
            self.root.after_cancel(self._march_after)
            self._march_after = None
        c = self.canvas
        c.delete('all')
        c.create_text(W//2, 140, text="HAL INVADERS",
                      font=("Courier", 42, "bold"), fill="#00ffff")
        c.create_text(W//2, 210, text="Score table",
                      font=("Courier", 16), fill="#aaaaaa")
        # Show invader types and points
        sample_y = 255
        type_rows  = [0, 1, 3]           # representative row index per type
        type_names = ['C', 'B', 'A']
        type_pts   = [30, 20, 10]
        for i, (row_idx, itype, pts) in enumerate(zip(type_rows, type_names, type_pts)):
            img   = self.sprites[row_idx][0]
            col   = INV_COLS[row_idx]
            xi    = W//2 - 120
            c.create_image(xi, sample_y, image=img)
            c.create_text(xi + 44, sample_y - 8, text=f"= {pts} PTS",
                          font=("Courier", 13, "bold"), fill=col, anchor='w')
            c.create_text(xi + 44, sample_y + 8, text=_NAMES[itype][0],
                          font=("Courier", 10), fill="#888888", anchor='w')
            sample_y += 58
        # UFO row
        c.create_image(W//2 - 120, sample_y, image=self.sprites['ufo'])
        c.create_text(W//2 - 76, sample_y - 8, text="= ??? PTS  (SHOOTS BOMBS!)",
                      font=("Courier", 13, "bold"), fill=UFO_COL, anchor='w')
        c.create_text(W//2 - 76, sample_y + 8, text=_UFO_NAMES[0],
                      font=("Courier", 10), fill="#888888", anchor='w')

        c.create_text(W//2, H - 140, text="PRESS  SPACE  TO  START",
                      font=("Courier", 20, "bold"), fill="#ffff00")
        c.create_text(W//2, H - 100, text="← → or A D  move     SPACE  fire",
                      font=("Courier", 13), fill="#888888")
        c.create_text(W//2, H - 70,  text=f"HI-SCORE  {self.hiscore:05d}",
                      font=("Courier", 14), fill="#00ffff")

    # ── New game ───────────────────────────────────────────────────────
    def new_game(self):
        if self._loop_id:
            self.root.after_cancel(self._loop_id)
            self._loop_id = None
        if self._march_after:
            self.root.after_cancel(self._march_after)
            self._march_after = None
        self._march_note_idx = 0

        self.canvas.delete('all')
        self.state        = 'playing'
        self.score        = 0
        self.level        = 1
        self.lives        = 3
        self.px           = W // 2   # player x centre
        self.player_frame = 0        # for death animation
        self.dead_timer   = 0        # >0 while player is dying

        # Invader grid state
        self.inv_frame    = 0        # animation frame (0/1), toggled on march
        self.grid_dx      = 1        # march direction (+1 right, -1 left)
        self.grid_ox      = 0        # accumulated x offset from initial
        self.grid_oy      = 0        # accumulated y offset
        self.need_drop    = False

        self._init_invaders()

        self.pbullets  = []   # list of {'y': float, 'id': canvas_id}
        self.ebullets  = []   # list of {'x': float, 'y': float, 'id': canvas_id}
        self.explosions= []   # list of {'x','y','frame','max','ids':[]}

        # UFO
        self.ufo       = None
        self.ufo_timer = random.randint(400, 900)  # frames until next UFO appears
        self.ufo_bombs = []   # list of {'x','y','id'}

        # Power-up
        self.powerup        = None   # {'x','y','ids':[],'blink':0} when on screen
        self.powerup_timer  = random.randint(PU_SPAWN_MIN, PU_SPAWN_MAX)
        self.powerup_active = False  # True while double-fire is in effect
        self._pu_reset_id   = None   # after() handle for deactivation
        self._pu_hud_id     = None   # canvas text item for active indicator

        self._init_shields()
        self._draw_hud()
        self._draw_ground()

        # March (separate timer)
        self._march_after = None
        self._schedule_march()

        # UFO sound loop ref
        self._ufo_playing = False

        self._loop()

    # ── Level reset (same lives, new grid) ────────────────────────────
    def _next_level(self):
        self.level += 1
        self.canvas.delete('invaders')
        self.canvas.delete('ebullet')
        self.canvas.delete('pbullet')
        self.canvas.delete('shield')
        self.canvas.delete('explosion')
        self.canvas.delete('ufo')
        self.canvas.delete('ufobomb')
        self.canvas.delete('powerup')
        self.pbullets   = []
        self.ebullets   = []
        self.explosions = []
        self.ufo        = None
        self.ufo_timer  = random.randint(400, 900)
        self.ufo_bombs  = []
        self.powerup    = None
        self.powerup_timer = random.randint(PU_SPAWN_MIN, PU_SPAWN_MAX)
        self.grid_dx    = 1
        self.grid_ox    = 0
        self.grid_oy    = 0
        self.need_drop  = False
        self.inv_frame  = 0
        self._init_invaders()
        self._init_shields()
        play_snd(self.sounds, 'win')

    # ── Invader initialisation ────────────────────────────────────────
    def _init_invaders(self):
        """Create invader dict list and canvas images."""
        self.canvas.delete('invaders')
        self.invaders    = []
        self.alive_count = 0
        # Build per-type name pools (shuffled so every wave has fresh names)
        name_pools = {k: random.sample(v, len(v)) for k, v in _NAMES.items()}
        name_idx   = {'C': 0, 'B': 0, 'A': 0}
        for r in range(ROWS):
            for c in range(COLS):
                x0    = GRID_X0 + c * CW + self.grid_ox
                y0    = GRID_Y0 + r * CH + self.grid_oy
                itype = _ROW_TYPE[r]
                pool  = name_pools[itype]
                name  = pool[name_idx[itype] % len(pool)]
                name_idx[itype] += 1
                img = self.sprites[r][self.inv_frame]
                cid = self.canvas.create_image(x0, y0, image=img, tags='invaders')
                self.invaders.append({
                    'row': r, 'col': c,
                    'x': x0, 'y': y0,
                    'alive': True,
                    'id': cid,
                    'name': name,
                })
                self.alive_count += 1

    # ── Shield initialisation ─────────────────────────────────────────
    def _init_shields(self):
        """Create 4 shield bunkers."""
        self.canvas.delete('shield')
        self.shields = []
        n_shields = 4
        spacing   = W // (n_shields + 1)
        sy_centre = GROUND_Y - 90
        for s in range(n_shields):
            sx = spacing * (s + 1) - (len(_BUNKER[0]) * BLOCK) // 2
            sy = sy_centre - (len(_BUNKER) * BLOCK) // 2
            for ry, row in enumerate(_BUNKER):
                for cx, ch in enumerate(row):
                    if ch != '#':
                        continue
                    bx = sx + cx * BLOCK
                    by = sy + ry * BLOCK
                    bid = self.canvas.create_rectangle(
                        bx, by, bx + BLOCK - 1, by + BLOCK - 1,
                        fill=SHD_COL, outline='', tags='shield')
                    self.shields.append({'x1': bx, 'y1': by,
                                         'x2': bx + BLOCK - 1, 'y2': by + BLOCK - 1,
                                         'id': bid, 'alive': True, 'hp': 2})

    # ── HUD ───────────────────────────────────────────────────────────
    def _draw_hud(self):
        c = self.canvas
        c.delete('hud')
        c.create_rectangle(0, 0, W, PANEL_H, fill="#000030", outline='', tags='hud')
        self._hud_score_id = c.create_text(
            10, PANEL_H // 2, text=f"SCORE  {self.score:05d}",
            anchor='w', font=("Courier", 14, "bold"), fill=HUD_COL, tags='hud')
        self._hud_hi_id = c.create_text(
            W // 2, PANEL_H // 2, text=f"HI  {self.hiscore:05d}",
            anchor='center', font=("Courier", 14, "bold"), fill="#aaaaaa", tags='hud')
        self._hud_level_id = c.create_text(
            W - 10, PANEL_H // 2, text=f"LEVEL {self.level}",
            anchor='e', font=("Courier", 14, "bold"), fill=HUD_COL, tags='hud')

    def _update_hud(self):
        self.canvas.itemconfigure(self._hud_score_id,
                                   text=f"SCORE  {self.score:05d}")
        self.canvas.itemconfigure(self._hud_hi_id,
                                   text=f"HI  {self.hiscore:05d}")
        self.canvas.itemconfigure(self._hud_level_id,
                                   text=f"LEVEL {self.level}")

    def _draw_lives(self):
        self.canvas.delete('lives')
        for i in range(self.lives):
            x = 16 + i * 38
            self._draw_player_ship(x, LIVES_Y, small=True, tag='lives')

    # ── Player drawing ────────────────────────────────────────────────
    def _draw_player_ship(self, cx, cy, small=False, tag='player'):
        """Draw the player's cannon at (cx, cy)."""
        s = 0.55 if small else 1.0
        w2 = int(24 * s); h2 = int(18 * s); nt = int(6 * s)
        pts = [
            cx,       cy - h2,
            cx + nt,  cy - h2 + nt,
            cx + w2,  cy - h2 + nt,
            cx + w2,  cy,
            cx - w2,  cy,
            cx - w2,  cy - h2 + nt,
            cx - nt,  cy - h2 + nt,
        ]
        col = P_COL if not small else "#007744"
        self.canvas.create_polygon(pts, fill=col, outline='', tags=tag)
        # Base bar
        self.canvas.create_rectangle(cx - w2, cy, cx + w2, cy + int(5 * s),
                                      fill=col, outline='', tags=tag)

    # ── March (separate timer) ────────────────────────────────────────
    def _schedule_march(self):
        """Compute next march delay and schedule."""
        if self.alive_count > 0:
            frac   = self.alive_count / (ROWS * COLS)
            delay  = max(MMIN_MS, int(MBASE_MS * frac))
            # Extra speed boost at low counts
            if self.alive_count <= 8:
                delay = max(MMIN_MS, delay - 30)
        else:
            delay = MBASE_MS
        self._march_after = self.root.after(delay, self._march_step)

    def _march_step(self):
        if self.state != 'playing':
            return
        play_snd(self.sounds, f'march{self._march_note()}')

        if self.need_drop:
            # Drop down and reverse
            dx_px = 0
            dy_px = DROP_PX
            self.grid_dx  *= -1
            self.grid_oy  += DROP_PX
            self.need_drop = False
        else:
            dx_px = self.grid_dx * MSTEP_PX
            dy_px = 0
            self.grid_ox += dx_px

        # Move all alive invaders
        for inv in self.invaders:
            if not inv['alive']:
                continue
            inv['x'] += dx_px
            inv['y'] += dy_px
            self.canvas.move(inv['id'], dx_px, dy_px)

        # Toggle animation frame
        self.inv_frame ^= 1
        for inv in self.invaders:
            if inv['alive']:
                self.canvas.itemconfigure(inv['id'],
                    image=self.sprites[inv['row']][self.inv_frame])

        # Check if any invader has hit the wall → set need_drop for NEXT step
        self._check_edge()

        self._schedule_march()

    def _march_note(self):
        n = self._march_note_idx
        self._march_note_idx = (n + 1) % 4
        return n

    def _check_edge(self):
        """Check whether the leading edge of the invader swarm has hit the wall.
        Only check the wall we are currently marching TOWARD — this prevents the
        immediate re-trigger that would occur if we checked both walls after a
        drop (the invaders haven't moved horizontally yet, so the just-hit wall
        would fire again and cause perpetual dropping with no sideways movement).
        """
        margin = 28
        for inv in self.invaders:
            if not inv['alive']:
                continue
            if self.grid_dx > 0:          # marching right → watch right wall
                if inv['x'] + INV_W // 2 + margin >= W:
                    self.need_drop = True
                    return
            else:                         # marching left  → watch left wall
                if inv['x'] - INV_W // 2 - margin <= 0:
                    self.need_drop = True
                    return

    # ── Game loop ─────────────────────────────────────────────────────
    def _loop(self):
        if self.state != 'playing':
            return
        self._update()
        self._loop_id = self.root.after(LOOP_MS, self._loop)

    def _update(self):
        # Player movement
        if self.dead_timer <= 0:
            if 'left' in self.keys or 'a' in self.keys:
                self.px = max(28, self.px - PSPD)
            if 'right' in self.keys or 'd' in self.keys:
                self.px = min(W - 28, self.px + PSPD)

        # Update bullets
        self._update_pbullets()
        self._update_ebullets()

        # Enemy fire
        self._maybe_enemy_fire()

        # UFO + UFO bombs
        self._update_ufo()
        self._update_ufo_bombs()

        # Power-up
        self._update_powerup()

        # Explosions
        self._update_explosions()

        # Redraw player
        self.canvas.delete('player')
        if self.dead_timer > 0:
            self.dead_timer -= 1
            # Flash explosion where player was
            self._draw_death_flash()
            if self.dead_timer == 0:
                if self.lives > 0:
                    # Respawn
                    self.px = W // 2
                else:
                    self._game_over()
                    return
        else:
            self._draw_player_ship(self.px, PLAYER_Y)

        # HUD
        self._update_hud()
        self._draw_lives()

        # Check win
        if self.alive_count == 0:
            self._next_level()

        # Check invaders reached ground
        for inv in self.invaders:
            if inv['alive'] and inv['y'] + INV_H // 2 >= GROUND_Y:
                self._game_over()
                return

    # ── Player bullet ─────────────────────────────────────────────────
    def _fire_player(self):
        if self.dead_timer > 0:
            return
        max_pb = 2 if self.powerup_active else MAX_PB
        if len(self.pbullets) >= max_pb:
            return
        bx = self.px
        by = PLAYER_Y - 18
        bid = self.canvas.create_rectangle(
            bx - 2, by - 8, bx + 2, by,
            fill=PB_COL, outline='', tags='pbullet')
        self.pbullets.append({'x': bx, 'y': float(by), 'id': bid})
        play_snd(self.sounds, 'shoot')

    def _update_pbullets(self):
        alive = []
        for b in self.pbullets:
            prev_y = b['y']
            b['y'] -= PBSPD
            if b['y'] < PANEL_H:
                self.canvas.delete(b['id'])
                continue
            # Move on canvas
            self.canvas.move(b['id'], 0, -PBSPD)

            # Hit invader?
            hit = self._pbullet_hit_invader(b)
            if hit:
                self.canvas.delete(b['id'])
                continue

            # Hit UFO?
            if self._pbullet_hit_ufo(b):
                self.canvas.delete(b['id'])
                continue

            # Hit power-up?
            if self._pbullet_hit_powerup(b):
                self.canvas.delete(b['id'])
                continue

            # Hit shield? (swept from prev_y to current y)
            if self._bullet_hit_shield(b['x'], b['y'], prev_y):
                self.canvas.delete(b['id'])
                continue

            alive.append(b)
        self.pbullets = alive

    def _pbullet_hit_invader(self, b):
        bx, by = b['x'], b['y']
        for inv in self.invaders:
            if not inv['alive']:
                continue
            if (abs(bx - inv['x']) < INV_W // 2 + 4 and
                    abs(by - inv['y']) < INV_H // 2 + 4):
                self._kill_invader(inv)
                return True
        return False

    def _pbullet_hit_ufo(self, b):
        if not self.ufo:
            return False
        ufo = self.ufo
        if (abs(b['x'] - ufo['x']) < 38 and abs(b['y'] - ufo['y']) < 20):
            pts = random.choice([50, 100, 150, 200, 300])
            self.score   += pts
            self.hiscore  = max(self.hiscore, self.score)
            self._add_explosion(ufo['x'], ufo['y'], big=True)
            play_snd(self.sounds, 'ufohit')
            self.canvas.delete(ufo['id'])
            self.canvas.delete('ufoscore')
            sid = self.canvas.create_text(
                ufo['x'], ufo['y'] - 10, text=f"+{pts}",
                font=("Courier", 14, "bold"), fill=UFO_COL, tags='ufoscore')
            self.root.after(800, lambda: self.canvas.delete('ufoscore'))
            self.ufo       = None
            self.ufo_timer = random.randint(400, 900)
            return True
        return False

    # ── Enemy bullets ─────────────────────────────────────────────────
    def _maybe_enemy_fire(self):
        if len(self.ebullets) >= MAX_EB:
            return
        if self.alive_count == 0:
            return
        # Probability scales up as invaders die (more aggressive fewer invaders)
        base_p  = 0.012
        scale_p = 1.0 + (1.0 - self.alive_count / (ROWS * COLS)) * 2.5
        if random.random() > base_p * scale_p:
            return
        # Pick a random bottom-of-column invader
        cols_alive = {}
        for inv in self.invaders:
            if inv['alive']:
                c = inv['col']
                if c not in cols_alive or inv['row'] > cols_alive[c]['row']:
                    cols_alive[c] = inv
        if not cols_alive:
            return
        shooter = random.choice(list(cols_alive.values()))
        bx, by  = shooter['x'], shooter['y'] + INV_H // 2
        bid = self.canvas.create_rectangle(
            bx - 2, by, bx + 2, by + 10,
            fill=EB_COL, outline='', tags='ebullet')
        self.ebullets.append({'x': float(bx), 'y': float(by), 'id': bid})
        play_snd(self.sounds, 'eshoot')

    def _update_ebullets(self):
        alive = []
        for b in self.ebullets:
            prev_y = b['y']
            b['y'] += EBSPD
            if b['y'] > GROUND_Y + 10:
                self.canvas.delete(b['id'])
                continue
            self.canvas.move(b['id'], 0, EBSPD)

            # Hit player?
            if (self.dead_timer == 0 and
                    abs(b['x'] - self.px) < 20 and
                    abs(b['y'] - PLAYER_Y) < 16):
                self.canvas.delete(b['id'])
                self._player_hit()
                continue

            # Hit shield? (swept from prev_y to current y)
            if self._bullet_hit_shield(b['x'], b['y'], prev_y):
                self.canvas.delete(b['id'])
                continue

            alive.append(b)
        self.ebullets = alive

    # ── Shield collision ──────────────────────────────────────────────
    def _bullet_hit_shield(self, bx, by, prev_by):
        """Swept collision: check the full y-range the bullet travelled this
        frame, not just its current position.  Without this, a fast bullet
        (PBSPD=15) can jump completely over an 8-px-tall block in one frame."""
        y_lo = min(by, prev_by)
        y_hi = max(by, prev_by)
        for sh in self.shields:
            if not sh['alive']:
                continue
            # x overlap (bullet is 4 px wide centred at bx)
            if bx + 2 < sh['x1'] or bx - 2 > sh['x2']:
                continue
            # y overlap with swept segment
            if y_hi < sh['y1'] or y_lo > sh['y2']:
                continue
            sh['hp'] -= 1
            if sh['hp'] <= 0:
                sh['alive'] = False
                self.canvas.delete(sh['id'])
            else:
                self.canvas.itemconfigure(sh['id'], fill="#005522")
            return True
        return False

    # ── Kill invader ──────────────────────────────────────────────────
    def _kill_invader(self, inv):
        pts            = INV_PTS[inv['row']]
        self.score    += pts
        self.hiscore   = max(self.hiscore, self.score)
        inv['alive']   = False
        self.alive_count -= 1
        self.canvas.delete(inv['id'])
        self._add_explosion(inv['x'], inv['y'])
        play_snd(self.sounds, 'boom')
        # Brief score pop-up
        col = INV_COLS[inv['row']]
        sid = self.canvas.create_text(
            inv['x'], inv['y'] - 8, text=f"+{pts}",
            font=("Courier", 11, "bold"), fill=col)
        self.root.after(500, lambda: self.canvas.delete(sid))

    # ── Player hit ────────────────────────────────────────────────────
    def _player_hit(self):
        if self.dead_timer > 0:
            return
        self.lives     -= 1
        self.dead_timer = 120   # ~2 s of death animation
        self._add_explosion(self.px, PLAYER_Y, big=True)
        play_snd(self.sounds, 'pdie')
        # Clear all bullets
        for b in self.pbullets:
            self.canvas.delete(b['id'])
        for b in self.ebullets:
            self.canvas.delete(b['id'])
        self.pbullets = []
        self.ebullets = []

    def _draw_death_flash(self):
        if (self.dead_timer // 8) % 2 == 0:
            # Draw a glitchy ghost of the ship
            self._draw_player_ship(self.px, PLAYER_Y)
            # Recolour it red
            for item in self.canvas.find_withtag('player'):
                self.canvas.itemconfigure(item, fill="#ff2200")

    # ── Explosions ────────────────────────────────────────────────────
    def _add_explosion(self, x, y, big=False):
        ids  = []
        r    = 4 if not big else 8
        col  = random.choice(EXP_COLS)
        cid  = self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                        fill=col, outline='', tags='explosion')
        ids.append(cid)
        # Sparks
        for _ in range(6 if not big else 12):
            angle = random.uniform(0, 2 * math.pi)
            sr    = random.uniform(r, r + (6 if not big else 14))
            ex    = x + sr * math.cos(angle)
            ey    = y + sr * math.sin(angle)
            lc = random.choice(EXP_COLS)
            lid = self.canvas.create_line(x, y, ex, ey,
                                           fill=lc, width=2, tags='explosion')
            ids.append(lid)
        self.explosions.append({
            'x': x, 'y': y,
            'frame': 0,
            'max': 16 if not big else 22,
            'ids': ids,
            'big': big,
        })

    def _update_explosions(self):
        alive = []
        for ex in self.explosions:
            ex['frame'] += 1
            frac = ex['frame'] / ex['max']
            if frac >= 1.0:
                for i in ex['ids']:
                    self.canvas.delete(i)
                continue
            # Expand and recolour
            r   = (4 + frac * (18 if not ex['big'] else 36))
            col = EXP_COLS[min(int(frac * len(EXP_COLS)), len(EXP_COLS) - 1)]
            x, y = ex['x'], ex['y']
            if ex['ids']:
                # first id is the central oval
                self.canvas.coords(ex['ids'][0],
                                    x - r, y - r, x + r, y + r)
                self.canvas.itemconfigure(ex['ids'][0], fill=col)
            # Recolour sparks
            for lid in ex['ids'][1:]:
                self.canvas.itemconfigure(lid, fill=col)
            alive.append(ex)
        self.explosions = alive

    # ── UFO ───────────────────────────────────────────────────────────
    def _update_ufo(self):
        if self.ufo is None:
            self.ufo_timer -= 1
            if self.ufo_timer <= 0:
                self._spawn_ufo()
            return

        ufo = self.ufo
        ufo['x'] += ufo['dx'] * 3
        self.canvas.move(ufo['id'], ufo['dx'] * 3, 0)

        # Play UFO sound periodically
        if not self._ufo_playing:
            self._ufo_playing = True
            play_snd(self.sounds, 'ufo')
            self.root.after(1600, self._reset_ufo_sound)

        # Drop a bomb periodically
        ufo['bomb_timer'] -= 1
        if ufo['bomb_timer'] <= 0:
            ufo['bomb_timer'] = UFO_BOMB_RATE
            bx = ufo['x']
            by = ufo['y'] + 16
            bid = self.canvas.create_oval(
                bx - 5, by, bx + 5, by + 14,
                fill=UFO_BOMB_COL, outline='#ffcc44', width=1, tags='ufobomb')
            self.ufo_bombs.append({'x': float(bx), 'y': float(by), 'id': bid})
            play_snd(self.sounds, 'ufobomb')

        # Off screen?
        if ufo['x'] < -60 or ufo['x'] > W + 60:
            self.canvas.delete(ufo['id'])
            self.ufo       = None
            self.ufo_timer = random.randint(400, 900)

    def _spawn_ufo(self):
        dx   = random.choice([-1, 1])
        sx   = -50 if dx == 1 else W + 50
        uy   = PANEL_H + 26
        uid  = self.canvas.create_image(sx, uy,
                                         image=self.sprites['ufo'], tags='ufo')
        name = random.choice(_UFO_NAMES)
        self.ufo = {'x': float(sx), 'y': float(uy), 'dx': dx,
                    'id': uid, 'name': name, 'bomb_timer': UFO_BOMB_RATE}

    def _update_ufo_bombs(self):
        """Move UFO bombs downward; check shield and player hits."""
        alive = []
        for b in self.ufo_bombs:
            prev_y = b['y']
            b['y'] += UFO_BOMB_SPD
            if b['y'] > GROUND_Y + 20:
                self.canvas.delete(b['id'])
                continue
            self.canvas.move(b['id'], 0, UFO_BOMB_SPD)

            # Hit player?
            if (self.dead_timer == 0 and
                    abs(b['x'] - self.px) < 22 and
                    abs(b['y'] - PLAYER_Y) < 18):
                self.canvas.delete(b['id'])
                self._player_hit()
                continue

            # Hit shield?
            if self._bullet_hit_shield(b['x'], b['y'], prev_y):
                self.canvas.delete(b['id'])
                continue

            alive.append(b)
        self.ufo_bombs = alive

    # ── Power-up ───────────────────────────────────────────────────────
    def _update_powerup(self):
        if self.powerup is None:
            self.powerup_timer -= 1
            if self.powerup_timer <= 0:
                self._spawn_powerup()
            return

        pu = self.powerup
        pu['y'] += PU_DRIFT
        for iid in pu['ids']:
            self.canvas.move(iid, 0, PU_DRIFT)

        # Blink
        pu['blink'] = (pu['blink'] + 1) % PU_BLINK_RATE
        state = 'normal' if pu['blink'] < PU_BLINK_RATE // 2 else 'hidden'
        for iid in pu['ids']:
            self.canvas.itemconfigure(iid, state=state)

        # Fell off screen
        if pu['y'] > GROUND_Y:
            for iid in pu['ids']:
                self.canvas.delete(iid)
            self.powerup       = None
            self.powerup_timer = random.randint(PU_SPAWN_MIN, PU_SPAWN_MAX)

    def _spawn_powerup(self):
        x = random.randint(80, W - 80)
        y = random.randint(int(GROUND_Y * 0.42), int(GROUND_Y * 0.62))
        ids = []
        # Glow halo
        ids.append(self.canvas.create_rectangle(
            x - 26, y - 14, x + 26, y + 14,
            fill=PU_GLOW, outline=PU_COL, width=2, tags='powerup'))
        # Label
        ids.append(self.canvas.create_text(
            x, y, text="2X", font=("Courier", 16, "bold"),
            fill=PU_COL, tags='powerup'))
        self.powerup = {'x': float(x), 'y': float(y), 'ids': ids, 'blink': 0}

    def _pbullet_hit_powerup(self, b):
        if self.powerup is None:
            return False
        pu = self.powerup
        if abs(b['x'] - pu['x']) < 28 and abs(b['y'] - pu['y']) < 16:
            for iid in pu['ids']:
                self.canvas.delete(iid)
            self.powerup       = None
            self.powerup_timer = random.randint(PU_SPAWN_MIN, PU_SPAWN_MAX)
            self._activate_powerup()
            return True
        return False

    def _activate_powerup(self):
        self.powerup_active = True
        play_snd(self.sounds, 'powerup')
        # Cancel any existing countdown
        if self._pu_reset_id:
            self.root.after_cancel(self._pu_reset_id)
        # Show HUD indicator
        self.canvas.delete('pu_hud')
        self._pu_hud_id = self.canvas.create_text(
            W // 2, GROUND_Y + 18, text=">> 2X RAPID FIRE <<",
            font=("Courier", 13, "bold"), fill=PU_COL, tags='pu_hud')
        self._pu_reset_id = self.root.after(PU_DURATION, self._deactivate_powerup)

    def _deactivate_powerup(self):
        self.powerup_active = False
        self._pu_reset_id   = None
        self.canvas.delete('pu_hud')

    def _reset_ufo_sound(self):
        self._ufo_playing = False
        if self.ufo and self.state == 'playing':
            play_snd(self.sounds, 'ufo')
            self.root.after(1600, self._reset_ufo_sound)

    # ── Game over / win ───────────────────────────────────────────────
    def _game_over(self):
        self.state = 'gameover'
        if self._march_after:
            self.root.after_cancel(self._march_after)
            self._march_after = None
        if self._pu_reset_id:
            self.root.after_cancel(self._pu_reset_id)
            self._pu_reset_id = None
        c = self.canvas
        c.create_rectangle(W//2 - 180, H//2 - 70,
                            W//2 + 180, H//2 + 70,
                            fill="#110022", outline="#ff44aa", width=3)
        c.create_text(W//2, H//2 - 30, text="GAME  OVER",
                      font=("Courier", 32, "bold"), fill="#ff44aa")
        c.create_text(W//2, H//2 + 10, text=f"SCORE  {self.score:05d}",
                      font=("Courier", 18), fill="#ffff00")
        c.create_text(W//2, H//2 + 40, text="PRESS SPACE TO RESTART",
                      font=("Courier", 13), fill="#aaaaaa")

    # ── Debug / utility ───────────────────────────────────────────────
    def _draw_ground(self):
        self.canvas.delete('ground')
        self.canvas.create_line(0, GROUND_Y, W, GROUND_Y,
                                 fill=GND_COL, width=2, tags='ground')
        self._draw_lives()


# ══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════

def main():
    root = tk.Tk()
    app  = SpaceInvaders(root)
    root.mainloop()
    # Clean up tmp sound files
    import shutil
    shutil.rmtree(_TMPDIR, ignore_errors=True)


if __name__ == '__main__':
    main()
