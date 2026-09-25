"""Historical data for the Spanish-American War / Philippine-American War video (Apr 1898 - Jul 1902).

Territory is drawn in layers. Every country has a base owner that changes on given dates; on top
of that, zones are painted in list order (later zones cover earlier ones), clipped to their
"victim" countries' land:
  * "poly"    zones morph between keyframe polygons (lon/lat rings),
  * "ellipse" zones grow/shrink/move between keyframe ellipses (lon, lat, radius lon, radius lat).

Army sizes are rounded estimates from standard histories (Trask, Linn, Cosmas and others) of the
forces present in each theatre; they are indicative, not exact.
"""
from datetime import date, timedelta

D = date.fromisoformat
START = D("1898-04-21")
END = D("1902-07-04")

FACTIONS = {  # key: (RGB, alpha, legend name)
    "US": ((66, 110, 212), 0.64, "United States"),
    "ESP": ((196, 152, 44), 0.66, "Kingdom of Spain"),
    "CLA": ((46, 150, 120), 0.62, "Cuban Liberation Army"),
    "FIL": ((196, 70, 58), 0.64, "Philippine revolutionaries"),
    "MORO": ((140, 120, 160), 0.45, "Moro sultanates (neutral)"),
    "CUBA": ((46, 150, 120), 0.50, "Republic of Cuba"),
}

# country -> [(date, owner)]
OWNERS = {
    "USA": [("1898-04-21", "US")],
    "CUB": [("1898-04-21", "ESP"), ("1899-01-01", "US"), ("1902-05-20", "CUBA")],
    "PRI": [("1898-04-21", "ESP"), ("1898-10-18", "US")],
    "PHL": [("1898-04-21", "ESP"), ("1898-12-10", "FIL")],
}

# Spanish-held towns inside rebel territory in eastern Cuba (lon, lat, radius deg, until)
_TOWN_R = 0.16
SPANISH_TOWNS_CUBA = [
    ("Santiago de Cuba", -75.82, 20.03, "1898-07-17"),
    ("Guantanamo", -75.21, 20.14, "1898-07-17"),
    ("Manzanillo", -77.12, 20.34, "1898-12-31"),
    ("Holguin", -76.26, 20.89, "1898-12-31"),
    ("Gibara", -76.13, 21.11, "1898-12-31"),
    ("Puerto Principe", -77.92, 21.38, "1898-12-31"),
    ("Nuevitas", -77.26, 21.55, "1898-12-31"),
]

# rough outline enclosing all of Luzon (zones are clipped to land, so it only has to cover it)
MANILA = [(120.93, 14.5), (120.95, 14.66), (121.05, 14.66), (121.07, 14.52), (120.98, 14.46)]
LUZON_ALL = [(120.3, 14.0), (120.0, 15.6), (120.2, 16.5), (120.4, 17.6), (120.6, 18.7), (121.3, 18.7),
             (122.4, 18.5), (122.3, 17.1), (121.7, 15.7), (122.3, 14.3), (123.6, 14.1), (124.4, 13.0),
             (124.1, 12.5), (122.8, 12.9), (121.2, 13.2), (120.5, 13.6)]
NORTH_LUZON = [(120.8, 14.2), (120.35, 14.9), (120.0, 15.9), (120.3, 16.4), (120.4, 17.5), (120.55, 18.6),
               (121.2, 18.7), (122.3, 18.5), (122.2, 17.2), (121.8, 16.2), (121.6, 15.2), (121.5, 14.5),
               (121.2, 14.2)]

