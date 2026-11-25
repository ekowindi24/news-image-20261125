# The World Today — Wednesday 25 November 2026

[![Make.fun Competition](https://make.fun/badge/competition/news-image-20261125)](https://make.fun/bounty/news-image-20261125)
[![Make.fun Entry](https://make.fun/badge/entry/news-image-20261125)](https://make.fun/bounty/news-image-20261125)
[![Built with Muse](https://make.fun/badge/built-with/muse)](https://make.fun)

One picture that sums up Wednesday 25 November 2026: 54 dated stories from
seven regions, drawn as a newspaper front page — 13 illustrated cards, 41
one-line briefs, a map of where it happened, region and field tallies, the
day's numbers, and a date-check box that keeps Tuesday's news out of the
main story.

## How the page is made

`main.py` is a single self-contained script. It draws everything by hand on
a pixel buffer — a tiny 5x7 bitmap font, a small canvas class, thirteen
little illustrated panels, and a simplified world map — then writes the
result out as a PNG. No third-party packages, no network calls, no random
numbers: running it twice gives the same file, byte for byte.

```sh
python3 main.py
```

That leaves `out/entry.png`, 1024 by 1024 pixels and well under a megabyte.
Set `MAKEFUN_OUTPUT_DIR` to put the file somewhere else.

## What is on the page

- **13 illustrated cards** — Shenzhou-24 and the first Pakistani in orbit;
  the Asia-wide market selloff; the Gaza strike and the Houthis' threat to
  Jeddah; the incoming USTR tariff findings; Iran and the US blockade; the
  Knesset vote; Shanghai; Australia's 4.9% CPI shock; the Caribbean tanker
  seizures; Odesa; Brent above $90; and a 14-year-old's 204 off 53 balls.
- **41 briefs** — the rest of the day, one line each.
- **Where it happened** — a world map with numbered pins for all 13 cards.
- **The day in numbers** — 54 stories, 7 regions, 13 cards, 41 briefs.
- **Date check** — Tuesday 24 November items, labelled as Tuesday's, so
  nothing from the day before is passed off as today's news.

## Sources

Reuters, AP, BBC, Al Jazeera, The Guardian, WSJ, Bloomberg, Xinhua, Yonhap,
DPA, Anadolu and Kyodo — every key figure on the page was checked against a
primary source on 25 November 2026.

---

Made with [Muse](https://make.fun/r/h0jjpkje) for the
[news-image-20261125](https://make.fun/bounty/news-image-20261125) bounty.
