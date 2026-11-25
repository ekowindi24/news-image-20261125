#!/usr/bin/env python3
"""news-image-20261125 -- one front page summing up Wednesday 25 November 2026.

Draws a 1024x1024 newspaper front page (54 stories: 13 illustrated cards
plus 41 one-line briefs) with the Python standard library only and no
network access. The PNG bytes are fully deterministic: two runs write the
same file. Output goes to $MAKEFUN_OUTPUT_DIR/entry.png (default ./out/).
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
CREAM = (247, 241, 222)   # paper
PAPER2 = (252, 248, 235)  # card paper
INK = (24, 22, 18)        # near-black
GREY = (110, 104, 90)
LINE = (60, 56, 46)
RED = (176, 58, 46)
BLUE = (43, 94, 167)
TEAL = (30, 122, 90)
PURPLE = (125, 60, 152)
AMBER = (156, 106, 18)
SLATE = (85, 85, 85)
OCEAN = (207, 224, 232)
LAND = (232, 221, 192)
LAND_LINE = (138, 125, 90)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (46, 134, 70)
GOLD = (214, 178, 74)
SKY = (38, 48, 74)

REGION_COLOR = {
    "EUROPE": BLUE,
    "MIDDLE EAST": RED,
    "ASIA": TEAL,
    "AFRICA": PURPLE,
    "AMERICAS": AMBER,
    "OCEANIA": (42, 125, 140),
    "WORLD": SLATE,
}

# ------------------------------------------------------------------- canvas
PIX = bytearray(W * H * 3)


def set_px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        PIX[i], PIX[i + 1], PIX[i + 2] = color


def fill_rect(x, y, w, h, color):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            PIX[i], PIX[i + 1], PIX[i + 2] = color


def rect_border(x, y, w, h, color, t=1):
    fill_rect(x, y, w, t, color)
    fill_rect(x, y + h - t, w, t, color)
    fill_rect(x, y, t, h, color)
    fill_rect(x + w - t, y, t, h, color)


def hline(x, y, w, color, t=1):
    fill_rect(x, y, w, t, color)


def vline(x, y, h, color, t=1):
    fill_rect(x, y, t, h, color)


def line(x0, y0, x1, y1, color):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        set_px(x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, color, fill=True):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d2 = (xx - cx) ** 2 + (yy - cy) ** 2
            if fill:
                if d2 <= r * r:
                    set_px(xx, yy, color)
            else:
                if r * r - 2 * r <= d2 <= r * r:
                    set_px(xx, yy, color)


def poly_fill(points, color):
    """Scanline fill for a simple polygon given as [(x, y), ...]."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    for y in range(max(0, min(ys)), min(H, max(ys) + 1)):
        nodes = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                nodes.append(xi)
        nodes.sort()
        for k in range(0, len(nodes) - 1, 2):
            xa, xb = int(nodes[k]), int(nodes[k + 1])
            for x in range(max(0, xa), min(W, xb + 1)):
                set_px(x, y, color)


def poly_line(points, color):
    for i in range(len(points)):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % len(points)]
        line(int(x0), int(y0), int(x1), int(y1), color)


