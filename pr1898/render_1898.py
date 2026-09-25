"""Renders the 1898 Puerto Rican Campaign map animation.

Usage:
    python3 render_1898.py info
    python3 render_1898.py preview "1898-08-09 12:00" [--w 1920 --h 1080]
    python3 render_1898.py video --w 3840 --h 2160 --jobs 4 --out build/pr1898_4k.mp4
"""
import argparse
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage
from shapely.geometry import Polygon

import panels_1898 as PN
import timeline_1898 as T

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
WW1 = os.path.join(os.path.dirname(HERE), "ww1")
FONTS = os.path.join(WW1, "assets", "fonts")
sys.path.insert(0, WW1)
import audio  # noqa: E402  (shared speech/music code from the WW1 project)

audio.BUILD = BUILD
FPS = 30
TARGET_SECONDS = 360.0
INTRO, OUTRO = 8.0, 20.0
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
END_DAY = (T.END - T.START).total_seconds() / 86400.0
CODES = {None: 0, "US": 1, "ESP": 2}


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def smooth(u):
    return u * u * (3 - 2 * u)


# ----------------------------------------------------------------------------- pacing
def pace_multiplier(day):
    t = T.date_at(day)
    if t < T.parse("1898-07-21"):
        return 12.0   # May - July: the naval war and the wait
    if t < T.parse("1898-07-25 04:00"):
        return 3.0
    if t < T.parse("1898-08-13 16:00"):
        return 1.0    # the campaign itself, hour by hour
    return 20.0       # armistice to handover


class Schedule:
    """Video time <-> calendar day. Speeches play in the background when their date is reached."""

    def __init__(self, meta):
        steps = np.arange(0, END_DAY, 1 / 24)
        inv = sum(1.0 / pace_multiplier(d) for d in steps) / 24
        self.rate = inv / (TARGET_SECONDS - INTRO - OUTRO)
        knots = [(0.0, 0.0), (INTRO, 0.0)]
        t, day = INTRO, 0.0
        while day < END_DAY - 1e-9:
            step = min(1 / 24, END_DAY - day)
            t += step / (self.rate * pace_multiplier(day))
            day += step
            knots.append((t, day))
        self.main_end = t
        knots.append((t + OUTRO, day))
        self.total = t + OUTRO
        self.kt = np.array([k[0] for k in knots])
        self.kd = np.array([k[1] for k in knots])
        self.speeches, free = [], INTRO + 0.5
        for s in T.SPEECHES:
            day = min(max(T.as_day(s["date"]), 0.0), END_DAY)
            t0 = max(float(np.interp(day, self.kd[1:], self.kt[1:])), free)
            m = meta[s["date"]]
            self.speeches.append(dict(s, t0=t0, duration=m["duration"], path=m["path"]))
            free = t0 + m["duration"] + 0.6

    def day(self, vt):
        return float(np.interp(vt, self.kt, self.kd))

    def vt_of(self, day):
        return float(np.interp(day, self.kd[1:], self.kt[1:]))


def load_schedule():
    return Schedule(audio.make_speeches(T.SPEECHES))


# ----------------------------------------------------------------------------- geometry
def chaikin(ring, iters=3):
    """Round off the corners of a closed ring (so control zones look like blobs, not boxes)."""
    a = np.asarray(ring, float)
    for _ in range(iters):
        b = np.roll(a, -1, 0)
        a = np.stack([0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b], 1).reshape(-1, 2)
    return a


def resample_ring(ring, n=240):
    a = chaikin(ring)
    a = np.concatenate([a, a[:1]])
    seg = np.sqrt(((a[1:] - a[:-1]) ** 2).sum(1))
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.stack([np.interp(t, s, a[:, 0]), np.interp(t, s, a[:, 1])], 1)


