"""
Headed stud dimensions per PCI Design Handbook, 6th Edition, Table 6.5.1.2
and ACI 318-08 related constants.
Units stored in imperial (inches, ksi, psi) - conversion happens at I/O boundary.
"""

# Stud dimensions: db (in) -> {Ase (in2), dhs (in), ths (in), Abrg (in2)}
STUD_TABLE = {
    0.250: {"Ase": 0.05, "dhs": 0.500, "ths": 0.1875, "Abrg": 0.15},
    0.375: {"Ase": 0.11, "dhs": 0.750, "ths": 0.2813, "Abrg": 0.33},
    0.500: {"Ase": 0.20, "dhs": 1.000, "ths": 0.3125, "Abrg": 0.59},
    0.625: {"Ase": 0.31, "dhs": 1.250, "ths": 0.3125, "Abrg": 0.62},
    0.750: {"Ase": 0.44, "dhs": 1.250, "ths": 0.3750, "Abrg": 0.79},
    0.875: {"Ase": 0.60, "dhs": 1.375, "ths": 0.3750, "Abrg": 0.88},
}

# Available stud diameters in mm for GUI display
STUD_DIAMETERS_MM = [6.35, 9.525, 12.7, 15.875, 19.05, 22.225]
STUD_DIAMETERS_IN = [0.250, 0.375, 0.500, 0.625, 0.750, 0.875]

# Phi factors per ACI 318-08 Appendix D
PHI_FACTORS = {
    "steel": {"tension": {"Ductile": 0.75, "Brittle": 0.65},
              "shear":   {"Ductile": 0.65, "Brittle": 0.60}},
    "concrete": {"tension":  {"A": 0.75, "B": 0.70},
                 "shear":    {"A": 0.75, "B": 0.70}},
}

# Concrete type lambda factors
LAMBDA_FACTORS = {"Normalwt": 1.0, "Sandlwt": 0.85, "Allwt": 0.75}

# kc for cast-in-place anchors
KC_CASTIN = 24

# Minimum steel edge distances per AISC Table J3.4 (in)
MIN_STEEL_EDGE = {
    0.250: 0.500, 0.375: 0.625, 0.500: 0.875,
    0.625: 0.875, 0.750: 1.125, 0.875: 1.125,
}

# Unit conversion constants
KN_TO_KIPS = 0.224809
KIPS_TO_KN = 4.44822
M_TO_IN = 39.3701
IN_TO_M = 0.0254
MM_TO_IN = 0.03937008
IN_TO_MM = 25.4
MPA_TO_PSI = 145.038
PSI_TO_MPA = 0.00689476
MPA_TO_KSI = 0.145038
KSI_TO_MPA = 6.89476
