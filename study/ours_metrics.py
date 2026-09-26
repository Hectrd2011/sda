import sys, numpy as np
sys.path.insert(0, '/home/user/sda/ww1'); sys.path.insert(0, '/home/user/sda/study')
import render as R, timeline as T
from ref_metrics import *
RATE = 2.75          # days per second of video
FPS = 10
def frames(r, start, seconds, crop):
    x0, y0, x1, y1 = crop
    d0 = T.as_day(start)
    return np.stack([r.map_layer(d0 + i * RATE / FPS)[y0:y1, x0:x1] for i in range(int(seconds * FPS))]).astype(np.float32)
if __name__ == "__main__":
    r = R.Renderer(1920, 1080)
    F = frames(r, sys.argv[1], float(sys.argv[2]), tuple(int(v) for v in sys.argv[3].split(",")))
    np.save(sys.argv[4], F.astype(np.uint8)); print(F.shape)
