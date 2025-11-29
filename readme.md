# Guardian Angel Smart Walker

**A comprehensive IoT and AI-powered smart walker to enhance safety, mobility, and health monitoring for the elderly.**

This project integrates a suite of sensors on a Raspberry Pi-powered walker, providing real-time data to a cloud-connected web application. The system offers live location tracking, health vital monitoring, obstacle detection with AI-powered scene description, and an interactive AI assistant.

![Guardian Angel Dashboard](<link_to_your_dashboard_screenshot.png>) <!-- TODO: Add a screenshot of your app -->

## Table of Contents
1.  [Features](#features)
2.  [System Architecture](#system-architecture)
3.  [Hardware Setup](#hardware-setup)
    *   [Components List](#components-list)
    *   [Wiring Diagram](#wiring-diagram)
4.  [Software Setup](#software-setup)
    *   [Cloud Backend (Firebase)](#cloud-backend-firebase)
    *   [Raspberry Pi (Device)](#raspberry-pi-device)
    *   [Web Application (Frontend)](#web-application-frontend)
5.  [How to Run the Full System](#how-to-run-the-full-system)
    *   [For Demos (No Hardware)](#for-demos-no-hardware)
    *   [For Production (With Hardware)](#for-production-with-hardware)

---

## Features

*   **Live Location Tracking:** Real-time GPS location displayed on an interactive map.
*   **Health Monitoring:** Live Heart Rate (BPM) and Blood Oxygen (SpO2) monitoring with a historical trend chart.
*   **Motion Analysis:** An IMU sensor provides live G-force data to analyze gait stability and detect potential falls.
*   **Intelligent Obstacle Avoidance:** An ultrasonic sensor provides distance warnings, coupled with a camera that sends images to the Gemini AI for real-time scene descriptions.
*   **AI Assistant:** A conversational AI (powered by Groq) for user queries about health, navigation, and general questions.
*   **Cloud-Connected Dashboard:** A responsive, multi-page web application for guardians to monitor all data remotely.

---

## System Architecture

The project is divided into two main parts: the **Device** (Raspberry Pi) and the **Frontend** (Web App), which communicate via a **Cloud Backend** (Firebase).
The Raspberry Pi application itself is a multi-process system to handle hardware and network tasks in parallel without blocking.

---

## Hardware Setup

### Components List

*   **Primary Controller:** Raspberry Pi 4 Model B (or newer)
*   **Camera:** Raspberry Pi Camera Module (v2 or v3)
*   **GPS:** NEO-6M GPS Module
*   **IMU:** MPU-6050 Accelerometer/Gyroscope
*   **Pulse Oximeter:** MAX30100 Heart Rate & SpO2 Sensor
*   **Distance Sensor:** HC-SR04 Ultrasonic Sensor
*   **Audio Output:** A small speaker or headphones connected to the Pi.
*   **Power:** A portable power bank capable of powering the Raspberry Pi.
*   **Misc:** Jumper wires, breadboard.

### Wiring Diagram

**Important:** Always connect hardware when the Raspberry Pi is powered off. Ensure all components are connected to the correct GPIO pins as referenced in the software.

*   **Power (VCC and GND):** All sensors require a 3.3V or 5V power connection and a common Ground (GND) connection to the Raspberry Pi.

*   **I2C Devices (IMU & Pulse Oximeter):**
    *   **SDA** (Data) pins on both sensors connect to **GPIO 2 (Pin 3)** on the Pi.
    *   **SCL** (Clock) pins on both sensors connect to **GPIO 3 (Pin 5)** on the Pi.

*   **UART Device (GPS):**
    *   **TXD** (Transmit) pin on the GPS module connects to **GPIO 15 (RXD - Pin 10)** on the Pi.
    *   **RXD** (Receive) pin on the GPS module connects to **GPIO 14 (TXD - Pin 8)** on the Pi.

*   **GPIO Device (Ultrasonic Sensor):**
    *   **Trig** pin connects to **GPIO 23 (Pin 16)** on the Pi.
    *   **Echo** pin connects to **GPIO 24 (Pin 18)** on the Pi.

*   **Camera:**
    *   Connects to the dedicated CSI (Camera Serial Interface) port on the Raspberry Pi.

---

## Software Setup

### Cloud Backend (Firebase)

1.  Create a new project in the [Firebase Console](https://console.firebase.google.com/).
2.  **Generate a Service Account Key:** Go to Project settings > Service accounts > "Generate new private key". Rename the downloaded file to `firebase-credentials.json`.
3.  **Create a Realtime Database:** In the "Build" menu, create a new Realtime Database. Start it in **"test mode"**. Copy the database URL.
4.  **Add a Web App:** From Project Overview, add a new Web App. Copy the `firebaseConfig` object provided.

### Raspberry Pi (Device)

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd <repo-folder-name>
    ```

2.  **Setup Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Enable Hardware Interfaces:**
    Run `sudo raspi-config` and go to `Interface Options` to enable:
    *   **I2C** (for IMU and Pulse Oximeter)
    *   **Serial Port** (for GPS, ensuring the login shell is disabled and the serial hardware is enabled)
    *   **Legacy Camera** (for the `picamera2` library)

5.  **Configure Secrets:**
    *   Place the `firebase-credentials.json` file you downloaded into this directory.
    *   Open `config.py` and paste in your `FIREBASE_DATABASE_URL` and `GOOGLE_API_KEY`.

### Web Application (Frontend)

1.  **Open the `public` directory** on your local computer.

2.  **Configure Secrets:**
    *   Open `public/main.js` and paste your `firebaseConfig` object.
    *   Open `public/assistant.html` (and other HTML files) and replace `YOUR_KIT_CODE.js` with your personal [Font Awesome](https://fontawesome.com) kit code.
    *   Open `public/agents/assistant.js` and paste your `GROQ_API_KEY`.

---

## How to Run the Full System

### For Demos (No Hardware)

This mode simulates all sensor data, making it perfect for development and presentations.

1.  **On the Raspberry Pi (or any computer with Python):**
    *   Navigate to the project directory and activate the virtual environment.
    *   Run the standalone simulator:
        ```bash
        python fake_walker_server.py
        ```
2.  **On your Local Computer:**
    *   Navigate **inside** the `public` directory.
    *   Start a local web server:
        ```bash
        python -m http.server 8000
        ```
    *   Open your browser to `http://localhost:8000`.

### For Production (With Hardware)

This requires the Raspberry Pi with all hardware connected and running.

1.  **On the Raspberry Pi (Terminal 1):** Start the camera service.
    ```bash
    # (Activate venv first)
    python camera_stream.py
    ```

2.  **On the Raspberry Pi (Terminal 2):** Start the main application.
    ```bash
    # (Activate venv first)
    python main.py
    ```

3.  **View the Dashboard:** Open the live `Hosting URL` from your Firebase deployment, or test it locally as described in the demo instructions.
