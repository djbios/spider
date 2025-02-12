# DIY Spider Robot Firmware (WIP)

Welcome to the **DIY Spider Robot** firmware project! This repository contains the code running on a CircuitPython-based microcontroller to control a quadruped (“spider”) robot. Below is a comprehensive overview of the project structure, how to deploy the code, its main functionalities, and instructions on how to customize or extend it.
<img src="https://pic.djbios.org/8odb5u.jpg"></img>
---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Hardware & Components](#hardware--components)
3. [Directory Structure & File Descriptions](#directory-structure--file-descriptions)
    - [Key Python Modules](#key-python-modules)
    - [Support Scripts & Utilities](#support-scripts--utilities)
4. [Installation & Setup](#installation--setup)
5. [Deploying to the Microcontroller](#deploying-to-the-microcontroller)
6. [Excluding Unwanted Files](#excluding-unwanted-files)
7. [Runtime Behavior](#runtime-behavior)
8. [REST API Endpoints](#rest-api-endpoints)
9. [Logging & Debugging](#logging--debugging)
10. [Testing](#testing)
11. [Future Improvements](#future-improvements)
12. [License & Credits](#license--credits)

---

## Project Overview

This project is intended for a custom quadruped robot (resembling a “spider” robot with four legs). It uses:

- A CircuitPython-compatible microcontroller (e.g., an ESP32-S3, Raspberry Pi Pico W, or similar).
- A PCA9685 PWM driver to control multiple servos for the legs.
- Various sensors, such as an accelerometer (ADXL345) and a battery monitor.
- A small SSD1306 OLED display for local feedback.
- A Wi-Fi module for hosting a local HTTP server, allowing for real-time commands and telemetry via REST endpoints.
- Flash memory for persistent storage of logs and saved servo positions.

---

## Hardware & Components

- **Microcontroller**: Must support CircuitPython and Wi-Fi (e.g., Espressif or Raspberry Pi Pico W).
- **Servo Driver**: [Adafruit PCA9685](https://www.adafruit.com/product/815) controlling up to 16 servos.
- **Servos**: Used in the `Walker` class to articulate the 4 legs (3 joints per leg = 12 servos).
- **Battery**: Typically a LiPo pack (3S or 2S). A designated pin reads battery voltage.
- **Accelerometer**: ADXL345 sensor (I²C).
- **Light**: An LED strip or single LED (PWM controlled).
- **OLED Display**: SSD1306 (128x32 or 128x64) for local debug info.
- **Mechanical**: The mechanical chassis is up to you. The `hardware.py` file sets pin assignments for the servos, battery sensor, etc.

---

## Directory Structure & File Descriptions

```
.
├── api.py                 # Defines the HTTP routes and command endpoints
├── code.py                # Entry point for the main async loop (CircuitPython main)
├── deploy.sh              # Bash script to deploy files to the microcontroller
├── excluded_files.txt     # List of files/directories to exclude from deployment
├── flash_storage.py       # Provides a dictionary-like persistent storage (JSON-based)
├── hardware.py            # Hardware pin config, setup of servos, battery, accelerometer, display, etc.
├── logging_.py            # Logging system with a ring buffer for storing logs
├── pins.py                # Pin definitions (board-level constants)
├── requirements.txt       # Dependencies (CircuitPython libraries) for reference
├── routines.py            # Routines registry for scheduling asynchronous tasks
├── serial_monitor.sh      # Simple script to open a serial console (screen)
├── tests.py               # Various test routines (like servo tests, light tests)
├── uart.py                # Example UART read routine
├── utils.py               # Helper utilities (async call wrapper, color math, inverse kinematics stubs)
│
├── python_utils/          # (Optional) Additional Python reference utilities (functools, itertools, etc.)
│
├── research/              # Extra URDF files, IKPy experiments, or other research notes
│
├── simulator/             # Contains a prototype Python GUI-based simulator (PyQt + Matplotlib)
│
├── static/                # Static web assets (like `index.html` for the built-in HTTP server)
│
└── tests/                 # Additional test configs or smaller tests
```

### Key Python Modules

1. **`api.py`**  
   - Sets up REST API endpoints using `adafruit_httpserver`.  
   - Routes include:
     - `/api/stats` for battery & sensor info
     - `/api/command` (POST) to receive commands (like servo movements, calibration, etc.)
     - `/api/logs` for logs
     - `/api/servos-angles` to read current servo angles
     - `/api/saved-positions` to list stored servo positions
   - Commands dictionary maps string commands to callable methods (e.g., `"wiggle" -> walker.wiggle`).

2. **`code.py`**  
   - The main entry point.  
   - Initializes the routines in `RoutinesRegistry` and starts them in an asyncio event loop.  
   - Handles any top-level exceptions, deactivates servos if an error occurs.

3. **`flash_storage.py`**  
   - Implements a JSON-backed storage dictionary to persist data on the microcontroller’s flash:
     - `storage["key"] = value` saves data to `data.json`.
     - Re-mounts storage in write mode, then returns to read-only mode.

4. **`hardware.py`**  
   - Configures hardware for:
     - I²C sensors (accelerometer & display).
     - The PCA9685 servo driver for controlling leg servos.
     - Wi-Fi connection.
     - Battery ADC reading.
     - LED Light PWM pin.  
   - Defines a global `walker` object with 4 `Leg` objects.

5. **`logging_.py`**  
   - Maintains an in-memory ring buffer for log lines.
   - `log("message")` to add a log line to both the ring buffer and print it.
   - `get_unsent_loglines(...)` used by `/api/logs` and the display routine to fetch new logs incrementally.

6. **`pins.py`**  
   - Board-specific pin definitions (I²C pins, LED pin, battery ADC pin, etc.).

7. **`requirements.txt`**  
   - References to the CircuitPython libraries used.  
   - For local simulation or typed-linting, there are also Python stubs (like `circuitpython-stubs`).

8. **`routines.py`**  
   - A minimal framework for registering background tasks (`tick()` methods).  
   - `RoutinesRegistry.register()` registers a routine, and the `initialise()` method schedules them into a single `asyncio.gather`.

9. **`tests.py`**  
   - Contains test routines, e.g. `leg_test()` that wiggles the legs one by one, or `light_test()` to fade the LED.  
   - Potentially run these test calls from the REPL or via an API command.

10. **`uart.py`**  
    - Basic example capturing data from a UART device.

11. **`utils.py`**  
    - Various helpers:  
      - `run_callable_async_or_not(...)` to unify calling sync or async tasks.  
      - Color interpolation stubs.  
      - Some inverse kinematics math stubs (for advanced control).

### Support Scripts & Utilities

- **`deploy.sh`**  
  Automates copying the code onto the microcontroller’s USB drive with `rsync`.  
- **`excluded_files.txt`**  
  Lists files/folders to skip during deployment.  
- **`serial_monitor.sh`**  
  Quick script using `screen` to open a serial console at the correct baud rate.

---

## Installation & Setup

1. **Install CircuitPython** on your microcontroller if not pre-flashed.
2. **Obtain** the correct drivers for your platform (e.g., [Adafruit PCA9685 library](https://github.com/adafruit/Adafruit_CircuitPython_PCA9685), etc.).
3. **Clone or download** this repository onto your PC.
4. **Solder & assemble** your hardware:
   - PCA9685 connected to the microcontroller’s I²C pins (`SDA`, `SCL`).
   - ADXL345 connected to the same I²C.
   - Battery sense pin connected to an ADC pin (through appropriate voltage divider).
   - Servos connected to the PCA9685 channels 0–15.
   - (Optional) SSD1306 OLED also on I²C.

---

## Deploying to the Microcontroller

The `deploy.sh` script automates copying the relevant project files to your microcontroller’s CIRCUITPY drive (or a mounted folder). **Steps**:

1. **Mount** the microcontroller’s CIRCUITPY drive, e.g., at `/Volumes/CIRCUITPY` on macOS or `/media/username/CIRCUITPY` on Linux.
2. **Open** a terminal in the project root.
3. **Run**:
   ```bash
   ./deploy.sh /path/to/CIRCUITPY
   ```
   - The script reads [`excluded_files.txt`](./excluded_files.txt) to skip certain files/folders.
   - `rsync` only copies changed files.

Once deployed, the microcontroller automatically restarts and runs `code.py` as the main script.

---

## Excluding Unwanted Files

In [`excluded_files.txt`](./excluded_files.txt), list everything you **do not** want to copy to the device. For instance:

- `.git/`, `.vscode/`, and other ephemeral dev folders.
- Large images or backups not needed on-device.
- `tests/` folder if not required at runtime.

Rsync uses `--exclude-from=excluded_files.txt`.

---

## Runtime Behavior

1. **`code.py`** starts an async event loop.
2. **Routines** from `RoutinesRegistry` start:
   - `HttpServerRoutine` to handle web requests on port 80 or 5000 (depending on your code in `hardware.py`).
   - `SchedulerRoutine` to periodically log battery stats.
   - `DisplayRoutine` (if using SSD1306).
   - `HttpCommandsRoutine` for queued tasks from the API.
3. The robot is now ready to accept commands via the `/api/command` endpoint to move servos, calibrate accelerometer, or log data.

---

## REST API Endpoints

When the robot boots, it connects to Wi-Fi with credentials in environment variables (or your `os.getenv(...)` in `hardware.py`).

Below are the main routes defined in [**`api.py`**](./api.py):

| Endpoint               | Method | Description                                                         | Example                             |
|------------------------|--------|---------------------------------------------------------------------|-------------------------------------|
| `/api/stats`          | `GET`  | Returns JSON with sensor data (battery, accelerometer, etc.).       | `curl http://robot/api/stats`       |
| `/api/logs`           | `GET`  | Returns logs since last fetch.                                      | `curl http://robot/api/logs`        |
| `/api/servos-angles`  | `GET`  | Returns a JSON dict of current servo angles.                        | `curl http://robot/api/servos-angles` |
| `/api/saved-positions`| `GET`  | Returns a JSON object of all saved positions.                       | `curl http://robot/api/saved-positions` |
| `/api/command`        | `POST` | Accepts a JSON with `action` and optional `params`. Executes command | `curl -X POST -d '{"action":"wiggle","params":{"movements":5}}' http://robot/api/command` |

**Example Command JSON**:
```json
{
  "action": "set-servos",
  "params": {
    "leg1_hip": 90,
    "leg1_knee": 90,
    "leg1_ankle": 90,
    "leg2_hip": 90,
    "leg2_knee": 90,
    "leg2_ankle": 90,
    "leg3_hip": 90,
    "leg3_knee": 90,
    "leg3_ankle": 90,
    "leg4_hip": 90,
    "leg4_knee": 90,
    "leg4_ankle": 90,
    "hard": true
  }
}
```

---

## Logging & Debugging

- **Serial Port**: Use `screen /dev/cu.usbmodemXXXX 115200` or run `./serial_monitor.sh` (depending on your OS).  
- **Logs**: The `logging_.py` system buffers logs in `LOG_LINES`.  
  - Request them via GET `/api/logs`.  
  - The display routine can also show them on the SSD1306 if set to `Logs` mode.

---

## Testing

1. **Live Tests**:  
   - With the robot connected via USB or Wi-Fi, call your test endpoints:
     - `POST /api/command` with `{ "action": "leg-test" }` or `{"action": "light-test"}` etc.
   - Watch the physical effect or logs.
2. **Local Tests**:  
   - The file `tests.py` includes small functions to test specific hardware.  
   - You can call them from REPL or from an endpoint (see `commands = { "leg-test": leg_test, ... }` in `api.py`).
3. **Simulator** (Experimental):  
   - In `simulator/`, you’ll find a `main.py` (PyQt + Matplotlib) that tries to simulate or visualize leg movements. This is purely optional for offline debugging.

---

## Future Improvements

- **Inverse Kinematics**: Currently partially implemented. Future expansions can add real-time IK-based walking gaits.
- **Motion Routines**: Waypoint-based or inverse-kinematics–based walking to be integrated in `routines.py`.
- **Web Interface**: Expand `static/index.html` for a more interactive servo control or real-time graphs.
- **Configuration**: Centralize all calibrations (like servo mid-angles, battery parameters) for easier adaptation to different hardware.

---

## License & Credits

This is a DIY project for personal use. The user can adapt, modify, or use any part. If you share derivatives, please include references to the original project structure.  
- *Adafruit libraries* used under their respective licenses.  
- *Thanks to the CircuitPython community* for building the ecosystem.  

**Disclaimer**: This code is a Work In Progress (WIP). Use at your own risk. You assume all responsibility for hardware damage, personal injury, or software issues arising from using this firmware.

---

**Enjoy building your quadruped robot!** For questions or contributions, open an Issue or PR on this repository.