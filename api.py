from hardware import server, battery, accelerometer, light
from adafruit_httpserver import Request, JSONResponse, POST, GET

@server.route("/api/stats", GET)
def stats(request: Request):
    data = {
        "battery_percentage": battery.get_battery_percentage(),
        "battery_voltage": battery.get_battery_voltage(),
        "accelerometer_xyz": accelerometer.xyz,
        "accelerometr_angles": accelerometer.angles,
    }
    return JSONResponse(request, data)

@server.route("/api/command", POST)
def command(request: Request):
    request_data = request.json()
    action = request_data.get("action")
    if action in commands:
        commands[action]()
    else:
        print(f"❌ Command not found: {action}")

    print(request_data)
    data = {
        "message": "Command received",
    }
    return JSONResponse(request, data)

commands = {
    "light-on": light.turn_on,
    "light-off": light.turn_off,
}