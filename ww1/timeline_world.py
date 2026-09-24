"""Extra data for the world map version: colonies, countries that joined later, colonial campaigns.

Everything in timeline.py (the European and Middle Eastern fronts) is reused; this module adds
what only shows up on a world map.

Colonial campaigns are modelled as "pockets": an ellipse that shrinks over time. For mode
"outside" the occupier holds the victim territory outside the ellipse (the defenders' pocket
shrinks); for mode "inside" the occupier holds the territory inside the ellipse (a raid or revolt).
Keys are (date, centre lon, centre lat, radius lon, radius lat).
"""

ALLIANCES = {
    # British Empire
    **{k: [("1914-08-04", "ENT")] for k in
       ("CAN", "AUS", "NZL", "SAF", "BEA", "SUD", "BWA", "BSO", "RHO", "BAS", "BAM")},
    # French Empire
    **{k: [("1914-08-03", "ENT")] for k in ("FEA", "FIC", "FAM")},
    "BCO": [("1914-08-04", "ENT")],
    "ICO": [("1915-05-23", "ENT")],
    "PCO": [("1916-03-09", "ENT")],
    # German colonies (the campaigns below show them being taken)
    "KAM": [("1914-08-01", "CP")], "TOG": [("1914-08-01", "CP")], "GSW": [("1914-08-01", "CP")],
    "GEA": [("1914-08-01", "CP")],
    "GSA": [("1914-08-01", "CP"), ("1914-08-29", "ENT")],   # Samoa, occupied by New Zealand
    "PNG": [("1914-08-01", "CP"), ("1914-09-17", "ENT")],   # German New Guinea, taken by Australia
    # countries that joined later
    "JAP": [("1914-08-23", "ENT")],
    "USA": [("1917-04-06", "ENT")],
    "CUB": [("1917-04-07", "ENT")], "PAN": [("1917-04-07", "ENT")],
    "SIA": [("1917-07-22", "ENT")],
    "LBR": [("1917-08-04", "ENT")],
    "CHN": [("1917-08-14", "ENT")],
    "BRA": [("1917-10-26", "ENT")],
    "GUA": [("1918-04-23", "ENT")], "NIC": [("1918-05-08", "ENT")], "CRI": [("1918-05-23", "ENT")],
    "HAI": [("1918-07-12", "ENT")], "HON": [("1918-07-19", "ENT")],
}