ZONES = [
    # ------------------------------------------------------------------ CARIBBEAN
    dict(name="Cuban Liberation Army (east)", panel="caribbean", kind="poly", occ="CLA", victims=["CUB"],
         start="1898-04-21", end="1899-01-01",
         keys=[("1898-04-21", [(-78.9, 22.6), (-77.4, 22.2), (-75.6, 21.3), (-74.0, 20.4), (-74.2, 19.9),
                               (-76.0, 19.7), (-77.7, 19.7), (-78.2, 20.4), (-79.2, 21.3), (-79.3, 22.0)])]),
    dict(name="Cuban Liberation Army (Las Villas)", panel="caribbean", kind="ellipse", occ="CLA",
         victims=["CUB"], start="1898-04-21", end="1899-01-01",
         keys=[("1898-04-21", -79.9, 22.2, 0.55, 0.3)]),
    *[dict(name=n, panel="caribbean", kind="ellipse", occ="ESP", victims=["CUB"], start="1898-04-21", end=u,
           keys=[("1898-04-21", lo, la, _TOWN_R, _TOWN_R * 0.95)]) for n, lo, la, u in SPANISH_TOWNS_CUBA],
    dict(name="US Marines at Guantanamo Bay", panel="caribbean", kind="ellipse", occ="US", victims=["CUB"],
         start="1898-06-10", end="1898-07-18",
         keys=[("1898-06-10", -75.13, 19.93, 0.0, 0.0), ("1898-06-14", -75.13, 19.93, 0.14, 0.1)]),
    dict(name="Santiago campaign", panel="caribbean", kind="poly", occ="US", victims=["CUB"],
         start="1898-06-22", end="1899-01-02",
         keys=[("1898-06-22", [(-75.72, 19.9), (-75.7, 20.0), (-75.55, 20.02), (-75.5, 19.9)]),
               ("1898-06-24", [(-75.8, 19.9), (-75.78, 20.05), (-75.55, 20.06), (-75.48, 19.9)]),
               ("1898-07-01", [(-75.95, 19.88), (-75.92, 20.12), (-75.72, 20.2), (-75.5, 20.1), (-75.45, 19.88)]),
               ("1898-07-16", [(-76.05, 19.88), (-75.98, 20.2), (-75.75, 20.28), (-75.48, 20.12), (-75.45, 19.88)]),
               ("1898-07-17", [(-76.5, 19.85), (-76.1, 20.6), (-75.0, 20.75), (-74.0, 20.3), (-74.4, 19.8)]),
               ("1898-12-31", [(-76.5, 19.85), (-76.1, 20.6), (-75.0, 20.75), (-74.0, 20.3), (-74.4, 19.8)])]),
    dict(name="Puerto Rico campaign", panel="caribbean", kind="poly", occ="US", victims=["PRI"],
         start="1898-07-25", end="1898-10-19",
         keys=[("1898-07-25", [(-66.93, 17.95), (-66.91, 17.99), (-66.87, 17.98), (-66.89, 17.94), (-66.92, 17.94)]),
               ("1898-07-28", [(-66.95, 17.96), (-66.88, 18.08), (-66.55, 18.07), (-66.55, 17.95), (-66.9, 17.93)]),
               ("1898-08-01", [(-66.97, 17.96), (-66.86, 18.1), (-66.5, 18.09), (-66.05, 18.02), (-66.02, 17.94)]),
               ("1898-08-09", [(-67.0, 17.96), (-66.86, 18.12), (-66.4, 18.13), (-66.1, 18.06), (-66.0, 17.94)]),
               ("1898-08-11", [(-67.25, 18.0), (-67.25, 18.25), (-66.72, 18.2), (-66.3, 18.14), (-66.0, 17.94)]),
               ("1898-08-13", [(-67.28, 18.0), (-67.25, 18.33), (-66.65, 18.3), (-66.25, 18.16), (-65.98, 17.94)]),
               ("1898-10-18", [(-67.28, 18.0), (-67.25, 18.33), (-66.65, 18.3), (-66.25, 18.16), (-65.98, 17.94)])]),
    # ------------------------------------------------------------------ PHILIPPINES 1898
    dict(name="Philippine Revolution (Luzon)", panel="philippines", kind="poly", occ="FIL", victims=["PHL"],
         start="1898-05-24", end="1898-12-11",
         keys=[("1898-05-24", [(120.82, 14.4), (120.88, 14.5), (120.97, 14.47), (120.98, 14.38), (120.9, 14.33)]),
               ("1898-06-12", [(120.6, 14.3), (120.7, 14.55), (120.85, 14.75), (121.0, 14.85), (121.1, 14.7),
                               (121.3, 14.45), (121.45, 14.2), (121.2, 13.95), (120.8, 14.0)]),
               ("1898-07-10", [(120.5, 14.15), (120.45, 14.8), (120.4, 15.25), (120.8, 15.45), (121.2, 15.3),
                               (121.45, 14.8), (121.8, 14.1), (121.6, 13.7), (121.0, 13.65), (120.6, 13.8)]),
               ("1898-08-13", [(120.4, 14.1), (120.2, 14.8), (120.0, 15.6), (120.1, 16.3), (120.7, 16.5),
                               (121.3, 16.2), (121.6, 15.4), (121.9, 14.6), (122.5, 13.9), (122.0, 13.4),
                               (120.9, 13.5)]),
               ("1898-09-30", LUZON_ALL), ("1898-12-10", LUZON_ALL)]),
    dict(name="Philippine Revolution (Visayas)", panel="philippines", kind="poly", occ="FIL", victims=["PHL"],
         start="1898-10-15", end="1898-12-11",
         keys=[("1898-10-15", [(122.0, 11.6), (122.9, 11.7), (122.8, 11.0), (122.1, 10.6), (121.9, 11.0)]),
               ("1898-11-10", [(121.8, 11.9), (123.3, 11.6), (123.5, 9.9), (122.4, 9.4), (121.8, 10.5)]),
               ("1898-12-10", [(121.7, 12.0), (125.6, 12.7), (125.2, 9.8), (122.4, 9.1), (121.8, 10.5)])]),
    dict(name="Spanish Manila", panel="philippines", kind="ellipse", occ="ESP", victims=["PHL"],
         start="1898-05-24", end="1898-08-14",
         keys=[("1898-05-24", 120.99, 14.59, 0.12, 0.12)]),
    dict(name="Spanish Iloilo", panel="philippines", kind="ellipse", occ="ESP", victims=["PHL"],
         start="1898-10-15", end="1898-12-25", keys=[("1898-10-15", 122.56, 10.72, 0.13, 0.12)]),
    dict(name="Moro lands", panel="philippines", kind="poly", occ="MORO", victims=["PHL"],
         start="1898-12-10", end="1902-07-05",
         keys=[("1898-12-10", [(121.8, 8.9), (126.7, 9.9), (126.7, 5.4), (120.2, 4.5), (119.5, 5.8)])]),
    dict(name="Spanish Zamboanga", panel="philippines", kind="ellipse", occ="ESP", victims=["PHL"],
         start="1898-04-21", end="1899-05-19", keys=[("1898-04-21", 122.08, 6.92, 0.14, 0.13)]),
    dict(name="Spanish Jolo", panel="philippines", kind="ellipse", occ="ESP", victims=["PHL"],
         start="1898-04-21", end="1899-05-19", keys=[("1898-04-21", 121.0, 6.05, 0.12, 0.1)]),
    dict(name="Siege of Baler", panel="philippines", kind="ellipse", occ="ESP", victims=["PHL"],
         start="1898-07-01", end="1899-06-03", keys=[("1898-07-01", 121.56, 15.76, 0.08, 0.08)]),
    # ------------------------------------------------------------------ PHILIPPINES 1898-1902: US advance
    dict(name="US Luzon", panel="philippines", kind="poly", occ="US", victims=["PHL"],
         start="1898-08-13", end="1902-07-05",
         keys=[("1898-08-13", MANILA), ("1899-02-04", MANILA),
               ("1899-02-12", [(120.9, 14.45), (120.9, 14.7), (121.0, 14.75), (121.12, 14.6), (121.1, 14.45),
                               (121.0, 14.4)]),
               ("1899-03-31", [(120.88, 14.42), (120.78, 14.7), (120.75, 14.9), (120.85, 14.95), (120.98, 14.85),
                               (121.1, 14.65), (121.12, 14.48), (121.0, 14.38)]),
               ("1899-05-05", [(120.85, 14.38), (120.7, 14.7), (120.6, 15.0), (120.72, 15.1), (120.9, 15.05),
                               (121.05, 14.85), (121.25, 14.55), (121.1, 14.35)]),
               ("1899-10-10", [(120.85, 14.35), (120.6, 14.7), (120.5, 15.0), (120.55, 15.2), (120.75, 15.25),
                               (121.0, 15.2), (121.15, 14.95), (121.3, 14.55), (121.1, 14.3)]),
               ("1899-11-20", [(120.85, 14.35), (120.55, 14.7), (120.3, 15.2), (120.2, 15.8), (120.25, 16.25),
                               (120.55, 16.3), (120.85, 16.05), (121.05, 15.6), (121.15, 15.0), (121.3, 14.55),
                               (121.1, 14.3)]),
               ("1899-12-31", NORTH_LUZON), ("1900-02-15", LUZON_ALL), ("1902-07-04", LUZON_ALL)]),
    dict(name="US Panay", panel="philippines", kind="ellipse", occ="US", victims=["PHL"],
         start="1899-02-11", end="1902-07-05",
         keys=[("1899-02-11", 122.56, 10.72, 0.05, 0.05), ("1899-02-14", 122.56, 10.72, 0.2, 0.18),
               ("1899-12-01", 122.45, 10.9, 0.45, 0.4), ("1900-03-01", 122.5, 11.1, 0.9, 0.8)]),
    dict(name="US Cebu", panel="philippines", kind="ellipse", occ="US", victims=["PHL"],
         start="1899-02-26", end="1902-07-05",
         keys=[("1899-02-26", 123.9, 10.31, 0.05, 0.05), ("1899-03-01", 123.9, 10.31, 0.2, 0.2),
               ("1900-01-15", 123.85, 10.3, 0.55, 0.9)]),
    dict(name="Negros (sides with the US)", panel="philippines", kind="ellipse", occ="US", victims=["PHL"],
         start="1899-03-04", end="1902-07-05",
         keys=[("1899-03-04", 122.95, 10.2, 0.0, 0.0), ("1899-03-20", 122.95, 10.2, 0.7, 1.1)]),
    dict(name="US Bohol", panel="philippines", kind="ellipse", occ="US", victims=["PHL"],
         start="1900-03-17", end="1902-07-05",
         keys=[("1900-03-17", 123.85, 9.65, 0.05, 0.05), ("1900-05-01", 124.1, 9.85, 0.5, 0.35)]),
    dict(name="US Leyte and Samar", panel="philippines", kind="ellipse", occ="US", victims=["PHL"],
         start="1900-01-20", end="1902-07-05",
         keys=[("1900-01-20", 125.0, 11.24, 0.05, 0.05), ("1900-04-01", 124.9, 11.6, 0.9, 1.2)]),
    dict(name="US garrisons in Mindanao", panel="philippines", kind="ellipse", occ="US", victims=["PHL"],
         start="1899-05-20", end="1902-07-05",
         keys=[("1899-05-20", 122.08, 6.92, 0.14, 0.13), ("1900-04-01", 122.2, 7.3, 0.35, 0.45)]),
    dict(name="US northern Mindanao", panel="philippines", kind="ellipse", occ="US", victims=["PHL"],
         start="1900-03-31", end="1902-07-05",
         keys=[("1900-03-31", 124.65, 8.48, 0.05, 0.05), ("1900-06-01", 124.8, 8.6, 0.8, 0.35)]),
    dict(name="US Jolo", panel="philippines", kind="ellipse", occ="US", victims=["PHL"],
         start="1899-05-19", end="1902-07-05", keys=[("1899-05-19", 121.0, 6.05, 0.12, 0.1)]),
    # by early 1900 the US had landed on Mindoro, Masbate, Romblon, Marinduque and Palawan and garrisoned the
    # coasts; everything north of Mindanao and Sulu that isn't a guerrilla pocket (below) is US-held from then on
    dict(name="US garrisons across the islands", panel="philippines", kind="poly", occ="US", victims=["PHL"],
         start="1900-03-01", end="1902-07-05",
         keys=[("1900-03-01", [(116.0, 21.8), (127.5, 21.8), (127.5, 8.7), (125.45, 8.7), (125.3, 9.3),
                               (125.0, 9.85), (124.2, 9.45), (123.2, 9.0), (122.2, 9.0), (120.5, 8.9),
                               (119.0, 8.4), (117.9, 7.6), (116.0, 7.6)])]),
    # ------------------------------------------------------------------ guerrilla war (Filipino pockets)
    dict(name="Aguinaldo's retreat to Palanan", panel="philippines", kind="ellipse", occ="FIL", victims=["PHL"],
         start="1899-11-13", end="1901-03-24",
         keys=[("1899-11-13", 120.8, 16.6, 0.5, 0.5), ("1899-12-02", 120.75, 16.95, 0.35, 0.35),
               ("1900-03-01", 121.9, 17.1, 0.4, 0.4), ("1900-09-06", 122.43, 17.06, 0.18, 0.2),
               ("1901-03-23", 122.43, 17.06, 0.12, 0.14)]),
    dict(name="Ilocos and Cordillera guerrillas", panel="philippines", kind="ellipse", occ="FIL",
         victims=["PHL"], start="1900-01-01", end="1901-06-01",
         keys=[("1900-01-01", 120.75, 17.6, 0.0, 0.0), ("1900-03-01", 120.75, 17.6, 0.35, 0.7),
               ("1901-05-31", 120.75, 17.6, 0.0, 0.0)]),
    dict(name="Batangas and Laguna guerrillas (Malvar)", panel="philippines", kind="ellipse", occ="FIL",
         victims=["PHL"], start="1900-02-01", end="1902-04-17",
         keys=[("1900-02-01", 121.25, 13.95, 0.0, 0.0), ("1900-03-15", 121.25, 13.95, 0.45, 0.35),
               ("1901-12-25", 121.25, 13.95, 0.42, 0.32), ("1902-04-16", 121.2, 13.9, 0.0, 0.0)]),
    dict(name="Bicol guerrillas", panel="philippines", kind="ellipse", occ="FIL", victims=["PHL"],
         start="1900-02-01", end="1901-07-05",
         keys=[("1900-02-01", 123.35, 13.4, 0.0, 0.0), ("1900-03-15", 123.35, 13.4, 0.4, 0.3),
               ("1901-07-04", 123.35, 13.4, 0.0, 0.0)]),
    dict(name="Panay guerrillas", panel="philippines", kind="ellipse", occ="FIL", victims=["PHL"],
         start="1900-03-01", end="1901-02-06",
         keys=[("1900-03-01", 122.4, 11.1, 0.4, 0.3), ("1901-02-05", 122.4, 11.1, 0.0, 0.0)]),
    dict(name="Cebu and Bohol guerrillas", panel="philippines", kind="ellipse", occ="FIL", victims=["PHL"],
         start="1900-01-15", end="1901-12-24",
         keys=[("1900-01-15", 124.0, 10.0, 0.3, 0.35), ("1901-10-27", 124.0, 10.0, 0.2, 0.25),
               ("1901-12-23", 124.0, 10.0, 0.0, 0.0)]),
    dict(name="Samar guerrillas (Lukban)", panel="philippines", kind="ellipse", occ="FIL", victims=["PHL"],
         start="1900-04-01", end="1902-04-28",
         keys=[("1900-04-01", 125.1, 11.9, 0.35, 0.4), ("1901-09-28", 125.2, 11.8, 0.45, 0.5),
               ("1902-02-18", 125.1, 11.9, 0.15, 0.18), ("1902-04-27", 125.1, 11.9, 0.0, 0.0)]),
]

