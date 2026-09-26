import numpy as np, subprocess, imageio_ffmpeg
from scipy import ndimage
FF = imageio_ffmpeg.get_ffmpeg_exe()
def frames(t0, t1):
    raw = subprocess.run([FF, "-v", "error", "-ss", str(t0), "-t", str(t1 - t0), "-i", "ww2_ref.mp4",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 144, 256, 3).astype(np.float32)
def labels(img):
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    L = img.mean(2)
    bg = ndimage.median_filter(L, 9)
    sat = img.max(2) - img.min(2)
    land = ndimage.binary_erosion((sat > 25) | ((L < 150) & (L > 60)), iterations=1)   # coloured, not sea/neutral
    m = (L - bg > 18) & ndimage.binary_dilation(land, iterations=3)
    m[:, :110] = False; m[130:] = False; m[:12] = False
    lab, n = ndimage.label(ndimage.binary_closing(m, iterations=2))
    out = []
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        if len(xs) < 15: continue
        c = np.cov(np.stack([xs, ys])); w, v = np.linalg.eigh(c)
        if w[1] / max(w[0], 1e-3) < 4: continue          # text runs are elongated
        ang = np.degrees(np.arctan2(v[1, 1], v[0, 1]))
        ang = (ang + 90) % 180 - 90
        side = "SOV" if img[int(ys.mean()), int(xs.mean()), 0] - img[int(ys.mean()), int(xs.mean()), 1] > 40 else "AXIS"
        out.append((side, xs.mean(), ys.mean(), 4 * np.sqrt(w[1]), ang))
    return out
import sys
t0, t1 = float(sys.argv[1]), float(sys.argv[2])
F = frames(t0, t1)
prev = {}
for i in range(0, len(F), 3):
    L = labels(F[i])
    print(f"{t0 + i / 15:6.1f}s " + "  ".join(f"{s}:({x:5.1f},{y:5.1f}) len{l:4.1f} ang{a:6.1f}" for s, x, y, l, a in sorted(L)))
