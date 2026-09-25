"""Puerto Rico's roads and railway in 1898, traced by hand through the towns they served (approximate).

In 1898 the French-built railway (Compania de los Ferrocarriles de Puerto Rico) ran only in separate
sections; the only first-class road was the Carretera Central (San Juan - Ponce, finished 1886).
Most other routes were rough country roads and bridle paths, which the American columns used.
"""

RAILWAYS = [
    # San Juan - Bayamon - Manati - Arecibo - Camuy
    [(-66.085, 18.455), (-66.12, 18.43), (-66.155, 18.40), (-66.21, 18.425), (-66.25, 18.44), (-66.27, 18.46),
     (-66.33, 18.44), (-66.39, 18.445), (-66.49, 18.435), (-66.54, 18.45), (-66.62, 18.465), (-66.716, 18.473),
     (-66.825, 18.486), (-66.845, 18.484)],
    # Aguadilla - Aguada - Anasco - Mayaguez - Hormigueros
    [(-67.155, 18.43), (-67.19, 18.38), (-67.17, 18.32), (-67.14, 18.28), (-67.14, 18.20), (-67.127, 18.139)],
    # Ponce - Guayanilla - Yauco
    [(-66.614, 18.012), (-66.72, 18.01), (-66.79, 18.02), (-66.85, 18.03)],
]

ROADS = [
    # Carretera Central: San Juan - Rio Piedras - Caguas - Cayey - Aibonito - Asomante - Coamo - Juana Diaz - Ponce
    [(-66.085, 18.455), (-66.05, 18.40), (-66.04, 18.33), (-66.035, 18.235), (-66.10, 18.17), (-66.166, 18.112),
     (-66.265, 18.14), (-66.31, 18.12), (-66.358, 18.08), (-66.43, 18.06), (-66.507, 18.052), (-66.614, 18.012)],
    # Guanica - Yauco, Yauco - Sabana Grande - San German - Hormigueros - Mayaguez
    [(-66.908, 17.972), (-66.88, 18.0), (-66.85, 18.035)],
    [(-66.85, 18.035), (-66.9, 18.06), (-66.96, 18.078), (-67.045, 18.082), (-67.1, 18.12), (-67.127, 18.139),
     (-67.139, 18.201)],
    # Yauco - Guayanilla - Penuelas - Ponce (coast road)
    [(-66.85, 18.035), (-66.79, 18.025), (-66.723, 18.063), (-66.65, 18.03), (-66.614, 18.012)],
    # Ponce - Juana Diaz - Santa Isabel - Salinas - Guayama - Arroyo
    [(-66.614, 18.012), (-66.507, 18.052), (-66.39, 17.975), (-66.26, 17.99), (-66.11, 17.984), (-66.061, 17.966)],
    # Guayama - Guamani heights - Cayey
    [(-66.11, 17.984), (-66.13, 18.03), (-66.15, 18.07), (-66.166, 18.112)],
    # Ponce - Adjuntas - Utuado - Arecibo (road and bridle path)
    [(-66.614, 18.012), (-66.65, 18.06), (-66.69, 18.11), (-66.722, 18.163), (-66.71, 18.21), (-66.7, 18.266),
     (-66.69, 18.33), (-66.70, 18.40), (-66.716, 18.468)],
    # Mayaguez - Las Marias - Lares; Mayaguez - Anasco - Aguadilla
    [(-67.139, 18.201), (-67.09, 18.22), (-67.04, 18.235), (-67.0, 18.25), (-66.94, 18.28), (-66.878, 18.295)],
    [(-67.139, 18.201), (-67.14, 18.28), (-67.17, 18.32), (-67.19, 18.375), (-67.155, 18.428)],
    # north coast: San Juan - Arecibo - Aguadilla
    [(-66.085, 18.455), (-66.155, 18.39), (-66.25, 18.43), (-66.39, 18.44), (-66.49, 18.425), (-66.716, 18.468),
     (-66.83, 18.48), (-66.94, 18.465), (-67.02, 18.49), (-67.155, 18.428)],
    # San Juan - Carolina - Rio Grande - Fajardo
    [(-66.085, 18.455), (-65.95, 18.38), (-65.83, 18.38), (-65.75, 18.37), (-65.652, 18.325), (-65.62, 18.37)],
]
