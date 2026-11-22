#!/usr/bin/env python3
"""Sunday 22 November 2026, summed up in one picture.

This program draws a broadsheet front page and writes it out as a PNG.
Everything is drawn by hand in code: a tiny RGB canvas, a 6-by-8 pixel
typeface sketched row by row, and a PNG encoder built from the file
format up.  Standard library only.  No network, no clock, no dice --
run it twice and the two files match byte for byte.

The page itself is a list of sections.  A short loop walks the list,
asking every section how much vertical room it needs and then giving
it a strip of the page to paint.
"""

import binascii
import os
import struct
import zlib

W = 1024
H = 1024
MARGIN = 36
COL = W - 2 * MARGIN

PAPER = (247, 243, 232)
INK = (27, 25, 23)
FAINT = (108, 100, 90)
RED = (172, 30, 38)
NAVY = (29, 52, 99)
GOLD = (188, 138, 38)
GREEN = (33, 104, 62)
ORANGE = (219, 106, 26)
SMOKE = (140, 134, 126)
WHITE = (252, 250, 244)

# ---------------------------------------------------------------------------
# Pixel typeface.  One entry per character: eight rows joined with "/",
# six cells a row, "#" for a painted cell.
# ---------------------------------------------------------------------------

FONT = {
    "A": ".####./#....#/#....#/######/#....#/#....#/#....#/#....#",
    "B": "#####./#....#/#....#/#####./#....#/#....#/#....#/#####.",
    "C": ".####./#....#/#...../#...../#...../#...../#....#/.####.",
    "D": "#####./#....#/#....#/#....#/#....#/#....#/#....#/#####.",
    "E": "######/#...../#...../#####./#...../#...../#...../######",
    "F": "######/#...../#...../#####./#...../#...../#...../#.....",
    "G": ".####./#....#/#...../#.####/#....#/#....#/#....#/.####.",
    "H": "#....#/#....#/#....#/######/#....#/#....#/#....#/#....#",
    "I": ".####./..##../..##../..##../..##../..##../..##../.####.",
    "J": "..####/....#./....#./....#./....#./....#./#...#./.###..",
    "K": "#....#/#...#./#..#../###.../#..#../#...#./#....#/#....#",
    "L": "#...../#...../#...../#...../#...../#...../#...../######",
    "M": "#....#/##..##/#.##.#/#.##.#/#....#/#....#/#....#/#....#",
    "N": "#....#/##...#/#.#..#/#..#.#/#...##/#....#/#....#/#....#",
    "O": ".####./#....#/#....#/#....#/#....#/#....#/#....#/.####.",
    "P": "#####./#....#/#....#/#####./#...../#...../#...../#.....",
    "Q": ".####./#....#/#....#/#....#/#....#/#.#..#/#..#.#/.##.##",
    "R": "#####./#....#/#....#/#####./#..#../#...#./#....#/#....#",
    "S": ".#####/#...../#...../.####./.....#/.....#/.....#/#####.",
    "T": "######/..##../..##../..##../..##../..##../..##../..##..",
    "U": "#....#/#....#/#....#/#....#/#....#/#....#/#....#/.####.",
    "V": "#....#/#....#/#....#/#....#/#....#/#....#/.#..#./..##..",
    "W": "#....#/#....#/#....#/#....#/#.##.#/#.##.#/##..##/#....#",
    "X": "#....#/.#..#./..##../..##../..##../.#..#./#....#/#....#",
    "Y": "#....#/#....#/.#..#./..##../..##../..##../..##../..##..",
    "Z": "######/.....#/....#./...#../..#.../.#..../#...../######",
    "0": ".####./#...##/#..#.#/#.#..#/##...#/#....#/#....#/.####.",
    "1": "..##../.###../..##../..##../..##../..##../..##../.####.",
    "2": ".####./#....#/.....#/....#./...#../..#.../.#..../######",
    "3": ".####./#....#/.....#/..###./.....#/.....#/#....#/.####.",
    "4": "...##./..#.#./.#..#./#...#./######/....#./....#./....#.",
    "5": "######/#...../#...../#####./.....#/.....#/#....#/.####.",
    "6": ".####./#....#/#...../#####./#....#/#....#/#....#/.####.",
    "7": "######/.....#/....#./....#./...#../...#../..#.../..#...",
    "8": ".####./#....#/#....#/.####./#....#/#....#/#....#/.####.",
    "9": ".####./#....#/#....#/#....#/.#####/.....#/#....#/.####.",
    " ": "....../....../....../....../....../....../....../......",
    ".": "....../....../....../....../....../....../.##.../.##...",
    ",": "....../....../....../....../....../.##.../.##.../.#....",
    ":": "....../.##.../.##.../....../....../.##.../.##.../......",
    ";": "....../.##.../.##.../....../....../.##.../.##.../.#....",
    "'": "..##../..##../..#.../....../....../....../....../......",
    "-": "....../....../....../.####./....../....../....../......",
    "+": "....../..##../..##../.####./.####./..##../..##../......",
    "%": "##...#/##..#./....#./...#../..#.../.#..../.#..##/#...##",
    "/": ".....#/.....#/....#./....#./...#../..#.../..#.../.#....",
    "(": "..##../.#..../#...../#...../#...../#...../.#..../..##..",
    ")": "..##../....#./.....#/.....#/.....#/.....#/....#./..##..",
    "!": "..##../..##../..##../..##../..##../..##../....../..##..",
    "?": ".####./#....#/.....#/....#./...#../..##../....../..##..",
    "$": "..##../.#####/#.##.#/#.##../..####/...##./#.##.#/.###..",
    "&": ".###../#...#./#...#./..#.../.#.#.#/#..#../#...##/.##.#.",
}

