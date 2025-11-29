# camera_stream.py
from flask import Flask, Response
from picamera2 import Picamera2
import io
import time
from PIL import Image

app = Flask(__name__)
picam2 = None

try:
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    print("[Camera Stream] Picamera2 initialized successfully in RGB888 mode.")
    time.sleep(2.0)
except Exception as e:
    print(f"!!!!!!!!!!!!!! [Camera Stream] FAILED to initialize camera: {e} !!!!!!!!!!!!!!")

def generate_frames():
    if not picam2: return
    while True:
        try:
            frame = picam2.capture_array()
            img = Image.fromarray(frame)
            stream = io.BytesIO()
            img.save(stream, format='jpeg', quality=85)
            stream.seek(0)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + stream.read() + b'\r\n')
            time.sleep(0.05)
        except Exception as e:
            print(f"[Camera Stream] Error during frame capture: {e}")
            break

@app-route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '<h1>Pi Camera MJPEG Stream</h1><img src="/video_feed" width="640" height="480">'

if __name__ == '__main__':
    if picam2:
        print("[Camera Stream] Starting Flask web server...")
        app.run(host='0.0.0.0', port=8080, threaded=True)
    else:
        print("[Camera Stream] Flask server NOT started due to camera initialization failure.")