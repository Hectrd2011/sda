"""Renders the WW1 map animation frame by frame and muxes it with the audio.

Usage:
    python3 render.py preview 1916-07-01 [W H]    # single PNG for a date
    python3 render.py video [--w 1920 --h 1080 --jobs 4]
"""
import argparse
import json
import math
import os
import subprocess
import sys
from datetime import timedelta

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage
from shapely.geometry import Point, Polygon

import audio
import basemap as bm
import timeline as T

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
FONTS = os.path.join(HERE, "assets", "fonts")
FPS = 30
TARGET_SECONDS = 600.0
INTRO = 8.0
OUTRO = 22.0
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
END_DAY = T.day_index(T.END) + 11 / 24  # 11:00 on 11 November 1918


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


# ----------------------------------------------------------------------------- pacing
def pace_multiplier(day):
    """Relative speed of the calendar (1 = normal). Lower = slower."""
    d = T.START + timedelta(days=int(day))
    y, m, dd = d.year, d.month, d.day
    if (y, m) == (1914, 7) or ((y, m) == (1914, 8) and dd <= 6):
        return 0.28
    if (y, m) in [(1914, 8), (1914, 9)]:
        return 0.6
    if (y, m) == (1918, 11):
        return 0.35
    if (y, m) in [(1918, 3), (1918, 4), (1918, 9), (1918, 10)]:
        return 0.8
    return 1.0


class Schedule:
    """Maps video time <-> calendar day. Speeches play in the background while the calendar
    keeps running; each starts when its date is reached (or after the previous one ends)."""

    def __init__(self, speech_meta):
        self.speeches = []
        for s in T.SPEECHES:
            m = speech_meta[s["date"]]
            day = min(T.day_index(T.D(s["date"])) + 0.3, END_DAY)
            self.speeches.append(dict(s, day=day, duration=m["duration"], path=m["path"]))
        days = np.arange(int(math.ceil(END_DAY)))
        inv = sum(1.0 / pace_multiplier(d) for d in days)
        self.rate = inv / (TARGET_SECONDS - INTRO - OUTRO)  # days per second at multiplier 1
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
        free = 0.0
        for s in self.speeches:
            s["t0"] = max(float(np.interp(s["day"], self.kd[1:], self.kt[1:])), free)
            free = s["t0"] + s["duration"] + 0.6

    def day(self, vt):
        return float(np.interp(vt, self.kt, self.kd))


