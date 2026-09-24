"""Builds the static layers of the map (terrain, water, borders, country ids).

Everything that does not change from frame to frame is computed once here and
cached in build/cache/basemap_<W>x<H>.npz so the renderer only has to paint the
moving parts (alliances, occupied territory, army sizes, captions).
"""
import functools
import json
import os
import zipfile

import numpy as np
import pyproj
import shapefile
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CACHE = os.path.join(HERE, "build", "cache")
DL = os.path.join(HERE, "build", "downloads")

# Lambert conformal conic centred on Europe; extent chosen so the Western
# Front, Petrograd and Baghdad/Basra all fit in a 16:9 frame.
PROJ = pyproj.Proj("+proj=lcc +lat_1=35 +lat_2=60 +lat_0=47 +lon_0=17 +ellps=WGS84")
X0, X1 = -2400e3, 3550e3
Y1 = 1480e3
Y0 = Y1 - (X1 - X0) * 9 / 16

NE_URLS = {
    "SR_50M": "https://naturalearth.s3.amazonaws.com/50m_raster/SR_50M.zip",
    "ne_50m_land": "https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_land.zip",
    "ne_50m_lakes": "https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_lakes.zip",
    "ne_50m_rivers_lake_centerlines": "https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_rivers_lake_centerlines.zip",
    "ne_10m_railroads": "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_railroads.zip",
}

# 1914 polity name -> country key used by the timeline.
NAME_KEYS = {
    "German Empire": "GER", "Austro-Hungarian Empire": "AUH", "Ottoman Empire": "OTT",
    "Bulgaria": "BUL", "France": "FRA", "United Kingdom of Great Britain and Ireland": "UK",
    "Belgium": "BEL", "Serbia": "SER", "Montenegro": "MNE", "Kingdom of Italy": "ITA",
    "Romania": "ROM", "Russian Empire": "RUS", "Finland": "FIN", "Georgia": "RUS",
    "Armenia": "RUS", "Azerbaijan": "RUS", "Greece": "GRE", "Portugal": "POR",
    "Algeria": "ALG", "Tunisia": "TUN", "Morocco": "MOR", "Egypt": "EGY", "Libya": "LIB",
    "Malta": "MLT", "Kuwait": "KUW", "British Protectorate": "BPR", "Spain": "ESP",
    "Spanish Morocco": "ESP", "Spanish Sahara": "ESP", "Rio De Oro": "ESP",
    "Sweden": "SWE", "Norway": "NOR", "Denmark": "DEN", "Iceland": "DEN",
    "Netherlands": "NED", "Switzerland": "SUI", "Luxembourg": "LUX", "Albania": "ALB",
    "Persia": "PER", "Arabia (Nejd)": "ARA", "Qatar": "ARA", "Afghanistan": "AFG",
    "French West Africa": "ALG", "British Raj": "BPR",
}
# Unnamed islands in the source data: (lon, lat) of a point on them -> key.
ISLAND_OVERRIDES = [((9.1, 42.2), "FRA"), ((33.2, 35.1), "CYP"), ((24.9, 35.2), "GRE"),
                    ((28.0, 36.3), "ITA"), ((9.0, 40.0), "ITA"), ((14.0, 37.5), "ITA")]


