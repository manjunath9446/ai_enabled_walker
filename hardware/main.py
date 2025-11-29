# main.py
from multiprocessing import Process, Queue
import time
import queue
import config
from sensors import run_sensor_process
from vision import run_vision_process
from actions import run_action_process

if __name__ == '__main__':
    print("[Main] Smart Walker application starting...")
    sensor_q, vision_q, command_q = Queue(5), Queue(5), Queue(5)
    
    processes = [
        Process(target=run_sensor_process, args=(sensor_q,)),
        Process(target=run_vision_process, args=(vision_q, config.GEMINI_API_INTERVAL_S)),
        Process(target=run_action_process, args=(command_q,))
    ]
    for p in processes: p.start()

    print("[Main] All processes started. Control loop running.")
    last_spoken_text = ""
    last_spoken_time = 0.0
    
    try:
        while True:
            try:
                sensor_data = sensor_q.get_nowait()
                vision_data = vision_q.get_nowait()
                
                command_q.put({'type': 'update_firebase_data', 'payload': sensor_data})
                
                dist_cm = None
                if sensor_data['ultrasonic']['status'] in ['OK', 'SIMULATED']:
                    dist_cm = sensor_data['ultrasonic']['data']['front_cm']

                dist_text = f"{dist_cm:.1f} cm" if dist_cm is not None else "distance not available"
                speech_to_say = None
                is_obstacle_close = dist_cm is not None and dist_cm < config.OBSTACLE_ALERT_DISTANCE_CM
                description = vision_data.get('gemini_description')

                if is_obstacle_close and description:
                    if dist_cm < 50: speech_to_say = f"Warning! {description}. Object very close at about {int(dist_cm)} centimeters."
                    else: speech_to_say = f"{description}. Object about {dist_text} away."
                elif is_obstacle_close:
                    speech_to_say = f"Careful. Nearest object {dist_text}."
                
                can_speak_now = (time.time() - last_spoken_time) > 6
                is_new_message = speech_to_say != last_spoken_text

                if speech_to_say and (is_new_message or can_speak_now):
                    print(f"[Brain] DECISION: Speak -> '{speech_to_say}'")
                    command_q.put({'type': 'local_speak', 'payload': speech_to_say})
                    last_spoken_text = speech_to_say
                    last_spoken_time = time.time()
            
            except queue.Empty:
                pass
            time.sleep(0.1) 
            
    except KeyboardInterrupt:
        print("\n[Main] Shutdown signal received.")
    finally:
        for p in processes: p.terminate()
        print("[Main] Application has shut down.")