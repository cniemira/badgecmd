import asyncio

from serial_asyncio import create_serial_connection

class Output(asyncio.Protocol):

    def __init__(self):
        super().__init__()
        self._transport = None

    def connection_made(self, transport):
        self._transport = transport
        print('port opened', self._transport)
        self._transport.serial.rts = False
        self._transport.write(b'Hello, World!\n')

    def data_received(self, data):
        print('data received', repr(data))
        if b'\n' in data:
            self._transport.close()

    def connection_lost(self, exc):
        print('port closed')
        self._transport.loop.stop()

    def pause_writing(self):
        print('pause writing')
        print(self._transport.get_write_buffer_size())

    def resume_writing(self):
        print(self._transport.get_write_buffer_size())
        print('resume writing')

loop = asyncio.get_event_loop()
coro = create_serial_connection(loop, Output, '/dev/tty.usbmodem1424421', baudrate=115200)
loop.run_until_complete(coro)
loop.run_forever()
loop.close()