class Panel:
    def __init__(self, name, W, H, lite=False):
        self.name = name
        self.fr = PN.PanelFrame(name, W, H)
        b = PN.build(name, W, H)
        self.base, self.ids, self.land, self.border = b["base"], b["ids"], b["land"], b["border"]
        self.road, self.rail, self.slope = b["road"], b["rail"], b["slope"]
        fr = self.fr
        self.px_km = (fr.X1 - fr.X0) / fr.pw * math.cos(math.radians(18.2)) / 1000.0
        self._reach = {}
        self.key_of = {v: k for k, v in PN.KEY_ID.items()}
        self._victim = {}
        self._mask = {}
        self._mask_bytes = 0
        self.zones = []
        for z in T.ZONES:
            z = dict(dict(panel=name, kind="reach", occ="US", victims=["PRI"]), **z)
            zz = dict(z, a=T.as_day(z["start"]), b=T.as_day(z["end"]))
            if zz["kind"] == "reach":
                zz["kf"] = [(T.as_day(d), self.P(pts), float(R)) for d, pts, R in z["keys"]]
                self.zones.append(zz)
                continue
            if z.get("kind", "ellipse") == "poly":
                zz["kf"] = [(T.as_day(d), self.P(resample_ring(r))) for d, r in z["keys"]]
            else:
                zz["kf"] = [(T.as_day(d), np.array(e, float)) for d, *e in z["keys"]]
            self.zones.append(zz)
        # at 4K, work out recently-captured ground on a half-size twin (much faster, looks the same)
        self.lo = Panel(name, W // 2, H // 2, lite=True) if (not lite and W > 1920) else None
        self.lo_min = None

    def P(self, lonlat):
        a = np.asarray(lonlat, float)
        x, y = self.fr.px(a[:, 0], a[:, 1], local=True)
        return np.stack([x, y], 1)

    def victim_mask(self, victims):
        key = tuple(victims)
        if key not in self._victim:
            m = np.isin(self.ids, [PN.KEY_ID[k] for k in victims]).astype(np.float32) * self.land
            ys, xs = np.nonzero(m > 0)
            bb = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1) if len(xs) else None
            self._victim[key] = (m, bb)
        return self._victim[key]

    def poly_mask(self, poly, bb):
        key = (np.round(poly, 1).tobytes(), bb)
        if key in self._mask:
            return self._mask[key]
        x0, y0, x1, y1 = bb
        ss = 2
        im = Image.new("L", ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * ss, (y - y0) * ss) for x, y in poly], fill=255)
        m = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255.0
        self._mask_bytes += m.nbytes
        if self._mask_bytes > 200e6:
            self._mask.clear()
            self._mask_bytes = m.nbytes
        self._mask[key] = m
        return m

    def zone_shape(self, z, day):
        kf = z["kf"]
        if day <= kf[0][0]:
            v = kf[0][1]
        elif day >= kf[-1][0]:
            v = kf[-1][1]
        else:
            for (d0, v0), (d1, v1) in zip(kf, kf[1:]):
                if day <= d1:
                    v = v0 + (v1 - v0) * smooth((day - d0) / max(d1 - d0, 1e-9))
                    break
        if z.get("kind", "ellipse") == "poly":
            return v
        cx, cy, rx, ry = v
        if rx < 1e-3 and ry < 1e-3:
            return None
        t = np.linspace(0, 2 * np.pi, 64, endpoint=False)
        return self.P(np.stack([cx + rx * np.cos(t), cy + ry * np.sin(t)], 1))

    # -- areas that spread along roads and valleys ------------------------------------------------
    def island_window(self):
        if not hasattr(self, "_win"):
            ys, xs = np.nonzero(self.land > 0.5)
            pad = 4
            self._win = (max(0, xs.min() - pad), max(0, ys.min() - pad), min(self.fr.pw, xs.max() + pad),
                         min(self.fr.ph, ys.max() + pad))
        return self._win

    def reach_maps(self, z):
        """Travel-cost distance (km of easy going) from the places held at each keyframe.
        Roads are fast, open country slower, steep slopes slowest, the sea impassable."""
        key = z["name"]
        if key in self._reach:
            return self._reach[key]
        from skimage.graph import MCP_Geometric
        x0, y0, x1, y1 = self.island_window()
        sl = (slice(y0, y1), slice(x0, x1))
        cost = 1.0 + 7.0 * np.minimum(self.slope[sl], 1.0)
        cost = np.where(self.road[sl] > 0.25, np.minimum(cost, 0.45), cost)
        cost = np.where(self.land[sl] > 0.5, cost, 1e6)
        maps, cache = [], {}
        for _, pts, _ in z["kf"]:
            k = tuple(map(tuple, np.round(pts, 1)))
            if k not in cache:
                starts = [(min(max(int(p[1]) - y0, 0), y1 - y0 - 1), min(max(int(p[0]) - x0, 0), x1 - x0 - 1))
                          for p in pts]
                d, _ = MCP_Geometric(cost).find_costs(starts)
                cache[k] = (d * self.px_km).astype(np.float32)
            maps.append(cache[k])
        self._reach[key] = ((x0, y0, x1, y1), maps)
        return self._reach[key]

    def reach_mask(self, z, day):
        (x0, y0, x1, y1), maps = self.reach_maps(z)
        kf = z["kf"]
        if day <= kf[0][0]:
            i, u = 0, 0.0
        elif day >= kf[-1][0]:
            i, u = len(kf) - 1, 0.0
        else:
            i = max(j for j in range(len(kf)) if kf[j][0] <= day)
            u = smooth((day - kf[i][0]) / max(kf[i + 1][0] - kf[i][0], 1e-9)) if i + 1 < len(kf) else 0.0
        j = min(i + 1, len(kf) - 1)
        R = kf[i][2] + (kf[j][2] - kf[i][2]) * u
        if R < 1e-3:
            return None
        D = maps[i] if u == 0 else np.minimum(maps[i], maps[j] + (1 - u) * 40.0)  # new places "grow in"
        soft = 1.2 * self.px_km
        m = np.clip((R - D) / soft + 0.5, 0, 1).astype(np.float32)
        return m, (x0, y0, x1, y1)

    def zones_at(self, day):
        for z in self.zones:
            if not (z["a"] <= day < z["b"]):
                continue
            if z["kind"] == "reach":
                got = self.reach_mask(z, day)
                if got is None:
                    continue
                m, bb = got
                vm, _ = self.victim_mask(z["victims"])
                m = m * vm[bb[1]:bb[3], bb[0]:bb[2]]
                if m.max() > 0.01:
                    yield m, z["occ"], bb
                continue
            shape = self.zone_shape(z, day)
            if shape is None:
                continue
            vm, vbb = self.victim_mask(z["victims"])
            if vbb is None:
                continue
            x0 = max(vbb[0], int(np.floor(shape[:, 0].min())) - 1)
            y0 = max(vbb[1], int(np.floor(shape[:, 1].min())) - 1)
            x1 = min(vbb[2], int(np.ceil(shape[:, 0].max())) + 2)
            y1 = min(vbb[3], int(np.ceil(shape[:, 1].max())) + 2)
            if x1 <= x0 or y1 <= y0:
                continue
            m = self.poly_mask(shape, (x0, y0, x1, y1)) * vm[y0:y1, x0:x1]
            if m.max() > 0.01:
                yield m, z["occ"], (x0, y0, x1, y1)

    def owner_luts(self, day):
        n = 256
        col, alp, code = np.zeros((n, 3), np.float32), np.zeros(n, np.float32), np.zeros(n, np.uint8)
        for key, idx in PN.KEY_ID.items():
            hist = [(T.as_day(d), o) for d, o in T.OWNERS.get(key, [])]
            cur, since, prev = None, -1e9, None
            for d, o in hist:
                if day >= d:
                    prev, cur, since = cur, o, d
            fade = min(1.0, max(0.0, (day - since) / 2.0))
            ca = (np.array(T.FACTIONS[cur][0], np.float32) / 255, T.FACTIONS[cur][1]) if cur else (np.zeros(3), 0.0)
            cp = (np.array(T.FACTIONS[prev][0], np.float32) / 255, T.FACTIONS[prev][1]) if prev else (ca[0], 0.0)
            col[idx] = cp[0] * (1 - fade) + ca[0] * fade
            alp[idx] = cp[1] * (1 - fade) + ca[1] * fade
            code[idx] = CODES[cur] if fade > 0.5 else CODES[prev]
        return col, alp, code

    def codes(self, day, base_code):
        c = base_code[self.ids]
        for m, occ, (x0, y0, x1, y1) in self.zones_at(day):
            sub = c[y0:y1, x0:x1]
            sub[m > 0.5] = CODES[occ]
        return c

    def capture_light(self, day, lut_code):
        src = self.lo if self.lo is not None else self
        now = src.codes(day, lut_code)
        light = np.zeros(now.shape, np.float32)
        for d, w in ((1.5 / 24, 1.0), (3 / 24, 0.6), (5 / 24, 0.3)):  # hours, not days, at this time scale
            past = src.codes(day - d, lut_code)
            light = np.maximum(light, ((past != now) & (now > 0)) * np.float32(w))
        if not light.any():
            return None
        if src is not self:
            light = np.asarray(Image.fromarray(light).resize((self.fr.pw, self.fr.ph), Image.BILINEAR), np.float32)
        return light * self.land

    def render(self, day):
        col, alp, code = self.owner_luts(day)
        idx = self.ids.copy()
        for k, (c, a, _) in T.FACTIONS.items():
            i = 200 + CODES[k]
            col[i], alp[i], code[i] = np.array(c, np.float32) / 255, a, CODES[k]
        for m, occ, (x0, y0, x1, y1) in self.zones_at(day):
            sub = idx[y0:y1, x0:x1]
            sub[m > 0.5] = 200 + CODES[occ]
        a = alp[idx][..., None] * self.land[..., None]
        out = self.base + (col[idx] - self.base) * a
        lt = self.capture_light(day, code)
        if lt is not None:  # freshly taken ground: a light band just behind the moving front
            k = (0.7 * lt)[..., None]
            out = out * (1 - k) + np.float32(0.97) * k
        kr = (self.road * 0.28)[..., None]  # roads: thin warm grey
        out = out * (1 - kr) + np.array([0.35, 0.3, 0.26], np.float32) * kr
        kl = (self.rail * 0.7)[..., None]   # railway: dark line, like the WW1 maps
        out = out * (1 - kl) + np.float32(0.1) * kl
        b = self.border[..., None] * np.float32(0.5)
        out = out * (1 - b) + np.array([0.86, 0.45, 0.5], np.float32) * b
        fac = code[idx]
        e = np.zeros(fac.shape, bool)
        dx = (fac[:, 1:] != fac[:, :-1]) & (fac[:, 1:] > 0) & (fac[:, :-1] > 0)
        dy = (fac[1:, :] != fac[:-1, :]) & (fac[1:, :] > 0) & (fac[:-1, :] > 0)
        e[:, 1:] |= dx
        e[:, :-1] |= dx
        e[1:, :] |= dy
        e[:-1, :] |= dy
        if self.fr.pw > 1500:
            e = ndimage.binary_dilation(e)
        ys, xs = np.nonzero(e)
        k = np.float32(0.85) * self.land[ys, xs][:, None]
        out[ys, xs] = out[ys, xs] * (1 - k) + np.float32(0.97) * k
        np.clip(out, 0, 1, out=out)
        return (out * 255).astype(np.uint8)


