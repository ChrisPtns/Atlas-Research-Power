import time
import board
import busio
import digitalio
import pigpio #PMW
from ina226 import INA226
import adafruit_rfm9x



class ThrusterController:
    
    def __init__(self, left_gpio=18, right_gpio=19):
        self.left_gpio = left_gpio
        self.right_gpio = right_gpio
        self.pi = pigpio.pi()

        if not self.pi.connected:
            raise RuntimeError("Unsuccessful connection with pigpio daemon!")

    def stop(self): #Stop both the motors
        self.set_speeds(1500, 1500)

    def arm(self): #Send signal 1500μs for the ESCs arming for 3s
        print("Arming ESCs...")
        self.stop()
        time.sleep(3)
        print("Armed and Ready.")

    def set_speeds(self, left_pwm: int, right_pwm: int): #Accept 1000-2000μs PMW and give speed and direction to the left and right motors
        self.pi.set_servo_pulsewidth(self.left_gpio, left_pwm)
        self.pi.set_servo_pulsewidth(self.right_gpio, right_pwm)

    def cleanup(self): #Disable signal PMW safely
        self.stop()
        time.sleep(0.5)
        self.pi.set_servo_pulsewidth(self.left_gpio, 0)
        self.pi.set_servo_pulsewidth(self.right_gpio, 0)
        self.pi.stop()


class BatteryMonitor: #Battery observation from INA226 & Shunt 50A sensors
    
    def __init__(self, i2c_bus=1, address=0x40, max_amps=50.0, shunt_ohms=0.0015):
        self.ina = INA226(busnum=i2c_bus, address=address)
        self.ina.configure(max_expected_amps=max_amps, shunt_ohms=shunt_ohms)
        #Volt limits 4S LiPo
        self.RTH_THRESHOLD = 14.0   # 3.5V/cell -> Return To Home
        self.CRITICAL_THRESHOLD = 13.2 # 3.3V/cell -> Emergency Cut-off

    def get_status(self) -> dict: #Values with dictionary
        return {
            "voltage": round(self.ina.voltage(), 2),
            "current": round(self.ina.current(), 2),
            "power": round(self.ina.power(), 2)
        }

    def check_safety_levels(self) -> str: #Check for the voltage safety value
        v = self.ina.voltage()
        #Critical condition
        if v <= self.CRITICAL_THRESHOLD:
            return "CRITICAL"
        #Return limit
        elif v <= self.RTH_THRESHOLD:
            return "RTH"
        return "OK"


class LoRaTransmitter: 
    
    def __init__(self, freq_mhz=868.0, tx_power=13):
        cs = digitalio.DigitalInOut(board.CE0)
        reset = digitalio.DigitalInOut(board.D25)
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        
        self.rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, freq_mhz)
        self.rfm9x.tx_power = tx_power

    def send(self, message: str):
        self.rfm9x.send(bytes(message, "utf-8"))
        print(f"[LoRa TX] -> {message}")

    def receive(self, timeout=0.1):
        packet = self.rfm9x.receive(timeout=timeout)
        if packet is not None:
           try:
               return str(packet, "utf-8")
           except UnicodeDecodeError:
                return None
        return None

class USVSystem: #Central access
    
    def __init__(self):
        self.thrusters = ThrusterController(left_gpio=18, right_gpio=19)
        self.battery = BatteryMonitor()
        self.lora = LoRaTransmitter()
        self.is_running = False

    def start_mission(self): #Start
        self.thrusters.arm()
        self.lora.send("STATUS: MISSION STARTED")
        self.is_running = True
        last_telemetry_time = 0

        try:
            while self.is_running:
                stats = self.battery.get_status()
                status = self.battery.check_safety_levels()

                # Continuous telemetry every 3 seconds
                if time.time() - last_telemetry_time > 3:
                    msg = f"STAT:OK | V:{stats['voltage']}V | A:{stats['current']}A"
                    self.lora.send(msg)
                    last_telemetry_time = time.time()

                command = self.lora.receive(timeout=0.1) # for 0.1s
                if command:
                    print(f"[SYSTEM] Command: {command}")
                    if command == "CMD_RTH":
                        print("[SYSTEM] Command by the user!")
                        self.execute_rth(stats)
                        self.is_running = False
                    elif command == "CMD_STOP":
                        print("[SYSTEM] Mechanical STOP!")
                        self.thrusters.stop()
                        self.is_running = False

                #Safety situation
                if status == "CRITICAL":
                    print("[SYSTEM] Critical voltage! Emergency stop!")
                    self.lora.send("EMERGENCY: CRITICAL BATTERY CUTOFF")
                    self.thrusters.stop()
                    self.is_running = False

                elif status == "RTH":
                    self.execute_rth(stats)
                    self.is_running = False

                else:
                    #Normal
                    self.thrusters.set_speeds(1650, 1650)

                time.sleep(0.5)

        except KeyboardInterrupt: #CTRL+C
            print("\n[SYSTEM] Stop by the user.")
        finally:
            self.shutdown()

    def execute_rth(self, current_stats: dict):
        #Return to home
        print("[SYSTEM] Low battery! Start RTH...")
        self.lora.send(f"ALARM: RTH INITIATED | V:{current_stats['voltage']}V")
        
        # Return
        self.thrusters.set_speeds(1600, 1600)
        
        for _ in range(10):
            st = self.battery.get_status()
            self.lora.send(f"RTH ACTIVE | V:{st['voltage']}V | A:{st['current']}A")
            time.sleep(2)

        self.thrusters.stop()
        self.lora.send("STATUS: USV SAFELY ARRIVED AT HOME")

    def shutdown(self):
        #C  lean and safe stop
        print("[SYSTEM] Shutting down...")
        self.thrusters.cleanup()
        print("[SYSTEM] Shutdown complete.")


if __name__ == "__main__":
    usv = USVSystem()
    usv.start_mission()
