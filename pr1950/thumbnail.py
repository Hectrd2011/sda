"""YouTube thumbnail for the 1950 Puerto Rican Nationalist uprisings video."""
import os
import sys

import numpy as np
from PIL import Image

import render_pr as R
import timeline_pr as T

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "ww1"))
from thumbkit import arrow, big_number, finish, fmt, icon_grid  # noqa: E402

W, H = 3840, 2160
S = W / 1280
DAY = T.as_day("1950-10-30 22:00")
BLUE, RED = (40, 70, 200), (190, 45, 38)


def main(out):
    r = R.Renderer(W, H)
    pan = r.pan["puertorico"]
    img = Image.fromarray(pan.render(DAY)).convert("RGBA")
    P = lambda lon, lat: np.array(pan.fr.px(lon, lat))
    x0, x1 = P(-67.35, 18)[0], P(-65.55, 18)[0]
    w = x1 - x0
    h = w * 9 / 16
    cy = P(-66.5, 18.2)[1]
    box = (int(x0), int(cy - h / 2), int(x0 + w), int(cy + h / 2))
    img = img.crop(box).resize((W, H), Image.LANCZOS)
    k = W / (box[2] - box[0])
    Q = lambda lon, lat: (P(lon, lat) - np.array(box[:2])) * k
    val = {l["name"]: r.army_value(l, DAY) for l in r.labels}
    # the National Guard converges on Jayuya and Utuado
    for a, b, c in [((-66.1, 18.42), (-66.35, 18.3), (-66.55, 18.23)),
                    ((-66.72, 18.46), (-66.72, 18.38), (-66.7, 18.3)),
                    ((-66.6, 18.02), (-66.62, 18.1), (-66.6, 18.19))]:
        arrow(img, [Q(*a), Q(*b), Q(*c)], 7 * S)
    big_number(img, fmt(val["Government forces"]), *Q(-66.0, 18.575), 78 * S, 0)
    big_number(img, fmt(val["Nationalist fighters"]), *Q(-66.95, 17.83), 78 * S, 0)
    icon_grid(img, 0.8 * W, 0.87 * H, 8, 2, 56 * S, BLUE)
    icon_grid(img, 0.4 * W, 0.87 * H, 2, 2, 56 * S, RED)
    finish(img, out)


if __name__ == "__main__":
    main(os.path.join(ROOT, "PR_Nationalist_Uprisings_1950_thumbnail.jpg"))
