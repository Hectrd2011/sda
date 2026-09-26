"""Metrics of an advance, used to compare our renderer with the reference frame by frame.
Input: frames (T,H,W,3) at 1080p-equivalent scale, fps; classifiers for 'defender' and 'attacker' colours."""
import numpy as np
from scipy import ndimage

def classify(F, defender, attacker, tol=38):
    d = np.sqrt(((F - np.array(defender, np.float32)) ** 2).sum(-1)) < tol
    a = np.sqrt(((F - np.array(attacker, np.float32)) ** 2).sum(-1)) < tol
    return d, a

def capture_trajectory(F, dmask, amask, fps, step=5, span=(-3, 12)):
    ys, xs = np.nonzero(dmask[0] & amask[-1])
    tr = []
    for y, x in zip(ys[::step], xs[::step]):
        nr = int(np.argmax(~dmask[:, y, x]))
        if nr + span[0] >= 0 and nr + span[1] < len(F):
            tr.append(F[nr + span[0]:nr + span[1], y, x])
    tr = np.array(tr)
    return np.median(tr, 0), len(tr)

def line_profile(img, dmask, amask, half=6):
    """Median colour vs signed distance (px) from the boundary: negative = attacker side."""
    da = ndimage.distance_transform_edt(~amask)
    dd = ndimage.distance_transform_edt(~dmask)
    band = (da < half + 1) & (dd < half + 1)
    sd = np.where(amask, -dd, da)  # rough signed distance
    out = {}
    for k in range(-half, half + 1):
        m = band & (np.abs(sd - k) < 0.5)
        if m.sum() > 20:
            out[k] = np.median(img[m], 0).astype(int)
    return out

def pale_colour(img, dmask, amask):
    L = img.mean(-1); sat = img.max(-1) - img.min(-1)
    pale = (L > 175) & ~dmask & ~amask
    near_a = ndimage.binary_dilation(amask, iterations=3)
    m = pale & near_a
    return np.median(img[m], 0).astype(int) if m.sum() > 30 else None, int(m.sum())

def tortuosity(amask):
    """Boundary length / smoothed boundary length of the attacker's territory: >1 = fingers."""
    e = amask ^ ndimage.binary_erosion(amask)
    sm = ndimage.gaussian_filter(amask.astype(np.float32), 12) > 0.5
    es = sm ^ ndimage.binary_erosion(sm)
    return e.sum() / max(es.sum(), 1)

def front_wiggle(amask, dmask, sigma=10):
    """Length of the attacker/defender boundary vs. the same boundary smoothed (sigma px): 1 = straight."""
    fr = amask & ndimage.binary_dilation(dmask, iterations=1)
    s = ndimage.gaussian_filter(amask.astype(np.float32), sigma) > 0.5
    ds = ndimage.gaussian_filter(dmask.astype(np.float32), sigma) > 0.5
    frs = s & ndimage.binary_dilation(ds, iterations=1)
    return fr.sum() / max(frs.sum(), 1), int(fr.sum())
