"""Historical data for the Russian invasion of Ukraine (24 Feb 2022 - Sep 2026).

Front lines are hand-traced through the towns on the line at each date (from ISW / DeepState-style
maps and news reports) and are approximate: small salients, grey zones and infiltrations are not
shown. The main front is a single line from the Russian border north-east of Kharkiv to the Black
Sea; everything between it and Russia (including Crimea, occupied since 2014) is Russian-occupied.

Troop numbers are rounded public estimates (Ukrainian and Western officials, ISW, IISS) of the forces
deployed in the war zone. They are indicative only; the real figures are secret and disputed.
"""
from datetime import date, timedelta

import numpy as np

import geo

D = date.fromisoformat
START = D("2022-02-24")
END = D("2026-09-20")

FACTIONS = {
    "UA": ((66, 128, 210), 0.66),
    "RU": ((178, 48, 40), 0.68),
    "OCC": ((212, 92, 104), 0.64),
    "BY": ((160, 78, 70), 0.42),
}
LEGEND = [("UA", "Ukraine", None), ("RU", "Russia", None), ("OCC", "Russian-occupied Ukraine", None),
          ("BY", "Belarus (Russian ally)", None)]

ALLIANCES = {
    "UKR": [("2022-02-24", "UA")],
    "RUS": [("2022-02-24", "RU")],
    "BLR": [("2022-02-24", "BY")],
}


def B(a, b, f, t):
    return ("B", a, b, f, t)


# ----------------------------------------------------------------------------- main front pieces
NE = (35.9, 50.33)  # northern end of the main front, on the Russian border north-east of Kharkiv
K = (38.2, 49.0)    # joint between the Kharkiv/Luhansk sector and the Donbas sector (near Kreminna)

# the pre-war contact line (2015-2022) and the northern edge of Crimea
PRE_DONBAS = [(39.5, 48.62), (39.25, 48.62), (38.95, 48.72), (38.7, 48.72), (38.5, 48.68), (38.37, 48.6),
              (38.25, 48.47), (38.1, 48.37), (37.95, 48.3), (37.8, 48.18), (37.72, 48.08), (37.62, 48.0),
              (37.5, 47.95), (37.45, 47.85), (37.55, 47.72), (37.7, 47.55), (37.8, 47.35), (37.88, 47.2),
              (37.92, 47.08)]
CRIMEA_NORTH = [(37.4, 46.7), (36.2, 46.2), (35.3, 45.95), (34.8, 46.05), (34.5, 46.02), (34.1, 46.07),
                (33.75, 46.15), (33.55, 46.12), (33.2, 46.0), (32.6, 45.95)]
PRE_WAR = [B("UKR", "RUS", NE, (39.75, 48.72))] + PRE_DONBAS + CRIMEA_NORTH

# Kharkiv / northern Luhansk sector: NE -> K
N = {
    "2022-02-26": [NE, (36.2, 50.12), (36.5, 50.05), (36.9, 50.0), (37.3, 49.9), (37.7, 49.7), (38.0, 49.45),
                   (38.25, 49.25), (38.35, 49.1), K],
    "2022-03-25": [NE, (36.15, 50.1), (36.4, 50.04), (36.6, 49.95), (36.72, 49.75), (36.85, 49.5),
                   (37.05, 49.33), (37.25, 49.22), (37.5, 49.12), (37.9, 49.1), (38.15, 49.08), K],
    "2022-05-25": [NE, (36.35, 50.25), (36.6, 50.15), (36.75, 49.92), (36.88, 49.62), (36.85, 49.45),
                   (37.0, 49.27), (37.2, 49.12), (37.5, 49.02), (37.75, 48.96), (38.0, 48.93), K],
    "2022-09-13": [B("UKR", "RUS", NE, (37.55, 50.38)), (37.62, 50.1), (37.62, 49.85), (37.6, 49.7),
                   (37.68, 49.5), (37.72, 49.3), (37.78, 49.12), (37.72, 49.02), (37.85, 48.93), (38.02, 48.92), K],
    "2022-10-06": [B("UKR", "RUS", NE, (37.95, 49.98)), (38.05, 49.72), (38.02, 49.45), (38.05, 49.2),
                   (38.12, 49.05), K],
    "2024-05-20": [NE, (36.1, 50.32), (36.3, 50.25), (36.45, 50.2), (36.6, 50.27), (36.85, 50.3),
                   (36.97, 50.27), (37.1, 50.33), (37.4, 50.4), (37.6, 50.3), (37.75, 50.0), (37.85, 49.8),
                   (37.92, 49.55), (38.0, 49.35), (38.05, 49.2), (38.12, 49.05), K],
    "2025-01-15": [NE, (36.1, 50.32), (36.3, 50.25), (36.45, 50.2), (36.6, 50.27), (36.85, 50.3),
                   (36.97, 50.27), (37.1, 50.33), (37.4, 50.37), (37.55, 50.1), (37.6, 49.9), (37.68, 49.78),
                   (37.7, 49.6), (37.75, 49.45), (37.85, 49.25), (37.95, 49.1), (38.1, 49.02), K],
    "2025-11-20": [NE, (36.1, 50.3), (36.3, 50.22), (36.45, 50.18), (36.6, 50.2), (36.85, 50.22),
                   (37.0, 50.2), (37.2, 50.25), (37.45, 50.05), (37.55, 49.8), (37.58, 49.7), (37.65, 49.55),
                   (37.7, 49.35), (37.72, 49.15), (37.8, 49.02), (37.95, 48.98), (38.1, 48.97), K],
    "2026-02-25": [NE, (36.1, 50.3), (36.3, 50.22), (36.45, 50.18), (36.6, 50.2), (36.85, 50.22),
                   (37.0, 50.2), (37.2, 50.25), (37.45, 50.05), (37.6, 49.85), (37.68, 49.72), (37.7, 49.55),
                   (37.72, 49.35), (37.74, 49.15), (37.8, 49.03), (37.95, 48.98), (38.1, 48.97), K],
    "2026-09-12": [NE, (36.1, 50.3), (36.3, 50.22), (36.45, 50.18), (36.6, 50.2), (36.85, 50.22),
                   (37.0, 50.2), (37.2, 50.25), (37.45, 50.05), (37.6, 49.85), (37.68, 49.72), (37.72, 49.55),
                   (37.8, 49.35), (37.92, 49.2), (38.0, 49.1), (38.1, 49.02), K],
}

