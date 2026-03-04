#!/usr/bin/env python3
"""
Pong Clone — Single Player
Controls: ↑ ↓ arrow keys | SPACE to pause | R to restart | ESC to quit
First to 7 points wins.
"""

import ctypes
import random
import math
import struct
import sys

# ─── SDL2 via ctypes ──────────────────────────────────────────────────────────

try:
    _sdl = ctypes.CDLL("libSDL2-2.0.so.0")
except OSError:
    sys.exit("SDL2 runtime not found. Install libsdl2: sudo apt install libsdl2-2.0-0")

SDL_INIT_VIDEO         = 0x00000020
SDL_INIT_AUDIO         = 0x00000010
SDL_WINDOWPOS_CENTERED = 0x2FFF0000
SDL_WINDOW_SHOWN       = 0x00000004
SDL_RENDERER_ACCELERATED  = 0x00000002
SDL_RENDERER_PRESENTVSYNC = 0x00000004
SDL_QUIT    = 0x100
SDL_KEYDOWN = 0x300
SDL_KEYUP   = 0x301

SDLK_ESCAPE = 27
SDLK_SPACE  = 32
SDLK_RETURN = 13
SDLK_UP     = 0x40000052
SDLK_DOWN   = 0x40000051
SDLK_r      = ord('r')
SDLK_R      = ord('R')


class SDL_Rect(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int),
                ("w", ctypes.c_int), ("h", ctypes.c_int)]


class SDL_Keysym(ctypes.Structure):
    _fields_ = [("scancode", ctypes.c_uint32), ("sym", ctypes.c_int32),
                ("mod", ctypes.c_uint16), ("unused", ctypes.c_uint32)]


class SDL_KeyboardEvent(ctypes.Structure):
    _fields_ = [("type", ctypes.c_uint32), ("timestamp", ctypes.c_uint32),
                ("windowID", ctypes.c_uint32), ("state", ctypes.c_uint8),
                ("repeat", ctypes.c_uint8), ("pad2", ctypes.c_uint8),
                ("pad3", ctypes.c_uint8), ("keysym", SDL_Keysym)]


class SDL_Event(ctypes.Union):
    _fields_ = [("type", ctypes.c_uint32),
                ("key",  SDL_KeyboardEvent),
                ("_pad", ctypes.c_uint8 * 56)]


# Function signatures
def _fn(name, restype, *argtypes):
    f = getattr(_sdl, name)
    f.restype  = restype
    f.argtypes = list(argtypes)
    return f


SDL_Init            = _fn("SDL_Init",            ctypes.c_int,    ctypes.c_uint32)
SDL_CreateWindow    = _fn("SDL_CreateWindow",    ctypes.c_void_p, ctypes.c_char_p,
                          ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                          ctypes.c_uint32)
SDL_CreateRenderer  = _fn("SDL_CreateRenderer",  ctypes.c_void_p, ctypes.c_void_p,
                          ctypes.c_int, ctypes.c_uint32)
SDL_DestroyRenderer = _fn("SDL_DestroyRenderer", None,            ctypes.c_void_p)
SDL_DestroyWindow   = _fn("SDL_DestroyWindow",   None,            ctypes.c_void_p)
SDL_Quit            = _fn("SDL_Quit",            None)
SDL_SetRenderDrawColor = _fn("SDL_SetRenderDrawColor", ctypes.c_int,
                             ctypes.c_void_p, ctypes.c_uint8, ctypes.c_uint8,
                             ctypes.c_uint8, ctypes.c_uint8)
SDL_RenderClear     = _fn("SDL_RenderClear",     ctypes.c_int,    ctypes.c_void_p)
SDL_RenderFillRect  = _fn("SDL_RenderFillRect",  ctypes.c_int,    ctypes.c_void_p,
                          ctypes.POINTER(SDL_Rect))
