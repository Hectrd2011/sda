"""Historical data for the Puerto Rican Campaign of the Spanish-American War (May - October 1898).

US-held ground is drawn as the area reachable along roads (then over open country and hills) from the
towns and landing places the Americans held on each date, so it grows along the routes the columns
actually marched. Times of day are approximate. Force sizes are rounded estimates from Trask,
"The War with Spain in 1898", Rivero, "Cronica de la Guerra Hispanoamericana en Puerto Rico", and
the US War Department reports; small detachments are the most uncertain.
"""
from datetime import datetime, timedelta

START = datetime(1898, 5, 10, 0, 0)
END = datetime(1898, 10, 18, 18, 0)


def parse(s):
    return datetime.fromisoformat(s if " " in s else s + " 00:00")


def as_day(s):
    return (parse(s) - START).total_seconds() / 86400.0


def date_at(day):
    return START + timedelta(days=day)


FACTIONS = {
    "US": ((66, 110, 212), 0.62, "United States Army"),
    "ESP": ((196, 152, 44), 0.60, "Spanish Army and Volunteers"),
}
OWNERS = {"PRI": [("1898-05-10", "ESP"), ("1898-10-18 12:00", "US")]}

P = {  # places (lon, lat)
    "Guanica": (-66.908, 17.972), "Seboruco": (-66.875, 18.0), "Yauco": (-66.85, 18.035),
    "Guayanilla": (-66.79, 18.022), "Penuelas": (-66.723, 18.063), "Ponce": (-66.614, 18.012),
    "Juana Diaz": (-66.507, 18.052), "Coamo": (-66.358, 18.08), "Asomante": (-66.31, 18.115),
    "Arroyo": (-66.061, 17.966), "Guayama": (-66.11, 17.984), "Guamani": (-66.13, 18.03),
    "Sabana Grande": (-66.96, 18.078), "San German": (-67.045, 18.082), "Hormigueros": (-67.127, 18.139),
    "Mayaguez": (-67.139, 18.201), "Las Marias": (-67.0, 18.25), "Rio Prieto": (-67.04, 18.235),
    "Adjuntas": (-66.722, 18.163), "Utuado": (-66.7, 18.266), "Fajardo lighthouse": (-65.618, 18.382),
    "Santa Isabel": (-66.39, 17.975), "Salinas": (-66.26, 17.99),
}

TOWNS = [(n, *P[k]) for n, k in [("Guánica", "Guanica"), ("Yauco", "Yauco"), ("Ponce", "Ponce"),
                                  ("Juana Díaz", "Juana Diaz"), ("Coamo", "Coamo"), ("Guayama", "Guayama"),
                                  ("Arroyo", "Arroyo"), ("San Germán", "San German"), ("Mayagüez", "Mayaguez"),
                                  ("Adjuntas", "Adjuntas"), ("Utuado", "Utuado")]] + \
    [("San Juan", -66.105, 18.466), ("Aibonito", -66.265, 18.14), ("Arecibo", -66.716, 18.473),
     ("Cayey", -66.166, 18.112), ("Aguadilla", -67.155, 18.428), ("Fajardo", -65.652, 18.325)]


def seeds(*names):
    return [P[n] for n in names]


