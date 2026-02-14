from dataclasses import dataclass


@dataclass
class SegmenterSettings:
    sample_rate = 16000
    silence_threshold_db = -42.0
    voice_time_to_unidle = 0.5
    min_segment_duration = 0.6
    min_speech_duration = 0.6
    min_silence_to_end = 0.35