# Donbas north sector: K -> junction near Horlivka / Toretsk (its end point moves west over time)
D1 = {
    "2022-02-26": [K, (38.4, 49.02), (38.55, 48.95), (38.6, 48.8), (38.45, 48.7), (38.37, 48.62), (38.25, 48.47),
                   (38.1, 48.37), (37.95, 48.33)],
    "2022-05-25": [K, (38.4, 48.98), (38.5, 48.92), (38.42, 48.82), (38.3, 48.72), (38.2, 48.62), (38.12, 48.48),
                   (38.0, 48.4), (37.95, 48.33)],
    "2022-07-04": [K, (38.18, 48.9), (38.15, 48.8), (38.15, 48.7), (38.1, 48.6), (38.05, 48.5), (38.0, 48.4),
                   (37.95, 48.33)],
    "2022-10-06": [K, (38.12, 48.93), (38.08, 48.85), (38.08, 48.72), (38.06, 48.6), (38.03, 48.5), (37.98, 48.4),
                   (37.95, 48.33)],
    "2023-01-16": [K, (38.12, 48.93), (38.08, 48.85), (38.03, 48.7), (38.04, 48.6), (38.02, 48.5), (37.98, 48.4),
                   (37.95, 48.33)],
    "2023-05-21": [K, (38.12, 48.93), (38.08, 48.85), (38.05, 48.73), (37.98, 48.63), (37.93, 48.58),
                   (37.93, 48.5), (37.95, 48.4), (37.95, 48.33)],
    "2024-07-15": [K, (38.12, 48.93), (38.07, 48.84), (38.02, 48.72), (37.93, 48.62), (37.87, 48.59),
                   (37.88, 48.5), (37.88, 48.4), (37.9, 48.35)],
    "2025-02-15": [K, (38.12, 48.93), (38.06, 48.84), (38.01, 48.72), (37.92, 48.62), (37.85, 48.58),
                   (37.82, 48.5), (37.8, 48.42), (37.78, 48.36)],
    "2025-07-20": [K, (38.12, 48.93), (38.07, 48.84), (38.0, 48.72), (37.9, 48.62), (37.82, 48.57),
                   (37.78, 48.5), (37.75, 48.42), (37.7, 48.35)],
    "2025-12-24": [K, (38.05, 48.95), (37.95, 48.87), (37.92, 48.78), (37.88, 48.68), (37.82, 48.6),
                   (37.74, 48.52), (37.7, 48.45), (37.62, 48.38)],
    "2026-07-04": [K, (38.05, 48.95), (37.92, 48.87), (37.85, 48.78), (37.8, 48.68), (37.72, 48.6),
                   (37.64, 48.55), (37.58, 48.47), (37.52, 48.4)],
}

