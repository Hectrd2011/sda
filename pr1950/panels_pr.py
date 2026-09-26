"""Static map layers for the 1950 Puerto Rican Nationalist uprisings video.

One full-frame panel of Puerto Rico in Mercator projection, with hill-shading computed from
Terrarium elevation tiles (AWS Terrain Tiles, zoom 11); the static layers (terrain, water, coastline, country ids) are built
once per panel and output size and cached in build/cache/.
"""
import os

import numpy as np
import pyproj
import shapefile
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import Polygon, box

HERE = os.path.dirname(os.path.abspath(__file__))
DL = os.path.join(HERE, "build", "downloads")
CACHE = os.path.join(HERE, "build", "cache")

# Panel layout in 1280x720 reference units: (x0, width) and the lon/lat window it shows.
# The window's height is derived from the panel's aspect ratio so the map is never stretched.
PANELS = {
    "puertorico": dict(title="", x0=0, w=1280, lon=(-67.42, -65.12), lat_center=18.2),
}
REF_W, REF_H = 1280, 720

# countries used by the timeline (Natural Earth ADM0_A3 -> key); everything else is neutral land
KEYS = {"PRI": "PRI"}
KEY_ID = {k: i + 1 for i, k in enumerate(sorted(set(KEYS.values())))}
MERC = pyproj.Proj("+proj=merc +ellps=WGS84")


class PanelFrame:
    """Maps lon/lat to pixels of the full output frame for one panel."""

    def __init__(self, name, W, H):
        p = PANELS[name]
        self.name, self.title = name, p["title"]
        s = W / REF_W
        self.px0 = int(round(p["x0"] * s))
        self.pw = int(round(p["w"] * s))
        self.ph = H
        x0, _ = MERC(p["lon"][0], 0)
        x1, _ = MERC(p["lon"][1], 0)
        _, yc = MERC(0, p["lat_center"])
        span_y = (x1 - x0) * self.ph / self.pw
        self.X0, self.X1 = x0, x1
        self.Y1 = yc + span_y / 2
        self.Y0 = yc - span_y / 2
        self.sx = self.pw / (x1 - x0)
        self.sy = self.ph / (self.Y1 - self.Y0)
        lo0, la0 = MERC(x0, self.Y0, inverse=True)
        lo1, la1 = MERC(x1, self.Y1, inverse=True)
        self.bbox = (lo0 - 1, la0 - 1, lo1 + 1, la1 + 1)

    def px(self, lon, lat, ss=1, local=False):
        x, y = MERC(np.asarray(lon, float), np.asarray(lat, float))
        X = (x - self.X0) * self.sx
        Y = (self.Y1 - y) * self.sy
        if not local:
            X = X + self.px0
        return X * ss, Y * ss

    def pts(self, lonlat, ss=1, local=True):
        a = np.asarray(lonlat, float)
        x, y = self.px(a[:, 0], a[:, 1], ss, local)
        return list(zip(x.tolist(), y.tolist()))

    def lonlat_grid(self):
        xs = self.X0 + (np.arange(self.pw) + 0.5) / self.sx
        ys = self.Y1 - (np.arange(self.ph) + 0.5) / self.sy
        gx, gy = np.meshgrid(xs, ys)
        return MERC(gx, gy, inverse=True)


def _rings(path, bbox, records=False):
    clip = box(*bbox)
    sf = shapefile.Reader(path)
    for sr in sf.iterShapeRecords():
        s = sr.shape
        if not s.points:
            continue
        b = s.bbox
        if b[2] < bbox[0] or b[0] > bbox[2] or b[3] < bbox[1] or b[1] > bbox[3]:
            continue
        parts = list(s.parts) + [len(s.points)]
        for i in range(len(parts) - 1):
            r = np.asarray(s.points[parts[i]:parts[i + 1]], float)
            if len(r) < 3:
                continue
            if r[:, 0].max() < bbox[0] or r[:, 0].min() > bbox[2] or r[:, 1].max() < bbox[1] \
                    or r[:, 1].min() > bbox[3]:
                continue
            g = Polygon(r).buffer(0).intersection(clip)
            for gg in (g.geoms if hasattr(g, "geoms") else [g]):
                if gg.geom_type == "Polygon" and not gg.is_empty:
                    yield (sr.record, gg) if records else gg


