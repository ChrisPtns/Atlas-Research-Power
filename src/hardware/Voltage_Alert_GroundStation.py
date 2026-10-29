import time
import threading
import board
import busio
import digitalio
import adafruit_rfm9x

# 1. SPI & PINS
CS = digitalio.DigitalInOut(board.CE0)      # GPIO 8
RESET = digitalio.DigitalInOut(board.D25)   # GPIO 25
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

# 2. LORA SX1276
RADIO_FREQ_MHZ = 868.0

try:
    rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
    print(f"LoRa SX1276 Receiver initialized at {RADIO_FREQ_MHZ} MHz.")
    print("Waiting for telemetry packets from USV...\n" + "="*50)
except Exception as e:
    print(f"Error initializing LoRa Module: {e}")
    exit()

def send_commands():
    while True:
        cmd = input("\nGive the command (CMD_RTH / CMD_STOP): ").strip()
        if cmd in ["CMD_RTH", "CMD_STOP"]:
            rfm9x.send(bytes(cmd, "utf-8"))
            print(f"[TX COMMAND] -> Command sent: {cmd}")
        else:
            print("[ERROR] Invalid command! Use CMD_RTH or CMD_STOP.")

#Start THREAD
threading.Thread(target=send_commands, daemon=True).start()

#Receiver Loop
while True:
    packet = rfm9x.receive(timeout=1.0)

    if packet is not None:
        try:
            message = str(packet, "utf-8")
            rssi = rfm9x.last_rssi  #dBm
            timestamp = time.strftime("%H:%M:%S")

            if "ALARM" in message or "CRITICAL" in message:
                print(f"\n[!!! WARNING {timestamp} !!!] Signal: {rssi} dBm")
                print(f"--> {message} <--\n")
            else:
                print(f"[{timestamp}] [RSSI: {rssi} dBm] {message}")

        except UnicodeDecodeError:
            print("[ERROR] Received corrupted packet.")

    time.sleep(0.1)