# The source dataset mixes borders from different years; these patches restore
# the 1914 situation: (gains, loses, polygon lon/lat).
BORDER_FIXES = [
    ("GER", ["FRA"], [(5.95, 49.52), (6.5, 49.52), (7.3, 48.6), (7.12, 48.5), (6.8, 48.62),
                      (6.5, 48.75), (6.3, 48.85), (6.02, 48.97), (5.95, 49.2)]),          # Lorraine
    ("AUH", ["ITA"], [(13.25, 45.7), (13.45, 45.95), (13.9, 45.9), (14.0, 45.4), (13.2, 45.4)]),  # Trieste
    ("RUS", ["OTT"], [(41.55, 41.52), (41.9, 41.2), (42.0, 40.6), (42.4, 40.3), (42.7, 40.0),
                      (43.2, 39.8), (43.9, 39.72), (44.3, 39.7), (44.67, 39.76), (44.4, 40.2),
                      (43.8, 41.2), (42.5, 41.6)]),                                         # Kars, Ardahan
    ("OTT", ["BUL"], [(26.0, 40.6), (26.1, 40.85), (26.35, 41.25), (26.35, 41.75), (26.6, 41.95),
                      (27.2, 42.05), (28.1, 41.98), (29.5, 41.2), (29.5, 40.0), (26.0, 40.0)]),  # East Thrace
    ("RUS", ["ROM"], [(26.6, 48.25), (26.95, 48.05), (27.25, 47.9), (27.6, 47.5), (27.85, 47.15),
                      (28.1, 46.8), (28.2, 46.4), (28.15, 45.9), (28.2, 45.47), (28.8, 45.2),
                      (30.0, 45.2), (30.5, 46.5), (29.5, 48.5), (27.0, 48.6)]),            # Bessarabia
    ("ROM", ["BUL"], [(26.5, 44.05), (26.5, 43.95), (28.1, 43.33), (28.8, 43.4), (28.8, 44.3),
                      (26.5, 44.3)]),                                                       # S. Dobruja
    ("AUH", ["SER"], [(19.0, 44.9), (19.4, 44.92), (19.7, 44.78), (20.0, 44.74), (20.25, 44.7),
                      (20.45, 44.83), (20.6, 44.9), (20.6, 45.4), (19.0, 45.4)]),           # Syrmia
]

COUNTRY_KEYS = sorted(set(NAME_KEYS.values()) | {"CYP"})
KEY_ID = {k: i + 1 for i, k in enumerate(COUNTRY_KEYS)}


@functools.lru_cache(None)
def country_shapes():
    """1914 countries as shapely geometries keyed by country key, with BORDER_FIXES applied."""
    from shapely.geometry import Point, Polygon, shape
    from shapely.ops import unary_union
    feats = json.load(open(os.path.join(DATA, "world_1914.geojson")))["features"]
    named, unnamed = {}, []
    for f in feats:
        name = f["properties"].get("NAME")
        g = shape(f["geometry"]).buffer(0)
        if name in NAME_KEYS:
            named.setdefault(NAME_KEYS[name], []).append(g)
        elif not name:
            unnamed.append(g)
    S = {k: unary_union(v) for k, v in named.items()}
    for g in unnamed:
        key = None
        for (lo, la), k in ISLAND_OVERRIDES:
            if g.buffer(0.3).contains(Point(lo, la)):
                key = k
        if key is None:
            c = g.representative_point()
            d, key = min((s.distance(c), k) for k, s in S.items())
            if d > 2.0:
                continue
        S[key] = unary_union([S[key], g]) if key in S else g
    for to, frm, poly in BORDER_FIXES:
        P = Polygon(poly)
        for k in frm:
            moved = S[k].intersection(P)
            S[k] = S[k].difference(P)
            S[to] = unary_union([S[to], moved])
    return S


def ensure_downloads():
    os.makedirs(DL, exist_ok=True)
    import urllib.request
    for name, url in NE_URLS.items():
        d = os.path.join(DL, name)
        if os.path.isdir(d):
            continue
        z = d + ".zip"
        if not os.path.exists(z):
            print("downloading", url)
            urllib.request.urlretrieve(url, z)
        with zipfile.ZipFile(z) as f:
            f.extractall(d)


class Frame:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.sx = W / (X1 - X0)
        self.sy = H / (Y1 - Y0)

    def px(self, lon, lat, ss=1):
        x, y = PROJ(np.asarray(lon, float), np.asarray(lat, float))
        return (x - X0) * self.sx * ss, (Y1 - y) * self.sy * ss

    def pts(self, lonlat, ss=1):
        a = np.asarray(lonlat, float)
        x, y = self.px(a[:, 0], a[:, 1], ss)
        return list(zip(x.tolist(), y.tolist()))

    def lonlat_grid(self):
        xs = X0 + (np.arange(self.W) + 0.5) / self.sx
        ys = Y1 - (np.arange(self.H) + 0.5) / self.sy
        gx, gy = np.meshgrid(xs, ys)
        lon, lat = PROJ(gx, gy, inverse=True)
        return lon, lat


