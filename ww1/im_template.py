"""Extracts Italian Mapper's map template (a Paint.NET file the channel owner has) for the Europe view.

The template is 7680x4320, Mercator. Layers, bottom to top:
  Layer 4     sea (224,234,248)
  Layer 3     black land, a little bigger than the white land (not used: his videos show no dark rim on the coasts)
  Background  white land (255,252,249)
  Layer 2     satellite texture at opacity 45/255
  Borders     modern borders in pink (not used, the renderer draws the 1914 borders)

Writes build/downloads/im_template_europe.npz with
  rgb     land colour (white + satellite), uint8
  land    white-land coverage 0..255 (the coastline)
  box     x0, y0, x1, y1 of the crop in template pixels
  proj    x0, px per degree of longitude, y of the equator, Mercator y scale (template pixels)
Usage: python3 im_template.py [template.pdn]
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DL = os.path.join(HERE, "build", "downloads")
# fitted on the template's European coasts against Natural Earth (IoU 0.973)
PROJ = (3623.14996187, 22.61357225, 2815.09104704, 1297.28831166)
BOX = (2831, 94, 5319, 2400)       # lon -35..75, lat 18..76


def main():
    import pypdn
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DL, "italian_mapper_template.pdn")
    layers = {l.name: l for l in pypdn.read(src).layers}
    x0, y0, x1, y1 = BOX
    crop = lambda name: layers[name].image[y0:y1, x0:x1].astype(np.float32)
    white, sat = crop("Background"), crop("Layer 2")
    a = sat[..., 3:] / 255.0 * layers["Layer 2"].opacity / 255.0
    rgb = np.array([255, 252, 249], np.float32) * (1 - a) + sat[..., :3] * a
    np.savez_compressed(os.path.join(DL, "im_template_europe.npz"),
                        rgb=np.round(rgb).astype(np.uint8), land=white[..., 3].astype(np.uint8),
                        box=np.array(BOX), proj=np.array(PROJ))
    print("wrote", os.path.join(DL, "im_template_europe.npz"))


if __name__ == "__main__":
    main()
