# vision.py
import cv2
import time
from multiprocessing import Queue
import requests
import numpy as np
from PIL import Image
import base64
import io
import config

_last_sig = None

def initialize_vision_models():
    print(f"[Vision] Using direct REST API for model: {config.GEMINI_MODEL}")

def get_latest_frame(url, time_budget=0.7, timeout=3):
    try:
        r = requests.get(url, stream=True, timeout=(3, timeout))
        r.raise_for_status()
        buf = b""
        latest_frame = None
        deadline = time.time() + time_budget
        for chunk in r.iter_content(4096):
            if chunk: buf += chunk
            a = buf.find(b"\xff\xd8"); b = buf.find(b"\xff\xd9")
            if a != -1 and b != -1 and b > a:
                jpg = buf[a:b+2]
                buf = buf[b+2:]
                img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if img is not None: latest_frame = img
            if time.time() > deadline: break
        return latest_frame
    except Exception as e:
        print(f"[Vision] Frame grab failed: {e}")
        return None

def scene_changed(img_bgr, thresh=8.0):
    global _last_sig
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (64, 36))
    sig = small.astype(np.int16)
    if _last_sig is None: _last_sig = sig; return True
    diff = np.mean(np.abs(sig - _last_sig))
    changed = diff > thresh
    if changed: _last_sig = sig
    return changed

def describe_image_with_gemini(pil_image):
    try:
        buf = io.BytesIO()
        pil_image.save(buf, format="JPEG")
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        prompt = "You are an assistant for a visually impaired person. Describe the scene in one short sentence, focusing on obstacles and walking safety."
        payload = {"contents": [{"parts": [{"text": prompt}, {"inlineData": {"mimeType": "image/jpeg", "data": img_b64}}]}]}
        url = config.GEMINI_API_URL_TEMPLATE.format(model=config.GEMINI_MODEL, key=config.GOOGLE_API_KEY)
        resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
        if resp.status_code == 429: print("[Vision] Gemini rate-limited."); return None
        resp.raise_for_status()
        data = resp.json()
        return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
    except Exception as e:
        print(f"[Vision] Gemini request failed: {repr(e)}")
        return None

def run_vision_process(vision_queue: Queue, gemini_interval: float):
    initialize_vision_models()
    video_source = config.VIDEO_SOURCE
    last_gemini_call_time = 0
    while True:
        try:
            frame = get_latest_frame(video_source, time_budget=0.7, timeout=3)
            if frame is None: time.sleep(1.0); continue
            has_scene_changed = scene_changed(frame)
            gemini_description = None
            current_time = time.time()
            if has_scene_changed and (current_time - last_gemini_call_time > gemini_interval):
                pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                gemini_description = describe_image_with_gemini(pil_img)
                last_gemini_call_time = current_time
            vision_data_packet = {'gemini_description': gemini_description, 'scene_changed': has_scene_changed, 'timestamp': time.time()}
            if not vision_queue.full(): vision_queue.put(vision_data_packet)
            time.sleep(0.5)
        except Exception as e:
            print(f"[Vision Process] An error occurred in the main loop: {e}")
            time.sleep(2.0)