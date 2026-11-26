#!/usr/bin/env python3
"""THE DAILY ORBIT - one page of world news as a single image.

Built for make.fun's news-image-20261126: the program draws a one-page
newspaper of Thursday 26 November 2026 and writes it to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

Pure Python standard library: the page is rasterised by hand into an RGB
buffer and encoded as a PNG with zlib, so two runs always produce the
same bytes.

NOTE ON THE NEWS DATA: the stories in the NEWS DATA block below are a
stand-in assembled from the main headlines of 24 November 2026. They hold
the layout while the page is built; in the final pass, before the last
submission, the whole block is swapped for the verified news of
26 November 2026.
"""

import math
import os
import struct
import zlib

# --------------------------------------------------------------------------
# NEWS DATA (placeholder: 24 November 2026 headlines - swap for 26 Nov final)
# --------------------------------------------------------------------------

PAPER_NAME = "THE DAILY ORBIT"
DATE_LINE = "THURSDAY - 26 NOVEMBER 2026"
VOL_LINE = "VOL. I - No. 26"
TAG_LINE = "ONE PAGE - ONE DAY"

LEAD = {
    "kicker": "EUROPE - WAR IN UKRAINE",
    "headline": "RUSSIAN STRIKES KILL AT LEAST 14 NEAR KYIV",
    "summary": "A FIVE-STOREY HOME COLLAPSED IN DYMER. RESCUERS KEPT "
               "DIGGING THROUGH THE RUBBLE AS THE TOLL ROSE.",
}

PANELS = [
    {
        "kicker": "BUSINESS - TECH",
        "color": (14, 124, 102),
        "icon": "chip",
        "headline": "NVIDIA REINSTATES HUANG AS CEO",
        "summary": "BACK AT THE TOP JOB. SHARES LEAPT 31.5% IN A DAY.",
    },
    {
        "kicker": "CLIMATE",
        "color": (194, 81, 10),
        "icon": "globe",
        "headline": "COP31 TALKS COLLAPSE, NO DEAL",
        "summary": "THE EU REJECTED A FINAL TEXT THAT DROPPED FOSSIL FUELS.",
    },
    {
        "kicker": "AMERICA",
        "color": (91, 62, 153),
        "icon": "dome",
        "headline": "DEMOCRATS WIN 258 HOUSE SEATS",
        "summary": "THE BIGGEST MAJORITY SINCE 1992. THE SENATE FELL TOO.",
    },
    {
        "kicker": "ASIA - INDONESIA",
        "color": (185, 122, 15),
        "icon": "factory",
        "headline": "FACTORY FIRE KILLS AT LEAST 26",
        "summary": "THE TOLL ROSE AT THE BANTEN CANDY FACTORY. 8 MISSING.",
    },
]

TICKER_LABEL = "ALSO TODAY"
TICKER_TEXT = "OREGON AND VIRGINIA SUE SPACEX OVER SEXUALISED GROK AI IMAGES"

# --------------------------------------------------------------------------
# Colours
# --------------------------------------------------------------------------

PAPER = (248, 246, 241)
INK = (20, 22, 26)
SOFT = (58, 63, 71)
RED = (179, 32, 42)
WHITE = (250, 249, 246)

W, H = 1024, 1024

# --------------------------------------------------------------------------
# Stroke font. Glyphs live on a grid 9 units tall (cap height), drawn as
# polylines in y-up space (baseline 0, cap top 9) and flipped when built.
# An arc helper samples ellipses so letters with bowls stay smooth.
# --------------------------------------------------------------------------


def _arc(cx, cy, rx, ry, a0, a1, n=None):
    if n is None:
        n = max(6, int(abs(a1 - a0) / 9))
    pts = []
    for i in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
    return pts


