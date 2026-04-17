"""
Main application window — Embedded Plate Design Tool.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QLabel, QFileDialog, QMessageBox, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.input_panel import InputPanel
from ui.results_panel import ResultsPanel
from ui.diagram import PlateDiagram
from util import InputData, calculate
from util.export import export_html


class MainWindow(QMainWindow):
    """Main application window with input, diagram, and results panels."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EmbedPlate — ACI 318-08 Appendix D Anchorage Design")
        self.setMinimumSize(1280, 750)
        self._current_input = None
        self._current_results = None
        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(52)
        header.setStyleSheet("background: #0d1520; border-bottom: 1px solid #2c3e50;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)

        logo = QLabel("⬡ EmbedPlate")
        logo.setFont(QFont("Segoe UI", 16, QFont.Bold))
        logo.setStyleSheet("color: #3498db;")
        subtitle = QLabel("ACI 318-08 Appendix D — Headed Concrete Anchor Design")
        subtitle.setStyleSheet("color: #7f8c8d; font-size: 12px;")

        h_layout.addWidget(logo)
        h_layout.addSpacing(12)
        h_layout.addWidget(subtitle)
        h_layout.addStretch()

        version = QLabel("v1.0")
        version.setStyleSheet("color: #5d6d7e; font-size: 11px;")
        h_layout.addWidget(version)
        outer.addWidget(header)

        # Body
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle { background: #2c3e50; width: 2px; }
        """)

        # Left: Input
        self.input_panel = InputPanel()
        self.input_panel.setMinimumWidth(340)
        self.input_panel.setMaximumWidth(450)
        splitter.addWidget(self.input_panel)

        # Center: Diagram
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(8, 8, 8, 8)
        diag_label = QLabel("Plate Configuration")
        diag_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        diag_label.setStyleSheet("color: #3498db;")
        diag_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(diag_label)

        self.diagram = PlateDiagram()
        center_layout.addWidget(self.diagram, 1)
        splitter.addWidget(center)

        # Right: Results
        self.results_panel = ResultsPanel()
        self.results_panel.setMinimumWidth(400)
        splitter.addWidget(self.results_panel)

        splitter.setSizes([380, 350, 550])
        outer.addWidget(splitter, 1)

        # Connect signals
        self.input_panel.calculate_requested.connect(self._run_calculation)
        self.results_panel.export_requested.connect(self._export_report)

    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #15202e; }
            QLabel { color: #e0e6ed; }
            QToolTip { background: #1a2636; color: #e0e6ed; border: 1px solid #3498db;
                       padding: 4px; font-size: 12px; }
        """)

    def _run_calculation(self, si_data):
        try:
            inp = InputData.from_si(si_data)
            results = calculate(inp)
            self._current_input = inp
            self._current_results = results
            self.results_panel.update_results(results)
            self.diagram.set_params(si_data)
        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", str(e))

    def _export_report(self):
        if not self._current_results:
            QMessageBox.warning(self, "No Results", "Run a calculation first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "EmbedPlate_Report.html", "HTML Files (*.html)")
        if path:
            try:
                info = self.input_panel.get_project_info()
                export_html(self._current_input, self._current_results, path, info)
                QMessageBox.information(self, "Export", f"Report saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))
