"""Shared drawing helpers for the YouTube thumbnails (style of the "every day with army sizes" videos):
big white army numbers, soldier-icon grids and curved advance arrows."""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")


def font(size):
    return ImageFont.truetype(os.path.join(FONTS, "LiberationSans-Bold.ttf"), int(size))


def soldier(d, x, y, s, col):
    """Simple standing-soldier pictogram, (x, y) = top of the head, s = height."""
    hr = s * 0.13
    d.ellipse([x - hr, y, x + hr, y + 2 * hr], fill=col)
    bw = s * 0.34
    d.rounded_rectangle([x - bw / 2, y + 2.3 * hr, x + bw / 2, y + s * 0.62], radius=s * 0.06, fill=col)
    lw = s * 0.12
    d.rectangle([x - bw / 2, y + s * 0.6, x - bw / 2 + lw, y + s], fill=col)
    d.rectangle([x + bw / 2 - lw, y + s * 0.6, x + bw / 2, y + s], fill=col)
    aw = s * 0.08
    d.rectangle([x - bw / 2 - aw, y + 2.5 * hr, x - bw / 2, y + s * 0.55], fill=col)
    d.rectangle([x + bw / 2, y + 2.5 * hr, x + bw / 2 + aw, y + s * 0.55], fill=col)
    d.line([x + bw / 2 + aw / 2, y + s * 0.05, x + bw / 2 + aw / 2, y + s * 0.6], fill=col, width=int(aw * 0.6))


def icon_grid(img, cx, cy, cols, rows, s, col):
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    for i in range(rows):
        for j in range(cols):
            soldier(g, cx + (j - (cols - 1) / 2) * s * 0.62, cy + (i - rows / 2) * s * 1.12, s, (255, 255, 255, 255))
    glow = glow.filter(ImageFilter.GaussianBlur(s * 0.12))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    for i in range(rows):
        for j in range(cols):
            soldier(d, cx + (j - (cols - 1) / 2) * s * 0.62, cy + (i - rows / 2) * s * 1.12, s, col + (255,))


def big_number(img, text, cx, cy, size, angle):
    f = font(size)
    bb = f.getbbox(text)
    pad = int(size * 0.3)
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    sh = Image.new("L", (w, h), 0)
    ImageDraw.Draw(sh).text((pad - bb[0] + size * 0.05, pad - bb[1] + size * 0.05), text, font=f, fill=200)
    sh = sh.filter(ImageFilter.GaussianBlur(size * 0.07))
    t = Image.merge("RGBA", (*Image.new("RGB", (w, h), (15, 15, 20)).split(), sh))
    ImageDraw.Draw(t).text((pad - bb[0], pad - bb[1]), text, font=f, fill=(255, 255, 255, 255),
                           stroke_width=int(size * 0.035), stroke_fill=(40, 40, 50, 255))
    t = t.rotate(angle, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(t, (int(cx - t.width / 2), int(cy - t.height / 2)))


def arrow(img, pts, width, col=(35, 35, 40, 235)):
    """Curved arrow through lon/lat points (already in pixels)."""
    pts = np.array(pts, float)
    t = np.linspace(0, 1, 60)
    # quadratic Bezier through the middle point
    p0, p1, p2 = pts
    c = 2 * p1 - (p0 + p2) / 2
    curve = ((1 - t) ** 2)[:, None] * p0 + (2 * (1 - t) * t)[:, None] * c + (t ** 2)[:, None] * p2
    d = ImageDraw.Draw(img)
    d.line([tuple(p) for p in curve[:-4]], fill=col, width=int(width), joint="curve")
    tip, back = curve[-1], curve[-6]
    v = (tip - back) / (np.linalg.norm(tip - back) + 1e-9)
    nrm = np.array([-v[1], v[0]])
    L = width * 3.2
    d.polygon([tuple(tip), tuple(tip - v * L + nrm * L * 0.6), tuple(tip - v * L - nrm * L * 0.6)], fill=col)


def fmt(v):
    return f"{int(v):,}".replace(",", ".")


def finish(img, out):
    img.convert("RGB").resize((1280, 720), Image.LANCZOS).save(out, quality=95)
    print(out)
