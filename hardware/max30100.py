# max30100.py
import smbus

INT_STATUS   = 0x00; INT_ENABLE   = 0x01; FIFO_WR_PTR  = 0x02; OVRFLOW_CTR  = 0x03; FIFO_RD_PTR  = 0x04; FIFO_DATA    = 0x05; MODE_CONFIG  = 0x06; SPO2_CONFIG  = 0x07; LED_CONFIG   = 0x09; TEMP_INTG    = 0x16; TEMP_FRAC    = 0x17; REV_ID       = 0xFE; PART_ID      = 0xFF
I2C_ADDRESS  = 0x57
PULSE_WIDTH = { 200: 0, 400: 1, 800: 2, 1600: 3 }
SAMPLE_RATE = { 50: 0, 100: 1, 167: 2, 200: 3, 400: 4, 600: 5, 800: 6, 1000: 7 }
LED_CURRENT = { 0:0, 4.4:1, 7.6:2, 11.0:3, 14.2:4, 17.4:5, 20.8:6, 24.0:7, 27.1:8, 30.6:9, 33.8:10, 37.0:11, 40.2:12, 43.6:13, 46.8:14, 50.0:15 }

def _get_valid(d, value):
    try: return d[value]
    except KeyError: raise KeyError("Value %s not valid, use one of: %s" % (value, ', '.join([str(s) for s in d.keys()])))

MODE_HR = 0x02; MODE_SPO2 = 0x03

class MAX30100(object):
    def __init__(self, i2c=None, mode=MODE_SPO2, sample_rate=100, led_current_red=11.0, led_current_ir=11.0, pulse_width=400, max_buffer_len=10000):
        self.i2c = i2c if i2c else smbus.SMBus(1)
        self.set_mode(MODE_HR); self.set_led_current(led_current_red, led_current_ir); self.set_spo_config(sample_rate, pulse_width); self.set_mode(mode)
        self.buffer_red = []; self.buffer_ir = []; self.max_buffer_len = max_buffer_len
    @property
    def red(self): return self.buffer_red[-1] if self.buffer_red else None
    @property
    def ir(self): return self.buffer_ir[-1] if self.buffer_ir else None
    def set_led_current(self, led_current_red=11.0, led_current_ir=11.0):
        self.i2c.write_byte_data(I2C_ADDRESS, LED_CONFIG, (_get_valid(LED_CURRENT, led_current_red) << 4) | _get_valid(LED_CURRENT, led_current_ir))
    def set_mode(self, mode):
        reg = self.i2c.read_byte_data(I2C_ADDRESS, MODE_CONFIG); self.i2c.write_byte_data(I2C_ADDRESS, MODE_CONFIG, (reg & 0xF8) | mode)
    def set_spo_config(self, sample_rate=100, pulse_width=1600):
        reg = self.i2c.read_byte_data(I2C_ADDRESS, SPO2_CONFIG)
        reg = (reg & 0xE0) | (_get_valid(SAMPLE_RATE, sample_rate) << 2) | _get_valid(PULSE_WIDTH, pulse_width)
        self.i2c.write_byte_data(I2C_ADDRESS, SPO2_CONFIG, reg)
    def read_sensor(self):
        bytes_read = self.i2c.read_i2c_block_data(I2C_ADDRESS, FIFO_DATA, 4)
        self.buffer_ir.append((bytes_read[0] << 8) | bytes_read[1]); self.buffer_red.append((bytes_read[2] << 8) | bytes_read[3])
        self.buffer_red = self.buffer_red[-self.max_buffer_len:]; self.buffer_ir = self.buffer_ir[-self.max_buffer_len:]
    def shutdown(self): self.i2c.write_byte_data(I2C_ADDRESS, MODE_CONFIG, self.i2c.read_byte_data(I2C_ADDRESS, MODE_CONFIG) | 0x80)
    def reset(self): self.i2c.write_byte_data(I2C_ADDRESS, MODE_CONFIG, self.i2c.read_byte_data(I2C_ADDRESS, MODE_CONFIG) | 0x40)