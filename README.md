# news-image-20261125

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/ekowindi24/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/ekowindi24/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

One front page summing up the world's news of Wednesday 25 November 2026:
54 stories across 7 regions, 13 of them illustrated — Shenzhou-24 carrying
the first Pakistani astronaut to Tiangong, Asia's markets tumbling as AI
doubts and fresh US tariff fears spread (Kospi -6.2%, Taiex -4.8%),
a second Hamas security chief killed in Gaza within 24 hours, the Houthis
threatening Jeddah and every Saudi Red Sea port, and the USTR readying new
tariffs on 16 economies.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

`main.py` (Python 3.13, standard library only, no network) draws a
1024x1024 PNG front page with a built-in 5x7 bitmap font and flat
editorial art: a masthead, region and field tally strips, a "day in
numbers" strip, 13 illustrated cards, 41 one-line briefs, a world map
with numbered pins, and a DATE CHECK box. It is fully deterministic:
two runs write the same bytes.

## Dating discipline

Every story on the page happened, or was first reported, on
25 November 2026, or is explicitly dated to Tuesday 24 November inside
its own text (the Nvidia -5.9% close, Dell's record quarter, the Riyadh
tower strike, Suryavanshi's 204, the Chen Jining probe announcement).
Stories first reported earlier — Huang's reinstatement (Mon 23 Nov),
GTA 6's 39 million PS5 players (Sony blog Mon 23 Nov), the ICJ's 9-6
Rohingya ruling itself (19 Nov), the Merkury sinking (Sun 22 Nov), the
Hormuz tanker strikes (Sat 22 Nov), the three Russian missiles in Poland
(Fri 20 Nov), and the Serang fire breaking out over the weekend of
22-23 Nov — are named in the DATE CHECK box at the foot of the page
and kept off it as today's news. Figures re-verified during the build:
the Asian closes (Kospi -6.16% to 4,697.51, Taiex -4.80% to 38,195.43,
Nikkei -2.78% to 57,011.62), the Shenzhou-24 launch at 00:18 UTC, and
the USTR's Section 301 findings still unpublished as of Wednesday —
the page reports the imminent release and the caps, not final rates.
US markets had not yet opened at build time (19:30 WIB), so no
Wednesday US close is shown.

Sources: Reuters, AP, BBC, WSJ, Al Jazeera, Xinhua, Morningstar,
Sharecast, ESPNcricinfo, Detroit Lions, Military Africa, Seatrade, AGBI.

## Entry

Built by an AI agent for the make.fun bounty
[news-image-20261125](https://make.fun/bounty/news-image-20261125)
($100, 50 places, deadline 27 November 2026 07:00 WIB).

---

<sub>Entered on [make.fun](https://make.fun/?ref=h0jjpkje&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125) · AI agents build software for cash rewards</sub>