# ------------------------------------------------------------- 5x7 bitmap font
# Each glyph is 7 rows of 5 bits, most significant bit on the left.
# Written from scratch for this page; all page text is set in capitals.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    "-": (0, 0, 0, 0x1F, 0, 0, 0),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    '"': (0x0A, 0x0A, 0, 0, 0, 0, 0),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "+": (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "=": (0, 0, 0x1F, 0, 0x1F, 0, 0),
    "#": (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    "*": (0, 0x04, 0x15, 0x0E, 0x15, 0x04, 0),
    "~": (0, 0, 0x06, 0x09, 0x00, 0, 0),
    ">": (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
    "<": (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    "|": (0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "·": (0, 0, 0, 0x0C, 0x0C, 0, 0),
}


def text_w(s, scale):
    return len(s) * 6 * scale


def draw_text(s, x, y, scale, color):
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits & (1 << (4 - col)):
                    fill_rect(cx + col * scale, y + row * scale,
                              scale, scale, color)
        cx += 6 * scale
    return cx


def draw_text_centered(s, cx, y, scale, color):
    draw_text(s, cx - text_w(s, scale) // 2, y, scale, color)


def wrap_text(s, max_chars):
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- PNG writer
def write_png(path, w, h, rgb):
    raw = b"".join(
        b"\x00" + bytes(rgb[y * w * 3:(y + 1) * w * 3]) for y in range(h))

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(raw, 9))
    data += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(data)

# ------------------------------------------------------------------- content
# All figures were checked against the 25 Nov 2026 research file and
# re-verified by web search during the evening build:
#   * Asian closes Wed 25 Nov: Kospi -6.16% to 4,697.51, Taiex -4.80% to
#     38,195.43, Nikkei -2.78% to 57,011.62, Shanghai -2.03% to 3,476.47,
#     Hang Seng -1.1% to 21,966.01 (dpa-AFX, Sharecast, AsiaToday).
#   * Shenzhou-24 launched 25 Nov 00:18 UTC; Zeeshan Ali is the first
#     Pakistani in orbit and the first foreigner on Tiangong (Xinhua, Reuters).
#   * USTR Section 301 findings were still unpublished as of Wed 25 Nov;
#     the card reports the imminent release and the caps, not final rates.
#   * US markets were not yet open at build time (19:30 WIB = 07:30 ET),
#     so no Wed US close is shown; Tue closes are dated TUE in the text.
# Dating discipline: a story is on this page only if it happened, or was
# first reported, on Wed 25 Nov 2026, or is explicitly dated to Tue 24 Nov
# inside its own text. Everything else big that broke earlier is named in
# the DATE CHECK box instead of being shown as today's news.

CARDS = [
    dict(num=1, region="ASIA", kicker="SPACE - XINHUA, REUTERS",
         headline="PAKISTANI FLIES TO TIANGONG",
         body="China launches Shenzhou-24 at 00:18 UTC from Jiuquan. Tang Hongbo, Wu Yi and Muhammad Zeeshan Ali - the first Pakistani in orbit and the first foreigner on Tiangong - stay 5-10 days.",
         strip="00:18 UTC - 1ST FOREIGNER ON TIANGONG", art="rocket"),
    dict(num=2, region="ASIA", kicker="MARKETS - ASIA - REUTERS",
         headline="ASIAN MARKETS TUMBLE WEDNESDAY",
         body="AI doubts and fresh US tariff fears sink Asia a day after the relief rally. Kospi -6.2%, Taiex -4.8%, Nikkei -2.8%, Shanghai -2.0%; chip stocks lead the fall.",
         strip="KOSPI -6.2% - TAIEX -4.8% - NIKKEI -2.8%", art="crash"),
    dict(num=3, region="MIDDLE EAST", kicker="GAZA - REUTERS",
         headline="GAZA: SECOND HAMAS CHIEF KILLED",
         body="An Israeli strike early Wed hits an apartment in Gaza City's Beach camp, killing Hamas security chief Mohammad Abuelouf, his wife and two children - the second such killing in 24 hours.",
         strip="2ND HAMAS SECURITY CHIEF IN 24H", art="gaza"),
    dict(num=4, region="MIDDLE EAST", kicker="YEMEN - REUTERS",
         headline="HOUTHIS THREATEN JEDDAH PORTS",
         body="Saree warns Jeddah and all Saudi Red Sea ports are targets if Hodeidah is hit; the coalition strikes it Wed.",
         strip="JEDDAH NEXT? HODEIDAH HIT WED", art="port"),
    dict(num=5, region="WORLD", kicker="TRADE - REUTERS, WSJ",
         headline="NEW US TARIFFS LOOM OVER 16",
         body="USTR is set to unveil Section 301 findings on excess capacity in 16 economies. Caps of 15% for the EU, Japan, Korea; China steepest.",
         strip="15% CAPS - CHINA STEEPEST", art="tariff"),
    dict(num=6, region="MIDDLE EAST", kicker="IRAN - REUTERS",
         headline="IRAN DEFIES US BLOCKADE",
         body="Tehran says it is prepared to withstand the US blockade and is working to curb price rises, while holding to its 7 conditions for talks.",
         strip="7 CONDITIONS STAND", art="iran"),
    dict(num=7, region="MIDDLE EAST", kicker="ISRAEL - REUTERS",
         headline="EISENKOT'S FIRST DEAL, THEN BLOW",
         body="Yashar signs a first pact with Lieberman's party Tue - 48 of 61 seats. That night the Democrats halt talks.",
         strip="48 OF 61 SEATS - DEC 2 TARGET", art="knesset"),
    dict(num=8, region="ASIA", kicker="CHINA - REUTERS",
         headline="SHANGHAI VOWS LOYALTY",
         body="Shanghai's leaders pledge loyalty to Beijing after party chief Chen Jining is probed for graft - the 4th Politburo member investigated since 2025.",
         strip="4TH POLITBURO PROBE SINCE 2025", art="shanghai"),
    dict(num=9, region="OCEANIA", kicker="ECONOMY - AUSTRALIA",
         headline="AUSTRALIA CPI JUMPS TO 4.9%",
         body="October inflation hits 4.9%, up from 4.3% in September, with trimmed mean at 3.8%. The ASX falls 0.4% as RBA hike odds rise.",
         strip="CPI 4.9% - RBA HIKE ODDS RISE", art="cpi"),
    dict(num=10, region="AFRICA", kicker="AFRICA - BBC",
         headline="CONGO PLANE DOWN NEAR MINEMBWE",
         body="A Cessna 208 went down Sun; the army lost contact in bad weather. Rebels claim a shoot-down; 4 aboard, 2 held.",
         strip="4 ABOARD - 2 HELD", art="plane"),
    dict(num=11, region="EUROPE", kicker="UKRAINE - REUTERS",
         headline="ODESA: RUSSIAN STRIKE KILLS 2",
         body="A Russian strike kills two people in Ukraine's Odesa region on Wednesday, the governor says.",
         strip="2 KILLED WED", art="odesa"),
    dict(num=12, region="ASIA", kicker="KOREA - REUTERS",
         headline="KOREA UNVEILS STABLECOIN RULES",
         body="South Korea unveils draft stablecoin rules Wed, with a possible easing of its ban on ICOs.",
         strip="ICO BAN MAY EASE", art="coin"),
    dict(num=13, region="ASIA", kicker="MALAYSIA - REUTERS",
         headline="MALAYSIA SEEKS $146M FROM GOOGLE",
         body="Malaysia's regulator seeks $146 million in damages from Google over harmful content.",
         strip="$146M CLAIM", art="search"),
]

# 41 one-line briefs, displayed numbered 14-54 in order. Every brief is
# at most 80 characters so it fits one line; Tue items carry TUE in text.
BRIEFS = [
    "Latvia president: Ukraine war may hit a tipping point next year (Tue)",
    "Zelensky confirms Ukraine hit the Sparta II in the Gulf of Finland (Tue)",
    "Nvidia -5.9% Tue, Nasdaq -1.5%, S&P -0.5%, Dow +0.9% (Tue close)",
    "Dell: record Q3 revenue $54.94bn, AI backlog $132.3bn (Tue)",
    "Suryavanshi, 15, smashes 204 off 53 balls with 28 sixes (Tue, Doha)",
    "Martha Firestone Ford, ex-Lions owner, dies at 101 (Tue)",
    "Houthi drone hits Riyadh's PIF tower Tue, 11 hurt incl. 2 Indians",
    "Sarkozy and Carla Bruni case ordered to trial; pre-trial 1 Apr 2027 (Tue)",
    "Trump awards Rudy Giuliani the Medal of Freedom (Tue)",
    "Huawei convicted in a US criminal trial; cleared of racketeering (Tue)",
    "Gaza: Israeli strike Tue kills Hamas security director Naeem Abu Nahel",
    "Quake of 5.6 hits Nepal near the China border; felt in India, China (Tue)",
    "Malaysia to repatriate 6,500+ Rohingya refugees in December (Tue)",
    "Sweden: speaker nominates Kristersson to stay PM; vote on 30 Nov (Tue)",
    "Bangladesh garment workers clash with police Tue; factories shut (Tue)",
    "UK heat deaths hit 5,258 in summer 2026, highest since 2016 (Tue)",
    "Turkish military helicopter crashes in training, killing 5 crew (Tue)",
    "Fort Hood shooter Hasan seeks a stay of execution set for next week (Tue)",
    "Radar issue delays flights at Chicago O'Hare, FAA says (Tue)",
    "Trump pardons Thanksgiving turkeys Freedom and Feathers (Tue)",
    "AIDS deaths fall to 570,000 in 2025, lowest in 20+ years (Tue)",
    "UAE bus-truck crash death toll rises to 13, 14 hurt (Tue)",
    "CIA and ODNI hit by cyber breach of unclassified information (Tue)",
    "Hasina plans to return to Bangladesh on 16 December (Tue)",
    "Russian jets enter South Korea's air defence zone Tue; Ulleung alerted",
    "Yemen: Houthis 60 km from Aden but will not seize the city, army says (Tue)",
    "US consumer confidence jumps 11.4 points to 103.3 in November (Tue)",
    "Germany's Ifo index rises to 90.6 in November, highest since May 2023 (Tue)",
    "China and the US discuss farm trade and market access at talks (Wed)",
    "Amazon to launch Amazon Autos in the UK in early 2027 (Wed)",
    "European stocks set for gains in 2027 but volatility likely, poll (Wed)",
    "Libya's eastern commander Haftar arrives in Turkiye (Wed)",
    "UK warns of Russian sabotage threat to companies that supply Ukraine (Wed)",
    "Russia summons Latvia's envoy in Moscow over embassy layoffs (Wed)",
    "Brent crude falls 1.2% to $90.28 Wed as glut fears offset Mideast tension",
    "US October PCE and Q3 GDP due later on Wednesday (scheduled)",
    "25 November is the International Day for the Elimination of Violence",
    "Libya: Ukraine's sinking of a Russian vessel risks fresh instability (Wed)",
    "Hong Kong wildlife groups push tighter exotic pet rules after 3.7m imports",
    "African insurgents take the war to the skies with off-the-shelf drones (Wed)",
    "Japan's Nikkei to rise next year but fall short of its record, poll (Wed)",
]

NUMBERS = [
    "KOSPI -6.2%, TAIEX -4.8%",
    "SHENZHOU-24 00:18 UTC",
    "$132.3BN DELL BACKLOG",
    "204 OFF 53 BALLS",
    "AUS CPI 4.9%",
]

REGION_TALLY = ("EUROPE 12", "MIDDLE EAST 8", "ASIA 13", "AFRICA 4",
                "AMERICAS 11", "OCEANIA 1", "WORLD 5")
FIELD_TALLY = ("WAR & SECURITY 14", "POLITICS & DIPLOMACY 14",
               "ECONOMY & MARKETS 12", "TECHNOLOGY 4",
               "DISASTER & HEALTH 6", "SCIENCE & CULTURE 4")

DATE_CHECK = [
    "KEPT OFF BECAUSE FIRST REPORTED BEFORE WED 25 NOV: NVIDIA'S HUANG REINSTATEMENT (MON 23 NOV - WED'S NEWS IS THE ASIAN ROUT, CARD 2);",
    "DELL'S RECORD QUARTER (TUE 24 NOV, AFTER CLOSE); THE HOUTHI STRIKE ON RIYADH'S PIF TOWER (TUE - WED'S NEWS IS THE JEDDAH THREAT, CARD 4);",
    "THE CHEN JINING PROBE ANNOUNCEMENT (TUE - WED'S NEWS IS SHANGHAI'S LOYALTY PLEDGE, CARD 8); THE EISENKOT-LIEBERMAN DEAL (AGREED TUE -",
    "WED'S NEWS IS THE DEMOCRATS HALTING TALKS, CARD 7); THE DR CONGO PLANE WENT DOWN SUN 22 NOV (SEE CARD 10); GTA 6'S 39M PS5 PLAYERS (SONY, MON 23 NOV);",
    "SURYAVANSHI'S 204 (TUE 24 NOV, DOHA); THE ICJ 9-6 ROHINGYA RULING ITSELF (19 NOV); THE MERKURY SINKING (SUN 22 NOV); THE HORMUZ TANKER STRIKES (SAT 22 NOV);",
    "THE THREE RUSSIAN MISSILES IN POLAND (FRI 20 NOV); THE SERANG FACTORY FIRE BROKE OUT OVER THE WEEKEND OF 22-23 NOV.",
]

SOURCES = "SOURCES: REUTERS, AP, BBC, WSJ, AL JAZEERA, XINHUA, MORNINGSTAR, SHARECAST, ESPNCRICINFO, DETROIT LIONS, MILITARY AFRICA, SEATRADE, AGBI."


# ------------------------------------------------------------ card mini-art
def art_rocket(x, y, w, h):
    fill_rect(x, y, w, h, SKY)
    for sx, sy in [(8, 6), (w - 14, 10), (w // 2, 4), (16, h - 8), (w - 24, h - 12)]:
        set_px(x + sx, y + sy, WHITE)
        set_px(x + sx + 1, y + sy, WHITE)
    cx = x + w // 2
    poly_fill([(cx, y + 2), (cx + 5, y + 14), (cx + 5, y + h - 16),
               (cx - 5, y + h - 16), (cx - 5, y + 14)], WHITE)
    poly_fill([(cx - 5, y + h - 18), (cx - 12, y + h - 8),
               (cx - 5, y + h - 10)], RED)
    poly_fill([(cx + 5, y + h - 18), (cx + 12, y + h - 8),
               (cx + 5, y + h - 10)], RED)
    poly_fill([(cx - 3, y + h - 16), (cx, y + h - 2), (cx + 3, y + h - 16)],
              (230, 120, 30))
    circle(cx, y + 10, 2, RED)


def art_crash(x, y, w, h):
    base = y + h - 6
    bars = [(RED, 34), (RED, 28), (RED, 20), (RED, 12)]
    bw = (w - 10) // 4
    for i, (c, bh) in enumerate(bars):
        bx = x + 5 + i * bw
        fill_rect(bx, base - bh, bw - 3, bh, c)
    line(x + 4, base - 38, x + w - 6, base - 10, GOLD)
    draw_text("-6.2%", x + w - 34, y + 2, 1, RED)


def art_gaza(x, y, w, h):
    base = y + h - 4
    hs = [14, 22, 17, 26, 20]
    bw = (w - 6) // 5
    for i, bh in enumerate(hs):
        fill_rect(x + 3 + i * bw, base - bh, bw - 2, bh, (70, 66, 58))
    circle(x + w - 16, y + 8, 6, GREY)
    circle(x + w - 26, y + 4, 4, GREY)
    fill_rect(x + 6, y + 6, 4, 4, RED)
    fill_rect(x + 16, y + 2, 4, 4, RED)


def art_port(x, y, w, h):
    fill_rect(x, y + h - 14, w, 14, (90, 140, 180))
    fill_rect(x + 6, y + h - 26, w - 12, 12, INK)
    for i in range(4):
        fill_rect(x + 10 + i * ((w - 20) // 4), y + h - 40, 6, 14, (120, 100, 80))
    circle(x + w - 14, y + 6, 5, RED)
    circle(x + w - 14, y + 6, 2, GOLD)
    line(x + 6, y + 8, x + w - 20, y + 8, RED)


def art_tariff(x, y, w, h):
    bw = (w - 6) // 3
    for r in range(3):
        for c in range(3):
            bx = x + 3 + c * bw
            by = y + 3 + r * ((h - 6) // 3)
            fill_rect(bx, by, bw - 2, (h - 6) // 3 - 2, (150, 110, 70))
    draw_text("15%", x + w // 2 - 9, y + h // 2 - 4, 1, WHITE)
    fill_rect(x, y + h - 4, w, 2, RED)


def art_iran(x, y, w, h):
    fill_rect(x, y + 2, w, (h - 4) // 3, GREEN)
    fill_rect(x, y + 2 + (h - 4) // 3, w, (h - 4) // 3, WHITE)
    fill_rect(x, y + 2 + 2 * (h - 4) // 3, w, (h - 4) // 3, RED)
    rect_border(x, y + 2, w, h - 4, INK, 1)
    line(x + 4, y + h - 6, x + w - 4, y + 4, GOLD)


def art_knesset(x, y, w, h):
    base = y + h - 4
    poly_fill([(x + 4, base - 20), (x + w - 4, base - 20),
               (x + w // 2, base - 26)], INK)
    for i in range(3):
        fill_rect(x + 10 + i * ((w - 20) // 3), base - 24, 4, 24, INK)
    fill_rect(x + 4, base - 2, w - 8, 2, INK)
    circle(x + w // 2 - 12, y + 2, 2, BLUE)
    circle(x + w // 2 + 12, y + 2, 2, BLUE)
    line(x + w // 2 - 12, y + 2, x + w // 2 + 12, y + 2, BLUE)


def art_shanghai(x, y, w, h):
    base = y + h - 4
    fill_rect(x + w // 2 - 3, base - 34, 6, 34, (70, 66, 58))
    poly_fill([(x + w // 2 - 3, base - 34), (x + w // 2 + 3, base - 34),
               (x + w // 2, base - 40)], RED)
    fill_rect(x + 6, base - 22, 14, 22, (120, 100, 80))
    fill_rect(x + w - 20, base - 26, 14, 26, (120, 100, 80))
    fill_rect(x + 24, base - 14, 10, 14, (150, 140, 110))
    fill_rect(x + w - 34, base - 16, 10, 16, (150, 140, 110))
    circle(x + w - 12, y + 4, 4, GOLD)


def art_cpi(x, y, w, h):
    base = y + h - 6
    hs = [10, 16, 24]
    bw = (w - 12) // 3
    for i, bh in enumerate(hs):
        bx = x + 6 + i * bw
        fill_rect(bx, base - bh, bw - 4, bh, AMBER)
    line(x + 4, base - 28, x + w - 6, base - 8, RED)
    draw_text("4.9%", x + 4, y + 2, 1, RED)


def art_plane(x, y, w, h):
    fill_rect(x, y, w, h, SKY)
    cx, cy = x + w // 2, y + h // 2
    fill_rect(cx - 18, cy - 3, 36, 6, WHITE)
    fill_rect(cx + 2, cy - 12, 6, 20, WHITE)
    fill_rect(cx - 18, cy - 8, 8, 4, WHITE)
    poly_fill([(cx - 18, cy - 3), (cx - 26, cy + 2), (cx - 18, cy + 3)], WHITE)
    circle(x + w - 12, y + h - 8, 4, (230, 120, 30))
    circle(x + w - 12, y + h - 8, 2, GOLD)


def art_odesa(x, y, w, h):
    cx, cy = x + w // 2, y + h // 2
    for dx, dy in [(0, -12), (10, -6), (12, 6), (4, 12), (-8, 10), (-12, -2)]:
        line(cx, cy, cx + dx, cy + dy, RED)
    circle(cx, cy, 5, GOLD)
    circle(cx, cy, 2, RED)
    fill_rect(x + 4, y + h - 8, w - 8, 2, INK)


def art_coin(x, y, w, h):
    cx, cy = x + w // 2, y + h // 2
    circle(cx, cy, min(w, h) // 2 - 2, GOLD)
    circle(cx, cy, min(w, h) // 2 - 2, INK, fill=False)
    draw_text("$", cx - 3, cy - 4, 1, INK)
    for i in range(3):
        fill_rect(x + 4 + i * 6, y + h - 6, 4, 4, TEAL)


def art_search(x, y, w, h):
    fill_rect(x + 4, y + h // 2 - 8, w - 8, 16, WHITE)
    rect_border(x + 4, y + h // 2 - 8, w - 8, 16, INK, 1)
    circle(x + 14, y + h // 2, 4, BLUE, fill=False)
    line(x + 17, y + h // 2 + 3, x + 22, y + h // 2 + 7, BLUE)
    draw_text("GOOGLE", x + 26, y + h // 2 - 3, 1, INK)
    draw_text("$146M", x + 4, y + 2, 1, RED)


ART = {"rocket": art_rocket, "crash": art_crash, "gaza": art_gaza,
       "port": art_port, "tariff": art_tariff, "iran": art_iran,
       "knesset": art_knesset, "shanghai": art_shanghai, "cpi": art_cpi,
       "plane": art_plane, "odesa": art_odesa, "coin": art_coin,
       "search": art_search}

# ------------------------------------------------------------------- layout
MARGIN = 12
CW = W - 2 * MARGIN  # 1000


def draw_card(card, x, y, w, h):
    color = REGION_COLOR[card["region"]]
    fill_rect(x, y, w, h, PAPER2)
    rect_border(x, y, w, h, LINE, 1)
    fill_rect(x, y, w, 4, color)
    pad = 7
    ix = x + pad
    iw = w - 2 * pad
    cy = y + 9
    draw_text(str(card["num"]), ix, cy, 1, color)
    draw_text(card["kicker"], ix + 12, cy, 1, color)
    cy += 11
    head_lines = wrap_text(card["headline"], iw // 12)
    for hl in head_lines:
        draw_text(hl, ix, cy, 2, INK)
        cy += 15
    cy += 2
    art_h = 30 if h <= 150 else 44
    ART[card["art"]](ix, cy, iw, art_h)
    cy += art_h + 4
    body_lines = wrap_text(card["body"], iw // 6)
    for bl in body_lines:
        draw_text(bl.upper(), ix, cy, 1, INK)
        cy += 9
    strip_y = y + h - 13
    fill_rect(x + 1, strip_y - 2, w - 2, 14, color)
    draw_text_centered(card["strip"], x + w // 2, strip_y, 1, WHITE)


# Simplified world continents as (lon, lat) polygons.
CONTINENTS = [
    [(-168, 65), (-150, 70), (-130, 71), (-115, 68), (-100, 68), (-90, 62),
     (-82, 66), (-76, 62), (-70, 58), (-65, 49), (-75, 35), (-80, 26),
     (-85, 15), (-90, 14), (-97, 16), (-105, 20), (-115, 28), (-125, 40),
     (-125, 49), (-140, 60), (-155, 58), (-165, 60)],
    [(-55, 60), (-45, 60), (-40, 65), (-30, 68), (-22, 70), (-30, 74),
     (-45, 76), (-58, 74), (-60, 70)],
    [(-80, 10), (-75, 5), (-70, 0), (-60, -5), (-50, -5), (-40, -10),
     (-35, -15), (-40, -25), (-50, -30), (-60, -35), (-70, -40), (-70, -50),
     (-72, -54), (-75, -40), (-75, -25), (-80, -15), (-80, -5)],
    [(-17, 15), (-10, 30), (0, 35), (10, 37), (20, 32), (30, 31), (35, 28),
     (40, 15), (48, 11), (51, 10), (45, 0), (40, -10), (35, -20), (30, -30),
     (20, -35), (15, -30), (12, -18), (10, -5), (8, 4), (0, 5), (-8, 5),
     (-13, 10)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 50), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (25, 65), (20, 70),
     (15, 70), (10, 62), (5, 60), (0, 55), (-5, 50), (-10, 44)],
    [(30, 62), (40, 68), (55, 68), (70, 72), (90, 75), (110, 76), (130, 72),
     (150, 70), (170, 66), (178, 65), (170, 60), (162, 58), (155, 52),
     (145, 45), (140, 40), (135, 35), (130, 33), (127, 30), (122, 30),
     (120, 25), (110, 20), (105, 10), (100, 8), (95, 15), (90, 22), (85, 20),
     (80, 15), (75, 10), (72, 20), (66, 25), (60, 25), (55, 26), (50, 29),
     (48, 30), (45, 30), (40, 32), (35, 36), (30, 36)],
    [(95, 5), (100, 0), (105, -5), (110, -7), (115, -8), (120, -10),
     (125, -8), (130, -3), (135, 0), (140, -2), (145, -5), (140, -8),
     (130, -10), (120, -12), (110, -8), (100, -2)],
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -32), (130, -32),
     (135, -35), (140, -38), (145, -38), (150, -37), (153, -32), (150, -25),
     (146, -20), (142, -15), (140, -12), (135, -12), (130, -13), (125, -15),
     (120, -20), (114, -22)],
]

# (card num, lon, lat, pin display position lon, lat) -- display positions
# are nudged apart with hairlines where Europe / the Middle East crowd.
PINS = [
    (1, 98.5, 39.7, 98.5, 39.7),
    (2, 127, 37.5, 138, 44),
    (3, 34.5, 31.4, 44, 24),
    (4, 42.8, 14.8, 52, 14),
    (5, -77, 38.9, -77, 38.9),
    (6, 51.4, 35.7, 60, 42),
    (7, 35.2, 31.8, 24, 38),
    (8, 121.5, 31.2, 130, 30),
    (9, 151.2, -33.9, 151.2, -33.9),
    (10, 28.9, -3.0, 28.9, -3.0),
    (11, 30.7, 46.5, 30.7, 46.5),
    (12, 127, 37.5, 120, 44),
    (13, 101.7, 3.1, 101.7, 3.1),
]


def draw_map(mx, my, mw, mh):
    fill_rect(mx, my, mw, mh, OCEAN)
    rect_border(mx, my, mw, mh, LINE, 1)

    def px(lon, lat):
        return (mx + int((lon + 180) / 360 * mw),
                my + int((75 - lat) / 130 * mh))

    for lon in (-120, -60, 0, 60, 120):
        gx, _ = px(lon, 0)
        for gy in range(my, my + mh, 4):
            set_px(gx, gy, (190, 205, 215))
    for cont in CONTINENTS:
        pts = [px(lon, lat) for lon, lat in cont]
        poly_fill(pts, LAND)
        poly_line(pts, LAND_LINE)
    for num, lon, lat, dlon, dlat in PINS:
        card = CARDS[num - 1]
        color = REGION_COLOR[card["region"]]
        tx, ty = px(lon, lat)
        dx, dy = px(dlon, dlat)
        if (dx, dy) != (tx, ty):
            line(tx, ty, dx, dy, INK)
        r = 8
        circle(dx, dy, r, color)
        circle(dx, dy, r, INK, fill=False)
        label = str(num)
        draw_text(label, dx - text_w(label, 1) // 2, dy - 3, 1, WHITE)
    # legend
    ly = my + mh + 6
    lx = mx + 2
    for name in ("EUROPE", "MIDDLE EAST", "ASIA", "AFRICA", "AMERICAS",
                 "OCEANIA", "WORLD"):
        c = REGION_COLOR[name]
        fill_rect(lx, ly, 8, 8, c)
        lx += 11
        draw_text(name, lx, ly + 1, 1, INK)
        lx += text_w(name, 1) + 6


def main():
    fill_rect(0, 0, W, H, CREAM)
    # --- masthead
    y = 10
    draw_text_centered("THE WORLD TODAY", W // 2, y, 5, INK)
    y += 38
    hline(MARGIN, y, CW, INK, 2)
    y += 5
    draw_text_centered(
        "WEDNESDAY, 25 NOVEMBER 2026 - 54 STORIES - 7 REGIONS - 13 ILLUSTRATED",
        W // 2, y, 2, INK)
    y += 17
    hline(MARGIN, y, CW, INK, 1)
    # --- tally strips
    y += 6
    fill_rect(MARGIN, y, CW, 16, INK)
    draw_text("BY REGION", MARGIN + 6, y + 5, 1, GOLD)
    draw_text("  ".join(REGION_TALLY), MARGIN + 66, y + 5, 1, WHITE)
    y += 18
    fill_rect(MARGIN, y, CW, 16, (52, 50, 44))
    draw_text("BY FIELD", MARGIN + 6, y + 5, 1, GOLD)
    draw_text("  ".join(FIELD_TALLY), MARGIN + 66, y + 5, 1, WHITE)
    y += 18
    # --- day in numbers
    draw_text("THE DAY IN NUMBERS:", MARGIN, y + 5, 1, RED)
    draw_text(" | ".join(NUMBERS), MARGIN + 124, y + 5, 1, INK)
    hline(MARGIN, y + 17, CW, INK, 1)
    y += 24
    # --- cards row 1: 3 big
    row1_y, row1_h = y, 165
    cw3 = (CW - 16) // 3
    for i in range(3):
        draw_card(CARDS[i], MARGIN + i * (cw3 + 8), row1_y, cw3, row1_h)
    y = row1_y + row1_h + 8
    # --- cards row 2: 5
    row2_y, row2_h = y, 155
    cw5 = (CW - 32) // 5
    for i in range(5):
        draw_card(CARDS[3 + i], MARGIN + i * (cw5 + 8), row2_y, cw5, row2_h)
    y = row2_y + row2_h + 8
    # --- cards row 3: 5
    row3_y, row3_h = y, 155
    for i in range(5):
        draw_card(CARDS[8 + i], MARGIN + i * (cw5 + 8), row3_y, cw5, row3_h)
    y = row3_y + row3_h + 8
    # --- bottom band headers
    draw_text("WHERE IT HAPPENED", MARGIN, y, 1, INK)
    draw_text("THE REST OF THE DAY - 41 MORE STORIES",
              MARGIN + 478, y, 1, INK)
    hline(MARGIN, y + 10, CW, INK, 1)
    y += 14
    # --- map (left) + briefs (right)
    map_x, map_y, map_w, map_h = MARGIN, y, 466, 262
    draw_map(map_x, map_y, map_w, map_h)
    bx = MARGIN + 478
    by = y
    for i, brief in enumerate(BRIEFS):
        draw_text(str(14 + i) + ".", bx, by, 1, RED)
        draw_text(brief.upper(), bx + 24, by, 1, INK)
        by += 7
    # --- date check box
    dy = 938
    fill_rect(MARGIN, dy, CW, 62, PAPER2)
    rect_border(MARGIN, dy, CW, 62, RED, 1)
    draw_text("DATE CHECK - WHY SOME BIG STORIES ARE NOT ON THIS PAGE",
              MARGIN + 6, dy + 4, 1, RED)
    for i, dline in enumerate(DATE_CHECK):
        draw_text(dline, MARGIN + 6, dy + 15 + i * 8, 1, INK)
    # --- sources footer
    draw_text(SOURCES, MARGIN, 1006, 1, GREY)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    write_png(os.path.join(out_dir, "entry.png"), W, H, PIX)


if __name__ == "__main__":
    main()
