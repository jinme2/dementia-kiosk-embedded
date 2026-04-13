# ~/kiosk_project/kiosk_main.py  v2.0
import requests
import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stt_engine.stt import listen
from tts_engine.tts import speak

# ── 설정 ──────────────────────────────────────────
API_URL = "http://localhost:8080/v1/chat/completions"
SYSTEM_PROMPT = (
    "You must respond ONLY in Korean language. Never use Chinese or Japanese characters. "
    "당신은 어르신들의 치매 선별 검사를 돕는 친절한 안내원입니다. "
    "반드시 한국어로만 짧고 다정하게 1~2문장으로 대답해주세요. "
    "절대 중국어, 일본어, 영어를 사용하지 마세요."
)
MAX_HISTORY = 6
# ─────────────────────────────────────────────────

conversation_history = []


def _call_llm(user_message: str) -> str:
    global conversation_history

    if len(conversation_history) > MAX_HISTORY * 2:
        conversation_history = conversation_history[-(MAX_HISTORY * 2):]

    conversation_history.append({
        "role": "user",
        "content": f"(반드시 한국어로만) {user_message}"
    })

    payload = {
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history,
        "temperature": 0.3,
        "max_tokens": 100,
    }

    response = requests.post(
        API_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=30
    )
    response.raise_for_status()
    reply = response.json()["choices"][0]["message"]["content"].strip()

    if not any('\uAC00' <= ch <= '\uD7A3' for ch in reply):
        reply = "죄송합니다, 다시 한번 말씀해 주시겠어요?"

    conversation_history.append({"role": "assistant", "content": reply})
    return reply


def reset_session():
    global conversation_history
    conversation_history = []
    print("[SYSTEM] 세션 초기화 완료", flush=True)


def run_voice_mode():
    print("=== 🧠 치매 선별 키오스크 음성 모드 시작 ===")
    speak("안녕하세요, 어르신. 치매 선별 검사를 도와드리겠습니다. 궁금한 것이 있으면 말씀해 주세요.")

    while True:
        try:
            user_text = listen()

            if not user_text.strip():
                speak("잘 들리지 않았어요. 다시 한번 말씀해 주세요.")
                continue

            if any(word in user_text for word in ["종료", "끝내", "그만"]):
                speak("검사를 마치겠습니다. 수고하셨습니다.")
                break

            print(f"[USER] {user_text}", flush=True)

            print("[AI] 생각하는 중...", flush=True)
            start = time.time()
            reply = _call_llm(user_text)
            elapsed = time.time() - start
            print(f"[AI] 응답 ({elapsed:.2f}초): {reply}", flush=True)

            speak(reply)

        except KeyboardInterrupt:
            print("\n[SYSTEM] 종료")
            break
        except Exception as e:
            print(f"[ERROR] {e}", flush=True)
            speak("오류가 발생했습니다. 다시 시도해 주세요.")


def run_text_mode():
    print("=== 🧠 치매 선별 키오스크 텍스트 모드 ===")
    while True:
        user_input = input("[어르신]: ").strip()
        if user_input.lower() in ["q", "종료"]:
            break
        if not user_input:
            continue
        print("🧠 AI가 생각하는 중 ...")
        start = time.time()
        reply = _call_llm(user_input)
        print(f"⏱️  응답 시간: {time.time()-start:.2f}초")
        print(f"🤖 안내원: {reply}\n")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "text"
    if mode == "voice":
        run_voice_mode()
    else:
        run_text_mode()
