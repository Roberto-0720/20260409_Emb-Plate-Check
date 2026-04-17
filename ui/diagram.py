"""
Plate diagram widget — renders a schematic SVG of the embedded plate configuration.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QBrush
import math


class PlateDiagram(QWidget):
    """Draws a plan-view schematic of the 2-stud embedded plate."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 250)
        self.params = None

    def set_params(self, params):
        """params dict with bx1, bx2, by1, by2, sx1, cx1, cx2, cy1, cy2 in mm."""
        self.params = params
        self.update()

    def paintEvent(self, event):
        if not self.params:
            return

        p = self.params
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 40

        # Compute total concrete and plate sizes
        plate_w = p["bx1"] + p["sx1"] + p["bx2"]
        plate_h = p["by1"] + p["by2"]
        conc_w = p["cx1"] + p["sx1"] + p["cx2"]
        conc_h = p["cy1"] + p["cy2"]

        # Scale to fit
        draw_w = w - 2 * margin
        draw_h = h - 2 * margin
        scale = min(draw_w / max(conc_w, 1), draw_h / max(conc_h, 1))

        def tx(x_mm):
            return margin + (x_mm / max(conc_w, 1)) * draw_w

        def ty(y_mm):
            return margin + (y_mm / max(conc_h, 1)) * draw_h

        # Draw concrete outline
        painter.setPen(QPen(QColor("#5d6d7e"), 2, Qt.DashLine))
        painter.setBrush(QBrush(QColor("#1a2636")))
        painter.drawRect(int(tx(0)), int(ty(0)),
                         int(conc_w * scale), int(conc_h * scale))

        # Draw plate
        plate_x0 = p["cx1"] - p["bx1"]
        plate_y0 = p["cy1"] - p["by1"]
        painter.setPen(QPen(QColor("#3498db"), 2))
        painter.setBrush(QBrush(QColor(52, 152, 219, 60)))
        painter.drawRect(int(tx(plate_x0)), int(ty(plate_y0)),
                         int(plate_w * scale), int(plate_h * scale))

        # Draw studs
        stud_r = max(4, int(6 * scale / max(conc_w, 1) * 100))
        stud_positions = [
            (p["cx1"], p["cy1"]),  # bolt 1
            (p["cx1"] + p["sx1"], p["cy1"]),  # bolt 2
        ]
        painter.setPen(QPen(QColor("#e74c3c"), 2))
        painter.setBrush(QBrush(QColor("#e74c3c")))
        for sx, sy in stud_positions:
            cx_px = int(tx(sx))
            cy_px = int(ty(sy))
            painter.drawEllipse(cx_px - stud_r, cy_px - stud_r, 2 * stud_r, 2 * stud_r)

        # Labels
        painter.setPen(QColor("#bdc3c7"))
        painter.setFont(QFont("Segoe UI", 8))

        # Dimension labels
        cx_mid = int(tx(p["cx1"] / 2))
        painter.drawText(cx_mid - 15, int(ty(0)) - 5, f"cx1={p['cx1']:.0f}")

        cy_mid = int(ty(p["cy1"] / 2))
        painter.drawText(int(tx(0)) - 38, cy_mid, f"cy1={p['cy1']:.0f}")

        # sx1 label
        sx_x = int(tx(p["cx1"] + p["sx1"] / 2))
        painter.drawText(sx_x - 15, int(ty(p["cy1"])) + stud_r + 15, f"sx1={p['sx1']:.0f}")

        painter.end()
