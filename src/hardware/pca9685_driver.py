import yaml #Αναγνώριση αρχείων ρυθμίσεων μορφής YAML
from adafruit_pca9685 import PCA9685 #Κλάση διαχείρισης της πλακέτας παραγωγής σημάτων PCA9685 
from board import SCL, SDA # Ορίζει φυσικό pin για το πρωτόκολλο I2C
import busio #Βιβλιοθήκη για την επικοινωνία I2C

class ThrusterDriver: 
    def __init__(self, config_path="config/motor_config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f) #Ανάγνωση αρχείου ρυθμίσεων YAML

        #Αρχικοποίηση I2C και PCA9685
        i2c_bus = busio.I2C(SCL, SDA) #Αρχικοποιεί το I2C με τα Pins SCL & SDA
        i2c_cfg = self.config.get('i2c', {}) #Απομονώνει το δίαυλο I2C του YAML (address & Συχνότητα)
        self.pca = PCA9685(i2c_bus, address=i2c_cfg.get('address', 0x40)) #Αρχικοποιεί την πλακέτα PCA9685 με το I2C bus και τη διεύθυνση
        self.pca.frequency = i2c_cfg["frequency_hz"] #50 Hz
    def _throttle_to_us(self, throttle: float, motor_cfg: dict) -> int:
        #Μετατρέπει τιμή throttle [-1.0 , 1.0] σε διάρκεια παλμπ'υ (μs)
        throttle = max (-1.0, min (1.0, throttle))#Εξασφαλίζει τιμή στο εύρος [-1.0,1.0]

        if motor_cfg.get("reversed", False):
            throttle = -throttle #Αν είναι αντιστραμμένο, αλλάζει το πρόσημο της ισχύος

# Διαβάζει τα όρια παλμών από το YAML

        min_us = motor_cfg["min_pulse_us"] #1100 μs 
        neutral_us = motor_cfg["neutral_pulse_us"] #1500
        max_us = motor_cfg["max_pulse_us"] #1900

        if throttle >= 0:
             pulse_us = neutral_us + throttle * (max_us - neutral_us)
        else:
            pulse_us = neutral_us + throttle * (neutral_us - min_us)

        return int(pulse_us) #Επιστρέφει τη διάρκεια του παλμού σε μs ακέραιο
    def set_throttle(self, thrust_name: str, throttle: float):
        #Ορίζει την ισχύ ενός μοτέρ
        if thrust_name not in self.config["motors"]:
            raise ValueError(f"Motor '{thrust_name}' not found in configuration.")
        