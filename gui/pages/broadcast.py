from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class BroadcastPage(QWidget):
    startRequested = Signal(int)
    stopRequested = Signal()
    sendManualRequested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        header = QLabel("Broadcast")
        header.setStyleSheet("font-weight:600; font-size:16px;")
        layout.addWidget(header)

        port_row = QHBoxLayout()
        port_row.addWidget(QLabel("Port"))
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(8765)
        port_row.addWidget(self.port_spin)
        layout.addLayout(port_row)

        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("Start Server")
        self.stop_btn = QPushButton("Stop Server")
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        layout.addLayout(btn_row)

        layout.addWidget(QLabel("Connected clients"))
        self.clients_list = QListWidget()
        layout.addWidget(self.clients_list, stretch=1)

        manual_row = QHBoxLayout()
        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("Texto a enviar manualmente")
        self.send_btn = QPushButton("Send")
        manual_row.addWidget(self.manual_input)
        manual_row.addWidget(self.send_btn)
        layout.addLayout(manual_row)

        # conexiones
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)
        self.send_btn.clicked.connect(self._on_send)

    def _on_start(self):
        port = int(self.port_spin.value())
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.startRequested.emit(port)

    def _on_stop(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.stopRequested.emit()

    def _on_send(self):
        txt = self.manual_input.text().strip()
        if txt:
            self.sendManualRequested.emit(txt)
            self.manual_input.clear()

    # API
    def set_clients(self, names: list[str]):
        self.clients_list.clear()
        self.clients_list.addItems(names)

    def add_client(self, name: str):
        self.clients_list.addItem(name)
