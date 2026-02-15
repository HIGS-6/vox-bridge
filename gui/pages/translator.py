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


class TranslatorPage(QWidget):
    translateRequested = Signal(str)
    settingsChanged = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        header = QLabel("Translator")
        header.setStyleSheet("font-weight:600; font-size:16px;")
        layout.addWidget(header)

        row = QHBoxLayout()
        row.addWidget(QLabel("From"))
        self.src_combo = QComboBox()
        self.src_combo.addItems(["auto", "en", "es"])
        row.addWidget(self.src_combo)

        row.addWidget(QLabel("To"))
        self.tgt_combo = QComboBox()
        self.tgt_combo.addItems(["es", "en"])
        row.addWidget(self.tgt_combo)

        layout.addLayout(row)

        btn_layout = QHBoxLayout()
        self.translate_btn = QPushButton("Translate last")
        btn_layout.addWidget(self.translate_btn)
        layout.addLayout(btn_layout)

        self.result_preview = QTextEdit()
        self.result_preview.setReadOnly(True)
        layout.addWidget(self.result_preview, stretch=1)

        # conexiones
        self.translate_btn.clicked.connect(self._on_translate)
        self.src_combo.currentIndexChanged.connect(self._emit_settings)
        self.tgt_combo.currentIndexChanged.connect(self._emit_settings)

    def _on_translate(self):
        # Emite señal con la dirección (el backend recogerá el texto del queue)
        self.translateRequested.emit("manual")

    def _emit_settings(self):
        self.settingsChanged.emit(
            {"from": self.src_combo.currentText(), "to": self.tgt_combo.currentText()}
        )

    # API
    def set_result(self, text: str):
        self.result_preview.append(text)
