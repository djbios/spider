import busio
import pins
from routines import BaseRoutine, RoutinesRegistry


@RoutinesRegistry.register()
class UARTRoutine(BaseRoutine):
    def __init__(self) -> None:
        #self.uart = busio.UART(pins.UART_TX, pins.UART_RX, baudrate=9600)
        super().__init__()

    async def run(self):
        ...
        # data = self.uart.read(32)
        # print(data)