# Donbas south sector: junction -> Velyka Novosilka / Huliaipole area
D2 = {
    "2022-02-26": [(37.95, 48.33), (37.8, 48.18), (37.73, 48.08), (37.6, 48.0), (37.5, 47.93), (37.35, 47.83),
                   (37.2, 47.72), (36.95, 47.68), (36.75, 47.7)],
    "2023-12-25": [(37.95, 48.33), (37.8, 48.18), (37.72, 48.1), (37.6, 48.0), (37.45, 47.95), (37.35, 47.83),
                   (37.2, 47.72), (36.95, 47.7), (36.75, 47.7)],
    "2024-02-17": [(37.95, 48.33), (37.8, 48.2), (37.68, 48.15), (37.6, 48.03), (37.42, 47.97), (37.35, 47.83),
                   (37.2, 47.72), (36.95, 47.7), (36.75, 47.7)],
    "2024-05-10": [(37.95, 48.33), (37.75, 48.25), (37.55, 48.27), (37.45, 48.25), (37.5, 48.12), (37.42, 48.0),
                   (37.35, 47.85), (37.2, 47.72), (36.95, 47.7), (36.75, 47.7)],
    "2024-07-15": [(37.9, 48.35), (37.75, 48.3), (37.55, 48.3), (37.42, 48.28), (37.42, 48.12), (37.38, 48.0),
                   (37.3, 47.85), (37.2, 47.74), (36.95, 47.7), (36.75, 47.7)],
    "2024-10-15": [(37.9, 48.35), (37.7, 48.35), (37.45, 48.3), (37.3, 48.25), (37.25, 48.1), (37.3, 47.98),
                   (37.2, 47.85), (37.1, 47.72), (36.9, 47.7), (36.75, 47.7)],
    "2025-02-15": [(37.78, 48.36), (37.6, 48.35), (37.35, 48.3), (37.22, 48.26), (37.12, 48.2), (37.0, 48.08),
                   (36.95, 47.95), (36.85, 47.84), (36.75, 47.72)],
    "2025-07-20": [(37.7, 48.35), (37.5, 48.35), (37.3, 48.32), (37.18, 48.26), (37.05, 48.2), (36.85, 48.12),
                   (36.65, 48.05), (36.55, 47.92), (36.6, 47.8), (36.7, 47.72)],
    "2025-08-12": [(37.7, 48.35), (37.5, 48.38), (37.38, 48.48), (37.28, 48.47), (37.25, 48.35), (37.12, 48.28),
                   (36.98, 48.2), (36.8, 48.1), (36.62, 48.03), (36.55, 47.9), (36.6, 47.8), (36.7, 47.72)],
    "2025-09-05": [(37.68, 48.36), (37.5, 48.37), (37.33, 48.36), (37.2, 48.3), (37.1, 48.25), (36.95, 48.18),
                   (36.78, 48.1), (36.6, 48.02), (36.52, 47.9), (36.55, 47.78), (36.65, 47.72)],
    "2025-12-24": [(37.62, 48.38), (37.45, 48.4), (37.3, 48.4), (37.15, 48.35), (37.05, 48.3), (36.95, 48.2),
                   (36.78, 48.12), (36.58, 48.04), (36.45, 47.94), (36.4, 47.82), (36.45, 47.72)],
    "2026-02-25": [(37.62, 48.38), (37.45, 48.4), (37.3, 48.4), (37.15, 48.35), (37.05, 48.3), (36.95, 48.2),
                   (36.83, 48.1), (36.7, 48.02), (36.62, 47.9), (36.58, 47.8), (36.52, 47.72)],
    "2026-07-04": [(37.52, 48.4), (37.4, 48.42), (37.28, 48.4), (37.15, 48.35), (37.05, 48.3), (36.95, 48.2),
                   (36.85, 48.1), (36.72, 48.02), (36.64, 47.9), (36.6, 47.8), (36.52, 47.72)],
    "2026-08-12": [(37.52, 48.4), (37.4, 48.42), (37.28, 48.4), (37.15, 48.35), (37.05, 48.28), (36.98, 48.15),
                   (36.9, 48.05), (36.8, 47.95), (36.72, 47.85), (36.65, 47.76), (36.55, 47.7)],
}

# the Dnipro below Zaporizhzhia to the delta (the front after November 2022)
DNIPRO = [(34.25, 47.55), (34.0, 47.4), (33.75, 47.12), (33.5, 46.92), (33.36, 46.78), (33.1, 46.72),
          (32.8, 46.66), (32.62, 46.6), (32.35, 46.55), (32.15, 46.5)]
KINBURN = [(31.9, 46.52), (31.5, 46.45), (31.2, 46.3)]
RESERVOIR = [(35.1, 47.53), (34.8, 47.53), (34.55, 47.56), (34.25, 47.55)]

