"""
Embedded Plate Anchorage Calculation Engine
Per ACI 318-08, Appendix D — Design of (2) Headed Concrete Anchor Stud Plate

All internal calculations in imperial units (kips, inches, psi, ksi).
Conversion to SI (kN, mm, MPa) at input/output boundary.
"""

import math
from data import (
    STUD_TABLE, PHI_FACTORS, LAMBDA_FACTORS, KC_CASTIN, MIN_STEEL_EDGE,
    KN_TO_KIPS, KIPS_TO_KN, MM_TO_IN, IN_TO_MM, MPA_TO_PSI, MPA_TO_KSI,
)


class InputData:
    """Stores all user inputs in imperial units."""

    def __init__(self):
        # Loads (kips)
        self.Nua = 0.0
        self.Vua_x = 0.0
        self.Vua_y = 0.0
        self.ex = 0.0  # in
        self.ey = 0.0  # in

        # Plate edge distances (in)
        self.bx1 = 0.0
        self.bx2 = 0.0
        self.by1 = 0.0
        self.by2 = 0.0

        # Stud spacing (in)
        self.sx1 = 0.0

        # Concrete edge distances (in)
        self.cx1 = 0.0
        self.cx2 = 0.0
        self.cy1 = 0.0
        self.cy2 = 0.0

        # Parameters
        self.db = 0.5  # in, stud diameter
        self.fc = 3000.0  # psi
        self.fy = 36.0  # ksi
        self.futa = 58.0  # ksi
        self.steel_element = "Ductile"
        self.hef = 9.5  # in
        self.ha = 12.0  # in
        self.supp_reinf = False
        self.cracking = False
        self.seismic = False
        self.concrete_type = "Normalwt"
        self.per_D623 = False

    @classmethod
    def from_si(cls, si_dict):
        """Create InputData from SI units (kN, mm, MPa)."""
        d = cls()
        d.Nua = si_dict["Nua"] * KN_TO_KIPS
        d.Vua_x = si_dict["Vua_x"] * KN_TO_KIPS
        d.Vua_y = si_dict["Vua_y"] * KN_TO_KIPS
        d.ex = si_dict["ex"] * MM_TO_IN
        d.ey = si_dict["ey"] * MM_TO_IN

        for key in ["bx1", "bx2", "by1", "by2", "sx1",
                     "cx1", "cx2", "cy1", "cy2", "hef", "ha"]:
            setattr(d, key, si_dict[key] * MM_TO_IN)

        d.db = si_dict["db"] * MM_TO_IN
        d.fc = si_dict["fc"] * MPA_TO_PSI
        d.fy = si_dict["fy"] * MPA_TO_KSI
        d.futa = si_dict["futa"] * MPA_TO_KSI
        d.steel_element = si_dict["steel_element"]
        d.supp_reinf = si_dict["supp_reinf"]
        d.cracking = si_dict["cracking"]
        d.seismic = si_dict["seismic"]
        d.concrete_type = si_dict["concrete_type"]
        d.per_D623 = si_dict["per_D623"]
        return d


class Results:
    """Stores all calculation results with status."""

    def __init__(self):
        self.sections = {}
        self.overall_status = "OK"

    def add(self, key, label, capacity, demand, phi, nominal, ratio, status, details=None):
        self.sections[key] = {
            "label": label,
            "capacity": capacity,   # phi * nominal (kips)
            "demand": demand,       # kips
            "phi": phi,
            "nominal": nominal,     # kips
            "ratio": ratio,
            "status": status,
            "details": details or {},
        }
        if status == "NG":
            self.overall_status = "NG"

    def add_na(self, key, label, reason="N/A"):
        self.sections[key] = {
            "label": label, "capacity": None, "demand": None,
            "phi": None, "nominal": None, "ratio": None,
            "status": "N/A", "details": {"reason": reason},
        }


