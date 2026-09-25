"""Historical data for the 1950 Puerto Rican Nationalist uprisings (29 Oct - 3 Nov 1950).

Times are approximate (sources differ by an hour or more for several attacks). Force sizes are
rounded estimates: the Nationalists who took part island-wide numbered in the low hundreds at
most; the government side is the Insular Police plus the Puerto Rico National Guard, which was
mobilized from the afternoon of 30 October.
"""
from datetime import datetime, timedelta

START = datetime(1950, 10, 29, 6, 0)
END = datetime(1950, 11, 3, 18, 0)


def parse(s):
    return datetime.fromisoformat(s if " " in s else s + " 00:00")


def as_day(s):
    return (parse(s) - START).total_seconds() / 86400.0


def date_at(day):
    return START + timedelta(days=day)


FACTIONS = {
    "GOV": ((66, 110, 212), 0.55, "Government (Insular Police, National Guard)"),
    "NAT": ((196, 60, 50), 0.78, "Nationalist Party insurgents"),
}
OWNERS = {"PRI": [("1950-10-29", "GOV")]}

# (name, lon, lat) shown as small place names on the map
TOWNS = [("San Juan", -66.105, 18.466), ("Jayuya", -66.592, 18.219), ("Utuado", -66.700, 18.266),
         ("Naranjito", -66.245, 18.300), ("Arecibo", -66.716, 18.473), ("Mayagüez", -67.139, 18.201),
         ("Ponce", -66.614, 18.011), ("Peñuelas", -66.723, 18.063), ("Hormigueros", -67.127, 18.139),
         ("Santurce", -66.06, 18.445)]

# areas held or contested by the Nationalists: ellipses (time, lon, lat, radius lon, radius lat)
ZONES = [
    dict(name="Macana, Penuelas", start="1950-10-29 20:00", end="1950-10-30 06:00",
         keys=[("1950-10-29 20:00", -66.73, 18.1, 0.0, 0.0), ("1950-10-29 21:00", -66.73, 18.1, 0.03, 0.028),
               ("1950-10-30 04:00", -66.73, 18.1, 0.03, 0.028), ("1950-10-30 06:00", -66.73, 18.1, 0.0, 0.0)]),
    dict(name="Naranjito", start="1950-10-30 10:00", end="1950-11-02 12:00",
         keys=[("1950-10-30 10:00", -66.245, 18.3, 0.0, 0.0), ("1950-10-30 11:00", -66.245, 18.3, 0.03, 0.028),
               ("1950-10-30 18:00", -66.23, 18.27, 0.035, 0.032), ("1950-11-01 12:00", -66.23, 18.26, 0.025, 0.022),
               ("1950-11-02 12:00", -66.23, 18.26, 0.0, 0.0)]),
    dict(name="Arecibo", start="1950-10-30 10:30", end="1950-10-30 14:00",
         keys=[("1950-10-30 10:30", -66.716, 18.47, 0.0, 0.0), ("1950-10-30 11:00", -66.716, 18.47, 0.025, 0.02),
               ("1950-10-30 13:00", -66.716, 18.47, 0.02, 0.016), ("1950-10-30 14:00", -66.716, 18.47, 0.0, 0.0)]),
    dict(name="Jayuya - Free Republic of Puerto Rico", start="1950-10-30 11:00", end="1950-11-02 06:00",
         keys=[("1950-10-30 11:00", -66.592, 18.219, 0.0, 0.0), ("1950-10-30 13:00", -66.592, 18.219, 0.055, 0.05),
               ("1950-10-31 12:00", -66.592, 18.219, 0.06, 0.055), ("1950-11-01 10:00", -66.59, 18.215, 0.035, 0.032),
               ("1950-11-01 20:00", -66.585, 18.205, 0.015, 0.014), ("1950-11-02 06:00", -66.585, 18.205, 0.0, 0.0)]),
    dict(name="Mayaguez and Hormigueros", start="1950-10-30 11:30", end="1950-10-31 16:00",
         keys=[("1950-10-30 11:30", -67.139, 18.201, 0.0, 0.0), ("1950-10-30 12:00", -67.139, 18.2, 0.025, 0.022),
               ("1950-10-30 18:00", -67.125, 18.15, 0.03, 0.027), ("1950-10-31 16:00", -67.125, 18.15, 0.0, 0.0)]),
    dict(name="Ponce", start="1950-10-30 11:30", end="1950-10-30 15:00",
         keys=[("1950-10-30 11:30", -66.614, 18.012, 0.0, 0.0), ("1950-10-30 12:00", -66.614, 18.012, 0.02, 0.018),
               ("1950-10-30 15:00", -66.614, 18.012, 0.0, 0.0)]),
    dict(name="Utuado", start="1950-10-30 13:00", end="1950-10-31 12:30",
         keys=[("1950-10-30 13:00", -66.7, 18.266, 0.0, 0.0), ("1950-10-30 14:00", -66.7, 18.266, 0.04, 0.036),
               ("1950-10-31 08:00", -66.7, 18.266, 0.03, 0.027), ("1950-10-31 12:00", -66.7, 18.266, 0.0, 0.0)]),
    dict(name="Albizu Campos's home, Old San Juan", start="1950-10-30 18:00", end="1950-11-02 16:30",
         keys=[("1950-10-30 18:00", -66.117, 18.466, 0.0, 0.0), ("1950-10-30 19:00", -66.117, 18.466, 0.012, 0.011),
               ("1950-11-02 16:00", -66.117, 18.466, 0.012, 0.011), ("1950-11-02 16:30", -66.117, 18.466, 0.0, 0.0)]),
]

