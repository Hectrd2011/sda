"""YouTube thumbnail for the Russia-Ukraine war video (1280x720), in the style of the other
"every day with army sizes" thumbnails: the map in March 2022, big troop numbers, soldier icons
for each side and arrows for the Russian invasion routes."""
import os
import sys

import numpy as np
from PIL import Image

import render as R
import timeline as T
from thumbkit import arrow, big_number, fmt, icon_grid

W, H = 1920, 1080
DAY = T.as_day("2022-03-20")
BLUE, RED = (52, 100, 205), (185, 40, 34)


def main(out):
    r = R.Renderer(W, H)
    img = Image.fromarray(r.map_layer(DAY)).convert("RGBA")
    P = lambda lon, lat: r.P([(lon, lat)])[0]
    # crop: Ukraine, with Russia to the east for the Russian number
    x0, x1 = P(22.0, 48.5)[0], P(41.5, 48.5)[0]
    w = x1 - x0
    h = w * 9 / 16
    cy = P(31.5, 48.6)[1]
    box = (int(x0), int(cy - h / 2), int(x0 + w), int(cy + h / 2))
    img = img.crop(box)
    k = 3840 / img.width
    img = img.resize((3840, 2160), Image.LANCZOS)
    Q = lambda lon, lat: (P(lon, lat) - np.array(box[:2])) * k
    S = 3840 / 1280

    # the invasion routes of February-March 2022
    for pts in [[(29.9, 51.95), (30.1, 51.4), (30.35, 50.75)],     # Belarus -> Kyiv
                [(33.8, 51.9), (32.9, 51.3), (31.4, 50.7)],      # Russia -> Chernihiv -> Kyiv
                [(37.3, 50.7), (36.9, 50.3), (36.35, 50.05)],    # Belgorod -> Kharkiv
                [(34.0, 45.8), (33.4, 46.3), (32.7, 46.6)],      # Crimea -> Kherson
                [(34.6, 45.9), (35.5, 46.6), (37.3, 47.1)]]:     # Crimea -> Mariupol
        arrow(img, [Q(*p) for p in pts], 7 * S)

    # troop numbers from the video's data on this day
    tot = {"A": 0, "B": 0}   # A = Ukraine, B = Russia
    for fr in r.fronts:
        for lab in fr["labels"]:
            if lab["side"] in tot:
                tot[lab["side"]] += r.army_value(lab, DAY)
    big_number(img, fmt(tot["A"]), *Q(27.6, 49.0), 80 * S, 6)
    big_number(img, fmt(tot["B"]), *Q(39.1, 49.35), 80 * S, -8)

    # soldier icons: Ukraine bottom-left (Romania/Moldova side), Russia top-right
    icon_grid(img, 0.16 * W * 2, 0.86 * H * 2, 6, 2, 56 * S, BLUE)
    icon_grid(img, 0.84 * W * 2, 0.13 * H * 2, 7, 2, 56 * S, RED)

    img.convert("RGB").resize((1280, 720), Image.LANCZOS).save(out, quality=95)
    print(out, tot)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                                                           "Russia_Ukraine_War_thumbnail.jpg"))