# Zaporizhzhia / Kherson sector: from the Donbas sector to the sea
S = {
    "2022-02-26": [(36.75, 47.7), (36.6, 47.3), (36.2, 47.15), (35.6, 47.1), (35.2, 47.15), (34.8, 47.22),
                   (34.4, 47.1), (33.9, 46.95), (33.4, 46.8), (32.9, 46.72), (32.6, 46.6), (32.3, 46.5),
                   (31.9, 46.42), (31.2, 46.3)],
    "2022-03-05": [(36.75, 47.7), (36.3, 47.5), (35.9, 47.45), (35.6, 47.4), (35.3, 47.42)] + RESERVOIR +
                  [(33.95, 47.45), (33.7, 47.4), (33.45, 47.3), (33.2, 47.18), (32.9, 47.1), (32.6, 46.95),
                   (32.3, 46.85), (32.1, 46.7), (31.95, 46.56)] + KINBURN,
    "2022-09-05": [(36.75, 47.7), (36.3, 47.55), (35.9, 47.5), (35.65, 47.45), (35.3, 47.47)] + RESERVOIR +
                  [(33.95, 47.42), (33.65, 47.35), (33.4, 47.2), (33.15, 47.08), (32.85, 46.97), (32.55, 46.86),
                   (32.35, 46.75), (32.15, 46.62), (31.95, 46.55)] + KINBURN,
    "2022-10-06": [(36.75, 47.7), (36.3, 47.55), (35.9, 47.5), (35.65, 47.45), (35.3, 47.47)] + RESERVOIR +
                  [(34.0, 47.42), (33.75, 47.1), (33.45, 47.0), (33.1, 46.9), (32.8, 46.8), (32.5, 46.72),
                   (32.3, 46.62), (32.15, 46.55), (31.95, 46.55)] + KINBURN,
    "2022-11-12": [(36.75, 47.7), (36.3, 47.55), (35.9, 47.5), (35.65, 47.45), (35.3, 47.47)] + RESERVOIR[:-1] +
                  DNIPRO + KINBURN,
    "2023-09-15": [(36.75, 47.7), (36.68, 47.62), (36.4, 47.55), (36.0, 47.5), (35.87, 47.42), (35.72, 47.46),
                   (35.4, 47.47)] + RESERVOIR[:-1] + DNIPRO + KINBURN,
    "2025-03-15": [(36.75, 47.72), (36.5, 47.62), (36.2, 47.55), (35.95, 47.5), (35.75, 47.47), (35.4, 47.48)] +
                  RESERVOIR[:-1] + DNIPRO + KINBURN,
    "2025-12-24": [(36.45, 47.72), (36.3, 47.7), (36.15, 47.62), (35.95, 47.56), (35.8, 47.5), (35.6, 47.52),
                   (35.4, 47.56), (35.2, 47.6)] + RESERVOIR[1:-1] + DNIPRO + KINBURN,
    "2026-01-25": [(36.45, 47.72), (36.2, 47.72), (36.05, 47.64), (35.9, 47.58), (35.78, 47.52), (35.6, 47.54),
                   (35.4, 47.58), (35.2, 47.62)] + RESERVOIR[1:-1] + DNIPRO + KINBURN,
    "2026-08-12": [(36.55, 47.7), (36.3, 47.66), (36.1, 47.6), (35.92, 47.55), (35.78, 47.5), (35.6, 47.53),
                   (35.4, 47.57), (35.2, 47.62)] + RESERVOIR[1:-1] + DNIPRO + KINBURN,
}

# dates at which the whole main front is assembled; every sector is interpolated to each of them
MAIN_DATES = ["2022-02-26", "2022-03-05", "2022-03-25", "2022-05-25", "2022-07-04", "2022-09-05", "2022-09-13",
              "2022-10-06", "2022-11-12", "2023-01-16", "2023-05-21", "2023-09-15", "2023-12-25", "2024-02-17",
              "2024-05-10", "2024-05-20", "2024-07-15", "2024-10-15", "2025-01-15", "2025-02-15", "2025-03-15",
              "2025-07-20", "2025-08-12", "2025-09-05", "2025-11-20", "2025-12-24", "2026-01-25", "2026-02-25",
              "2026-07-04", "2026-08-12", "2026-09-12", "2026-09-20"]

