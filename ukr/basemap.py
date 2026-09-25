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

class View:
    """A map view: projection, frame extent and (for world maps) the longitude where it wraps."""

    def __init__(self, name, proj, x0, x1, y1, bbox=None, seam=None, min_lat=None, label_scale=1.0):
        self.name, self.proj = name, pyproj.Proj(proj)
        self.X0, self.X1, self.Y1 = x0, x1, y1
        self.Y0 = y1 - (x1 - x0) * 9 / 16
        self.bbox, self.seam, self.min_lat, self.label_scale = bbox, seam, min_lat, label_scale


def _world_view():
    p = pyproj.Proj("+proj=mill +lon_0=10 +over +ellps=WGS84")
    x0, _ = p(-170, 0)
    x1, _ = p(190, 0)
    _, y1 = p(0, 84)
    return View("world", "+proj=mill +lon_0=10 +over +ellps=WGS84", x0, x1, y1, seam=-170.0, min_lat=-60.0,
                label_scale=0.55)


def _ukraine_view():
    proj = "+proj=lcc +lat_1=45 +lat_2=52 +lat_0=48.35 +lon_0=31.5 +ellps=WGS84"
    p = pyproj.Proj(proj)
    x0, _ = p(20.2, 48.35)
    x1, _ = p(42.8, 48.35)
    _, yc = p(31.5, 48.35)
    y1 = yc + (x1 - x0) * 9 / 32
    return View("ukraine", proj, x0, x1, y1, bbox=(14, 38, 50, 58))


VIEWS = {
    "ukraine": _ukraine_view(),
}

NE_URLS = {
    "SR_50M": "https://naturalearth.s3.amazonaws.com/50m_raster/SR_50M.zip",
    "ne_50m_land": "https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_land.zip",
    "ne_50m_lakes": "https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_lakes.zip",
    "ne_50m_rivers_lake_centerlines": "https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_rivers_lake_centerlines.zip",
    "ne_10m_railroads": "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_railroads.zip",
}

# Modern countries (Natural Earth ADM0_A3) shown on the map; everything else in view is "OTH".
COUNTRIES = ["UKR", "RUS", "BLR", "MDA", "ROU", "POL", "SVK", "HUN", "GEO", "BGR", "TUR", "LTU", "LVA", "KAZ"]
COUNTRY_KEYS = sorted(COUNTRIES + ["OTH"])
KEY_ID = {k: i + 1 for i, k in enumerate(COUNTRY_KEYS)}
NAME_KEYS = {}  # kept for compatibility with geo.py


@functools.lru_cache(None)
def country_shapes():
    """Countries as shapely geometries. Crimea and Sevastopol (drawn inside Russia by Natural Earth)
    are returned to Ukraine; the timeline shows them as occupied since 2014."""
    from shapely.geometry import shape
    from shapely.ops import unary_union
    S = {}
    sf = shapefile.Reader(os.path.join(DL, "ne_10m_admin_0_countries", "ne_10m_admin_0_countries.shp"))
    for sr in sf.iterShapeRecords():
        a3 = sr.record["ADM0_A3"]
        b = sr.shape.bbox
        if b[2] < 10 or b[0] > 60 or b[3] < 35 or b[1] > 62:
            continue
        key = a3 if a3 in COUNTRIES else "OTH"
        S.setdefault(key, []).append(shape(sr.shape.__geo_interface__).buffer(0))
    S = {k: unary_union(v) for k, v in S.items()}
    sf = shapefile.Reader(os.path.join(DL, "ne_10m_admin_1_states_provinces", "ne_10m_admin_1_states_provinces.shp"))
    crimea = unary_union([shape(sr.shape.__geo_interface__).buffer(0) for sr in sf.iterShapeRecords()
                          if sr.record["adm0_a3"] == "RUS" and sr.record["name"] in ("Crimea", "Sevastopol")])
    S["RUS"] = S["RUS"].difference(crimea.buffer(0.005))
    S["UKR"] = unary_union([S["UKR"], crimea])
    return S


@functools.lru_cache(None)
def oblast_lines():
    """Internal borders of Ukraine (oblasts) and of Russia's border regions, as lon/lat rings."""
    from shapely.geometry import shape
    sf = shapefile.Reader(os.path.join(DL, "ne_10m_admin_1_states_provinces", "ne_10m_admin_1_states_provinces.shp"))
    rings = []
    for sr in sf.iterShapeRecords():
        if sr.record["adm0_a3"] not in ("UKR", "RUS", "BLR"):
            continue
        b = sr.shape.bbox
        if b[2] < 20 or b[0] > 44 or b[3] < 43 or b[1] > 54:
            continue
        g = shape(sr.shape.__geo_interface__)
        for p in (g.geoms if hasattr(g, "geoms") else [g]):
            rings.append(np.asarray(p.exterior.coords))
    return rings