SOUTH_1 = ("Guanica", "Seboruco", "Yauco", "Guayanilla", "Penuelas", "Ponce")
# US-held ground: (time, places held, reach in km of easy going around each)
ZONES = [
    dict(name="US occupation (south and west)", occ="US", start="1898-07-25 08:00", end="1898-10-19",
         keys=[("1898-07-25 08:00", seeds("Guanica"), 0.0),
               ("1898-07-25 16:00", seeds("Guanica"), 2.5),
               ("1898-07-26 14:00", seeds("Guanica", "Seboruco"), 3.0),
               ("1898-07-27 12:00", seeds("Guanica", "Seboruco", "Yauco"), 3.5),
               ("1898-07-28 12:00", seeds(*SOUTH_1), 4.0),
               ("1898-07-31 12:00", seeds(*SOUTH_1), 4.5),
               ("1898-08-01 16:00", seeds(*SOUTH_1, "Arroyo"), 4.5),
               ("1898-08-02 12:00", seeds(*SOUTH_1, "Juana Diaz", "Arroyo"), 4.5),
               ("1898-08-05 14:00", seeds(*SOUTH_1, "Juana Diaz", "Arroyo", "Guayama"), 5.0),
               ("1898-08-08 12:00", seeds(*SOUTH_1, "Juana Diaz", "Arroyo", "Guayama", "Santa Isabel"), 5.0),
               ("1898-08-09 16:00", seeds(*SOUTH_1, "Juana Diaz", "Arroyo", "Guayama", "Santa Isabel", "Coamo",
                                          "Sabana Grande"), 5.0),
               ("1898-08-10 18:00", seeds(*SOUTH_1, "Juana Diaz", "Arroyo", "Guayama", "Santa Isabel", "Coamo",
                                          "Sabana Grande", "San German", "Hormigueros", "Adjuntas"), 5.0),
               ("1898-08-11 16:00", seeds(*SOUTH_1, "Juana Diaz", "Arroyo", "Guayama", "Santa Isabel", "Coamo",
                                          "Sabana Grande", "San German", "Hormigueros", "Mayaguez", "Adjuntas"),
                5.5),
               ("1898-08-13 12:00", seeds(*SOUTH_1, "Juana Diaz", "Arroyo", "Guayama", "Santa Isabel", "Coamo",
                                          "Sabana Grande", "San German", "Hormigueros", "Mayaguez", "Rio Prieto",
                                          "Adjuntas", "Utuado", "Salinas"), 6.0),
               ("1898-10-18 12:00", seeds(*SOUTH_1, "Juana Diaz", "Arroyo", "Guayama", "Santa Isabel", "Coamo",
                                          "Sabana Grande", "San German", "Hormigueros", "Mayaguez", "Rio Prieto",
                                          "Adjuntas", "Utuado", "Salinas"), 6.0)]),
    dict(name="Fajardo lighthouse", occ="US", start="1898-08-01 18:00", end="1898-08-06",
         keys=[("1898-08-01 18:00", seeds("Fajardo lighthouse"), 0.0),
               ("1898-08-02 06:00", seeds("Fajardo lighthouse"), 1.2),
               ("1898-08-05 06:00", seeds("Fajardo lighthouse"), 1.2),
               ("1898-08-05 20:00", seeds("Fajardo lighthouse"), 0.0)]),
]

# numbers; hints move with the columns (lon, lat)
LABELS = [
    dict(name="Spanish forces", fixed=True, hint=[("1898-05-10", (-66.25, 18.36))],
         army=[("1898-05-10", 17_000), ("1898-07-25", 17_000), ("1898-08-13", 15_800), ("1898-10-17", 9_000),
               ("1898-10-18 12:00", 0)]),
    dict(name="Miles's expedition", hint=[("1898-07-25", (-66.93, 17.9)), ("1898-07-26", (-66.86, 18.02)), ("1898-07-28 12:00", (-66.78, 18.06))],
         army=[("1898-07-25 06:00", 3_400), ("1898-07-28", 3_400), ("1898-07-31", 7_000),
               ("1898-08-01 12:00", 7_000), ("1898-08-01 13:00", 0)]),
    dict(name="Wilson's column", hint=[("1898-08-01", (-66.52, 18.08)), ("1898-08-09 12:00", (-66.33, 18.1))],
         army=[("1898-08-01 12:00", 3_200), ("1898-08-13 12:00", 3_200), ("1898-10-18", 3_000)]),
    dict(name="Brooke's column", hint=[("1898-08-01", (-66.07, 17.99)), ("1898-08-05", (-66.12, 18.03))],
         army=[("1898-08-01 16:00", 1_600), ("1898-08-03", 5_000), ("1898-10-18", 5_000)]),
    dict(name="Schwan's column", hint=[("1898-08-09", (-66.95, 18.1)), ("1898-08-10 12:00", (-67.08, 18.15)), ("1898-08-11 16:00", (-67.05, 18.23))],
         army=[("1898-08-09 06:00", 1_450), ("1898-10-18", 1_450)]),
    dict(name="Henry's column", hint=[("1898-08-06", (-66.68, 18.1)), ("1898-08-13", (-66.68, 18.12))],
         army=[("1898-08-06", 2_800), ("1898-10-18", 2_800)]),
    dict(name="Spanish at Aibonito and Asomante", hint=[("1898-08-02", (-66.28, 18.13))],
         army=[("1898-08-02", 1_300), ("1898-10-17", 1_300), ("1898-10-18", 0)]),
    dict(name="Spanish in the west (Mayaguez)", hint=[("1898-07-26", (-67.05, 18.15)), ("1898-08-11 16:00", (-67.0, 18.26))],
         army=[("1898-07-26", 1_300), ("1898-08-10 12:00", 1_300), ("1898-08-11", 1_050), ("1898-08-13", 900),
               ("1898-10-17", 900), ("1898-10-18", 0)]),
]

