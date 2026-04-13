import requests
import json
import time

# 로컬에서 돌아가고 있는 llama-server 주소
API_URL = "http://localhost:8080/v1/chat/completions"

def ask_dementia_assistant(user_message):
    headers = {"Content-Type": "application/json"}

    # 시스템 프롬프트와 사용자의 음성 텍스트(STT 결과라고 가정)를 조합
    payload = {
        "messages": [
            {"role": "system", "content": "당신은 어르신들의 치매 선별 검사를 돕는 친절한 안내원입니다. 짧고 다정하게 1~2문장으로 대답해주세요."},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7 # 답변의 다양성 조절 (0.0~1.0)
    }

    start_time = time.time()
    print("🧠 AI가 생각하는 중...")

    try:
        # 서버로 API 요청 보내기
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # 에러 확인

        # JSON 결과 파싱해서 실제 답변 텍스트만 추출
        result = response.json()
        ai_reply = result["choices"][0]["message"]["content"]

        latency = time.time() - start_time
        print(f"⏱️ 응답 시간: {latency:.2f}초")
        return ai_reply

    except Exception as e:
        return f"서버 통신 에러가 발생했습니다: {e}"

# --- 메인 실행 흐름 ---
if __name__ == "__main__":
    print("=== 👵 치매 선별 키오스크 메인 로직 시작 ===")

    # 나중에 이 input() 부분이 마이크(STT)로 대체될 예정!
    while True:
        user_input = input("\n어르신 (종료하려면 q 입력): ")
        if user_input.lower() == 'q':
            break

        answer = ask_dementia_assistant(user_input)
        # 나중에 이 print() 부분이 스피커(TTS)로 대체될 예정!
        print(f"🤖 안내원: {answer}")
