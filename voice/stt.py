import time
import tempfile
import queue

import numpy as np
import sounddevice as sd
import webrtcvad
from scipy.io.wavfile import write
import whisper

MODEL_NAME = "base"  # tiny | base | small
_model = whisper.load_model(MODEL_NAME)

# Force MacBook Air Microphone from your device list
INPUT_DEVICE_INDEX = 1


def record_until_silence(
    sample_rate: int = 16000,
    frame_ms: int = 20,
    vad_aggressiveness: int = 1,
    max_record_sec: float = 2.0,
    silence_stop_ms: int = 350,
    pre_roll_ms: int = 250,
    input_gain: float = 8.0,        # 🔥 boosted for low mic amplitude
) -> np.ndarray:
    vad = webrtcvad.Vad(vad_aggressiveness)
    q: "queue.Queue[np.ndarray]" = queue.Queue()

    frame_samples = int(sample_rate * frame_ms / 1000)
    silence_frames_to_stop = max(1, int(silence_stop_ms / frame_ms))
    max_frames = max(1, int(max_record_sec * 1000 / frame_ms))
    pre_roll_frames = max(0, int(pre_roll_ms / frame_ms))

    got_speech = False
    silent_count = 0
    frames: list[np.ndarray] = []
    ring: list[np.ndarray] = []

    def callback(indata, frames_count, time_info, status):
        # float32 [-1,1] -> gain -> clip -> int16 PCM
        x = indata[:, 0] * float(input_gain)
        x = np.clip(x, -1.0, 1.0)
        pcm16 = (x * 32767).astype(np.int16)
        q.put(pcm16)

    try:
        with sd.InputStream(
            device=INPUT_DEVICE_INDEX,
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            blocksize=frame_samples,
            callback=callback,
        ):
            for _ in range(max_frames):
                pcm16 = q.get()

                # keep pre-roll
                ring.append(pcm16)
                if len(ring) > pre_roll_frames:
                    ring.pop(0)

                is_speech = vad.is_speech(pcm16.tobytes(), sample_rate)

                if is_speech:
                    if not got_speech:
                        frames.extend(ring)
                        ring.clear()
                    got_speech = True
                    silent_count = 0
                    frames.append(pcm16)
                else:
                    if got_speech:
                        frames.append(pcm16)
                        silent_count += 1
                        if silent_count >= silence_frames_to_stop:
                            break
    except Exception as e:
        print(f"⚠️ Audio recording error: {e}")
        return np.zeros((0,), dtype=np.int16)

    if not frames:
        return np.zeros((0,), dtype=np.int16)

    return np.concatenate(frames)


def listen_and_transcribe(duration_seconds: int = 5) -> str:
    total_start = time.perf_counter()
    sample_rate = 16000
    max_record_sec = min(float(duration_seconds), 2.0)

    print(f"\n🎤 Speak now... (max {max_record_sec:.1f}s, auto-stops on silence)")
    print(f"🎛️ Using input device #{INPUT_DEVICE_INDEX}: {sd.query_devices(INPUT_DEVICE_INDEX)['name']}")

    # RECORD
    record_start = time.perf_counter()
    audio_1d = record_until_silence(
        sample_rate=sample_rate,
        max_record_sec=max_record_sec,
    )
    record_ms = (time.perf_counter() - record_start) * 1000

    if audio_1d.size == 0:
        total_ms = (time.perf_counter() - total_start) * 1000
        print(f"⏱️ STT timings | recording_ms={record_ms:.2f}, transcribe_ms=0.00, total_stt_ms={total_ms:.2f}")
        return "Sorry, I couldn't hear that. Please try again."

    # Save WAV (keep for manual playback debugging)
    audio = audio_1d.reshape(-1, 1)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name
    write(wav_path, sample_rate, audio)
    print(f"🔎 Debug WAV saved at: {wav_path}")
    print("ℹ️ If needed, play it manually with: afplay <path>")

    # TRANSCRIBE (more sensitive to low volume)
    print("🧠 Transcribing locally with Whisper...")
    transcribe_start = time.perf_counter()
    result = _model.transcribe(
        wav_path,
        fp16=False,
        language="en",
        temperature=0.0,
        # ↓ make it less likely to discard as "no speech"
        no_speech_threshold=0.6,
        logprob_threshold=-2.0,
        compression_ratio_threshold=2.4,
        condition_on_previous_text=False,
    )
    transcribe_ms = (time.perf_counter() - transcribe_start) * 1000

    text = (result.get("text") or "").strip()
    total_ms = (time.perf_counter() - total_start) * 1000

    print(f"⏱️ STT timings | recording_ms={record_ms:.2f}, transcribe_ms={transcribe_ms:.2f}, total_stt_ms={total_ms:.2f}")

    if not text:
        return "Sorry, I couldn't hear that. Please try again."

    print(f"📝 Transcribed text: {text}")
    return text
