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


def _im_view():
    """Italian Mapper's WW1 framing, measured from his video: Miller cylindrical, 20.55W..55.94E, top at 63.16N."""
    proj = "+proj=mill +lon_0=0 +ellps=WGS84"
    p = pyproj.Proj(proj)
    x0, _ = p(-20.55, 0)
    x1, _ = p(55.94, 0)
    _, y1 = p(0, 63.16)
    return View("europe", proj, x0, x1, y1, bbox=(-40, 15, 80, 80))


VIEWS = {
    "europe": _im_view(),
    # the earlier Lambert conformal conic view (Western Front, Petrograd and Basra in one 16:9 frame)
    "europe_lcc": View("europe_lcc", "+proj=lcc +lat_1=35 +lat_2=60 +lat_0=47 +lon_0=17 +ellps=WGS84",
                       -2400e3, 3550e3, 1480e3, bbox=(-30, 15, 75, 90)),
    # Miller cylindrical world map from Alaska (left) to Chukotka (right).
    "world": _world_view(),
}

NE_URLS = {
    "SR_50M": "https://naturalearth.s3.amazonaws.com/50m_raster/SR_50M.zip",
    "ne_50m_land": "https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_land.zip",
    "ne_50m_lakes": "https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_lakes.zip",
    "ne_50m_rivers_lake_centerlines": "https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_rivers_lake_centerlines.zip",
    "ne_10m_railroads": "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_railroads.zip",
    "ne_10m_urban_areas": "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_urban_areas.zip",
}
# NASA Blue Marble Next Generation, July 2004 (public domain), the satellite texture under the map
BLUE_MARBLE = ("bm_200407.jpg",
               "https://eoimages.gsfc.nasa.gov/images/imagerecords/74000/74092/world.200407.3x21600x10800.jpg")
# Fitted to Christopher's WW2 map (4K, 13 regions, mean error 1.5 levels): the texture is the satellite
# image with its contrast boosted, T = clip(TEX_P + TEX_Q * bluemarble); every area is then
# alpha * colour + (1 - alpha) * T  (neutral land: alpha 0.77 of a cream).
TEX_P = (24.0, 40.0, 79.0)
TEX_Q = 2.27
NEUTRAL = ((246, 241, 230), 0.77)
SEA_MEAN = (208, 221, 236)   # Italian Mapper's WW1 sea (Christopher: 217,226,238)
SHADE_K = 0.45   # strength of the terrain shading over the colours
RAIL_CATEGORIES = (1, 2)
RAIL_MAX_SCALERANK = 7     # the more important lines only: Italian Mapper's network is moderate

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
    # ---- rest of the world (used by the world view) ----
    "Canada": "CAN", "Australia": "AUS", "New Zealand": "NZL", "Niue": "NZL", "South Africa": "SAF",
    "Lesotho": "SAF", "Swaziland": "SAF", "Ceylon": "BPR", "British East Africa": "BEA", "Uganda": "BEA",
    "Anglo-Egyptian Sudan": "SUD", "Nigeria": "BWA", "Gold Coast": "BWA", "Sierra Leone": "BWA",
    "Gambia, The": "BWA", "British Somaliland": "BSO", "Rhodesia": "RHO", "Malawi": "RHO", "Botswana": "RHO",
    "Malaya": "BAS", "Brunei": "BAS", "Hong Kong": "BAS", "Fiji": "BAS", "Tonga": "BAS",
    "Belize": "BAM", "Guyana": "BAM", "Antigua and Barbuda": "BAM", "Barbados": "BAM", "Dominica": "BAM",
    "Grenada": "BAM", "Montserrat": "BAM", "Saint Kitts and Nevis": "BAM", "Saint Lucia": "BAM",
    "Saint Vincent and the Grenadines": "BAM", "Anguilla": "BAM",
    "French Equatorial Africa": "FEA", "Madagascar (France)": "FEA", "Djibouti": "FEA",
    "French Indochina": "FIC", "Wallis and Futuna Islands": "FIC", "French Guiana": "FAM",
    "Guadeloupe": "FAM", "Martinique": "FAM", "Saint Barthelemy": "FAM", "Saint Martin": "FAM",
    "Belgian Congo": "BCO", "Angola": "PCO", "Mozambique": "PCO", "Portuguese Guinea": "PCO",
    "Eritrea": "ICO", "Italian Somaliland": "ICO",
    "Kamerun": "KAM", "Togoland": "TOG", "German South-West Africa": "GSW",
    "German E. Africa (Tanganyika)": "GEA", "Samoa": "GSA", "Papua New Guinea": "PNG",
    "Empire of Japan": "JAP", "Sakhalin (RU)": "RUS",
    "United States": "USA", "Puerto Rico": "USA", "Philippines": "USA", "American Samoa": "USA",
    "United States Virgin Islands": "USA",
    "Manchu Empire": "CHN", "Xinjiang": "CHN", "Tibet": "TIB", "Mongolia": "MNG",
    "Brazil": "BRA", "Cuba": "CUB", "Panama": "PAN", "Guatemala": "GUA", "Nicaragua": "NIC",
    "Costa Rica": "CRI", "Haiti": "HAI", "Honduras": "HON", "Liberia": "LBR", "Rattanakosin Kingdom": "SIA",
    "Mexico": "MEX", "Argentina": "ARG", "Chile": "CHL", "Rapa Nui": "CHL", "Peru": "PRU", "Bolivia": "BOL",
    "Paraguay": "PRY", "Uruguay": "URY", "Venezuela": "VEN", "Colombia": "COL", "Ecuador": "ECU",
    "El Salvador": "SLV", "Dominican Republic": "DOM", "Suriname": "NED", "Netherlands Antilles": "NED",
    "Netherlands Indies": "NEI", "Abyssinia": "ABY", "Nepal": "NEP", "Bhutan": "BHU",
    "Equatorial Guinea": "ESP",
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
    def __init__(self, W, H, view="europe"):
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


