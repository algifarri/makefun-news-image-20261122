#!/usr/bin/env python3
"""One image that sums up the world news of Sunday 22 November 2026.

A broadsheet front page drawn entirely by this program: a small RGB
canvas, a hand-drawn 6x8 bitmap typeface and a from-scratch PNG writer.
Pure Python standard library only, no network, no clock, no randomness
-- every run writes exactly the same bytes.

The page is a list of sections; one walker paints them top to bottom,
each section reporting how tall it is before the next one starts.
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
SKY = (96, 140, 190)

# ---------------------------------------------------------------------------
# 6x8 bitmap typeface.  Eight rows of six cells per glyph; '#' paints ink.
# ---------------------------------------------------------------------------

FONT = {
    "A": (".####.", "#....#", "#....#", "######", "#....#", "#....#", "#....#", "#....#"),
    "B": ("#####.", "#....#", "#....#", "#####.", "#....#", "#....#", "#....#", "#####."),
    "C": (".####.", "#....#", "#.....", "#.....", "#.....", "#.....", "#....#", ".####."),
    "D": ("#####.", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", "#####."),
    "E": ("######", "#.....", "#.....", "#####.", "#.....", "#.....", "#.....", "######"),
    "F": ("######", "#.....", "#.....", "#####.", "#.....", "#.....", "#.....", "#....."),
    "G": (".####.", "#....#", "#.....", "#.####", "#....#", "#....#", "#....#", ".####."),
    "H": ("#....#", "#....#", "#....#", "######", "#....#", "#....#", "#....#", "#....#"),
    "I": (".####.", "..##..", "..##..", "..##..", "..##..", "..##..", "..##..", ".####."),
    "J": ("..####", "....#.", "....#.", "....#.", "....#.", "....#.", "#...#.", ".###.."),
    "K": ("#....#", "#...#.", "#..#..", "###...", "#..#..", "#...#.", "#....#", "#....#"),
    "L": ("#.....", "#.....", "#.....", "#.....", "#.....", "#.....", "#.....", "######"),
    "M": ("#....#", "##..##", "#.##.#", "#.##.#", "#....#", "#....#", "#....#", "#....#"),
    "N": ("#....#", "##...#", "#.#..#", "#..#.#", "#...##", "#....#", "#....#", "#....#"),
    "O": (".####.", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", ".####."),
    "P": ("#####.", "#....#", "#....#", "#####.", "#.....", "#.....", "#.....", "#....."),
    "Q": (".####.", "#....#", "#....#", "#....#", "#....#", "#.#..#", "#..#.#", ".##.##"),
    "R": ("#####.", "#....#", "#....#", "#####.", "#..#..", "#...#.", "#....#", "#....#"),
    "S": (".#####", "#.....", "#.....", ".####.", ".....#", ".....#", ".....#", "#####."),
    "T": ("######", "..##..", "..##..", "..##..", "..##..", "..##..", "..##..", "..##.."),
    "U": ("#....#", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", ".####."),
    "V": ("#....#", "#....#", "#....#", "#....#", "#....#", "#....#", ".#..#.", "..##.."),
    "W": ("#....#", "#....#", "#....#", "#....#", "#.##.#", "#.##.#", "##..##", "#....#"),
    "X": ("#....#", ".#..#.", "..##..", "..##..", "..##..", ".#..#.", "#....#", "#....#"),
    "Y": ("#....#", "#....#", ".#..#.", "..##..", "..##..", "..##..", "..##..", "..##.."),
    "Z": ("######", ".....#", "....#.", "...#..", "..#...", ".#....", "#.....", "######"),
    "0": (".####.", "#...##", "#..#.#", "#.#..#", "##...#", "#....#", "#....#", ".####."),
    "1": ("..##..", ".###..", "..##..", "..##..", "..##..", "..##..", "..##..", ".####."),
    "2": (".####.", "#....#", ".....#", "....#.", "...#..", "..#...", ".#....", "######"),
    "3": (".####.", "#....#", ".....#", "..###.", ".....#", ".....#", "#....#", ".####."),
    "4": ("...##.", "..#.#.", ".#..#.", "#...#.", "######", "....#.", "....#.", "....#."),
    "5": ("######", "#.....", "#.....", "#####.", ".....#", ".....#", "#....#", ".####."),
    "6": (".####.", "#....#", "#.....", "#####.", "#....#", "#....#", "#....#", ".####."),
    "7": ("######", ".....#", "....#.", "....#.", "...#..", "...#..", "..#...", "..#..."),
    "8": (".####.", "#....#", "#....#", ".####.", "#....#", "#....#", "#....#", ".####."),
    "9": (".####.", "#....#", "#....#", "#....#", ".#####", ".....#", "#....#", ".####."),
    " ": ("......", "......", "......", "......", "......", "......", "......", "......"),
    ".": ("......", "......", "......", "......", "......", "......", ".##...", ".##..."),
    ",": ("......", "......", "......", "......", "......", ".##...", ".##...", ".#...."),
    ":": ("......", ".##...", ".##...", "......", "......", ".##...", ".##...", "......"),
    ";": ("......", ".##...", ".##...", "......", "......", ".##...", ".##...", ".#...."),
    "'": ("..##..", "..##..", "..#...", "......", "......", "......", "......", "......"),
    "-": ("......", "......", "......", ".####.", "......", "......", "......", "......"),
    "+": ("......", "..##..", "..##..", ".####.", ".####.", "..##..", "..##..", "......"),
    "%": ("##...#", "##..#.", "....#.", "...#..", "..#...", ".#....", ".#..##", "#...##"),
    "/": (".....#", ".....#", "....#.", "....#.", "...#..", "..#...", "..#...", ".#...."),
    "(": ("..##..", ".#....", "#.....", "#.....", "#.....", "#.....", ".#....", "..##.."),
    ")": ("..##..", "....#.", ".....#", ".....#", ".....#", ".....#", "....#.", "..##.."),
    "!": ("..##..", "..##..", "..##..", "..##..", "..##..", "..##..", "......", "..##.."),
    "?": (".####.", "#....#", ".....#", "....#.", "...#..", "..##..", "......", "..##.."),
    "$": ("..##..", ".#####", "#.##.#", "#.##..", "..####", "...##.", "#.##.#", ".###.."),
    "&": (".###..", "#...#.", "#...#.", "..#...", ".#.#.#", "#..#..", "#...##", ".##.#."),
}

CW, CH = 6, 8


def glyph(ch):
    return FONT.get(ch, FONT["?"])


def span(s, scale, gap=1):
    if not s:
        return 0
    return len(s) * (CW * scale + gap) - gap


def put_text(cv, x, y, s, scale, color, gap=1):
    pen = x
    for ch in s.upper():
        for ry, row in enumerate(glyph(ch)):
            for rx, cell in enumerate(row):
                if cell == "#":
                    cv.rect(pen + rx * scale, y + ry * scale, scale, scale, color)
        pen += CW * scale + gap
    return pen


def put_centred(cv, cx, y, s, scale, color, gap=1):
    put_text(cv, cx - span(s, scale, gap) // 2, y, s, scale, color, gap)


def wrap(s, scale, max_px, gap=1):
    lines, cur = [], ""
    for word in s.split():
        trial = word if not cur else cur + " " + word
        if span(trial, scale, gap) <= max_px or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def put_para(cv, x, y, s, scale, color, max_px, leading, gap=1):
    for line in wrap(s, scale, max_px, gap):
        put_text(cv, x, y, line, scale, color, gap)
        y += leading
    return y


# ---------------------------------------------------------------------------
# Canvas: a flat RGB buffer and a small kit of drawing primitives.
# ---------------------------------------------------------------------------

class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bytes(bg) * (w * h))

    def dot(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        run = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(run)] = run

    def outline(self, x, y, w, h, color, t=2):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=2):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = t // 2
        for k in range(steps + 1):
            x = x0 + (x1 - x0) * k // steps
            y = y0 + (y1 - y0) * k // steps
            self.rect(x - r, y - r, t, t, color)

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            self.rect(cx - half, cy + dy, 2 * half + 1, 1, color)

    def smoke(self, x, y, puffs, color):
        for i, (r, dx) in enumerate(puffs):
            self.disc(x + dx, y - i * (r + 4), r, color)


# ---------------------------------------------------------------------------
# Scene painters.  Each fills a box (x, y, w, h).
# ---------------------------------------------------------------------------

def scene_cop(cv, x, y, w, h):
    # A warming globe, a thermometer running hot, and a NO DEAL placard.
    cx, cy, r = x + 110, y + 58, 46
    cv.disc(cx, cy, r, NAVY)
    cv.disc(cx - 18, cy - 14, 12, GREEN)
    cv.disc(cx + 15, cy + 8, 14, GREEN)
    cv.disc(cx + 4, cy - 26, 9, GREEN)
    cv.disc(cx - 26, cy + 22, 8, GREEN)
    tx = x + w - 84
    cv.rect(tx, y + 6, 10, 84, INK)
    cv.rect(tx + 2, y + 38, 6, 52, RED)
    cv.disc(tx + 5, y + 94, 12, RED)
    cv.disc(tx + 5, y + 94, 7, ORANGE)
    px, py = x + 210, y + 42
    cv.rect(px, py, 128, 34, WHITE)
    cv.outline(px, py, 128, 34, RED, 3)
    put_text(cv, px + 14, py + 9, "NO DEAL", 2, RED)
    put_text(cv, x + 8, y + h - 14, "ANTALYA", 1, FAINT)
    put_text(cv, x + 168, y + h - 14, "200 NATIONS", 1, FAINT)


def scene_strike(cv, x, y, w, h):
    # A factory, a smoking chimney and a picket sign demanding 5 pct.
    ground = y + h - 12
    cv.line(x + 4, ground, x + w - 4, ground, INK, 3)
    cv.rect(x + 8, ground - 44, 50, 44, INK)
    cv.line(x + 4, ground - 44, x + 20, ground - 56, RED, 3)
    cv.line(x + 20, ground - 56, x + 36, ground - 44, RED, 3)
    cv.line(x + 36, ground - 44, x + 52, ground - 56, RED, 3)
    cv.line(x + 52, ground - 56, x + 62, ground - 44, RED, 3)
    cv.rect(x + 64, ground - 72, 12, 72, FAINT)
    cv.smoke(x + 70, ground - 78, [(5, 0), (7, 4), (9, 9)], SMOKE)
    cv.line(x + 100, ground, x + 100, ground - 58, INK, 3)
    cv.rect(x + 80, ground - 82, 40, 26, WHITE)
    cv.outline(x + 80, ground - 82, 40, 26, RED, 2)
    put_text(cv, x + 85, ground - 76, "5 PCT", 1, RED)


def scene_g20(cv, x, y, w, h):
    # A globe over the letters G20.
    cx, cy, r = x + 60, y + 46, 34
    cv.disc(cx, cy, r, NAVY)
    cv.disc(cx - 12, cy - 10, 9, GREEN)
    cv.disc(cx + 11, cy + 6, 10, GREEN)
    cv.disc(cx + 2, cy - 20, 6, GREEN)
    put_centred(cv, x + 60, y + 92, "G20", 3, INK)


def scene_un(cv, x, y, w, h):
    # The French tricolore and the US stars and stripes, side by side.
    base = y + h - 10
    cv.line(x + 6, base, x + w - 6, base, INK, 2)
    for px, kind in ((x + 12, "fr"), (x + 66, "us")):
        cv.rect(px, y + 12, 4, base - y - 12, INK)
        fx, fy, fw, fh = px + 4, y + 12, 36, 24
        if kind == "fr":
            cv.rect(fx, fy, 12, fh, NAVY)
            cv.rect(fx + 12, fy, 12, fh, WHITE)
            cv.rect(fx + 24, fy, 12, fh, RED)
        else:
            for s in range(7):
                cv.rect(fx, fy + s * 3, fw, 3, RED if s % 2 == 0 else WHITE)
            cv.rect(fx, fy, 15, 12, NAVY)
            for gx in range(3):
                for gy in range(2):
                    cv.rect(fx + 2 + gx * 5, fy + 2 + gy * 5, 2, 2, WHITE)
        cv.outline(fx, fy, fw, fh, INK, 1)
    cv.line(x + w // 2 - 10, y + h - 30, x + w // 2, y + h - 20, GREEN, 4)
    cv.line(x + w // 2, y + h - 20, x + w // 2 + 14, y + h - 36, GREEN, 4)


def scene_robot(cv, x, y, w, h):
    # A boxy robot inside a red prohibition ring.
    cx, cy = x + w // 2, y + h // 2 + 4
    cv.disc(cx, cy, 52, RED)
    cv.disc(cx, cy, 46, PAPER)
    cv.rect(cx - 16, cy - 34, 32, 24, INK)
    cv.rect(cx - 10, cy - 28, 5, 5, WHITE)
    cv.rect(cx + 5, cy - 28, 5, 5, WHITE)
    cv.line(cx, cy - 34, cx, cy - 46, INK, 3)
    cv.disc(cx, cy - 48, 3, RED)
    cv.rect(cx - 22, cy - 6, 44, 34, FAINT)
    cv.rect(cx - 8, cy + 4, 16, 12, GOLD)
    cv.line(cx - 22, cy + 2, cx - 34, cy + 14, INK, 4)
    cv.line(cx + 22, cy + 2, cx + 34, cy + 14, INK, 4)
    cv.line(cx - 12, cy + 28, cx - 12, cy + 40, INK, 4)
    cv.line(cx + 12, cy + 28, cx + 12, cy + 40, INK, 4)
    cv.line(cx - 36, cy - 36, cx + 36, cy + 40, RED, 5)


SCENES = {
    "cop": scene_cop,
    "strike": scene_strike,
    "g20": scene_g20,
    "un": scene_un,
    "robot": scene_robot,
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
# Section painters.  Each returns the height it consumed.
# ---------------------------------------------------------------------------

def paint_masthead(cv, sec, top):
    cv.rect(MARGIN, top, COL, 5, INK)
    cv.rect(MARGIN, top + 8, COL, 2, INK)
    put_text(cv, MARGIN, top + 22, sec["left"], 2, FAINT)
    rspan = span(sec["right"], 2)
    put_text(cv, W - MARGIN - rspan, top + 22, sec["right"], 2, FAINT)
    put_centred(cv, W // 2, top + 16, sec["date"], 3, RED)
    put_centred(cv, W // 2, top + 44, sec["title"], 6, INK)
    cv.rect(MARGIN, top + 96, COL, 3, INK)
    return 104


def paint_hero(cv, sec, top):
    put_text(cv, MARGIN, top, sec["kicker"], 2, RED)
    y = top + 26
    for line in sec["headline"]:
        put_text(cv, MARGIN, y, line, 6, INK)
        y += 56
    y = put_para(cv, MARGIN, y + 4, sec["dek"], 2, INK, COL, 19)
    scene_y = y + 6
    SCENES[sec["scene"]](cv, MARGIN, scene_y, COL, 120)
    y = scene_y + 128
    y = put_para(cv, MARGIN, y, sec["caption"], 2, FAINT, COL, 19)
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
    cv.outline(x, y, w, h, INK, 2)
    cv.rect(x, y, w, 6, card["accent"])
    sx, sy, sw, sh = x + 12, y + 40, 120, 128
    SCENES[card["scene"]](cv, sx, sy, sw, sh)
    tx = x + 146
    tw = x + w - 12 - tx
    put_text(cv, tx, y + 14, card["kicker"], 2, card["accent"])
    hy = put_para(cv, tx, y + 38, card["headline"], 3, INK, tw, 27)
    put_para(cv, tx, hy + 4, card["body"], 2, INK, tw, 18)


def paint_briefs(cv, sec, top):
    cv.rect(MARGIN, top, COL, 60, INK)
    cv.rect(MARGIN + 10, top + 10, 96, 40, RED)
    put_centred(cv, MARGIN + 58, top + 15, "IN", 2, WHITE)
    put_centred(cv, MARGIN + 58, top + 33, "BRIEF", 2, WHITE)
    y = top + 5
    for line in sec["lines"]:
        put_text(cv, MARGIN + 122, y, line, 2, WHITE)
        y += 18
    return 68


def paint_footer(cv, sec, top):
    put_centred(cv, W // 2, top + 2, sec["text"], 2, FAINT)
    return 20


PAINTERS = {
    "masthead": paint_masthead,
    "hero": paint_hero,
    "cards": paint_cards,
    "briefs": paint_briefs,
    "footer": paint_footer,
}


def compose():
    cv = Canvas(W, H, PAPER)
    y = 22
    for sec in PAGE:
        y += PAINTERS[sec["kind"]](cv, sec, y) + 10
    return cv


# ---------------------------------------------------------------------------
# PNG writer: signature, IHDR, one IDAT of filter-0 scanlines, IEND.
# ---------------------------------------------------------------------------

def chunk(tag, payload):
    body = tag + payload
    return (struct.pack(">I", len(payload)) + body
            + struct.pack(">I", binascii.crc32(body) & 0xFFFFFFFF))


def encode_png(cv):
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.buf[yy * stride:(yy + 1) * stride]
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(compose())
    with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
        fh.write(data)


if __name__ == "__main__":
    main()