LABELS = [
    dict(name="Government forces", hint=[("1950-10-29", (-65.95, 18.2))],
         army=[("1950-10-29", 2_400), ("1950-10-30 15:00", 2_400), ("1950-10-30 22:00", 4_000),
               ("1950-10-31 12:00", 6_000), ("1950-11-01 12:00", 7_000), ("1950-11-03 18:00", 7_000)]),
    dict(name="Nationalist fighters", hint=[("1950-10-29", (-66.45, 18.13))],
         army=[("1950-10-29", 140), ("1950-10-30 20:00", 125), ("1950-10-31 12:00", 90), ("1950-11-01 12:00", 45),
               ("1950-11-02 16:00", 12), ("1950-11-03 12:00", 3), ("1950-11-03 18:00", 0)]),
    dict(name="Utuado group", hint=[("1950-10-30 13:00", (-66.77, 18.33))],
         army=[("1950-10-30 13:00", 32), ("1950-10-31 11:00", 32), ("1950-10-31 12:30", 0)]),
    dict(name="La Fortaleza attackers", hint=[("1950-10-30 12:30", (-66.13, 18.53))],
         army=[("1950-10-30 12:30", 5), ("1950-10-30 12:45", 5), ("1950-10-30 13:30", 0)]),
]

MARKERS = [  # (text, lon, lat, start, end)
    ("Peñuelas shootout", -66.73, 18.1, "1950-10-29 20:00", "1950-10-30 04:00"),
    ("La Fortaleza", -66.12, 18.464, "1950-10-30 12:30", "1950-10-30 13:30"),
    ("Salón Boricua", -66.05, 18.44, "1950-10-30 14:00", "1950-10-30 17:00"),
    ("Air attacks", -66.63, 18.24, "1950-10-31 10:00", "1950-11-01 10:00"),
    ("Siege of Albizu Campos", -66.117, 18.466, "1950-10-30 18:00", "1950-11-02 16:00"),
]

# a card in the corner for the attack in Washington, D.C.
INSET = dict(start="1950-11-01 14:00", end="1950-11-02 02:00", title="Washington, D.C. - Blair House",
             lines=["Oscar Collazo and Griselio Torresola", "attack the residence of President Truman"],
             numbers=[("Nationalists", 2)])

EVENTS = [
    ("1950-10-29 06:00", "Police move against the Nationalist Party of Pedro Albizu Campos"),
    ("1950-10-29 20:00", "Police raid Nationalists in Barrio Macaná, Peñuelas - a gunfight breaks out"),
    ("1950-10-30 09:00", "The Nationalist uprising begins across Puerto Rico"),
    ("1950-10-30 10:00", "Nationalists attack the police station in Naranjito"),
    ("1950-10-30 10:30", "Nationalists attack the police station in Arecibo"),
    ("1950-10-30 11:00", "Jayuya: Blanca Canales leads the attack on the police station"),
    ("1950-10-30 11:30", "Clashes with the police in Mayagüez and Ponce"),
    ("1950-10-30 12:00", "Blanca Canales proclaims the Free Republic of Puerto Rico in Jayuya"),
    ("1950-10-30 12:30", "Five Nationalists attack La Fortaleza, the governor's residence"),
    ("1950-10-30 13:00", "Nationalists attack the police in Utuado"),
    ("1950-10-30 14:00", "Vidal Santiago Díaz holds off police for hours at the Salón Boricua, Santurce"),
    ("1950-10-30 16:00", "Governor Luis Muñoz Marín calls out the National Guard"),
    ("1950-10-30 18:00", "Police surround Albizu Campos's home in Old San Juan"),
    ("1950-10-31 06:00", "The National Guard advances on Jayuya and Utuado"),
    ("1950-10-31 10:00", "National Guard P-47 Thunderbolts attack Jayuya and Utuado"),
    ("1950-10-31 12:00", "Utuado: the Nationalists surrender - five are shot dead by guardsmen"),
    ("1950-11-01 10:00", "The National Guard retakes Jayuya"),
    ("1950-11-01 14:20", "Washington: Nationalists Collazo and Torresola attack Blair House"),
    ("1950-11-01 14:40", "Torresola and White House policeman Leslie Coffelt are killed"),
    ("1950-11-02 16:00", "Tear gas forces Albizu Campos out - he is arrested"),
    ("1950-11-03 08:00", "Hundreds of Nationalists and suspected sympathizers are arrested"),
]

SPEECHES = [
    dict(date="1950-10-29", speaker="Pedro Albizu Campos", role="Nationalist Party motto", voice="em_alex",
         lang="es", text="La patria es valor y sacrificio."),
    dict(date="1950-10-30 12:00", speaker="Blanca Canales", role="Jayuya", voice="ef_dora", lang="es",
         text="¡Viva Puerto Rico libre!"),
    dict(date="1950-11-01 16:00", speaker="President Harry S. Truman", role="after the Blair House attack",
         voice="am_michael", text="A president has to expect these things."),
]

TOTALS = [
    ("Dead", "about 28"),
    ("Nationalists", "16"),
    ("Police and guardsmen", "8"),
    ("Bystanders", "4"),
    ("Arrested", "over 1,000"),
]
