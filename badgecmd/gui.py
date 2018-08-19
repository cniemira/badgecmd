import argparse
import asyncio
import logging
import sys

import serial
import quamash
import serial_asyncio

from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMainWindow
from quamash import QEventLoop

from badgecmd.badgebus import Packet, StreamProcessor
from badgecmd.mainwindow import Ui_MainWindow


logging.basicConfig(level=logging.DEBUG)

qBlack = QColor(0, 0, 0)
qBlue = QColor(0, 0, 255)
qGreen = QColor(32, 192, 32)
qRed = QColor(255, 0, 0)


def chunk(data, size):
    for i in range(0, len(data), size):
        yield data[i:i + size]


@asyncio.coroutine
def create_serial_connection(loop, protocol, *args, **kwargs):
    ser = serial.serial_for_url(*args, **kwargs)
    transport = serial_asyncio.SerialTransport(loop, protocol, ser)
    return (transport, protocol)



class BadgeProtocol(asyncio.Protocol):
    def __init__(self, io):
        asyncio.Protocol.__init__(self)
        self.io = io
        self.stream = None
        self.transport = None

    def close(self):
        if self.transport:
            self.transport.close()
            self.transport = None

    def connection_lost(self, exc):
        logging.debug('port closed')
        self.io.disconnect.emit()
        asyncio.get_event_loop().stop()

    def connection_made(self, transport):
        self.stream = StreamProcessor()
        self.transport = transport
        logging.debug('opened: %s' % (transport,))
        transport.serial.rts = False

    def data_received(self, data):
        logging.debug('rx: %s' % (repr(data),))
        for byte in data:
            packet = self.stream.process(int(byte))
            if packet:
                self.io.rx.emit(packet)

    def pause(self):
        if self.transport:
            self.transport.pause_reading()

    def send(self, data):
        data_bytes = bytes(data)
        logging.debug('tx: %s' % (data_bytes))
        if self.transport:
            self.transport.write(data_bytes)

    def unpause(self):
        if self.transport:
            self.transport.resume_reading()


class IoSignals(QObject):
    disconnect = pyqtSignal()
    rx = pyqtSignal(object)


class BadgecmdMainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, app, device, baudrate):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        self.device = device
        self.baudrate = baudrate

        self.app = app
        self.setupUi(self)
        self.setWindowTitle('Badgecmd')

        self.main_loop = QEventLoop(self.app)
        asyncio.set_event_loop(self.main_loop)

        self.io = IoSignals()
        self.proto = BadgeProtocol(self.io)
        self.serial_coro = None
        self.awaiting = None
        self.paused = False

        # connect all of the signals 
        for method in self.__dir__():
            if method.startswith('_when_'):
                emitter_name, signal_name = method.split('_')[-2:]
                signal = getattr(getattr(self, emitter_name), signal_name)
                signal.connect(getattr(self, method))

    def _serial_connect(self):
        if not self.serial_coro:
            self.serial_coro = create_serial_connection(
                self.main_loop,
                self.proto,
                self.device,
                # baudrate=9600
                baudrate=self.baudrate
                )
            self.main_loop.run_until_complete(self.serial_coro)

    def _serial_disconnect(self):
        if self.serial_coro:
            self.proto.close()
            self.serial_coro = None

    def _when_clear_clicked(self):
        self.output.clear()

    def _when_connect_clicked(self):
        if self.connect.text() == 'connect':
            self._serial_connect()
            self.connect.setText('disconnect')
            self.pause.setText('pause')
            self.paused = False
        else:
            self._serial_disconnect()
            self.connect.setText('connect')

    def _when_io_disconnect(self):
        self.connect.setText('connect')

    def _when_io_rx(self, packet):
        # if packet.command == 0xAF and packet.slave_reply == 0:
        #     logging.warn('skipping 0xAF')
            # return
        if self.paused:
            return
        if self.awaiting == packet.command and packet.slave_reply:
            self.output.setTextColor(qGreen)
            self.awaiting = None
        else:
            self.output.setTextColor(qBlue)
        self.output.append(' '.join([
            'rx:',
            repr(packet),
            ','.join(["0x{:02X}".format(i) for i in packet.to_bytes()])
            ]))
        self.output.setTextColor(qBlack)

    def _when_input_returnPressed(self):
        raw = self.input.text()
        if len(raw):
            try:
                data = [int(i, 16) for i in raw.split(' ')]
            except ValueError as e:
                logging.error(e)
                return
            packet = Packet(
                command = data[0],
                data = data[1:],
                include_checksum = self.crc.isChecked(),
                slave_reply = self.mode.text() == 'S'
                )
            packet_bytes = packet.to_bytes()
            if self.mode.text() == 'M':
                self.awaiting = packet.command
            self.proto.send(packet_bytes)
            self.output.setTextColor(qRed)
            self.output.append(' '.join([
                'tx:',
                repr(packet),
                ','.join(["0x{:02X}".format(i) for i in packet_bytes])
                ]))
            self.output.setTextColor(qBlack)

    def _when_mode_clicked(self):
        if self.mode.text() == 'M':
            self.mode.setText('S')
        else:
            self.mode.setText('M')

    def _when_pause_clicked(self):
        if self.pause.text() == 'pause':
            self.pause.setText('unpause')
            self.paused = True
            # self.proto.pause()
        else:
            self.pause.setText('pause')
            self.paused = False
            # self.proto.unpause()

    def exec_(self):
        return self.main_loop.run_forever()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("device", type=str)
    args = vars(parser.parse_args())

    app = QApplication(['Badgecmd'])
    window = BadgecmdMainWindow(app, args['device'], args['baud'])
    window.show()
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()
