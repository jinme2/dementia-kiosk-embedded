# ~/kiosk_project/face_server.py
from flask import Flask, jsonify
from flask_cors import CORS
from face_detector import detect_face

app = Flask(__name__)
CORS(app)

@app.route("/face/detect", methods=["POST"])
def detect():
    result = detect_face()
    return jsonify(result)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8083, debug=False)