def dem_sample(lon, lat, z=8):
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
    def __init__(self, W, H, view="ukraine"):
        self.W, self.H = W, H
        self.view = v = VIEWS[view] if isinstance(view, str) else view
        self.sx = W / (v.X1 - v.X0)
        self.sy = H / (v.Y1 - v.Y0)

    def px(self, lon, lat, ss=1):
        v = self.view
        lon = np.asarray(lon, float)
        if v.seam is not None:
            lon = np.where(lon < v.seam, lon + 360.0, lon)
        x, y = v.proj(lon, np.asarray(lat, float))
        return (x - v.X0) * self.sx * ss, (v.Y1 - y) * self.sy * ss

    def pts(self, lonlat, ss=1):
        a = np.asarray(lonlat, float)
        x, y = self.px(a[:, 0], a[:, 1], ss)
        return list(zip(x.tolist(), y.tolist()))

    def lonlat_grid(self):
        v = self.view
        xs = v.X0 + (np.arange(self.W) + 0.5) / self.sx
        ys = v.Y1 - (np.arange(self.H) + 0.5) / self.sy
        gx, gy = np.meshgrid(xs, ys)
        lon, lat = v.proj(gx, gy, inverse=True)
        return (lon + 180.0) % 360.0 - 180.0, lat

    # -- geometry helpers that respect the view's extent and wrap seam --
    def in_view(self, a):
        v = self.view
        if v.min_lat is not None and a[:, 1].max() < v.min_lat:
            return False
        if v.bbox is None:
            return True
        x0, y0, x1, y1 = v.bbox
        return a[:, 0].max() > x0 and a[:, 0].min() < x1 and a[:, 1].max() > y0 and a[:, 1].min() < y1

    def split_polygon(self, poly):
        """Shapely polygon -> list of polygons that do not cross the wrap seam."""
        v = self.view
        if v.seam is None:
            return [poly]
        from shapely.geometry import box
        from shapely.affinity import translate
        out = []
        for part, shift in ((poly.intersection(box(v.seam, -90, 180, 90)), 0.0),
                            (poly.intersection(box(-180, -90, v.seam, 90)), 360.0)):
            if part.is_empty:
                continue
            geoms = part.geoms if hasattr(part, "geoms") else [part]
            for g in geoms:
                if g.geom_type == "Polygon" and not g.is_empty:
                    out.append(translate(g, shift) if shift else g)
        return out

    def split_line(self, a):
        """(N,2) lon/lat polyline -> pieces that do not jump across the wrap seam."""
        v = self.view
        if v.seam is None:
            return [a]
        lon = np.where(a[:, 0] < v.seam, a[:, 0] + 360.0, a[:, 0])
        cut = np.nonzero(np.abs(np.diff(lon)) > 180)[0]
        pieces = np.split(np.stack([lon, a[:, 1]], 1), cut + 1)
        return [p for p in pieces if len(p) > 1]