SDL_RenderPresent   = _fn("SDL_RenderPresent",   None,            ctypes.c_void_p)
SDL_PollEvent       = _fn("SDL_PollEvent",       ctypes.c_int,    ctypes.POINTER(SDL_Event))
SDL_GetTicks        = _fn("SDL_GetTicks",        ctypes.c_uint32)
SDL_Delay           = _fn("SDL_Delay",           None,            ctypes.c_uint32)

# ─── SDL2 audio ───────────────────────────────────────────────────────────────

AUDIO_S16LSB = 0x8010   # signed 16-bit little-endian PCM


class SDL_AudioSpec(ctypes.Structure):
    """32-byte struct on 64-bit Linux."""
    _fields_ = [
        ("freq",     ctypes.c_int),
        ("format",   ctypes.c_uint16),
        ("channels", ctypes.c_uint8),
        ("silence",  ctypes.c_uint8),
        ("samples",  ctypes.c_uint16),
        ("padding",  ctypes.c_uint16),
        ("size",     ctypes.c_uint32),
        ("callback", ctypes.c_void_p),   # NULL → use SDL_QueueAudio
        ("userdata", ctypes.c_void_p),
    ]


SDL_OpenAudioDevice  = _fn("SDL_OpenAudioDevice",  ctypes.c_uint32,
                            ctypes.c_char_p, ctypes.c_int,
                            ctypes.POINTER(SDL_AudioSpec),
                            ctypes.POINTER(SDL_AudioSpec),
                            ctypes.c_int)
SDL_PauseAudioDevice = _fn("SDL_PauseAudioDevice", None,
                            ctypes.c_uint32, ctypes.c_int)
SDL_QueueAudio       = _fn("SDL_QueueAudio",       ctypes.c_int,
                            ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32)
SDL_ClearQueuedAudio = _fn("SDL_ClearQueuedAudio", ctypes.c_int,
                            ctypes.c_uint32)
SDL_CloseAudioDevice = _fn("SDL_CloseAudioDevice", None, ctypes.c_uint32)

# ─── Sound engine ─────────────────────────────────────────────────────────────

_SR = 44100   # sample rate


def _sine(freq, ms, amp=8000, fade=True):
    """Sine-wave tone, optionally fading out."""
    n = int(_SR * ms / 1000)
    data = bytearray(n * 2)
    for i in range(n):
        env = (1.0 - i / n) if fade else 1.0
        val = int(amp * env * math.sin(2 * math.pi * freq * i / _SR))
        struct.pack_into("<h", data, i * 2, max(-32767, min(32767, val)))
    return bytes(data)


def _sweep(f0, f1, ms, amp=7000):
    """Linear frequency sweep with exponential decay."""
    n = int(_SR * ms / 1000)
    data = bytearray(n * 2)
    phase = 0.0
    for i in range(n):
        t = i / n
        freq = f0 + (f1 - f0) * t
        env = math.exp(-3.5 * t)
        val = int(amp * env * math.sin(phase))
        struct.pack_into("<h", data, i * 2, max(-32767, min(32767, val)))
        phase += 2 * math.pi * freq / _SR
    return bytes(data)


def _silence(ms):
    return bytes(int(_SR * ms / 1000) * 2)


def _arpeggio(freqs, note_ms, gap_ms=18):
    return b"".join(_sine(f, note_ms) + _silence(gap_ms) for f in freqs)


