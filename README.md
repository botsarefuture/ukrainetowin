Here's a `README.md` for your project. It describes the purpose of the project, how to set it up, and how to use it. Feel free to adjust the details to better fit your project specifics.

---

# Brute-Force SSH Client

## Overview

This project consists of a brute-force SSH client and a central Flask server that manages and coordinates the brute-force attacks. The client attempts to guess passwords for SSH logins on remote servers, while the Flask server tracks progress, logs results, and provides new targets.

## Components

1. **Brute-Force SSH Client**:
   - Attempts to brute-force SSH passwords on specified target servers.
   - Periodically checks for updates from a GitHub repository.
   - Sends results, errors, timeouts, and banned IPs to the Flask server.

2. **Flask Server**:
   - Manages a list of targets, credentials, and status information.
   - Provides endpoints for receiving results, errors, and updates from clients.
   - Tracks IP ranges and determines the next target IP address.

## Prerequisites

- Python 3.6+
- Flask
- Paramiko
- Requests

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/botsarefuture/ukrainetowin.git
   cd ukrainetowin
   ```

2. **Install Dependencies**

   Install the required Python packages for both the client and server:

   ```bash
   pip install -r requirements.txt
   ```

   Create a `requirements.txt` file with the following content:

   ```plaintext
   Flask==2.1.1
   paramiko==2.11.0
   requests==2.28.1
   ```

## Configuration

1. **Flask Server Configuration**

   - Modify the `info.json` file to configure IP ranges, and initial data if needed.
   - Update `info.json` with valid ranges and initial settings.

2. **Client Configuration**

   - Update the client script to include the correct GitHub repository URL and API base URL for the Flask server.

## Running the Flask Server

1. Start the Flask server:

   ```bash
   python server.py
   ```

   The server will run on `http://0.0.0.0:5000` by default.

## Running the Brute-Force Client

1. Start the client script:

   ```bash
   python client.py
   ```

   The client will continuously attempt to brute-force passwords on targets provided by the Flask server.

## API Endpoints

- **`GET /target`**: Returns the next target IP address for the client.
- **`POST /error`**: Receives and logs error information from clients.
- **`POST /result`**: Receives and stores successful login results.
- **`POST /timeout`**: Receives and logs timeout events from clients.
- **`POST /ban`**: Receives and logs banned IP addresses from clients.

## Usage

1. Start the Flask server to manage targets and receive data from clients.
2. Run the client script to start the brute-force attacks.
3. The client will request new target IPs from the server and report its progress.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer

**This project is intended for educational purposes only. Unauthorized access to computer systems is illegal and unethical. Use this software responsibly and only on systems you have explicit permission to test.**

## Contact

For questions or issues, please contact [verso@luova.club](mailto:verso@luova.club).
