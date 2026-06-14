# 🧠 치매 선별 키오스크 — 임베디드 AI 파이프라인

> 캡스톤 디자인 | 경로당(6조) | 임베디드 파트

---

## 📖 About

치매 조기 발견을 위한 온디바이스 AI 키오스크 프로젝트.
보건소 또는 지하철역 등 공공장소에 설치하여 어르신이 대기 시간 중
CIST(인지선별검사)를 음성으로 진행할 수 있도록 돕는 시스템.
모든 AI 연산(STT, LLM, TTS)은 클라우드 없이 Raspberry Pi 5 단독으로 처리하며,
검사 결과는 AWS 백엔드로 전송 후 치매안심센터 예약까지 연결된다.

---
## 📅 개발 기간

| 기간 | 내용 |
|---|---|
| 2026.03 | 프로젝트 기획 및 하드웨어 구성 확정 |
| 2026.04.09 | llama.cpp 빌드 및 LLM 온디바이스 구동 |
| 2026.04.13 | STT-LLM-TTS 전체 파이프라인 통합 |
| 2026.04.18 | STT 서버 분리 및 USB 마이크 설정 |
| 2026.04.27 | VAD 적용 및 CIST 문항별 처리 분리 |
| 2026.05.10 | TTS 서버 구현 및 Chromium 키오스크 연동 |
| 2026.05.23 | RPi Camera Module 연결 및 MediaPipe 포팅 |
| 2026.06.14 | 프론트엔드 통합 및 STT 후처리 구현 |

---
## 🏗️ 시스템 아키텍처

### 음성 AI 파이프라인

```
[사용자 음성 입력]
        ↓
     [STT] — Whisper small (localhost:8081)
        ↓
     [LLM] — Qwen2.5-3B-Instruct (localhost:8080)
        ↓
     [TTS] — edge-tts (ko-KR-SunHiNeural, localhost:8082)
        ↓
  [음성 출력 (JBL 블루투스 / wm8960 HAT)]
```

### 전체 시스템 구성

```
[Raspberry Pi 5]
        │
        ├── [터치 모니터 15.6"] ── Chromium 키오스크
        │         │
        │    [start.html] ──→ [index.html] ──→ [face_main.py]
        │         │                │                  │
        │    TTS 안내음성      CIST 설문 진행      표정 분석
        │
        ├── [wm8960 HAT]
        │    ├── MEMS 마이크 (STT 입력)
        │    └── 스피커 출력
        │
        ├── [JBL Bluetooth] ── TTS 음성 출력
        │
        └── [RPi Camera Module imx219]
                  │
            MediaPipe 얼굴 분석
            (표정 변화 점수, 무표정 감지)

[서버 포트 구성]
  8080 → llama-server    (LLM 추론)
  8081 → stt_server.py   (Whisper STT)
  8082 → tts_server.py   (edge-tts TTS)
  8083 → face_server.py  (얼굴 감지)
  8000 → face_main.py    (MediaPipe 분석)
  3000 → http.server     (프론트엔드)

[클라우드 연동 - AWS]
  GET  /cist/questions  → CIST 문항 수신
  POST /cist/submit     → 검사 결과 전송 (예정)
  POST /api/reservation → 치매센터 예약
```
---

## 🖥️ 하드웨어 사양

```
| 항목 | 사양 |
|---|---|
| 보드 | Raspberry Pi 5 |
| CPU | 64-bit Quad-core (ARM Cortex-A76) |
| RAM | 8GB SDRAM |
| 스토리지 | Micro SD 128GB |
| 오디오 출력 | Asul RPI Voice HAT (WM8960, card 2) |
| 마이크 입력 | wm8960 HAT 내장 MEMS 마이크 (DEVICE_INDEX=1) |
| 블루투스 스피커 | JBL Pulse 2 (A2DP) |
| 모니터 | 15.6인치 터치 모니터 (HDMI) |
| 카메라 | WEKIT 광각 카메라 모듈 (imx219, CSI) |
```

---

## 📁 폴더 구조

