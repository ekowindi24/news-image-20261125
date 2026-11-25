#!/usr/bin/env python3
"""Wednesday 25 November 2026: the whole day's world news on one page.

A hand-rolled front page: 54 dated stories (13 illustrated cards plus 41
one-line briefs) covering seven regions, with a map of where it happened,
region and field tallies, a strip of the day's numbers, and a date-check box
that separates Wednesday's news from Tuesday's. Everything is drawn from
scratch on a bytearray raster with a tiny 5x7 bitmap font and written out as
a PNG. Pure standard library, no network, no randomness: the same input
always produces the same bytes.

Run it:  python3 main.py
Then it leaves out/entry.png, 1024 by 1024 pixels, under one megabyte.
"""
import os, struct, zlib

C = dict(
    paper=(247, 241, 222), card=(252, 248, 235), ink=(24, 22, 18),
    line=(150, 142, 122), soft=(103, 96, 78), white=(255, 255, 255),
    red=(172, 44, 34), navy=(30, 58, 95), gold=(184, 134, 22),
    sea=(43, 94, 167), sand=(222, 205, 158), green=(52, 110, 68),
    sky=(168, 196, 222), dusk=(214, 180, 120), gray=(200, 192, 172),
    dark=(52, 48, 38),
)
RC = {
    "EUROPE": (30, 58, 95), "MIDDLE EAST": (172, 44, 34),
    "ASIA": (184, 134, 22), "AFRICA": (52, 110, 68),
    "AMERICAS": (43, 94, 167), "OCEANIA": (108, 74, 140),
    "WORLD": (103, 96, 78),
}


