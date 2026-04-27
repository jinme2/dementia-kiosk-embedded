# ~/kiosk_project/cist_runner.py
# CIST 설문을 음성으로 진행하는 메인 로직
import requests
import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tts_engine.tts import speak
from stt_engine.stt import listen

# ── 설정 ──────────────────────────────────────────
BACKEND_URL  = "http://[EC2주소]/cist/questions"  # 나중에 채워넣기
LOCAL_JSON   = "/home/pi/kiosk_project/cist_questions.json"  # 로컬 테스트용
LLM_URL      = "http://127.0.0.1:8080/v1/chat/completions"
STT_URL      = "http://127.0.0.1:8081/listen"

# 그림이 필요한 문항 번호 (터치스크린으로 처리)
VISUAL_QUESTIONS = [6, 7, 8, 9, 11]
# 점수 없는 문항 (기억 등록용, 읽어주기만 함)
NO_SCORE_QUESTIONS = [3]
# 1분 제한 문항
TIMED_QUESTIONS = {13: 60}

# ─────────────────────────────────────────────────

def load_questions():
    """백엔드 or 로컬 JSON에서 문항 불러오기"""
    try:
        resp = requests.get(BACKEND_URL, timeout=5)
        data = resp.json()
        print("[CIST] 백엔드에서 문항 로드 완료")
    except:
        print("[CIST] 백엔드 연결 실패 → 로컬 JSON 사용")
        with open(LOCAL_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    return data["questions"]


def ask_llm_hint(question_text: str, user_answer: str) -> str:
    """어르신이 모르겠다고 할 때 LLM이 힌트 제공"""
    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "당신은 치매 선별 검사를 돕는 친절한 안내원입니다. "
                    "어르신이 문제를 어려워하면 답을 알려주지 말고 "
                    "쉬운 힌트만 한 문장으로 말해주세요. 반드시 한국어로만 답하세요."
                )
            },
            {
                "role": "user",
                "content": f"문제: {question_text}\n어르신 답변: {user_answer}\n힌트를 주세요."
            }
        ],
        "temperature": 0.3,
        "max_tokens": 80
    }
    try:
        resp = requests.post(LLM_URL,
                             headers={"Content-Type": "application/json"},
                             json=payload, timeout=30)
        return resp.json()["choices"][0]["message"]["content"].strip()
    except:
        return "천천히 생각해보세요."

def conduct_question(q: dict) -> dict:
    q_num = q["question_number"]
    sub   = q.get("sub_number") or ""
    text  = q["question_text"]
    instr = q.get("instruction") or ""
    options = q.get("options")

    print(f"\n[CIST] Q{q_num}{sub} ({q['domain']} - {q['sub_domain']})")

    # 1. 문항 음성 출력
    speak(text)

    # 기억 등록 문항 (Q3)
    if q_num in NO_SCORE_QUESTIONS:
        from stt_engine.stt import listen_until_silence

        speak("1차 시행입니다. 민수는, 자전거를 타고, 공원에 가서, 11시부터, 야구를 했다")
        time.sleep(1.5)  # TTS 잔향 대기
        listen_until_silence(duration=30, silence_sec=4)

        speak("잘 하셨습니다. 다시 한번 불러드리겠습니다.")
        speak("2차 시행입니다. 민수는, 자전거를 타고, 공원에 가서, 11시부터, 야구를 했다")
        time.sleep(1.5)  # TTS 잔향 대기
        listen_until_silence(duration=30, silence_sec=4)

        speak("제가 이 문장을 나중에 여쭤보겠습니다. 잘 기억하세요.")
        return {"question_number": q_num, "sub_number": sub,
                "answer": "기억등록완료", "score": 0}
    # 객관식 문항 → TTS만, 터치로 선택
    if options:
        speak("화면에서 선택해 주세요.")
        return {"question_number": q_num, "sub_number": sub,
                "answer": "터치입력대기", "score": -1}

    # 그림 문항 → TTS만 + 엔터 대기
    if q_num in VISUAL_QUESTIONS:
        speak("화면을 보시고 답변해 주세요. 완료하시면 확인 버튼을 눌러주세요.")
        input(">>> 완료되면 엔터: ")
        return {"question_number": q_num, "sub_number": sub,
                "answer": "시각문항", "score": -1}

    # 객관식 문항 → TTS만 + 엔터 대기
    if options:
        speak("화면에서 선택해 주세요. 완료하시면 확인 버튼을 눌러주세요.")
        input(">>> 완료되면 엔터: ")
        return {"question_number": q_num, "sub_number": sub,
                "answer": "터치입력대기", "score": -1}

    # 행동 문항 (Q12) → TTS만 + 엔터 대기
    if q_num == 12:
        speak("행동으로 보여주세요. 완료하시면 확인 버튼을 눌러주세요.")
        input(">>> 완료되면 엔터: ")
        return {"question_number": q_num, "sub_number": sub,
                "answer": "행동확인", "score": -1}

    # 1분 제한 문항 (Q13 유창성)
    if q_num in TIMED_QUESTIONS:
        from stt_engine.stt import listen_until_silence
        speak("지금부터 시작합니다.")

        # 60초 동안 말하기, 4초 침묵하면 자동 종료
        answer_text = listen_until_silence(duration=60, silence_sec=4)

        speak("그만.")

        # 단어 개수 세기
        words = [w for w in answer_text.split() if w]
        count = len(words)
        print(f"[CIST] 유창성 단어 수: {count}개 → {answer_text}")
        score = 0 if count <= 8 else (1 if count <= 14 else 2)

        return {"question_number": q_num, "sub_number": sub,
                "answer": answer_text, "score": score}

    # 주관식 문항 → STT로 음성 응답
    speak("말씀해 주세요.")
    time.sleep(1.0)  # TTS 잔향 대기
    user_answer = listen(duration=15)
    print(f"[CIST] 어르신 답변: '{user_answer}'")

    # 모르겠다 / 빈 응답 → LLM 힌트
    if not user_answer.strip() or any(
        w in user_answer for w in ["모르", "몰라", "모르겠", "잘 모르"]
    ):
        hint = ask_llm_hint(text, user_answer)
        speak(hint)
        speak("다시 한번 말씀해 주세요.")
        time.sleep(1.0)  # 여기도 추가
        user_answer = listen(duration=15)

    return {
        "question_number": q_num,
        "sub_number": sub,
        "answer": user_answer,
        "score": -1
    }


def run_cist():
    """CIST 전체 진행"""
    print("=== 🧠 CIST 인지선별검사 시작 ===")
    speak("안녕하세요, 어르신. 지금부터 인지선별검사를 시작하겠습니다. 천천히 편하게 답해주세요.")

    questions = load_questions()
    results = []

    for i, q in enumerate(questions):
        result = conduct_question(q)
        results.append(result)
        speak("감사합니다.")
        time.sleep(0.5)

    speak("검사가 모두 끝났습니다. 수고하셨습니다.")
    print("\n[CIST] 전체 결과:")
    print(json.dumps(results, ensure_ascii=False, indent=2))

    # TODO: EC2 주소 받으면 여기에 POST 추가
    # requests.post(f"{BACKEND_URL}/submit", json={"answers": results})

    return results


if __name__ == "__main__":
    run_cist()
