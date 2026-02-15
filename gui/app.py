from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
)

from gui.pages import (
    BroadcastPage,
    ListenerPage,
    STTPage,
    TranslatorPage,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vox Bridge — Control")
        self.resize(1280, 720)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Pages
        self.listener_page = ListenerPage()
        self.stt_page = STTPage()
        self.translator_page = TranslatorPage()
        self.broadcast_page = BroadcastPage()

        self.tabs.addTab(self.listener_page, "Listener")
        self.tabs.addTab(self.stt_page, "STT")
        self.tabs.addTab(self.translator_page, "Translator")
        self.tabs.addTab(self.broadcast_page, "Broadcast")

    # Helpers para que el backend pueda acceder rápido
    def set_db_value(self, db: float):
        self.listener_page.set_db(db)

    def append_transcription_preview(self, text: str):
        self.stt_page.append_transcript(text)

    def set_translation_result(self, text: str):
        self.translator_page.set_result(text)

    def set_connected_clients(self, names: list[str]):
        self.broadcast_page.set_clients(names)

    def add_connected_client(self, name: str):
        self.broadcast_page.add_client(name)


def run_gui():
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec()
