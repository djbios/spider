# import asyncio
# from routines import RoutinesRegistry, BaseRoutine
# import circuitpython_schedule as schedule
# from hardware import battery, walker, storage
# from adafruit_pca9685 import PCA9685
# import time

# # Discovery
# from serial import * # noqa
# from tests import leg_test, light_test  # noqa


# # Tests


# # Routines
# @RoutinesRegistry.register()
# class SchedulerRoutine(BaseRoutine):
#     def __init__(self) -> None:
#         schedule.every(30).seconds.do(battery.print_battery)
#         print("SchedulerRoutine initialized")
#         super().__init__()

#     async def tick(self):
#         schedule.run_pending()


# async def initial_actions():
#     battery.print_battery()
#     light_test()
#     storage['last_boot'] = time.time()
#     await leg_test()
#     await walker.wiggle(10)
#     await walker.to_zero()


# # Main
# async def main():
#     await RoutinesRegistry.initialise()
#     await asyncio.gather(
#         asyncio.create_task(initial_actions()),
#         RoutinesRegistry.routines_coroutine,
#     )


# try:
#     asyncio.run(main())
# except KeyboardInterrupt:
#     print("Interrupted")
#     walker.deactivate()

import os

import adafruit_connection_manager
import wifi

import adafruit_requests


# Get WiFi details, ensure these are setup in settings.toml
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
JSON_GET_URL = "https://httpbin.org/get"
JSON_POST_URL = "https://httpbin.org/post"

# Initalize Wifi, Socket Pool, Request Session
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)
rssi = wifi.radio.ap_info.rssi

print(f"\nConnecting to {ssid}...")
print(f"Signal Strength: {rssi}")
try:
    # Connect to the Wi-Fi network
    wifi.radio.connect(ssid, password)
except OSError as e:
    print(f"❌ OSError: {e}")
print(f"✅ Wifi! IP: {wifi.radio.ipv4_address}")

print(f" | GET Text Test: {TEXT_URL}")
with requests.get(TEXT_URL) as response:
    print(f" | ✅ GET Response: {response.text}")
print("-" * 80)

print(f" | GET Full Response Test: {JSON_GET_URL}")
with requests.get(JSON_GET_URL) as response:
    print(f" | ✅ Unparsed Full JSON Response: {response.json()}")
print("-" * 80)

DATA = "This is an example of a JSON value"
print(f" | ✅ JSON 'value' POST Test: {JSON_POST_URL} {DATA}")
with requests.post(JSON_POST_URL, data=DATA) as response:
    json_resp = response.json()
    # Parse out the 'data' key from json_resp dict.
    print(f" | ✅ JSON 'value' Response: {json_resp['data']}")
print("-" * 80)

json_data = {"Date": "January 1, 1970"}
print(f" | ✅ JSON 'key':'value' POST Test: {JSON_POST_URL} {json_data}")
with requests.post(JSON_POST_URL, json=json_data) as response:
    json_resp = response.json()
    # Parse out the 'json' key from json_resp dict.
    print(f" | ✅ JSON 'key':'value' Response: {json_resp['json']}")
print("-" * 80)

print("Finished!")

from adafruit_httpserver import (
    Server,
    REQUEST_HANDLED_RESPONSE_SENT,
    Request,
    FileResponse,
)

server = Server(pool, "/static", debug=True)


@server.route("/")
def base(request: Request):
    """
    Serve the default index.html file.
    """
    return FileResponse(request, "index.html")

server.start(str(wifi.radio.ipv4_address))


while True:
    try:
        # Do something useful in this section,
        # for example read a sensor and capture an average,
        # or a running total of the last 10 samples

        # Process any waiting requests
        pool_result = server.poll()

        if pool_result == REQUEST_HANDLED_RESPONSE_SENT:
            # Do something only after handling a request
            pass

        # If you want you can stop the server by calling server.stop() anywhere in your code
    except OSError as error:
        print(error)
        continue