def dem_sample(lon, lat, z=11):
    """Elevation (m) at lon/lat from the downloaded Terrarium tiles (bilinear)."""
    n = 2 ** z
    gx = (lon + 180) / 360 * n * 256
    gy = (1 - np.arcsinh(np.tan(np.radians(lat))) / np.pi) / 2 * n * 256
    tx0, ty0 = int(gx.min() // 256), int(gy.min() // 256)
    tx1, ty1 = int(gx.max() // 256), int(gy.max() // 256)
    mosaic = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), np.float32)
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            f = os.path.join(DL, "dem", f"{z}_{tx}_{ty}.png")
            if not os.path.exists(f):
                continue
            a = np.asarray(Image.open(f).convert("RGB"), np.float32)
            mosaic[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = \
                a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    return ndimage.map_coordinates(mosaic, [gy - ty0 * 256, gx - tx0 * 256], order=1)


def hillshade(elev, fr, az=315.0, alt=45.0):
    m_per_px = (fr.X1 - fr.X0) / fr.pw * np.cos(np.radians(18.2))
    e = np.maximum(elev, 0) * 1.6  # mild vertical exaggeration
    gy, gx = np.gradient(ndimage.gaussian_filter(e, 0.7), m_per_px)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    a, z = np.radians(az), np.radians(90 - alt)
    hs = np.cos(z) * np.cos(slope) + np.sin(z) * np.sin(slope) * np.cos(a - aspect)
    return 0.62 + 0.42 * hs


def build(name, W, H):
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, f"panel_{name}_{W}x{H}.npz")
    if os.path.exists(out):
        return dict(np.load(out))
    fr = PanelFrame(name, W, H)
    pw, ph, SS = fr.pw, fr.ph, 3
    bb = fr.bbox

    def poly(draw, g, fill, ss=SS):
        draw.polygon(fr.pts(g.exterior.coords, ss), fill=fill)
        for h in g.interiors:
            draw.polygon(fr.pts(h.coords, ss), fill=0)

    land = Image.new("L", (pw * SS, ph * SS), 0)
    ld = ImageDraw.Draw(land)
    coast = []
    for f in ("ne_10m_land", "ne_10m_minor_islands"):
        for g in _rings(os.path.join(DL, f, f + ".shp"), bb):
            poly(ld, g, 255)
            coast.append(np.asarray(g.exterior.coords))
    for g in _rings(os.path.join(DL, "ne_10m_lakes", "ne_10m_lakes.shp"), bb):
        poly(ld, g, 0)
        coast.append(np.asarray(g.exterior.coords))
    land_a = np.asarray(land.resize((pw, ph), Image.BOX), np.float32) / 255.0
    # the elevation data has a far more detailed coastline than Natural Earth at this zoom
    lon, lat = fr.lonlat_grid()
    elev = dem_sample(lon, lat)
    dem_land = elev > 0.5
    dem_land = ndimage.binary_closing(ndimage.binary_opening(dem_land, iterations=1), iterations=2)
    ne_core = ndimage.binary_erosion(land_a > 0.5, iterations=max(2, pw // 480))
    land_bin = ndimage.binary_fill_holes(dem_land | ne_core)
    land_a = ndimage.gaussian_filter(land_bin.astype(np.float32), 0.7)
    coast = []  # coastline drawn from the land mask below instead

    idimg = Image.new("L", (pw * SS, ph * SS), 0)
    dr = ImageDraw.Draw(idimg)
    for rec, g in _rings(os.path.join(DL, "ne_10m_admin_0_countries", "ne_10m_admin_0_countries.shp"), bb,
                         records=True):
        key = KEYS.get(rec["ADM0_A3"])
        poly(dr, g, KEY_ID[key] if key else 250)
    ids_ss = np.asarray(idimg)
    ids = ids_ss[SS // 2::SS, SS // 2::SS].copy()
    missing = ids == 0
    _, (iy, ix) = ndimage.distance_transform_edt(missing, return_indices=True)
    ids = ids[iy, ix]
    ids[land_a < 0.5] = 0
    ids[ids == 250] = 0  # neutral countries: plain land

    # terrain: hill-shading from Terrarium elevation tiles
    rel = np.clip(hillshade(elev, fr) * 1.0, 0.45, 1.06)
    rng = np.random.default_rng(3)
    grain = ndimage.gaussian_filter(rng.normal(0, 1, (ph, pw)).astype(np.float32), 1.2) * 0.02
    landc = np.array([234, 232, 224], np.float32)[None, None] / 255 * (rel[..., None] + grain[..., None])
    yy, xx = np.mgrid[0:ph, 0:pw]
    hatch = ((xx + yy) % 6 < 1).astype(np.float32) * 0.025
    waterc = np.array([203, 218, 232], np.float32)[None, None] / 255 - hatch[..., None]
    base = waterc * (1 - land_a[..., None]) + landc * land_a[..., None]

    def line_layer(lines, width, closed=True):
        im = Image.new("L", (pw * SS, ph * SS), 0)
        d = ImageDraw.Draw(im)
        for r in lines:
            r = np.asarray(r, float)
            if closed:
                r = np.concatenate([r, r[:1]])
            d.line(fr.pts(r, SS), fill=255, width=width, joint="curve")
        return np.asarray(im.resize((pw, ph), Image.BOX), np.float32) / 255.0

    coast_a = np.clip(np.abs(land_a - ndimage.uniform_filter(land_a, 3)) * 4.0, 0, 1)
    rivers = []
    sf = shapefile.Reader(os.path.join(DL, "ne_10m_rivers_lake_centerlines", "ne_10m_rivers_lake_centerlines.shp"))
    for s in sf.shapes():
        b = s.bbox
        if b[2] < bb[0] or b[0] > bb[2] or b[3] < bb[1] or b[1] > bb[3]:
            continue
        parts = list(s.parts) + [len(s.points)]
        for i in range(len(parts) - 1):
            r = np.asarray(s.points[parts[i]:parts[i + 1]], float)
            if len(r) > 1:
                rivers.append(r)
    river_a = line_layer(rivers, max(1, SS // 2), closed=False) * land_a
    # 1950 roads (hand-traced main roads plus Natural Earth highways) and the railway
    import network_pr as NW
    roads = [np.asarray(r, float) for r in NW.ROADS]
    for s in shapefile.Reader(os.path.join(DL, "ne_10m_roads", "ne_10m_roads.shp")).shapes():
        b = s.bbox
        if b[2] < bb[0] or b[0] > bb[2] or b[3] < bb[1] or b[1] > bb[3]:
            continue
        parts = list(s.parts) + [len(s.points)]
        roads += [np.asarray(s.points[parts[i]:parts[i + 1]], float) for i in range(len(parts) - 1)]
    # Keep every route on land: densify it, then move any point that falls in the sea or right on the
    # shoreline to the nearest point at least ~500 m inland, so routes hug the coast instead of cutting
    # across bays (the hand-traced routes are straight between towns).
    km_px = (fr.X1 - fr.X0) / pw * np.cos(np.radians(18.2)) / 1000.0
    inland = ndimage.binary_erosion(land_a > 0.5, iterations=max(1, int(round(0.5 / km_px))))
    _, (iy, ix) = ndimage.distance_transform_edt(~inland, return_indices=True)

    def on_land(line):
        a = np.asarray(line, float)
        seg = np.sqrt(((a[1:] - a[:-1]) ** 2).sum(1))
        n = max(2, int(seg.sum() / 0.004))
        s = np.concatenate([[0], np.cumsum(seg)])
        t = np.linspace(0, s[-1], n)
        lo, la = np.interp(t, s, a[:, 0]), np.interp(t, s, a[:, 1])
        x, y = fr.px(lo, la, local=True)
        xi = np.clip(np.round(x).astype(int), 0, pw - 1)
        yi = np.clip(np.round(y).astype(int), 0, ph - 1)
        bad = ~inland[yi, xi]
        x = np.where(bad, ix[yi, xi], x).astype(float)
        y = np.where(bad, iy[yi, xi], y).astype(float)
        k = np.ones(5) / 5  # smooth out the kinks left by snapping
        if len(x) > 5:
            x = np.concatenate([x[:2], np.convolve(x, k, "valid"), x[-2:]])
            y = np.concatenate([y[:2], np.convolve(y, k, "valid"), y[-2:]])
        return list(zip((x * SS).tolist(), (y * SS).tolist()))

    def route_layer(lines, width):
        im = Image.new("L", (pw * SS, ph * SS), 0)
        d = ImageDraw.Draw(im)
        for r in lines:
            if len(r) > 1:
                d.line(on_land(r), fill=255, width=width, joint="curve")
        return np.asarray(im.resize((pw, ph), Image.BOX), np.float32) / 255.0

    road_a = route_layer(roads, max(2, SS)) * land_a
    rail_a = route_layer([np.asarray(r, float) for r in NW.RAILWAYS], max(2, SS)) * land_a
    # slope (rise over run) for movement costs
    m_per_px = (fr.X1 - fr.X0) / fr.pw * np.cos(np.radians(18.2))
    gy, gx = np.gradient(ndimage.gaussian_filter(np.maximum(elev, 0), 1.0), m_per_px)
    slope = np.hypot(gx, gy)
    base = base * (1 - 0.6 * river_a[..., None]) + np.array([150, 170, 190], np.float32) / 255 * 0.6 * river_a[..., None]
    base = base * (1 - 0.55 * coast_a[..., None]) + np.array([120, 130, 140], np.float32) / 255 * 0.55 * coast_a[..., None]

    # borders between countries (only where both sides are land)
    e = np.zeros(ids_ss.shape, bool)
    e[:, 1:] |= (ids_ss[:, 1:] != ids_ss[:, :-1]) & (ids_ss[:, 1:] > 0) & (ids_ss[:, :-1] > 0)
    e[1:, :] |= (ids_ss[1:, :] != ids_ss[:-1, :]) & (ids_ss[1:, :] > 0) & (ids_ss[:-1, :] > 0)
    e = ndimage.binary_dilation(e)
    border_a = np.asarray(Image.fromarray((e * 255).astype(np.uint8)).resize((pw, ph), Image.BOX),
                          np.float32) / 255.0 * land_a * (1 - coast_a)

    res = dict(base=base.astype(np.float32), ids=ids.astype(np.uint8), land=land_a.astype(np.float32),
               border=border_a.astype(np.float32), road=road_a.astype(np.float32),
               rail=rail_a.astype(np.float32), slope=slope.astype(np.float32))
    np.savez_compressed(out, **res)
    return res


if __name__ == "__main__":  # noqa
    import sys
    W, H = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1280, 720)
    full = np.full((H, W, 3), 0.1, np.float32)
    for name in PANELS:
        r = build(name, W, H)
        fr = PanelFrame(name, W, H)
        img = r["base"].copy()
        img[r["ids"] > 0] *= np.array([0.8, 0.85, 1.0], np.float32)
        full[:, fr.px0:fr.px0 + fr.pw] = img
        print(name, fr.bbox)
    Image.fromarray((np.clip(full, 0, 1) * 255).astype(np.uint8)).save(os.path.join(CACHE, "preview.png"))
