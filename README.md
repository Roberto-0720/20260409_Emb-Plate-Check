# EmbedPlate — Embedded Plate Anchorage Design Tool

**ACI 318-08, Appendix D — Design of (2) Headed Concrete Anchor Stud Plate**

## Overview

Professional GUI tool for designing embedded plates with headed concrete anchors per ACI 318-08 Appendix D. Calculates embedment strength checks including tension, shear, interaction, and dimensional requirements.

## Features

- **11 Design Checks** per ACI 318-08 Appendix D:
  1. Steel strength in tension (D.5.1)
  2. Concrete breakout in tension (D.5.2)
  3. Pullout strength in tension (D.5.3)
  4. Side-face blowout (D.5.4)
  5. Steel strength in shear (D.6.1)
  6. Concrete breakout in shear — X & Y, perpendicular & parallel (D.6.2)
  7. Concrete pryout in shear (D.6.3)
  8. Tension-shear interaction (D.7)
  9. Dimensional requirements (D.8)
  10. Plate bearing (Section 10.14)
  11. Punching shear (Section 11.12)

- **SI Units**: kN, mm, MPa throughout the interface
- **Dark-themed dashboard** with color-coded status indicators
- **Interactive plate diagram** showing anchor configuration
- **HTML report export** with full calculation summary
- **Elastic bolt group analysis** for load distribution

## Project Structure

```
embedded_plate_tool/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── data/
│   └── __init__.py      # Stud tables, phi factors, unit conversions
├── ui/
│   ├── __init__.py      # UI package
│   ├── mainwindow.py    # Main application window
│   ├── input_panel.py   # Input form panel
│   ├── results_panel.py # Results dashboard
│   └── diagram.py       # Plate schematic diagram
├── util/
│   ├── __init__.py      # Calculation engine (ACI 318-08 App. D)
│   └── export.py        # HTML report generator
├── resource/            # Images, logos, custom assets
└── .claude/             # Project configuration
```

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Design References

1. ACI 318-08, Building Code Requirements for Structural Concrete
2. PCI Design Handbook, 6th Edition (Stud dimensions, Table 6.5.1.2)

## Units Convention

- All user-facing inputs/outputs: **kN, mm, MPa**
- Internal calculations: imperial (kips, inches, psi) — converted at I/O boundary

## Extending

- Add new stud sizes: edit `data/__init__.py` → `STUD_TABLE`
- Add new checks: extend `util/__init__.py` → `calculate()` function
- Customize report: edit `util/export.py`
- Add images/logos: place files in `resource/` directory
