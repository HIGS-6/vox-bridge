import threading
from queue import Queue

from models.segmenter_settings import SegmenterSettings

translator_enabled = True
stt_enabled = True
listener_enabled = True

audio_queue = Queue()
transcripted_text = Queue[str]()
translated_text = Queue[str]()

shared = {
    "current_db": 0.0,
    "settings": SegmenterSettings,
}
lock = threading.Lock()
