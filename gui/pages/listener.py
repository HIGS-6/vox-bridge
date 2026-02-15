from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class ListenerPage(QWidget):
    # Señales para que el backend conecte
    startRequested = Signal()
    stopRequested = Signal()
    settingsChanged = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Listener")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header.setStyleSheet("font-weight:600; font-size:16px;")
        layout.addWidget(header)

        # DB meter + label
        meter_layout = QHBoxLayout()
        self.db_label = QLabel("dB: -∞")
        self.db_bar = QProgressBar()
        self.db_bar.setRange(-100, 0)
        self.db_bar.setValue(-100)
        self.db_bar.setTextVisible(False)
        self.db_bar.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        meter_layout.addWidget(self.db_label)
        meter_layout.addWidget(self.db_bar)
        layout.addLayout(meter_layout)

        # Controls grid
        grid = QGridLayout()
        grid.addWidget(QLabel("Silence threshold (dB)"), 0, 0)
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(-100, 0)
        self.threshold_spin.setValue(-40)
        grid.addWidget(self.threshold_spin, 0, 1)

        grid.addWidget(QLabel("Min voice (ms)"), 1, 0)
        self.min_voice_spin = QSpinBox()
        self.min_voice_spin.setRange(10, 5000)
        self.min_voice_spin.setValue(200)
        grid.addWidget(self.min_voice_spin, 1, 1)

        grid.addWidget(QLabel("Min silence (ms)"), 2, 0)
        self.min_silence_spin = QSpinBox()
        self.min_silence_spin.setRange(10, 5000)
        self.min_silence_spin.setValue(500)
        grid.addWidget(self.min_silence_spin, 2, 1)

        grid.addWidget(QLabel("Pre-roll (ms)"), 3, 0)
        self.pre_roll_spin = QSpinBox()
        self.pre_roll_spin.setRange(0, 3000)
        self.pre_roll_spin.setValue(200)
        grid.addWidget(self.pre_roll_spin, 3, 1)

        layout.addLayout(grid)

        # Start / Stop
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Listener")
        self.stop_btn = QPushButton("Stop Listener")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

        # Conexiones
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)

        for w in (
            self.threshold_spin,
            self.min_voice_spin,
            self.min_silence_spin,
            self.pre_roll_spin,
        ):
            w.valueChanged.connect(self._emit_settings)

    @Slot()
    def _on_start(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.startRequested.emit()

    @Slot()
    def _on_stop(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.stopRequested.emit()

    def _emit_settings(self):
        cfg = {
            "silence_threshold_db": float(self.threshold_spin.value()),
            "voice_time_to_unidle_ms": int(self.min_voice_spin.value()),
            "min_silence_ms": int(self.min_silence_spin.value()),
            "pre_roll_ms": int(self.pre_roll_spin.value()),
        }
        self.settingsChanged.emit(cfg)

    # API pública para backend
    @Slot(float)
    def set_db(self, db: float):
        if db < -100:
            db = -100
        if db > 0:
            db = 0
        self.db_bar.setValue(int(db))
        self.db_label.setText(f"dB: {db:.1f}")