def _build_glyphs():
    g = {}
    # width, list of polylines (each a list of (x, y) in y-up units)
    g["A"] = (5.6, [[(0.3, 0), (2.8, 9), (5.3, 0)], [(1.35, 3.4), (4.25, 3.4)]])
    g["B"] = (5.4, [[(0.7, 0), (0.7, 9)],
                    [(0.7, 9), (2.2, 9)] + _arc(2.2, 6.6, 1.95, 2.4, 90, -90),
                    [(0.7, 4.2), (2.35, 4.2)] + _arc(2.35, 2.1, 2.1, 2.1, 90, -90),
                    [(0.7, 0), (2.35, 0)]])
    g["C"] = (5.8, [_arc(3.0, 4.5, 2.55, 4.5, 55, 305)])
    g["D"] = (5.8, [[(0.7, 0), (0.7, 9)],
                    [(0.7, 9), (2.2, 9)] + _arc(2.2, 4.5, 2.75, 4.5, 90, -90)
                    + [(0.7, 0)]])
    g["E"] = (4.9, [[(4.4, 9), (0.7, 9), (0.7, 0), (4.4, 0)],
                    [(0.7, 4.5), (3.7, 4.5)]])
    g["F"] = (4.7, [[(0.7, 0), (0.7, 9), (4.4, 9)], [(0.7, 4.5), (3.5, 4.5)]])
    g["G"] = (6.0, [_arc(3.05, 4.5, 2.6, 4.5, 55, 385),
                    [(3.2, 4.1), (5.5, 4.1), (5.5, 1.5)]])
    g["H"] = (5.8, [[(0.7, 0), (0.7, 9)], [(5.1, 0), (5.1, 9)],
                    [(0.7, 4.5), (5.1, 4.5)]])
    g["I"] = (2.8, [[(1.4, 0), (1.4, 9)], [(0.3, 9), (2.5, 9)],
                    [(0.3, 0), (2.5, 0)]])
    g["J"] = (4.6, [[(3.8, 9), (3.8, 2.6)] + _arc(2.15, 2.6, 1.65, 2.6, 0, -180)
                    + [(0.5, 3.6)]])
    g["K"] = (5.4, [[(0.7, 0), (0.7, 9)], [(4.9, 9), (1.0, 4.1), (5.1, 0)]])
    g["L"] = (4.7, [[(0.7, 9), (0.7, 0), (4.4, 0)]])
    g["M"] = (6.8, [[(0.5, 0), (0.5, 9), (3.4, 3.8), (6.3, 9), (6.3, 0)]])
    g["N"] = (6.0, [[(0.6, 0), (0.6, 9), (5.4, 0), (5.4, 9)]])
    g["O"] = (6.2, [_arc(3.1, 4.5, 2.7, 4.5, 0, 360)])
    g["P"] = (5.4, [[(0.7, 0), (0.7, 9)],
                    [(0.7, 9), (2.2, 9)] + _arc(2.2, 6.6, 2.05, 2.4, 90, -90)
                    + [(0.7, 4.2)]])
    g["Q"] = (6.2, [_arc(3.1, 4.5, 2.7, 4.5, 0, 360), [(3.6, 1.9), (5.9, -0.7)]])
    g["R"] = (5.4, [[(0.7, 0), (0.7, 9)],
                    [(0.7, 9), (2.2, 9)] + _arc(2.2, 6.6, 2.05, 2.4, 90, -90)
                    + [(0.7, 4.2)], [(2.7, 4.2), (5.1, 0)]])
    g["S"] = (5.4, [_arc(2.7, 6.4, 2.0, 2.4, 30, 250)
                    + _arc(2.7, 2.5, 2.0, 2.4, 110, -145)])
    g["T"] = (5.4, [[(0.3, 9), (5.1, 9)], [(2.7, 9), (2.7, 0)]])
    g["U"] = (5.8, [[(0.6, 9), (0.6, 2.7)] + _arc(2.9, 2.7, 2.3, 2.7, 180, 360)
                    + [(5.2, 9)]])
    g["V"] = (5.6, [[(0.3, 9), (2.8, 0), (5.3, 9)]])
    g["W"] = (7.4, [[(0.3, 9), (1.7, 0), (3.7, 6.6), (5.7, 0), (7.1, 9)]])
    g["X"] = (5.4, [[(0.5, 9), (4.9, 0)], [(0.5, 0), (4.9, 9)]])
    g["Y"] = (5.6, [[(0.3, 9), (2.8, 4.6), (5.3, 9)], [(2.8, 4.6), (2.8, 0)]])
    g["Z"] = (5.4, [[(0.5, 9), (4.9, 9), (0.5, 0), (4.9, 0)]])
    g["0"] = (5.4, [_arc(2.7, 4.5, 2.15, 4.5, 0, 360)])
    g["1"] = (4.0, [[(1.0, 6.8), (2.3, 9), (2.3, 0)], [(0.9, 0), (3.7, 0)]])
    g["2"] = (5.4, [_arc(2.7, 6.7, 2.05, 2.3, 190, -60) + [(0.6, 0), (4.8, 0)]])
    g["3"] = (5.4, [[(0.8, 9), (2.3, 9)] + _arc(2.3, 6.7, 1.95, 2.3, 90, -90)
                    + _arc(2.35, 2.2, 2.1, 2.2, 90, -90)])
    g["4"] = (5.6, [[(3.8, 0), (3.8, 9), (0.6, 2.2), (5.3, 2.2)]])
    g["5"] = (5.4, [[(4.6, 9), (0.8, 9), (0.8, 5.7)]
                    + _arc(2.5, 3.2, 2.1, 2.4, 100, -165)])
    g["6"] = (5.4, [[(4.5, 7.9)] + _arc(2.7, 2.9, 2.1, 2.9, 72, 432)])
    g["7"] = (5.4, [[(0.6, 9), (4.8, 9), (2.3, 0)]])
    g["8"] = (5.4, [_arc(2.7, 6.8, 1.8, 2.2, 0, 360),
                    _arc(2.7, 2.5, 2.1, 2.5, 0, 360)])
    g["9"] = (5.4, [_arc(2.7, 6.1, 2.1, 2.9, 0, 360),
                    [(4.8, 6.1), (4.7, 2.8)] + _arc(3.5, 1.7, 1.2, 1.7, 90, 205)])
    g["."] = (2.2, [_arc(1.1, 0.55, 0.55, 0.55, 0, 360)])
    g[","] = (2.2, [_arc(1.1, 0.95, 0.5, 0.5, 0, 360), [(1.5, 0.7), (1.0, -1.0)]])
    g["'"] = (1.9, [[(1.25, 9), (0.85, 6.4)]])
    g['"'] = (3.4, [[(0.95, 9), (0.6, 6.4)], [(2.6, 9), (2.25, 6.4)]])
    g["-"] = (4.0, [[(0.6, 4.3), (3.4, 4.3)]])
    g["|"] = (6.4, [[(0.4, 4.3), (6.0, 4.3)]])  # used as an em dash
    g[":"] = (2.2, [_arc(1.1, 7.4, 0.52, 0.52, 0, 360),
                    _arc(1.1, 1.5, 0.52, 0.52, 0, 360)])
    g["!"] = (2.2, [[(1.1, 9), (1.1, 2.3)], _arc(1.1, 0.55, 0.52, 0.52, 0, 360)])
    g["?"] = (5.0, [_arc(2.5, 6.7, 1.95, 2.3, 170, -80) + [(2.5, 3.1), (2.5, 2.1)],
                    _arc(2.5, 0.55, 0.52, 0.52, 0, 360)])
    g["%"] = (5.6, [_arc(1.25, 7.5, 0.95, 1.1, 0, 360),
                    _arc(4.35, 1.5, 0.95, 1.1, 0, 360),
                    [(4.7, 9.2), (0.9, -0.2)]])
    g["/"] = (5.0, [[(4.3, 9.4), (0.7, -0.4)]])
    g["+"] = (5.2, [[(2.6, 1.9), (2.6, 7.1)], [(0.5, 4.5), (4.7, 4.5)]])
    g["("] = (2.8, [_arc(3.6, 4.7, 2.0, 5.4, 112, 248)])
    g[")"] = (2.8, [_arc(0.4, 4.7, 2.0, 5.4, 68, -68)])
    # flip y-up into screen space (cap top = 0, baseline = 9)
    out = {}
    for ch, (w, lines) in g.items():
        flipped = [[(x, 9.0 - y) for (x, y) in line] for line in lines]
        out[ch] = (w, flipped)
    return out