def _rings(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        yield poly[0], poly[1:]


def _clip_ring(ring):
    a = np.asarray(ring, float)
    return a if (a[:, 0].max() > -30 and a[:, 0].min() < 75 and a[:, 1].max() > 15) else None


def build(W=1280, H=720):
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, f"basemap_{W}x{H}.npz")
    if os.path.exists(out):
        return dict(np.load(out))
    ensure_downloads()
    fr = Frame(W, H)
    SS = 3  # supersampling for anti-aliased lines

    # ---- country id raster (drawn at SS, borders derived from it) --------------
    idimg = Image.new("L", (W * SS, H * SS), 0)
    dr = ImageDraw.Draw(idimg)
    for key, shp in country_shapes().items():
        polys = shp.geoms if shp.geom_type == "MultiPolygon" else [shp]
        for p in polys:
            e = _clip_ring(p.exterior.coords)
            if e is None:
                continue
            dr.polygon(fr.pts(e, SS), fill=KEY_ID[key])
            for h in p.interiors:
                dr.polygon(fr.pts(h.coords, SS), fill=0)

    # ---- land / water ---------------------------------------------------------
    land = Image.new("L", (W * SS, H * SS), 0)
    ld = ImageDraw.Draw(land)
    sf = shapefile.Reader(os.path.join(DL, "ne_50m_land", "ne_50m_land.shp"))
    coast = []
    for s in sf.shapes():
        parts = list(s.parts) + [len(s.points)]
        for i in range(len(parts) - 1):
            r = _clip_ring(s.points[parts[i]:parts[i + 1]])
            if r is not None:
                ld.polygon(fr.pts(r, SS), fill=255)
                coast.append(r)
    lakes = []
    sf = shapefile.Reader(os.path.join(DL, "ne_50m_lakes", "ne_50m_lakes.shp"))
    for s in sf.shapes():
        parts = list(s.parts) + [len(s.points)]
        for i in range(len(parts) - 1):
            r = _clip_ring(s.points[parts[i]:parts[i + 1]])
            if r is not None:
                ld.polygon(fr.pts(r, SS), fill=0)
                lakes.append(r)
    land_a = np.asarray(land.resize((W, H), Image.BOX), np.float32) / 255.0
    landmask = land_a > 0.5

    ids_ss = np.asarray(idimg)
    ids = ids_ss[SS // 2::SS, SS // 2::SS].copy()
    # fill land pixels the historical dataset missed with the nearest country
    missing = (ids == 0)
    _, (iy, ix) = ndimage.distance_transform_edt(missing, return_indices=True)
    ids = ids[iy, ix]
    ids[~landmask] = 0

    # ---- terrain --------------------------------------------------------------
    Image.MAX_IMAGE_PIXELS = None
    sr = np.asarray(Image.open(os.path.join(DL, "SR_50M", "SR_50M.tif")), np.float32)
    lon, lat = fr.lonlat_grid()
    col = (lon + 179.98333) / 0.0333333
    row = (89.98333 - lat) / 0.0333333
    relief = ndimage.map_coordinates(sr, [row, col], order=1) / 255.0
    rel = np.clip((relief - 0.55) * 1.3 + 0.8, 0.45, 1.06)

    land_rgb = np.array([234, 232, 224], np.float32) / 255.0
    rng = np.random.default_rng(3)
    grain = ndimage.gaussian_filter(rng.normal(0, 1, (H, W)).astype(np.float32), 1.2) * 0.02
    landc = land_rgb[None, None, :] * (rel[..., None] + grain[..., None])

    water_rgb = np.array([203, 218, 232], np.float32) / 255.0
    yy, xx = np.mgrid[0:H, 0:W]
    hatch = ((xx + yy) % 6 < 1).astype(np.float32) * 0.025
    waterc = water_rgb[None, None, :] - hatch[..., None]

    base = waterc * (1 - land_a[..., None]) + landc * land_a[..., None]

    # ---- line layers (drawn at SS and downsampled) ----------------------------
    def line_layer(rings_or_lines, width, closed=True):
        im = Image.new("L", (W * SS, H * SS), 0)
        d = ImageDraw.Draw(im)
        for r in rings_or_lines:
            p = fr.pts(r, SS)
            if closed:
                p = p + [p[0]]
            d.line(p, fill=255, width=width, joint="curve")
        return np.asarray(im.resize((W, H), Image.BOX), np.float32) / 255.0

    coast_a = line_layer(coast + lakes, max(1, SS // 2))
    e = np.zeros(ids_ss.shape, bool)
    e[:, 1:] |= (ids_ss[:, 1:] != ids_ss[:, :-1]) & (ids_ss[:, 1:] > 0) & (ids_ss[:, :-1] > 0)
    e[1:, :] |= (ids_ss[1:, :] != ids_ss[:-1, :]) & (ids_ss[1:, :] > 0) & (ids_ss[:-1, :] > 0)
    e = ndimage.binary_dilation(e, iterations=1)
    border_a = np.asarray(Image.fromarray((e * 255).astype(np.uint8)).resize((W, H), Image.BOX),
                          np.float32) / 255.0 * land_a * (1 - coast_a)
    rivers = []
    sf = shapefile.Reader(os.path.join(DL, "ne_50m_rivers_lake_centerlines",
                                       "ne_50m_rivers_lake_centerlines.shp"))
    for s in sf.shapes():
        parts = list(s.parts) + [len(s.points)]
        for i in range(len(parts) - 1):
            r = np.asarray(s.points[parts[i]:parts[i + 1]], float)
            if len(r) > 1 and r[:, 0].max() > -30 and r[:, 0].min() < 75 and r[:, 1].max() > 15:
                rivers.append(r)
    river_a = line_layer(rivers, max(1, SS // 2), closed=False) * land_a

    # railways (main and secondary lines), drawn on top of the alliance colours by the renderer
    rails = []
    sf = shapefile.Reader(os.path.join(DL, "ne_10m_railroads", "ne_10m_railroads.shp"))
    for sr in sf.iterShapeRecords():
        if sr.record["category"] not in (1, 2):
            continue
        s = sr.shape
        parts = list(s.parts) + [len(s.points)]
        for i in range(len(parts) - 1):
            r = np.asarray(s.points[parts[i]:parts[i + 1]], float)
            if len(r) > 1 and r[:, 0].max() > -30 and r[:, 0].min() < 75 and r[:, 1].max() > 15:
                rails.append(r)
    rail_a = line_layer(rails, max(1, SS // 2), closed=False) * land_a

    river_rgb = np.array([150, 170, 190], np.float32) / 255.0
    base = base * (1 - 0.6 * river_a[..., None]) + river_rgb * 0.6 * river_a[..., None]
    coast_rgb = np.array([120, 130, 140], np.float32) / 255.0
    base = base * (1 - 0.55 * coast_a[..., None]) + coast_rgb * 0.55 * coast_a[..., None]

    res = dict(base=base.astype(np.float32), ids=ids.astype(np.uint8), land=land_a.astype(np.float32),
               border=border_a.astype(np.float32), rail=rail_a.astype(np.float32))
    np.savez_compressed(out, **res)
    return res


if __name__ == "__main__":
    import sys
    W, H = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1280, 720)
    r = build(W, H)
    img = (np.clip(r["base"], 0, 1) * 255).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(CACHE, "base_preview.png"))
    rng = np.random.default_rng(0)
    pal = rng.integers(60, 255, (256, 3)).astype(np.uint8)
    pal[0] = 0
    Image.fromarray(pal[r["ids"]]).save(os.path.join(CACHE, "ids_preview.png"))
    print({k: KEY_ID[k] for k in COUNTRY_KEYS})
