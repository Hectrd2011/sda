"""Geometry helpers for authoring the timeline: 1914 country shapes and shared borders."""
import functools
import json
import os

import numpy as np
from shapely.geometry import LineString, Point, shape
from shapely.ops import unary_union

import basemap as bm


@functools.lru_cache(None)
def shapes():
    return bm.country_shapes()


def _unused():
    feats = json.load(open(os.path.join(bm.DATA, "world_1914.geojson")))["features"]
    S = {}
    for f in feats:
        k = bm.NAME_KEYS.get(f["properties"].get("NAME"))
        if k:
            S.setdefault(k, []).append(shape(f["geometry"]))
    return {k: unary_union(v) for k, v in S.items()}


@functools.lru_cache(None)
def border(a, b, tol=0.03):
    """Longest shared border run between countries a and b as an (N,2) array."""
    S = bm.country_shapes()
    A = S[a]
    polys = A.geoms if A.geom_type == "MultiPolygon" else [A]
    runs = []
    for p in polys:
        c = np.array(p.exterior.coords)[:-1]
        near = np.array([S[b].distance(Point(x, y)) < tol for x, y in c])
        if near.all() or not near.any():
            continue
        i0 = int(np.argmin(near))
        c, near = np.roll(c, -i0, 0), np.roll(near, -i0)
        cur = []
        for pt, n in zip(c, near):
            if n:
                cur.append(pt)
            elif cur:
                runs.append(np.array(cur))
                cur = []
        if cur:
            runs.append(np.array(cur))
    return max(runs, key=len)


def border_between(a, b, p_from, p_to, simplify=0.01):
    """Border run a/b oriented and clipped from the point nearest p_from to nearest p_to."""
    r = border(a, b)
    i = int(np.argmin(((r - p_from) ** 2).sum(1)))
    j = int(np.argmin(((r - p_to) ** 2).sum(1)))
    seg = r[i:j + 1] if i <= j else r[j:i + 1][::-1]
    if simplify and len(seg) > 2:
        seg = np.array(LineString(seg).simplify(simplify).coords)
    return [tuple(map(float, p)) for p in seg]


if __name__ == "__main__":
    import sys
    a, b = sys.argv[1], sys.argv[2]
    r = np.array(LineString(border(a, b)).simplify(0.08).coords)
    print(a, b, len(r))
    print(", ".join(f"({x:.2f},{y:.2f})" for x, y in r))