def build(W=1280, H=720, view="europe"):
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
    for r in shp_rings(os.path.join(DL, "ne_50m_land", "ne_50m_land.shp")):
        if fr.view.min_lat is not None and r[:, 1].max() < fr.view.min_lat:
            continue
        for p in fr.split_polygon(SPolygon(r).buffer(0)):
            ld.polygon(fr.pts(p.exterior.coords, SS), fill=255)
        coast.append(r)  # outline from the original ring (split_line handles the seam)
    lakes = []
    for r in shp_rings(os.path.join(DL, "ne_50m_lakes", "ne_50m_lakes.shp")):
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

    # ---- terrain: contrast-boosted satellite texture ---------------------------
    Image.MAX_IMAGE_PIXELS = None
    bm_path = os.path.join(DL, BLUE_MARBLE[0])
    if not os.path.exists(bm_path):
        import urllib.request
        urllib.request.urlretrieve(BLUE_MARBLE[1], bm_path)
    lon, lat = fr.lonlat_grid()
    lon = ((lon + 180.0) % 360.0) - 180.0
    bmi = Image.open(bm_path)
    BW, BH = bmi.size
    cx = (lon + 180.0) / 360.0 * BW - 0.5
    cy = (90.0 - lat) / 180.0 * BH - 0.5
    x0, x1 = max(0, int(np.floor(cx.min())) - 2), min(BW, int(np.ceil(cx.max())) + 3)
    y0, y1 = max(0, int(np.floor(cy.min())) - 2), min(BH, int(np.ceil(cy.max())) + 3)
    crop = np.asarray(bmi.crop((x0, y0, x1, y1)), np.float32)
    del bmi
    # pre-blur a little where the output is coarser than the source (avoids sparkle)
    sat = np.stack([ndimage.map_coordinates(crop[..., c], [cy - y0, cx - x0], order=1, mode="nearest")
                    for c in range(3)], -1)
    # the Caspian is missing from the lake data: take it from the satellite image instead
    casp = (lon > 46.0) & (lon < 55.5) & (lat > 36.3) & (lat < 47.6)
    wet = casp & (sat.mean(-1) < 95) & (sat[..., 2] >= sat[..., 0] - 4)
    wet = ndimage.binary_opening(ndimage.binary_closing(wet, iterations=2), iterations=1)
    if wet.any():
        land_a = np.where(wet, 0.0, land_a).astype(np.float32)
        land_a = np.minimum(land_a, ndimage.gaussian_filter(land_a, 0.5))
        ids[wet] = 0
    tex = np.clip(np.array(TEX_P, np.float32) + TEX_Q * sat, 0, 255)
    # Italian Mapper's own map template (white land + satellite layer at 45/255), when it is present
    tpath = os.path.join(DL, "im_template_europe.npz")
    use_template = os.path.exists(tpath)
    if use_template:
        Tm = np.load(tpath)
        x0c, kxt, yeqt, kyt = Tm["proj"]
        bx0, by0 = Tm["box"][:2]
        txp = x0c + kxt * lon - bx0
        typ = yeqt - kyt * np.log(np.tan(np.pi / 4 + np.radians(np.clip(lat, -85, 85)) / 2)) - by0
        trgb = np.stack([ndimage.map_coordinates(Tm["rgb"][..., c].astype(np.float32), [typ, txp], order=1, mode="nearest")
                         for c in range(3)], -1)
        tland = ndimage.map_coordinates(Tm["land"].astype(np.float32), [typ, txp], order=1, mode="constant") > 0.5
        tex = np.where(tland[..., None], trgb, np.array([255, 252, 249], np.float32))
    # cities: dark blots, like the reference
    urban = Image.new("L", (W * SS, H * SS), 0)
    ud = ImageDraw.Draw(urban)
    for r in shp_rings(os.path.join(DL, "ne_10m_urban_areas", "ne_10m_urban_areas.shp")):
        for p in fr.split_polygon(SPolygon(r).buffer(0)):
            ud.polygon(fr.pts(p.exterior.coords, SS), fill=255)
    urban_a = np.asarray(urban.resize((W, H), Image.BOX), np.float32) / 255.0
    urban_a = ndimage.gaussian_filter(urban_a, 0.6 * W / 1920) * land_a
    if not use_template:   # Christopher's satellite style shows cities as dark blots; Italian Mapper's does not
        tex = tex * (1 - 0.55 * urban_a[..., None]) + np.array([70, 62, 55], np.float32) * 0.55 * urban_a[..., None]
    landc = tex / 255.0
    # terrain shading applied over the (near-solid) colours, as in Italian Mapper's WW1
    sr = np.asarray(Image.open(os.path.join(DL, "SR_50M", "SR_50M.tif")), np.float32)
    col = ((lon + 179.98333) % 360.0) / 0.0333333
    row = (89.98333 - lat) / 0.0333333
    relief = ndimage.map_coordinates(sr, [row, col], order=1) / 255.0
    del sr
    shade = np.clip(1.0 + (0.0 if use_template else SHADE_K) * (relief - np.median(relief[land_a > 0.5])), 0.8, 1.06)
    shade = (shade * land_a + (1 - land_a)).astype(np.float32)

    # sea as in the reference: pale blue with fine diagonal hatching running top-left to bottom-right
    # (measured on the 4K reference: 6.5 px spacing at 4K, lines at ~39 deg, 1080p mean (217,226,238), L std ~9.6)
    sp = 5.7 * W / 3840.0         # Italian Mapper: 2.85 px apart at 1080p, lines at 45 deg
    ss = 2 if W < 3000 else 1
    ang = np.radians(45.0)
    g = np.zeros((H, W), np.float32)
    for y0 in range(0, H, 256):           # in strips, to keep memory low at 4K
        y1 = min(H, y0 + 256)
        yy, xx = np.mgrid[y0 * ss:y1 * ss, 0:W * ss].astype(np.float32) / ss
        u = -xx * np.sin(ang) + yy * np.cos(ang)
        gg = ((1 + np.cos(2 * np.pi * u / sp)) / 2) ** 3
        g[y0:y1] = gg.reshape(y1 - y0, ss, W, ss).mean((1, 3))
    g = (g - g.mean()) / (g.std() + 1e-6)
    waterc = (np.array(SEA_MEAN, np.float32)[None, None, :] - 9.5 * g[..., None]) / 255.0

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
    rivers = []
    sf = shapefile.Reader(os.path.join(DL, "ne_50m_rivers_lake_centerlines",
                                       "ne_50m_rivers_lake_centerlines.shp"))
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
        if sr.record["category"] not in RAIL_CATEGORIES or sr.record["scalerank"] > RAIL_MAX_SCALERANK:
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
               border=border_a.astype(np.float32), rail=rail_a.astype(np.float32), shade=shade)
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