class Renderer:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.s = W / PN.REF_W
        self.panels = [Panel(n, W, H) for n in PN.PANELS]
        self.pan = {p.name: p for p in self.panels}
        self._fonts = {}
        self.events = []
        last = None
        for d, txt in T.EVENTS:
            day = T.as_day(d)
            if last is not None and day <= last:
                day = last + 0.5
            self.events.append((day, txt))
            last = day
        self.labels = []
        for i, lab in enumerate(T.LABELS):
            p = self.pan[lab.get("panel", "puertorico")]
            side = "ESP" if "Spanish" in lab["name"] else "US"
            self.labels.append(dict(lab, seed=i * 7 + 3, side=side,
                                    hint=[(T.as_day(d), np.array(p.fr.px(q[0], q[1]))) for d, q in lab["hint"]],
                                    army=[(T.as_day(d), v) for d, v in lab["army"]]))
        self.markers = [(txt, *self.pan["puertorico"].fr.px(lo, la), T.as_day(a), T.as_day(b))
                        for txt, lo, la, a, b in T.MARKERS]
        self.towns = [(n, *self.pan["puertorico"].fr.px(lo, la)) for n, lo, la in T.TOWNS]
        self._vis = {}

    def font(self, name, size):
        k = (name, int(size))
        if k not in self._fonts:
            self._fonts[k] = ImageFont.truetype(os.path.join(FONTS, name), int(size))
        return self._fonts[k]

    # -- numbers -----------------------------------------------------------------------------
    def army_value(self, lab, day):
        ds = [d for d, _ in lab["army"]]
        if day < ds[0]:
            return 0
        v = float(np.interp(day, ds, [x for _, x in lab["army"]]))
        if v <= 0:
            return 0
        if v < 1000:  # small groups are counted exactly
            return int(round(v))
        sd = lab["seed"]
        j = 1 + 0.004 * math.sin(day * 12.0 + sd) + 0.0025 * math.sin(day * 40.0 + sd * 3)
        return int(v * j)

    def number_size(self, v):
        return min(15.0, 10.0 + 5.0 * math.sqrt(v / 17_000)) * self.s

    def draw_text_shadow(self, img, text, cx, cy, size, alpha=1.0, font="LiberationSans-Bold.ttf", angle=0.0):
        s = self.s
        f = self.font(font, size)
        bb = f.getbbox(text)
        pad = int(6 * s)
        w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
        sh = Image.new("L", (w, h), 0)
        ImageDraw.Draw(sh).text((pad - bb[0] + s, pad - bb[1] + s), text, font=f, fill=int(170 * alpha))
        sh = sh.filter(ImageFilter.GaussianBlur(1.1 * s))
        t = Image.merge("RGBA", (*Image.new("RGB", (w, h), (20, 20, 20)).split(), sh))
        ImageDraw.Draw(t).text((pad - bb[0], pad - bb[1]), text, font=f, fill=(255, 255, 255, int(255 * alpha)))
        if abs(angle) > 0.05:
            t = t.rotate(angle, resample=Image.BICUBIC, expand=True)
            w, h = t.size
        x, y = cx - w / 2, cy - h / 2
        ix, iy = math.floor(x), math.floor(y)
        t = t.transform(t.size, Image.AFFINE, (1, 0, -(x - ix), 0, 1, -(y - iy)), resample=Image.BILINEAR)
        img.alpha_composite(t, (max(0, ix), max(0, iy)))

    # -- numbers that follow the front -------------------------------------------------------------
    def front_codes(self, day):
        """Control codes (US / Spanish) at a working resolution, cached per time."""
        pan = self.pan["puertorico"]
        src = pan.lo if pan.lo is not None else pan
        key = round(day, 4)
        cache = self.__dict__.setdefault("_codes_cache", {})
        if key not in cache:
            if len(cache) > 40:
                cache.clear()
            cache[key] = src.codes(day, src.owner_luts(day)[2])
        return src, cache[key]

    def label_pose(self, lab, day, hint, v=0, size=10.0):
        """Anchor on the nearest stretch of front, offset into the label's own side, angle along the front
        (capped at 45 degrees), averaged over +-8 hours so it glides."""
        pan = self.pan["puertorico"]
        own = CODES[lab["side"]]
        other = CODES["ESP" if lab["side"] == "US" else "US"]
        pts, dirs = [], []
        for dd in (-12, -8, -4, 0, 4, 8, 12):
            src, c = self.front_codes(day + dd / 24)
            k = src.fr.pw / pan.fr.pw  # working px per output px
            hx, hy = (hint[0] - pan.fr.px0) * k, hint[1] * k
            b = np.zeros(c.shape, bool)
            dx = ((c[:, 1:] == own) & (c[:, :-1] == other)) | ((c[:, 1:] == other) & (c[:, :-1] == own))
            dy = ((c[1:, :] == own) & (c[:-1, :] == other)) | ((c[1:, :] == other) & (c[:-1, :] == own))
            b[:, 1:] |= dx
            b[1:, :] |= dy
            ys, xs = np.nonzero(b)
            if len(xs) == 0:
                pts.append(tuple(hint)); dirs.append((1.0, 0.0))  # no front nearby: stay level at the hint
                continue
            d2 = (xs - hx) ** 2 + (ys - hy) ** 2
            R = 130 * self.s * k
            fb = float(np.clip((R - math.sqrt(d2.min())) / (0.5 * R), 0, 1))
            fb = fb * fb * (3 - 2 * fb)  # how much the front "holds" the number (fades in as it approaches)
            near = d2 < R * R
            if near.sum() < 6 or fb <= 0:
                pts.append(tuple(hint)); dirs.append((1.0, 0.0))
                continue
            xs, ys, d2 = xs[near].astype(float), ys[near].astype(float), d2[near]
            sig = 22 * self.s * k
            w = np.exp(-(d2 - d2.min()) / (2 * sig * sig))
            ax, ay = (w * xs).sum() / w.sum(), (w * ys).sum() / w.sum()
            # direction of the front: main axis of the boundary pixels around the anchor
            w2 = np.exp(-((xs - ax) ** 2 + (ys - ay) ** 2) / (2 * (2.2 * sig) ** 2))
            cx, cy = xs - ax, ys - ay
            cov = np.array([[(w2 * cx * cx).sum(), (w2 * cx * cy).sum()], [(w2 * cx * cy).sum(), (w2 * cy * cy).sum()]])
            ev, evec = np.linalg.eigh(cov)
            t = evec[:, 1]
            if t[0] < 0:
                t = -t
            n = np.array([-t[1], t[0]])
            # point the normal into the label's own territory
            px_, py_ = int(round(ax + n[0] * 6 * k * self.s)), int(round(ay + n[1] * 6 * k * self.s))
            px_, py_ = min(max(px_, 0), c.shape[1] - 1), min(max(py_, 0), c.shape[0] - 1)
            if c[py_, px_] != own:
                n = -n
            th = math.atan2(t[1], t[0])
            front = -math.degrees(th)
            if front > 90:
                front -= 180
            elif front < -90:
                front += 180
            ang = 45.0 * math.tanh(front / 45.0)
            # find the spot nearest the front where the whole (tilted) number lies in its own territory,
            # clear of town names: try steps away from the line and sideways along it
            txt = f"{v:,}".replace(",", ".")
            hw = self.font("LiberationSans-Bold.ttf", size).getlength(txt) / 2 * k
            hh = 0.55 * size * k
            a = math.radians(-ang)
            u = np.array([math.cos(a), math.sin(a)])
            vv = np.array([-u[1], u[0]])
            gx, gy = np.meshgrid(np.linspace(-1, 1, 11), np.linspace(-1, 1, 5))
            box = (gx.ravel()[:, None] * hw * u + gy.ravel()[:, None] * hh * vv)
            offs = np.linspace(hh + 3 * k * self.s, hh + 60 * k * self.s, 10)
            lats = np.linspace(-70, 70, 15) * k * self.s
            OO, LL = np.meshgrid(offs, lats, indexing="ij")
            cands = (np.array([ax, ay])[None, None] + OO[..., None] * n + LL[..., None] * t).reshape(-1, 2)
            q = cands[:, None, :] + box[None]                      # (candidates, box points, 2)
            qx = np.clip(np.round(q[..., 0]).astype(int), 0, c.shape[1] - 1)
            qy = np.clip(np.round(q[..., 1]).astype(int), 0, c.shape[0] - 1)
            bad = (c[qy, qx] != own).sum(1) + self._town_hits(q / k, pan)
            costs = bad * 25 + OO.ravel() / k + np.abs(LL.ravel()) / k * 0.6
            wts = np.exp(-(costs - costs.min()) / (20.0 * self.s))  # soft choice: no jumps between spots
            best = (np.array(cands) * wts[:, None]).sum(0) / wts.sum()
            fx, fy = best[0] / k + pan.fr.px0, best[1] / k
            pts.append((hint[0] + (fx - hint[0]) * fb, hint[1] + (fy - hint[1]) * fb))
            ang *= fb
            dirs.append((math.cos(math.radians(2 * ang)), math.sin(math.radians(2 * ang))))
        if not pts:
            return np.array(hint, float), 0.0
        p = np.mean(pts, 0)
        c2, s2 = np.mean(dirs, 0)
        return p, math.degrees(0.5 * math.atan2(s2, c2))

    def label_pose_smooth(self, lab, day, step=2 / 24):
        """label_pose sampled on a fixed 2-hour grid and linearly interpolated: always continuous."""
        cache = self.__dict__.setdefault("_pose_cache", {})
        g0 = math.floor(day / step) * step
        out = []
        for g in (g0, g0 + step):
            key = (lab["seed"], round(g, 5))
            if key not in cache:
                if len(cache) > 400:
                    cache.clear()
                hx = T_interp([(d, q[0]) for d, q in lab["hint"]], g)
                hy = T_interp([(d, q[1]) for d, q in lab["hint"]], g)
                v = max(self.army_value(lab, day), 1)
                cache[key] = self.label_pose(lab, g, (hx, hy), v, self.number_size(v))
            out.append(cache[key])
        u = (day - g0) / step
        (p0, a0), (p1, a1) = out
        return np.asarray(p0) * (1 - u) + np.asarray(p1) * u, a0 * (1 - u) + a1 * u

    def _town_hits(self, q, pan):
        """How many of the points q (panel-local output px) fall on a town dot or name."""
        s = self.s
        boxes = self.__dict__.get("_town_boxes")
        if boxes is None:
            f = self.font("LiberationSans-Regular.ttf", 10 * s)
            boxes = np.array([(x - pan.fr.px0 - 4 * s, y - 4 * s, x - pan.fr.px0 + 6 * s + f.getlength(nm), y + 15 * s)
                              for nm, x, y in self.towns])
            self._town_boxes = boxes
        qq = q[..., None, :]  # (..., 1, 2) against (towns, 4)
        inside = ((qq[..., 0] >= boxes[:, 0]) & (qq[..., 0] <= boxes[:, 2]) &
                  (qq[..., 1] >= boxes[:, 1]) & (qq[..., 1] <= boxes[:, 3]))
        return inside.any(-1).sum(-1)

    def draw_labels(self, img, day):
        cands = []
        for lab in self.labels:
            v = self.army_value(lab, day)
            alpha = min(1.0, (day - lab["army"][0][0] + 0.05) / 0.15)
            if v <= 0 or alpha <= 0:
                continue
            hx = T_interp([(d, q[0]) for d, q in lab["hint"]], day)
            hy = T_interp([(d, q[1]) for d, q in lab["hint"]], day)
            size = self.number_size(v)
            if lab.get("fixed"):
                p, ang = (hx, hy), 0.0
            else:
                p, ang = self.label_pose_smooth(lab, day)
            cands.append((v, p, ang, alpha, lab["seed"], size))
        placed = []
        for v, p, ang, alpha, key, size in sorted(cands, key=lambda c: -c[0]):
            txt = f"{v:,}".replace(",", ".")
            w = self.font("LiberationSans-Bold.ttf", size).getlength(txt) / 2 + 3 * self.s
            h = size * 0.6 + 2 * self.s
            a = math.radians(-ang)
            ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
            box = Polygon([(p[0] + sx * w * ux + sy * h * vx, p[1] + sx * w * uy + sy * h * vy)
                           for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
            free = not any(box.intersects(b) for b in placed)
            if free:
                placed.append(box)
            cur = self._vis.get(key, 1.0 if free else 0.0)
            cur = min(1.0, cur + 0.15) if free else max(0.0, cur - 0.15)
            self._vis[key] = cur
            if cur > 0.01:
                self.draw_text_shadow(img, txt, p[0], p[1], size, alpha * cur, angle=ang)

    def draw_markers(self, img, day, vt):
        s = self.s
        d = ImageDraw.Draw(img)
        for txt, x, y, a, b in self.markers:
            if not (a <= day < b):
                continue
            r = 7 * s
            rot = (vt * 90) % 360
            for k in range(8):
                st = rot + k * 45
                d.arc([x - r, y - r, x + r, y + r], st, st + 25, fill=(255, 255, 255, 235), width=max(2, int(2 * s)))
            f = self.font("LiberationSans-Bold.ttf", 10 * s)
            d.text((x + r + 6 * s, y - 7 * s), txt, font=f, fill=(255, 255, 255, 255),
                   stroke_width=max(1, int(1.4 * s)), stroke_fill=(40, 40, 40, 150))

    def draw_hud(self, img, day):
        s, W, H = self.s, self.W, self.H
        d = ImageDraw.Draw(img)
        dt = T.date_at(min(day, END_DAY))
        hour = dt.hour
        f_date = self.font("LiberationSans-Bold.ttf", 22 * s)
        f_time = self.font("LiberationSans-Bold.ttf", 12 * s)
        x, y = 14 * s, 8 * s
        dd = str(dt.day)
        d.text((x + 28 * s - d.textlength(dd, font=f_date), y), dd, font=f_date, fill=(15, 15, 15))
        d.text((x + 40 * s, y), MONTHS[dt.month - 1], font=f_date, fill=(15, 15, 15))
        d.text((x + 40 * s + d.textlength(MONTHS[dt.month - 1], font=f_date) + 8 * s, y), str(dt.year),
               font=f_date, fill=(15, 15, 15))
        d.text((x + 1 * s, y + 31 * s), f"{hour:02d}:00", font=f_time, fill=(15, 15, 15))
        cap = None
        for eday, txt in self.events:
            if eday <= day:
                cap = txt
        if cap:
            d.text((14 * s, H - 36 * s), cap, font=self.font("LiberationSans-Bold.ttf", 20 * s), fill=(15, 15, 15))
        # place names
        f = self.font("LiberationSans-Regular.ttf", 10 * s)
        for n, x, y in self.towns:
            d.ellipse([x - 1.6 * s, y - 1.6 * s, x + 1.6 * s, y + 1.6 * s], fill=(40, 40, 40))
            d.text((x + 4 * s, y + 1 * s), n, font=f, fill=(35, 35, 35))
        self.draw_inset(img, day)
        # legend: factions visible right now
        shown = [k for k in T.FACTIONS if self._faction_visible(k, day)]
        f = self.font("LiberationSans-Bold.ttf", 11 * s)
        car = self.pan["puertorico"].fr  # open sea south-east of the island
        lx = car.px0 + car.pw - 14 * s - max(d.textlength(T.FACTIONS[k][2], font=f) for k in shown) - 20 * s
        ly = H - 16 * s - 18 * s * len(shown)
        for i, k in enumerate(shown):
            yy = ly + i * 18 * s
            d.rectangle([lx, yy + 2 * s, lx + 14 * s, yy + 14 * s], fill=T.FACTIONS[k][0] + (230,),
                        outline=(40, 40, 40, 120))
            d.text((lx + 20 * s, yy), T.FACTIONS[k][2], font=f, fill=(25, 25, 25))

    def draw_inset(self, img, day):
        ins = getattr(T, "INSET", None)
        if ins is None:
            return
        a0, a1 = T.as_day(ins["start"]), T.as_day(ins["end"])
        if not (a0 <= day < a1):
            return
        a = min(1.0, (day - a0) / 0.03, (a1 - day) / 0.03)
        s = self.s
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        fb = self.font("LiberationSans-Bold.ttf", 14 * s)
        fr = self.font("LiberationSans-Regular.ttf", 12 * s)
        w = 300 * s
        x0, y0 = self.W - w - 16 * s, 16 * s
        h = (40 + 18 * len(ins["lines"]) + 24 * len(ins["numbers"])) * s
        d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=6 * s, fill=(245, 243, 236, int(235 * a)),
                            outline=(60, 60, 60, int(200 * a)), width=max(1, int(s)))
        d.text((x0 + 12 * s, y0 + 10 * s), ins["title"], font=fb, fill=(20, 20, 20, int(255 * a)))
        for i, ln in enumerate(ins["lines"]):
            d.text((x0 + 12 * s, y0 + (34 + 18 * i) * s), ln, font=fr, fill=(40, 40, 40, int(255 * a)))
        yy = y0 + (38 + 18 * len(ins["lines"])) * s
        for name, v in ins["numbers"]:
            c = T.FACTIONS["NAT"][0]
            d.rectangle([x0 + 12 * s, yy + 3 * s, x0 + 24 * s, yy + 15 * s], fill=c + (int(230 * a),))
            d.text((x0 + 32 * s, yy), f"{name}: {v}", font=fb, fill=(20, 20, 20, int(255 * a)))
            yy += 24 * s
        img.alpha_composite(ov)

    def _faction_visible(self, k, day):
        for key, hist in T.OWNERS.items():
            cur = None
            for d, o in hist:
                if day >= T.as_day(d):
                    cur = o
            if cur == k:
                return True
        return any(z.get("occ", "US") == k and T.as_day(z["start"]) <= day < T.as_day(z["end"]) for z in T.ZONES)

    def draw_intro(self, img, vt):
        s, W, H = self.s, self.W, self.H
        a = (1.0 if vt < INTRO - 1.2 else max(0.0, (INTRO - vt) / 1.2)) * min(1.0, vt / 1.0)
        ov = Image.new("RGBA", img.size, (10, 12, 16, int(170 * a)))
        d = ImageDraw.Draw(ov)
        for txt, f, y, c in [("THE PUERTO RICAN CAMPAIGN", self.font("LiberationSans-Bold.ttf", 58 * s), 0.32, 255),
                             ("Spanish-American War, 1898 - Hour by Hour with Army Sizes",
                              self.font("LiberationSans-Bold.ttf", 24 * s), 0.46, 230),
                             ("12 May  -  18 October 1898", self.font("LiberationSans-Regular.ttf", 17 * s),
                              0.54, 200)]:
            w = d.textlength(txt, font=f)
            d.text(((W - w) / 2, H * y), txt, font=f, fill=(c, c, c, int(255 * a)))
        img.alpha_composite(ov)

    def draw_outro(self, img, vt, sched):
        s, W, H = self.s, self.W, self.H
        t = vt - sched.main_end
        if t <= 1.0:
            return
        a = min(1.0, (t - 1.0) / 1.5)
        ov = Image.new("RGBA", img.size, (10, 12, 16, int(185 * a)))
        d = ImageDraw.Draw(ov)
        big = self.font("LiberationSans-Bold.ttf", 40 * s)
        mid = self.font("LiberationSans-Bold.ttf", 19 * s)
        small = self.font("LiberationSans-Regular.ttf", 13 * s)
        A = int(255 * a)
        if t < 11.0:
            txt = "The Puerto Rican Campaign, 1898"
            d.text(((W - d.textlength(txt, font=big)) / 2, H * 0.16), txt, font=big, fill=(255, 255, 255, A))
            for i, (k, v) in enumerate(T.TOTALS):
                a2 = int(255 * min(1.0, max(0.0, (t - 2.0 - i * 1.0) / 0.8)) * a)
                y = H * 0.3 + i * 40 * s
                d.text((W * 0.5 - 20 * s - d.textlength(k, font=mid), y), k, font=mid, fill=(200, 200, 200, a2))
                d.text((W * 0.5 + 20 * s, y), v, font=mid, fill=(255, 255, 255, a2))
        else:
            a3 = int(255 * min(1.0, (t - 11.0) / 1.0) * min(1.0, max(0.0, (OUTRO - t) / 1.5)))
            notes = ["Notes",
                     "Army sizes are rounded estimates; small detachments and times of day are approximate.",
                     "US-held ground spreads along the 1898 roads (hand-traced) from the towns held on each date.",
                     "Quotations are performed by an AI voice with a phonograph filter; no recordings survive.",
                     "Music: marches by John Philip Sousa (public domain scores from the Mutopia Project),",
                     "played by a synthesized band (GeneralUser GS soundfont). Map: Natural Earth, AWS Terrain Tiles."]
            for i, n in enumerate(notes):
                f = mid if i == 0 else small
                d.text(((W - d.textlength(n, font=f)) / 2, H * 0.3 + i * 30 * s), n, font=f,
                       fill=(235, 235, 235, a3))
        img.alpha_composite(ov)

    def frame(self, vt, sched):
        day = sched.day(vt)
        out = np.zeros((self.H, self.W, 3), np.uint8)
        out[:] = (38, 42, 50)  # divider colour between the panels
        for p in self.panels:
            out[:, p.fr.px0:p.fr.px0 + p.fr.pw] = p.render(day)
        img = Image.fromarray(out).convert("RGBA")
        self.draw_labels(img, day)
        self.draw_markers(img, day, vt)
        self.draw_hud(img, day)
        if vt < INTRO:
            self.draw_intro(img, vt)
        if vt > sched.main_end:
            self.draw_outro(img, vt, sched)
        return img.convert("RGB")


def T_interp(series, t):
    if t <= series[0][0]:
        return series[0][1]
    for (t0, v0), (t1, v1) in zip(series, series[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * smooth((t - t0) / max(t1 - t0, 1e-9))
    return series[-1][1]


# ----------------------------------------------------------------------------- drivers
def render_chunk(args):
    W, H, f0, f1, path = args
    sched = load_schedule()
    r = Renderer(W, H)
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-tune", "animation",
           "-pix_fmt", "yuv420p", "-g", "250", "-threads", "2", "-x264-params", "rc-lookahead=15", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(f0, f1):
        p.stdin.write(r.frame(i / FPS, sched).tobytes())
        if (i - f0) % 250 == 0:
            print(f"[{os.path.basename(path)}] frame {i - f0}/{f1 - f0}", flush=True)
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError(f"encoder failed for {path}")
    open(path + ".done", "w").write("ok")
    return path


def march_audio(name):
    """Band rendering of one Sousa march (cached)."""
    import band
    p = os.path.join(BUILD, "music", name + ".npy")
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        y = band.render(os.path.join(HERE, "midi", name + ".midi")).mean(1).astype(np.float32)
        np.save(p, y)
    return np.load(p)


def battle_sounds(sched, n):
    """Distant rifle volleys and artillery during the battles (quiet, under the music)."""
    from scipy import signal as sg
    rng = np.random.default_rng(7)
    out = np.zeros(n, np.float32)
    sr = audio.SR
    for a, b in T.BATTLES:
        t0, t1 = sched.vt_of(T.as_day(a)), sched.vt_of(T.as_day(b))
        if t1 - t0 < 0.5:
            continue
        for _ in range(int((t1 - t0) * 6)):  # rifle shots
            t = rng.uniform(t0, t1)
            k = int(0.08 * sr)
            s = int(t * sr)
            if s + k >= n:
                continue
            burst = rng.normal(0, 1, k) * np.exp(-np.arange(k) / (0.012 * sr))
            out[s:s + k] += burst.astype(np.float32) * rng.uniform(0.15, 0.4)
        for _ in range(int((t1 - t0) * 0.8)):  # artillery
            t = rng.uniform(t0, t1)
            k = int(1.6 * sr)
            s = int(t * sr)
            if s + k >= n:
                continue
            tt = np.arange(k) / sr
            boom = (np.sin(2 * np.pi * 45 * tt) + rng.normal(0, 0.6, k)) * np.exp(-tt * 3.5)
            out[s:s + k] += boom.astype(np.float32) * 0.6
    out = sg.sosfilt(sg.butter(2, 2500, fs=sr, output="sos"), out).astype(np.float32)  # far away
    return audio.reverb(out, seconds=2.5, mix=0.5)


def build_audio(sched, out_wav):
    import wave
    sr = audio.SR
    n = int(sched.total * sr)
    music = np.zeros(n, np.float32)
    cues = [(sched.vt_of(T.as_day(d)) if T.as_day(d) > 0 else 0.0, name) for name, d in T.MUSIC]
    cues.append((sched.total, None))
    for (t0, name), (t1, _) in zip(cues, cues[1:]):
        y = march_audio(name)
        s0, s1 = int(t0 * sr), min(n, int((t1 + 3.0) * sr))
        seg = np.resize(y, s1 - s0)  # loop a march if the section is longer than it
        fade = np.ones(len(seg), np.float32)
        nf = min(int(3.0 * sr), len(seg) // 3)
        fade[:nf] = np.linspace(0, 1, nf)
        fade[-nf:] = np.linspace(1, 0, nf)
        music[s0:s1] += seg * fade
    music = audio.reverb(music, seconds=1.8, mix=0.2)
    music /= np.abs(music).max() + 1e-9
    music += battle_sounds(sched, n) * 0.5
    events = [(s["t0"], np.load(s["path"])) for s in sched.speeches]
    pcm = audio.mix(sched.total, music, events, bell_time=None)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main():
    sys.path.insert(0, WW1)
    import render as R  # reuse the resumable chunk bookkeeping from the WW1 renderer
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preview", "video", "audio", "info"])
    ap.add_argument("date", nargs="?")
    ap.add_argument("--w", type=int, default=1920)
    ap.add_argument("--h", type=int, default=1080)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--vt", type=float, default=None)
    ap.add_argument("--out", default=os.path.join(BUILD, "pr1898.mp4"))
    args = ap.parse_args()
    sched = load_schedule()
    if args.mode == "info":
        print(f"total {sched.total:.1f}s, rate {sched.rate:.2f} days/s")
        for s in sched.speeches:
            print(s["date"], f"{s['t0']:.1f}s", s["speaker"])
        return
    if args.mode == "preview":
        r = Renderer(args.w, args.h)
        vt = args.vt if args.vt is not None else sched.vt_of(T.as_day(args.date))
        img = r.frame(vt, sched)
        out = os.path.join(BUILD, f"preview_{(args.date or str(vt)).replace(' ', '_').replace(':', '')}.png")
        img.save(out)
        print(out)
        return
    wav = os.path.join(BUILD, "audio.wav")
    build_audio(sched, wav)
    if args.mode == "audio":
        print(wav)
        return
    for name in PN.PANELS:  # build static layers once before the workers start
        PN.build(name, args.w, args.h)
        if args.w > 1920:
            PN.build(name, args.w // 2, args.h // 2)
    nframes = int(sched.total * FPS)
    chunk_dir = os.path.join(BUILD, f"chunks_{args.w}x{args.h}")
    os.makedirs(chunk_dir, exist_ok=True)
    from concurrent.futures import ProcessPoolExecutor
    from concurrent.futures.process import BrokenProcessPool
    for attempt in range(4):
        done, gaps = R.missing_ranges(chunk_dir, nframes)
        if not gaps:
            break
        todo = [(args.w, args.h, a, b, os.path.join(chunk_dir, f"chunk_{a:06d}_{b:06d}.mp4"))
                for a, b in R.split_ranges(gaps, args.jobs)]
        print(f"rendering {sum(t[3] - t[2] for t in todo)} frames in {len(todo)} pieces", flush=True)
        try:
            with ProcessPoolExecutor(args.jobs) as ex:
                list(ex.map(render_chunk, todo))
        except (BrokenProcessPool, RuntimeError) as e:
            print("worker failed, retrying:", e, flush=True)
    done, gaps = R.missing_ranges(chunk_dir, nframes)
    if gaps:
        raise SystemExit(f"could not render frames {gaps}")
    lst = os.path.join(chunk_dir, "list.txt")
    with open(lst, "w") as f:
        for a, b in done:
            f.write(f"file '{os.path.join(chunk_dir, f'chunk_{a:06d}_{b:06d}.mp4')}'\n")
    subprocess.check_call([ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                           "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
                           "-movflags", "+faststart", args.out])
    print("wrote", args.out)


if __name__ == "__main__":
    main()
