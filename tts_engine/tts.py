# ~/kiosk_project/tts_engine/tts.py
import asyncio
import edge_tts
import subprocess
import os

# ── 설정 ──────────────────────────────
VOICE       = "ko-KR-SunHiNeural"   # 한국어 여성 음성
OUTPUT_FILE = "/tmp/tts_output.mp3"
# ─────────────────────────────────────


async def _synthesize(text: str):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(OUTPUT_FILE)


def speak(text: str):
    if not text or not text.strip():
        return

    print(f"[TTS] 🔊 출력: '{text[:40]}'", flush=True)
    asyncio.run(_synthesize(text))
    subprocess.run(["mpg123", "-q", OUTPUT_FILE], check=True)

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)


if __name__ == "__main__":
    print("=== TTS 단독 테스트 ===")
    speak("안녕하세요, 어르신. 치매 선별 검사를 도와드리겠습니다.")
    speak("모르시는 문제가 있으면 편하게 말씀해 주세요.")
    print("TTS 테스트 완료")
