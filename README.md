# 🧠 치매 선별 키오스크 — 임베디드 AI 파이프라인

> 캡스톤 디자인 | 경로당(6조) | 임베디드 파트

---

## 📋 프로젝트 개요

어르신이 CIST(인지선별검사) 설문 중 어려운 문항을 만났을 때,
**음성으로 질문하면 AI가 힌트를 제공하는** 온디바이스 AI 파이프라인.
모든 AI 연산은 클라우드 없이 Raspberry Pi 5 단독으로 처리.


[사용자 음성 입력]
↓
[STT] — Whisper (한국어)
↓
[LLM] — Qwen2.5-3B-Instruct (llama.cpp)
↓
[TTS] — 음성 출력

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

~/kiosk_project/
├── kiosk_main.py          # 메인 실행 파일 (LLM API 클라이언트)
├── README.md
├── .gitignore
├── llama.cpp/             # LLM 엔진 (CMake 빌드)
│   └── models/
│       └── qwen/
│           └── qwen2.5-3b-instruct-q4_k_m.gguf  # ← .gitignore로 제외
├── stt_engine/            # STT 모듈 (예정)
└── tts_engine/            # TTS 모듈 (예정)

---

## ✅ 완료된 작업 (~ 2026.04.09)

### 1. 초기 환경 세팅
```bash
uname -m          # aarch64 (64bit 확인)
free -h           # 가용 RAM 7.3Gi 확인
sudo apt install build-essential cmake git wget curl -y
python3 -m venv kiosk_env
source kiosk_env/bin/activate
```

### 2. llama.cpp 빌드 (CMake 방식)

> ⚠️ 트러블슈팅: `make -j4` 방식은 최신 llama.cpp에서 폐기됨 → CMake로 전환

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build --config Release -j4
```

빌드 결과물 위치: `./build/bin/llama-server`, `./build/bin/llama-cli`

### 3. Qwen2.5-3B 모델 다운로드

```bash
mkdir -p models/qwen && cd models/qwen
wget https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf
```

- 모델 크기: 약 2.4GB (4비트 양자화 Q4_K_M)

### 4. LLM 성능 측정 결과

| 지표 | 결과 | 설명 |
|---|---|---|
| TTFT (첫 토큰 지연) | 평균 7~8초 | 첫 번째 질문 기준 |
| TPS (생성 속도) | 평균 5.8 t/s | -j4 + Q4_K_M 최적화 |
| Total Latency (예상) | 10~13초 | STT 2~3초 + TTFT 7~8초 + TTS 1~2초 |

> 💡 두 번째 질문부터 TTFT 1~2초로 급감 → KV 캐싱 효과 확인

### 5. 아키텍처 결정: llama-server 백그라운드 상시 실행

```bash
# llama-server 실행 (백그라운드)
cd ~/kiosk_project/llama.cpp
./build/bin/llama-server \
  -m models/qwen/qwen2.5-3b-instruct-q4_k_m.gguf \
  -c 2048 -n 256 -t 4 \
  --host 127.0.0.1 --port 8080 \
  --log-disable &
```

기존 `llama-cli` 방식 대비 장점:
- 모델·KV Cache를 RAM에 상주 → 매번 로딩 불필요
- AI 연산과 UI/음성 프로세스 완전 분리
- `localhost:8080` HTTP API로 Python에서 호출

---

## 🐛 발견된 문제 및 트러블슈팅

### 문제 1 — make -j4 빌드 실패
- **원인**: llama.cpp가 CMake 방식으로 전환됨
- **해결**: `cmake -B build && cmake --build build --config Release -j4`

### 문제 2 — `-c 512` 설정으로 대화 중 강제 종료
- **원인**: 시스템 프롬프트 + 대화 기록이 512 토큰을 빠르게 채움
- **해결**: `-c 2048`로 증가

### ⚠️ 문제 3 — 다국어 환각(Hallucination): 대화 지속 시 중국어·일본어로 응답

**가장 중요한 이슈.** Qwen은 원래 중국어 기반 모델이라,
컨텍스트가 길어지면 중국어/일본어로 응답이 회귀하는 현상 발생.

**발생 조건:**
- 동일 세션에서 대화 4~5턴 이상 지속
- 컨텍스트 윈도우가 절반 이상 채워졌을 때

**해결 방법 (현재 `kiosk_main.py`에 반영):**

1. **시스템 프롬프트 이중 강화**: 한국어 명시를 영문+한글 동시 작성
```python
    "You must respond ONLY in Korean language. Never use Chinese or Japanese."
    "반드시 한국어로만 대답해주세요."
```

2. **온도(temperature) 낮춤**: `0.3` 설정으로 창의적 변형 억제

3. **max_tokens 제한**: `100` 토큰으로 응답 길이 제한 → 불필요한 언어 전환 방지

4. **한국어 감지 안전장치**: 응답에 한글(가-힣)이 없으면 재질문 유도
```python
    if not any('\uAC00' <= ch <= '\uD7A3' for ch in reply):
        return "죄송합니다, 다시 한번 말씀해 주시겠어요?"
```

5. **컨텍스트 히스토리 제한**: 최근 6턴만 유지하여 컨텍스트 오염 방지

---

## 🔜 다음 작업 예정

- [ ] Asul RPI Voice HAT WM8960 드라이버 설치 및 마이크/스피커 세팅
- [ ] STT 연결: Whisper `small` 모델 (한국어)
- [ ] TTS 연결: edge-tts `ko-KR-SunHiNeural`
- [ ] 전체 파이프라인 통합 (STT → LLM → TTS)
- [ ] 스플래시 스크린 (Time Masking) 구현

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

# 3. 서버 대기
sleep 10

# 4. 메인 실행 (텍스트 모드)
cd ~/kiosk_project
python kiosk_main.py
```

---

## 🔧 의존성

```bash
pip install requests langdetect
```
