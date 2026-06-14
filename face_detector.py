# ~/kiosk_project/face_detector.py
import cv2
import subprocess

CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

def capture_image(path="/tmp/face_capture.jpg"):
    subprocess.run([
        "rpicam-still", "-o", path,
        "--timeout", "2000", "-n"
    ], capture_output=True)
    return path

def detect_face(image_path=None):
    """
    얼굴 감지 메인 함수
    반환: {"detected": True/False, "count": N, "faces": [(x,y,w,h)]}
    """
    if image_path is None:
        image_path = capture_image()

    img = cv2.imread(image_path)
    if img is None:
        return {"detected": False, "count": 0, "faces": []}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(150, 150)  # 오탐지 필터링 (100→150)
    )

    result = {
        "detected": len(faces) > 0,
        "count": len(faces),
        "faces": [{"x": int(x), "y": int(y), "w": int(w), "h": int(h)}
                  for (x, y, w, h) in faces]
    }

    print(f"[FACE] 감지 결과: {result['count']}명", flush=True)
    return result

if __name__ == "__main__":
    result = detect_face()
    if result["detected"]:
        print(f"얼굴 {result['count']}개 감지!")
        for f in result["faces"]:
            print(f"  위치: ({f['x']}, {f['y']}) 크기: {f['w']}x{f['h']}")
    else:
        print("얼굴 감지 안 됨")