# ----------------------------------------------------------------------------- the northern front of 2022
BLR_BORDER = B("UKR", "BLR", (29.25, 51.38), (31.76, 52.10))
RUS_BORDER_N = B("UKR", "RUS", (31.76, 52.10), NE)
NORTH_MAX = [(29.25, 51.38), (29.55, 51.1), (29.72, 50.85), (29.78, 50.6), (29.95, 50.5), (30.15, 50.52),
             (30.27, 50.53), (30.38, 50.62), (30.42, 50.8), (30.5, 51.0), (30.7, 50.95), (30.85, 50.72),
             (30.97, 50.56), (31.3, 50.62), (31.7, 50.8), (32.0, 50.93), (32.5, 50.95), (33.0, 51.0),
             (33.5, 50.88), (34.1, 50.68), (34.6, 50.45), (35.0, 50.4), (35.4, 50.38), NE]

FRONTS = [
    dict(
        name="Northern front",
        A=dict(occ="UA", victims=[], rear=[(35.0, 49.2), (30.0, 49.0), (27.5, 50.5), (28.0, 51.5)]),
        B=dict(occ="OCC", victims=["UKR"], rear=[(36.6, 50.6), (37.5, 52.5), (31.0, 53.8), (28.8, 52.4)],
               until="2022-04-06"),
        label_off=20,
        keys=[
            ("2022-02-24", [BLR_BORDER, RUS_BORDER_N]),
            ("2022-02-26", [(29.25, 51.38), (29.6, 51.1), (29.95, 50.9), (30.2, 50.62), (30.38, 50.66),
                            (30.48, 50.95), (30.65, 51.1), (30.95, 51.18), (31.3, 51.33), (31.8, 51.3),
                            (32.3, 51.25), (32.9, 51.2), (33.5, 51.1), (34.2, 50.9), (34.7, 50.6), (35.1, 50.45),
                            (35.5, 50.36), NE]),
            ("2022-03-12", NORTH_MAX),
            ("2022-03-26", NORTH_MAX),
            ("2022-04-01", [(29.25, 51.38), (29.5, 51.2), (29.9, 51.0), (30.3, 50.95), (30.6, 51.05), (30.95, 51.0),
                            (31.3, 51.2), (31.8, 51.35), (32.4, 51.4), (33.1, 51.4), (33.7, 51.25), (34.3, 51.0),
                            (34.9, 50.75), (35.3, 50.5), NE]),
            ("2022-04-06", [BLR_BORDER, RUS_BORDER_N]),
        ],
        labels=[
            dict(side="B", hint=[("2022-02-24", (31.0, 51.2))],
                 army=[("2022-02-24", 40_000), ("2022-03-10", 60_000), ("2022-03-29", 55_000), ("2022-04-06", 0)]),
            dict(side="A", hint=[("2022-02-24", (31.4, 50.5))],
                 army=[("2022-02-24", 45_000), ("2022-03-10", 70_000), ("2022-04-01", 70_000), ("2022-04-06", 0)]),
        ],
    ),
    dict(
        name="Main front",
        A=dict(occ="UA", victims=[], rear=[(32.0, 44.5), (29.0, 46.0), (28.0, 49.0), (30.0, 51.0), (34.5, 50.9)]),
        B=dict(occ="OCC", victims=["UKR"],
               rear=[(32.4, 44.2), (37.5, 44.0), (41.0, 46.0), (43.0, 49.0), (41.0, 52.0), (37.5, 51.5), (36.4, 50.8)]),
        label_off=34,
        keys=None,  # built below from the sectors
        labels=[
            dict(side="B", hint=[("2022-02-24", (38.4, 48.4)), ("2022-10-06", (38.3, 48.9)),
                                 ("2024-02-17", (37.9, 48.25)), ("2025-07-20", (37.5, 48.2)),
                                 ("2026-09-20", (37.5, 48.3))],
                 army=[("2022-02-24", 105_000), ("2022-03-25", 130_000), ("2022-04-07", 190_000),
                       ("2022-06-01", 200_000), ("2022-09-01", 190_000), ("2022-11-01", 250_000),
                       ("2023-01-01", 300_000), ("2023-06-01", 410_000), ("2024-01-01", 470_000),
                       ("2024-06-01", 520_000), ("2024-08-20", 490_000), ("2024-11-01", 470_000),
                       ("2025-01-01", 545_000), ("2025-04-26", 600_000), ("2025-07-01", 695_000),
                       ("2026-01-01", 710_000), ("2026-06-30", 721_000), ("2026-09-20", 730_000)]),
            dict(side="A", hint=[("2022-02-24", (37.9, 48.6)), ("2022-10-06", (37.7, 49.2)),
                                 ("2024-02-17", (37.5, 48.4)), ("2025-07-20", (37.1, 48.5)),
                                 ("2026-09-20", (37.2, 48.6))],
                 army=[("2022-02-24", 150_000), ("2022-03-25", 190_000), ("2022-04-07", 260_000),
                       ("2022-06-01", 300_000), ("2022-09-01", 330_000), ("2023-01-01", 350_000),
                       ("2023-06-01", 380_000), ("2024-01-01", 400_000), ("2024-08-20", 390_000),
                       ("2025-01-01", 410_000), ("2025-04-26", 420_000), ("2026-01-01", 430_000),
                       ("2026-09-20", 440_000)]),
        ],
    ),
    dict(
        name="Kursk",
        A=dict(occ="UA", victims=["RUS"], rear=[(34.8, 50.6), (34.5, 51.0)], until="2025-04-26"),
        B=dict(occ="RU", victims=[], rear=[(36.2, 51.2), (36.0, 51.9), (35.0, 51.8)]),
        label_off=18,
        keys=[
            ("2024-08-05", [(35.08, 51.21), (35.16, 51.08), (35.24, 50.95)]),
            ("2024-08-07", [(35.08, 51.21), (35.15, 51.28), (35.3, 51.25), (35.33, 51.1), (35.24, 50.95)]),
            ("2024-08-16", [(35.08, 51.21), (35.05, 51.35), (35.2, 51.5), (35.4, 51.55), (35.55, 51.45),
                            (35.6, 51.3), (35.5, 51.1), (35.24, 50.95)]),
            ("2024-10-01", [(35.08, 51.21), (35.08, 51.33), (35.2, 51.45), (35.4, 51.5), (35.53, 51.42),
                            (35.57, 51.28), (35.47, 51.1), (35.24, 50.95)]),
            ("2024-12-31", [(35.08, 51.21), (35.1, 51.32), (35.25, 51.42), (35.45, 51.38), (35.5, 51.25),
                            (35.4, 51.1), (35.24, 50.95)]),
            ("2025-03-13", [(35.08, 51.21), (35.15, 51.23), (35.28, 51.18), (35.3, 51.05), (35.24, 50.95)]),
            ("2025-04-26", [(35.08, 51.21), (35.16, 51.08), (35.24, 50.95)]),
        ],
        labels=[
            dict(side="A", hint=[("2024-08-06", (35.3, 51.3))],
                 army=[("2024-08-06", 10_000), ("2024-08-20", 12_000), ("2025-01-01", 10_000),
                       ("2025-03-13", 5_000), ("2025-04-26", 0)]),
            dict(side="B", hint=[("2024-08-06", (35.75, 51.45))],
                 army=[("2024-08-06", 5_000), ("2024-08-20", 30_000), ("2024-11-01", 50_000),
                       ("2025-01-15", 60_000), ("2025-03-13", 60_000), ("2025-04-26", 0)]),
        ],
    ),
]

