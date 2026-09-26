"""YouTube thumbnail for the Spanish-American War / Philippine-American War video."""
import os
import sys

import numpy as np
from PIL import Image

import render_saw as R
import timeline_saw as T

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "ww1"))
from thumbkit import arrow, big_number, finish, fmt, icon_grid  # noqa: E402

W, H = 3840, 2160
S = W / 1280
DAY = T.as_day("1898-07-10") + 0.5
BLUE, GOLD, RED, GREEN = (40, 70, 200), (190, 140, 25), (190, 50, 40), (30, 130, 100)


def main(out):
    r = R.Renderer(W, H)
    frame = np.zeros((H, W, 3), np.uint8)
    frame[:] = (38, 42, 50)
    for p in r.panels:
        frame[:, p.fr.px0:p.fr.px0 + p.fr.pw] = p.render(DAY)
    img = Image.fromarray(frame).convert("RGBA")
    car, phl = r.pan["caribbean"].fr, r.pan["philippines"].fr
    C = lambda lon, lat: np.array(car.px(lon, lat))
    F = lambda lon, lat: np.array(phl.px(lon, lat))
    val = {l["name"]: r.army_value(l, DAY) for l in r.labels}
    # the US landing at Santiago and Dewey's fleet at Manila
    arrow(img, [C(-74.2, 18.4), C(-75.0, 19.3), C(-75.55, 19.85)], 8 * S)
    arrow(img, [F(118.2, 13.2), F(119.6, 14.3), F(120.75, 14.5)], 8 * S)
    big_number(img, fmt(val["Spanish army in Cuba"]), *C(-80.3, 23.4), 64 * S, 0)
    big_number(img, fmt(val["US V Corps / Army of occupation"]), *C(-75.3, 18.6), 58 * S, 0)
    big_number(img, fmt(val["Filipino forces"]), *F(119.2, 16.4), 44 * S, 0)
    icon_grid(img, *C(-70.0, 26.6), 7, 2, 46 * S, GOLD)
    icon_grid(img, *C(-68.5, 16.5), 4, 2, 46 * S, BLUE)
    icon_grid(img, *F(119.4, 7.6), 4, 2, 38 * S, RED)
    finish(img, out)


if __name__ == "__main__":
    main(os.path.join(ROOT, "Spanish_American_War_thumbnail.jpg"))
