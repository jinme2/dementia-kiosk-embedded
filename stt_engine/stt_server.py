# ~/kiosk_project/stt_engine/stt_server.py
# Whisper를 백그라운드 서버로 상주시켜 매번 로딩 제거
from flask import Flask, request, jsonify
import whisper
import sounddevice as sd
import numpy as np
import scipy.signal as signal
import tempfile, wave, os

app = Flask(__name__)

HW_SAMPLE_RATE = 48000
WHISPER_RATE   = 16000
DEVICE_INDEX   = 0
# USB 마이크    HW_SAMPLE_RATE = 44100, DEVICE_INDEX   = 1

print("[STT Server] faster-whisper 'small' 모델 로딩 중...", flush=True)
model = whisper.load_model("small")
print("[STT Server] 모델 로딩 완료. 대기 중...", flush=True)

import re

def record_until_answer(max_duration=15, silence_threshold=0.03, silence_sec=1.5):
    """
    말이 시작되면 녹음 시작
    침묵이 1.5초 이상 지속되면 자동 종료
    최대 15초
    """
    import collections
    CHUNK = int(HW_SAMPLE_RATE * 0.1)  # 0.1초 청크
    max_chunks = int(max_duration / 0.1)
    silence_chunks = int(silence_sec / 0.1)

    print("[STT] 🎙️ 말씀하세요...", flush=True)

    frames = []
    silence_count = 0
    started = False

    with sd.InputStream(samplerate=HW_SAMPLE_RATE, channels=2,
                        dtype='float32', device=DEVICE_INDEX,
                        blocksize=CHUNK) as stream:
        for _ in range(max_chunks):
            data, _ = stream.read(CHUNK)
            mono = data.mean(axis=1)
            volume = float(np.abs(mono).mean())

            if not started:
                if volume > silence_threshold:
                    started = True
                    print("[STT] 음성 감지됨", flush=True)
                    frames.append(mono)
            else:
                frames.append(mono)
                if volume < silence_threshold:
                    silence_count += 1
                    if silence_count >= silence_chunks:
                        print("[STT] 침묵 감지 → 종료", flush=True)
                        break
                else:
                    silence_count = 0

    if not frames:
        return np.zeros(HW_SAMPLE_RATE)

    return np.concatenate(frames)


@app.route("/listen", methods=["POST"])
def listen():
    max_duration = request.json.get("duration", 15)

    # VAD 녹음 (말 시작 감지 → 침묵 1.5초 → 자동 종료)
    CHUNK = int(HW_SAMPLE_RATE * 0.1)
    max_chunks = int(max_duration / 0.1)
    silence_chunks = 15  # 1.5초
    silence_threshold = 0.01

    frames = []
    silence_count = 0
    started = False

    print("[STT] 🎙️ 말씀하세요...", flush=True)

    with sd.InputStream(samplerate=HW_SAMPLE_RATE, channels=2,
                        dtype='float32', device=DEVICE_INDEX,
                        blocksize=CHUNK) as stream:
        for _ in range(max_chunks):
            data, _ = stream.read(CHUNK)
            mono = data.mean(axis=1)
            volume = float(np.abs(mono).mean())

            if not started:
                if volume > silence_threshold:
                    started = True
                    print("[STT] 음성 감지됨", flush=True)
                    frames.append(mono)
            else:
                frames.append(mono)
                if volume < silence_threshold:
                    silence_count += 1
                    if silence_count >= silence_chunks:
                        print("[STT] 침묵 감지 → 종료", flush=True)
                        break
                else:
                    silence_count = 0

    if not frames:
        return jsonify({"text": ""})

    audio_mono = np.concatenate(frames)
    num_samples = int(len(audio_mono) * WHISPER_RATE / HW_SAMPLE_RATE)
    audio_16k = signal.resample(audio_mono, num_samples)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(WHISPER_RATE)
        wf.writeframes((audio_16k * 32767).astype(np.int16).tobytes())

    result = model.transcribe(tmp.name, language="ko", fp16=False, temperature=0.0)
    text = result["text"].strip()
    os.unlink(tmp.name)

    print(f"[STT Server] 인식: '{text}'", flush=True)
    return jsonify({"text": text})

@app.route("/listen_until_silence", methods=["POST"])
def listen_until_silence():
    """
    말하다가 4초 침묵 or 엔터(중단 신호) 오면 종료
    기억등록 문항처럼 긴 문장 받을 때 사용
    """
    max_duration = request.json.get("duration", 60)
    silence_sec  = request.json.get("silence_sec", 4)  # 4초 침묵

    CHUNK          = int(HW_SAMPLE_RATE * 0.1)
    max_chunks     = int(max_duration / 0.1)
    silence_chunks = int(silence_sec / 0.1)  # 40 chunks = 4초
    silence_threshold = 0.05

    frames = []
    silence_count = 0
    started = False

    print("[STT] 🎙️ 말씀하세요... (4초 침묵 or 엔터로 종료)", flush=True)

    with sd.InputStream(
        samplerate=HW_SAMPLE_RATE,
        channels=2,
        dtype="float32",
        device=DEVICE_INDEX,
        blocksize=CHUNK
    ) as stream:
        for _ in range(max_chunks):
            data, _ = stream.read(CHUNK)
            mono   = data.mean(axis=1)
            volume = float(np.abs(mono).mean())

            if not started:
                if volume > silence_threshold:
                    started = True
                    frames.append(mono)
            else:
                frames.append(mono)
                if volume < silence_threshold:
                    silence_count += 1
                    if silence_count >= silence_chunks:
                        print("[STT] 4초 침묵 → 종료", flush=True)
                        break
                else:
                    silence_count = 0

    if not frames:
        return jsonify({"text": ""})

    audio_mono  = np.concatenate(frames)
    num_samples = int(len(audio_mono) * WHISPER_RATE / HW_SAMPLE_RATE)
    audio_16k   = signal.resample(audio_mono, num_samples)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(WHISPER_RATE)
        wf.writeframes((audio_16k * 32767).astype(np.int16).tobytes())

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