# Army sizes: labels drawn at (possibly moving) positions.
LABELS = [
    # Cuba
    dict(panel="caribbean", name="Spanish army in Cuba",
         hint=[("1898-04-21", (-80.4, 22.55))],
         army=[("1898-04-21", 172_000), ("1898-07-17", 165_000), ("1898-10-01", 140_000),
               ("1898-12-31", 25_000), ("1899-01-02", 0)]),
    dict(panel="caribbean", name="Santiago garrison",
         hint=[("1898-04-21", (-76.2, 19.75))],
         army=[("1898-04-21", 24_000), ("1898-07-16", 23_500), ("1898-07-17", 0)]),
    dict(panel="caribbean", name="Cuban Liberation Army",
         hint=[("1898-04-21", (-77.2, 21.0))],
         army=[("1898-04-21", 32_000), ("1898-08-13", 40_000), ("1898-12-31", 38_000), ("1899-04-01", 0)]),
    dict(panel="caribbean", name="US V Corps / Army of occupation",
         hint=[("1898-06-22", (-75.3, 19.72)), ("1898-12-20", (-75.3, 19.72)), ("1899-01-05", (-79.3, 21.75))],
         army=[("1898-06-22", 6_000), ("1898-06-26", 16_900), ("1898-07-10", 19_500), ("1898-08-20", 17_000),
               ("1898-09-30", 10_500), ("1898-12-31", 24_000), ("1899-03-01", 45_000), ("1899-12-01", 11_000),
               ("1901-01-01", 5_500), ("1902-05-19", 4_800), ("1902-05-20", 0)]),
    dict(panel="caribbean", name="US Marines Guantanamo",
         hint=[("1898-06-10", (-74.8, 19.72))],
         army=[("1898-06-10", 650), ("1898-07-16", 650), ("1898-07-17", 0)]),
    # Puerto Rico
    dict(panel="caribbean", name="Spanish Puerto Rico",
         hint=[("1898-04-21", (-66.3, 18.72))],
         army=[("1898-04-21", 17_000), ("1898-08-13", 16_000), ("1898-10-18", 0)]),
    dict(panel="caribbean", name="US Puerto Rico",
         hint=[("1898-07-25", (-66.55, 17.62))],
         army=[("1898-07-25", 3_400), ("1898-08-01", 10_000), ("1898-08-10", 15_200), ("1898-10-18", 10_000),
               ("1899-06-01", 3_000), ("1899-07-01", 0)]),
    # Philippines
    dict(panel="philippines", name="Spanish Philippines",
         hint=[("1898-04-21", (121.6, 16.6)), ("1898-08-13", (121.4, 17.3)), ("1898-10-01", (123.1, 10.6)),
               ("1898-12-20", (122.6, 7.6))],
         army=[("1898-04-21", 30_000), ("1898-08-12", 26_000), ("1898-08-13", 12_000), ("1898-12-10", 6_000),
               ("1899-06-02", 1_500), ("1899-06-03", 0)]),
    dict(panel="philippines", name="Filipino forces",
         hint=[("1898-05-24", (121.1, 14.15)), ("1898-08-01", (120.8, 15.5)), ("1899-02-04", (121.25, 15.6)),
               ("1899-11-20", (121.2, 17.3)), ("1900-03-01", (122.5, 12.1)), ("1901-04-01", (121.25, 13.75))],
         army=[("1898-05-24", 4_000), ("1898-07-01", 12_000), ("1898-08-13", 30_000), ("1898-12-31", 40_000),
               ("1899-02-04", 80_000), ("1899-11-13", 60_000), ("1900-12-31", 40_000), ("1901-04-01", 20_000),
               ("1901-12-31", 10_000), ("1902-04-16", 3_000), ("1902-07-04", 0)]),
    dict(panel="philippines", name="US Eighth Army Corps / Division of the Philippines",
         hint=[("1898-06-30", (120.35, 14.45)), ("1899-05-05", (120.3, 14.75)), ("1899-11-20", (119.8, 15.8)),
               ("1900-03-01", (120.9, 15.7))],
         army=[("1898-06-30", 2_500), ("1898-07-31", 8_500), ("1898-08-13", 10_900), ("1898-12-31", 15_000),
               ("1899-02-04", 21_000), ("1899-06-01", 26_000), ("1899-12-31", 47_000), ("1900-12-31", 70_000),
               ("1901-07-01", 49_000), ("1902-01-01", 40_000), ("1902-07-04", 34_000)]),
]