def _rings(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        yield poly[0], poly[1:]


def build(W=1280, H=720, view="ukraine"):
    os.makedirs(CACHE, exist_ok=True)
    vname = view if isinstance(view, str) else view.name
    out = os.path.join(CACHE, f"basemap_{vname}_{W}x{H}_k{len(KEY_ID)}.npz")
    if os.path.exists(out):
        return dict(np.load(out))
    ensure_downloads()
    fr = Frame(W, H, view)
    SS = 3  # supersampling for anti-aliased lines
    from shapely.geometry import Polygon as SPolygon

    def polys_of(geom):
        gs = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        for g in gs:
            if not fr.in_view(np.asarray(g.exterior.coords)):
                continue
            yield from fr.split_polygon(g)

    # ---- country id raster (drawn at SS, borders derived from it) --------------
    idimg = Image.new("L", (W * SS, H * SS), 0)
    dr = ImageDraw.Draw(idimg)
    for key, shp in country_shapes().items():
        for p in polys_of(shp):
            dr.polygon(fr.pts(p.exterior.coords, SS), fill=KEY_ID[key])
            for h in p.interiors:
                dr.polygon(fr.pts(h.coords, SS), fill=0)

    # ---- land / water ---------------------------------------------------------
    def shp_rings(path):
        for s in shapefile.Reader(path).shapes():
            parts = list(s.parts) + [len(s.points)]
            for i in range(len(parts) - 1):
                r = np.asarray(s.points[parts[i]:parts[i + 1]], float)
                if len(r) > 2 and fr.in_view(r):
                    yield r

    land = Image.new("L", (W * SS, H * SS), 0)
    ld = ImageDraw.Draw(land)
    coast = []
    for r in shp_rings(os.path.join(DL, "ne_10m_land", "ne_10m_land.shp")):
        if fr.view.min_lat is not None and r[:, 1].max() < fr.view.min_lat:
            continue
        for p in fr.split_polygon(SPolygon(r).buffer(0)):
            ld.polygon(fr.pts(p.exterior.coords, SS), fill=255)
        coast.append(r)  # outline from the original ring (split_line handles the seam)
    lakes = []
    for r in shp_rings(os.path.join(DL, "ne_10m_lakes", "ne_10m_lakes.shp")):
        for p in fr.split_polygon(SPolygon(r).buffer(0)):
            ld.polygon(fr.pts(p.exterior.coords, SS), fill=0)
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

    # ---- terrain: hill-shading from Terrarium elevation tiles (zoom 8) ------------------------
    lon, lat = fr.lonlat_grid()
    elev = dem_sample(lon, lat)
    m_per_px = (fr.view.X1 - fr.view.X0) / W
    e = ndimage.gaussian_filter(np.maximum(elev, 0), 0.8) * 3.0  # exaggerate: Ukraine is mostly flat
    gy, gx = np.gradient(e, m_per_px)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, zen = np.radians(315.0), np.radians(45.0)
    hs = np.cos(zen) * np.cos(slope) + np.sin(zen) * np.sin(slope) * np.cos(az - aspect)
    rel = np.clip(0.63 + 0.42 * hs, 0.45, 1.06).astype(np.float32)

    land_rgb = np.array([196, 200, 170], np.float32) / 255.0  # muted green, like satellite imagery
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
            r = np.asarray(r, float)
            if closed:
                r = np.concatenate([r, r[:1]])
            for piece in fr.split_line(r):
                d.line(fr.pts(piece, SS), fill=255, width=width, joint="curve")
        return np.asarray(im.resize((W, H), Image.BOX), np.float32) / 255.0

    coast_a = line_layer(coast + lakes, max(1, SS // 2))
    e = np.zeros(ids_ss.shape, bool)
    e[:, 1:] |= (ids_ss[:, 1:] != ids_ss[:, :-1]) & (ids_ss[:, 1:] > 0) & (ids_ss[:, :-1] > 0)
    e[1:, :] |= (ids_ss[1:, :] != ids_ss[:-1, :]) & (ids_ss[1:, :] > 0) & (ids_ss[:-1, :] > 0)
    e = ndimage.binary_dilation(e, iterations=1)
    border_a = np.asarray(Image.fromarray((e * 255).astype(np.uint8)).resize((W, H), Image.BOX),
                          np.float32) / 255.0 * land_a * (1 - coast_a)
    # oblast / region borders: thinner and fainter than national borders
    border_a = np.maximum(border_a, 0.45 * line_layer(oblast_lines(), max(1, SS // 2)) * land_a * (1 - coast_a))
    rivers = []
    sf = shapefile.Reader(os.path.join(DL, "ne_10m_rivers_lake_centerlines",
                                       "ne_10m_rivers_lake_centerlines.shp"))
    for s in sf.shapes():
        parts = list(s.parts) + [len(s.points)]
        for i in range(len(parts) - 1):
            r = np.asarray(s.points[parts[i]:parts[i + 1]], float)
            if len(r) > 1 and fr.in_view(r):
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
            if len(r) > 1 and fr.in_view(r):
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
    view = sys.argv[3] if len(sys.argv) > 3 else "europe"
    r = build(W, H, view)
    img = (np.clip(r["base"], 0, 1) * 255).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(CACHE, f"base_preview_{view}.png"))
    rng = np.random.default_rng(0)
    pal = rng.integers(60, 255, (256, 3)).astype(np.uint8)
    pal[0] = 0
    Image.fromarray(pal[r["ids"]]).save(os.path.join(CACHE, f"ids_preview_{view}.png"))
    print({k: KEY_ID[k] for k in COUNTRY_KEYS})
