# ~/kiosk_project/stt_engine/stt.py
import whisper
import sounddevice as sd
import numpy as np

# ── 설정 ──────────────────────────────
HW_SAMPLE_RATE   = 48000   # WM8960 하드웨어 실제 샘플레이트
WHISPER_RATE     = 16000   # Whisper 요구 샘플레이트
RECORD_SECS      = 5
DEVICE_INDEX     = 0
MODEL_SIZE       = "small"
# ─────────────────────────────────────

print(f"[STT] Whisper '{MODEL_SIZE}' 모델 로딩 중...", flush=True)
model = whisper.load_model(MODEL_SIZE)
print("[STT] 모델 로딩 완료", flush=True)


def record_audio(duration: int = RECORD_SECS) -> np.ndarray:
    print(f"[STT] 🎙️  {duration}초 녹음 시작...", flush=True)
    audio = sd.rec(
        int(duration * HW_SAMPLE_RATE),
        samplerate=HW_SAMPLE_RATE,
        channels=2,           # WM8960 스테레오
        dtype="float32",
        device=DEVICE_INDEX
    )
    sd.wait()
    print("[STT] 녹음 완료", flush=True)

    # 스테레오 → 모노 변환
    audio_mono = audio.mean(axis=1)

    # 48000Hz → 16000Hz 다운샘플링 (1/3 샘플링)
    step = HW_SAMPLE_RATE // WHISPER_RATE   # = 3
    audio_resampled = audio_mono[::step]

    return audio_resampled


def transcribe(audio_array: np.ndarray) -> str:
    print("[STT] 음성 인식 중...", flush=True)
    result = model.transcribe(
        audio_array,
        language="ko",
        fp16=False,
        temperature=0.0
    )
    text = result["text"].strip()
    print(f"[STT] 인식 결과: '{text}'", flush=True)
    return text


def listen() -> str:
    audio = record_audio()
    return transcribe(audio)


if __name__ == "__main__":
    print("=== STT 단독 테스트 ===")
    text = listen()
    print(f"최종 텍스트: {text}")
