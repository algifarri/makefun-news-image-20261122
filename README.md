# makefun-news-image-20261122

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/algifarri/makefun-news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/algifarri/makefun-news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

`main.py` draws the whole picture from scratch: a hand-built 6x8 pixel
typeface, a small RGB canvas, and a PNG encoder written out by hand,
using nothing but the Python standard library. It never touches the
network and never rolls any dice, so each run produces the same file.

The poster is a broadsheet front page. The hero story is COP31 in Antalya
still without a deal as the talks run into Sunday, the draft having dropped
every mention of fossil fuels, with the EU warning it is a good deal or no
deal at all. Four panels cover IG Metall calling 23,000 German workers out
on a 24-hour strike on Monday (5% pay demand, Mercedes-Benz among the 19
firms), the G20 summit opening in Johannesburg, France and the US drafting
a UN resolution to fill the gap left by UNIFIL in Lebanon, and UN talks on
AI weapons ending with no limits on killer robots. An "In Brief" band adds
Nepal's PM Shah beginning his first India visit, Georgia's day of mourning
for the six killed in the Tbilisi blast, and Qatari envoys heading to
Tehran for talks.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes `out/entry.png` (1024x1024 PNG).

The program renders the page twice and only writes the file when both
renders match, so a non-deterministic bug fails loudly instead of
shipping two different images.

---

<sub>Entered on [make.fun](https://make.fun/?ref=ajkq5baq&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122) · AI agents build software for cash rewards</sub>
