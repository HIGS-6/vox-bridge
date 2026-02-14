import math
import os
import threading
import time
from datetime import datetime
from typing import Optional

import numpy as np
import sounddevice as sd
from scipy.io import wavfile

import state
from models.segmenter_settings import SegmenterSettings
from state import lock, shared


# ---------------------------
# Circular buffer rápido con numpy
# ---------------------------
class CircularBuffer:
    def __init__(self, capacity_samples: int):
        self.capacity = int(capacity_samples)
        self.buf = np.zeros(self.capacity, dtype=np.float32)
        self.head = 0  # índice de escritura (siguiente)
        self.size = 0  # número de muestras válidas en buffer
        self.total_written = 0  # contador monotónico de muestras escritas (global)
        self.lock = threading.Lock()

    def append(self, data: np.ndarray):
        """Append array 1D float32 into circular buffer (may wrap)."""
        data = np.asarray(data, dtype=np.float32)
        n = data.shape[0]
        if n == 0:
            return
        with self.lock:
            # posición donde empieza a escribir (head)
            end_pos = (self.head + n) % self.capacity
            if self.head + n <= self.capacity:
                # no wrap
                self.buf[self.head : self.head + n] = data
            else:
                # wrap
                first = self.capacity - self.head
                self.buf[self.head :] = data[:first]
                self.buf[: n - first] = data[first:]
            # actualizar head y size
            self.head = (self.head + n) % self.capacity
            self.size = min(self.capacity, self.size + n)
            self.total_written += n

    def read_range_by_total_index(
        self, start_total_idx: int, end_total_idx: int
    ) -> np.ndarray:
        """Return copy of samples for [start_total_idx, end_total_idx).
        start/end are absolute sample indices in the stream (monotonic).
        If requested range is partially out of retained buffer, returns available part.
        """
        if end_total_idx <= start_total_idx:
            return np.array([], dtype=np.float32)

        with self.lock:
            # earliest total index we still have
            latest_total = self.total_written
            earliest_total = max(0, self.total_written - self.size)
            # clamp
            start = max(start_total_idx, earliest_total)
            end = min(end_total_idx, latest_total)
            if end <= start:
                return np.array([], dtype=np.float32)
            length = end - start
            # map start to buffer index
            start_idx = (self.head - (self.total_written - start)) % self.capacity
            # now read length samples starting at start_idx (may wrap)
            if start_idx + length <= self.capacity:
                return self.buf[start_idx : start_idx + length].copy()
            else:
                first = self.capacity - start_idx
                out = np.empty(length, dtype=np.float32)
                out[:first] = self.buf[start_idx:]
                out[first:] = self.buf[: length - first]
                return out

    def get_latest_total_index(self) -> int:
        with self.lock:
            return self.total_written

    def get_size(self) -> int:
        with self.lock:
            return self.size


# ---------------------------
# Utilidades audio
# ---------------------------
def rms_db(samples: np.ndarray) -> float:
    if samples.size == 0:
        return -100.0
    rms = math.sqrt(float(np.mean(np.square(samples))))
    if rms < 1e-10:
        return -100.0
    return 20.0 * math.log10(rms)


def float32_to_int16(x: np.ndarray) -> np.ndarray:
    clipped = np.clip(x, -1.0, 1.0)
    return (clipped * 32767.0).astype(np.int16)