def _get_stud_props(db):
    """Get stud properties for given diameter."""
    # Find closest match
    best = min(STUD_TABLE.keys(), key=lambda k: abs(k - db))
    return STUD_TABLE[best]


def _bolt_reactions(inp):
    """Compute individual bolt reactions using elastic method for 2-bolt group."""
    n = 2
    # Bolt coordinates (bolt 1 at origin-ish, bolt 2 at sx1 apart)
    bolts = [
        (inp.bx1, inp.by1),
        (inp.bx1 + inp.sx1, inp.by1),
    ]

    # Centroid
    xc = sum(b[0] for b in bolts) / n
    yc = sum(b[1] for b in bolts) / n

    # Distances from centroid
    dx = [b[0] - xc for b in bolts]
    dy = [b[1] - yc for b in bolts]

    Ix = sum(d ** 2 for d in dy)
    Iy = sum(d ** 2 for d in dx)
    J = Ix + Iy

    # Loads at CG
    Pz = inp.Nua
    Px = inp.Vua_x
    Py = inp.Vua_y

    # Moments at CG
    Mx_pz = 0.0
    My_pz = -Pz * inp.ex if inp.ex != 0 else 0.0
    Mz_py = Py * (inp.ey if inp.ey != 0 else 0.0)
    Mz_px = 0.0

    My = My_pz
    Mz = Mz_py + Mz_px

    # Axial reactions (tension positive = pulling out)
    axial = []
    for i in range(n):
        Rz = -Pz / n
        if Ix > 1e-10:
            Rz -= My * dy[i] / Ix  # approximation
        axial.append(Rz)

    # Shear reactions
    shear = []
    for i in range(n):
        Rhx = Px / n
        Rhy = Py / n
        if J > 1e-10:
            Rhx += Mz * (-dy[i]) / J
            Rhy += Mz * dx[i] / J
        Rh = math.sqrt(Rhx ** 2 + Rhy ** 2)
        shear.append(Rh)

    return axial, shear


