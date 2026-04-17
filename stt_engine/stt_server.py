# ~/kiosk_project/stt_engine/stt_server.py
# Whisper를 백그라운드 서버로 상주시켜 매번 로딩 제거
from flask import Flask, request, jsonify
import whisper
import sounddevice as sd
import numpy as np
import tempfile, wave, os

app = Flask(__name__)

HW_SAMPLE_RATE = 44100
WHISPER_RATE   = 16000
DEVICE_INDEX   = 1

print("[STT Server] faster-whisper 'small' 모델 로딩 중...", flush=True)
model = whisper.load_model("small")
print("[STT Server] 모델 로딩 완료. 대기 중...", flush=True)


@app.route("/listen", methods=["POST"])
def listen():
    duration = request.json.get("duration", 5)

    # 1. 녹음 (모노, 16000Hz 직접)
    audio = sd.rec(
        int(duration * HW_SAMPLE_RATE),
        samplerate=HW_SAMPLE_RATE,
        channels=1,          # USB 마이크는 모노 지원
        dtype="float32",
        device=DEVICE_INDEX
    )
    sd.wait()
    audio_mono = audio.flatten()

    # 정확한 리샘플링 (44100 → 16000)
    import scipy.signal as signal
    num_samples = int(len(audio_mono) * WHISPER_RATE / HW_SAMPLE_RATE)
    audio_16k = signal.resample(audio_mono, num_samples)

    # 2. 임시 WAV 저장
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(WHISPER_RATE)
        wf.writeframes((audio_mono * 32767).astype(np.int16).tobytes())

    result = model.transcribe(tmp.name, language="ko", fp16=False, temperature=0.0)
    text = result["text"].strip()
    os.unlink(tmp.name)

    print(f"[STT Server] 인식: '{text}'", flush=True)
    return jsonify({"text": text})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081, debug=False)