class SoundEngine:
    """
    Pre-generates all game sounds as raw S16LE PCM and plays them
    through SDL2's audio queue (non-blocking, mixes automatically).
    Fails silently if the audio device cannot be opened.
    """

    _SOUNDS = {
        # Short punchy click on paddle contact
        "paddle_hit":   lambda: _sine(660, 40, amp=7000),
        # Ascending ding when YOU score (ball exits AI side)
        "score_player": lambda: _sweep(700, 1300, 200, amp=7500),
        # Descending boop when AI scores (ball exits your side)
        "score_ai":     lambda: _sweep(420, 190, 260, amp=7000),
        # Three rising notes on ENTER / game start
        "game_start":   lambda: _arpeggio([523, 659, 784], 85),
        # Triumphant ascending fanfare on WIN
        "win":          lambda: _arpeggio([523, 659, 784, 1047, 1319], 110, gap_ms=22),
        # Sad descending tones on LOSE
        "lose":         lambda: _arpeggio([392, 330, 262, 220], 130, gap_ms=25),
    }

    def __init__(self):
        self._dev = 0
        spec = SDL_AudioSpec()
        spec.freq     = _SR
        spec.format   = AUDIO_S16LSB
        spec.channels = 1
        spec.samples  = 1024
        spec.callback = None
        spec.userdata = None
        obtained = SDL_AudioSpec()
        dev = SDL_OpenAudioDevice(None, 0,
                                  ctypes.byref(spec),
                                  ctypes.byref(obtained), 0)
        if dev == 0:
            return   # no audio — game still works
        self._dev = dev
        SDL_PauseAudioDevice(dev, 0)   # 0 = start playing
        # Pre-generate all PCM buffers
        self._pcm = {name: fn() for name, fn in self._SOUNDS.items()}

    def play(self, name, clear_first=False):
        if not self._dev:
            return
        pcm = self._pcm.get(name)
        if pcm is None:
            return
        if clear_first:
            SDL_ClearQueuedAudio(self._dev)
        SDL_QueueAudio(self._dev, pcm, len(pcm))

    def close(self):
        if self._dev:
            SDL_CloseAudioDevice(self._dev)
            self._dev = 0

# ─── Drawing helpers ──────────────────────────────────────────────────────────

def set_color(r, color):
    SDL_SetRenderDrawColor(r, color[0], color[1], color[2], 255)


def fill_rect(r, x, y, w, h):
    rect = SDL_Rect(int(x), int(y), int(w), int(h))
    SDL_RenderFillRect(r, ctypes.byref(rect))


def draw_rect_outline(r, x, y, w, h, t=2):
    fill_rect(r, x,     y,     w, t)
    fill_rect(r, x,     y+h-t, w, t)
    fill_rect(r, x,     y,     t, h)
    fill_rect(r, x+w-t, y,     t, h)


# ─── 5×7 bitmap font ──────────────────────────────────────────────────────────
# Each char: 7 rows, each row is a 5-bit mask (bit4=left, bit0=right)

