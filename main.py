from threading import Thread

from gui import app
from workers import broadcast, listener, stt, translator


def main():
    # Make a thread for every worker:
    listener_t = Thread(target=listener.run_listener, daemon=True)
    stt_t = Thread(target=stt.run_stt, daemon=True)
    translator_t = Thread(target=translator.run_translator, daemon=True)
    broadcast_t = Thread(target=broadcast.run_broadcast, daemon=True)

    # Start the Threads
    listener_t.start()
    stt_t.start()
    translator_t.start()
    broadcast_t.start()

    # Run the GUI
    app.run_gui()


if __name__ == "__main__":
    main()