POCKETS = [
    dict(name="Togoland", occ="ENT", victims=["TOG"], mode="outside",
         keys=[("1914-08-06", 0.9, 8.6, 5.0, 5.0), ("1914-08-12", 0.9, 8.0, 0.9, 1.8),
               ("1914-08-20", 1.0, 7.6, 0.5, 0.8), ("1914-08-26", 1.1, 7.5, 0.0, 0.0)],
         labels=[dict(hint=[("1914-08-06", (-1.2, 8.5))],
                      army=[("1914-08-06", 1_800), ("1914-08-26", 1_800), ("1914-08-28", 0)]),
                 dict(hint=[("1914-08-06", (1.0, 9.8)), ("1914-08-26", (1.1, 8.0))],
                      army=[("1914-08-06", 1_500), ("1914-08-26", 0)])]),
    dict(name="Kamerun", occ="ENT", victims=["KAM"], mode="outside",
         keys=[("1914-08-24", 13.0, 6.0, 15.0, 15.0), ("1914-09-27", 13.2, 6.3, 4.5, 5.5),
               ("1915-06-10", 12.8, 5.0, 3.0, 3.5), ("1915-11-01", 12.0, 4.0, 1.6, 1.7),
               ("1916-01-01", 11.2, 3.1, 0.9, 0.9), ("1916-02-18", 10.8, 2.2, 0.0, 0.0)],
         labels=[dict(hint=[("1914-08-24", (8.5, 7.5)), ("1916-02-18", (9.5, 4.5))],
                      army=[("1914-08-24", 7_000), ("1915-06-01", 18_000), ("1916-01-01", 25_000),
                            ("1916-02-18", 25_000), ("1916-02-21", 0)]),
                 dict(hint=[("1914-08-24", (13.0, 6.0)), ("1915-06-10", (12.8, 5.0)),
                            ("1916-01-01", (11.2, 3.2)), ("1916-02-18", (10.8, 2.4))],
                      army=[("1914-08-24", 8_000), ("1915-06-01", 6_500), ("1916-01-01", 5_000),
                            ("1916-02-18", 0)])]),
    dict(name="German South-West Africa", occ="ENT", victims=["GSW"], mode="outside",
         keys=[("1914-09-14", 18.0, -22.0, 15.0, 15.0), ("1914-12-01", 17.8, -21.5, 6.0, 6.2),
               ("1915-03-01", 17.5, -21.0, 4.8, 4.2), ("1915-05-12", 17.4, -19.9, 3.0, 2.2),
               ("1915-07-09", 17.3, -19.3, 0.0, 0.0)],
         labels=[dict(hint=[("1914-09-14", (20.0, -28.5)), ("1915-07-09", (15.0, -23.0))],
                      army=[("1914-09-14", 8_000), ("1915-01-01", 40_000), ("1915-05-12", 67_000),
                            ("1915-07-09", 67_000), ("1915-07-12", 0)]),
                 dict(hint=[("1914-09-14", (18.0, -21.0)), ("1915-07-09", (17.3, -19.3))],
                      army=[("1914-09-14", 9_000), ("1915-05-12", 5_500), ("1915-07-09", 0)])]),
    dict(name="German East Africa", occ="ENT", victims=["GEA"], mode="outside",
         keys=[("1914-08-01", 35.0, -6.0, 15.0, 15.0), ("1916-03-01", 35.0, -6.3, 8.0, 7.8),
               ("1916-03-12", 35.0, -6.6, 5.6, 5.0), ("1916-07-07", 35.5, -7.2, 4.6, 4.2),
               ("1916-09-19", 37.5, -8.6, 3.0, 2.8), ("1917-06-01", 38.0, -9.6, 2.2, 2.0),
               ("1917-11-25", 37.6, -11.2, 0.7, 0.5), ("1917-11-28", 37.8, -11.6, 0.0, 0.0)],
         labels=[dict(hint=[("1914-08-01", (37.5, 1.5)), ("1916-09-19", (35.0, -5.5)),
                            ("1917-11-25", (36.0, -9.5)), ("1918-07-03", (39.5, -16.0)),
                            ("1918-11-11", (32.5, -8.0))],
                      army=[("1914-08-15", 8_000), ("1914-11-01", 15_000), ("1916-02-01", 45_000),
                            ("1916-09-01", 60_000), ("1917-11-25", 45_000), ("1918-11-11", 40_000)]),
                 dict(hint=[("1914-08-01", (35.0, -6.0)), ("1916-09-19", (37.5, -8.6)),
                            ("1917-11-25", (37.6, -11.4)), ("1918-04-01", (38.2, -13.5)),
                            ("1918-07-03", (37.2, -17.0)), ("1918-09-28", (35.0, -10.8)),
                            ("1918-11-11", (31.3, -10.2))],
                      army=[("1914-08-15", 6_000), ("1915-06-01", 14_000), ("1916-03-01", 15_000),
                            ("1916-12-01", 11_000), ("1917-11-25", 2_000), ("1918-11-11", 1_500)])]),
    # Lettow-Vorbeck's column after it left German East Africa
    dict(name="Lettow-Vorbeck's raid", occ="CP", victims=["PCO", "GEA", "RHO"], mode="inside",
         keys=[("1917-11-24", 37.8, -11.6, 0.0, 0.0), ("1917-11-28", 37.8, -12.0, 1.3, 1.2),
               ("1918-04-01", 38.2, -13.5, 1.3, 1.2), ("1918-07-03", 37.2, -16.8, 1.3, 1.2),
               ("1918-09-01", 36.5, -14.0, 1.3, 1.2), ("1918-09-28", 35.0, -10.8, 1.3, 1.2),
               ("1918-11-11", 31.3, -10.2, 1.3, 1.2)],
         labels=[]),
    # the Arab Revolt against the Ottomans in the Hejaz
    dict(name="Arab Revolt", occ="ENT", victims=["OTT"], mode="inside",
         keys=[("1916-06-09", 39.8, 21.4, 0.0, 0.0), ("1916-07-30", 39.6, 22.2, 2.2, 1.8),
               ("1917-01-24", 38.3, 24.0, 3.2, 3.4), ("1917-07-06", 37.5, 25.5, 4.0, 4.5),
               ("1918-11-11", 37.5, 25.5, 4.0, 4.5)],
         labels=[dict(hint=[("1916-06-10", (41.5, 22.0)), ("1917-07-06", (40.5, 24.5))],
                      army=[("1916-06-10", 10_000), ("1917-07-06", 25_000), ("1918-09-01", 30_000)])]),
]

