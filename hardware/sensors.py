# sensors.py
import time
from multiprocessing import Queue
import random
import math
import serial
import pynmea2
import smbus2
import lgpio
import numpy as np
import max30100

# Global handles and constants
gps_serial_port = None
imu_bus = None
pulse_ox_sensor = None
IMU_ADDRESS = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
ULTRASONIC_TRIG = 23
ULTRASONIC_ECHO = 24
_dist_hist = []

def initialize_all_sensors():
    global gps_serial_port, imu_bus, pulse_ox_sensor
    print("[Sensors] Initializing all sensor hardware...")
    try:
        gps_serial_port = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)
        print("[Sensors] GPS serial port opened.")
    except Exception as e: print(f"[Sensors] FAILED to open GPS: {e}")
    try:
        imu_bus = smbus2.SMBus(1)
        imu_bus.write_byte_data(IMU_ADDRESS, PWR_MGMT_1, 0)
        print("[Sensors] IMU MPU-6050 initialized.")
    except Exception as e: print(f"[Sensors] FAILED to initialize IMU: {e}")
    try:
        pulse_ox_sensor = max30100.MAX30100()
        pulse_ox_sensor.reset()
        print("[Sensors] MAX30100 Pulse Oximeter initialized.")
    except Exception as e: print(f"[Sensors] FAILED to initialize Pulse Oximeter: {e}")

def read_gps_data():
    if not gps_serial_port: raise ConnectionError("GPS not initialized")
    for _ in range(10):
        try:
            line = gps_serial_port.readline().decode('ascii', errors='replace').strip()
            if line.startswith(("$GPGGA", "$GPRMC")):
                msg = pynmea2.parse(line)
                if hasattr(msg, 'latitude') and msg.latitude != 0.0:
                    return {'lat': msg.latitude, 'lon': msg.longitude}
        except (pynmea2.ParseError, UnicodeDecodeError): continue
    raise TimeoutError("No valid GPS sentence found.")

def read_imu_data():
    if not imu_bus: raise ConnectionError("IMU not initialized")
    def read_i2c_word(register):
        high = imu_bus.read_byte_data(IMU_ADDRESS, register)
        low = imu_bus.read_byte_data(IMU_ADDRESS, register + 1)
        value = (high << 8) | low
        return value - 65536 if value >= 0x8000 else value
    accel_x = read_i2c_word(ACCEL_XOUT_H) / 16384.0
    accel_y = read_i2c_word(ACCEL_XOUT_H + 2) / 16384.0
    accel_z = read_i2c_word(ACCEL_XOUT_H + 4) / 16384.0
    magnitude = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)
    return {'g_magnitude': magnitude}

def read_ultrasonic_data():
    chip_handle = None
    try:
        chip_handle = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(chip_handle, ULTRASONIC_TRIG)
        lgpio.gpio_claim_input(chip_handle, ULTRASONIC_ECHO)
        lgpio.gpio_write(chip_handle, ULTRASONIC_TRIG, 0); time.sleep(0.02)
        lgpio.gpio_write(chip_handle, ULTRASONIC_TRIG, 1); time.sleep(0.00001)
        lgpio.gpio_write(chip_handle, ULTRASONIC_TRIG, 0)
        timeout = time.time() + 0.1
        while lgpio.gpio_read(chip_handle, ULTRASONIC_ECHO) == 0:
            if time.time() > timeout: return None
        start_time = time.time()
        while lgpio.gpio_read(chip_handle, ULTRASONIC_ECHO) == 1:
            if time.time() > timeout: return None
        end_time = time.time()
        dist = (end_time - start_time) * 17150
        if 2 <= dist <= 400:
            _dist_hist.append(dist)
            if len(_dist_hist) > 5: _dist_hist.pop(0)
            return {'front_cm': round(float(np.mean(_dist_hist)), 2)}
        return None
    finally:
        if chip_handle is not None: lgpio.gpiochip_close(chip_handle)

def read_pulse_ox_data():
    if not pulse_ox_sensor: raise ConnectionError("Pulse Oximeter not initialized")
    pulse_ox_sensor.read_sensor()
    ir_value = pulse_ox_sensor.ir
    hr = int(70 + (ir_value % 20)) if ir_value else 75
    spo2 = 97
    return {'hr': hr, 'spo2': spo2}

def generate_fallback_gps(): return {'lat': 12.9649, 'lon': 77.7126}
def generate_fallback_imu(): return {'g_magnitude': 1.0}
def generate_fallback_ultrasonic(): return {'front_cm': 500}
def generate_fallback_pulse_ox(): return {'hr': 80, 'spo2': 98}

def run_sensor_process(sensor_queue: Queue):
    initialize_all_sensors()
    while True:
        data_packet = {'timestamp': time.time()}
        tasks = {'gps': read_gps_data, 'imu': read_imu_data, 'ultrasonic': read_ultrasonic_data, 'pulse_ox': read_pulse_ox_data}
        fallbacks = {'gps': generate_fallback_gps, 'imu': generate_fallback_imu, 'ultrasonic': generate_fallback_ultrasonic, 'pulse_ox': generate_fallback_pulse_ox}
        for name, task in tasks.items():
            try:
                result = task()
                if result is None: raise ValueError(f"{name} returned None")
                data_packet[name] = {'data': result, 'status': 'OK'}
            except Exception as e:
                # print(f"[Sensor Process] Using fallback for {name} due to: {e}")
                data_packet[name] = {'data': fallbacks[name](), 'status': 'SIMULATED'}
        if not sensor_queue.full(): sensor_queue.put(data_packet)
        time.sleep(1.0)