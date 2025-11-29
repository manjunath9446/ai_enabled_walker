# Smart Walker Project - Device Code

This repository contains the Python source code for the Smart Walker device, which runs on a Raspberry Pi.

## Features

- Multi-process architecture for handling sensors, vision, and actions in parallel.
- Real-time sensor data collection (GPS, IMU, Pulse Oximeter, Ultrasonic).
- Live video stream processing with object detection and scene description via Gemini.
- Fallback "Demo Mode" for testing without hardware.
- Real-time data synchronization with a Firebase backend.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd smart_walker
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Secrets:**
    *   Create a `config.py` file by copying `config.py.example` (if you create one).
    *   Add your `GOOGLE_API_KEY` and `FIREBASE_DATABASE_URL` to `config.py`.
    *   Place your `firebase-credentials.json` file in the root directory.

## How to Run

### For Demoing (No Hardware Needed)

Run the standalone simulator. This will send realistic, simulated data to your Firebase project.

```bash
python fake_walker_server.py