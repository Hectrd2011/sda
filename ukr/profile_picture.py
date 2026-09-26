"""Channel profile picture (800x800, shown as a circle): a close-up of a front line in the style of
the videos - blue and red territory, the white front line between them - with a soldier on each side."""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

import render as R
import timeline as T
from thumbkit import soldier

N = 800


def main(out):
    r = R.Renderer(3840, 2160)
    img = np.array(Image.fromarray(r.map_layer(T.as_day("2023-03-01"))))
    cx, cy = r.P([(38.0, 48.6)])[0]           # Bakhmut: the front runs north-south here
    h = 360
    crop = img[int(cy) - h:int(cy) + h, int(cx) - h - 60:int(cx) + h - 60].astype(np.float32)
    # stronger, flatter colours than the video so they read at thumbnail size
    blue = (crop[..., 2] > crop[..., 0] + 20)
    red = (crop[..., 0] > crop[..., 2] + 20)
    blue = ndimage.binary_opening(blue, iterations=2)
    red = ndimage.binary_opening(red, iterations=2)
    # every other pixel (old border lines, labels) takes the colour of the nearest side
    cls = np.where(blue, 1, np.where(red, 2, 0))
    _, (iy, ix) = ndimage.distance_transform_edt(cls == 0, return_indices=True)
    cls = cls[iy, ix]
    blue, red = cls == 1, cls == 2
    shade = crop.mean(2, keepdims=True) / crop.mean()
    out_img = np.where(blue[..., None], np.array([48, 104, 200]) * (0.85 + 0.15 * shade), crop)
    out_img = np.where(red[..., None], np.array([196, 52, 44]) * (0.85 + 0.15 * shade), out_img)
    # thick white front line where blue meets red
    line = ndimage.binary_dilation(blue, iterations=7) & ndimage.binary_dilation(red, iterations=7)
    soft = ndimage.gaussian_filter(line.astype(np.float32), 2.0)[..., None]
    out_img = out_img * (1 - soft) + 255 * soft
    im = Image.fromarray(np.clip(out_img, 0, 255).astype(np.uint8)).resize((N, N), Image.LANCZOS).convert("RGBA")

    # one soldier on each side, white with a soft shadow
    shadow = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    figs = [(240, 250, 300), (590, 250, 300)]
    for x, y, s in figs:
        soldier(sd, x + 8, y + 10, s, (0, 0, 0, 150))
    im.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    for x, y, s in figs:
        soldier(d, x, y, s, (255, 255, 255, 255))
    im.convert("RGB").save(out, quality=95)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../profile_picture.png")
