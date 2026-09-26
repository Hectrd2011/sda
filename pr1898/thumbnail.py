"""YouTube thumbnail for the 1898 Puerto Rican Campaign video (1280x720), in the style of the
"every day with army sizes" thumbnails: map at the height of the campaign, big army numbers,
soldier icons for each side and arrows for the US advance."""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import render_1898 as R
import timeline_1898 as T

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ww1"))
from thumbkit import arrow, big_number, icon_grid  # noqa: E402

W, H = 3840, 2160
DAY = T.as_day("1898-08-11 18:00")
BLUE, GOLD = (52, 92, 210), (205, 150, 30)


def main(out):
    r = R.Renderer(W, H)
    pan = r.pan["puertorico"]
    img = Image.fromarray(pan.render(DAY)).convert("RGBA")
    P = lambda lon, lat: np.array(pan.fr.px(lon, lat))
    # crop: the island, with sea above and below for the icons
    x0, x1 = P(-67.35, 18)[0], P(-65.55, 18)[0]
    w = x1 - x0
    h = w * 9 / 16
    cy = P(-66.5, 18.2)[1]
    box = (int(x0), int(cy - h / 2), int(x0 + w), int(cy + h / 2))
    img = img.crop(box)
    k = W / img.width
    img = img.resize((W, H), Image.LANCZOS)
    Q = lambda lon, lat: (P(lon, lat) - np.array(box[:2])) * k
    S = W / 1280

    # arrows: the US advance inland from the south coast
    for a, b, c in [((-66.9, 17.97), (-67.02, 18.07), (-67.13, 18.19)),   # Guanica -> Mayaguez
                    ((-66.62, 18.02), (-66.69, 18.11), (-66.71, 18.24)),  # Ponce -> Utuado
                    ((-66.5, 18.05), (-66.38, 18.08), (-66.3, 18.13)),    # Juana Diaz -> Coamo -> Aibonito
                    ((-66.08, 17.96), (-66.1, 18.02), (-66.14, 18.08))]:  # Guayama -> Cayey
        arrow(img, [Q(*a), Q(*b), Q(*c)], 7 * S)

    # army numbers from the video's data at this moment
    val = {l["name"]: r.army_value(l, DAY) for l in r.labels}
    us = sum(v for n, v in val.items() if "Spanish" not in n)
    esp = val["Spanish forces"]
    big_number(img, f"{esp:,}".replace(",", "."), *Q(-66.35, 18.37), 78 * S, 8)
    big_number(img, f"{us:,}".replace(",", "."), *Q(-66.6, 17.84), 78 * S, -6)

    # soldier icons: Spain north (sea), US south (sea, where they landed)
    icon_grid(img, 0.79 * W, 0.125 * H, 7, 2, 56 * S, GOLD)
    icon_grid(img, 0.15 * W, 0.87 * H, 6, 2, 56 * S, BLUE)

    img.convert("RGB").resize((1280, 720), Image.LANCZOS).save(out, quality=95)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "PR_Campaign_1898_thumbnail.jpg")