# Ukrainian-held cities surrounded or besieged behind the front (painted back in Ukrainian colours)
STATIC_ZONES = [
    dict(name="Mariupol", occ="UA", victims=["UKR"], start="2022-03-01", end="2022-04-21",
         poly=[(37.42, 47.05), (37.45, 47.16), (37.6, 47.17), (37.68, 47.1), (37.62, 47.03)]),
    dict(name="Azovstal", occ="UA", victims=["UKR"], start="2022-04-21", end="2022-05-20",
         poly=[(37.6, 47.08), (37.6, 47.11), (37.65, 47.11), (37.66, 47.08)]),
    dict(name="Chernihiv", occ="UA", victims=["UKR"], start="2022-02-26", end="2022-04-02",
         poly=[(31.1, 51.42), (31.15, 51.6), (31.45, 51.6), (31.5, 51.43), (31.3, 51.38)]),
    dict(name="Sumy", occ="UA", victims=["UKR"], start="2022-02-26", end="2022-04-05",
         poly=[(34.62, 50.85), (34.65, 50.98), (34.92, 50.98), (34.95, 50.85), (34.8, 50.8)]),
    dict(name="Nizhyn and Okhtyrka", occ="UA", victims=["UKR"], start="2022-02-26", end="2022-04-05",
         poly=[(31.75, 50.98), (31.8, 51.12), (32.05, 51.12), (32.1, 50.98)]),
]