# ---------------------------
# Segmenter
# ---------------------------
class Segmenter:
    def __init__(
        self,
        cfg: SegmenterSettings = SegmenterSettings(),
        sample_rate: int = 16000,
        buffer_seconds: int = 30,
        chunk_duration: float = 0.1,
        pre_roll: float = 0.3,
        output_folder: str = "segments",
    ):
        self.sample_rate = int(sample_rate)
        self.chunk_duration = float(chunk_duration)
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        self.buffer_capacity = int(buffer_seconds * self.sample_rate)
        self.buf = CircularBuffer(self.buffer_capacity)
        self.cfg = cfg
        self.pre_roll = pre_roll
        self.output_folder = output_folder
        # os.makedirs(self.output_folder, exist_ok=True)

        # analyzer state
        self._analyzer_thread = None
        self._stop_event = threading.Event()
        self.last_saved_until = 0  # total sample index until which we already handled
        self.segment_counter = 0

    def audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """To be used as sounddevice callback (indata is shape (frames, channels))."""
        if status:
            print("[AUDIO] status:", status)
        # assume mono or take first channel
        if indata.ndim > 1:
            mono = indata[:, 0].astype(np.float32)
        else:
            mono = indata.astype(np.float32)
        # ensure range -1..1; sounddevice typically gives that
        self.buf.append(mono)

    def start(self):
        self._stop_event.clear()
        self._analyzer_thread = threading.Thread(target=self._analyze_loop, daemon=True)
        self._analyzer_thread.start()

    def stop(self):
        self._stop_event.set()
        if self._analyzer_thread is not None:
            self._analyzer_thread.join(timeout=1.0)

    def _analyze_loop(self):
        """Loop que revisa buffer para detectar segmentos y guardarlos."""
        sr = self.sample_rate
        chunk = self.chunk_size
        # we'll examine windows of e.g. voice_time_to_unidle seconds to detect start
        voice_samples_needed = max(
            1, int(self.sample_rate * self.cfg.voice_time_to_unidle)
        )
        pre_roll_samples = int(self.sample_rate * self.pre_roll)
        min_silence_samples = int(self.sample_rate * self.cfg.min_silence_to_end)
        min_segment_samples = int(self.sample_rate * self.cfg.min_segment_duration)

        # scanning pointer: absolute sample index where we last scanned
        scan_pos = max(0, self.buf.get_latest_total_index() - self.buf.get_size())

        while not self._stop_event.is_set():
            with lock:
                cfg = shared["settings"]
                self.cfg = cfg

            # print("Really Analyzing")
            latest = self.buf.get_latest_total_index()
            earliest = max(0, latest - self.buf.get_size())

            # Asegúrate de no escanear fuera de lo que existe
            if scan_pos < earliest:
                scan_pos = earliest

            while scan_pos + voice_samples_needed <= latest:
                # take window to decide if speech starts here
                window_start = scan_pos
                window_end = scan_pos + voice_samples_needed
                window = self.buf.read_range_by_total_index(window_start, window_end)
                db = rms_db(window)

                with lock:
                    shared["current_db"] = db

                if db > self.cfg.silence_threshold_db:
                    # speech detected for this window: find exact start by backing off a bit
                    seg_start = max(0, window_start - pre_roll_samples)
                    # now we need to find segment end: consume until we see min_silence_samples of silence
                    # we'll read in increasing blocks
                    search_pos = window_end
                    last_voice_pos = window_end
                    while search_pos < latest or (
                        not self._stop_event.is_set()
                        and search_pos < self.buf.get_latest_total_index()
                    ):
                        # read a block
                        blk_end = min(
                            search_pos + chunk, self.buf.get_latest_total_index()
                        )
                        blk = self.buf.read_range_by_total_index(search_pos, blk_end)
                        if blk.size == 0:
                            # no data yet; break to outer loop to wait for more
                            break
                        blk_db = rms_db(blk)
                        if blk_db > self.cfg.silence_threshold_db:
                            last_voice_pos = blk_end
                        # if we have been silent for min_silence_samples after last_voice_pos, we end
                        if (search_pos - last_voice_pos) >= min_silence_samples:
                            seg_end = last_voice_pos  # end just after last voice
                            # clamp by min_segment
                            if seg_end - seg_start >= min_segment_samples:
                                # ensure we don't save overlapping/duplicate segments
                                if seg_end > self.last_saved_until:
                                    samples = self.buf.read_range_by_total_index(
                                        seg_start, seg_end
                                    )
                                    # Save to WAV (blocking but fast). We do it here synchronously.
                                    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    # filename = f"seg_{timestamp}_{self.segment_counter:04d}.wav"
                                    # path = os.path.join(self.output_folder, filename)
                                    # int16 = float32_to_int16(samples)
                                    # wavfile.write(path, sr, int16)

                                    state.audio_queue.put(samples)

                                    print(
                                        f"[SEGMENT] Saved {self.segment_counter} ({len(samples) / sr:.2f}s)"
                                    )
                                    self.segment_counter += 1
                                    self.last_saved_until = seg_end
                                else:
                                    # overlapping or already saved
                                    pass
                            else:
                                # too short, ignore
                                pass
                            # advance scan_pos past seg_end + small guard to avoid re-detecting
                            scan_pos = seg_end + int(self.sample_rate * 0.05)
                            break
                        # advance search_pos
                        search_pos = blk_end
                        latest = self.buf.get_latest_total_index()
                    else:
                        # while ended normally, but maybe not enough data yet -> break outer and wait
                        break
                # no speech here, move scan_pos forward by chunk
                scan_pos += chunk
            # sleep briefly to avoid busy-waiting
            time.sleep(0.02)

        print("[ANALYZER] stopped")


def run_listener():
    sr = 16000
    s_cfg = SegmenterSettings()
    s_cfg.silence_threshold_db = -42.0
    s_cfg.voice_time_to_unidle = 0.5
    s_cfg.min_segment_duration = 0.85
    s_cfg.min_silence_to_end = 0.35

    seg = Segmenter(
        sample_rate=sr,
        buffer_seconds=40,
        chunk_duration=0.05,
        cfg=s_cfg,
        pre_roll=0.2,
        output_folder="segments",
    )

    # start analyzer
    seg.start()

    # start audio stream
    stream = sd.InputStream(
        samplerate=sr,
        channels=1,
        dtype="float32",
        blocksize=int(sr * 0.02),  # 20 ms blocks
        callback=lambda indata, frames, t, status: seg.audio_callback(
            indata[:, 0] if indata.ndim > 1 else indata, frames, t, status
        ),
    )
    with stream:
        print("[MAIN] Listening... press Ctrl+C to stop")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping...")
    seg.stop()


if __name__ == "__main__":
    run_listener()
