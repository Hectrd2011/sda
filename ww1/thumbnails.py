"""YouTube thumbnails for the two WW1 videos (Europe and World), drawn from the videos' own map and data."""
import os
import sys

import numpy as np
from PIL import Image

import render as R
import timeline as T
from thumbkit import arrow, big_number, finish, fmt, icon_grid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 3840, 2160
S = W / 1280
CP_COL, ENT_COL = (30, 32, 26), (40, 70, 200)


def side_totals(r, day):
    """Army totals per side from every label in the video at this moment."""
    tot = {"CP": 0, "ENT": 0}
    for fr in r.fronts:
        for lab in fr["labels"]:
            occ = fr["sides"][lab["side"]]["occ"]
            tot["CP" if occ == "CP" else "ENT"] += r.army_value(lab, day)
    for p in r.pockets:
        for i, lab in enumerate(p["labels"]):
            tot["ENT" if (i % 2 == 0 and p["occ"] == "ENT") or (p["occ"] == "CP" and i % 2) else "CP"] += \
                r.army_value(lab, day)
    for i, lab in enumerate(r.point_labels):
        tot["ENT" if i % 2 == 0 else "CP"] += r.army_value(lab, day)
    return tot


def front_values(r, day, name):
    fr = next(f for f in r.fronts if f["name"] == name)
    out = {"CP": 0, "ENT": 0}
    for lab in fr["labels"]:
        occ = fr["sides"][lab["side"]]["occ"]
        out["CP" if occ == "CP" else "ENT"] += r.army_value(lab, day)
    return out


def europe(out):
    day = T.as_day("1916-06-20") + 0.5
    r = R.Renderer(W, H)
    img = Image.fromarray(r.map_layer(day)).convert("RGBA")
    P = lambda lon, lat: np.array(r.fr.px(lon, lat))
    # the Brusilov Offensive and the Somme
    for a, b, c in [((29.0, 51.0), (26.8, 50.6), (24.8, 50.1)), ((28.8, 49.4), (26.6, 48.9), (24.8, 48.3)),
                    ((1.2, 49.6), (2.0, 49.9), (2.9, 50.0))]:
        arrow(img, [P(*a), P(*b), P(*c)], 8 * S)
    west, east = front_values(r, day, "Western Front"), front_values(r, day, "Eastern Front")
    big_number(img, fmt(west["CP"]), *P(7.2, 50.9), 48 * S, -58)
    big_number(img, fmt(west["ENT"]), *P(0.2, 48.4), 48 * S, -58)
    big_number(img, fmt(east["CP"]), *P(22.6, 52.6), 58 * S, -72)
    big_number(img, fmt(east["ENT"]), *P(29.8, 53.4), 62 * S, -72)
    icon_grid(img, *P(15.5, 51.3), 5, 2, 50 * S, CP_COL)
    icon_grid(img, *P(-4.5, 53.8), 3, 2, 42 * S, ENT_COL)
    icon_grid(img, *P(42.0, 52.5), 7, 4, 50 * S, ENT_COL)
    finish(img, out)


def world(out):
    day = T.as_day("1917-06-01") + 0.5
    r = R.Renderer(W, H, view="world")
    img = Image.fromarray(r.map_layer(day)).convert("RGBA")
    P = lambda lon, lat: np.array(r.fr.px(lon, lat))
    tot = side_totals(r, day)
    # America joins the war; the Allies push into Palestine
    arrow(img, [P(-72, 40), P(-40, 50), P(-8, 47)], 9 * S)
    arrow(img, [P(31, 30.5), P(33.5, 32.5), P(35.4, 33.6)], 7 * S)
    big_number(img, fmt(tot["CP"]), *P(-24, 30), 60 * S, 0)
    big_number(img, fmt(tot["ENT"]), *P(92, 55), 72 * S, 0)
    icon_grid(img, *P(-24, 2), 5, 2, 46 * S, CP_COL)
    icon_grid(img, *P(-125, 15), 8, 4, 46 * S, ENT_COL)
    finish(img, out)


if __name__ == "__main__":
    which = sys.argv[1:] or ["europe", "world"]
    if "europe" in which:
        europe(os.path.join(ROOT, "WW1_Europe_thumbnail.jpg"))
    if "world" in which:
        world(os.path.join(ROOT, "WW1_World_thumbnail.jpg"))