MARKERS = [  # (text, panel, lon, lat, start, end)
    ("Manila Bay", "philippines", 120.75, 14.55, "1898-05-01", "1898-05-02"),
    ("Baler", "philippines", 121.56, 15.76, "1898-07-01", "1899-06-02"),
    ("Balangiga", "philippines", 125.39, 11.11, "1901-09-28", "1901-10-15"),
]

EVENTS = [
    ("1898-04-21", "The US Navy blockades Cuba"),
    ("1898-04-23", "Spain declares war on the United States"),
    ("1898-04-25", "The United States declares war on Spain"),
    ("1898-05-01", "Commodore Dewey destroys the Spanish fleet in Manila Bay"),
    ("1898-05-12", "The US Navy bombards San Juan, Puerto Rico"),
    ("1898-05-19", "Emilio Aguinaldo returns to the Philippines"),
    ("1898-05-28", "Filipino revolutionaries defeat the Spanish at Alapan"),
    ("1898-05-29", "Admiral Cervera's squadron is trapped in Santiago harbour"),
    ("1898-06-10", "US Marines land at Guantanamo Bay"),
    ("1898-06-12", "Aguinaldo proclaims the independence of the Philippines"),
    ("1898-06-14", "US Army V Corps sails from Tampa"),
    ("1898-06-20", "The US Navy seizes Guam"),
    ("1898-06-22", "US troops land at Daiquiri and Siboney"),
    ("1898-06-24", "The Battle of Las Guasimas"),
    ("1898-06-30", "The first American troops arrive at Manila"),
    ("1898-07-01", "The Battles of San Juan Hill and El Caney"),
    ("1898-07-03", "The Spanish fleet is destroyed leaving Santiago"),
    ("1898-07-07", "The United States annexes Hawaii"),
    ("1898-07-17", "Santiago de Cuba surrenders"),
    ("1898-07-25", "US troops land at Guanica, Puerto Rico"),
    ("1898-07-28", "Ponce surrenders to the Americans"),
    ("1898-08-09", "The Battle of Coamo"),
    ("1898-08-12", "Spain and the United States sign an armistice"),
    ("1898-08-13", "The Americans capture Manila, keeping the Filipinos out"),
    ("1898-09-15", "The Malolos Congress of the Philippine Republic opens"),
    ("1898-10-18", "Puerto Rico is formally handed over to the United States"),
    ("1898-11-05", "The Negros Revolution overthrows Spanish rule"),
    ("1898-12-10", "The Treaty of Paris - Spain cedes the Philippines, Puerto Rico and Guam"),
    ("1898-12-21", "McKinley proclaims 'Benevolent Assimilation' of the Philippines"),
    ("1898-12-25", "The Spanish evacuate Iloilo"),
    ("1899-01-01", "Spain hands over Cuba - US military occupation begins"),
    ("1899-01-23", "The First Philippine Republic is inaugurated at Malolos"),
    ("1899-02-04", "Fighting breaks out in Manila - the Philippine-American War begins"),
    ("1899-02-06", "The US Senate ratifies the Treaty of Paris"),
    ("1899-02-11", "US troops capture Iloilo"),
    ("1899-03-31", "The Americans capture the Filipino capital Malolos"),
    ("1899-05-05", "US troops take San Fernando, Pampanga"),
    ("1899-06-02", "The Spanish garrison of Baler surrenders after 337 days"),
    ("1899-06-05", "General Antonio Luna is assassinated"),
    ("1899-08-20", "The Bates Treaty with the Sultan of Sulu"),
    ("1899-11-12", "The Americans take Tarlac - Aguinaldo orders guerrilla war"),
    ("1899-12-02", "The Battle of Tirad Pass"),
    ("1899-12-19", "General Lawton is killed at San Mateo"),
    ("1900-01-04", "US offensive in southern Luzon"),
    ("1900-01-20", "US troops land on Samar and Leyte"),
    ("1900-06-21", "Amnesty proclamation for Filipino fighters"),
    ("1900-09-13", "Filipino victory at Pulang Lupa"),
    ("1900-12-20", "General MacArthur declares martial law"),
    ("1901-03-02", "The Platt Amendment limits Cuban independence"),
    ("1901-03-23", "Aguinaldo is captured at Palanan"),
    ("1901-04-19", "Aguinaldo calls on Filipinos to end the fighting"),
    ("1901-07-04", "Civil government under William Taft replaces military rule"),
    ("1901-09-14", "Theodore Roosevelt becomes President"),
    ("1901-09-28", "Samar guerrillas attack the US garrison at Balangiga"),
    ("1901-10-24", "General Jacob Smith's campaign of reprisal on Samar"),
    ("1901-12-25", "General Bell's campaign in Batangas begins"),
    ("1902-02-18", "Vicente Lukban is captured on Samar"),
    ("1902-04-16", "General Miguel Malvar surrenders in Batangas"),
    ("1902-05-20", "The Republic of Cuba becomes independent"),
    ("1902-07-01", "The Philippine Organic Act is passed"),
    ("1902-07-04", "President Roosevelt declares the Philippine insurrection over"),
]