MARKERS = [  # (text, lon, lat, start, end)
    ("Bombardment of San Juan", -66.12, 18.475, "1898-05-12 05:00", "1898-05-12 09:00"),
    ("Naval battle off San Juan", -66.1, 18.51, "1898-06-22 12:00", "1898-06-22 18:00"),
    ("Guánica", -66.908, 17.965, "1898-07-25 06:00", "1898-07-25 14:00"),
    ("Yauco (Seboruco)", -66.875, 18.0, "1898-07-26 01:00", "1898-07-26 10:00"),
    ("Fajardo", -65.618, 18.382, "1898-08-01 18:00", "1898-08-05 12:00"),
    ("Guayama", -66.11, 17.984, "1898-08-05 08:00", "1898-08-05 16:00"),
    ("Coamo", -66.358, 18.08, "1898-08-09 05:00", "1898-08-09 14:00"),
    ("Silva Heights", -67.12, 18.15, "1898-08-10 10:00", "1898-08-10 19:00"),
    ("Asomante", -66.31, 18.115, "1898-08-12 12:00", "1898-08-12 18:00"),
    ("Guamaní Heights", -66.13, 18.03, "1898-08-13 08:00", "1898-08-13 13:00"),
    ("Río Prieto", -67.04, 18.235, "1898-08-13 06:00", "1898-08-13 12:00"),
]
BATTLES = [(a, b) for _, _, _, a, b in MARKERS]  # for the gunfire sound

EVENTS = [
    ("1898-05-10", "Puerto Rico, a Spanish colony since 1508, prepares for war"),
    ("1898-05-12 05:00", "Admiral Sampson's squadron bombards San Juan"),
    ("1898-06-22 12:00", "The US auxiliary cruiser St. Paul fights Spanish warships off San Juan"),
    ("1898-07-17", "Santiago de Cuba surrenders - the US turns to Puerto Rico"),
    ("1898-07-21", "General Nelson Miles's expedition sails from Guantánamo"),
    ("1898-07-25 06:00", "US troops land at Guánica"),
    ("1898-07-26 01:00", "The Battle of Yauco at the Hacienda Desideria"),
    ("1898-07-27 12:00", "US troops enter Yauco"),
    ("1898-07-28 06:00", "Ponce surrenders to the US Navy without a fight"),
    ("1898-07-28 12:00", "General Miles issues his proclamation to the people of Puerto Rico"),
    ("1898-07-31", "Reinforcements land at Ponce"),
    ("1898-08-01 12:00", "General Brooke's troops land at Arroyo"),
    ("1898-08-01 18:00", "US sailors hold the Fajardo lighthouse against Spanish attacks"),
    ("1898-08-05 08:00", "The Battle of Guayama - the town falls to Brooke's column"),
    ("1898-08-06", "Four US columns advance into the interior"),
    ("1898-08-09 05:00", "The Battle of Coamo - Wilson's column takes the town"),
    ("1898-08-09 12:00", "Schwan's column marches west from Yauco"),
    ("1898-08-10 10:00", "The Battle of Silva Heights near Hormigueros"),
    ("1898-08-11 12:00", "US troops enter Mayagüez"),
    ("1898-08-12 12:00", "The Battle of Asomante - artillery duel below Aibonito"),
    ("1898-08-12 16:30", "Spain and the United States sign an armistice in Washington"),
    ("1898-08-13 06:00", "Last clashes at Guamaní Heights and Río Prieto, before news of the armistice arrives"),
    ("1898-08-13 14:00", "News of the armistice reaches Puerto Rico - the fighting stops"),
    ("1898-09-10", "American and Spanish commissioners meet in San Juan"),
    ("1898-10-18 12:00", "The Spanish flag is lowered in San Juan - Puerto Rico passes to the United States"),
]

SPEECHES = [
    dict(date="1898-05-10", speaker="President William McKinley", role="War message to Congress",
         voice="am_michael",
         text="In the name of humanity, in the name of civilization, in behalf of endangered American "
              "interests which give us the right and the duty to speak and to act, the war in Cuba must stop."),
    dict(date="1898-07-28 12:00", speaker="General Nelson A. Miles", role="Proclamation to the people of Puerto Rico",
         voice="am_adam",
         text="We have not come to make war upon the people of a country that for centuries has been oppressed, "
              "but, on the contrary, to bring you protection, not only to yourselves but to your property, "
              "to promote your prosperity, and to bestow upon you the immunities and blessings of the liberal "
              "institutions of our government."),
]

TOTALS = [
    ("US killed in action", "about 5"),
    ("US wounded", "about 40"),
    ("Spanish killed", "about 17"),
    ("Spanish wounded", "about 88"),
    ("Handover", "18 October 1898"),
]

# which Sousa march plays when (march file, start date); crossfaded
MUSIC = [
    ("ElCapitanMarch", "1898-05-10"),
    ("TheLibertyBell", "1898-07-17"),
    ("TheStarsAndStripesForever", "1898-07-25 06:00"),
    ("KingCotton", "1898-08-06"),
    ("HandsacrosstheSea", "1898-08-12 16:30"),
]