```
~/kiosk_project/
|-- kiosk_main.py            # 메인 실행 파일 (STT+LLM+TTS 통합)
|-- cist_runner.py           # CIST 설문 진행 메인 로직
|-- cist_questions.json      # CIST 문항 로컬 데이터
|-- face_detector.py         # OpenCV 얼굴 감지 모듈
|-- face_server.py           # 얼굴 인식 HTTP 서버 (port 8083)
|-- start_kiosk.sh           # 통합 실행 스크립트
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- llama.cpp/               # LLM 엔진 (CMake 빌드)
|   |-- build/bin/
|   |   |-- llama-server     # 백그라운드 LLM 서버 (port 8080)
|   |-- models/qwen/
|       |-- qwen2.5-3b-instruct-q4_k_m.gguf  # .gitignore 제외
|-- stt_engine/
|   |-- stt_server.py        # Whisper 백그라운드 서버 (port 8081)
|   |-- stt.py               # STT HTTP 클라이언트
|-- tts_engine/
|   |-- tts_server.py        # edge-tts TTS 서버 (port 8082)
|   |-- tts.py               # TTS 직접 호출 모듈
|-- front_page/              # 프론트엔드 (front 브랜치 클론)
    |-- start.html           # 시작 화면
    |-- index.html           # CIST 설문 화면
    |-- face_main.py         # MediaPipe 얼굴 분석 서버 (port 8000)
    |-- face_landmarker.task # MediaPipe 모델 파일
```

---

## 🙋 나의 역할 및 핵심 기여

### 담당 파트: 임베디드 AI 파이프라인 (Raspberry Pi 5)

- **라즈베리파이 제어:**
  - 온디바이스 STT-LLM-TTS 파이프라인 구축 (Whisper + Qwen2.5-3B + edge-tts)
  - Whisper STT 백그라운드 서버 분리로 실행 속도 개선 (30~60초 → 2~3초)
  - CIST 설문 음성 진행 로직 구현 (문항별 TTS 출력 + VAD STT + LLM 힌트)
  - 시작 화면 구현 (start.html) 및 Chromium 키오스크 모드 연동
  - MediaPipe 얼굴 분석 서버 RPi5 포팅 (rpicam-vid 스트리밍 방식)
  - OpenCV Haar Cascade 얼굴 감지 모듈 구현

- **통신 및 데이터 처리:**
  - llama-server / STT 서버 / TTS 서버 HTTP API 로컬 통신
  - 백엔드 EC2 GET /cist/questions 문항 수신 (연동 예정)
  - CORS 설정으로 Chromium ↔ 로컬 서버 통신

- 📌 **내가 작성한 주요 코드 파일:**
  - `kiosk_main.py` — 메인 실행 파일
  - `cist_runner.py` — CIST 설문 진행 로직
  - `stt_engine/stt_server.py` — Whisper 백그라운드 서버
  - `tts_engine/tts_server.py` — TTS HTTP 서버
  - `face_detector.py` — OpenCV 얼굴 감지
  - `face_server.py` — 얼굴 인식 HTTP 서버
  - `front_page/start.html` — 시작 화면
  - `front_page/face_main.py` — MediaPipe 얼굴 분석 (RPi5 포팅)

---

## ✅ 완료된 작업

### ~ 2026.04.09
- llama.cpp CMake 빌드 완료
- Qwen2.5-3B-Instruct-Q4_K_M 모델 구동 확인
- llama-server 백그라운드 아키텍처 확정
- 다국어 환각(Hallucination) 방지 로직 구현

### ~ 2026.04.13
- Asul RPI Voice HAT WM8960 드라이버 설치
- STT 엔진 구현 (Whisper small, 48000Hz→16000Hz 다운샘플링)
- TTS 엔진 구현 (edge-tts ko-KR-SunHiNeural)
- STT → LLM → TTS 전체 파이프라인 통합 완료

### ~ 2026.04.18
- STT 서버 분리 (Whisper Flask 서버, port 8081)
- 실행 속도 개선 (30~60초 → 2~3초)
- ALSA 입출력 분리 설정
- scipy.signal.resample로 정확한 리샘플링

### ~ 2026.04.27
- VAD 적용 (말 감지 → 4초 침묵 → 자동 종료)
- CIST 문항별 처리 분리 (5가지 타입)
- JBL 블루투스 스피커 연결

### ~ 2026.05.10
- TTS 서버 구현 (port 8082, CORS 적용)
- 시작 화면 구현 (start.html)
- TTS 완료 후 STT 자동 시작 연계
- TTS 첫 글자 짤림 방지 (무음 패딩 0.3초)
- 로컬 HTTP 서버 방식으로 전환 (python3 -m http.server 3000)