GLYPHS = _build_glyphs()
SPACE_W = 3.1


def _clean(text):
    return (text.replace("\u2019", "'").replace("\u2018", "'")
            .replace("\u2014", "|").replace("\u2013", "-")
            .replace("\u00b7", ".").upper())


def text_width(text, cap, weight, tracking=0.55):
    """Width in pixels of a string at the given cap height."""
    scale = cap / 9.0
    total = 0.0
    for ch in _clean(text):
        if ch == " ":
            total += SPACE_W
        elif ch in GLYPHS:
            total += GLYPHS[ch][0]
        else:
            total += SPACE_W
        total += tracking
    return total * scale


# --------------------------------------------------------------------------
# Canvas
# --------------------------------------------------------------------------


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(bg) * (w * h))
        self._tiles = {}

    def blend_px(self, x, y, color, a):
        if a <= 0.0 or x < 0 or y < 0 or x >= self.w or y >= self.h:
            return
        i = (y * self.w + x) * 3
        if a >= 1.0:
            self.buf[i:i + 3] = bytes(color)
        else:
            b = self.buf
            b[i] = int(b[i] + (color[0] - b[i]) * a)
            b[i + 1] = int(b[i + 1] + (color[1] - b[i + 1]) * a)
            b[i + 2] = int(b[i + 2] + (color[2] - b[i + 2]) * a)

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, int(x0)); y0 = max(0, int(y0))
        x1 = min(self.w, int(x1)); y1 = min(self.h, int(y1))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def fill_circle(self, cx, cy, r, color):
        x0 = int(cx - r - 1); x1 = int(cx + r + 2)
        y0 = int(cy - r - 1); y1 = int(cy + r + 2)
        for y in range(y0, y1):
            for x in range(x0, x1):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                self.blend_px(x, y, color, min(1.0, r - d + 0.5))

    def fill_poly(self, pts, color):
        ys = [p[1] for p in pts]
        y0 = max(0, int(min(ys))); y1 = min(self.h - 1, int(max(ys)) + 1)
        n = len(pts)
        for y in range(y0, y1 + 1):
            yc = y + 0.5
            xs = []
            for i in range(n):
                xa, ya = pts[i]
                xb, yb = pts[(i + 1) % n]
                if (ya <= yc < yb) or (yb <= yc < ya):
                    xs.append(xa + (yc - ya) * (xb - xa) / (yb - ya))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[i]), y, int(xs[i + 1]) + 1, y + 1, color)

    def stroke(self, pts, color, width_px):
        """Draw a polyline with round caps and distance-based soft edges."""
        if len(pts) == 1:
            pts = [pts[0], pts[0]]
        half = width_px / 2.0
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        x0 = int(min(xs) - half - 1); x1 = int(max(xs) + half + 2)
        y0 = int(min(ys) - half - 1); y1 = int(max(ys) + half + 2)
        segs = list(zip(pts, pts[1:]))
        for y in range(y0, y1):
            for x in range(x0, x1):
                px, py = x + 0.5, y + 0.5
                best = 1e9
                for (ax, ay), (bx, by) in segs:
                    dx, dy = bx - ax, by - ay
                    ll = dx * dx + dy * dy
                    if ll == 0:
                        t = 0.0
                    else:
                        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / ll))
                    d = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
                    if d < best:
                        best = d
                self.blend_px(x, y, color, min(1.0, half - best + 0.5))

    # -- text ---------------------------------------------------------------

    def _glyph_tile(self, ch, cap, weight):
        key = (ch, round(cap, 1), round(weight, 2))
        if key in self._tiles:
            return self._tiles[key]
        scale = cap / 9.0
        w_units, lines = GLYPHS[ch]
        half = weight * scale / 2.0
        pad = half + 1.5
        tw = int(w_units * scale + 2 * pad) + 1
        th = int(11.5 * scale + 2 * pad) + 1  # room for descenders
        yoff = 1.0 * scale + pad  # cap top sits 1 unit below tile top
        alpha = bytearray(tw * th)
        for line in lines:
            pts = [(x * scale + pad, y * scale + yoff) for (x, y) in line]
            if len(pts) == 1:
                pts = [pts[0], pts[0]]
            segs = list(zip(pts, pts[1:]))
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            x0 = max(0, int(min(xs) - half - 1)); x1 = min(tw, int(max(xs) + half + 2))
            y0 = max(0, int(min(ys) - half - 1)); y1 = min(th, int(max(ys) + half + 2))
            for yy in range(y0, y1):
                for xx in range(x0, x1):
                    px, py = xx + 0.5, yy + 0.5
                    best = 1e9
                    for (ax, ay), (bx, by) in segs:
                        dx, dy = bx - ax, by - ay
                        ll = dx * dx + dy * dy
                        if ll == 0:
                            t = 0.0
                        else:
                            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / ll))
                        d = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
                        if d < best:
                            best = d
                    cov = min(1.0, half - best + 0.5)
                    if cov > 0:
                        idx = yy * tw + xx
                        v = int(cov * 255)
                        if v > alpha[idx]:
                            alpha[idx] = v
        tile = (alpha, tw, th, pad, yoff)
        self._tiles[key] = tile
        return tile

    def draw_text(self, text, x, y_top, cap, color, weight=1.25, tracking=0.55):
        """Draw text with its cap top at y_top; returns the end x."""
        scale = cap / 9.0
        cx = float(x)
        for ch in _clean(text):
            if ch == " ":
                cx += (SPACE_W + tracking) * scale
                continue
            if ch not in GLYPHS:
                cx += (SPACE_W + tracking) * scale
                continue
            alpha, tw, th, pad, yoff = self._glyph_tile(ch, cap, weight)
            gx = int(cx - pad)
            gy = int(y_top - yoff + 1.0 * scale)
            for yy in range(th):
                ty = gy + yy
                if ty < 0 or ty >= self.h:
                    continue
                base = yy * tw
                for xx in range(tw):
                    a = alpha[base + xx]
                    if a:
                        self.blend_px(gx + xx, ty, color, a / 255.0)
            cx += (GLYPHS[ch][0] + tracking) * scale
        return cx

    def draw_text_centered(self, text, cx, y_top, cap, color, weight=1.25,
                           tracking=0.55):
        w = text_width(text, cap, weight, tracking)
        return self.draw_text(text, cx - w / 2.0, y_top, cap, color, weight,
                              tracking)