SPEECHES = [
    dict(date="1898-04-11", speaker="President William McKinley", role="War message to Congress",
         voice="am_michael",
         text="In the name of humanity, in the name of civilization, in behalf of endangered American "
              "interests which give us the right and the duty to speak and to act, the war in Cuba must stop."),
    dict(date="1898-05-01", speaker="Commodore George Dewey", role="Manila Bay", voice="am_adam",
         text="You may fire when you are ready, Gridley."),
    dict(date="1898-07-27", speaker="John Hay", role="US Ambassador to Britain, letter to Theodore Roosevelt",
         voice="am_eric",
         text="It has been a splendid little war; begun with the highest motives, carried on with magnificent "
              "intelligence and spirit, favored by that fortune which loves the brave."),
    dict(date="1898-12-21", speaker="President William McKinley", role="Benevolent Assimilation proclamation",
         voice="am_michael",
         text="The mission of the United States is one of benevolent assimilation, substituting the mild "
              "sway of justice and right for arbitrary rule."),
    dict(date="1900-01-09", speaker="Senator Albert Beveridge", role="Speech to the US Senate",
         voice="am_onyx",
         text="The Philippines are ours forever. And just beyond the Philippines are China's illimitable "
              "markets. We will not retreat from either."),
    dict(date="1900-10-15", speaker="Mark Twain", role="Interview, New York Herald", voice="am_fenrir",
         text="I have seen that we do not intend to free, but to subjugate the people of the Philippines. "
              "And so I am an anti-imperialist. I am opposed to having the eagle put its talons on any "
              "other land."),
    dict(date="1901-04-19", speaker="Emilio Aguinaldo", role="Manifesto after his capture (translated)",
         voice="bm_daniel",
         text="Let the stream of blood cease to flow; let there be an end to tears and desolation."),
    dict(date="1901-10-24", speaker="General Jacob H. Smith", role="Orders on Samar (court-martial testimony)",
         voice="am_liam",
         text="I want no prisoners. I wish you to kill and burn; the more you kill and burn, the better "
              "it will please me."),
]

TOTALS = [
    ("Spanish-American War", "Apr - Aug 1898"),
    ("US dead (1898)", "~2,900, mostly from disease"),
    ("Philippine-American War", "Feb 1899 - Jul 1902"),
    ("US dead (1899-1902)", "~4,200"),
    ("Filipino soldiers killed", "~20,000"),
    ("Filipino civilian dead", "200,000 or more"),
]


def day_index(d):
    return (d - START).days


def as_day(s):
    return day_index(D(s))


def date_at(day_float):
    import math
    return START + timedelta(days=int(math.floor(day_float)))
