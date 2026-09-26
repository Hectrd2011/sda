"""Profile picture variations (800x800 each) plus a contact sheet showing them as circles."""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

import render as R
import timeline as T
from thumbkit import arrow, big_number, soldier

N = 800
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profile_pictures")


def front_masks():
    r = R.Renderer(3840, 2160)
    img = np.array(Image.fromarray(r.map_layer(T.as_day("2023-03-01"))))
    cx, cy = r.P([(38.0, 48.6)])[0]
    h = 360
    crop = img[int(cy) - h:int(cy) + h, int(cx) - h - 60:int(cx) + h - 60].astype(np.float32)
    blue = ndimage.binary_opening(crop[..., 2] > crop[..., 0] + 20, iterations=2)
    red = ndimage.binary_opening(crop[..., 0] > crop[..., 2] + 20, iterations=2)
    cls = np.where(blue, 1, np.where(red, 2, 0))
    _, (iy, ix) = ndimage.distance_transform_edt(cls == 0, return_indices=True)
    cls = cls[iy, ix]
    shade = crop.mean(2, keepdims=True) / crop.mean()
    return cls == 1, cls == 2, shade


def base(masks, col_a, col_b, line=(255, 255, 255), texture=0.15):
    blue, red, shade = masks
    k = (1 - texture) + texture * shade
    out = np.where(blue[..., None], np.array(col_a) * k, np.array(col_b) * k)
    edge = ndimage.binary_dilation(blue, iterations=7) & ndimage.binary_dilation(red, iterations=7)
    soft = ndimage.gaussian_filter(edge.astype(np.float32), 2.0)[..., None]
    out = out * (1 - soft) + np.array(line) * soft
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((N, N), Image.LANCZOS).convert("RGBA")


def shadowed(im, draw_fn, blur=10, off=(8, 10), alpha=150):
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(sh), (0, 0, 0, alpha), off)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    draw_fn(ImageDraw.Draw(im), (255, 255, 255, 255), (0, 0))


def soldiers(im, figs=((240, 250, 300), (590, 250, 300))):
    shadowed(im, lambda d, c, o: [soldier(d, x + o[0], y + o[1], s, c) for x, y, s in figs])


def sword(d, cx, cy, ang, L, col):
    """A simple sword centred at (cx, cy), pointing along ang (degrees)."""
    v = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
    n = np.array([-v[1], v[0]])
    c = np.array([cx, cy])
    tip, guard = c + v * L * 0.55, c - v * L * 0.2
    w = L * 0.045
    d.polygon([tuple(tip), tuple(guard + n * w), tuple(guard - n * w)], fill=col)
    d.line([tuple(guard + n * L * 0.13), tuple(guard - n * L * 0.13)], fill=col, width=int(L * 0.05))
    d.line([tuple(guard), tuple(guard - v * L * 0.22)], fill=col, width=int(L * 0.055))
    p = guard - v * L * 0.26
    d.ellipse([p[0] - L * 0.04, p[1] - L * 0.04, p[0] + L * 0.04, p[1] + L * 0.04], fill=col)


def swords(im):
    shadowed(im, lambda d, c, o: [sword(d, 400 + o[0], 400 + o[1], a, 560, c) for a in (-45, -135)])


def main():
    os.makedirs(OUT, exist_ok=True)
    m = front_masks()
    BLUE, RED = (48, 104, 200), (196, 52, 44)
    v = {}
    im = base(m, BLUE, RED); soldiers(im); v["1_soldiers"] = im
    im = base(m, BLUE, RED); big_number(im, "1914", 400, 400, 230, 62); v["2_number"] = im
    im = base(m, BLUE, RED)
    arrow(im, [(170, 560), (300, 470), (360, 330)], 34, (255, 255, 255, 255))
    arrow(im, [(640, 260), (520, 330), (450, 470)], 34, (25, 25, 30, 240))
    v["3_arrows"] = im
    im = base(m, BLUE, RED); swords(im); v["4_swords"] = im
    im = base(m, (70, 110, 175), (125, 125, 118), texture=0.25); soldiers(im); v["5_ww1_colours"] = im
    im = base(m, (22, 48, 104), (104, 24, 24), line=(245, 245, 235), texture=0.3); swords(im); v["6_dark"] = im
    for k, im in v.items():
        im.convert("RGB").save(os.path.join(OUT, f"profile_{k}.png"))
    # contact sheet: how each one looks as YouTube's circle
    cell, pad = 300, 40
    sheet = Image.new("RGB", (3 * cell + 4 * pad, 2 * (cell + 60) + pad), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    mask = Image.new("L", (cell, cell), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, cell - 1, cell - 1], fill=255)
    from thumbkit import font
    for i, (k, im) in enumerate(v.items()):
        x, y = pad + (i % 3) * (cell + pad), pad + (i // 3) * (cell + 60)
        sheet.paste(im.resize((cell, cell), Image.LANCZOS).convert("RGB"), (x, y), mask)
        d.text((x + cell / 2 - d.textlength(k[0], font=font(34)) / 2, y + cell + 8), k[0], font=font(34), fill=(240, 240, 240))
    sheet.save(os.path.join(OUT, "all_variations.png"))
    print(OUT)


if __name__ == "__main__":
    main()