def wrap_text(text, cap, weight, max_w, tracking=0.55):
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, cap, weight, tracking) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_lines(text, cap, weight, max_w, max_lines, tracking=0.55):
    """Wrap at cap size, shrinking until the text fits max_lines."""
    while cap > 8:
        lines = wrap_text(text, cap, weight, max_w, tracking)
        if len(lines) <= max_lines:
            return lines, cap
        cap -= 2
    return wrap_text(text, cap, weight, max_w, tracking), cap


# --------------------------------------------------------------------------
# Scene: a night skyline under attack, drawn with flat shapes
# --------------------------------------------------------------------------


def draw_scene(cv, x0, y0, x1, y1):
    h = y1 - y0
    # sky: vertical gradient, indigo down to a dull orange horizon glow
    top = (24, 29, 58)
    mid = (43, 36, 62)
    low = (112, 58, 44)
    for i in range(h):
        t = i / max(1, h - 1)
        if t < 0.62:
            u = t / 0.62
            c = tuple(int(top[k] + (mid[k] - top[k]) * u) for k in range(3))
        else:
            u = (t - 0.62) / 0.38
            c = tuple(int(mid[k] + (low[k] - mid[k]) * u) for k in range(3))
        cv.fill_rect(x0, y0 + i, x1, y0 + i + 1, c)
    # stars: a sparse deterministic scatter in the upper half
    for i in range(46):
        sx = x0 + (i * 173) % (x1 - x0 - 8) + 4
        sy = y0 + (i * 37) % int(h * 0.45) + 5
        cv.fill_rect(sx, sy, sx + 2, sy + 2, (198, 206, 226))
    # moon
    cv.fill_circle(x1 - 92, y0 + 34, 17, (236, 228, 204))
    cv.fill_circle(x1 - 99, y0 + 29, 14, (35, 38, 66))
    # far skyline: a row of lighter blocks on a raised baseline
    far = [(0, 64, 34), (72, 52, 52), (132, 70, 28), (210, 48, 60),
           (266, 66, 38), (340, 54, 48), (402, 72, 30), (482, 50, 56),
           (540, 68, 36), (616, 52, 50), (676, 64, 32), (748, 56, 54),
           (812, 70, 40), (890, 54, 46)]
    for (dx, bw, bh) in far:
        cv.fill_rect(x0 + dx, y1 - 22 - bh, x0 + dx + bw, y1 - 22,
                     (30, 34, 58))
    # explosion: a starburst over the middle-right of the skyline
    ex, ey = x0 + int((x1 - x0) * 0.62), y0 + int(h * 0.40)
    star = []
    for i in range(16):
        ang = math.pi * i / 8.0
        r = 37 if i % 2 == 0 else 15
        star.append((ex + r * math.cos(ang), ey + r * math.sin(ang)))
    cv.fill_poly(star, (232, 106, 30))
    star2 = []
    for i in range(16):
        ang = math.pi * i / 8.0 + 0.2
        r = 21 if i % 2 == 0 else 8
        star2.append((ex + r * math.cos(ang), ey + r * math.sin(ang)))
    cv.fill_poly(star2, (245, 185, 63))
    # smoke: soft grey puffs drifting up-left from the burst, kept in frame
    for (dx, dy, r) in [(-14, -20, 10), (-32, -32, 13), (-54, -40, 16),
                        (-80, -44, 18), (8, -26, 8)]:
        cv.fill_circle(ex + dx, max(y0 + r + 2, ey + dy), r, (120, 116, 122))
    # near skyline: black blocks with lit windows
    near = [(0, 96, 74), (84, 96, 58), (176, 96, 84), (292, 96, 64),
            (388, 96, 92), (512, 96, 70), (616, 96, 88), (736, 96, 60),
            (828, 96, 78)]
    for (dx, bw, bh) in near:
        bx = x0 + dx
        cv.fill_rect(bx, y1 - bh, bx + bw, y1, (9, 10, 17))
        for wy in range(10, bh - 8, 15):
            for wx in range(8, bw - 8, 14):
                if (wx * 7 + wy * 13 + dx) % 5 < 2:
                    cv.fill_rect(bx + wx, y1 - bh + wy, bx + wx + 5,
                                 y1 - bh + wy + 7, (232, 163, 61))
    cv.fill_rect(x0, y1 - 4, x1, y1, (9, 10, 17))


