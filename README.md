# 🧠 치매 선별 키오스크 — 임베디드 AI 파이프라인

> 캡스톤 디자인 | 경로당(6조) | 임베디드 파트

---

## 📋 프로젝트 개요

어르신이 CIST(인지선별검사) 설문 중 어려운 문항을 만났을 때,
**음성으로 질문하면 AI가 힌트를 제공하는** 온디바이스 AI 파이프라인.
모든 AI 연산은 클라우드 없이 Raspberry Pi 5 단독으로 처리.

```
[사용자 음성 입력]
↓
[STT] — Whisper small (localhost:8081)
↓
[LLM] — Qwen2.5-3B-Instruct (localhost:8080)
↓
[TTS] — edge-tts (ko-KR-SunHiNeural)
↓
[음성 출력 (wm8960 HAT)]
```

---

## 🖥️ 하드웨어 사양

| 항목 | 사양 |
|---|---|
| 보드 | Raspberry Pi 5 |
| CPU | 64-bit Quad-core (ARM Cortex-A76) |
| RAM | 8GB SDRAM |
| 스토리지 | Micro SD 128GB |
| 오디오 출력 | Asul RPI Voice HAT (WM8960, card 2) |
| 마이크 입력 | USB PnP Sound Device (card 3, 44100Hz) |
| 접속 방식 | SSH Headless |

---

## 📁 폴더 구조

```
~/kiosk_project/
|-- kiosk_main.py          # 메인 실행 파일 (STT+LLM+TTS 통합)
|-- kiosk_main_backup.py   # 이전 버전 백업
|-- cist_runner.py         # CIST 설문 진행 메인 로직 (신규)
|-- cist_questions.json    # CIST 문항 로컬 데이터 (신규)
|-- README.md
|-- .gitignore
|-- llama.cpp/             # LLM 엔진 (CMake 빌드)
|   |-- build/bin/
|   |   |-- llama-server   # 백그라운드 LLM 서버 (port 8080)
|   |-- models/qwen/
|       |-- qwen2.5-3b-instruct-q4_k_m.gguf  # .gitignore 제외
|-- stt_engine/
|   |-- stt_server.py      # Whisper 백그라운드 서버 (port 8081)
|   |-- stt.py             # STT HTTP 클라이언트
|-- tts_engine/
    |-- tts.py             # edge-tts 음성 출력
```

---

## ✅ 완료된 작업

### ~ 2026.04.09
- llama.cpp CMake 빌드 완료
- Qwen2.5-3B-Instruct-Q4_K_M 모델 구동 확인
- llama-server 백그라운드 아키텍처 확정
- TTFT/TPS 성능 측정 (TTFT 7~8초, TPS 5.8 t/s)
- 다국어 환각(Hallucination) 방지 로직 구현

### ~ 2026.04.13
- Asul RPI Voice HAT WM8960 드라이버 설치
- STT 엔진 구현 (Whisper small, 48000Hz→16000Hz 다운샘플링)
- TTS 엔진 구현 (edge-tts ko-KR-SunHiNeural)
- STT → LLM → TTS 전체 파이프라인 통합 완료
- LLM 응답 시간 2~4초 확인

### ~ 2026.04.18
- STT 서버 분리 (Whisper Flask 서버, port 8081)
- 실행 속도 개선: 30\~60초 → 2\~3초
- USB 마이크 추가 연결 (card 3, 44100Hz)
- ALSA 입출력 분리 (.asoundrc)
  - 입력: USB 마이크 (hw:3,0)
  - 출력: wm8960 HAT (hw:2,0)
- scipy.signal.resample로 44100→16000Hz 정확 변환

### ~ 2026.04.20
- HAT 마이크 .asoundrc 충돌 해결 및 인식률 복구
- CIST JSON API 구조 분석 (19문항, 6영역, 30점)
- cist_runner.py 구현 (TTS+STT+LLM 힌트 통합)
  - 문항 타입별 처리 (음성/그림/기억등록/유창성)
  - 백엔드 실패 시 로컬 JSON 폴백
  - 모르겠다 감지 → LLM 힌트 제공
---

## 🐛 트러블슈팅

### 문제 1 — make -j4 빌드 실패
- **원인**: llama.cpp가 CMake 방식으로 전환
- **해결**: `cmake -B build && cmake --build build --config Release -j4`

### 문제 2 — 다국어 환각(Hallucination)
- **원인**: Qwen 중국어 기반 모델 → 컨텍스트 길어지면 중국어 회귀
- **해결**: 시스템 프롬프트 이중 강화 + temperature=0.3 + 한글 감지 안전장치

### 문제 3 — PaErrorCode -9997 (Invalid sample rate)
- **원인**: WM8960(48000Hz) vs Whisper(16000Hz) 불일치
- **해결**: [::3] 다운샘플링 → scipy.signal.resample로 정확 변환

### 문제 4 — Device or resource busy (장치 충돌)
- **원인**: STT(USB 마이크)와 TTS(wm8960)가 ALSA default 장치 충돌
- **해결**: ~/.asoundrc에서 입출력 장치 명시적 분리

### ⚠️ Known Issue — 공공장소 소음 수음
- **원인**: USB 마이크 무지향성 + 쿨링팬 소음 + 주변 환경 소음
- **해결 예정**: VAD(webrtcvad) 적용으로 음성 구간만 STT 처리

---

## 🚀 실행 방법

```bash
# 1. 가상환경 활성화
source ~/kiosk_env/bin/activate

# 2. LLM 서버 실행 (터미널 1)
cd ~/kiosk_project/llama.cpp
./build/bin/llama-server \
  -m models/qwen/qwen2.5-3b-instruct-q4_k_m.gguf \
  -c 2048 -n 256 -t 4 \
  --host 127.0.0.1 --port 8080 \
  --log-disable &

# 3. STT 서버 실행 (터미널 2)
python ~/kiosk_project/stt_engine/stt_server.py

# 4. 메인 실행 (터미널 3)
cd ~/kiosk_project
python kiosk_main.py voice
```

---

## 🔜 다음 작업 예정

- [ ] VAD 적용 (webrtcvad) — 소음 환경 음성 감지
- [ ] EC2 주소 확정 후 POST /cist/submit 백엔드 연동
- [ ] 그림 문항 화면 표시 (터치스크린 연동)
- [ ] 전체 CIST 파이프라인 실제 동작 테스트

---

## 🔧 의존성
```bash
# 시스템 패키지
sudo apt install -y portaudio19-dev python3-pyaudio ffmpeg mpg123

# Python 패키지
pip install openai-whisper sounddevice numpy pyaudio requests edge-tts
```
