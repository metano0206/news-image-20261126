# THE DAILY ORBIT — news-image-20261126

[![make.fun](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/metano0206/news-image-20261126/rank.svg)](https://make.fun/bounty/news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/metano0206/news-image-20261126/reward.svg)](https://make.fun/bounty/news-image-20261126)

An entry for make.fun's [news-image-20261126](https://make.fun/bounty/news-image-20261126):
sum up the world news of Thursday 26 November 2026 in one image.

`main.py` (Python 3.13, standard library only) draws a one-page newspaper —
masthead, a lead story with a night-skyline scene, four side panels and a
news ticker — with its own stroke font, rasterises it by hand and writes it
as a deterministic PNG to `$MAKEFUN_OUTPUT_DIR/entry.png`.

Run it:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3.13 main.py
```

The news data at the top of `main.py` is the verified news of 26 November
2026, each story checked against at least two major outlets.

Licensed under the MIT License (see `LICENSE`).
