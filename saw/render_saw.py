"""Renders the Spanish-American War / Philippine-American War map animation (split screen).

Usage:
    python3 render_saw.py info
    python3 render_saw.py preview 1898-07-10 [--w 1920 --h 1080]
    python3 render_saw.py video --w 3840 --h 2160 --jobs 4 --out build/saw_4k.mp4
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

import panels as PN
import timeline_saw as T

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
WW1 = os.path.join(os.path.dirname(HERE), "ww1")
FONTS = os.path.join(WW1, "assets", "fonts")
sys.path.insert(0, WW1)
import audio  # noqa: E402  (shared speech/music code from the WW1 project)

audio.BUILD = BUILD
FPS = 30
TARGET_SECONDS = 600.0
INTRO, OUTRO = 8.0, 22.0
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
END_DAY = T.day_index(T.END) + 0.5
CODES = {None: 0, "US": 1, "ESP": 2, "CLA": 3, "FIL": 4, "MORO": 5, "CUBA": 6}


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
    d = T.START.toordinal() + int(day)
    if d < T.D("1898-08-15").toordinal():
        return 0.22   # the Spanish-American War itself: slow
    if d < T.D("1899-02-04").toordinal():
        return 1.0
    if d < T.D("1900-01-01").toordinal():
        return 0.75   # conventional phase of the Philippine-American War
    return 1.15       # guerrilla war


class Schedule:
    """Video time <-> calendar day. Speeches play in the background when their date is reached."""

    def __init__(self, meta):
        days = np.arange(int(math.ceil(END_DAY)))
        inv = sum(1.0 / pace_multiplier(d) for d in days)
        self.rate = inv / (TARGET_SECONDS - INTRO - OUTRO)
        knots = [(0.0, 0.0), (INTRO, 0.0)]
        t, day = INTRO, 0.0
        while day < END_DAY - 1e-9:
            step = min(1.0 - (day % 1.0), END_DAY - day)
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
            day = min(max(T.as_day(s["date"]) + 0.3, 0.0), END_DAY)
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
        self.key_of = {v: k for k, v in PN.KEY_ID.items()}
        self._victim = {}
        self._mask = {}
        self._mask_bytes = 0
        self.zones = []
        for z in T.ZONES:
            if z["panel"] != name:
                continue
            zz = dict(z, a=T.as_day(z["start"]), b=T.as_day(z["end"]))
            if z["kind"] == "poly":
                zz["kf"] = [(T.as_day(d), self.P(resample_ring(r))) for d, r in z["keys"]]
            else:
                zz["kf"] = [(T.as_day(d), np.array(e, float)) for d, *e in z["keys"]]
            self.zones.append(zz)
        # at 4K, work out recently-captured ground on a half-size twin (much faster, looks the same)
        self.lo = Panel(name, W // 2, H // 2, lite=True) if (not lite and W > 1920) else None

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
        if z["kind"] == "poly":
            return v
        cx, cy, rx, ry = v
        if rx < 1e-3 and ry < 1e-3:
            return None
        t = np.linspace(0, 2 * np.pi, 64, endpoint=False)
        return self.P(np.stack([cx + rx * np.cos(t), cy + ry * np.sin(t)], 1))

    def zones_at(self, day):
        for z in self.zones:
            if not (z["a"] <= day < z["b"]):
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
        for d, w in ((0.4, 1.0), (0.9, 0.6), (1.6, 0.3)):
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
            p = self.pan[lab["panel"]]
            self.labels.append(dict(lab, seed=i * 7 + 3,
                                    hint=[(T.as_day(d), np.array(p.fr.px(q[0], q[1]))) for d, q in lab["hint"]],
                                    army=[(T.as_day(d), v) for d, v in lab["army"]]))
        self.markers = [(txt, *self.pan[pn].fr.px(lo, la), T.as_day(a), T.as_day(b) + 1)
                        for txt, pn, lo, la, a, b in T.MARKERS]
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
        sd = lab["seed"]
        j = 1 + 0.004 * math.sin(day * 0.61 + sd) + 0.0025 * math.sin(day * 2.3 + sd * 3)
        return int(v * j)

    def number_size(self, v):
        return min(22.0, 14.0 + 8.0 * math.sqrt(v / 100_000)) * self.s

    def draw_text_shadow(self, img, text, cx, cy, size, alpha=1.0, font="LiberationSans-Bold.ttf"):
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
        x, y = cx - w / 2, cy - h / 2
        ix, iy = math.floor(x), math.floor(y)
        t = t.transform(t.size, Image.AFFINE, (1, 0, -(x - ix), 0, 1, -(y - iy)), resample=Image.BILINEAR)
        img.alpha_composite(t, (max(0, ix), max(0, iy)))

    def draw_labels(self, img, day):
        cands = []
        for lab in self.labels:
            v = self.army_value(lab, day)
            alpha = min(1.0, (day - lab["army"][0][0] + 0.3) / 1.5)
            if v <= 0 or alpha <= 0:
                continue
            hx = T_interp([(d, q[0]) for d, q in lab["hint"]], day)
            hy = T_interp([(d, q[1]) for d, q in lab["hint"]], day)
            cands.append((v, (hx, hy), alpha, lab["seed"]))
        placed = []
        for v, p, alpha, key in sorted(cands, key=lambda c: -c[0]):
            txt = f"{v:,}".replace(",", ".")
            size = self.number_size(v)
            w = self.font("LiberationSans-Bold.ttf", size).getlength(txt) / 2 + 3 * self.s
            h = size * 0.6 + 2 * self.s
            box = Polygon([(p[0] - w, p[1] - h), (p[0] + w, p[1] - h), (p[0] + w, p[1] + h), (p[0] - w, p[1] + h)])
            free = not any(box.intersects(b) for b in placed)
            if free:
                placed.append(box)
            cur = self._vis.get(key, 1.0 if free else 0.0)
            cur = min(1.0, cur + 0.15) if free else max(0.0, cur - 0.15)
            self._vis[key] = cur
            if cur > 0.01:
                self.draw_text_shadow(img, txt, p[0], p[1], size, alpha * cur)

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
        dt = T.date_at(min(day, END_DAY - 0.51))
        hour = int((day % 1.0) * 24)
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
        # panel titles
        f = self.font("LiberationSans-Bold.ttf", 13 * s)
        for p in self.panels:
            t = p.fr.title
            tw = d.textlength(t, font=f)
            d.text((p.fr.px0 + p.fr.pw - tw - 12 * s, 10 * s), t, font=f, fill=(40, 45, 55))
        # legend: factions visible right now
        shown = [k for k in T.FACTIONS if self._faction_visible(k, day)]
        f = self.font("LiberationSans-Bold.ttf", 11 * s)
        car = self.pan["caribbean"].fr  # open sea south of Hispaniola, clear of any land
        lx = car.px0 + car.pw - 14 * s - max(d.textlength(T.FACTIONS[k][2], font=f) for k in shown) - 20 * s
        ly = H - 16 * s - 18 * s * len(shown)
        for i, k in enumerate(shown):
            yy = ly + i * 18 * s
            d.rectangle([lx, yy + 2 * s, lx + 14 * s, yy + 14 * s], fill=T.FACTIONS[k][0] + (230,),
                        outline=(40, 40, 40, 120))
            d.text((lx + 20 * s, yy), T.FACTIONS[k][2], font=f, fill=(25, 25, 25))

    def _faction_visible(self, k, day):
        for key, hist in T.OWNERS.items():
            cur = None
            for d, o in hist:
                if day >= T.as_day(d):
                    cur = o
            if cur == k:
                return True
        return any(z["occ"] == k and T.as_day(z["start"]) <= day < T.as_day(z["end"]) for z in T.ZONES)

    def draw_intro(self, img, vt):
        s, W, H = self.s, self.W, self.H
        a = (1.0 if vt < INTRO - 1.2 else max(0.0, (INTRO - vt) / 1.2)) * min(1.0, vt / 1.0)
        ov = Image.new("RGBA", img.size, (10, 12, 16, int(170 * a)))
        d = ImageDraw.Draw(ov)
        for txt, f, y, c in [("THE SPANISH-AMERICAN WAR", self.font("LiberationSans-Bold.ttf", 58 * s), 0.32, 255),
                             ("and the Philippine-American War - Every Day with Army Sizes",
                              self.font("LiberationSans-Bold.ttf", 24 * s), 0.46, 230),
                             ("21 April 1898  -  4 July 1902", self.font("LiberationSans-Regular.ttf", 17 * s),
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
        if t < 13.0:
            txt = "1898 - 1902"
            d.text(((W - d.textlength(txt, font=big)) / 2, H * 0.16), txt, font=big, fill=(255, 255, 255, A))
            for i, (k, v) in enumerate(T.TOTALS):
                a2 = int(255 * min(1.0, max(0.0, (t - 2.0 - i * 1.0) / 0.8)) * a)
                y = H * 0.3 + i * 40 * s
                d.text((W * 0.5 - 20 * s - d.textlength(k, font=mid), y), k, font=mid, fill=(200, 200, 200, a2))
                d.text((W * 0.5 + 20 * s, y), v, font=mid, fill=(255, 255, 255, a2))
        else:
            a3 = int(255 * min(1.0, (t - 13.0) / 1.0) * min(1.0, max(0.0, (OUTRO - t) / 1.5)))
            notes = ["Notes",
                     "Army sizes are rounded estimates of the forces in each theatre, based on standard histories.",
                     "Areas of control are simplified; the guerrilla war had no fixed front lines.",
                     "Speeches are historical quotations performed by an AI voice (translated where needed).",
                     "Music composed procedurally for this video.",
                     "Map data: Natural Earth."]
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


def build_audio(sched, out_wav):
    import wave
    cues = [(0.0, "intro"), (INTRO, "march"), (sched.vt_of(T.as_day("1898-08-13")), "hope"),
            (sched.vt_of(T.as_day("1899-02-04")), "tension"), (sched.vt_of(T.as_day("1899-11-13")), "dark"),
            (sched.vt_of(T.as_day("1901-03-23")), "lament")]
    music = audio.make_music(sched.total, cues, seed=23)
    events = [(s["t0"], np.load(s["path"])) for s in sched.speeches]
    pcm = audio.mix(sched.total, music, events, bell_time=None)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(audio.SR)
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
    ap.add_argument("--out", default=os.path.join(BUILD, "saw.mp4"))
    args = ap.parse_args()
    sched = load_schedule()
    if args.mode == "info":
        print(f"total {sched.total:.1f}s, rate {sched.rate:.2f} days/s")
        for s in sched.speeches:
            print(s["date"], f"{s['t0']:.1f}s", s["speaker"])
        return
    if args.mode == "preview":
        r = Renderer(args.w, args.h)
        vt = args.vt if args.vt is not None else sched.vt_of(T.as_day(args.date) + 0.5)
        img = r.frame(vt, sched)
        out = os.path.join(BUILD, f"preview_{args.date or vt}.png")
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