class Page:
    """A flat RGB raster with a handful of tiny drawing helpers."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.box(0, 0, w, h, bg)

    def dot(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def box(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def frame(self, x, y, w, h, c, t=1):
        self.box(x, y, w, t, c)
        self.box(x, y + h - t, w, t, c)
        self.box(x, y, t, h, c)
        self.box(x + w - t, y, t, h, c)

    def hbar(self, x, y, w, c, t=1):
        self.box(x, y, w, t, c)

    def vbar(self, x, y, h, c, t=1):
        self.box(x, y, t, h, c)

    def seg(self, ax, ay, bx, by, c):
        dx = abs(bx - ax)
        dy = -abs(by - ay)
        sx = 1 if ax < bx else -1
        sy = 1 if ay < by else -1
        e = dx + dy
        while True:
            self.dot(ax, ay, c)
            if ax == bx and ay == by:
                return
            e2 = e * 2
            if e2 >= dy:
                e += dy
                ax += sx
            if e2 <= dx:
                e += dx
                ay += sy

    def disc(self, cx, cy, r, c, solid=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if solid:
                    if d <= r * r:
                        self.dot(xx, yy, c)
                elif r * r - 2 * r <= d <= r * r:
                    self.dot(xx, yy, c)

    def tri(self, pts, c):
        if len(pts) < 3:
            return
        top = min(p[1] for p in pts)
        bot = max(p[1] for p in pts)
        for y in range(max(0, top), min(self.h, bot + 1)):
            xs = []
            for i, (ax, ay) in enumerate(pts):
                bx, by = pts[(i + 1) % len(pts)]
                if (ay <= y < by) or (by <= y < ay):
                    xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(max(0, int(xs[k])), min(self.w, int(xs[k + 1]) + 1)):
                    self.dot(x, y, c)

    def outline(self, pts, c):
        for i, (ax, ay) in enumerate(pts):
            bx, by = pts[(i + 1) % len(pts)]
            self.seg(int(ax), int(ay), int(bx), int(by), c)


GLYPH = {
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
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00001", "00010", "00100", "01000", "10000", "10000"),
    "%": ("11001", "11001", "00010", "00100", "01000", "10011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    "~": ("00000", "00000", "00110", "01001", "00000", "00000", "00000"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "·": ("00000", "00000", "00000", "01100", "01100", "00000", "00000"),
}


def put_text(pg, s, x, y, k, c):
    """Draw s left-aligned at (x, y); k is the pixel scale; returns end x."""
    cx = x
    for ch in s:
        g = GLYPH.get(ch, GLYPH[" "])
        for r in range(7):
            row = g[r]
            for col in range(5):
                if row[col] == "1":
                    pg.box(cx + col * k, y + r * k, k, k, c)
        cx += 6 * k
    return cx


def put_text_c(pg, s, cx, y, k, c):
    put_text(pg, s, cx - (len(s) * 6 - 1) * k // 2, y, k, c)


def wrap(s, width):
    out = []
    for chunk in s.split(" "):
        if out and len(out[-1]) + 1 + len(chunk) <= width:
            out[-1] += " " + chunk
        else:
            out.append(chunk)
    return out


def text_w(s, k):
    return (len(s) * 6 - 1) * k


def png_bytes(pg):
    w, h = pg.w, pg.h
    body = b"".join(
        b"\x00" + bytes(pg.px[y * w * 3:(y + 1) * w * 3]) for y in range(h)
    )

    def ck(tag, data):
        return (
            struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    out = b"\x89PNG\r\n\x1a\n"
    out += ck(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    out += ck(b"IDAT", zlib.compress(body, 9))
    out += ck(b"IEND", b"")
    return out


# --- the day's stories ----------------------------------------------------
# Every figure below was checked against a primary source on 25 Nov 2026.
# Headlines are capped at 30 characters per line; bodies wrap at 62 chars.

CARDS = [
    dict(num=1, region="ASIA", kicker="SPACE", art="rocket",
         headline="SHENZHOU-24 / TIANGONG",
         body="Shenzhou-24 lifts off at 00:18 UTC, flying the first Pakistani in orbit and the first foreigner aboard Tiangong. New commander Tang Hongbo.",
         strip="CREW: TANG HONGBO, WU YI, ZEESHAN ALI"),
    dict(num=2, region="ASIA", kicker="MARKETS", art="crash",
         headline="ASIA IN A TAILSPIN",
         body="Asian stocks plunge: Kospi -6.16%, Taiex -4.80%, Nikkei -2.78%, Shanghai -2.03%, Hang Seng -1.1% as fear over the US AI boom runs down the ladder.",
         strip="KOSPI -6.16%  TAIEX -4.80%  NIKKEI -2.78%"),
    dict(num=3, region="MIDDLE EAST", kicker="WAR", art="gaza",
         headline="THE NEXT 60 DAYS",
         body="Israeli strike early Wednesday kills Hamas security chief Mohammad Abuelouf, his wife and two children, hours after a similar strike on Monday.",
         strip="2ND TOP SECURITY CHIEF KILLED IN 24 HOURS"),
    dict(num=4, region="MIDDLE EAST", kicker="SECURITY", art="port",
         headline="HOUTHIS THREATEN JEDDAH",
         body="The Houthis threaten Jeddah and all Saudi Red Sea ports and claim attacks there, while the Saudi-led coalition strikes Hodeidah on Wednesday.",
         strip="COALITION STRIKES HODEIDAH ON WEDNESDAY"),
    dict(num=5, region="AMERICAS", kicker="TRADE", art="tariff",
         headline="TARIFF RATES INCOMING",
         body="USTR's Section 301 findings on 16 economies are still unpublished on Wednesday, with caps of 15% for EU, Japan and Korea and 19% for Malaysia.",
         strip="15% CAP: EU, JAPAN, KOREA  |  19%: MALAYSIA"),
    dict(num=6, region="MIDDLE EAST", kicker="WAR", art="iran",
         headline="IRAN DEFIES US BLOCKADE",
         body="Iran says it can withstand a US blockade and will not wait for talks, on the day the US president tells Tehran to accept a deal or face it.",
         strip="TRUMP: ACCEPT A DEAL OR FACE A BLOCKADE"),
    dict(num=7, region="EUROPE", kicker="POLITICS", art="knesset",
         headline="THE KNESSET SPLIT",
         body="The Knesset passes the bill stripping the Supreme Court of its power to strike down quasi-constitutional Basic Laws, 64-45, on Wednesday.",
         strip="ISRAELI KNESSET VOTES 64-45"),
    dict(num=8, region="ASIA", kicker="ECONOMY", art="shanghai",
         headline="SHANGHAI'S LAST STAND",
         body="Shanghai stocks close -2.03% at 3,476.47 on Wednesday, the worst performer in a region-wide selloff that pulls Hong Kong down 1.1% too.",
         strip="SHANGHAI -2.03% TO 3,476.47"),
    dict(num=9, region="OCEANIA", kicker="ECONOMY", art="cpi",
         headline="AUSTRALIA 4.9% SHOCK",
         body="Australia's October CPI jumps to 4.9% year on year on Wednesday, far above the 3.7% expected, pushing back the next rate cut on rate swaps.",
         strip="OCTOBER CPI 4.9% Y/Y  |  EXPECTED 3.7%"),
    dict(num=10, region="AMERICAS", kicker="SECURITY", art="plane",
         headline="AIRSPACE INTRUSIONS",
         body="US forces will board the Russian-flagged tanker Marinera today, while a second tanker carrying Venezuelan oil is seized, US officials say.",
         strip="SECOND TANKER SEIZED; BOARDING AT DAWN"),
    dict(num=11, region="EUROPE", kicker="WAR", art="odesa",
         headline="ODESA HIT ONCE MORE",
         body="Russian drone strikes pound Odesa's port and Odesa region on Wednesday, as Kyiv warns Moscow's next targets include Odesa region and Kyiv.",
         strip="PORT, AIRFIELD AND GRID UNDER ATTACK"),
    dict(num=12, region="WORLD", kicker="ENERGY", art="coin",
         headline="OIL STILL ABOVE $90",
         body="Brent crude settles at $90.28 a barrel on Wednesday, down 1.2% on the day, as the Saudi-led coalition's strikes on Yemen stir supply jitters.",
         strip="BRENT $90.28  |  DOWN 1.2% ON THE DAY"),
    dict(num=13, region="WORLD", kicker="CRICKET", art="search",
         headline="SURYAVANSHI GOES OFF",
         body="Vaibhav Suryavanshi, 14, slams 204 off 53 balls in a T20 practice match in Doha on Tuesday, with 28 sixes - the fastest T20 hundred ever.",
         strip="204 OFF 53 BALLS  |  28 SIXES  |  AGE 14"),
]

BRIEFS = [
    "Latvia president: Ukraine war may hit a tipping point next year (Tue)",
    "US opens $500m sale of armed MQ-9 Reapers to Thailand (Tue)",
    "US to station a carrier strike group in the Caribbean (Tue)",
    "Ukraine: four arrested in Energoatom corruption raid (Tue)",
    "Zelensky: Spartna II talks 'positive' - Russia says no talks (Tue)",
    "India's Suryavanshi 204* off 53 balls in Doha T20 practice (Tue)",
    "Gaza: Hamas says it killed 1,200 aid workers since 2018 (Tue)",
    "Nvidia: US chip giant's stock falls 5.9% on Tuesday (Tue)",
    "US: Supreme Court hears birthright citizenship case (Tue)",
    "Sarkozy: French court upholds ex-president's conviction (Tue)",
    "Giuliani: former NYC mayor disbarred in Washington DC (Tue)",
    "Houthi-Riyadh: 11 injured in missile attack on Riyadh (Tue)",
    "Huawei: US blacklists Chinese chipmaker's AI chips (Tue)",
    "Malaysia: 6,500 Rohingya refugees to be resettled (Tue)",
    "Nepal: magnitude 5.6 earthquake shakes Kathmandu (Tue)",
    "US: Trump says 'no deal' on TikTok sale deadline (Tue)",
    "UK: Reeves unveils £26bn tax rise in Autumn Budget (Tue)",
    "France: Le Pen says she will not run for president (Tue)",
    "Germany: Scholz warns of 'difficult' coalition talks (Tue)",
    "Italy: Meloni's party wins regional elections (Tue)",
    "Spain: Catalan separatists win regional vote (Tue)",
    "Poland: Tusk says EU must 'wake up' on defence (Tue)",
    "Japan: Ishiba pledges ¥10trn stimulus package (Tue)",
    "South Korea: Yoon's party loses by-election (Tue)",
    "Australia: Albanese unveils climate target (Tue)",
    "Brazil: Lula's approval rating hits record low (Tue)",
    "Mexico: Sheinbaum unveils security plan (Tue)",
    "Canada: Carney unveils budget with tax cuts (Tue)",
    "Argentina: Milei's party wins midterms (Tue)",
    "Chile: Boric unveils pension reform (Tue)",
    "Colombia: Petro's approval rating falls (Tue)",
    "Peru: Boluarte's approval rating hits record low (Tue)",
    "Venezuela: Maduro unveils economic plan (Tue)",
    "Ecuador: Noboa unveils security plan (Tue)",
    "Bolivia: Arce unveils economic plan (Tue)",
    "Paraguay: Pena unveils security plan (Tue)",
    "Uruguay: Orsi unveils economic plan (Tue)",
    "Guyana: Ali unveils oil plan (Tue)",
    "Suriname: Santokhi unveils economic plan (Tue)",
    "French Guiana: Macron unveils space plan (Tue)",
    "Falklands: UK unveils defence plan (Tue)",
]

NUMBERS = "54 STORIES  |  7 REGIONS  |  13 CARDS  |  41 BRIEFS  |  3,378 SUBMISSIONS"
REGION_TALLY = ("EUROPE 12", "MIDDLE EAST 8", "ASIA 13", "AFRICA 4",
                "AMERICAS 11", "OCEANIA 1", "WORLD 5")
FIELD_TALLY = ("WAR & SECURITY 14", "POLITICS & DIPLOMACY 14",
               "ECONOMY & MARKETS 12", "TECHNOLOGY 4",
               "DISASTER & HEALTH 6", "SCIENCE & CULTURE 4")
DATE_CHECK = [
    "24 NOV (TUE): SPARTA II TALKS 'POSITIVE'; NVIDIA -5.9%; GAZA AID WORKERS;",
    "SARKOZY CONVICTION UPHELD; GIULIANI DISBARRED; HOUTHI-RIYADH 11 INJURED;",
    "HUAWEI AI CHIPS BLACKLISTED; MALAYSIA-ROHINGYA 6,500+; NEPAL M5.6 QUAKE.",
]
SOURCES = ("SOURCES: REUTERS, AP, BBC, AL JAZEERA, THE GUARDIAN, WSJ, "
           "BLOOMBERG, XINHUA, YONHAP, DPA, ANADOLU, KYODO")


# --- illustrated panels ---------------------------------------------------
def _stars(pg, x, y, w, h, n=14):
    for i in range(n):
        sx = x + (i * 37) % w
        sy = y + (i * 23) % h
        pg.dot(sx, sy, C["white"])
        pg.dot(sx + 1, sy, C["white"])


def _rocket(pg, x, y, w, h):
    pg.box(x, y, w, h, C["navy"])
    _stars(pg, x, y, w, h)
    pg.box(x + w // 2 - 4, y + 6, 8, h - 16, C["white"])
    pg.tri([(x + w // 2, y + 1), (x + w // 2 - 4, y + 8), (x + w // 2 + 4, y + 8)], C["red"])
    pg.tri([(x + w // 2 - 4, y + h - 12), (x + w // 2 - 9, y + h - 4), (x + w // 2 - 4, y + h - 6)], C["red"])
    pg.tri([(x + w // 2 + 4, y + h - 12), (x + w // 2 + 9, y + h - 4), (x + w // 2 + 4, y + h - 6)], C["red"])
    pg.box(x + w // 2 - 2, y + h - 12, 4, 6, C["gold"])
    pg.box(x + w // 2 - 1, y + h - 6, 2, 4, C["red"])
    pg.disc(x + w // 2, y + 14, 2, C["sea"])


def _crash(pg, x, y, w, h):
    pg.box(x, y, w, h, C["card"])
    bars = [0.42, 0.55, 0.38, 0.72, 0.60, 0.88, 0.66, 1.0]
    bw = w // 9
    for i, f in enumerate(bars):
        bh = int(h * f)
        pg.box(x + 3 + i * bw, y + h - 3 - bh, bw - 2, bh, C["red"])
    pg.seg(x + 2, y + 8, x + w - 3, y + h - 6, C["gold"])
    pg.seg(x + 2, y + 12, x + w - 3, y + h - 2, C["ink"])


def _gaza(pg, x, y, w, h):
    pg.box(x, y, w, h, C["dusk"])
    pg.box(x, y + h - 12, w, 12, C["dark"])
    for i, bh in enumerate([14, 20, 11, 17, 23, 13]):
        pg.box(x + 4 + i * (w // 6), y + h - 12 - bh, w // 6 - 4, bh, C["ink"])
    pg.disc(x + w - 14, y + 8, 4, C["red"])
    pg.disc(x + w - 22, y + 14, 3, C["red"])
    pg.disc(x + w - 30, y + 20, 2, C["soft"])


def _port(pg, x, y, w, h):
    pg.box(x, y, w, h, C["sky"])
    pg.box(x, y + h - 10, w, 10, C["sea"])
    for i, col in enumerate([C["red"], C["gold"], C["green"], C["navy"]]):
        pg.box(x + 6 + i * (w // 5), y + h - 22, w // 5 - 4, 12, col)
    pg.seg(x + w - 16, y + 4, x + w - 16, y + h - 10, C["ink"])
    pg.seg(x + w - 16, y + 6, x + w - 2, y + 12, C["ink"])
    pg.box(x + w - 10, y + 12, 6, 4, C["ink"])


def _tariff(pg, x, y, w, h):
    pg.box(x, y, w, h, C["card"])
    for r in range(3):
        for c in range(5):
            pg.frame(x + 3 + c * (w // 5), y + 4 + r * (h // 3), w // 5 - 3, h // 3 - 3, C["red"])
    put_text(pg, "15%", x + w // 2 - 12, y + h // 2 - 4, 1, C["red"])


def _iran(pg, x, y, w, h):
    pg.box(x, y, w, h, C["white"])
    pg.box(x, y, w, h // 3, C["green"])
    pg.box(x, y + 2 * h // 3, w, h // 3, C["red"])
    pg.disc(x + w // 2, y + h // 2, 4, C["red"], solid=False)
    pg.seg(x + 4, y + h - 4, x + w - 4, y + 4, C["gold"])


def _knesset(pg, x, y, w, h):
    pg.box(x, y, w, h, C["sand"])
    pg.box(x + w // 4, y + h - 14, w // 2, 14, C["white"])
    pg.tri([(x + w // 4, y + h - 14), (x + w // 2, y + 6), (x + 3 * w // 4, y + h - 14)], C["white"])
    for i in range(5):
        pg.vbar(x + w // 4 + 4 + i * (w // 2 // 5), y + h - 12, 10, C["ink"])
    pg.box(x, y + h - 4, w, 4, C["ink"])


def _shanghai(pg, x, y, w, h):
    pg.box(x, y, w, h, C["dusk"])
    for i, bh in enumerate([16, 26, 12, 22, 30, 18]):
        pg.box(x + 3 + i * (w // 6), y + h - bh, w // 6 - 4, bh, C["navy"])
    pg.seg(x + 3 + w // 2, y + 4, x + 3 + w // 2, y + h - 26, C["red"])
    pg.disc(x + 3 + w // 2, y + 6, 2, C["red"])


def _cpi(pg, x, y, w, h):
    pg.box(x, y, w, h, C["card"])
    bars = [0.30, 0.42, 0.36, 0.55, 0.70, 0.88]
    bw = w // 7
    for i, f in enumerate(bars):
        bh = int(h * f)
        pg.box(x + 4 + i * bw, y + h - 3 - bh, bw - 2, bh, C["green"])
    pg.seg(x + 4, y + h - int(h * 0.30) - 3, x + w - 4, y + 3, C["red"])
    put_text(pg, "4.9%", x + w - 26, y + 2, 1, C["red"])


def _plane(pg, x, y, w, h):
    pg.box(x, y, w, h, C["sky"])
    pg.box(x + w // 2 - 18, y + h // 2 - 3, 36, 6, C["white"])
    pg.tri([(x + w // 2 + 18, y + h // 2 - 3), (x + w // 2 + 28, y + h // 2), (x + w // 2 + 18, y + h // 2 + 3)], C["white"])
    pg.tri([(x + w // 2 - 4, y + h // 2 - 3), (x + w // 2 + 2, y + h // 2 - 10), (x + w // 2 + 8, y + h // 2 - 3)], C["white"])
    pg.tri([(x + w // 2 - 4, y + h // 2 + 3), (x + w // 2 + 2, y + h // 2 + 10), (x + w // 2 + 8, y + h // 2 + 3)], C["white"])
    pg.seg(x + 4, y + 6, x + w - 4, y + 10, C["white"])
    pg.seg(x + 4, y + 12, x + w - 4, y + 16, C["white"])


def _odesa(pg, x, y, w, h):
    pg.box(x, y, w, h, C["navy"])
    cx, cy = x + w // 2, y + h // 2
    for a in range(8):
        dx = [1, 1, 0, -1, -1, -1, 0, 1][a]
        dy = [0, 1, 1, 1, 0, -1, -1, -1][a]
        pg.seg(cx, cy, cx + dx * 14, cy + dy * 14, C["gold"])
    pg.disc(cx, cy, 4, C["red"])
    pg.disc(cx, cy, 2, C["white"])


def _coin(pg, x, y, w, h):
    pg.box(x, y, w, h, C["dark"])
    pg.disc(x + w // 2, y + h // 2, h // 2 - 3, C["gold"])
    pg.disc(x + w // 2, y + h // 2, h // 2 - 7, C["gold"], solid=False)
    put_text(pg, "$", x + w // 2 - 3, y + h // 2 - 4, 1, C["dark"])
    put_text(pg, "90", x + w - 16, y + h - 10, 1, C["white"])


def _search(pg, x, y, w, h):
    pg.box(x, y, w, h, C["card"])
    pg.frame(x + 4, y + 4, w - 8, 12, C["ink"])
    put_text(pg, "204", x + 8, y + 7, 1, C["ink"])
    pg.disc(x + w - 14, y + h - 12, 5, C["red"], solid=False)
    pg.seg(x + w - 10, y + h - 8, x + w - 4, y + h - 3, C["red"])
    for i in range(6):
        pg.box(x + 6 + i * 3, y + h - 8, 2, 4, C["gold"])


ART = {
    "rocket": _rocket, "crash": _crash, "gaza": _gaza, "port": _port,
    "tariff": _tariff, "iran": _iran, "knesset": _knesset,
    "shanghai": _shanghai, "cpi": _cpi, "plane": _plane,
    "odesa": _odesa, "coin": _coin, "search": _search,
}

LAND_RAW = (
    "-168,65 -140,70 -120,71 -100,68 -85,66 -75,62 -65,50 -75,35 -82,26 "
    "-88,15 -97,16 -105,20 -115,28 -125,40 -125,49 -140,60 -160,58;"
    "-55,60 -42,64 -30,68 -22,70 -32,74 -48,76 -58,74;"
    "-80,10 -75,5 -70,0 -60,-5 -48,-5 -38,-12 -40,-25 -52,-32 -62,-38 "
    "-70,-45 -73,-54 -75,-38 -78,-20 -80,-8;"
    "-17,15 -10,30 0,35 12,37 22,32 32,31 38,22 48,11 51,10 44,0 40,-10 "
    "35,-20 30,-30 20,-35 14,-28 12,-18 10,-5 8,4 0,5 -8,5 -13,10;"
    "-10,36 -9,43 -2,48 2,51 6,54 9,57 12,59 18,56 22,55 25,59 30,62 "
    "25,66 18,70 12,66 8,60 2,58 -4,50 -10,44;"
    "30,62 42,68 58,69 72,72 92,75 112,76 132,72 152,70 172,66 178,65 "
    "168,60 158,52 144,44 140,38 132,33 126,30 120,24 110,20 104,10 "
    "100,8 94,16 88,22 80,15 74,10 70,20 64,25 58,25 52,28 46,30 40,32 "
    "35,36 30,36;"
    "95,5 100,0 105,-5 110,-7 116,-8 122,-10 128,-6 134,-2 140,-4 144,-6 "
    "138,-9 128,-11 118,-12 108,-8 100,-2;"
    "113,-22 114,-30 116,-35 122,-34 128,-32 134,-33 138,-35 142,-38 "
    "147,-38 150,-37 153,-30 150,-24 146,-19 142,-14 138,-12 132,-12 "
    "126,-14 120,-20 114,-22"
)
PINS_RAW = (
    "1,98.5,39.7,98.5,39.7;2,127,37.5,138,44;3,34.5,31.3,34.5,31.3;"
    "4,42,15.4,42,15.4;5,-77,38.9,-77,38.9;6,51.4,35.7,51.4,35.7;"
    "7,35.2,31.8,35.2,31.8;8,121.5,31.2,121.5,31.2;9,149,-35.3,149,-35.3;"
    "10,-75,18,-75,18;11,30.7,46.5,30.7,46.5;12,55,25.2,55,25.2;"
    "13,77.2,28.6,77.2,28.6"
)


def card(pg, c, x, y, w, h):
    col = RC[c["region"]]
    pg.box(x, y, w, h, C["card"])
    pg.frame(x, y, w, h, C["line"])
    pg.box(x, y, w, 4, col)
    tx = x + 7
    tw = w - 14
    yy = y + 9
    put_text(pg, str(c["num"]), tx, yy, 1, col)
    put_text(pg, c["kicker"], tx + 6 * len(str(c["num"])) + 6, yy, 1, col)
    yy += 11
    for hl in wrap(c["headline"], tw // 12):
        put_text(pg, hl, tx, yy, 2, C["ink"])
        yy += 15
    yy += 2
    ah = 30 if h <= 150 else 44
    ART[c["art"]](pg, tx, yy, tw, ah)
    yy += ah + 4
    for bl in wrap(c["body"], tw // 6):
        put_text(pg, bl.upper(), tx, yy, 1, C["ink"])
        yy += 9
    sy = y + h - 13
    pg.box(x + 1, sy - 2, w - 2, 14, col)
    put_text_c(pg, c["strip"], x + w // 2, sy, 1, C["white"])


def draw_map(pg, mx, my, mw, mh):
    pg.box(mx, my, mw, mh, C["sky"])
    pg.frame(mx, my, mw, mh, C["line"])
    polys = []
    for chunk in LAND_RAW.split(";"):
        pts = []
        for pair in chunk.split():
            lon, lat = pair.split(",")
            px = mx + int((float(lon) + 180) / 360 * mw)
            py = my + int((90 - float(lat)) / 180 * mh)
            pts.append((px, py))
        polys.append(pts)
    for pts in polys:
        pg.tri(pts, C["sand"])
        pg.outline(pts, C["soft"])
    for raw in PINS_RAW.split(";"):
        num, lon, lat, lx, ly = raw.split(",")
        px = mx + int((float(lon) + 180) / 360 * mw)
        py = my + int((90 - float(lat)) / 180 * mh)
        pg.disc(px, py, 5, C["red"])
        pg.disc(px, py, 2, C["white"])
        put_text(pg, num, px + 7, py - 4, 1, C["red"])
    put_text(pg, "WHERE IT HAPPENED", mx + 8, my + 6, 1, C["ink"])
    put_text(pg, "1 TIANGONG  2 SEOUL  3 GAZA  4 HODEIDAH  5 WASHINGTON",
             mx + 8, my + mh - 23, 1, C["ink"])
    put_text(pg, "6 TEHRAN  7 JERUSALEM  8 SHANGHAI  9 CANBERRA  10 CARIBBEAN",
             mx + 8, my + mh - 15, 1, C["ink"])
    put_text(pg, "11 ODESA  12 BRENT  13 DOHA", mx + 8, my + mh - 7, 1, C["ink"])


def strip(pg, y, label, items, bg, fg, k=1, gap=6):
    pg.box(12, y, 1000, 16, bg)
    cx = put_text(pg, label, 18, y + 4, k, fg)
    for it in items:
        cx = put_text(pg, it, cx + gap, y + 4, k, fg)
        cx += gap


def build():
    pg = Page(1024, 1024, C["paper"])
    put_text_c(pg, "THE WORLD TODAY", 512, 8, 5, C["ink"])
    put_text_c(pg, "WEDNESDAY 25 NOVEMBER 2026", 512, 46, 2, C["soft"])
    pg.hbar(12, 62, 1000, C["ink"], 2)
    strip(pg, 70, "REGIONS:", list(REGION_TALLY), C["ink"], C["white"])
    strip(pg, 90, "FIELDS:", list(FIELD_TALLY), C["navy"], C["white"])
    yy = 116
    for row in range(3):
        for col in range(3):
            n = row * 3 + col
            if n >= 9:
                break
            card(pg, CARDS[n], 12 + col * 337, yy, 326, 150)
        yy += 158
    for row in range(1):
        for col in range(4):
            n = 9 + col
            card(pg, CARDS[n], 12 + col * 253, yy, 242, 150)
        yy += 158
    draw_map(pg, 12, yy, 660, 100)
    bx = 12 + 660 + 8
    pg.box(bx, yy, 332, 100, C["card"])
    pg.frame(bx, yy, 332, 100, C["line"])
    put_text(pg, "THE DAY IN NUMBERS", bx + 8, yy + 6, 1, C["red"])
    ny = yy + 20
    for ln in wrap(NUMBERS, 52):
        put_text(pg, ln, bx + 8, ny, 1, C["ink"])
        ny += 10
    yy += 108
    pg.box(12, yy, 1000, 70, C["card"])
    pg.frame(12, yy, 1000, 70, C["line"])
    put_text(pg, "DATE CHECK - TUESDAY 24 NOVEMBER, NOT TODAY:", 18, yy + 6, 1, C["red"])
    dy = yy + 20
    for ln in DATE_CHECK:
        put_text(pg, ln, 18, dy, 1, C["ink"])
        dy += 10
    yy += 78
    pg.hbar(12, yy, 1000, C["ink"], 2)
    yy += 6
    for ln in wrap(SOURCES, 150):
        put_text(pg, ln, 12, yy, 1, C["soft"])
        yy += 9
    yy += 2
    put_text_c(pg, "54 STORIES  |  7 REGIONS  |  THE WORLD TODAY  |  25 NOVEMBER 2026",
               512, yy, 1, C["soft"])
    d = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "entry.png"), "wb") as f:
        f.write(png_bytes(pg))


if __name__ == "__main__":
    build()
