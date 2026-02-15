import numpy as np

import state

_whisper = None


def prepare_for_whisper(samples: np.ndarray, sample_rate: int) -> np.ndarray:
    x = samples

    # Si es estéreo u otro formato multicanal -> a mono
    if x.ndim == 2:
        x = x.mean(axis=1)

    # Convertir a float32 y normalizar si hace falta
    if x.dtype == np.int16:
        x = x.astype(np.float32) / 32768.0
    elif x.dtype == np.int32:
        x = x.astype(np.float32) / 2147483648.0
    else:
        x = x.astype(np.float32)

    # Clip por si acaso alguien hizo algo creativo
    np.clip(x, -1.0, 1.0, out=x)

    return x


def init_worker():
    from faster_whisper import WhisperModel

    global _whisper

    print("[STT] Starting Whisper...")

    _whisper = WhisperModel(
        "small.en",
        device="cpu",
        compute_type="int8",
        local_files_only=False,
    )


def run_stt():
    print("[STT] Waiting for GUI...")
    # state.gui_ready_event.wait()

    init_worker()

    if _whisper is None:
        raise Exception("STT model not initialized properly")

    # state.stt_worker_ready = True

    print("[STT] Whisper Ready.")

    while True:
        audio_path = state.audio_queue.get()
        try:
            audio = prepare_for_whisper(audio_path, 2)

            segments, _ = _whisper.transcribe(
                audio, language="en", beam_size=1, vad_filter=True
            )

            text = " ".join(s.text for s in segments).strip()

            if text:
                print(f"[STT] Result: {text}")
                state.transcripted_text.put(text)
            else:
                print("[STT] Empty result.")

        except Exception as e:
            print(f"[STT] Error processing {audio_path}: {e}")
