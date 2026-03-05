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

# Side mushroom cloud colors (bright, unmistakable explosion)
C1 = (185, 115, 20)     # core amber
C2 = (145, 80, 12)      # mid orange
C3 = (95, 55, 10)       # edge
C4 = (210, 145, 30)     # bright glow
C5 = (230, 170, 45)     # hot highlight
Cf = (165, 40, 10)      # fire accent
Cs = (60, 50, 42)       # smoke edge

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
    # Row 20: arm extends out to gun — thin arm (2px), then barrel + flash
    [_, _, _, _, _, _, _, R, R, R, R, R, R, R, R, R, R, R, R, S, S, M, M, M, M, M, M, M, M, Mh,Mh,Mf,Mf,Mf,Mf, _, _, _, _, _, _],
    # Row 21: hand gripping below barrel
    [_, _, _, _, _, _, _, R, R,Rk, R, R, R, R, R, R,Rk, R, _, _, S, M, M, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
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

# ── Generate standalone mushroom cloud for banner ──
def make_side_cloud(w, h):
    """Standalone mushroom cloud to sit beside Duke in the banner."""
    grid = [[None] * w for _ in range(h)]
    cx = w / 2.0

    def hot(d):
        """Bright center gradient."""
        if d < 0.15: return C5
        if d < 0.35: return C4
        if d < 0.55: return C1
        if d < 0.75: return C2
        if d < 0.9: return C3
        return Cs

    for y in range(h):
        for x in range(w):
            dx = x - cx
            val = None

            # === MUSHROOM CAP (rows 0-11) ===
            # Flat wide ellipse - THE defining shape
            cap_cy = 5.0
            cap_rx = w * 0.48
            cap_ry = 5.5
            dc = math.sqrt((dx / cap_rx) ** 2 + ((y - cap_cy) / cap_ry) ** 2)
            if dc < 1.0:
                val = hot(dc)
                # Fire ring detail inside cap
                if 0.3 < dc < 0.5 and 2 <= y <= 8:
                    val = Cf

            # Billowing top (extra pixels on top of cap for rounder look)
            if 0 <= y <= 2:
                top_rx = w * 0.3 - y * 0.5
                if abs(dx) < top_rx:
                    d = abs(dx) / top_rx
                    val = hot(d * 0.7 + 0.2)  # slightly dimmer

            # === NARROW NECK (rows 11-13) - must be VERY thin ===
            if 11 <= y <= 13:
                nw = 1.5
                if abs(dx) < nw:
                    d = abs(dx) / nw
                    val = C4 if d < 0.5 else C1
                elif val is not None:
                    val = None  # clear any cap bleed

            # === STEM (rows 14-21) - narrow fire column ===
            if 14 <= y <= 21:
                sw = 1.8 + (y - 14) * 0.25
                if abs(dx) < sw:
                    d = abs(dx) / sw
                    if d < 0.3: val = C4
                    elif d < 0.6: val = C1
                    else: val = C3

            # === GROUND RING (rows 20-30) - spreading debris ===
            if 20 <= y <= 30:
                base_cy = 25.0
                base_rx = w * 0.45
                base_ry = 5.5
                db = math.sqrt((dx / base_rx) ** 2 + ((y - base_cy) / base_ry) ** 2)
                if db < 1.0:
                    val = hot(db)

            grid[y][x] = val
    return grid

# Build banner grid: full Duke (including gun arm) + cloud to the right
DUKE_PAD = 36   # pad duke rows to this width (gun reaches col ~33)
CLOUD_W = 18
side_cloud = make_side_cloud(CLOUD_W, 36)
duke = duke_body
banner_grid = []
for y in range(len(duke_body)):
    row = list(duke_body[y])
    # Pad to fixed width so cloud aligns
    if len(row) < DUKE_PAD:
        row += [None] * (DUKE_PAD - len(row))
    else:
        row = row[:DUKE_PAD]
    # Add cloud
    if y < len(side_cloud):
        row += side_cloud[y]
    else:
        row += [None] * CLOUD_W
    banner_grid.append(row)


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
banner_lines = render_art(banner_grid, "    ")
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

    # DUKE_BANNER: title on top, then duke + mushroom cloud side by side
    f.write("pub const DUKE_BANNER: &str = \"\\\n")
    for line in title_lines:
        f.write(f"\\n        {line}\\\n")
    f.write("\\n\\\n")  # blank line between title and art
    for line in banner_lines:
        f.write(f"\\n{line}\\\n")
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
