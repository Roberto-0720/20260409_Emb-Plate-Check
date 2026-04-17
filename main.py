#!/usr/bin/env python3
"""
EmbedPlate — Embedded Plate Anchorage Design Tool
Per ACI 318-08, Appendix D

Usage:
    python main.py
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from ui.mainwindow import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setApplicationName("EmbedPlate")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