FONT = {
    ' ': [0b00000]*7,
    'A': [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    'B': [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110],
    'C': [0b01111, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b01111],
    'D': [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
    'E': [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
    'F': [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000],
    'G': [0b01111, 0b10000, 0b10000, 0b10111, 0b10001, 0b10001, 0b01110],
    'H': [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    'I': [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b11111],
    'J': [0b11111, 0b00001, 0b00001, 0b00001, 0b00001, 0b10001, 0b01110],
    'K': [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001],
    'L': [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
    'M': [0b10001, 0b11011, 0b10101, 0b10001, 0b10001, 0b10001, 0b10001],
    'N': [0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001],
    'O': [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    'P': [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
    'Q': [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101],
    'R': [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
    'S': [0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110],
    'T': [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
    'U': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    'V': [0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b01010, 0b00100],
    'W': [0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001],
    'X': [0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b01010, 0b10001],
    'Y': [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100],
    'Z': [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111],
    '0': [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
    '1': [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    '2': [0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111],
    '3': [0b11111, 0b00001, 0b00010, 0b00110, 0b00001, 0b10001, 0b01110],
    '4': [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
    '5': [0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110],
    '6': [0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
    '7': [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
    '8': [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
    '9': [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100],
    '!': [0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00000, 0b00100],
    '-': [0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000],
    ':': [0b00000, 0b00100, 0b00000, 0b00000, 0b00000, 0b00100, 0b00000],
    '|': [0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
    '.': [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00100],
    '/': [0b00001, 0b00010, 0b00100, 0b00100, 0b01000, 0b10000, 0b00000],
    '>': [0b10000, 0b01000, 0b00100, 0b00010, 0b00100, 0b01000, 0b10000],
    '<': [0b00001, 0b00010, 0b00100, 0b01000, 0b00100, 0b00010, 0b00001],
}


def draw_char(r, ch, x, y, scale=2):
    rows = FONT.get(ch.upper(), FONT.get(ch, FONT[' ']))
    for ri, row in enumerate(rows):
        for ci in range(5):
            if row & (1 << (4 - ci)):
                fill_rect(r, x + ci * scale, y + ri * scale, scale, scale)


def text_width(text, scale=2):
    return len(text) * (5 + 1) * scale


def draw_text(r, text, x, y, scale=2):
    cx = x
    for ch in text:
        draw_char(r, ch, cx, y, scale)
        cx += (5 + 1) * scale


def draw_text_centered(r, text, cy_x, y, scale=2):
    """cy_x is the horizontal center."""
    x = cy_x - text_width(text, scale) // 2
    draw_text(r, text, x, y, scale)


# ─── Colors ───────────────────────────────────────────────────────────────────

BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GRAY_DIM   = (55,  55,  55)
GRAY_MID   = (110, 110, 110)
CYAN       = (80,  220, 255)
GREEN      = (80,  255, 140)
RED        = (255, 80,  80)
YELLOW     = (255, 220, 60)
DARK_PANEL = (18,  18,  28)

# ─── Game constants ───────────────────────────────────────────────────────────

W, H       = 900, 600
PADDLE_W   = 14
PADDLE_H   = 100
BALL_SZ    = 14
P_MARGIN   = 34        # paddle distance from edge
P_SPEED    = 7.5       # player paddle speed px/frame
AI_SPEED   = 5.2       # AI base speed (≈ 69% of player)
BALL_INIT  = 5.5       # initial ball speed px/frame
BALL_MAX   = 13.0      # max ball speed
BALL_ACC   = 0.35      # speed gain per paddle hit
WIN_SCORE  = 7
TARGET_FPS = 60
FRAME_MS   = 1000 // TARGET_FPS

# ─── Entities ─────────────────────────────────────────────────────────────────

class Paddle:
    def __init__(self, x):
        self.x = float(x)
        self.y = float(H // 2 - PADDLE_H // 2)

    def cy(self):
        return self.y + PADDLE_H / 2

    def clamp(self):
        self.y = max(0.0, min(float(H - PADDLE_H), self.y))


class Ball:
    def __init__(self):
        self.x = float(W // 2 - BALL_SZ // 2)
        self.y = float(H // 2 - BALL_SZ // 2)
        self.vx = 0.0
        self.vy = 0.0

    def cx(self): return self.x + BALL_SZ / 2
    def cy(self): return self.y + BALL_SZ / 2
    def speed(self): return math.sqrt(self.vx ** 2 + self.vy ** 2)

    def launch(self, direction=0):
        if direction == 0:
            direction = random.choice([-1, 1])
        angle = random.uniform(-math.pi / 5, math.pi / 5)
        self.vx = math.cos(angle) * BALL_INIT * direction
        self.vy = math.sin(angle) * BALL_INIT
        self.x = float(W // 2 - BALL_SZ // 2)
        self.y = float(H // 2 - BALL_SZ // 2)

# ─── AI brain ─────────────────────────────────────────────────────────────────

class AI:
    """
    Imperfect AI that tracks the ball with occasional mistakes.
    Mistakes happen ~25% of the time and last 0.3–1.1 seconds.
    """

    def __init__(self):
        self.mistake        = False
        self.mistake_frames = 0
        self.mistake_dir    = 0      # -1, 0 (freeze), +1
        self.next_check     = random.randint(100, 220)

    def update(self, paddle, ball):
        self.next_check -= 1
        if self.next_check <= 0:
            # Re-evaluate every 1.7–3.7 s
            self.next_check = random.randint(100, 220)
            if random.random() < 0.25:
                self.mistake        = True
                self.mistake_frames = random.randint(18, 65)
                # 50% wrong dir, 50% freeze
                self.mistake_dir    = random.choice([-1, 0, 0, 1])
            else:
                self.mistake = False

        speed = AI_SPEED

        if self.mistake and self.mistake_frames > 0:
            self.mistake_frames -= 1
            if self.mistake_frames == 0:
                self.mistake = False
            if self.mistake_dir == 0:
                return                          # freeze
            paddle.y += self.mistake_dir * speed * 0.55
            paddle.clamp()
            return

        # Normal: track ball y with a small dead-zone
        # When ball moves away, drift gently toward center
        if ball.vx > 0:
            target = H / 2
            speed *= 0.25
        else:
            target = ball.cy()

        diff = target - paddle.cy()
        if abs(diff) < 3:
            return

        move = min(speed, abs(diff) * 0.14)
        paddle.y += move * (1 if diff > 0 else -1)
        paddle.clamp()

# ─── Main game ────────────────────────────────────────────────────────────────

class PongGame:
    START  = "start"
    PLAY   = "play"
    PAUSE  = "pause"
    WIN    = "win"
    LOSE   = "lose"

    def __init__(self, renderer, snd):
        self.r   = renderer
        self.snd = snd
        self.state = self.START

        # Input
        self.up_held   = False
        self.down_held = False

        self._new_game()

    def _new_game(self):
        self.player  = Paddle(W - P_MARGIN - PADDLE_W)
        self.ai_pad  = Paddle(P_MARGIN)
        self.ball    = Ball()
        self.ai      = AI()
        self.pscore  = 0
        self.ascore  = 0
        self._serve(delay=True)

    def _serve(self, direction=0, delay=False):
        self.ball_live    = False
        self.serve_dir    = direction
        self.serve_delay  = 90 if delay else 70  # frames

    # ── Input ──────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        """Return False to quit."""
        t = event.type
        if t == SDL_QUIT:
            return False
        if t == SDL_KEYDOWN:
            sym = event.key.keysym.sym
            if sym == SDLK_ESCAPE:
                return False
            if sym == SDLK_UP:
                self.up_held   = True
            if sym == SDLK_DOWN:
                self.down_held = True

            if self.state == self.START:
                if sym in (SDLK_RETURN, SDLK_SPACE):
                    self.state = self.PLAY
                    self.snd.play("game_start", clear_first=True)

            elif self.state == self.PLAY:
                if sym == SDLK_SPACE:
                    self.state = self.PAUSE
                if sym in (SDLK_r, SDLK_R):
                    self._new_game()
                    self.state = self.PLAY
                    self.snd.play("game_start", clear_first=True)

            elif self.state == self.PAUSE:
                if sym == SDLK_SPACE:
                    self.state = self.PLAY
                if sym in (SDLK_r, SDLK_R):
                    self._new_game()
                    self.state = self.PLAY
                    self.snd.play("game_start", clear_first=True)

            elif self.state in (self.WIN, self.LOSE):
                if sym in (SDLK_r, SDLK_R, SDLK_RETURN, SDLK_SPACE):
                    self._new_game()
                    self.state = self.PLAY
                    self.snd.play("game_start", clear_first=True)

        elif t == SDL_KEYUP:
            sym = event.key.keysym.sym
            if sym == SDLK_UP:
                self.up_held   = False
            if sym == SDLK_DOWN:
                self.down_held = False

        return True

    # ── Update ─────────────────────────────────────────────────────────────────

    def update(self):
        if self.state != self.PLAY:
            return

        # Serve countdown
        if not self.ball_live:
            self.serve_delay -= 1
            if self.serve_delay <= 0:
                self.ball.launch(self.serve_dir)
                self.ball_live = True
            return

        # Player paddle
        if self.up_held:
            self.player.y -= P_SPEED
        if self.down_held:
            self.player.y += P_SPEED
        self.player.clamp()

        # AI paddle
        self.ai.update(self.ai_pad, self.ball)

        # Ball physics
        b = self.ball
        b.x += b.vx
        b.y += b.vy

        # Top / bottom walls
        if b.y <= 0:
            b.y  = 0
            b.vy = abs(b.vy)
        if b.y + BALL_SZ >= H:
            b.y  = float(H - BALL_SZ)
            b.vy = -abs(b.vy)

        # Player paddle collision (ball moving right)
        p = self.player
        if (b.vx > 0
                and b.x + BALL_SZ >= p.x
                and b.x <= p.x + PADDLE_W
                and b.y + BALL_SZ >= p.y
                and b.y <= p.y + PADDLE_H):
            hit   = (b.cy() - p.cy()) / (PADDLE_H / 2)
            hit   = max(-1.0, min(1.0, hit))
            angle = hit * math.pi / 3.2
            spd   = min(b.speed() + BALL_ACC, BALL_MAX)
            b.vx  = -abs(math.cos(angle) * spd)
            b.vy  = math.sin(angle) * spd
            b.x   = p.x - BALL_SZ - 1
            self.snd.play("paddle_hit")

        # AI paddle collision (ball moving left)
        a = self.ai_pad
        if (b.vx < 0
                and b.x <= a.x + PADDLE_W
                and b.x + BALL_SZ >= a.x
                and b.y + BALL_SZ >= a.y
                and b.y <= a.y + PADDLE_H):
            hit   = (b.cy() - a.cy()) / (PADDLE_H / 2)
            hit   = max(-1.0, min(1.0, hit))
            angle = hit * math.pi / 3.2
            spd   = min(b.speed() + BALL_ACC, BALL_MAX)
            b.vx  = abs(math.cos(angle) * spd)
            b.vy  = math.sin(angle) * spd
            b.x   = a.x + PADDLE_W + 1
            self.snd.play("paddle_hit")

        # Scoring
        if b.x + BALL_SZ < 0:
            self.pscore += 1
            if self.pscore >= WIN_SCORE:
                self.state = self.WIN
                self.ball_live = False
                self.snd.play("win", clear_first=True)
            else:
                self._serve(direction=1)   # toward player next
                self.snd.play("score_player")
        elif b.x > W:
            self.ascore += 1
            if self.ascore >= WIN_SCORE:
                self.state = self.LOSE
                self.ball_live = False
                self.snd.play("lose", clear_first=True)
            else:
                self._serve(direction=-1)  # toward AI next
                self.snd.play("score_ai")

    # ── Draw ───────────────────────────────────────────────────────────────────

    def draw(self):
        r = self.r

        # Background
        set_color(r, BLACK)
        SDL_RenderClear(r)

        # Center dashes
        set_color(r, GRAY_DIM)
        dash_h, gap = 18, 14
        for y in range(0, H, dash_h + gap):
            fill_rect(r, W // 2 - 2, y, 4, dash_h)

        # Score area divider (thin line)
        set_color(r, GRAY_MID)
        fill_rect(r, 0, 64, W, 1)

        # Scores (large)
        set_color(r, WHITE)
        draw_text_centered(r, str(self.ascore),  W // 4,     14, scale=5)
        draw_text_centered(r, str(self.pscore),  3 * W // 4, 14, scale=5)

        # "AI" / "YOU" labels (small, above scores)
        set_color(r, GRAY_MID)
        draw_text_centered(r, "AI",  W // 4,     6, scale=1)
        draw_text_centered(r, "YOU", 3 * W // 4, 6, scale=1)

        # Paddles
        set_color(r, WHITE)
        fill_rect(r, self.ai_pad.x, self.ai_pad.y, PADDLE_W, PADDLE_H)
        fill_rect(r, self.player.x, self.player.y, PADDLE_W, PADDLE_H)

        # Ball
        if self.ball_live:
            set_color(r, CYAN)
            fill_rect(r, self.ball.x, self.ball.y, BALL_SZ, BALL_SZ)
        elif self.state == self.PLAY:
            # Blinking dot at center while waiting to serve
            if (self.serve_delay // 10) % 2 == 0:
                set_color(r, GRAY_MID)
                fill_rect(r, W // 2 - BALL_SZ // 2, H // 2 - BALL_SZ // 2,
                          BALL_SZ, BALL_SZ)

        # Overlays
        self._draw_overlay()

        SDL_RenderPresent(r)

    def _draw_overlay(self):
        r = self.r
        if self.state == self.START:
            self._panel(H // 2 - 80, 180)
            set_color(r, CYAN)
            draw_text_centered(r, "PONG", W // 2, H // 2 - 68, scale=5)
            set_color(r, WHITE)
            draw_text_centered(r, "PRESS ENTER OR SPACE TO START", W // 2, H // 2 + 18, scale=2)
            set_color(r, GRAY_MID)
            draw_text_centered(r, "UP/DOWN ARROWS  SPACE PAUSE  R RESTART  ESC QUIT",
                               W // 2, H // 2 + 48, scale=1)
            draw_text_centered(r, "FIRST TO 7 POINTS WINS",
                               W // 2, H // 2 + 62, scale=1)

        elif self.state == self.PAUSE:
            self._panel(H // 2 - 50, 110)
            set_color(r, YELLOW)
            draw_text_centered(r, "PAUSED", W // 2, H // 2 - 38, scale=4)
            set_color(r, WHITE)
            draw_text_centered(r, "SPACE TO CONTINUE", W // 2, H // 2 + 18, scale=2)
            set_color(r, GRAY_MID)
            draw_text_centered(r, "R RESTART   ESC QUIT", W // 2, H // 2 + 40, scale=1)

        elif self.state == self.WIN:
            self._panel(H // 2 - 60, 130)
            set_color(r, GREEN)
            draw_text_centered(r, "YOU WIN!", W // 2, H // 2 - 50, scale=4)
            set_color(r, WHITE)
            draw_text_centered(r, f"{self.pscore} - {self.ascore}", W // 2, H // 2 + 8, scale=3)
            set_color(r, GRAY_MID)
            draw_text_centered(r, "R TO PLAY AGAIN   ESC QUIT", W // 2, H // 2 + 46, scale=1)

        elif self.state == self.LOSE:
            self._panel(H // 2 - 60, 130)
            set_color(r, RED)
            draw_text_centered(r, "GAME OVER", W // 2, H // 2 - 50, scale=4)
            set_color(r, WHITE)
            draw_text_centered(r, f"{self.pscore} - {self.ascore}", W // 2, H // 2 + 8, scale=3)
            set_color(r, GRAY_MID)
            draw_text_centered(r, "R TO PLAY AGAIN   ESC QUIT", W // 2, H // 2 + 46, scale=1)

    def _panel(self, y, h, margin=160):
        """Draw a semi-transparent dark panel for overlay text."""
        r = self.r
        set_color(r, DARK_PANEL)
        fill_rect(r, margin, y, W - margin * 2, h)
        set_color(r, GRAY_MID)
        draw_rect_outline(r, margin, y, W - margin * 2, h, t=2)

# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    if SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO) < 0:
        sys.exit("SDL_Init failed")

    window = SDL_CreateWindow(
        b"Pong Clone",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        W, H,
        SDL_WINDOW_SHOWN,
    )
    if not window:
        sys.exit("Could not create window")

    renderer = SDL_CreateRenderer(
        window, -1,
        SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC,
    )
    if not renderer:
        SDL_DestroyWindow(window)
        sys.exit("Could not create renderer")

    snd   = SoundEngine()
    game  = PongGame(renderer, snd)
    event = SDL_Event()
    running = True

    while running:
        frame_start = SDL_GetTicks()

        # Events
        while SDL_PollEvent(ctypes.byref(event)):
            if not game.handle_event(event):
                running = False
                break

        game.update()
        game.draw()

        # Cap frame rate (vsync should handle it, this is a fallback)
        elapsed = SDL_GetTicks() - frame_start
        if elapsed < FRAME_MS:
            SDL_Delay(FRAME_MS - elapsed)

    snd.close()
    SDL_DestroyRenderer(renderer)
    SDL_DestroyWindow(window)
    SDL_Quit()


if __name__ == "__main__":
    main()
