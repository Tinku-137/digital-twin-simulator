# bridge_server.py
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow Streamlit or browsers to fetch if needed

latest_data = {
    "temp": 0.0,
    "vibration": 0.0,
    "sound": 0.0,
    "current": 0.0,
    "current_amps": None
}

@app.route("/update", methods=["POST"])
def update():
    global latest_data
    data = request.get_json(force=True)
    # Save what you receive; keep names consistent
    latest_data.update(data)
    return "OK", 200

@app.route("/latest", methods=["GET"])
def latest():
    return jsonify(latest_data)

if __name__ == "__main__":
    # host 0.0.0.0 so ESP32 can reach it on LAN
    app.run(host="0.0.0.0", port=5000)
