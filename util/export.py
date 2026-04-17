"""
Report export utility — generates calculation report as HTML file.
"""

import os
import datetime
from data import KIPS_TO_KN, IN_TO_MM


def _to_si_force(val_kips):
    if val_kips is None:
        return "N/A"
    return f"{val_kips * KIPS_TO_KN:.2f}"


def _to_si_len(val_in):
    if val_in is None:
        return "N/A"
    return f"{val_in * IN_TO_MM:.1f}"


def export_html(inp, results, filepath, project_info=None):
    """Export calculation results as a styled HTML report."""
    info = project_info or {}
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    rows_embed = ""
    embed_keys = [
        "steel_tension", "conc_breakout_tension", "pullout_tension",
        "sideface_blowout", "steel_shear",
        "conc_breakout_shear_x_perp", "conc_breakout_shear_y_perp",
        "conc_breakout_shear_x_par", "conc_breakout_shear_y_par",
        "pryout_shear", "interaction",
    ]
    for i, key in enumerate(embed_keys, 1):
        sec = results.sections.get(key, {})
        label = sec.get("label", key)
        status = sec.get("status", "N/A")
        ratio = sec.get("ratio")
        cap = sec.get("capacity")
        dem = sec.get("demand")
        color = "#27ae60" if status == "OK" else ("#e74c3c" if status == "NG" else "#95a5a6")
        ratio_str = f"{ratio:.3f}" if ratio is not None else "N/A"
        cap_str = _to_si_force(cap) if key != "interaction" else (f"{cap:.2f}" if cap else "N/A")
        dem_str = _to_si_force(dem) if key != "interaction" else (f"{dem:.3f}" if dem else "N/A")

        rows_embed += f"""<tr>
            <td>{i}</td><td>{label}</td>
            <td>{cap_str}</td><td>{dem_str}</td>
            <td>{ratio_str}</td>
            <td style="color:{color};font-weight:bold">{status}</td>
        </tr>\n"""

    dim_keys = ["dim_spacing", "dim_conc_edge", "dim_steel_edge", "dim_thickness"]
    rows_dim = ""
    for key in dim_keys:
        sec = results.sections.get(key, {})
        label = sec.get("label", key)
        status = sec.get("status", "N/A")
        det = sec.get("details", {})
        color = "#27ae60" if status == "OK" else "#e74c3c"
        detail_str = ", ".join(f"{k}={_to_si_len(v)} mm" for k, v in det.items())
        rows_dim += f"""<tr>
            <td>{label}</td><td>{detail_str}</td>
            <td style="color:{color};font-weight:bold">{status}</td>
        </tr>\n"""

    overall_color = "#27ae60" if results.overall_status == "OK" else "#e74c3c"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Embedded Plate Calculation Report</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 40px auto; color: #2c3e50; }}
h1 {{ border-bottom: 3px solid #2c3e50; padding-bottom: 10px; }}
h2 {{ color: #34495e; margin-top: 30px; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
th, td {{ border: 1px solid #bdc3c7; padding: 8px 12px; text-align: center; }}
th {{ background: #34495e; color: white; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
.overall {{ font-size: 1.4em; font-weight: bold; color: {overall_color}; padding: 15px;
            border: 3px solid {overall_color}; text-align: center; border-radius: 8px; margin: 20px 0; }}
.info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
.info-grid div {{ background: #ecf0f1; padding: 8px 12px; border-radius: 4px; }}
.info-grid span {{ font-weight: bold; }}
</style>
</head><body>
<h1>Embedded Plate Design — ACI 318-08 Appendix D</h1>
<p><em>Report generated: {now}</em></p>
<div class="info-grid">
    <div><span>Project:</span> {info.get('project', '—')}</div>
    <div><span>Subject:</span> {info.get('subject', '—')}</div>
    <div><span>Engineer:</span> {info.get('engineer', '—')}</div>
    <div><span>Checker:</span> {info.get('checker', '—')}</div>
</div>

<div class="overall">OVERALL: {results.overall_status}</div>

<h2>Input Summary</h2>
<table>
<tr><th>Parameter</th><th>Value</th><th>Unit</th></tr>
<tr><td>Nua (Tension)</td><td>{inp.Nua * KIPS_TO_KN:.2f}</td><td>kN</td></tr>
<tr><td>Vua,x (Shear X)</td><td>{inp.Vua_x * KIPS_TO_KN:.2f}</td><td>kN</td></tr>
<tr><td>Vua,y (Shear Y)</td><td>{inp.Vua_y * KIPS_TO_KN:.2f}</td><td>kN</td></tr>
<tr><td>Stud Diameter</td><td>{inp.db * IN_TO_MM:.1f}</td><td>mm</td></tr>
<tr><td>Embedment Depth (hef)</td><td>{inp.hef * IN_TO_MM:.1f}</td><td>mm</td></tr>
<tr><td>Member Thickness (ha)</td><td>{inp.ha * IN_TO_MM:.1f}</td><td>mm</td></tr>
<tr><td>f'c</td><td>{inp.fc * 0.00689476:.1f}</td><td>MPa</td></tr>
<tr><td>futa</td><td>{inp.futa * 6.89476:.1f}</td><td>MPa</td></tr>
</table>

<h2>Embedment Strength Checks</h2>
<table>
<tr><th>#</th><th>Check</th><th>ΦRn (kN)</th><th>Demand (kN)</th><th>Ratio</th><th>Status</th></tr>
{rows_embed}
</table>

<h2>Dimensional Requirements</h2>
<table>
<tr><th>Check</th><th>Details</th><th>Status</th></tr>
{rows_dim}
</table>

<p style="text-align:center; color:#95a5a6; margin-top:40px;">
Embedded Plate Tool — ACI 318-08 Appendix D | Generated by EmbedPlate Calculator
</p>
</body></html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath
