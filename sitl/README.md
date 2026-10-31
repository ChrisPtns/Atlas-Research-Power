# ArduRover SITL & Sensors (Ομάδα 1)

## Περιεχόμενα
- `scripts/`: Python / DroneKit / MAVLink scripts για SITL missions
- `missions/`: Mission files (.waypoints / plans) & simulation logs
- `../sensors/datasheets/`: Datasheets αισθητήρων (GPS, IMU, Depth, Barometer, Sonar)
- `../sensors/kicad/`: Σχηματικά διασύνδεσης αισθητήρων στο KiCad
- `../telemetry/lora/`: LoRa Link Budget calculations

## Οδηγίες Εκκίνησης SITL
```bash
# Παράδειγμα εκκίνησης ArduRover SITL
sim_vehicle.py -v Rover --console --map
```