# Siege and battle markers: (label, lon, lat, start, end)
MARKERS = [
    ("Siege of Mariupol", 37.55, 47.1, "2022-03-01", "2022-05-20"),
    ("Battle of Kyiv", 30.52, 50.45, "2022-02-25", "2022-04-02"),
    ("Siege of Chernihiv", 31.29, 51.5, "2022-02-26", "2022-04-01"),
    ("Sievierodonetsk", 38.49, 48.95, "2022-05-13", "2022-06-25"),
    ("Bakhmut", 38.0, 48.59, "2022-08-01", "2023-05-21"),
    ("Avdiivka", 37.75, 48.14, "2023-10-10", "2024-02-17"),
    ("Vuhledar", 37.25, 47.78, "2024-09-01", "2024-10-01"),
    ("Pokrovsk", 37.18, 48.28, "2025-07-15", "2025-12-31"),
    ("Kupiansk", 37.61, 49.71, "2025-11-01", "2026-02-25"),
    ("Kostiantynivka", 37.71, 48.53, "2025-12-01", "2026-07-04"),
    ("Kramatorsk", 37.56, 48.72, "2026-07-04", "2026-09-20"),
]

EVENTS = [
    ("2022-02-24", "Russia launches a full-scale invasion of Ukraine"),
    ("2022-02-25", "Russian forces reach the outskirts of Kyiv"),
    ("2022-02-26", "Zelenskyy refuses to leave Kyiv - \"I need ammunition, not a ride\""),
    ("2022-03-01", "Kherson and Melitopol fall - Mariupol is surrounded"),
    ("2022-03-04", "Russia seizes the Zaporizhzhia nuclear power plant"),
    ("2022-03-16", "A Russian airstrike destroys the Mariupol Drama Theatre"),
    ("2022-03-29", "Russia announces its withdrawal from Kyiv and Chernihiv"),
    ("2022-04-02", "Ukraine liberates the Kyiv region - the atrocities in Bucha are revealed"),
    ("2022-04-14", "The cruiser Moskva, flagship of the Black Sea Fleet, is sunk"),
    ("2022-05-20", "The last defenders of Azovstal surrender - Mariupol falls"),
    ("2022-06-25", "Sievierodonetsk falls"),
    ("2022-07-03", "Lysychansk falls - Russia controls all of Luhansk Oblast"),
    ("2022-09-06", "Ukraine's lightning Kharkiv counteroffensive begins"),
    ("2022-09-10", "Ukraine liberates Balakliia, Kupiansk and Izium"),
    ("2022-09-21", "Putin announces a partial mobilisation"),
    ("2022-09-30", "Russia declares the annexation of four Ukrainian regions"),
    ("2022-10-01", "Ukraine liberates Lyman"),
    ("2022-10-08", "The Crimean Bridge is hit by an explosion"),
    ("2022-11-11", "Ukraine liberates Kherson - Russia retreats across the Dnipro"),
    ("2023-01-16", "Wagner captures Soledar"),
    ("2023-05-21", "After ten months of fighting, Bakhmut falls"),
    ("2023-06-06", "The Kakhovka dam is destroyed"),
    ("2023-06-08", "Ukraine's 2023 counteroffensive begins in Zaporizhzhia"),
    ("2023-06-24", "Prigozhin's Wagner mutiny marches towards Moscow"),
    ("2023-08-28", "Ukraine liberates Robotyne"),
    ("2023-11-15", "Ukraine holds a bridgehead at Krynky across the Dnipro"),
    ("2024-02-17", "Ukraine withdraws from Avdiivka"),
    ("2024-04-24", "The US approves a $61 billion aid package for Ukraine"),
    ("2024-05-10", "Russia opens a new offensive north of Kharkiv"),
    ("2024-08-06", "Ukraine invades Russia's Kursk Oblast"),
    ("2024-08-15", "Ukraine controls around 1,000 km2 of Kursk Oblast"),
    ("2024-10-01", "Vuhledar falls"),
    ("2024-11-04", "North Korean troops join the fighting in Kursk"),
    ("2024-11-19", "Ukraine fires US ATACMS missiles into Russia"),
    ("2025-01-06", "Russia takes Kurakhove"),
    ("2025-02-28", "Zelenskyy and Trump clash in the Oval Office"),
    ("2025-03-13", "Russia retakes Sudzha - the Kursk salient collapses"),
    ("2025-04-26", "Russia claims the last Ukrainian positions in Kursk"),
    ("2025-06-01", "Operation Spiderweb - Ukrainian drones strike Russian bombers across Russia"),
    ("2025-06-08", "Russian forces cross into Dnipropetrovsk Oblast"),
    ("2025-08-12", "A Russian breakthrough near Dobropillia is cut off by Ukrainian counterattacks"),
    ("2025-08-15", "Trump and Putin meet in Alaska"),
    ("2025-11-15", "Russian troops break into Pokrovsk"),
    ("2025-12-01", "Russia claims Pokrovsk and Kupiansk"),
    ("2025-12-24", "Siversk falls - Russian troops enter Huliaipole"),
    ("2026-01-25", "Huliaipole falls - Myrnohrad is almost entirely lost"),
    ("2026-01-29", "Ukraine launches a counteroffensive in the south-east"),
    ("2026-02-25", "Ukraine clears Kupiansk after a months-long battle"),
    ("2026-03-15", "Ukraine liberates 26 villages on the Oleksandrivka axis"),
    ("2026-06-06", "The main battle moves to the Kramatorsk fortress belt"),
    ("2026-07-04", "Russia captures Kostiantynivka"),
    ("2026-08-12", "Ukraine: 627 km2 liberated on the Oleksandrivka and Huliaipole axes"),
    ("2026-09-11", "Ukraine cuts off the Russian salient north of Lyman"),
]

