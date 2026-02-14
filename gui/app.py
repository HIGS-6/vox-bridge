from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMainWindow,
    QProgressBar,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

import state


class MainWindow(QMainWindow):
    # Emite un dict con los settings actuales cuando cambia algo
    settingsChanged = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Audio Segmenter Control")
        self.resize(520, 360)

        central = QWidget(self)
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setSpacing(12)

        # =========================
        # dB Meter
        # =========================
        meter_box = QGroupBox("Input Level")
        meter_layout = QVBoxLayout(meter_box)

        self.db_label = QLabel("−∞ dB")
        self.db_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.db_label.setStyleSheet("font-size: 20px; font-weight: 600;")

        self.db_bar = QProgressBar()
        self.db_bar.setRange(-100, 0)  # dBFS típico
        self.db_bar.setValue(-100)
        self.db_bar.setTextVisible(False)
        self.db_bar.setFixedHeight(24)

        meter_layout.addWidget(self.db_label)
        meter_layout.addWidget(self.db_bar)

        root.addWidget(meter_box)

        # =========================
        # Settings
        # =========================
        settings_box = QGroupBox("Segmenter Settings")
        grid = QGridLayout(settings_box)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        # Threshold dB
        grid.addWidget(QLabel("Threshold (dB):"), 0, 0)
        self.spin_threshold = QDoubleSpinBox()
        self.spin_threshold.setRange(-100.0, 0.0)
        self.spin_threshold.setDecimals(1)
        self.spin_threshold.setSingleStep(0.5)
        self.spin_threshold.setValue(-40.0)
        grid.addWidget(self.spin_threshold, 0, 1)

        # Min voice ms
        grid.addWidget(QLabel("Min voice (ms):"), 1, 0)
        self.spin_min_voice = QSpinBox()
        self.spin_min_voice.setRange(10, 10_000)
        self.spin_min_voice.setSingleStep(50)
        self.spin_min_voice.setValue(300)
        grid.addWidget(self.spin_min_voice, 1, 1)

        # Min silence ms
        grid.addWidget(QLabel("Min silence (ms):"), 2, 0)
        self.spin_min_silence = QSpinBox()
        self.spin_min_silence.setRange(10, 10_000)
        self.spin_min_silence.setSingleStep(50)
        self.spin_min_silence.setValue(500)
        grid.addWidget(self.spin_min_silence, 2, 1)

        # Pre-roll ms
        grid.addWidget(QLabel("Pre-roll (ms):"), 3, 0)
        self.spin_pre_roll = QSpinBox()
        self.spin_pre_roll.setRange(0, 5_000)
        self.spin_pre_roll.setSingleStep(50)
        self.spin_pre_roll.setValue(200)
        grid.addWidget(self.spin_pre_roll, 3, 1)

        # Post-roll ms
        grid.addWidget(QLabel("Post-roll (ms):"), 4, 0)
        self.spin_post_roll = QSpinBox()
        self.spin_post_roll.setRange(0, 5_000)
        self.spin_post_roll.setSingleStep(50)
        self.spin_post_roll.setValue(300)
        grid.addWidget(self.spin_post_roll, 4, 1)

        root.addWidget(settings_box)

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_db)
        self.timer.start(100)

        # =========================
        # Signals
        # =========================
        self.spin_threshold.valueChanged.connect(self._emit_settings)
        self.spin_min_voice.valueChanged.connect(self._emit_settings)
        self.spin_min_silence.valueChanged.connect(self._emit_settings)
        self.spin_pre_roll.valueChanged.connect(self._emit_settings)
        self.spin_post_roll.valueChanged.connect(self._emit_settings)

    def update_db(self):
        with state.lock:
            self.db_bar.setValue(state.shared["current_db"])
            self.db_label.setText(f"{int(state.shared['current_db'])} dB")

    # =========================
    # Public API for backend
    # =========================
    @Slot(float)
    def set_current_db(self, db_value: float):
        # Clamp por si acaso
        if db_value < -100:
            db_value = -100
        if db_value > 0:
            db_value = 0

        self.db_bar.setValue(int(db_value))
        self.db_label.setText(f"{db_value:.1f} dB")

    def get_settings(self) -> dict:
        return {
            "threshold_db": float(self.spin_threshold.value()),
            "min_voice_ms": int(self.spin_min_voice.value()),
            "min_silence_ms": int(self.spin_min_silence.value()),
            "pre_roll_ms": int(self.spin_pre_roll.value()),
            "post_roll_ms": int(self.spin_post_roll.value()),
        }

    @Slot()
    def _emit_settings(self):
        self.settingsChanged.emit(self.get_settings())


def run_gui():
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec()
