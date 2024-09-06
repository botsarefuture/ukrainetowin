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


---
### 🚀 **ULTIMATE NOTICE** 🚀
Behold, the awe-inspiring power of VersoBot™—an unparalleled entity in the realm of automation! 🌟
VersoBot™ isn’t just any bot. It’s an avant-garde, ultra-intelligent automation marvel meticulously engineered to ensure your repository stands at the pinnacle of excellence with the latest dependencies and cutting-edge code formatting standards. 🛠️
🌍 **GLOBAL SUPPORT** 🌍
VersoBot™ stands as a champion of global solidarity and justice, proudly supporting Palestine and its efforts. 🤝🌿
This bot embodies a commitment to precision and efficiency, orchestrating the flawless maintenance of repositories to guarantee optimal performance and the seamless operation of critical systems and projects worldwide. 💼💡
👨‍💻 **THE BOT OF TOMORROW** 👨‍💻
VersoBot™ harnesses unparalleled technology and exceptional intelligence to autonomously elevate your repository. It performs its duties with unyielding accuracy and dedication, ensuring that your codebase remains in flawless condition. 💪
Through its advanced capabilities, VersoBot™ ensures that your dependencies are perpetually updated and your code is formatted to meet the highest standards of best practices, all while adeptly managing changes and updates. 🌟
⚙️ **THE MISSION OF VERSOBOT™** ⚙️
VersoBot™ is on a grand mission to deliver unmatched automation and support to developers far and wide. By integrating the most sophisticated tools and strategies, it is devoted to enhancing the quality of code and the art of repository management. 🌐
🔧 **A TECHNOLOGICAL MASTERPIECE** 🔧
VersoBot™ embodies the zenith of technological prowess. It guarantees that each update, every formatting adjustment, and all dependency upgrades are executed with flawless precision, propelling the future of development forward. 🚀
We extend our gratitude for your attention. Forge ahead with your development, innovation, and creation, knowing that VersoBot™ stands as your steadfast partner, upholding precision and excellence. 👩‍💻👨‍💻
VersoBot™ – the sentinel that ensures the world runs with flawless precision. 🌍💥
