import numpy as np, subprocess, imageio_ffmpeg
from scipy import ndimage
FF = imageio_ffmpeg.get_ffmpeg_exe()
def frames(t0, t1):
    raw = subprocess.run([FF, "-v", "error", "-ss", str(t0), "-t", str(t1 - t0), "-i", "ww2_ref.mp4",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 144, 256, 3).astype(np.int16)
F = frames(250, 290)   # 22 Jun 1941 onwards
print("frames", len(F))
r, g, b = F[..., 0], F[..., 1], F[..., 2]
sov = (r - g > 45) & (r > 150)
axis = (abs(r - g) < 18) & (abs(g - b) < 22) & (r < 150) & (r > 60)
white = (r > 215) & (g > 215) & (b > 215)
# 1) front position: for rows 40..110, first Soviet column east of x=120
rows = range(40, 110, 5)
pos = np.array([[np.argmax(sov[i, y, 120:]) + 120 for y in rows] for i in range(len(F))], float)
d = np.diff(pos, axis=0)
moving = (np.abs(d) > 0).mean(1)
print("fraction of rows whose front moved, per frame (first 60):")
print(np.round(moving[:60], 2))
area = sov[:, :, 120:].sum((1, 2))
print("soviet area per frame (first 60):", area[:60].tolist())
# 2) labels: white blobs over coloured land, track centroid + angle
for i in range(0, len(F), 15):
    lab, n = ndimage.label(ndimage.binary_dilation(white[i], iterations=2))
    out = []
    for k in range(1, n + 1):
        ys, xs = np.nonzero((lab == k) & white[i])
        if len(xs) < 12 or xs.mean() < 120: continue
        c = np.cov(np.stack([xs, ys]))
        w, v = np.linalg.eigh(c)
        ang = np.degrees(np.arctan2(v[1, 1], v[0, 1]))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        out.append((round(xs.mean(), 1), round(ys.mean(), 1), len(xs), round(-ang, 1), round(np.sqrt(w[1] / max(w[0], 1e-3)), 1)))
    print(f"t={250 + i / 15:.1f}s labels(x,y,npix,angle,elong):", out)
