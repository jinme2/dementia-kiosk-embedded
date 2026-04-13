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
[STT] — Whisper small (한국어)
↓
[LLM] — Qwen2.5-3B-Instruct (llama.cpp)
↓
[TTS] — edge-tts (ko-KR-SunHiNeural)
```

---

## 🖥️ 하드웨어 사양

| 항목 | 사양 |
|---|---|
| 보드 | Raspberry Pi 5 |
| CPU | 64-bit Quad-core (ARM Cortex-A76) |
| RAM | 8GB SDRAM |
| 스토리지 | Micro SD 128GB |
| 오디오 모듈 | Asul RPI Voice HAT (WM8960, MEMS 마이크 2개 내장) |
| 접속 방식 | SSH Headless |

---

## 📁 폴더 구조

```
~/kiosk_project/
|-- kiosk_main.py          # 메인 실행 파일 (STT+LLM+TTS 통합)
|-- kiosk_main_backup.py   # 이전 버전 백업
|-- README.md
|-- .gitignore
|-- llama.cpp/             # LLM 엔진 (CMake 빌드)
|   |-- build/bin/
|   |   |-- llama-server   # 백그라운드 AI 서버
|   |-- models/qwen/
|       |-- qwen2.5-3b-instruct-q4_k_m.gguf  # .gitignore 제외
|-- stt_engine/
|   |-- stt.py             # Whisper STT + 다운샘플링
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

---

## 🐛 트러블슈팅

### 문제 1 — make -j4 빌드 실패
- **원인**: llama.cpp가 CMake 방식으로 전환
- **해결**: `cmake -B build && cmake --build build --config Release -j4`

### 문제 2 — `-c 512` 설정으로 대화 중 강제 종료
- **원인**: 시스템 프롬프트 + 대화 기록이 512 토큰 초과
- **해결**: `-c 2048`로 증가

### ⚠️ 문제 3 — 다국어 환각(Hallucination)
- **원인**: Qwen 중국어 기반 모델 → 컨텍스트 길어지면 중국어 회귀
- **해결**: 시스템 프롬프트 이중 강화 + temperature=0.3 + 한글 감지 안전장치 + 히스토리 12개 제한

### 문제 4 — PaErrorCode -9997 (Invalid sample rate)
- **원인**: WM8960 하드웨어(48000Hz) vs Whisper 요구(16000Hz) 불일치
- **해결**: 48000Hz 녹음 후 `[::3]` 슬라이싱으로 16000Hz 다운샘플링

---

## 🚀 실행 방법

```bash
# 1. 가상환경 활성화
source ~/kiosk_env/bin/activate

# 2. llama-server 백그라운드 실행
cd ~/kiosk_project/llama.cpp
./build/bin/llama-server \
  -m models/qwen/qwen2.5-3b-instruct-q4_k_m.gguf \
  -c 2048 -n 256 -t 4 \
  --host 127.0.0.1 --port 8080 \
  --log-disable &

# 3. 텍스트 모드 테스트
cd ~/kiosk_project
python kiosk_main.py text

# 4. 음성 모드 실행
python kiosk_main.py voice
```

---

## 🔜 다음 작업 예정

- [ ] VAD 적용 (webrtcvad) — 고정 5초 녹음 → 자동 발화 감지
- [ ] 백엔드 EC2 API 연결 — CIST 설문 JSON 연동
- [ ] 스플래시 스크린 (Time Masking) 구현

---

## 🔧 의존성

```bash
# 시스템 패키지
sudo apt install -y portaudio19-dev python3-pyaudio ffmpeg mpg123

# Python 패키지
pip install openai-whisper sounddevice numpy pyaudio requests edge-tts
```