# ----------------------------------------------------------------------------- renderer
class Renderer:
    def __init__(self, W, H, lite=False):
        self.W, self.H = W, H
        self.s = W / 1280.0
        self.fr = bm.Frame(W, H)
        base = bm.build(W, H)
        self.base = base["base"]
        self.ids = base["ids"]
        self.land = base["land"]
        self.border = base["border"]
        self.key_of = {v: k for k, v in bm.KEY_ID.items()}
        self.fac_code = {None: 0, "CP": 1, "ENT": 2, "SOV": 4, "OUT": 5}
        self._victim_cache = {}
        self._mask_cache = {}
        self._prepare_fronts()
        self._fonts = {}
        self.alliance = {k: [(T.as_day(d), f) for d, f in v] for k, v in T.ALLIANCES.items()}
        self.events = [(T.as_day(d), txt) for d, txt in T.EVENTS]
        self.markers = [(txt, *self.fr.px(lo, la), T.as_day(a), T.as_day(b) + 1) for txt, lo, la, a, b in T.MARKERS]
        # half-resolution twin used to work out how recently each pixel changed hands
        self.lo = None if lite else Renderer(W // 2, H // 2, lite=True)

    # -- helpers -------------------------------------------------------------------------------
    def font(self, name, size):
        k = (name, int(size))
        if k not in self._fonts:
            self._fonts[k] = ImageFont.truetype(os.path.join(FONTS, name), int(size))
        return self._fonts[k]

    def P(self, lonlat, ss=1):
        a = np.asarray(lonlat, float)
        x, y = self.fr.px(a[:, 0], a[:, 1], ss)
        return np.stack([x, y], 1)

    def victim_mask(self, victims, day):
        keys = tuple(v if isinstance(v, str) else v[0] for v in victims
                     if isinstance(v, str) or day >= T.as_day(v[1]))
        if keys not in self._victim_cache:
            ids = [bm.KEY_ID[k] for k in keys]
            m = np.isin(self.ids, ids).astype(np.float32) * self.land
            ys, xs = np.nonzero(m > 0)
            bbox = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1) if len(xs) else None
            self._victim_cache[keys] = (m, bbox)
        return self._victim_cache[keys]

    def _prepare_fronts(self):
        N = 500
        self.fronts = []
        for f in T.FRONTS:
            keys = []
            for d, items in f["keys"]:
                line = T.resolve_line(items)
                keys.append((T.as_day(d), self.P(T.resample(line, N))))
            sides = {}
            for s in ("A", "B"):
                sd = f[s]
                sides[s] = dict(occ=sd["occ"], victims=sd["victims"], rear=self.P(sd["rear"]),
                                until=T.as_day(sd["until"]) if sd.get("until") else None)
            labels = []
            for lab in f["labels"]:
                hint = [(T.as_day(d), self.P([p])[0]) for d, p in lab["hint"]]
                army = [(T.as_day(d), v) for d, v in lab["army"]]
                labels.append(dict(side=lab["side"], hint=hint, army=army, seed=len(labels) * 7 + len(self.fronts)))
            from scipy.interpolate import PchipInterpolator
            days = np.array([k[0] for k in keys], float)
            interp = PchipInterpolator(days, np.stack([k[1] for k in keys]), axis=0)
            for lab in labels:
                ts = []
                for kd, kl in keys:
                    hint = np.array([T.interp_series([(k, p[0]) for k, p in lab["hint"]], kd),
                                     T.interp_series([(k, p[1]) for k, p in lab["hint"]], kd)])
                    i = int(np.argmin(((kl - hint) ** 2).sum(1)))
                    i = min(max(i, 60), len(kl) - 61)
                    t = kl[i + 60] - kl[i - 60]
                    t = t / (np.linalg.norm(t) + 1e-9)
                    ts.append(t if not ts or np.dot(t, ts[0]) >= 0 else -t)
                ref = np.mean(ts, 0)
                if ref[0] < 0:  # read left-to-right (or top-to-bottom for vertical fronts)
                    ref = -ref
                lab["refdir"] = ref / (np.linalg.norm(ref) + 1e-9)
            winding = {}
            for s in ("A", "B"):  # orientation of each side's polygon, fixed from the first keyframe
                poly = np.concatenate([keys[0][1], sides[s]["rear"]])
                winding[s] = np.sign(np.sum(poly[:, 0] * np.roll(poly[:, 1], -1) - np.roll(poly[:, 0], -1) * poly[:, 1]))
            self.fronts.append(dict(name=f["name"], keys=keys, sides=sides, labels=labels, interp=interp,
                                    winding=winding))
        self.static = []
        for z in T.STATIC_ZONES:
            self.static.append(dict(z, poly_px=self.P(z["poly"]), a=T.as_day(z["start"]), b=T.as_day(z["end"])))

    def front_line(self, fr, day):
        """Front line at a (fractional) day: monotone cubic interpolation between keyframes,
        so fronts accelerate and decelerate smoothly instead of stopping at every keyframe."""
        keys = fr["keys"]
        if day <= keys[0][0]:
            return keys[0][1], day >= keys[0][0] - 0.5
        if day >= keys[-1][0]:
            return keys[-1][1], True
        return fr["interp"](day), True

    def poly_mask(self, poly, bbox):
        """Anti-aliased polygon coverage restricted to bbox (x0,y0,x1,y1) at 1x."""
        key = (np.round(poly, 1).tobytes(), bbox)
        if key in self._mask_cache:
            return self._mask_cache[key]
        x0, y0, x1, y1 = bbox
        ss = 2
        im = Image.new("L", ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        pts = [((x - x0) * ss, (y - y0) * ss) for x, y in poly]
        ImageDraw.Draw(im).polygon(pts, fill=255)
        m = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255.0
        m = ndimage.grey_opening(m, size=(3, 3))
        if len(self._mask_cache) > 400:
            self._mask_cache.clear()
        self._mask_cache[key] = m
        return m

    def faction(self, key, day):
        f, since = None, -1e9
        for d, fac in self.alliance.get(key, []):
            if day >= d:
                f, since = fac, d
        return f, since

    # -- map layer ----------------------------------------------------------------------------
    def alliance_luts(self, day):
        lut_c = np.zeros((256, 3), np.float32)
        lut_a = np.zeros(256, np.float32)
        lut_f = np.zeros(256, np.uint8)
        for key, idx in bm.KEY_ID.items():
            fac, since = self.faction(key, day)
            prev = None
            for d, f2 in self.alliance.get(key, []):
                if d < since:
                    prev = f2
            fade = min(1.0, max(0.0, (day - since) / 3.0))
            ca = (np.array(T.FACTIONS[fac][0], np.float32) / 255, T.FACTIONS[fac][1]) if fac else (np.zeros(3), 0.0)
            cp = (np.array(T.FACTIONS[prev][0], np.float32) / 255, T.FACTIONS[prev][1]) if prev else (np.zeros(3), 0.0)
            if prev is None:
                cp = (ca[0], 0.0)
            if fac is None:
                ca = (cp[0], 0.0)
            lut_c[idx] = cp[0] * (1 - fade) + ca[0] * fade
            lut_a[idx] = cp[1] * (1 - fade) + ca[1] * fade
            lut_f[idx] = self.fac_code[fac] if fade > 0.5 else self.fac_code[prev]
        return lut_c, lut_a, lut_f

    def zones(self, day, set_line=False):
        """Yield (mask, occupier, bbox) for every occupied area at a (fractional) day."""
        for fr in self.fronts:
            line, active = self.front_line(fr, day)
            if not active:
                continue
            if set_line:
                fr["_line"] = line
            for s in ("A", "B"):
                sd = fr["sides"][s]
                if not sd["victims"]:
                    continue
                vm, bbox = self.victim_mask(sd["victims"], day)
                if bbox is None:
                    continue
                poly = np.concatenate([line, sd["rear"]])
                m = self.poly_mask(poly, bbox) * vm[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                if sd["until"] is not None:
                    m = m * min(1.0, max(0.0, (sd["until"] + 3.0 - day) / 3.0))
                if m.max() > 0.01:
                    yield m, sd["occ"], bbox
        for z in self.static:
            if z["a"] <= day < z["b"]:
                vm, bbox = self.victim_mask(z["victims"], day)
                yield self.poly_mask(z["poly_px"], bbox) * vm[bbox[1]:bbox[3], bbox[0]:bbox[2]], z["occ"], bbox

    def zone_codes(self, day, base):
        fac = base.copy()
        for m, occ, (x0, y0, x1, y1) in self.zones(day):
            sl = (slice(y0, y1), slice(x0, x1))
            fac[sl] = np.where(m > 0.5, self.fac_code[occ], fac[sl])
        return fac

    # Newly taken ground is shown in a light tint that darkens into the occupier's colour.
    RECENCY = [(0.6, 1.0), (1.4, 0.7), (2.8, 0.42), (5.0, 0.2)]

    def capture_light(self, day, lut_f):
        lo = self.lo
        base = lut_f[lo.ids]
        now = lo.zone_codes(day, base)
        light = np.zeros(now.shape, np.float32)
        for d, w in self.RECENCY:
            past = lo.zone_codes(day - d, base)
            changed = (past != now) & (now > 0)
            light = np.maximum(light, changed * np.float32(w))
        if not light.any():
            return None
        light = ndimage.gaussian_filter(light, 0.6)
        return np.asarray(Image.fromarray(light).resize((self.W, self.H), Image.BILINEAR), np.float32) * self.land

    def map_layer(self, day):
        W, H = self.W, self.H
        lut_c, lut_a, lut_f = self.alliance_luts(day)
        col = lut_c[self.ids]
        a = lut_a[self.ids] * self.land
        fac = lut_f[self.ids]

        for m, occ, (x0, y0, x1, y1) in self.zones(day, set_line=True):
            c = np.array(T.FACTIONS[occ][0], np.float32) / 255
            al = T.FACTIONS[occ][1]
            sl = (slice(y0, y1), slice(x0, x1))
            col[sl] = col[sl] * (1 - m[..., None]) + c * m[..., None]
            a[sl] = a[sl] * (1 - m) + al * m
            fac[sl] = np.where(m > 0.5, self.fac_code[occ], fac[sl])

        out = self.base * (1 - a[..., None]) + col * a[..., None]
        if self.lo is not None:
            lt = self.capture_light(day, lut_f)
            if lt is not None:  # freshly captured land: whitish, fading into the occupier's colour
                k = (0.8 * lt)[..., None]
                out = out * (1 - k) + np.float32(0.96) * k
        # borders (pink, like old atlas maps)
        b = self.border[..., None] * 0.55
        out = out * (1 - b) + np.array([0.86, 0.45, 0.5], np.float32) * b
        # light outline where two warring factions meet
        e = np.zeros((H, W), bool)
        dx = (fac[:, 1:] != fac[:, :-1]) & (fac[:, 1:] > 0) & (fac[:, :-1] > 0)
        dy = (fac[1:, :] != fac[:-1, :]) & (fac[1:, :] > 0) & (fac[:-1, :] > 0)
        e[:, 1:] |= dx
        e[1:, :] |= dy
        ef = ndimage.uniform_filter(e.astype(np.float32), 2) * self.land
        out = out * (1 - 0.45 * ef[..., None]) + 0.97 * 0.45 * ef[..., None]
        return (np.clip(out, 0, 1) * 255).astype(np.uint8)

    # -- overlays -------------------------------------------------------------------------------
    def army_value(self, lab, day):
        """Army size at a fractional day. Continuous, so the counter rolls every frame."""
        v = float(np.interp(day, [d for d, _ in lab["army"]], [x for _, x in lab["army"]]))
        if v <= 0:
            return 0
        seed = lab["seed"]
        jitter = 1 + 0.004 * math.sin(day * 0.61 + seed) + 0.0025 * math.sin(day * 2.3 + seed * 3) + \
            0.0015 * math.sin(day * 7.1 + seed * 5)
        return int(v * jitter)

    def draw_rotated_text(self, img, text, cx, cy, angle, size, alpha=1.0):
        """White number with a soft drop shadow, rotated to follow the front."""
        s = self.s
        f = self.font("OpenSans-Bold.ttf", size)
        bb = f.getbbox(text)
        pad = int(6 * s)
        w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
        sh = Image.new("L", (w, h), 0)
        ImageDraw.Draw(sh).text((pad - bb[0] + s, pad - bb[1] + s), text, font=f, fill=int(200 * alpha))
        sh = sh.filter(ImageFilter.GaussianBlur(1.6 * s))
        t = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        t.putalpha(sh)
        t = Image.alpha_composite(Image.new("RGBA", (w, h), (0, 0, 0, 0)),
                                  Image.merge("RGBA", (*Image.new("RGB", (w, h), (20, 20, 20)).split(), sh)))
        ImageDraw.Draw(t).text((pad - bb[0], pad - bb[1]), text, font=f, fill=(255, 255, 255, int(255 * alpha)))
        r0 = t.rotate(angle, resample=Image.BICUBIC, expand=True)
        x, y = cx - r0.width / 2, cy - r0.height / 2
        ix, iy = math.floor(x), math.floor(y)
        # shift by the fractional part so labels glide smoothly instead of stepping pixel by pixel
        r = r0.transform(r0.size, Image.AFFINE, (1, 0, -(x - ix), 0, 1, -(y - iy)), resample=Image.BILINEAR)
        cx0, cy0 = max(0, -ix), max(0, -iy)  # alpha_composite needs a non-negative destination
        if cx0 < r.width and cy0 < r.height:
            img.alpha_composite(r.crop((cx0, cy0, r.width, r.height)), (ix + cx0, iy + cy0))

    def draw_army_labels(self, img, day):
        s = self.s
        for fr in self.fronts:
            line = fr.get("_line")
            if line is None:
                continue
            active, _ = self.front_line(fr, day)
            for lab in fr["labels"]:
                v = self.army_value(lab, day)
                if v <= 0:
                    continue
                first = lab["army"][0][0]
                alpha = min(1.0, (day - first + 0.5) / 3.0)
                if alpha <= 0:
                    continue
                p1, ang = self.label_pose(fr, lab, day)
                txt = f"{v:,}".replace(",", ".")
                self.draw_rotated_text(img, txt, p1[0], p1[1], ang, 16 * s, alpha)

    def label_pose(self, fr, lab, day):
        """Position/angle of an army label. Smoothed over +-6 days and aimed along a long chord of
        the front, with a fixed reading direction per label so the text never flips."""
        offs = np.linspace(-6.0, 6.0, 13)
        wts = np.exp(-0.5 * (offs / 3.0) ** 2)
        sign = fr["winding"][lab["side"]]
        pos, dirs = [], []
        for dd in offs:
            d = day + dd
            line, _ = self.front_line(fr, d)
            hint = np.array([T.interp_series([(k, p[0]) for k, p in lab["hint"]], d),
                             T.interp_series([(k, p[1]) for k, p in lab["hint"]], d)])
            # soft anchor: blend every line point by closeness to the hint, so the anchor slides
            # continuously instead of hopping between segments of a jagged line
            d2 = ((line - hint) ** 2).sum(1)
            sig = 28.0 * self.s
            w = np.exp(-(d2 - d2.min()) / (2 * sig * sig))
            idx = np.arange(len(line))
            tan = line[np.minimum(idx + 60, len(line) - 1)] - line[np.maximum(idx - 60, 0)]
            tan /= (np.linalg.norm(tan, axis=1, keepdims=True) + 1e-9)
            nrm = np.stack([-tan[:, 1], tan[:, 0]], 1) * sign  # side's territory is left of travel
            pos.append((w[:, None] * (line + nrm * 12 * self.s)).sum(0) / w.sum())
            tan = np.where((tan @ lab["refdir"])[:, None] >= 0, tan, -tan)
            dirs.append((w[:, None] * tan).sum(0) / w.sum())
        p1 = np.average(pos, axis=0, weights=wts)
        t = np.average(dirs, axis=0, weights=wts)
        return p1, -math.degrees(math.atan2(t[1], t[0]))

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
            f = self.font("OpenSans-Bold.ttf", 13 * s)
            tw = d.textlength(txt, font=f)
            d.text((x + r + 6 * s, y - 9 * s), txt, font=f, fill=(255, 255, 255, 255),
                   stroke_width=max(1, int(1.4 * s)), stroke_fill=(40, 40, 40, 150))

    def draw_hud(self, img, day, vt, sched):
        s, W, H = self.s, self.W, self.H
        d = ImageDraw.Draw(img)
        dt = T.date_at(day)
        hour = int((day % 1.0) * 24)
        if day >= END_DAY - 1e-6:
            dt, hour = T.END, 11
        f_date = self.font("OpenSans-Bold.ttf", 22 * s)
        f_time = self.font("OpenSans-Bold.ttf", 11 * s)
        x, y = 14 * s, 8 * s
        dd = f"{dt.day:02d}"
        d.text((x, y), dd, font=f_date, fill=(20, 20, 20))
        d.text((x + 36 * s, y), MONTHS[dt.month - 1], font=f_date, fill=(20, 20, 20))
        d.text((x + 36 * s + d.textlength(MONTHS[dt.month - 1], font=f_date) + 14 * s, y), str(dt.year),
               font=f_date, fill=(20, 20, 20))
        d.text((x + 1 * s, y + 31 * s), f"{hour:02d}:00", font=f_time, fill=(20, 20, 20))
        # caption (latest event)
        cap, cday = None, None
        for eday, txt in self.events:
            if eday <= day:
                cap, cday = txt, eday
        if cap:
            f = self.font("OpenSans-Bold.ttf", 19 * s)
            d.text((14 * s, H - 36 * s), cap, font=f, fill=(15, 15, 15))
        # legend
        f = self.font("OpenSans-SemiBold.ttf", 11 * s)
        items = [(fac, name) for fac, name, since in T.LEGEND if since is None or day >= T.as_day(since)]
        lx, ly = W - 205 * s, H - 16 * s - 18 * s * len(items)
        for i, (fac, name) in enumerate(items):
            c = T.FACTIONS[fac][0]
            yy = ly + i * 18 * s
            d.rectangle([lx, yy + 2 * s, lx + 14 * s, yy + 14 * s], fill=c + (230,), outline=(40, 40, 40, 120))
            d.text((lx + 20 * s, yy), name, font=f, fill=(25, 25, 25))

    def draw_intro(self, img, vt):
        s, W, H = self.s, self.W, self.H
        a = 1.0 if vt < INTRO - 1.2 else max(0.0, (INTRO - vt) / 1.2)
        a *= min(1.0, vt / 1.0)
        ov = Image.new("RGBA", img.size, (10, 12, 16, int(170 * a)))
        d = ImageDraw.Draw(ov)
        f1 = self.font("OpenSans-Bold.ttf", 64 * s)
        f2 = self.font("OpenSans-SemiBold.ttf", 26 * s)
        f3 = self.font("OpenSans-Regular.ttf", 17 * s)
        for txt, f, y, c in [("WORLD WAR I", f1, H * 0.34, (255, 255, 255)),
                             ("Every Front, Every Day - with Army Sizes", f2, H * 0.47, (230, 230, 230)),
                             ("28 July 1914  -  11 November 1918", f3, H * 0.55, (200, 200, 200))]:
            w = d.textlength(txt, font=f)
            d.text(((W - w) / 2, y), txt, font=f, fill=c + (int(255 * a),))
        img.alpha_composite(ov)

    def draw_outro(self, img, vt, sched):
        s, W, H = self.s, self.W, self.H
        t = vt - sched.main_end
        if t <= 1.0:
            return
        a = min(1.0, (t - 1.0) / 1.5)
        ov = Image.new("RGBA", img.size, (10, 12, 16, int(185 * a)))
        d = ImageDraw.Draw(ov)
        big = self.font("OpenSans-Bold.ttf", 44 * s)
        mid = self.font("OpenSans-SemiBold.ttf", 20 * s)
        small = self.font("OpenSans-Regular.ttf", 13 * s)
        A = int(255 * a)
        if t < 13.0:
            txt = "THE GREAT WAR  1914 - 1918"
            w = d.textlength(txt, font=big)
            d.text(((W - w) / 2, H * 0.2), txt, font=big, fill=(255, 255, 255, A))
            for i, (k, v) in enumerate(T.TOTALS):
                a2 = int(255 * min(1.0, max(0.0, (t - 2.0 - i * 1.2) / 0.8)) * a)
                y = H * 0.36 + i * 44 * s
                d.text((W * 0.5 - 20 * s - d.textlength(k, font=mid), y), k, font=mid, fill=(200, 200, 200, a2))
                d.text((W * 0.5 + 20 * s, y), v, font=mid, fill=(255, 255, 255, a2))
        else:
            a3 = int(255 * min(1.0, (t - 13.0) / 1.0) * min(1.0, max(0.0, (OUTRO - t) / 1.5)))
            notes = [
                "Notes",
                "Army sizes are rounded estimates of the forces deployed on each front, based on standard histories.",
                "Front lines are simplified; small actions and colonial fronts outside the map are not shown.",
                "Speeches are historical quotations performed by an AI voice (English translations where needed).",
                "Music composed procedurally for this video.",
                "Map data: historical-basemaps (1914 borders, corrected), Natural Earth.",
            ]
            for i, n in enumerate(notes):
                f = mid if i == 0 else small
                w = d.textlength(n, font=f)
                d.text(((W - w) / 2, H * 0.3 + i * 30 * s), n, font=f, fill=(235, 235, 235, a3))
        img.alpha_composite(ov)

    def frame(self, vt, sched):
        day = sched.day(vt)
        m = self.map_layer(day)
        img = Image.fromarray(m).convert("RGBA")
        self.draw_army_labels(img, day)
        self.draw_markers(img, day, vt)
        self.draw_hud(img, day, vt, sched)
        if vt < INTRO:
            self.draw_intro(img, vt)
        if vt > sched.main_end:
            self.draw_outro(img, vt, sched)
        return img.convert("RGB")


# ----------------------------------------------------------------------------- drivers
def load_schedule():
    meta = audio.make_speeches(T.SPEECHES)
    return Schedule(meta)


def render_chunk(args):
    W, H, f0, f1, path = args
    sched = load_schedule()
    r = Renderer(W, H)
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-tune", "animation",
           "-pix_fmt", "yuv420p", "-g", "250", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(f0, f1):
        img = r.frame(i / FPS, sched)
        p.stdin.write(img.tobytes())
        if (i - f0) % 250 == 0:
            print(f"[{os.path.basename(path)}] frame {i - f0}/{f1 - f0}", flush=True)
    p.stdin.close()
    p.wait()
    return path


def build_audio(sched, out_wav):
    import wave
    # music cues follow the course of the war
    def vt_of_day(day):
        return float(np.interp(day, sched.kd[1:], sched.kt[1:]))
    cues = [(0.0, "intro"), (INTRO, "march"), (vt_of_day(T.as_day("1914-10-25")), "dark"),
            (vt_of_day(T.as_day("1915-10-01")), "lament"), (vt_of_day(T.as_day("1916-06-01")), "tension"),
            (vt_of_day(T.as_day("1916-12-20")), "dark"), (vt_of_day(T.as_day("1917-11-01")), "lament"),
            (vt_of_day(T.as_day("1918-03-15")), "tension"), (vt_of_day(T.as_day("1918-08-08")), "hope")]
    music = audio.make_music(sched.total, cues)
    events = [(s["t0"], np.load(s["path"])) for s in sched.speeches]
    bell_t = vt_of_day(END_DAY - 0.05)
    pcm = audio.mix(sched.total, music, events, bell_time=bell_t)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(audio.SR)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preview", "video", "audio", "info"])
    ap.add_argument("date", nargs="?")
    ap.add_argument("--w", type=int, default=1920)
    ap.add_argument("--h", type=int, default=1080)
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(HERE), "WW1_Every_Day_with_Army_Sizes.mp4"))
    ap.add_argument("--seconds", type=float, default=None, help="render only the first N seconds")
    ap.add_argument("--vt", type=float, default=None, help="preview at a video time")
    args = ap.parse_args()
    sched = load_schedule()
    if args.mode == "info":
        print(f"total {sched.total:.1f}s, main_end {sched.main_end:.1f}s, rate {sched.rate:.2f} days/s")
        for s in sched.speeches:
            print(s["date"], f"{s['t0']:.1f}s", s["speaker"])
        return
    if args.mode == "preview":
        r = Renderer(args.w, args.h)
        if args.vt is not None:
            vt = args.vt
        else:
            day = T.as_day(args.date) + 0.5
            vt = float(np.interp(day, sched.kd[1:], sched.kt[1:]))
        import time
        t = time.time()
        img = r.frame(vt, sched)
        print("frame time", round(time.time() - t, 3))
        out = os.path.join(BUILD, f"preview_{args.date or vt}.png")
        img.save(out)
        print(out)
        return
    os.makedirs(os.path.join(BUILD, "chunks"), exist_ok=True)
    wav = os.path.join(BUILD, "audio.wav")
    build_audio(sched, wav)
    if args.mode == "audio":
        print(wav)
        return
    total = sched.total if args.seconds is None else min(sched.total, args.seconds)
    nframes = int(total * FPS)
    jobs = max(1, args.jobs)
    bounds = np.linspace(0, nframes, jobs + 1).astype(int)
    chunks = [(args.w, args.h, int(bounds[i]), int(bounds[i + 1]),
               os.path.join(BUILD, "chunks", f"chunk_{i:02d}.mp4")) for i in range(jobs)]
    from multiprocessing import Pool
    with Pool(jobs) as pool:
        paths = pool.map(render_chunk, chunks)
    lst = os.path.join(BUILD, "chunks", "list.txt")
    with open(lst, "w") as f:
        for p in paths:
            f.write(f"file '{p}'\n")
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
           "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", args.out]
    subprocess.check_call(cmd)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