### ~ 2026.05.23
- RPi Camera Module (imx219) 연결 및 인식 성공
- OpenCV Haar Cascade 얼굴 감지 구현
- MediaPipe 0.10.9 설치 성공 (pyenv Python 3.11.9)
- face_main.py RPi5 포팅 (rpicam-vid MJPEG 스트리밍)
- 얼굴 분석 서버 동작 확인 (표정 변화 점수, 무표정 감지)

### ~ 2026.06.14
- launch_kiosk.py 통합 런처 적용 (face_env/kiosk_env 자동 전환)
- TTS 서버 launch_kiosk.py 연동 (port 8082)
- index.html TTS 자동 재생 + STT 자동 시작 연동
- Q3 기억등록 지시문 화면 숨김 처리
- 처음부터 다시하기 버튼 TTS 연동
- STT 후처리(postprocess) 구현
  - 연도/월/일/요일 한글→숫자 보정
  - 유사 발음 보정 (칫솔, 그네, 주사위, 산강수금)
  - initial_prompt로 인식률 개선
- Chromium keyring 팝업 제거
- 백엔드 EC2 연동 완료 (http://3.35.210.123:8000)
- face_main.py RPi5 카메라 스레드 재적용 (rpicam-vid 방식)
  - 팀원 코드 업데이트 후 cv2.VideoCapture 방식으로 덮어씌워진 것 복구
  - camera_thread + frame_lock 방식으로 재포팅

---

## 🐛 트러블슈팅

### ✅ 해결된 문제

**문제 1 — make -j4 빌드 실패**
- 원인: llama.cpp가 CMake 방식으로 전환
- 해결: `cmake -B build && cmake --build build --config Release -j4`

**문제 2 — 다국어 환각(Hallucination)**
- 원인: Qwen 중국어 기반 모델 → 컨텍스트 길어지면 중국어 회귀
- 해결: 시스템 프롬프트 이중 강화(EN+KR) + temperature=0.3 + 한글 감지 안전장치 + 히스토리 12개 제한

**문제 3 — PaErrorCode -9997 (Invalid sample rate)**
- 원인: WM8960 HAT(48000Hz) vs Whisper 요구(16000Hz) 불일치
- 해결: scipy.signal.resample로 48000→16000Hz 정확 변환

**문제 4 — Device or resource busy (장치 충돌)**
- 원인: STT(마이크)와 TTS(스피커)가 ALSA default 장치 충돌
- 해결: ~/.asoundrc에서 입출력 장치 명시적 분리

**문제 5 — TTS 첫 글자 짤림**
- 원인: mpg123 오디오 버퍼 초기화 지연 (0.2~0.3초)
- 해결: ffmpeg으로 0.3초 무음 패딩을 TTS 파일 앞에 추가

**문제 6 — Chromium CORS 차단**
- 원인: 브라우저가 localhost Flask 서버 요청을 cross-origin으로 차단
- 해결: flask-cors 설치 후 CORS(app) 적용, host=0.0.0.0으로 변경

**문제 7 — RPi Camera 인식 실패**
- 원인: config.txt에 dtoverlay=imx708 설정이 있었으나 실제 센서는 imx219
- 해결: dtoverlay=imx219로 교체 후 인식 성공

**문제 8 — mediapipe-rpi4 Python 버전 호환 불가**
- 원인: mediapipe-rpi4는 Python 3.9용, 시스템은 Python 3.13
- 해결: pyenv로 Python 3.11.9 설치 → mediapipe 0.10.9 공식 버전 설치 성공

**문제 9 — face_main.py cv2.VideoCapture RPi 카메라 인식 불가**
- 원인: RPi 카메라는 V4L2 직접 접근 불가, libcamera 방식 필요
- 해결: rpicam-vid MJPEG 스트리밍을 subprocess로 실행 후 JPEG 파싱하여 OpenCV 프레임으로 변환

**문제 10 — launch_kiosk.py face_main.py mediapipe 오류**
- 원인: launch_kiosk.py가 kiosk_env(Python 3.13)로 face_main.py 실행
- 해결: face_main.py 실행 시 /home/pi/face_env/bin/python 명시적 지정

**문제 11 — TTS 서버 launch_kiosk.py에서 실행 안 됨**
- 원인: tts_server.py가 front_page/tts_engine/에 없고 kiosk_project/tts_engine/에 있음
- 해결: 절대 경로 /home/pi/kiosk_project/tts_engine/tts_server.py로 지정

**문제 12 — Chromium keyring 팝업**
- 원인: Chromium이 비밀번호 저장을 위해 GNOME Keyring 접근 시도
- 해결: --password-store=basic --use-mock-keychain 옵션 추가

**문제 13 — STT 숫자 환각 (5 5 5 5... 무한 반복)**
- 원인: initial_prompt에 숫자 힌트 넣었더니 Whisper가 힌트를 그대로 반복
- 해결: initial_prompt에서 숫자 제거, 고정 단어(칫솔/그네/주사위 등)만 유지

- **문제 14 — face_main.py git pull 후 카메라 블랙 스크린**
- 원인: front 브랜치 업데이트로 camera_thread 코드가 cv2.VideoCapture(0)으로 덮어씌워짐
- 해결: rpicam-vid subprocess + frame_lock 방식 재적용

---

## 🚀 실행 방법

### 사전 준비 (공통)

```bash
# 블루투스 스피커 연결
bluetoothctl
connect [블루투스_MAC_주소]
exit

# 오디오 출력 설정
pactl set-default-sink bluez_output.[MAC주소_언더바].1
```

### 통합 실행 (추천)
```bash
cd ~/kiosk_project/front_page
source ~/kiosk_env/bin/activate
DISPLAY=:0 python launch_kiosk.py --no-backend
```

### 개별 실행

```bash
# 1. 가상환경 활성화
source ~/kiosk_env/bin/activate

# 2. LLM 서버 (터미널 1)
cd ~/kiosk_project/llama.cpp
./build/bin/llama-server \
  -m models/qwen/qwen2.5-3b-instruct-q4_k_m.gguf \
  -c 2048 -n 256 -t 4 \
  --host 127.0.0.1 --port 8080 \
  --log-disable &

# 3. STT 서버 (터미널 2)
python ~/kiosk_project/stt_engine/stt_server.py

# 4. TTS 서버 (터미널 3)
python ~/kiosk_project/tts_engine/tts_server.py

# 5. 얼굴 분석 서버 (터미널 4)
source ~/face_env/bin/activate
cd ~/kiosk_project/front_page
python face_main.py

# 6. 프론트 로컬 서버 (터미널 5)
cd ~/kiosk_project/front_page
python3 -m http.server 3000

# 7. Chromium 실행 (모니터에서)
DISPLAY=:0 chromium --kiosk http://localhost:3000/start.html
```

### CIST 음성 모드 실행

```bash
source ~/kiosk_env/bin/activate
cd ~/kiosk_project
python cist_runner.py
```

---

## 🔧 의존성

### 시스템 패키지

```bash
sudo apt install -y portaudio19-dev python3-pyaudio ffmpeg mpg123 \
  chromium libcamera-apps i2c-tools bluetooth bluez \
  pulseaudio pulseaudio-module-bluetooth
```

### Python 패키지 (kiosk_env — Python 3.13)

```bash
pip install -r requirements.txt
# 핵심: openai-whisper sounddevice numpy scipy pyaudio
#       requests edge-tts flask flask-cors opencv-python-headless
```

### Python 패키지 (face_env — Python 3.11.9)

```bash
source ~/face_env/bin/activate
pip install mediapipe==0.10.9 fastapi uvicorn \
  opencv-python-headless numpy websockets
```

### Linux (Raspberry Pi OS)

```bash
# pyenv 설치 (Python 3.11.9용)
curl https://pyenv.run | bash
pyenv install 3.11.9
python3.11 -m venv ~/face_env
```

### Windows

```bash
# PowerShell
python -m venv venv
venv\Scripts\activate
pip install mediapipe fastapi uvicorn opencv-python numpy websockets
```

### macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install mediapipe fastapi uvicorn opencv-python numpy websockets
```

---

## 🔜 다음 작업 예정
- [ ] face_main.py 결과를 백엔드로 전송
- [ ] VAD 정확도 개선 (주변 소음 환경)
- [ ] STT 인식률 개선 (마이크 위치 최적화)
