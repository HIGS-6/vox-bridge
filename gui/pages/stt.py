from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class STTPage(QWidget):
    startRequested = Signal()
    stopRequested = Signal()
    modelChanged = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        header = QLabel("Speech-To-Text")
        header.setStyleSheet("font-weight:600; font-size:16px;")
        layout.addWidget(header)

        hl = QHBoxLayout()
        hl.addWidget(QLabel("Model"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium"])
        hl.addWidget(self.model_combo)

        hl.addWidget(QLabel("Compute"))
        self.compute_combo = QComboBox()
        self.compute_combo.addItems(["int8", "float32"])
        hl.addWidget(self.compute_combo)
        layout.addLayout(hl)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start STT")
        self.stop_btn = QPushButton("Stop STT")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # Output preview
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Transcriptions will appear here (preview).")
        layout.addWidget(self.preview, stretch=1)

        # conexiones
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)
        self.model_combo.currentIndexChanged.connect(self._emit_model)
        self.compute_combo.currentIndexChanged.connect(self._emit_model)

    def _on_start(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.startRequested.emit()

    def _on_stop(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.stopRequested.emit()

    def _emit_model(self):
        self.modelChanged.emit(
            {
                "model": self.model_combo.currentText(),
                "compute": self.compute_combo.currentText(),
            }
        )

    # API
    def append_transcript(self, text: str):
        self.preview.append(text)