# Kiautschou / Tsingtao: the German naval base in China, taken by Japan and Britain.
KIAUTSCHOU = [(119.7, 35.7), (120.9, 35.7), (120.9, 36.6), (119.7, 36.6)]
STATIC_ZONES = [
    dict(name="Kiautschou (German)", occ="CP", victims=["CHN"], start="1914-08-01", end="1914-11-07",
         poly=KIAUTSCHOU),
    dict(name="Kiautschou (Japanese)", occ="ENT", victims=["CHN"], start="1914-11-07", end="1918-11-12",
         poly=KIAUTSCHOU),
]

# Numbers drawn at a fixed place (fronts too small to have a line at world scale).
POINT_LABELS = [
    dict(hint=[("1914-09-02", (122.8, 34.8))],
         army=[("1914-09-02", 23_000), ("1914-10-31", 26_000), ("1914-11-07", 26_000), ("1914-11-09", 0)]),
    dict(hint=[("1914-09-02", (118.0, 37.6))],
         army=[("1914-09-02", 4_700), ("1914-11-07", 0)]),
]

MARKERS = [
    ("Tsingtao", 120.3, 36.07, "1914-09-02", "1914-11-07"),
    ("Tanga", 39.1, -5.07, "1914-11-02", "1914-11-05"),
]

EVENTS = [
    ("1914-08-07", "British and French troops invade German Togoland"),
    ("1914-08-23", "Japan declares war on Germany"),
    ("1914-08-27", "German Togoland surrenders"),
    ("1914-08-29", "New Zealand troops occupy German Samoa"),
    ("1914-09-11", "Australian troops land in German New Guinea"),
    ("1914-09-27", "Allied troops capture Douala in Kamerun"),
    ("1914-10-14", "Japan seizes Germany's islands in the Pacific"),
    ("1914-11-01", "German cruisers win the naval Battle of Coronel off Chile"),
    ("1914-11-04", "British defeat at Tanga in German East Africa"),
    ("1914-11-07", "Tsingtao falls to Japanese and British forces"),
    ("1914-12-08", "The German squadron is destroyed off the Falkland Islands"),
    ("1915-05-12", "South African troops capture Windhoek"),
    ("1915-06-10", "The British capture Garua in Kamerun"),
    ("1915-07-09", "German South-West Africa surrenders"),
    ("1916-01-02", "Allied troops capture Yaoundé in Kamerun"),
    ("1916-02-18", "The last German garrison in Kamerun surrenders at Mora"),
    ("1916-03-12", "Smuts' offensive takes the Kilimanjaro region"),
    ("1916-09-04", "British troops capture Dar es Salaam"),
    ("1916-09-19", "Belgian troops capture Tabora"),
    ("1917-07-22", "Siam declares war on Germany"),
    ("1917-08-14", "China declares war on Germany"),
    ("1917-10-26", "Brazil declares war on Germany"),
    ("1917-11-25", "Lettow-Vorbeck crosses into Portuguese Mozambique"),
    ("1918-07-03", "Lettow-Vorbeck's column wins at Nhamacurra in Mozambique"),
]
