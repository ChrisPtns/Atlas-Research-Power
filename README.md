# Atlas Aqua Control

Control system and driver software for Atlas Aqua robotics / motor control platform.

## Project Structure

```text
atlas-aqua-control/
├── .gitignore
├── README.md
├── requirements.txt
├── config/
│   └── motor_config.yaml
├── src/
│   ├── __init__.py
│   ├── hardware/
│   │   ├── __init__.py
│   │   └── pca9685_driver.py
│   ├── control/
│   │   ├── __init__.py
│   │   ├── kinematics.py
│   │   └── pid_controller.py
│   └── safety/
│       ├── __init__.py
│       └── watchdog.py
├── scripts/
│   └── run_motors.py
└── docs/
    └── wiring_schema.png
```

## Setup & Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python scripts/run_motors.py
```
