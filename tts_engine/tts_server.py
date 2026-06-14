from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import edge_tts
import subprocess
import os
import signal

app = Flask(__name__)
CORS(app)

VOICE = "ko-KR-SunHiNeural"
OUTPUT_FILE = "/tmp/tts_output.mp3"

# 현재 재생 중인 프로세스 추적
current_process = None

async def _synthesize(text):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(OUTPUT_FILE)

    # 파일 앞에 0.3초 무음 추가
    silent = "/tmp/silent.mp3"
    final  = "/tmp/tts_final.mp3"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", "0.3",
        silent
    ], capture_output=True)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", f"concat:{silent}|{OUTPUT_FILE}",
        "-acodec", "copy",
        final
    ], capture_output=True)
    os.replace(final, OUTPUT_FILE)

@app.route("/tts", methods=["POST"])
def tts():
    global current_process

    text = request.json.get("text", "")
    callback = request.json.get("callback", False)

    if not text:
        return jsonify({"status": "error"})

    # 기존 재생 중인 TTS 강제 종료
    if current_process and current_process.poll() is None:
        current_process.kill()
        current_process.wait()
        current_process = None

    # TTS 생성
    asyncio.run(_synthesize(text))

    if callback:
        # 동기 재생 → 끝나면 완료 반환
        subprocess.run(["mpg123", "-q", OUTPUT_FILE])
        return jsonify({"status": "done"})
    else:
        # 비동기 재생
        current_process = subprocess.Popen(["mpg123", "-q", OUTPUT_FILE])
        return jsonify({"status": "ok"})

@app.route("/tts/stop", methods=["POST"])
def tts_stop():
    global current_process
    if current_process and current_process.poll() is None:
        current_process.kill()
        current_process.wait()
        current_process = None
    return jsonify({"status": "stopped"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082, debug=False)
