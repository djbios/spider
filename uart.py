import busio
import pins
from routines import BaseRoutine, RoutinesRegistry
from logging_ import log

@RoutinesRegistry.register()
class UARTRoutine(BaseRoutine):
    def __init__(self) -> None:
        self.uart = busio.UART(pins.UART_TX, pins.UART_RX, baudrate=115200, timeout=0.0001)

        super().__init__()

    async def tick(self):
        data = self.uart.read()
        if data is not None:
            data_str = ''.join([chr(b) for b in data])
            log(data_str, end='')
