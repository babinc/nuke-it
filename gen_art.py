#!/usr/bin/env python3
"""Generate ANSI true-color art for nuke-it as Rust source constants."""
import sys
import math

def fg(r, g, b):
    return f"\x1b[38;2;{r};{g};{b}m"

def bg_c(r, g, b):
    return f"\x1b[48;2;{r};{g};{b}m"

RST = "\x1b[0m"

def render_art(pixels, indent="    "):
    lines = []
    h = len(pixels)
    w = len(pixels[0]) if h > 0 else 0

    for y in range(0, h, 2):
        top_row = pixels[y]
        bot_row = pixels[y + 1] if y + 1 < h else [None] * w
        # Normalize row lengths
        row_w = max(len(top_row), len(bot_row))
        top_row = top_row + [None] * (row_w - len(top_row))
        bot_row = bot_row + [None] * (row_w - len(bot_row))

        line = ""
        last_fg = None
        last_bg = None

        for x in range(row_w):
            t = top_row[x]
            b = bot_row[x]

            if t is None and b is None:
                if last_fg is not None or last_bg is not None:
                    line += RST
                    last_fg = None
                    last_bg = None
                line += " "
            elif t == b:
                if last_bg is not None:
                    line += "\x1b[49m"
                    last_bg = None
                if t != last_fg:
                    line += fg(*t)
                    last_fg = t
                line += "\u2588"
            elif t is not None and b is None:
                if last_bg is not None:
                    line += "\x1b[49m"
                    last_bg = None
                if t != last_fg:
                    line += fg(*t)
                    last_fg = t
                line += "\u2580"
            elif t is None and b is not None:
                if last_bg is not None:
                    line += "\x1b[49m"
                    last_bg = None
                if b != last_fg:
                    line += fg(*b)
                    last_fg = b
                line += "\u2584"
            else:
                if t != last_fg:
                    line += fg(*t)
                    last_fg = t
                if b != last_bg:
                    line += bg_c(*b)
                    last_bg = b
                line += "\u2580"

        line += RST
        lines.append(indent + line)

    return lines


# ── Color palette (dark/menacing) ────────
_ = None
H  = (160, 135, 35)     # blonde hair (muted)
Hd = (120, 100, 25)     # hair shadow
S  = (165, 120, 80)     # skin (darker)
Sd = (130, 90, 60)      # skin shadow
G  = (8, 8, 12)         # sunglasses lens (near black)
Gf = (40, 42, 55)       # sunglasses frame
Gh = (60, 65, 85)       # sunglasses glint (subtle)
R  = (140, 25, 25)      # red tank top (deep)
Rk = (95, 12, 12)       # red dark
Rh = (170, 45, 45)      # red highlight (muted)
B  = (60, 45, 25)       # belt
Bh = (90, 72, 38)       # belt buckle
P  = (30, 30, 42)       # pants (darker)
Pk = (18, 18, 28)       # pants shadow
Bt = (35, 28, 22)       # boots
Bk = (20, 16, 12)       # boots dark
M  = (70, 70, 78)       # gun metal (darker)
Mh = (105, 105, 115)    # gun highlight
Mf = (200, 160, 40)     # muzzle flash (dimmer)
W  = (200, 200, 200)    # teeth (not blinding white)

# Background mushroom cloud colors (bright enough to read as explosion)
C1 = (150, 90, 18)      # core amber
C2 = (110, 62, 12)      # mid orange
C3 = (70, 42, 12)       # edge dark
C4 = (175, 110, 22)     # bright glow
C5 = (195, 135, 30)     # hot highlight
Cf = (130, 35, 10)      # fire accent

