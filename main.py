#!/usr/bin/env python3
"""Render a newspaper-style infographic summing up the world news of
Monday 23 November 2026 as a single 1024x1024 PNG.

Pure Python 3 standard library: a small 5x7 bitmap font, simple shape
drawing on an RGB bytearray, and a minimal PNG encoder (zlib).
No network, no files read, no randomness: both runs write identical bytes.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   ->  out/entry.png
"""

import binascii
import os
import struct
import zlib

# ---------------------------------------------------------------- font
# 5x7 bitmap glyphs. Each glyph is 7 rows of 5 bits, '1' = ink.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "11110", "10001", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
}

CHAR_W = 6  # 5 px glyph + 1 px gap, at scale 1
CHAR_H = 7


def text_width(text, scale):
    """Width in pixels of `text` drawn at `scale`."""
    return len(text) * CHAR_W * scale


def wrap_text(text, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def _off(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = self._off(x, y)
            self.px[o:o + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            o = self._off(x0, yy)
            self.px[o:o + len(row)] = row

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        """Bresenham line with square thickness t."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0 - t // 2, y0 - t // 2, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=False, t=2):
        """Midpoint circle; outline (thickness t) or filled."""
        x = 0
        y = r
        d = 1 - r
        pts = []

        def plot(px, py):
            pts.append((px, py))

        while x <= y:
            for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)):
                plot(cx + sx, cy + sy)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1
        if fill:
            rows = {}
            for px, py in pts:
                rows.setdefault(py, [px, px])
                rows[py][0] = min(rows[py][0], px)
                rows[py][1] = max(rows[py][1], px)
            for py, (a, b) in rows.items():
                self.fill_rect(a, py, b - a + 1, 1, color)
        else:
            for px, py in pts:
                self.fill_rect(px - t // 2, py - t // 2, t, t, color)

    def ellipse(self, cx, cy, rx, ry, color, t=2):
        """Outline ellipse drawn as a scaled circle sample."""
        import math
        steps = max(48, int(2 * math.pi * max(rx, ry)))
        prev = None
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            px = int(round(cx + rx * math.cos(a)))
            py = int(round(cy + ry * math.sin(a)))
            if prev is not None:
                self.line(prev[0], prev[1], px, py, color, t)
            prev = (px, py)

    def triangle(self, p1, p2, p3, color):
        """Filled triangle, scanline fill."""
        pts = sorted((p1, p2, p3), key=lambda p: p[1])
        (x1, y1), (x2, y2), (x3, y3) = pts

        def interp(xa, ya, xb, yb, y):
            if yb == ya:
                return xa
            return xa + (xb - xa) * (y - ya) / (yb - ya)

        for y in range(y1, y3 + 1):
            if y < y2:
                xa = interp(x1, y1, x2, y2, y)
                xb = interp(x1, y1, x3, y3, y)
            else:
                xa = interp(x2, y2, x3, y3, y)
                xb = interp(x1, y1, x3, y3, y)
            a, b = int(min(xa, xb)), int(max(xa, xb))
            self.fill_rect(a, y, b - a + 1, 1, color)

    # ---------------------------------------------------------------- text
    def draw_glyph(self, x, y, ch, scale, color):
        glyph = FONT.get(ch)
        if glyph is None:
            glyph = FONT["?"] if ch != " " else FONT[" "]
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "1":
                    self.fill_rect(x + col * scale, y + row * scale,
                                   scale, scale, color)

    def draw_text(self, x, y, text, scale, color):
        """Draw text (upper-cased; unknown chars become space)."""
        cx = x
        for ch in text.upper():
            if ch not in FONT:
                ch = " "
            self.draw_glyph(cx, y, ch, scale, color)
            cx += CHAR_W * scale
        return cx

    def draw_text_centered(self, cx, y, text, scale, color):
        w = text_width(text, scale)
        return self.draw_text(cx - w // 2, y, text, scale, color)

    def draw_lines(self, x, y, lines, scale, color, leading=None):
        if leading is None:
            leading = CHAR_H * scale + 4
        for line in lines:
            self.draw_text(x, y, line, scale, color)
            y += leading
        return y


# ---------------------------------------------------------------- PNG out
def write_png(path, canvas):
    w, h = canvas.w, canvas.h
    raw = bytearray()
    rowlen = w * 3
    for y in range(h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * rowlen:(y + 1) * rowlen]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 232)   # newsprint off-white
INK = (26, 26, 30)        # near-black
RED = (163, 22, 33)       # headline red
NAVY = (31, 58, 95)       # deep blue
TEAL = (15, 107, 92)      # green-teal
OCHRE = (176, 116, 28)    # warm ochre
SLATE = (90, 96, 110)     # grey for rules / captions
TINT_RED = (244, 224, 220)
TINT_NAVY = (222, 231, 240)
TINT_TEAL = (214, 235, 229)
TINT_OCHRE = (244, 233, 209)
TINT_SLATE = (232, 232, 228)
WHITE = (255, 255, 255)

W, H = 1024, 1024
MARGIN = 36


# ---------------------------------------------------------------- icons
def icon_summit(c, x, y, s, color, accent):
    """Three flags over a table line: a trilateral summit."""
    cx = x + s // 2
    c.hline(x + 8, y + s - 14, s - 16, color, 3)
    for i, fx in enumerate((x + s // 4, cx, x + 3 * s // 4)):
        c.vline(fx, y + 14, s - 30, color, 3)
        fc = accent if i == 1 else color
        c.triangle((fx, y + 14), (fx, y + 34), (fx + 24, y + 24), fc)


def icon_missile(c, x, y, s, color, accent):
    """Rocket with flame, nose up."""
    cx = x + s // 2
    c.fill_rect(cx - 8, y + 18, 16, 38, color)
    c.triangle((cx - 8, y + 18), (cx + 8, y + 18), (cx, y + 2), color)
    c.triangle((cx - 8, y + 46), (cx - 20, y + 60), (cx - 8, y + 56), color)
    c.triangle((cx + 8, y + 46), (cx + 20, y + 60), (cx + 8, y + 56), color)
    c.triangle((cx - 6, y + 56), (cx + 6, y + 56), (cx, y + 76), accent)


def icon_chart(c, x, y, s, color, accent):
    """Falling market chart with a down arrow."""
    c.vline(x + 10, y + 10, s - 20, color, 3)
    c.hline(x + 10, y + s - 10, s - 20, color, 3)
    pts = [(x + 16, y + 14), (x + 30, y + 28), (x + 44, y + 24),
           (x + 58, y + 44), (x + 70, y + 58)]
    for i in range(len(pts) - 1):
        c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], accent, 3)
    ex, ey = pts[-1]
    c.line(ex, ey, ex - 9, ey - 1, accent, 3)
    c.line(ex, ey, ex - 1, ey - 9, accent, 3)


def icon_shield(c, x, y, s, color, accent):
    """Shield with a star: an alliance meeting."""
    cx = x + s // 2
    c.line(x + 12, y + 10, x + s - 12, y + 10, color, 3)
    c.line(x + 12, y + 10, x + 12, y + s // 2, color, 3)
    c.line(x + s - 12, y + 10, x + s - 12, y + s // 2, color, 3)
    c.line(x + 12, y + s // 2, cx, y + s - 8, color, 3)
    c.line(x + s - 12, y + s // 2, cx, y + s - 8, color, 3)
    c.circle(cx, y + s // 2 - 8, 7, accent, fill=True)
    c.line(cx - 12, y + s // 2 - 8, cx + 12, y + s // 2 - 8, accent, 2)
    c.line(cx, y + s // 2 - 20, cx, y + s // 2 + 4, accent, 2)


def icon_blast(c, x, y, s, color, accent):
    """Explosion star over two buildings: airstrikes."""
    cx, cy = x + s // 2, y + s // 2 - 8
    c.line(cx - 18, cy, cx + 18, cy, accent, 3)
    c.line(cx, cy - 18, cx, cy + 18, accent, 3)
    c.line(cx - 13, cy - 13, cx + 13, cy + 13, accent, 2)
    c.line(cx - 13, cy + 13, cx + 13, cy - 13, accent, 2)
    c.circle(cx, cy, 5, accent, fill=True)
    c.fill_rect(x + 12, y + s - 26, 20, 22, color)
    c.fill_rect(x + 44, y + s - 32, 20, 28, color)


ICONS = {
    "summit": icon_summit,
    "missile": icon_missile,
    "chart": icon_chart,
    "shield": icon_shield,
    "blast": icon_blast,
}


def icon_box(c, x, y, s, tint, icon, color, accent):
    """Tinted square with a thin outline, icon drawn inside."""
    c.fill_rect(x, y, s, s, tint)
    c.fill_rect(x, y, s, 2, color)
    c.fill_rect(x, y + s - 2, s, 2, color)
    c.fill_rect(x, y, 2, s, color)
    c.fill_rect(x + s - 2, y, 2, s, color)
    ICONS[icon](c, x + 6, y + 6, s - 12, color, accent)

# ---------------------------------------------------------------- stories
LEAD = {
    "kicker": "SUMMIT",
    "color": NAVY,
    "tint": TINT_NAVY,
    "icon": "summit",
    "headline": ["TRUMP, XI AND PUTIN", "MEET IN SHENZHEN"],
    "summary": ("THE FIRST EVER TRILATERAL SUMMIT OF THE THREE NUCLEAR "
                "POWERS, ON THE SIDELINES OF APEC. THEY SIGN A FOUR-POINT "
                "DECLARATION TOWARD PEACE ON UN REFORM, OIL SUPPLY, "
                "COURTS AND NUCLEAR RISKS."),
    "stat": "FIRST THREE-WAY SUMMIT - 90 MINUTES - 4-POINT DECLARATION",
}

GRID = [
    {
        "kicker": "GULF",
        "color": RED,
        "tint": TINT_RED,
        "icon": "missile",
        "headline": "IRAN'S BIGGEST MISSILE WEEK IN A YEAR",
        "summary": ("TRUMP SAYS IRAN LAUNCHED ITS HEAVIEST MISSILE WEEK IN "
                    "OVER A YEAR. THE US STRUCK A TANKER AND VOWED TO SINK "
                    "SHIPS BREACHING ITS BLOCKADE."),
    },
    {
        "kicker": "MARKETS",
        "color": OCHRE,
        "tint": TINT_OCHRE,
        "icon": "chart",
        "headline": "BITCOIN SINKS TO $55,100 IN MARKET ROUT",
        "summary": ("BITCOIN FALLS TO ITS LOWEST SINCE SEPTEMBER 2024. "
                    "NVIDIA DROPS ABOUT 23% IN ITS WORST WEEK SINCE 2008 "
                    "AS THE S&P 500 ENTERS CORRECTION."),
    },
    {
        "kicker": "EUROPE",
        "color": NAVY,
        "tint": TINT_NAVY,
        "icon": "shield",
        "headline": "NATO MEETS IN EMERGENCY OVER POLAND",
        "summary": ("NATO MEETS IN EMERGENCY AFTER THREE RUSSIAN OBJECTS "
                    "CAME DOWN IN POLAND. THE EU PROPOSES NEW SANCTIONS ON "
                    "60 BANKS, CRYPTO AND THE SHADOW FLEET."),
    },
    {
        "kicker": "WAR",
        "color": TEAL,
        "tint": TINT_TEAL,
        "icon": "blast",
        "headline": "RUSSIAN STRIKES KILL 15 IN KYIV REGION",
        "summary": ("RUSSIAN STRIKES ON THE KYIV REGION KILL AT LEAST 15 "
                    "PEOPLE. A MISSILE HITS KRYVYI RIH, KILLING TWO "
                    "INCLUDING A 7-YEAR-OLD BOY."),
    },
]

ALSO = [
    "US POLITICS: DEMOCRATS REACH 258 HOUSE SEATS, THEIR LARGEST MAJORITY SINCE 1992.",
    "INDONESIA: 24 KILLED IN A FACTORY BLAZE AS RESCUERS SEARCH FOR DOZENS MISSING.",
    "NEPAL: EARTHQUAKE STRIKES KOSHI PROVINCE, FELT ACROSS NORTHERN INDIA.",
    "MEXICO: DRUG LORD CHAPO ISIDRO CAPTURED AFTER A RAID AND CARTEL VIOLENCE.",
]

# ---------------------------------------------------------------- layout
def render():
    c = Canvas(W, H, PAPER)

    # ---- masthead
    c.draw_text_centered(W // 2, 30, "THE WORLD IN ONE DAY", 6, INK)
    c.hline(MARGIN, 82, W - 2 * MARGIN, INK, 2)
    c.hline(MARGIN, 86, W - 2 * MARGIN, INK, 1)
    c.draw_text_centered(W // 2, 98, "MONDAY, 23 NOVEMBER 2026", 4, RED)
    c.hline(MARGIN, 134, W - 2 * MARGIN, INK, 3)
    c.draw_text_centered(W // 2, 144,
                         "THE DAY'S NEWS FROM EVERY CORNER OF THE EARTH",
                         2, SLATE)

    # ---- lead story
    ly = 172
    c.draw_text(MARGIN, ly, LEAD["kicker"], 2, LEAD["color"])
    icon_box(c, W - MARGIN - 170, ly, 170, LEAD["tint"], LEAD["icon"],
             LEAD["color"], RED)
    hy = ly + 26
    for line in LEAD["headline"]:
        c.draw_text(MARGIN, hy, line, 4, INK)
        hy += 32
    sy = hy + 8
    lines = wrap_text(LEAD["summary"], 2, W - MARGIN - 170 - MARGIN - 24)
    sy = c.draw_lines(MARGIN, sy, lines, 2, INK, leading=18)
    c.draw_text(MARGIN, sy + 12, LEAD["stat"], 2, LEAD["color"])
    c.hline(MARGIN, 372, W - 2 * MARGIN, INK, 2)

    # ---- 2x2 grid of stories
    cell_w = (W - 2 * MARGIN - 24) // 2
    cell_h = 176
    grid_top = 392
    for i, story in enumerate(GRID):
        cx = MARGIN + (i % 2) * (cell_w + 24)
        cy = grid_top + (i // 2) * (cell_h + 16)
        icon_box(c, cx, cy, 92, story["tint"], story["icon"],
                 story["color"], RED)
        c.draw_text(cx + 104, cy + 4, story["kicker"], 2, story["color"])
        hl = wrap_text(story["headline"], 3, cell_w - 104)
        yy = c.draw_lines(cx + 104, cy + 24, hl, 3, INK, leading=25)
        sl = wrap_text(story["summary"], 2, cell_w)
        c.draw_lines(cx, cy + 102, sl, 2, INK, leading=18)

    # ---- also today
    ay = 776
    c.draw_text(MARGIN, ay, "ALSO TODAY", 3, INK)
    c.hline(MARGIN, ay + 26, W - 2 * MARGIN, INK, 2)
    for i, item in enumerate(ALSO):
        ix = MARGIN + (i % 2) * (cell_w + 24)
        iy = ay + 44 + (i // 2) * 62
        c.fill_rect(ix, iy + 2, 10, 10, RED)
        lines = wrap_text(item, 2, cell_w - 20)
        c.draw_lines(ix + 20, iy, lines, 2, INK, leading=18)

    # ---- footer
    c.hline(MARGIN, 948, W - 2 * MARGIN, SLATE, 1)
    c.draw_text_centered(W // 2, 962,
                         "MAKE.FUN - THE WORLD IN ONE IMAGE - 23 NOVEMBER 2026",
                         2, SLATE)
    return c


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path, render())
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
