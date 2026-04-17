# ~/kiosk_project/stt_engine/stt.py
import requests

STT_SERVER = "http://127.0.0.1:8081"

def listen(duration: int = 5) -> str:
    print(f"[STT] 🎙️  {duration}초 녹음 시작...", flush=True)
    try:
        resp = requests.post(
            f"{STT_SERVER}/listen",
            json={"duration": duration},
            timeout=60
        )
        text = resp.json().get("text", "")
        print(f"[STT] 인식 결과: '{text}'", flush=True)
        return text
    except Exception as e:
        print(f"[STT] 서버 연결 실패: {e}", flush=True)
        return ""
