"""
Input panel widget for the Embedded Plate Tool.
All user-facing units: kN, mm, MPa.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton, QScrollArea,
    QFrame, QSizePolicy,
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QDoubleValidator

from data import STUD_DIAMETERS_MM, STUD_DIAMETERS_IN


class FloatInput(QLineEdit):
    """Styled float input field."""

    def __init__(self, default=0.0, suffix="", parent=None):
        super().__init__(parent)
        self.setValidator(QDoubleValidator(-1e9, 1e9, 4))
        self.setText(str(default))
        self.setFixedWidth(100)
        self.setAlignment(Qt.AlignRight)
        self.setStyleSheet("""
            QLineEdit {
                background: #1e2a38;
                color: #e0e6ed;
                border: 1px solid #3a4f65;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
            }
        """)

    def value(self):
        try:
            return float(self.text())
        except ValueError:
            return 0.0


class InputPanel(QWidget):
    """Left-side input panel collecting all design parameters."""

    calculate_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _section_label(self, text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl.setStyleSheet("color: #3498db; margin-top: 8px; margin-bottom: 2px;")
        return lbl

    def _unit_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        lbl.setFixedWidth(40)
        return lbl

    def _param_row(self, grid, row, label_text, default, unit_text):
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #bdc3c7; font-size: 13px;")
        inp = FloatInput(default)
        unit = self._unit_label(unit_text)
        grid.addWidget(lbl, row, 0)
        grid.addWidget(inp, row, 1)
        grid.addWidget(unit, row, 2)
        return inp

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: #15202e; width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #3a4f65; border-radius: 4px; min-height: 30px;
            }
        """)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(6)

        # === PROJECT INFO ===
        main_layout.addWidget(self._section_label("📋 Project Info"))
        grid_info = QGridLayout()
        grid_info.setSpacing(4)
        self.inp_project = FloatInput.__new__(FloatInput)
        QLineEdit.__init__(self.inp_project)
        self.inp_project.setPlaceholderText("Project Name")
        self.inp_project.setStyleSheet("""QLineEdit { background: #1e2a38; color: #e0e6ed;
            border: 1px solid #3a4f65; border-radius: 4px; padding: 4px 8px; font-size: 13px; }""")
        self.inp_subject = FloatInput.__new__(FloatInput)
        QLineEdit.__init__(self.inp_subject)
        self.inp_subject.setPlaceholderText("Subject")
        self.inp_subject.setStyleSheet(self.inp_project.styleSheet())
        self.inp_engineer = FloatInput.__new__(FloatInput)
        QLineEdit.__init__(self.inp_engineer)
        self.inp_engineer.setPlaceholderText("Engineer")
        self.inp_engineer.setStyleSheet(self.inp_project.styleSheet())

        grid_info.addWidget(QLabel("Project:"), 0, 0)
        grid_info.addWidget(self.inp_project, 0, 1, 1, 2)
        grid_info.addWidget(QLabel("Subject:"), 1, 0)
        grid_info.addWidget(self.inp_subject, 1, 1, 1, 2)
        grid_info.addWidget(QLabel("Engineer:"), 2, 0)
        grid_info.addWidget(self.inp_engineer, 2, 1, 1, 2)
        for i in range(3):
            grid_info.itemAtPosition(i, 0).widget().setStyleSheet("color:#bdc3c7;font-size:13px;")
        main_layout.addLayout(grid_info)

        # === LOADS ===
        main_layout.addWidget(self._section_label("⚡ Applied Loads"))
        grid_loads = QGridLayout()
        grid_loads.setSpacing(4)
        self.inp_Nua = self._param_row(grid_loads, 0, "Nua (Tension)", 28.91, "kN")
        self.inp_Vua_x = self._param_row(grid_loads, 1, "Vua,x (Shear X)", 22.24, "kN")
        self.inp_Vua_y = self._param_row(grid_loads, 2, "Vua,y (Shear Y)", 22.24, "kN")
        self.inp_ex = self._param_row(grid_loads, 3, "ex (Eccentricity X)", 25.4, "mm")
        self.inp_ey = self._param_row(grid_loads, 4, "ey (Eccentricity Y)", 0.0, "mm")
        main_layout.addLayout(grid_loads)

        # === PLATE DIMENSIONS ===
        main_layout.addWidget(self._section_label("📐 Plate Edge Distances"))
        grid_plate = QGridLayout()
        grid_plate.setSpacing(4)
        self.inp_bx1 = self._param_row(grid_plate, 0, "bx1", 50.8, "mm")
        self.inp_bx2 = self._param_row(grid_plate, 1, "bx2", 50.8, "mm")
        self.inp_by1 = self._param_row(grid_plate, 2, "by1", 50.8, "mm")
        self.inp_by2 = self._param_row(grid_plate, 3, "by2", 50.8, "mm")
        main_layout.addLayout(grid_plate)

        # === STUD SPACING ===
        main_layout.addWidget(self._section_label("↔️ Stud Spacing"))
        grid_sp = QGridLayout()
        grid_sp.setSpacing(4)
        self.inp_sx1 = self._param_row(grid_sp, 0, "sx1 (X-dir spacing)", 101.6, "mm")
        main_layout.addLayout(grid_sp)

        # === CONCRETE EDGES ===
        main_layout.addWidget(self._section_label("🧱 Concrete Edge Distances"))
        grid_conc = QGridLayout()
        grid_conc.setSpacing(4)
        self.inp_cx1 = self._param_row(grid_conc, 0, "cx1", 1219.2, "mm")
        self.inp_cx2 = self._param_row(grid_conc, 1, "cx2", 1219.2, "mm")
        self.inp_cy1 = self._param_row(grid_conc, 2, "cy1", 304.8, "mm")
        self.inp_cy2 = self._param_row(grid_conc, 3, "cy2", 1117.6, "mm")
        main_layout.addLayout(grid_conc)

        # === PARAMETERS ===
        main_layout.addWidget(self._section_label("⚙️ Material & Anchor Parameters"))
        grid_param = QGridLayout()
        grid_param.setSpacing(4)

        # Stud diameter combo
        lbl_db = QLabel("Stud Diameter")
        lbl_db.setStyleSheet("color: #bdc3c7; font-size: 13px;")
        self.combo_db = QComboBox()
        for d_mm, d_in in zip(STUD_DIAMETERS_MM, STUD_DIAMETERS_IN):
            self.combo_db.addItem(f"{d_mm:.2f} mm  ({d_in:.3f}\")", d_mm)
        self.combo_db.setCurrentIndex(2)  # 12.7mm = 0.5"
        self.combo_db.setStyleSheet("""
            QComboBox { background: #1e2a38; color: #e0e6ed; border: 1px solid #3a4f65;
                        border-radius: 4px; padding: 4px 8px; font-size: 13px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #1e2a38; color: #e0e6ed;
                        selection-background-color: #2c3e50; }
        """)
        grid_param.addWidget(lbl_db, 0, 0)
        grid_param.addWidget(self.combo_db, 0, 1, 1, 2)

        self.inp_fc = self._param_row(grid_param, 1, "f'c (Concrete)", 20.68, "MPa")
        self.inp_fy = self._param_row(grid_param, 2, "fy (Yield)", 248.2, "MPa")
        self.inp_futa = self._param_row(grid_param, 3, "futa (Tensile)", 399.9, "MPa")
        self.inp_hef = self._param_row(grid_param, 4, "hef (Embedment)", 241.3, "mm")
        self.inp_ha = self._param_row(grid_param, 5, "ha (Thickness)", 304.8, "mm")
        main_layout.addLayout(grid_param)

        # === OPTIONS ===
        main_layout.addWidget(self._section_label("🔧 Design Options"))
        chk_style = "QCheckBox { color: #bdc3c7; font-size: 13px; } QCheckBox::indicator { width:16px; height:16px; }"

        self.combo_ductile = QComboBox()
        self.combo_ductile.addItems(["Ductile", "Brittle"])
        self.combo_ductile.setStyleSheet(self.combo_db.styleSheet())
        duct_row = QHBoxLayout()
        duct_lbl = QLabel("Steel Element:")
        duct_lbl.setStyleSheet("color: #bdc3c7; font-size: 13px;")
        duct_row.addWidget(duct_lbl)
        duct_row.addWidget(self.combo_ductile)
        duct_row.addStretch()
        main_layout.addLayout(duct_row)

        self.combo_conc_type = QComboBox()
        self.combo_conc_type.addItems(["Normalwt", "Sandlwt", "Allwt"])
        self.combo_conc_type.setStyleSheet(self.combo_db.styleSheet())
        ct_row = QHBoxLayout()
        ct_lbl = QLabel("Concrete Type:")
        ct_lbl.setStyleSheet("color: #bdc3c7; font-size: 13px;")
        ct_row.addWidget(ct_lbl)
        ct_row.addWidget(self.combo_conc_type)
        ct_row.addStretch()
        main_layout.addLayout(ct_row)

        self.chk_supp_reinf = QCheckBox("Supplementary Reinforcement")
        self.chk_supp_reinf.setStyleSheet(chk_style)
        self.chk_cracking = QCheckBox("Cracking Anticipated")
        self.chk_cracking.setStyleSheet(chk_style)
        self.chk_seismic = QCheckBox("Seismic Category C/D/E/F")
        self.chk_seismic.setStyleSheet(chk_style)
        self.chk_D623 = QCheckBox("Per Section D.6.2.3")
        self.chk_D623.setStyleSheet(chk_style)
        main_layout.addWidget(self.chk_supp_reinf)
        main_layout.addWidget(self.chk_cracking)
        main_layout.addWidget(self.chk_seismic)
        main_layout.addWidget(self.chk_D623)

        main_layout.addStretch()

        # === CALCULATE BUTTON ===
        self.btn_calc = QPushButton("▶  CALCULATE")
        self.btn_calc.setFixedHeight(44)
        self.btn_calc.setCursor(Qt.PointingHandCursor)
        self.btn_calc.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #2980b9, stop:1 #3498db);
                color: white; font-size: 15px; font-weight: bold;
                border: none; border-radius: 6px;
            }
            QPushButton:hover { background: #3498db; }
            QPushButton:pressed { background: #2471a3; }
        """)
        self.btn_calc.clicked.connect(self._on_calculate)
        main_layout.addWidget(self.btn_calc)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _on_calculate(self):
        data = {
            "Nua": self.inp_Nua.value(),
            "Vua_x": self.inp_Vua_x.value(),
            "Vua_y": self.inp_Vua_y.value(),
            "ex": self.inp_ex.value(),
            "ey": self.inp_ey.value(),
            "bx1": self.inp_bx1.value(),
            "bx2": self.inp_bx2.value(),
            "by1": self.inp_by1.value(),
            "by2": self.inp_by2.value(),
            "sx1": self.inp_sx1.value(),
            "cx1": self.inp_cx1.value(),
            "cx2": self.inp_cx2.value(),
            "cy1": self.inp_cy1.value(),
            "cy2": self.inp_cy2.value(),
            "db": self.combo_db.currentData(),
            "fc": self.inp_fc.value(),
            "fy": self.inp_fy.value(),
            "futa": self.inp_futa.value(),
            "hef": self.inp_hef.value(),
            "ha": self.inp_ha.value(),
            "steel_element": self.combo_ductile.currentText(),
            "supp_reinf": self.chk_supp_reinf.isChecked(),
            "cracking": self.chk_cracking.isChecked(),
            "seismic": self.chk_seismic.isChecked(),
            "concrete_type": self.combo_conc_type.currentText(),
            "per_D623": self.chk_D623.isChecked(),
        }
        self.calculate_requested.emit(data)

    def get_project_info(self):
        return {
            "project": self.inp_project.text(),
            "subject": self.inp_subject.text(),
            "engineer": self.inp_engineer.text(),
        }
