import json
from hardware import server, battery, accelerometer, light, walker, display
from adafruit_httpserver import Request, JSONResponse, POST, GET
from tests import leg_test
from routines import RoutinesRegistry, BaseRoutine
from utils import run_callable_async_or_not
from flash_storage import storage
from logging import log, get_unsent_loglines


@RoutinesRegistry.register()
class HttpCommandsRoutine(BaseRoutine):
    def __init__(self) -> None:
        super().__init__()
        self.tasks = []

    async def tick(self):
        while len(self.tasks):
            task, task_kwargs = self.tasks.pop(0)
            await run_callable_async_or_not(task, **task_kwargs)


    def add_task(self, task, task_kwargs):
        log(f"Adding task: {task}")
        self.get_instance().tasks.append((task, task_kwargs))


@server.route("/api/stats", GET)
def stats(request: Request):
    data = {
        "battery_percentage": battery.get_battery_percentage(),
        "battery_voltage": battery.get_battery_voltage(),
        "accelerometer_xyz": accelerometer.xyz,
        "accelerometr_angles": accelerometer.angles,
        "light_brightness": light.get_brightness(),
        "storage_content": json.dumps(storage._data),
    }
    return JSONResponse(request, data)


@server.route("/api/command", POST)
def command(request: Request):
    request_data = request.json()
    action = request_data.get("action")
    if action in commands:
        kwargs = request_data.get("params", {})
        action_function = commands[action]
        HttpCommandsRoutine.get_instance().add_task(action_function, kwargs)
    else:
        log(f"❌ Command not found: {action}")

    data = {
        "message": "Command received",
    }
    return JSONResponse(request, data)

@server.route("/api/logs", GET)
def logs(request: Request):
    logs = get_unsent_loglines('http')
    return JSONResponse(request, logs)


commands = {
    "set-light-brightness": light.set_brightness,
    "wiggle": walker.wiggle,
    "leg-test": leg_test,
    "to-zero": walker.to_zero,
    "calibrate-zero": accelerometer.calibrate_zero,
    "write-oled": display.write_text,
    "display-mode": display.set_mode,
    "set-servos": walker.set_servos,
    "save-position": walker.save_position,
    "load-position": walker.load_position,
}
