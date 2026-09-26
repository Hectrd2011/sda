import numpy as np, subprocess, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
# 4K crop around the central front during Barbarossa, 10 fps, downscaled 2x (1080p-equivalent pixels)
t0, dur, fps = 250.0, 12.0, 10
raw = subprocess.run([FF, "-v", "error", "-ss", str(t0), "-t", str(dur), "-i", "ww2_4k.webm",
                      "-vf", f"crop=1200:1000:1800:350,scale=600:500,fps={fps}", "-f", "rawvideo",
                      "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
F = np.frombuffer(raw, np.uint8).reshape(-1, 500, 600, 3).astype(np.float32)
np.save("barb.npy", F.astype(np.uint8))
r, g, b = F[..., 0], F[..., 1], F[..., 2]
L = F.mean(3)
red = (r - g > 35) & (r - b > 35)                      # Soviet terracotta
green = (np.abs(r - g) < 25) & (g - b > -5) & (L < 150) & (r - b < 40)   # Axis olive-grey
pale = (L > 185) & (F.max(3) - F.min(3) < 60)           # cream fringe / white line
print("frames", len(F))
# pixels that start red and end green
cand = red[0] & green[-1]
ys, xs = np.nonzero(cand)
print("captured pixels", len(ys))
# for each: first frame not red, first frame green; how many frames pale in between / after
res = []
for y, x in zip(ys[::7], xs[::7]):
    nr = np.argmax(~red[:, y, x]); ng = np.argmax(green[:, y, x])
    npale = pale[nr:, y, x].sum()
    res.append((nr, ng, ng - nr, npale))
res = np.array(res)
print("frames from leaving red to being green: median %.1f  p90 %.1f" % (np.median(res[:, 2]), np.percentile(res[:, 2], 90)))
print("frames spent pale: median %.1f  p90 %.1f" % (np.median(res[:, 3]), np.percentile(res[:, 3], 90)))
# average colour trajectory after the moment a pixel stops being red
traj = []
for y, x in zip(ys[::7], xs[::7]):
    nr = np.argmax(~red[:, y, x])
    if nr + 25 < len(F):
        traj.append(F[nr - 2:nr + 25, y, x])
traj = np.array(traj)
m = traj.mean(0)
for i in range(0, len(m), 2):
    print(f"{(i - 2) / fps:+.1f}s", np.round(m[i]).astype(int))