CW, CH = 6, 8


def rows_for(ch):
    return FONT.get(ch, FONT["?"]).split("/")


def measure(text, scale, gap=1):
    if not text:
        return 0
    return len(text) * (CW * scale + gap) - gap


def draw(cv, x, y, text, scale, color, gap=1):
    pen = x
    for ch in text.upper():
        for ry, row in enumerate(rows_for(ch)):
            for rx, cell in enumerate(row):
                if cell == "#":
                    cv.fill(pen + rx * scale, y + ry * scale, scale, scale, color)
        pen += CW * scale + gap
    return pen


def draw_centred(cv, cx, y, text, scale, color, gap=1):
    draw(cv, cx - measure(text, scale, gap) // 2, y, text, scale, color, gap)


def wrap_text(text, scale, max_px, gap=1):
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if measure(trial, scale, gap) <= max_px or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, text, scale, color, max_px, leading, gap=1):
    for line in wrap_text(text, scale, max_px, gap):
        draw(cv, x, y, line, scale, color, gap)
        y += leading
    return y


# ---------------------------------------------------------------------------
# The canvas: one flat RGB bytearray and a handful of shapes.
# ---------------------------------------------------------------------------

class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bytes(bg) * (w * h))

    def pixel(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def fill(self, x, y, w, h, color):
        lo_x, lo_y = max(0, x), max(0, y)
        hi_x, hi_y = min(self.w, x + w), min(self.h, y + h)
        if hi_x <= lo_x or hi_y <= lo_y:
            return
        strip = bytes(color) * (hi_x - lo_x)
        for yy in range(lo_y, hi_y):
            i = (yy * self.w + lo_x) * 3
            self.buf[i:i + len(strip)] = strip

    def frame(self, x, y, w, h, color, t=2):
        self.fill(x, y, w, t, color)
        self.fill(x, y + h - t, w, t, color)
        self.fill(x, y, t, h, color)
        self.fill(x + w - t, y, t, h, color)

    def stroke(self, x0, y0, x1, y1, color, t=2):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = t // 2
        for k in range(steps + 1):
            x = x0 + (x1 - x0) * k // steps
            y = y0 + (y1 - y0) * k // steps
            self.fill(x - r, y - r, t, t, color)

    def blob(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            self.fill(cx - half, cy + dy, 2 * half + 1, 1, color)

    def puff(self, x, y, puffs, color):
        for i, (r, dx) in enumerate(puffs):
            self.blob(x + dx, y - i * (r + 4), r, color)


# ---------------------------------------------------------------------------
# Pictures.  Each paints inside a box (x, y, w, h).
# ---------------------------------------------------------------------------

def pic_cop(cv, x, y, w, h):
    # A warming globe, a thermometer running hot, a NO DEAL placard.
    cx, cy, r = x + 110, y + 58, 46
    cv.blob(cx, cy, r, NAVY)
    cv.blob(cx - 18, cy - 14, 12, GREEN)
    cv.blob(cx + 15, cy + 8, 14, GREEN)
    cv.blob(cx + 4, cy - 26, 9, GREEN)
    cv.blob(cx - 26, cy + 22, 8, GREEN)
    tx = x + w - 84
    cv.fill(tx, y + 6, 10, 84, INK)
    cv.fill(tx + 2, y + 38, 6, 52, RED)
    cv.blob(tx + 5, y + 94, 12, RED)
    cv.blob(tx + 5, y + 94, 7, ORANGE)
    px, py = x + 210, y + 42
    cv.fill(px, py, 128, 34, WHITE)
    cv.frame(px, py, 128, 34, RED, 3)
    draw(cv, px + 14, py + 9, "NO DEAL", 2, RED)
    sx, sy = x + 26, y + 22
    cv.blob(sx, sy, 8, GOLD)
    for dx, dy in ((14, 0), (-14, 0), (0, 14), (0, -14)):
        cv.stroke(sx, sy, sx + dx, sy + dy, GOLD, 2)
    draw(cv, x + 8, y + h - 14, "ANTALYA", 1, FAINT)
    draw(cv, x + 168, y + h - 14, "200 NATIONS", 1, FAINT)


def pic_strike(cv, x, y, w, h):
    # A factory, a smoking chimney and a picket sign demanding 5 pct.
    ground = y + h - 12
    cv.stroke(x + 4, ground, x + w - 4, ground, INK, 3)
    cv.fill(x + 8, ground - 44, 50, 44, INK)
    cv.stroke(x + 4, ground - 44, x + 20, ground - 56, RED, 3)
    cv.stroke(x + 20, ground - 56, x + 36, ground - 44, RED, 3)
    cv.stroke(x + 36, ground - 44, x + 52, ground - 56, RED, 3)
    cv.stroke(x + 52, ground - 56, x + 62, ground - 44, RED, 3)
    cv.fill(x + 64, ground - 72, 12, 72, FAINT)
    cv.puff(x + 70, ground - 78, [(5, 0), (7, 4), (9, 9)], SMOKE)
    cv.stroke(x + 100, ground, x + 100, ground - 58, INK, 3)
    cv.fill(x + 80, ground - 82, 40, 26, WHITE)
    cv.frame(x + 80, ground - 82, 40, 26, RED, 2)
    draw(cv, x + 85, ground - 76, "5 PCT", 1, RED)


def pic_g20(cv, x, y, w, h):
    # A globe over the letters G20.
    cx, cy, r = x + 60, y + 46, 34
    cv.blob(cx, cy, r, NAVY)
    cv.blob(cx - 12, cy - 10, 9, GREEN)
    cv.blob(cx + 11, cy + 6, 10, GREEN)
    cv.blob(cx + 2, cy - 20, 6, GREEN)
    draw_centred(cv, x + 60, y + 92, "G20", 3, INK)


def pic_un(cv, x, y, w, h):
    # The French tricolore and the US stars and stripes, side by side.
    base = y + h - 10
    cv.stroke(x + 6, base, x + w - 6, base, INK, 2)
    for px, kind in ((x + 12, "fr"), (x + 66, "us")):
        cv.fill(px, y + 12, 4, base - y - 12, INK)
        fx, fy, fw, fh = px + 4, y + 12, 36, 24
        if kind == "fr":
            cv.fill(fx, fy, 12, fh, NAVY)
            cv.fill(fx + 12, fy, 12, fh, WHITE)
            cv.fill(fx + 24, fy, 12, fh, RED)
        else:
            for s in range(7):
                cv.fill(fx, fy + s * 3, fw, 3, RED if s % 2 == 0 else WHITE)
            cv.fill(fx, fy, 15, 12, NAVY)
            for gx in range(3):
                for gy in range(2):
                    cv.fill(fx + 2 + gx * 5, fy + 2 + gy * 5, 2, 2, WHITE)
        cv.frame(fx, fy, fw, fh, INK, 1)
    cv.stroke(x + w // 2 - 10, y + h - 30, x + w // 2, y + h - 20, GREEN, 4)
    cv.stroke(x + w // 2, y + h - 20, x + w // 2 + 14, y + h - 36, GREEN, 4)


def pic_robot(cv, x, y, w, h):
    # A boxy robot inside a red prohibition ring.
    cx, cy = x + w // 2, y + h // 2 + 4
    cv.blob(cx, cy, 52, RED)
    cv.blob(cx, cy, 46, PAPER)
    cv.fill(cx - 16, cy - 34, 32, 24, INK)
    cv.fill(cx - 10, cy - 28, 5, 5, WHITE)
    cv.fill(cx + 5, cy - 28, 5, 5, WHITE)
    cv.stroke(cx, cy - 34, cx, cy - 46, INK, 3)
    cv.blob(cx, cy - 48, 3, RED)
    cv.fill(cx - 22, cy - 6, 44, 34, FAINT)
    cv.fill(cx - 8, cy + 4, 16, 12, GOLD)
    cv.stroke(cx - 22, cy + 2, cx - 34, cy + 14, INK, 4)
    cv.stroke(cx + 22, cy + 2, cx + 34, cy + 14, INK, 4)
    cv.stroke(cx - 12, cy + 28, cx - 12, cy + 40, INK, 4)
    cv.stroke(cx + 12, cy + 28, cx + 12, cy + 40, INK, 4)
    cv.stroke(cx - 36, cy - 36, cx + 36, cy + 40, RED, 5)


PICS = {
    "cop": pic_cop,
    "strike": pic_strike,
    "g20": pic_g20,
    "un": pic_un,
    "robot": pic_robot,
}

# ---------------------------------------------------------------------------
# The day's news, as reported on Sunday 22 November 2026 (Reuters, AP,
# SBS and wire roundups of the day).
# ---------------------------------------------------------------------------

PAGE = [
    {"kind": "masthead",
     "title": "THE SUNDAY LEDGER",
     "left": "VOL. I - NO. 22",
     "right": "WORLD EDITION",
     "date": "SUNDAY 22 NOVEMBER 2026"},
    {"kind": "hero",
     "kicker": "CLIMATE - COP31 IN ANTALYA",
     "headline": ["COP31: STILL NO DEAL"],
     "dek": ("TALKS RUN INTO SUNDAY WITH NO AGREEMENT AS THE DRAFT DROPS "
             "EVERY MENTION OF FOSSIL FUELS. EU WARNS: A GOOD DEAL OR "
             "NO DEAL AT ALL."),
     "scene": "cop",
     "caption": ("NEARLY 200 NATIONS ARE DEADLOCKED OVER FOSSIL FUELS AND "
                 "FINANCE. NO NEW TEXT HAD LANDED BY SATURDAY NIGHT.")},
    {"kind": "ticker",
     "text": "ANTALYA - BERLIN - JOHANNESBURG - GENEVA - NEW DELHI - TBILISI"},
    {"kind": "cards",
     "cards": [
         {"accent": RED, "scene": "strike",
          "kicker": "GERMANY",
          "headline": "23,000 TO STRIKE ON MONDAY",
          "body": ("IG METALL CALLS A 24-HOUR WALKOUT AT 19 FIRMS, "
                   "INCLUDING MERCEDES-BENZ. UNION WANTS 5 PCT PAY RISE.")},
         {"accent": NAVY, "scene": "g20",
          "kicker": "SOUTH AFRICA",
          "headline": "G20 OPENS IN JOHANNESBURG",
          "body": ("LEADERS GATHER FOR A TWO-DAY SUMMIT IN "
                   "JOHANNESBURG, SOUTH AFRICA.")},
         {"accent": GREEN, "scene": "un",
          "kicker": "LEBANON",
          "headline": "FRANCE AND US DRAFT UN PLAN",
          "body": ("PARIS AND WASHINGTON WORK ON A RESOLUTION TO FILL "
                   "THE GAP LEFT BY UNIFIL IN LEBANON.")},
         {"accent": ORANGE, "scene": "robot",
          "kicker": "AI WEAPONS",
          "headline": "NO LIMITS ON KILLER ROBOTS",
          "body": ("UN STATES AGREE ONLY TO MORE TALKS ON AI WEAPONS, "
                   "WITH NO FIRM COMMITMENT.")},
     ]},
    {"kind": "briefs",
     "label": "IN BRIEF",
     "lines": [
         "NEPAL PM SHAH BEGINS FIRST INDIA VISIT TODAY",
         "GEORGIA MARKS DAY OF MOURNING FOR 6 KILLED IN TBILISI BLAST",
         "QATAR ENVOYS HEAD TO TEHRAN FOR TALKS, IRAN SAYS",
     ]},
    {"kind": "footer",
     "text": "SUNDAY 22 NOVEMBER 2026 - DRAWN BY AN AI AGENT FOR MAKE.FUN"},
]


# ---------------------------------------------------------------------------
# Sections.  Each paints itself and reports the height it took.
# ---------------------------------------------------------------------------

def rule(cv, y):
    cv.fill(MARGIN, y, COL, 2, FAINT)


def paint_masthead(cv, sec, top):
    cv.fill(MARGIN, top, COL, 5, INK)
    cv.fill(MARGIN, top + 8, COL, 2, INK)
    draw(cv, MARGIN, top + 22, sec["left"], 2, FAINT)
    rspan = measure(sec["right"], 2)
    draw(cv, W - MARGIN - rspan, top + 22, sec["right"], 2, FAINT)
    draw_centred(cv, W // 2, top + 16, sec["date"], 3, RED)
    draw_centred(cv, W // 2, top + 44, sec["title"], 6, INK)
    cv.fill(MARGIN, top + 96, COL, 3, INK)
    return 104


def paint_hero(cv, sec, top):
    draw(cv, MARGIN, top, sec["kicker"], 2, RED)
    y = top + 26
    for line in sec["headline"]:
        draw(cv, MARGIN, y, line, 6, INK)
        y += 56
    y = draw_para(cv, MARGIN, y + 4, sec["dek"], 2, INK, COL, 19)
    scene_y = y + 6
    PICS[sec["scene"]](cv, MARGIN, scene_y, COL, 120)
    y = scene_y + 128
    y = draw_para(cv, MARGIN, y, sec["caption"], 2, FAINT, COL, 19)
    return y - top


def paint_cards(cv, sec, top):
    gap = 16
    card_w = (COL - gap) // 2
    card_h = 190
    y = top
    for row in range(2):
        for col in range(2):
            card = sec["cards"][row * 2 + col]
            x = MARGIN + col * (card_w + gap)
            paint_card(cv, card, x, y, card_w, card_h)
        y += card_h + 12
    return y - top - 12


def paint_card(cv, card, x, y, w, h):
    cv.frame(x, y, w, h, INK, 2)
    cv.fill(x, y, w, 6, card["accent"])
    sx, sy, sw, sh = x + 12, y + 40, 120, 128
    PICS[card["scene"]](cv, sx, sy, sw, sh)
    tx = x + 146
    tw = x + w - 12 - tx
    draw(cv, tx, y + 14, card["kicker"], 2, card["accent"])
    hy = draw_para(cv, tx, y + 38, card["headline"], 3, INK, tw, 27)
    draw_para(cv, tx, hy + 4, card["body"], 2, INK, tw, 18)


def paint_briefs(cv, sec, top):
    cv.fill(MARGIN, top, COL, 60, INK)
    cv.fill(MARGIN + 10, top + 10, 96, 40, RED)
    draw_centred(cv, MARGIN + 58, top + 15, "IN", 2, WHITE)
    draw_centred(cv, MARGIN + 58, top + 33, "BRIEF", 2, WHITE)
    y = top + 5
    for line in sec["lines"]:
        draw(cv, MARGIN + 122, y, line, 2, WHITE)
        y += 18
    return 68


def paint_ticker(cv, sec, top):
    draw_centred(cv, W // 2, top + 2, sec["text"], 1, FAINT)
    return 12


def paint_footer(cv, sec, top):
    draw_centred(cv, W // 2, top + 2, sec["text"], 2, FAINT)
    return 20


PAINTERS = {
    "masthead": paint_masthead,
    "hero": paint_hero,
    "ticker": paint_ticker,
    "cards": paint_cards,
    "briefs": paint_briefs,
    "footer": paint_footer,
}


def compose():
    cv = Canvas(W, H, PAPER)
    y = 22
    for sec in PAGE:
        y += PAINTERS[sec["kind"]](cv, sec, y) + 10
        rule(cv, y - 6)
    return cv


# ---------------------------------------------------------------------------
# PNG output: signature, IHDR, a single IDAT of filter-0 rows, IEND.
# ---------------------------------------------------------------------------

def make_chunk(tag, payload):
    body = tag + payload
    crc = binascii.crc32(body) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", crc)


def encode_png(cv):
    header = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    row_bytes = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.buf[yy * row_bytes:(yy + 1) * row_bytes]
    parts = [b"\x89PNG\r\n\x1a\n", make_chunk(b"IHDR", header)]
    parts.append(make_chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
    parts.append(make_chunk(b"IEND", b""))
    return b"".join(parts)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    first = encode_png(compose())
    second = encode_png(compose())
    if first != second:
        raise SystemExit("non-deterministic render")
    if len(first) > 1048576:
        raise SystemExit("entry over 1 MiB")
    with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
        fh.write(first)


if __name__ == "__main__":
    main()
