"""
Results panel — displays calculation results in a professional dashboard style.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QGridLayout, QProgressBar, QPushButton, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from data import KIPS_TO_KN, IN_TO_MM


class StatusBadge(QLabel):
    """Colored status badge."""

    def __init__(self, status="—", parent=None):
        super().__init__(status, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(60, 26)
        self.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.set_status(status)

    def set_status(self, status):
        colors = {
            "OK": ("#27ae60", "#e8f8f0"),
            "NG": ("#e74c3c", "#fdedec"),
            "N/A": ("#95a5a6", "#ebedef"),
        }
        fg, bg = colors.get(status, ("#95a5a6", "#ebedef"))
        self.setText(status)
        self.setStyleSheet(f"""
            background: {bg}; color: {fg}; border-radius: 4px;
            padding: 2px 8px; font-weight: bold;
        """)


class RatioBar(QWidget):
    """Visual ratio bar 0-1.2+."""

    def __init__(self, ratio=0.0, parent=None):
        super().__init__(parent)
        self.setFixedHeight(20)
        self.setMinimumWidth(120)
        self.ratio = ratio
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.bar = QProgressBar()
        self.bar.setRange(0, 120)
        self.bar.setValue(min(int(self.ratio * 100), 120))
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(14)

        if self.ratio <= 0.7:
            color = "#27ae60"
        elif self.ratio <= 1.0:
            color = "#f39c12"
        else:
            color = "#e74c3c"

        self.bar.setStyleSheet(f"""
            QProgressBar {{ background: #1e2a38; border-radius: 3px; border: none; }}
            QProgressBar::chunk {{ background: {color}; border-radius: 3px; }}
        """)
        self.lbl = QLabel(f"{self.ratio:.3f}")
        self.lbl.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")
        self.lbl.setFixedWidth(50)
        self.lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(self.bar, 1)
        layout.addWidget(self.lbl)

    def set_ratio(self, ratio):
        self.ratio = ratio
        val = min(int(ratio * 100), 120)
        self.bar.setValue(val)
        if ratio <= 0.7:
            color = "#27ae60"
        elif ratio <= 1.0:
            color = "#f39c12"
        else:
            color = "#e74c3c"
        self.bar.setStyleSheet(f"""
            QProgressBar {{ background: #1e2a38; border-radius: 3px; border: none; }}
            QProgressBar::chunk {{ background: {color}; border-radius: 3px; }}
        """)
        self.lbl.setText(f"{ratio:.3f}")
        self.lbl.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")


class ResultsPanel(QWidget):
    """Right-side results dashboard."""

    export_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

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

        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(12, 8, 12, 8)
        self.main_layout.setSpacing(10)

        # Overall status
        self.overall_frame = QFrame()
        self.overall_frame.setFixedHeight(60)
        self.overall_frame.setStyleSheet("""
            QFrame { background: #1a2636; border: 2px solid #3a4f65;
                     border-radius: 8px; }
        """)
        of_layout = QHBoxLayout(self.overall_frame)
        self.overall_label = QLabel("OVERALL STATUS")
        self.overall_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.overall_label.setStyleSheet("color: #7f8c8d;")
        self.overall_badge = StatusBadge("—")
        self.overall_badge.setFixedSize(80, 34)
        self.overall_badge.setFont(QFont("Segoe UI", 13, QFont.Bold))
        of_layout.addWidget(self.overall_label)
        of_layout.addStretch()
        of_layout.addWidget(self.overall_badge)
        self.main_layout.addWidget(self.overall_frame)

        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Check", "ΦRn (kN)", "Demand (kN)", "Ratio", "Status"])
        self.table.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background: #1a2636; color: #3498db; font-weight: bold; "
            "border: 1px solid #2c3e50; padding: 6px; font-size: 12px; }"
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setStyleSheet("""
            QTableWidget {
                background: #15202e; color: #e0e6ed; gridline-color: #2c3e50;
                border: 1px solid #2c3e50; border-radius: 4px; font-size: 12px;
            }
            QTableWidget::item { padding: 4px; }
        """)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 5):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.main_layout.addWidget(self.table)

        # Dimensional checks table
        dim_label = QLabel("Dimensional Requirements")
        dim_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        dim_label.setStyleSheet("color: #3498db; margin-top: 6px;")
        self.main_layout.addWidget(dim_label)

        self.dim_table = QTableWidget()
        self.dim_table.setColumnCount(3)
        self.dim_table.setHorizontalHeaderLabels(["Check", "Details", "Status"])
        self.dim_table.horizontalHeader().setStyleSheet(
            self.table.horizontalHeader().styleSheet()
        )
        self.dim_table.verticalHeader().setVisible(False)
        self.dim_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dim_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.dim_table.setStyleSheet(self.table.styleSheet())
        dh = self.dim_table.horizontalHeader()
        dh.setSectionResizeMode(0, QHeaderView.Stretch)
        dh.setSectionResizeMode(1, QHeaderView.Stretch)
        dh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.main_layout.addWidget(self.dim_table)

        self.main_layout.addStretch()

        # Export button
        self.btn_export = QPushButton("📄  Export Report")
        self.btn_export.setFixedHeight(40)
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background: #1a2636; color: #3498db; font-size: 14px; font-weight: bold;
                border: 2px solid #3498db; border-radius: 6px;
            }
            QPushButton:hover { background: #2c3e50; }
        """)
        self.btn_export.clicked.connect(self.export_requested.emit)
        self.main_layout.addWidget(self.btn_export)

        scroll.setWidget(self.container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def update_results(self, results):
        """Populate tables from Results object."""
        # Overall
        self.overall_badge.set_status(results.overall_status)
        border_color = "#27ae60" if results.overall_status == "OK" else "#e74c3c"
        self.overall_frame.setStyleSheet(f"""
            QFrame {{ background: #1a2636; border: 2px solid {border_color};
                      border-radius: 8px; }}
        """)

        # Embedment strength table
        embed_keys = [
            "steel_tension", "conc_breakout_tension", "pullout_tension",
            "sideface_blowout", "steel_shear",
            "conc_breakout_shear_x_perp", "conc_breakout_shear_y_perp",
            "conc_breakout_shear_x_par", "conc_breakout_shear_y_par",
            "pryout_shear", "interaction", "bearing", "punching_shear",
        ]
        self.table.setRowCount(len(embed_keys))

        for row, key in enumerate(embed_keys):
            sec = results.sections.get(key, {})
            label = sec.get("label", key)
            status = sec.get("status", "N/A")
            ratio = sec.get("ratio")
            cap = sec.get("capacity")
            dem = sec.get("demand")

            # Label
            item_label = QTableWidgetItem(label)
            item_label.setForeground(QColor("#e0e6ed"))
            self.table.setItem(row, 0, item_label)

            # Capacity
            if key == "interaction":
                cap_str = f"{cap:.2f}" if cap is not None else "N/A"
            else:
                cap_str = f"{cap * KIPS_TO_KN:.2f}" if cap is not None else "N/A"
            item_cap = QTableWidgetItem(cap_str)
            item_cap.setTextAlignment(Qt.AlignCenter)
            item_cap.setForeground(QColor("#e0e6ed"))
            self.table.setItem(row, 1, item_cap)

            # Demand
            if key == "interaction":
                dem_str = f"{dem:.3f}" if dem is not None else "N/A"
            else:
                dem_str = f"{dem * KIPS_TO_KN:.2f}" if dem is not None else "N/A"
            item_dem = QTableWidgetItem(dem_str)
            item_dem.setTextAlignment(Qt.AlignCenter)
            item_dem.setForeground(QColor("#e0e6ed"))
            self.table.setItem(row, 2, item_dem)

            # Ratio
            ratio_str = f"{ratio:.3f}" if ratio is not None else "N/A"
            item_ratio = QTableWidgetItem(ratio_str)
            item_ratio.setTextAlignment(Qt.AlignCenter)
            if ratio is not None:
                if ratio <= 0.7:
                    item_ratio.setForeground(QColor("#27ae60"))
                elif ratio <= 1.0:
                    item_ratio.setForeground(QColor("#f39c12"))
                else:
                    item_ratio.setForeground(QColor("#e74c3c"))
            self.table.setItem(row, 3, item_ratio)

            # Status
            colors = {"OK": "#27ae60", "NG": "#e74c3c", "N/A": "#95a5a6"}
            item_status = QTableWidgetItem(status)
            item_status.setTextAlignment(Qt.AlignCenter)
            item_status.setForeground(QColor(colors.get(status, "#95a5a6")))
            font = item_status.font()
            font.setBold(True)
            item_status.setFont(font)
            self.table.setItem(row, 4, item_status)

        self.table.resizeRowsToContents()

        # Dimensional table
        dim_keys = ["dim_spacing", "dim_conc_edge", "dim_steel_edge", "dim_thickness"]
        self.dim_table.setRowCount(len(dim_keys))
        for row, key in enumerate(dim_keys):
            sec = results.sections.get(key, {})
            label = sec.get("label", key)
            status = sec.get("status", "N/A")
            det = sec.get("details", {})
            detail_parts = []
            for k, v in det.items():
                detail_parts.append(f"{k}={v * IN_TO_MM:.1f} mm")
            detail_str = ", ".join(detail_parts)

            item_l = QTableWidgetItem(label)
            item_l.setForeground(QColor("#e0e6ed"))
            self.dim_table.setItem(row, 0, item_l)

            item_d = QTableWidgetItem(detail_str)
            item_d.setForeground(QColor("#bdc3c7"))
            self.dim_table.setItem(row, 1, item_d)

            colors = {"OK": "#27ae60", "NG": "#e74c3c"}
            item_s = QTableWidgetItem(status)
            item_s.setTextAlignment(Qt.AlignCenter)
            item_s.setForeground(QColor(colors.get(status, "#95a5a6")))
            font = item_s.font()
            font.setBold(True)
            item_s.setFont(font)
            self.dim_table.setItem(row, 2, item_s)

        self.dim_table.resizeRowsToContents()