# speeches: filled in with real audio files by audio.real_speeches(); the text is shown nowhere (background)
SPEECHES = [   # original recordings (build/real/speeches/<file>.wav); the text is only used for the AI-voice fallback
    dict(date="2022-02-24", speaker="Vladimir Putin", role="Address announcing the invasion", voice="bm_daniel",
         text="I have made the decision to conduct a special military operation.", file="putin_2022_02_24"),
    dict(date="2022-02-25", speaker="Volodymyr Zelenskyy", role="Address to the citizens of Russia", voice="bm_george",
         text="If they try to take away our country, our freedom, our lives, we will defend ourselves. "
              "When you attack us, you will see our faces, not our backs.", file="zelenskyy_2022_02_24"),
    dict(date="2022-12-21", speaker="Volodymyr Zelenskyy", role="Address to the US Congress", voice="bm_george",
         text="Against all odds and doom-and-gloom scenarios, Ukraine didn't fall. Ukraine is alive and kicking.",
         file="zelenskyy_2022_12_21"),
    dict(date="2023-02-21", speaker="Joe Biden", role="Speech in Warsaw", voice="am_michael",
         text="One year ago, the world was bracing for the fall of Kyiv. Kyiv stands strong. Kyiv stands proud. "
              "It stands tall. And most important, it stands free.", file="biden_2023_02_21"),
]

TOTALS = [
    ("Ukrainian territory occupied (Sep 2026)", "about 19%"),
    ("Refugees abroad", "over 6 million"),
    ("Civilians killed (UN verified)", "over 14,000"),
    ("Military casualties", "hundreds of thousands on both sides"),
]


# ----------------------------------------------------------------------------- helpers (same as the WW1 project)
def day_index(d):
    return (d - START).days


def as_day(s):
    return day_index(D(s))


def date_at(day_float):
    return START + timedelta(days=int(np.floor(day_float)))


def resolve_line(items):
    pts = []
    for it in items:
        if isinstance(it, tuple) and len(it) == 5 and it[0] == "B":
            pts.extend(geo.border_between(it[1], it[2], np.array(it[3]), np.array(it[4])))
        else:
            pts.append(tuple(map(float, it)))
    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) > 1e-6 or abs(p[1] - out[-1][1]) > 1e-6:
            out.append(p)
    return np.array(out)


def resample(line, n):
    seg = np.sqrt(((line[1:] - line[:-1]) ** 2).sum(1))
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, line[:, 0]), np.interp(t, s, line[:, 1])], 1)


def interp_series(series, t, ease=True):
    if t <= series[0][0]:
        return series[0][1]
    for (t0, v0), (t1, v1) in zip(series, series[1:]):
        if t <= t1:
            u = (t - t0) / max(t1 - t0, 1e-9)
            if ease:
                u = u * u * (3 - 2 * u)
            return v0 + (v1 - v0) * u
    return series[-1][1]


def _sector_at(sector, d, n=60):
    """A sector's line at date d: linear interpolation between its own keyframes (resampled)."""
    keys = sorted((as_day(k), resample(resolve_line(v), n)) for k, v in sector.items())
    x = as_day(d)
    if x <= keys[0][0]:
        return keys[0][1]
    for (d0, l0), (d1, l1) in zip(keys, keys[1:]):
        if x <= d1:
            u = (x - d0) / max(d1 - d0, 1e-9)
            return l0 + (l1 - l0) * u
    return keys[-1][1]


def _build_main():
    keys = [("2022-02-24", PRE_WAR)]
    for d in MAIN_DATES:
        line = []
        for sec in (N, D1, D2, S):
            part = [tuple(p) for p in _sector_at(sec, d)]
            if line and np.hypot(line[-1][0] - part[0][0], line[-1][1] - part[0][1]) < 1e-6:
                part = part[1:]
            line += part
        keys.append((d, line))
    return keys


FRONTS[1]["keys"] = _build_main()