# --------------------------------------------------------------------------
# Panel icons: small line drawings in the panel's colour
# --------------------------------------------------------------------------


def draw_icon(cv, kind, x, y, color):
    s = 36.0  # box size in px
    wdt = 3.0
    if kind == "chip":
        cv.stroke([(x + 9, y + 9), (x + 27, y + 9), (x + 27, y + 27),
                   (x + 9, y + 27), (x + 9, y + 9)], color, wdt)
        cv.stroke([(x + 15, y + 15), (x + 21, y + 15), (x + 21, y + 21),
                   (x + 15, y + 21), (x + 15, y + 15)], color, wdt)
        for t in (13, 18, 23):
            cv.stroke([(x + t, y + 2), (x + t, y + 9)], color, wdt)
            cv.stroke([(x + t, y + 27), (x + t, y + 34)], color, wdt)
            cv.stroke([(x + 2, y + t), (x + 9, y + t)], color, wdt)
            cv.stroke([(x + 27, y + t), (x + 34, y + t)], color, wdt)
    elif kind == "globe":
        pts = [(x + 18 + 15 * math.cos(math.radians(a)),
                y + 18 + 15 * math.sin(math.radians(a))) for a in range(0, 361, 10)]
        cv.stroke(pts, color, wdt)
        pts = [(x + 18 + 6.5 * math.cos(math.radians(a)),
                y + 18 + 15 * math.sin(math.radians(a))) for a in range(0, 361, 10)]
        cv.stroke(pts, color, wdt)
        cv.stroke([(x + 3, y + 18), (x + 33, y + 18)], color, wdt)
    elif kind == "dome":
        pts = [(x + 18 + 14 * math.cos(math.radians(a)),
                y + 20 + 13 * math.sin(math.radians(a)))
               for a in range(180, 361, 9)]
        cv.stroke(pts, color, wdt)
        cv.stroke([(x + 18, y + 7), (x + 18, y + 2)], color, wdt)
        cv.stroke([(x + 3, y + 21), (x + 33, y + 21)], color, wdt)
        cv.stroke([(x + 2, y + 27), (x + 34, y + 27)], color, wdt)
        for t in (9, 15, 21, 27):
            cv.stroke([(x + t, y + 21), (x + t, y + 27)], color, wdt)
        cv.stroke([(x + 2, y + 33), (x + 34, y + 33)], color, wdt)
    elif kind == "factory":
        cv.stroke([(x + 3, y + 33), (x + 3, y + 15), (x + 12, y + 20),
                   (x + 21, y + 15), (x + 30, y + 20), (x + 30, y + 33),
                   (x + 3, y + 33)], color, wdt)
        cv.stroke([(x + 24, y + 17), (x + 24, y + 4), (x + 29, y + 4),
                   (x + 29, y + 18)], color, wdt)
        cv.fill_rect(x + 9, y + 25, x + 13, y + 29, color)
        cv.fill_rect(x + 18, y + 25, x + 22, y + 29, color)
    else:
        cv.fill_circle(x + 18, y + 18, 6, color)
    _ = s


