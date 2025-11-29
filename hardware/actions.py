# actions.py
import time
from multiprocessing import Queue
import firebase_admin
from firebase_admin import credentials, db
from gtts import gTTS
import subprocess
import config

try:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred, {'databaseURL': config.FIREBASE_DATABASE_URL})
    FIREBASE_ENABLED = True
except Exception as e:
    print(f"[Actions] FIREBASE FAILED: {e}. Running in offline mode.")
    FIREBASE_ENABLED = False

def update_firebase_data(data):
    if FIREBASE_ENABLED:
        try: db.reference('walker/live-status').set(data)
        except Exception as e: print(f"[Actions Error] Firebase update failed: {e}")

def push_alert_to_firebase(alert_type, message, details):
    if FIREBASE_ENABLED:
        try:
            db.reference('walker/alerts').push({
                'type': alert_type, 'message': message, 'details': details,
                'timestamp': int(time.time() * 1000)
            })
        except Exception as e: print(f"[Actions Error] Firebase push failed: {e}")

def speak_text(text):
    print(f"\n[ACTION: SPEAK] <<< {text} >>>\n")
    try:
        tts = gTTS(text=text, lang='en')
        tts.save("response.mp3")
        subprocess.run(["mpg123", "-q", "response.mp3"])
    except Exception as e:
        print(f"[Actions] Text-to-Speech failed: {e}")

def run_action_process(command_queue: Queue):
    while True:
        command = command_queue.get()
        cmd_type = command.get('type')
        payload = command.get('payload')

        if cmd_type == 'update_firebase_data': update_firebase_data(payload)
        elif cmd_type == 'send_critical_alert': push_alert_to_firebase(payload['type'], payload['message'], payload['details'])
        elif cmd_type == 'local_speak': speak_text(payload)