def calculate(inp: InputData) -> Results:
    """Run full ACI 318-08 Appendix D calculation."""
    res = Results()
    stud = _get_stud_props(inp.db)
    Ase = stud["Ase"]
    Abrg = stud["Abrg"]
    lam = LAMBDA_FACTORS.get(inp.concrete_type, 1.0)
    n_bolts = 2

    # Bolt reactions
    axial_reactions, shear_reactions = _bolt_reactions(inp)
    Nu_max = max(abs(a) for a in axial_reactions)
    Vu_max = max(shear_reactions)

    cond = "B" if inp.supp_reinf else "B"  # Default Condition B (no supp reinf)
    if inp.supp_reinf:
        cond = "A"

    phi_steel_t = PHI_FACTORS["steel"]["tension"][inp.steel_element]
    phi_steel_v = PHI_FACTORS["steel"]["shear"][inp.steel_element]
    phi_conc_t = PHI_FACTORS["concrete"]["tension"][cond]
    phi_conc_v = PHI_FACTORS["concrete"]["shear"][cond]

    # ========================
    # 1. Steel strength in tension (D.5.1)
    # ========================
    Nsa = Ase * inp.futa  # per bolt
    phi_Nsa = phi_steel_t * Nsa
    ratio_1 = Nu_max / phi_Nsa if phi_Nsa > 0 else 999
    res.add("steel_tension", "Steel Strength in Tension (D.5.1)",
            phi_Nsa, Nu_max, phi_steel_t, Nsa, ratio_1,
            "OK" if ratio_1 <= 1.0 else "NG",
            {"Ase": Ase, "futa": inp.futa, "n": 1})

    # ========================
    # 2. Concrete breakout in tension (D.5.2)
    # ========================
    hef = inp.hef
    Anco = 9 * hef ** 2

    # Anc calculation - projected area
    ca_min_x1 = min(inp.cx1, 1.5 * hef)
    ca_min_x2 = min(inp.cx2, 1.5 * hef)
    ca_min_y1 = min(inp.cy1, 1.5 * hef)
    ca_min_y2 = min(inp.cy2, 1.5 * hef)
    sx_eff = min(inp.sx1, 3 * hef)

    Anc_x = ca_min_x1 + sx_eff + ca_min_x2
    Anc_y = ca_min_y1 + ca_min_y2
    Anc = Anc_x * Anc_y
    Anc = min(Anc, n_bolts * Anco)

    # Psi_ec,N
    psi_ecN_x = 1.0 / (1.0 + 2.0 * abs(inp.ex) / (3.0 * hef)) if inp.ex != 0 else 1.0
    psi_ecN_y = 1.0 / (1.0 + 2.0 * abs(inp.ey) / (3.0 * hef)) if inp.ey != 0 else 1.0
    psi_ecN = psi_ecN_x * psi_ecN_y

    # Psi_ed,N
    c_min = min(inp.cx1, inp.cx2, inp.cy1, inp.cy2)
    if c_min >= 1.5 * hef:
        psi_edN = 1.0
    else:
        psi_edN = 0.7 + 0.3 * c_min / (1.5 * hef)

    # Psi_c,N
    psi_cN = 1.25 if not inp.cracking else 1.0

    # Psi_cp,N
    psi_cpN = 1.0  # for cast-in anchors

    # Nb
    kc = KC_CASTIN
    if hef <= 11:
        Nb = kc * lam * math.sqrt(inp.fc) * hef ** 1.5
    else:
        Nb = 16 * lam * math.sqrt(inp.fc) * hef ** (5.0 / 3.0)
    Nb /= 1000.0  # convert from lbs to kips

    Ncbg = (Anc / Anco) * psi_ecN * psi_edN * psi_cN * psi_cpN * Nb
    phi_Ncbg = phi_conc_t * Ncbg
    Nua_group = inp.Nua
    ratio_2 = Nua_group / phi_Ncbg if phi_Ncbg > 0 else 999
    res.add("conc_breakout_tension", "Concrete Breakout in Tension (D.5.2)",
            phi_Ncbg, Nua_group, phi_conc_t, Ncbg, ratio_2,
            "OK" if ratio_2 <= 1.0 else "NG",
            {"Anc": Anc, "Anco": Anco, "psi_ecN": psi_ecN,
             "psi_edN": psi_edN, "psi_cN": psi_cN, "Nb": Nb})

    # ========================
    # 3. Pullout in tension (D.5.3)
    # ========================
    Np = Abrg * 8 * inp.fc / 1000.0  # kips
    psi_cP = 1.4 if not inp.cracking else 1.0
    Npn = psi_cP * Np
    phi_Npn = phi_conc_t * Npn
    ratio_3 = Nu_max / phi_Npn if phi_Npn > 0 else 999
    res.add("pullout_tension", "Pullout Strength in Tension (D.5.3)",
            phi_Npn, Nu_max, phi_conc_t, Npn, ratio_3,
            "OK" if ratio_3 <= 1.0 else "NG",
            {"Abrg": Abrg, "Np": Np, "psi_cP": psi_cP})

    # ========================
    # 4. Side-face blowout (D.5.4)
    # ========================
    ca1_sf = min(inp.cx1, inp.cx2, inp.cy1, inp.cy2)
    if ca1_sf < 0.4 * hef:
        Nsb = 160 * ca1_sf * math.sqrt(Abrg) * lam * math.sqrt(inp.fc) / 1000.0
        ca2_sf = max(inp.cx1, inp.cx2, inp.cy1, inp.cy2)
        ratio_ca = ca2_sf / ca1_sf if ca1_sf > 0 else 999
        if ratio_ca < 3.0:
            factor_sf = (1 + ratio_ca) / 4.0
        else:
            factor_sf = 1.0
        Nsb *= factor_sf
        phi_Nsb = phi_conc_t * Nsb
        ratio_4 = Nu_max / phi_Nsb if phi_Nsb > 0 else 999
        res.add("sideface_blowout", "Side-Face Blowout (D.5.4)",
                phi_Nsb, Nu_max, phi_conc_t, Nsb, ratio_4,
                "OK" if ratio_4 <= 1.0 else "NG")
    else:
        res.add_na("sideface_blowout", "Side-Face Blowout (D.5.4)",
                    "ca1 >= 0.4*hef => N/A")

    # ========================
    # 5. Steel strength in shear (D.6.1)
    # ========================
    Vsa = Ase * inp.futa  # per bolt
    phi_Vsa = phi_steel_v * Vsa
    ratio_5 = Vu_max / phi_Vsa if phi_Vsa > 0 else 999
    res.add("steel_shear", "Steel Strength in Shear (D.6.1)",
            phi_Vsa, Vu_max, phi_steel_v, Vsa, ratio_5,
            "OK" if ratio_5 <= 1.0 else "NG",
            {"Ase_V": Ase, "futa": inp.futa})

    # ========================
    # 6. Concrete breakout in shear (D.6.2) - Multiple directions
    # ========================
    da = inp.db
    le = min(hef, 8 * da)
    psi_cV = 1.4 if not inp.cracking else 1.0

    def calc_shear_breakout(ca1, ca2a, ca2b, ha, Vu, e_v, sx=0, is_group_perp=True):
        """Calculate Vcbg for one direction."""
        if ca1 <= 0:
            return None

        Avco = 4.5 * ca1 ** 2

        if is_group_perp and sx > 0:
            Avc_w = min(1.5 * ca1, ca2a) + min(3 * ca1, sx) + min(1.5 * ca1, ca2b)
        else:
            Avc_w = min(1.5 * ca1, ca2a) + min(1.5 * ca1, ca2b)

        Avc_h = min(1.5 * ca1, ha)
        Avc = Avc_w * Avc_h

        psi_ecV = 1.0 / (1.0 + 2.0 * abs(e_v) / (3.0 * ca1)) if e_v != 0 else 1.0
        psi_edV = 1.0 if ca2a >= 1.5 * ca1 and ca2b >= 1.5 * ca1 else \
            0.7 + 0.3 * min(ca2a, ca2b) / (1.5 * ca1)
        psi_hV = min(1.0, math.sqrt(1.5 * ca1 / ha)) if ha < 1.5 * ca1 else 1.0

        Vb = 7.0 * (le / da) ** 0.2 * math.sqrt(da) * lam * math.sqrt(inp.fc) * ca1 ** 1.5 / 1000.0

        Vcbg = (Avc / Avco) * psi_ecV * psi_edV * psi_cV * psi_hV * Vb
        return Vcbg

    # Determine ca1 values considering D.6.2.4 max spacing rule
    # X-direction perpendicular: ca1 = cx1 (or cx2), check if needs adjustment
    def adj_ca1(ca1_raw, ca2a, ca2b, sx, ha):
        """Adjust ca1 per Section D.6.2.4."""
        max_of = max(ca2a, ca2b, sx if sx > 0 else 0, ha)
        ca1_max = max_of / 1.5
        # Per D.6.2.4: if ca1 > max(ca2/1.5, s/3, ha/1.5), use adjusted
        limit = max(ca2a / 1.5, ca2b / 1.5, ha / 1.5)
        if sx > 0:
            limit = max(limit, sx / 3.0)
        return min(ca1_raw, limit) if ca1_raw > limit else ca1_raw

    # (-) X-Direction perpendicular: ca1 based on cx1 side
    ca1_xn_raw = inp.cx1 + inp.sx1  # rear bolt for 2-bolt case
    ca1_xn = adj_ca1(ca1_xn_raw, inp.cy1, inp.cy2, 0, inp.ha)
    Vcbg_xn = calc_shear_breakout(ca1_xn, inp.cy1, inp.cy2, inp.ha,
                                   inp.Vua_x, inp.ey, 0, False)

    # (+) X-Direction perpendicular
    ca1_xp_raw = inp.cx2 + inp.sx1
    ca1_xp = adj_ca1(ca1_xp_raw, inp.cy1, inp.cy2, 0, inp.ha)
    Vcbg_xp = calc_shear_breakout(ca1_xp, inp.cy1, inp.cy2, inp.ha,
                                   inp.Vua_x, inp.ey, 0, False)

    # (-) Y-Direction perpendicular
    ca1_yn = adj_ca1(inp.cy1, inp.cx1, inp.cx2, inp.sx1, inp.ha)
    Vcbg_yn = calc_shear_breakout(ca1_yn, inp.cx1, inp.cx2, inp.ha,
                                   inp.Vua_y, inp.ex, inp.sx1, True)

    # (+) Y-Direction perpendicular
    ca1_yp = adj_ca1(inp.cy2, inp.cx1, inp.cx2, inp.sx1, inp.ha)
    Vcbg_yp = calc_shear_breakout(ca1_yp, inp.cx1, inp.cx2, inp.ha,
                                   inp.Vua_y, inp.ex, inp.sx1, True)

    # Governing X breakout (perpendicular)
    Vcbg_x_perp = min(v for v in [Vcbg_xn, Vcbg_xp] if v is not None) if Vcbg_xn and Vcbg_xp else 0
    phi_Vcbg_x = phi_conc_v * Vcbg_x_perp
    ratio_6x = inp.Vua_x / phi_Vcbg_x if phi_Vcbg_x > 0 and inp.Vua_x > 0 else 0
    res.add("conc_breakout_shear_x_perp", "Breakout in Shear X-Perp (D.6.2)",
            phi_Vcbg_x, inp.Vua_x, phi_conc_v, Vcbg_x_perp, ratio_6x,
            "OK" if ratio_6x <= 1.0 else "NG")

    # Governing Y breakout (perpendicular)
    Vcbg_y_perp = min(v for v in [Vcbg_yn, Vcbg_yp] if v is not None) if Vcbg_yn and Vcbg_yp else 0
    phi_Vcbg_y = phi_conc_v * Vcbg_y_perp
    ratio_6y = inp.Vua_y / phi_Vcbg_y if phi_Vcbg_y > 0 and inp.Vua_y > 0 else 0
    res.add("conc_breakout_shear_y_perp", "Breakout in Shear Y-Perp (D.6.2)",
            phi_Vcbg_y, inp.Vua_y, phi_conc_v, Vcbg_y_perp, ratio_6y,
            "OK" if ratio_6y <= 1.0 else "NG")

    # Parallel edge: capacity = 2x perpendicular capacity
    Vcbg_x_par = 2 * Vcbg_y_perp if Vcbg_y_perp else 0
    phi_Vcbg_x_par = phi_conc_v * Vcbg_x_par
    ratio_6xp = inp.Vua_x / phi_Vcbg_x_par if phi_Vcbg_x_par > 0 and inp.Vua_x > 0 else 0
    res.add("conc_breakout_shear_x_par", "Breakout in Shear X-Parallel (D.6.2)",
            phi_Vcbg_x_par, inp.Vua_x, phi_conc_v, Vcbg_x_par, ratio_6xp,
            "OK" if ratio_6xp <= 1.0 else "NG")

    Vcbg_y_par = 2 * Vcbg_x_perp if Vcbg_x_perp else 0
    phi_Vcbg_y_par = phi_conc_v * Vcbg_y_par
    ratio_6yp = inp.Vua_y / phi_Vcbg_y_par if phi_Vcbg_y_par > 0 and inp.Vua_y > 0 else 0
    res.add("conc_breakout_shear_y_par", "Breakout in Shear Y-Parallel (D.6.2)",
            phi_Vcbg_y_par, inp.Vua_y, phi_conc_v, Vcbg_y_par, ratio_6yp,
            "OK" if ratio_6yp <= 1.0 else "NG")

    # ========================
    # 7. Pryout strength in shear (D.6.3)
    # ========================
    kcp = 2.0 if hef >= 2.5 else 1.0
    # Use Ncbg with full group (no eccentricity reduction for pryout)
    Ncbg_pryout = (Anc / Anco) * 1.0 * psi_edN * psi_cN * psi_cpN * Nb
    Vcpg = kcp * Ncbg_pryout
    phi_Vcpg = phi_conc_v * Vcpg
    Vu_total = math.sqrt(inp.Vua_x ** 2 + inp.Vua_y ** 2)
    ratio_7 = Vu_total / phi_Vcpg if phi_Vcpg > 0 else 999
    res.add("pryout_shear", "Concrete Pryout in Shear (D.6.3)",
            phi_Vcpg, Vu_total, phi_conc_v, Vcpg, ratio_7,
            "OK" if ratio_7 <= 1.0 else "NG",
            {"kcp": kcp, "Ncbg": Ncbg_pryout})

    # ========================
    # 8. Interaction (D.7)
    # ========================
    # Governing tension
    tension_ratios = []
    for k in ["steel_tension", "conc_breakout_tension", "pullout_tension", "sideface_blowout"]:
        sec = res.sections[k]
        if sec["status"] != "N/A" and sec["ratio"] is not None:
            tension_ratios.append(sec["ratio"])
    max_tension_ratio = max(tension_ratios) if tension_ratios else 0

    # Governing shear
    shear_ratios = []
    for k in ["steel_shear", "conc_breakout_shear_x_perp", "conc_breakout_shear_y_perp",
              "conc_breakout_shear_x_par", "conc_breakout_shear_y_par", "pryout_shear"]:
        sec = res.sections[k]
        if sec["status"] != "N/A" and sec["ratio"] is not None and sec["ratio"] > 0:
            shear_ratios.append(sec["ratio"])
    max_shear_ratio = max(shear_ratios) if shear_ratios else 0

    if max_shear_ratio <= 0.2:
        csr = max_tension_ratio
        interaction_note = "Vua/ΦVn ≤ 0.2 → Full tension check only"
    elif max_tension_ratio <= 0.2:
        csr = max_shear_ratio
        interaction_note = "Nua/ΦNn ≤ 0.2 → Full shear check only"
    else:
        csr = max_tension_ratio + max_shear_ratio
        interaction_note = "Nua/ΦNn + Vua/ΦVn ≤ 1.2"

    interaction_ok = csr <= 1.2
    res.add("interaction", "Interaction Check (D.7)",
            1.2, csr, None, None, csr / 1.2,
            "OK" if interaction_ok else "NG",
            {"tension_ratio": max_tension_ratio, "shear_ratio": max_shear_ratio,
             "csr": csr, "note": interaction_note})

    # ========================
    # 9. Dimensional checks
    # ========================
    # Minimum spacing
    s_min = 4 * da
    s_act = inp.sx1
    spacing_ok = s_act >= s_min

    # Minimum concrete edge
    conc_edge_min = 6 * da  # conservative for torqued
    conc_edge_act = min(inp.cx1, inp.cx2, inp.cy1, inp.cy2)
    conc_edge_ok = conc_edge_act >= conc_edge_min

    # Minimum steel edge
    steel_edge_min = MIN_STEEL_EDGE.get(round(inp.db, 3), 0.875)
    steel_edge_act = min(inp.bx1, inp.bx2, inp.by1, inp.by2)
    steel_edge_ok = steel_edge_act >= steel_edge_min

    # Minimum thickness
    ha_min = hef + 0.75
    thickness_ok = inp.ha >= ha_min

    res.sections["dim_spacing"] = {
        "label": "Minimum Spacing", "status": "OK" if spacing_ok else "NG",
        "details": {"s_min": s_min, "s_act": s_act},
        "capacity": None, "demand": None, "phi": None, "nominal": None, "ratio": None,
    }
    res.sections["dim_conc_edge"] = {
        "label": "Minimum Concrete Edge Distance", "status": "OK" if conc_edge_ok else "NG",
        "details": {"min": conc_edge_min, "act": conc_edge_act},
        "capacity": None, "demand": None, "phi": None, "nominal": None, "ratio": None,
    }
    res.sections["dim_steel_edge"] = {
        "label": "Minimum Steel Edge Distance", "status": "OK" if steel_edge_ok else "NG",
        "details": {"min": steel_edge_min, "act": steel_edge_act},
        "capacity": None, "demand": None, "phi": None, "nominal": None, "ratio": None,
    }
    res.sections["dim_thickness"] = {
        "label": "Minimum Concrete Thickness", "status": "OK" if thickness_ok else "NG",
        "details": {"ha_min": ha_min, "ha": inp.ha},
        "capacity": None, "demand": None, "phi": None, "nominal": None, "ratio": None,
    }

    if not (spacing_ok and conc_edge_ok and steel_edge_ok and thickness_ok):
        res.overall_status = "NG"

    # ========================
    # 10. Bearing (Section 10.14)
    # ========================
    A1 = (inp.bx1 + inp.sx1 + inp.bx2) * (inp.by1 + inp.by2)
    A2 = (inp.cx1 + inp.sx1 + inp.cx2) * (inp.cy1 + inp.cy2)
    mult_factor = min(math.sqrt(A2 / A1) if A1 > 0 else 2.0, 2.0)
    Pn_bearing = 0.85 * (inp.fc / 1000.0) * A1 * mult_factor
    phi_Pn = 0.65 * Pn_bearing
    ratio_10 = inp.Nua / phi_Pn if phi_Pn > 0 and inp.Nua > 0 else 0
    res.add("bearing", "Plate Bearing (Sec 10.14)",
            phi_Pn, inp.Nua, 0.65, Pn_bearing, ratio_10,
            "OK" if ratio_10 <= 1.0 else "NG",
            {"A1": A1, "A2": A2, "mult_factor": mult_factor})

    # ========================
    # 11. Punching shear (Section 11.12.2.1)
    # ========================
    bo = 2 * ((inp.bx1 + inp.sx1 + inp.bx2) + (inp.by1 + inp.by2))
    d_punch = inp.ha - 2.0  # assume 2" cover
    if d_punch > 0:
        long_side = max(inp.bx1 + inp.sx1 + inp.bx2, inp.by1 + inp.by2)
        short_side = min(inp.bx1 + inp.sx1 + inp.bx2, inp.by1 + inp.by2)
        beta_punch = long_side / short_side if short_side > 0 else 2.0
        factor_punch = min(2 + 4 / beta_punch, 4.0)
        Vc_punch = factor_punch * math.sqrt(inp.fc) * bo * d_punch / 1000.0
        phi_Vc = 0.65 * Vc_punch  # phi for shear
        ratio_11 = inp.Nua / phi_Vc if phi_Vc > 0 and inp.Nua > 0 else 0
        res.add("punching_shear", "Punching Shear (Sec 11.12)",
                phi_Vc, inp.Nua, 0.65, Vc_punch, ratio_11,
                "OK" if ratio_11 <= 1.0 else "NG",
                {"bo": bo, "d": d_punch, "beta": beta_punch, "factor": factor_punch})
    else:
        res.add_na("punching_shear", "Punching Shear (Sec 11.12)", "d <= 0")

    # Store bolt reactions for reporting
    res.sections["_bolt_reactions"] = {
        "axial": axial_reactions, "shear": shear_reactions,
        "Nu_max": Nu_max, "Vu_max": Vu_max,
    }

    return res