# --------------------------------------------------------------------------
# Page layout
# --------------------------------------------------------------------------

M = 40
CW = W - 2 * M


def build_page():
    cv = Canvas(W, H, PAPER)

    # masthead block
    cv.fill_rect(M, 26, W - M, 29, INK)
    cv.fill_rect(M, 33, W - M, 34, INK)
    cv.draw_text_centered(PAPER_NAME, W // 2, 44, 72, INK, weight=1.7,
                          tracking=0.7)
    cv.fill_rect(M, 126, W - M, 130, RED)
    # dateline row
    cv.draw_text(VOL_LINE, M, 140, 20, SOFT, weight=1.2)
    cv.draw_text_centered(DATE_LINE, W // 2, 138, 22, INK, weight=1.6)
    tw = text_width(TAG_LINE, 20, 1.2)
    cv.draw_text(TAG_LINE, W - M - tw, 140, 20, SOFT, weight=1.2)
    cv.fill_rect(M, 170, W - M, 172, INK)

    # lead story
    cv.fill_rect(M, 184, M + 14, 198, RED)
    cv.draw_text(LEAD["kicker"], M + 22, 182, 24, RED, weight=1.55)
    lines, cap = fit_lines(LEAD["headline"], 76, 1.6, CW, 2)
    y = 216
    for ln in lines:
        cv.draw_text(ln, M, y, cap, INK, weight=1.6)
        y += int(cap * 1.28)
    scene_y0 = y + 12
    scene_y1 = scene_y0 + 110
    draw_scene(cv, M, scene_y0, W - M, scene_y1)
    lines, cap = fit_lines(LEAD["summary"], 24, 1.2, CW, 2)
    y = scene_y1 + 12
    for ln in lines:
        cv.draw_text(ln, M, y, cap, SOFT, weight=1.2)
        y += int(cap * 1.22)
    lead_end = y

    # ticker strip
    tick_y = lead_end + 10
    cv.fill_rect(M, tick_y, W - M, tick_y + 44, INK)
    lx = cv.draw_text(TICKER_LABEL, M + 16, tick_y + 10, 22, (245, 185, 63),
                      weight=1.6)
    rest_w = (W - M - 14) - (lx + 14)
    tlines, tcap = fit_lines(TICKER_TEXT, 20, 1.3, rest_w, 1)
    cv.draw_text(tlines[0], lx + 14, tick_y + 11, tcap, WHITE, weight=1.3)

    # panels: two columns, two rows
    grid_y = tick_y + 44 + 16
    col_w = (CW - 32) // 2
    row_h = (H - 16 - grid_y) // 2
    for i, panel in enumerate(PANELS):
        px = M + (i % 2) * (col_w + 32)
        py = grid_y + (i // 2) * row_h
        color = panel["color"]
        cv.fill_rect(px, py, px + col_w, py + 4, color)
        cv.draw_text(panel["kicker"], px, py + 10, 18, color, weight=1.55)
        draw_icon(cv, panel["icon"], px + col_w - 38, py + 6, color)
        lines, cap = fit_lines(panel["headline"], 35, 1.55, col_w, 2)
        yy = py + 36
        for ln in lines:
            cv.draw_text(ln, px, yy, cap, INK, weight=1.55)
            yy += int(cap * 1.22)
        lines, cap = fit_lines(panel["summary"], 19, 1.2, col_w, 2)
        yy += 4
        for ln in lines:
            cv.draw_text(ln, px, yy, cap, SOFT, weight=1.2)
            yy += int(cap * 1.18)
    return cv


# --------------------------------------------------------------------------
# PNG encoding (deterministic: fixed filter, zlib level 9)
# --------------------------------------------------------------------------


def write_png(path, cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", comp)
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build_page()
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path, cv)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
