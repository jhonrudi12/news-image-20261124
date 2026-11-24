#!/usr/bin/env python3
"""The World Today - 24 November 2026.

A one-page newspaper poster summing up the day's world news in a
single image. Pure Python standard library: a tiny 5x7 bitmap font,
a software rasteriser and a hand-rolled PNG encoder. Deterministic:
same input, same bytes, every run.

Writes /output/entry.png (1024x1024).
"""

import binascii
import os
import struct
import zlib

W = 1024
H = 1024
PAPER = (250, 248, 240)
INK = (22, 22, 22)
RED = (176, 32, 32)
GREY = (105, 105, 100)

# 5x7 bitmap font: each glyph is 7 rows of 5 cells ('#' = ink).
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "a": (".....", ".....", ".####", "....#", ".####", "#...#", ".###."),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#..#", ".#...", "###..", ".#...", ".#...", ".#..."),
    "g": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": (".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."),
    "j": ("..#..", ".....", "..#..", "..#..", "..#..", "..#..", ".#..."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "###..", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", "#...#", ".####", "....#"),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap(text, max_px, scale):
    """Greedy word wrap; returns a list of lines fitting max_px."""
    lines = []
    cur = ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_px or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def rect(self, x, y, w, h, color):
        r, g, b = color
        for yy in range(y, y + h):
            if yy < 0 or yy >= self.h:
                continue
            for xx in range(w):
                if x + xx < 0 or x + xx >= self.w:
                    continue
                i = (yy * self.w + x + xx) * 3
                self.px[i] = r
                self.px[i + 1] = g
                self.px[i + 2] = b

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT["?"])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale

    def centred(self, y, s, scale, color):
        self.text((self.w - text_width(s, scale)) // 2, y, s, scale, color)


def write_png(path, w, h, px):
    raw = b"".join(b"\x00" + bytes(px[y * w * 3:(y + 1) * w * 3])
                   for y in range(h))

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


LEAD = (
    "TECHNOLOGY",
    "HUANG RETURNS TO NVIDIA",
    "Nvidia's board reinstated Jensen Huang as chief executive on Monday, "
    "only 11 days after he resigned over revelations of extramarital "
    "affairs, including one with a woman US authorities suspect of spying "
    "for China. The U-turn followed direct intervention by President Trump.",
)

GRID_TOP = [
    ("CLIMATE",
     "COP31 COLLAPSES OVER FOSSIL FUELS",
     "Global climate talks in Turkey broke down after countries failed to "
     "agree on moving away from fossil fuels, leaving the summit with no "
     "deal on finance or implementation."),
    ("UKRAINE WAR",
     "KYIV SAYS IT SANK RUSSIAN WARSHIP",
     "Ukraine claimed it sank a Russian warship and damaged a cargo vessel "
     "off Libya's Benghazi port, a long-range strike far from the front. "
     "Russia vowed a response."),
]

GRID_BOTTOM = [
    ("MIDDLE EAST",
     "IRAN SQUEEZED AS US TIGHTENS GRIP",
     "Iran stepped up attacks on US bases and Gulf sites while a US naval "
     "blockade and sanctions squeeze its economy. Tehran began rationing "
     "electricity as the power grid strains."),
    ("EUROPE",
     "EU PROPOSES 22ND RUSSIA SANCTIONS",
     "The European Commission proposed a 22nd sanctions package against "
     "Russia, targeting banks, crypto platforms and ex-combatants, and "
     "barring Russian teams from competing under their flag."),
    ("MEXICO",
     "MEXICO NABS 'EL CHAPO ISIDRO'",
     "Mexican forces captured the alleged drug lord known as 'El Chapo "
     "Isidro', who will face trial at home rather than extradition."),
]


def story_block(c, x, y, w, kicker, headline, body, head_scale,
                body_scale, head_leading, body_leading, max_body_lines):
    c.text(x, y, kicker, 1, RED)
    y += 7 + 10
    for line in wrap(headline, w, head_scale):
        c.text(x, y, line, head_scale, INK)
        y += head_leading
    y += 4
    lines = wrap(body, w, body_scale)[:max_body_lines]
    for line in lines:
        c.text(x, y, line, body_scale, INK)
        y += body_leading
    return y


def render():
    c = Canvas(W, H, PAPER)
    # Masthead.
    c.centred(44, "THE WORLD TODAY", 5, INK)
    c.centred(102, "TUESDAY, 24 NOVEMBER 2026", 2, GREY)
    c.rect(40, 138, 944, 3, INK)
    c.rect(40, 145, 944, 1, INK)
    # Lead story, full width.
    kicker, headline, body = LEAD
    c.text(40, 168, kicker, 2, RED)
    c.text(40, 200, headline, 4, INK)
    y = 248
    for line in wrap(body, 944, 2):
        c.text(40, y, line, 2, INK)
        y += 20
    c.rect(40, 348, 944, 1, INK)
    # Second row: two stories side by side.
    col_w = (944 - 24) // 2
    story_block(c, 40, 368, col_w, *GRID_TOP[0], 3, 2, 26, 20, 5)
    story_block(c, 40 + col_w + 24, 368, col_w, *GRID_TOP[1], 3, 2, 26, 20, 5)
    c.rect(40, 596, 944, 1, INK)
    # Third row: three stories side by side.
    col3 = (944 - 48) // 3
    x = 40
    for story in GRID_BOTTOM:
        story_block(c, x, 616, col3, *story, 2, 1, 18, 11, 5)
        x += col3 + 24
    # The day in one line: a single-sentence summary of the front page.
    c.rect(40, 820, 944, 1, INK)
    c.text(40, 836, "THE DAY IN ONE LINE", 1, RED)
    y = 862
    for line in wrap(
            "A chief executive returns, a climate summit fails, a warship "
            "sinks far from home, and a drug lord is caught.", 944, 2):
        c.text(40, y, line, 2, INK)
        y += 20
    # Footer.
    c.rect(40, 940, 944, 1, INK)
    c.centred(956, "THE WORLD TODAY - TUESDAY, 24 NOVEMBER 2026", 1, GREY)
    return c


def main():
    out_dir = "/output"
    os.makedirs(out_dir, exist_ok=True)
    for name in os.listdir(out_dir):
        path = os.path.join(out_dir, name)
        if os.path.isfile(path):
            os.remove(path)
    canvas = render()
    write_png(os.path.join(out_dir, "entry.png"), W, H, canvas.px)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
