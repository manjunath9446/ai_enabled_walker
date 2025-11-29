# fake_walker_server.py
import time
import random
import math
import firebase_admin
from firebase_admin import credentials, db
import numpy as np

# --- CONFIGURATION ---
CRED_PATH = "firebase-credentials.json"
FIREBASE_DATABASE_URL = "https://your-project-name-default-rtdb.firebaseio.com/"

# --- SIMULATION LOGIC ---
_dist_hist = []
def simulate_gps_data():
    lat = 12.9649 + (random.random() - 0.5) * 0.0001
    lon = 77.7126 + (random.random() - 0.5) * 0.0001
    return {'lat': lat, 'lon': lon}

def simulate_imu_data():
    g_magnitude = 1.1 + (random.random() - 0.5) * 0.3
    if random.random() < 0.1: g_magnitude += 0.5
    return {'g_magnitude': g_magnitude}

def simulate_pulse_ox_data():
    hr = 85 + random.randint(-4, 4)
    spo2 = 98 + random.randint(-1, 1)
    if random.random() < 0.02: spo2 = 91
    return {'hr': hr, 'spo2': spo2}

# --- MAIN SIMULATOR LOOP ---
def run_simulator():
    try:
        cred = credentials.Certificate(CRED_PATH)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DATABASE_URL})
        print("[Simulator] Firebase initialized successfully.")
    except Exception as e:
        print(f"!!!!!!!!!! FIREBASE FAILED TO INITIALIZE: {e} !!!!!!!!!!")
        return

    print("[Simulator] Starting fake walker server. Press Ctrl+C to stop.")
    while True:
        try:
            live_data_packet = {
                'timestamp': time.time(),
                'gps': {'data': simulate_gps_data(), 'status': 'SIMULATED'},
                'imu': {'data': simulate_imu_data(), 'status': 'SIMULATED'},
                'pulse_ox': {'data': simulate_pulse_ox_data(), 'status': 'SIMULATED'}
            }
            db.reference('walker/live-status').set(live_data_packet)
            print(f"Sent update to Firebase at {time.strftime('%H:%M:%S')}")
            time.sleep(2.0)
        except KeyboardInterrupt:
            print("\n[Simulator] Shutdown signal received.")
            break
        except Exception as e:
            print(f"[Simulator] An error occurred: {e}")
            time.sleep(5)

if __name__ == '__main__':
    run_simulator()