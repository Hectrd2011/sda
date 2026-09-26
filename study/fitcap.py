import numpy as np, sys
from scipy.optimize import least_squares
def fit(F, OLD, NEW, fps=10, tol=30):
    d = np.sqrt(((F - OLD) ** 2).sum(-1)) < tol
    a = np.sqrt(((F - NEW) ** 2).sum(-1)) < tol
    ys, xs = np.nonzero(d[0] & a[-1])
    tr = []
    for y, x in zip(ys[::2], xs[::2]):
        nr = int(np.argmax(~d[:, y, x]))
        if nr >= 1 and nr + 16 < len(F):
            tr.append(F[nr - 1:nr + 16, y, x])
    tr = np.median(np.array(tr), 0); T = len(tr)
    def model(p):
        C = p[:3]; s = p[3:3 + T]; c = p[3 + T:]
        return (OLD[None] * (1 - s[:, None]) + NEW[None] * s[:, None]) * (1 - c[:, None]) + C[None] * c[:, None]
    p0 = np.concatenate([[235, 225, 215], np.linspace(0, 1, T), np.zeros(T)])
    lo = np.concatenate([[150] * 3, np.zeros(T), np.zeros(T)]); hi = np.concatenate([[255] * 3, np.ones(T), np.ones(T)])
    sol = least_squares(lambda p: (model(p) - tr).ravel(), p0, bounds=(lo, hi))
    return sol.x[:3], sol.x[3:3 + T], sol.x[3 + T:], len(ys), tr
if __name__ == "__main__":
    F = np.load(sys.argv[1]).astype(np.float32)
    OLD = np.array([float(v) for v in sys.argv[2].split(",")]); NEW = np.array([float(v) for v in sys.argv[3].split(",")])
    C, s, c, n, tr = fit(F, OLD, NEW)
    print("cream", np.round(C).astype(int), "pixels", n)
    for i in range(len(s)):
        print(f"{(i - 1) / 10:+.1f}s  new {s[i]:.2f}  cream {c[i]:.2f}  obs {tr[i].astype(int)}")