# ── DUKE BODY (40w x 36h) — no cloud, just the character ──
duke_body = [
    # Row 0-1: hair top
    [_, _, _, _, _, _, _, _, _, _, _, H, H, H, H, H, H, H, H, H, H, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, H, H, H, H, H, H, H, H, H, H, H, H, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 2-3: hair
    [_, _, _, _, _, _, _, _, _, _, H, H, H, H, H, H, H, H, H, H, H, H, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, H, H, H, H, H, H, H, H, H, H, H, H, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 4-5: forehead
    [_, _, _, _, _, _, _, _, _, _, _,Hd, S, S, S, S, S, S, S, S,Hd, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _,Hd, S, S, S, S, S, S, S, S,Hd, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 6-7: sunglasses
    [_, _, _, _, _, _, _, _, _, _,Gf,Gf, G, G, G,Gf, S,Gf, G, G, G,Gf, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _,Gf,Gf,Gh, G, G,Gf, S,Gf,Gh, G, G,Gf, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 8-9: nose
    [_, _, _, _, _, _, _, _, _, _, _, S, S, S, S, S, S, S, S, S, S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, S, S, S,Sd, S,Sd, S, S, S, S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 10-11: mouth
    [_, _, _, _, _, _, _, _, _, _, _, S, S, S, S, S, S, S, S, S, S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _,Sd, S, W, W, W, S,Sd, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 12-13: chin
    [_, _, _, _, _, _, _, _, _, _, _, _, _, S, S, S, S, S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _,Sd,Sd,Sd, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 14-15: shoulders
    [_, _, _, _, _, _, _, _, S, S, R, R, R, R, R, R, R, R, R, S, S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, S, S, R, R, R, R, R, R, R, R, R, R, R, S, S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 16-17: upper torso
    [_, _, _, _, _, _, S, S, R, R, R, R,Rk, R, R,Rk, R, R, R, R, S, S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, S, S, R, R, R, R, R, R, R, R, R, R, R, R, R, R, S, S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 18-19: mid torso
    [_, _, _, _, _, S, S, R, R, R,Rk, R, R, R, R, R,Rk, R, R, S, S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, S, R, R, R, R, R, R, R, R, R, R, R, S, S, S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 20: arm extends, holding long gun barrel + big muzzle flash
    [_, _, _, _, _, _, _, R, R, R, R, R, R, R, R, R, R, R, S, _, _, S, M, M, M, M, M, M, M, Mh,Mh,Mf,Mf,Mf,Mf, _, _, _, _, _, _],
    # Row 21: hand grip visible below barrel
    [_, _, _, _, _, _, _, R, R,Rk, R, R, R, R, R, R,Rk, R, _, _, _, S, S, M, M, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 22-23: waist
    [_, _, _, _, _, _, _, _,Rk, R, R, R, R, R, R, R, R,Rk, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, B, B, B, B,Bh,Bh,Bh,Bh, B, B, B, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 24-25: upper pants
    [_, _, _, _, _, _, _, _, P, P, P, P, P, P, P, P, P, P, P, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, P, P, P, P, P, P, P, P, P, P, P, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 26-27: pants split
    [_, _, _, _, _, _, _, _, P, P, P, P, P, _, _, P, P, P, P, P, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, P, P, P, P, _, _, _, _, P, P, P, P, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 28-31: legs
    [_, _, _, _, _, _, _, _, P, P, P,Pk, _, _, _, _, _,Pk, P, P, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, P, P, P,Pk, _, _, _, _, _,Pk, P, P, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, P, P, P, P, _, _, _, _, _, P, P, P, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, P, P, P, P, _, _, _, _, _, P, P, P, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    # Row 32-35: boots
    [_, _, _, _, _, _, _, _,Bt,Bt,Bt,Bt,Bt, _, _, _,Bt,Bt,Bt,Bt,Bt, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _,Bt,Bt,Bt,Bt,Bt, _, _, _,Bt,Bt,Bt,Bt,Bt, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _,Bk,Bk,Bt,Bt,Bt,Bk, _, _, _,Bk,Bt,Bt,Bt,Bk,Bk, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _,Bk,Bk,Bt,Bt,Bt,Bk, _, _, _,Bk,Bt,Bt,Bt,Bk,Bk, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
]

# ── Generate mushroom cloud background ──
def make_cloud(w, h):
    """Procedural mushroom cloud that fills the background behind Duke."""
    grid = [[None] * w for _ in range(h)]
    cx = 31  # cloud center x (right side of frame)

    for y in range(min(h, 22)):
        for x in range(w):
            dx = x - cx
            val = None

            # Mushroom cap (big oval, rows 0-9)
            cap_cy = 4.0
            cap_rx = 8.5
            cap_ry = 5.0
            dc = math.sqrt((dx / cap_rx) ** 2 + ((y - cap_cy) / cap_ry) ** 2)
            if dc < 1.0:
                if dc < 0.2:
                    val = C5
                elif dc < 0.4:
                    val = C4
                elif dc < 0.6:
                    val = C1
                elif dc < 0.8:
                    val = C2
                else:
                    val = C3

            # Fire ring inside cap (donut shape for detail)
            if 0.35 < dc < 0.55 and 1 <= y <= 7:
                val = Cf

            # Stem (rows 8-15, narrow column)
            if 8 <= y <= 15:
                sw = 2.2 + (y - 8) * 0.15
                if abs(dx) < sw:
                    d = abs(dx) / sw
                    if d < 0.3:
                        val = C4
                    elif d < 0.6:
                        val = C1
                    elif val is None:
                        val = C3

            # Base bloom (rows 13-20, spreading wide)
            if 13 <= y <= 21:
                base_cy = 17.0
                base_rx = 9.0
                base_ry = 4.5
                db = math.sqrt((dx / base_rx) ** 2 + ((y - base_cy) / base_ry) ** 2)
                if db < 1.0:
                    if db < 0.2:
                        val = C5
                    elif db < 0.4:
                        val = C4
                    elif db < 0.6:
                        val = C1
                    elif db < 0.8:
                        val = C2
                    elif val is None:
                        val = C3

            grid[y][x] = val
    return grid

cloud = make_cloud(40, 36)

# Composite: Duke's body pixels over cloud background
duke = []
for y in range(len(duke_body)):
    row = []
    bw = len(duke_body[y])
    for x in range(40):
        body_px = duke_body[y][x] if x < bw else None
        cloud_px = cloud[y][x] if y < len(cloud) and x < len(cloud[y]) else None
        row.append(body_px if body_px is not None else cloud_px)
    duke.append(row)


# ── MUSHROOM CLOUD (40w x 30h, ominous) ─
Y  = (190, 140, 30)     # deep amber (was bright yellow)
Yh = (220, 175, 60)     # hot center (was white-yellow)
O  = (180, 95, 15)      # burnt orange
Od = (145, 70, 10)      # dark orange
F  = (160, 35, 12)      # fire red
Fk = (110, 18, 8)       # dark fire
Sm = (55, 48, 44)       # smoke (darker)
Sl = (78, 70, 65)       # smoke light
Sk = (35, 30, 28)       # smoke dark
Gr = (25, 25, 22)       # ground (near black)

nuke = [
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, Sm,Sm,Sl,Sl,Sl,Sl,Sl,Sm,Sm, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, Sm,Sm,Sl,Sl, O, O, Y, Y, Y, O, O,Sl,Sl,Sm, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, Sm,Sl, O, O, Y, Y,Yh,Yh,Yh,Yh,Yh,Yh, Y, Y, O, O,Sl,Sm, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, Sm,Sl, O, Y,Yh,Yh,Yh,Yh,Yh,Yh,Yh,Yh,Yh,Yh,Yh, Y, O,Sl,Sm, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, Sm, O, O, Y,Yh,Yh, Y, Y,Yh,Yh,Yh,Yh,Yh, Y, Y,Yh,Yh, Y, O, O,Sm, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, Sm, O, O, Y, Y, Y, O, O, Y, Y,Yh,Yh,Yh, Y, Y, O, O, Y, Y, Y, O, O,Sm, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, Sm, O, O, Y, Y, O, O,Od, O, O, Y, Y, Y, Y, Y, O, O,Od, O, O, Y, Y, O, O,Sm, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, Sm,Sl, O, Y, Y, O,Od, F, F,Od, O, O, Y, Y, Y, O, O,Od, F, F,Od, O, Y, Y, O,Sl,Sm, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, Sm, O, O, Y, O,Od, F,Fk,Fk, F,Od, O, O, Y, O, O,Od, F,Fk,Fk, F,Od, O, Y, O, O,Sm, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, Sm, O, O, O,Od, F,Fk,Fk,Fk, F, F,Od, O, O, O,Od, F, F,Fk,Fk,Fk, F,Od, O, O, O,Sm, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, Sm, O, O,Od, F,Fk,Sk,Fk, F,Od, O, O, O, O, O,Od, F,Fk,Sk,Fk, F,Od, O, O,Sm, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _,Sm,Sl, O,Od, F, F, F,Od, O, O, O, O, O, O, O,Od, F, F, F,Od, O,Sl,Sm, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, Sm,Sm,Sl, O,Od,Od, O, O, O,Sl,Sl,Sl, O, O, O,Od,Od, O,Sl,Sm,Sm, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, Sm,Sm,Sl,Sl, O, O,Sl,Sm,Sm,Sm,Sl, O, O,Sl,Sl,Sm,Sm, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, Sm,Sm,Sm,Sl,Sm,Sk,Sk,Sk,Sm,Sl,Sm,Sm,Sm, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, Sm,Sm,Sk,Sk,Sk,Sk,Sk,Sm,Sm, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, Sm,Sl, O, O, Y, O, O,Sl,Sm, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, Sm,Sl, O, Y, Y, Y, O,Sl,Sm, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, Sm, O, O, Y,Yh, Y, O, O,Sm, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, Sm,Sl, O, O, Y, Y, Y, O, O,Sl,Sm, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, Sm,Sl, O, O, Y, Y,Yh, Y, Y, O, O,Sl,Sm, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, Sm,Sl, O, O, Y, Y,Yh,Yh,Yh, Y, Y, O, O,Sl,Sm, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, Sm,Sl, O, O, Y, Y,Yh,Yh,Yh,Yh,Yh, Y, Y, O, O,Sl,Sm, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, Sm, O, O, O, Y, Y, Y, Y,Yh,Yh,Yh, Y, Y, Y, Y, O, O, O,Sm, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _,Sm,Sl, O, O, Y, Y,Yh, Y, Y, Y, Y, Y, Y, Y,Yh, Y, Y, O, O,Sl,Sm, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _,Sm,Sl, O, O, Y, Y,Yh,Yh,Yh, Y, Y, Y, Y, Y,Yh,Yh,Yh, Y, Y, O, O,Sl,Sm, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, Sm,Sm,Sl, O, O, Y, Y,Yh,Yh, Y, O, O, Y, Y, Y, O, O, Y,Yh,Yh, Y, Y, O, O,Sl,Sm,Sm, _, _, _, _, _, _, _],
    [_, _, _, _,Sm,Sl, O, O, O, Y, Y,Yh,Yh, Y, O,Od, F, O, Y, O, F,Od, O, Y,Yh,Yh, Y, Y, O, O, O,Sl,Sm, _, _, _, _, _, _],
    [Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr],
    [Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr,Gr],
]

# ── Generate output ──────────────────────
duke_lines = render_art(duke, "        ")
nuke_lines = render_art(nuke, "    ")

# Title text for right side of duke banner
# Use bright amber — high contrast, clean pixel font on a 5x7 grid per char
T = (220, 160, 40)    # bright amber
Td = (170, 115, 20)   # darker amber shadow
RS = RST

# Define each letter as a 5-wide x 7-tall bitmap (1 = filled, 0 = empty)
FONT = {
    'N': [
        [1,0,0,0,1],
        [1,1,0,0,1],
        [1,1,1,0,1],
        [1,0,1,1,1],
        [1,0,0,1,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
    ],
    'U': [
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
        [0,1,1,1,0],
    ],
    'K': [
        [1,0,0,1,0],
        [1,0,1,1,0],
        [1,1,1,0,0],
        [1,1,0,0,0],
        [1,1,1,0,0],
        [1,0,1,1,0],
        [1,0,0,1,0],
    ],
    'E': [
        [1,1,1,1,1],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,1,1,1,1],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,1,1,1,1],
    ],
    '-': [
        [0,0,0],
        [0,0,0],
        [0,0,0],
        [1,1,1],
        [0,0,0],
        [0,0,0],
        [0,0,0],
    ],
    'I': [
        [1,1,1],
        [0,1,0],
        [0,1,0],
        [0,1,0],
        [0,1,0],
        [0,1,0],
        [1,1,1],
    ],
    'T': [
        [1,1,1,1,1],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
    ],
}

def render_title(text, color, shadow):
    """Render text using the pixel font, returning lines with half-blocks."""
    # Build combined bitmap rows
    rows = [[] for _ in range(7)]
    for ci, ch in enumerate(text):
        glyph = FONT[ch]
        if ci > 0:
            for r in range(7):
                rows[r].append(0)  # 2-col gap between letters
                rows[r].append(0)
        for r in range(7):
            rows[r].extend(glyph[r])

    # Pad to even row count
    if len(rows) % 2 == 1:
        rows.append([0] * len(rows[0]))

    # Set colors once at the start, use spaces for gaps
    c = fg(*color)
    s = fg(*shadow)

    lines = []
    for y in range(0, len(rows), 2):
        top = rows[y]
        bot = rows[y + 1] if y + 1 < len(rows) else [0] * len(top)

        # Build segments: group consecutive same-type cells to minimize escapes
        line = "  "
        last_type = None  # track what color state we're in
        for x in range(len(top)):
            t = top[x]
            b = bot[x]
            if t and b:
                if last_type != "full":
                    line += c
                    last_type = "full"
                line += "\u2588"
            elif t and not b:
                if last_type != "top":
                    line += c
                    last_type = "top"
                line += "\u2580"
            elif not t and b:
                if last_type != "bot":
                    line += s
                    last_type = "bot"
                line += "\u2584"
            else:
                if last_type != "space":
                    line += RST
                    last_type = "space"
                line += " "
        line += RST
        lines.append(line)
    return lines

title_lines = render_title("NUKE-IT", T, Td)

# Write art.rs
with open("src/art.rs", "w", encoding="utf-8") as f:
    f.write("// Auto-generated ANSI true-color pixel art. Do not edit by hand.\n\n")

    # DUKE_BANNER: duke + title on right
    f.write("pub const DUKE_BANNER: &str = \"\\\n")
    for i, line in enumerate(duke_lines):
        right = ""
        # Place title next to duke's torso area (rows 4-10)
        ti = i - 4
        if 0 <= ti < len(title_lines):
            right = title_lines[ti]
        f.write(f"\\n{line}{right}\\\n")
    f.write("\\n\";\n\n")

    # DUKE_ART: just duke (used for shred/done/abort/wipe prompts)
    f.write("pub const DUKE_ART: &str = \"\\\n")
    for line in duke_lines:
        f.write(f"\\n{line}\\\n")
    f.write("\\n\";\n\n")

    # NUKE_ART: mushroom cloud (shown after nuking)
    f.write("pub const NUKE_ART: &str = \"\\\n")
    for line in nuke_lines:
        f.write(f"\\n{line}\\\n")
    f.write("\\n\";\n\n")

print("Generated src/art.rs successfully.", file=sys.stderr)
