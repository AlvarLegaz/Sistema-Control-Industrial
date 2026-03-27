from flask import Flask, request, jsonify
from planta import Planta
import threading
import time

app = Flask(__name__)
planta = Planta()


# ---------------- LOOP DE SIMULACIÓN ----------------
def simulation_loop():
    while True:
        planta.update()
        time.sleep(0.5)


threading.Thread(target=simulation_loop, daemon=True).start()


# ---------------- ENDPOINTS ----------------

@app.route("/state", methods=["GET"])
def get_state():
    return jsonify(planta.get_state())


@app.route("/command", methods=["POST"])
def command():
    data = request.json
    planta.command(data)
    return jsonify({"status": "ok"})


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)