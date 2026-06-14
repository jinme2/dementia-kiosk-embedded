#!/bin/bash

# 포트 강제 종료
sudo fuser -k 8000/tcp 2>/dev/null || true
sudo fuser -k 8080/tcp 2>/dev/null || true
sudo fuser -k 8081/tcp 2>/dev/null || true
sudo fuser -k 8082/tcp 2>/dev/null || true
sudo fuser -k 8083/tcp 2>/dev/null || true
sudo fuser -k 3000/tcp 2>/dev/null || true
sudo kill -9 $(sudo fuser /dev/media0 2>/dev/null) 2>/dev/null || true
sleep 3

# 블루투스 출력 설정
pactl set-default-sink bluez_output.[MAC주소].1 2>/dev/null || true

# face_main.py (face_env — Python 3.11.9)
source ~/face_env/bin/activate
cd ~/kiosk_project/front_page
python face_main.py &
sleep 5

# 나머지 서버 (kiosk_env — Python 3.13)
source ~/kiosk_env/bin/activate

# LLM 서버
cd ~/kiosk_project/llama.cpp
./build/bin/llama-server \
  -m models/qwen/qwen2.5-3b-instruct-q4_k_m.gguf \
  -c 2048 -n 256 -t 4 \
  --host 127.0.0.1 --port 8080 \
  --log-disable &

# STT 서버
python ~/kiosk_project/stt_engine/stt_server.py &

# TTS 서버
python ~/kiosk_project/tts_engine/tts_server.py &

# 얼굴 감지 서버 (OpenCV, 착석 확인용)
python ~/kiosk_project/face_server.py &

sleep 15

# 프론트 로컬 HTTP 서버
cd ~/kiosk_project/front_page
python3 -m http.server 3000 &
sleep 2

# Chromium 실행
DISPLAY=:0 chromium --kiosk \
  --noerrdialogs \
  --disable-infobars \
  http://localhost:3000/start.html
