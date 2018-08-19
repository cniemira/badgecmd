import logging
import struct

logging.basicConfig(level=logging.INFO)


ENDIAN = 'big'
STATUS_INCLUDES_CHECKSUM = 0x80
STATUS_IS_SLAVE_REPLY = 0x40
STATUS_INVALID_DATA = 0x10
STATUS_COMMAND_NOT_SUPPORTED = 0x08
STATUS_CHECKSUM_NOT_VALID = 0x04
STATUS_PACKET_TOO_LONG_TMP = 0x02
STATUS_PACKET_TOO_LONG = 0x01


class StreamProcessor(object):
    def __init__(self):
        self.states = {
            0: 'reset',
            1: 'u',
            2: 'uu',
            3: 'uub',
            4: 'uubb',
            5: 'uubbs',
            6: 'uubbsc',
            7: 'uubbscl',
            8: 'c',
            9: 'cc',
            }
        self.buffer = []
        self.expecting_checksum = False
        self.remaining = 0
        self.state = 0
        self.reset()


    def process(self, b:int):
        if (self.state in (0, 1) and b == 0x55) \
                or (self.state in (2, 3) and b == 0x42) \
                or (self.state in (5, 8)):
            self.buffer.append(b)
            self.state += 1

        elif self.state == 4:
            if b & STATUS_INCLUDES_CHECKSUM:
                self.expecting_checksum = True
            # A master request should never contain these bits
            if not b & STATUS_IS_SLAVE_REPLY and b & (
                STATUS_INVALID_DATA |
                STATUS_COMMAND_NOT_SUPPORTED |
                STATUS_CHECKSUM_NOT_VALID |
                STATUS_PACKET_TOO_LONG_TMP |
                STATUS_PACKET_TOO_LONG
                ):
                self.reset()
                return
            self.buffer.append(b)
            self.state += 1

        elif self.state == 6:
            self.buffer.append(b)
            self.remaining = b
            if self.remaining:
                self.state += 1
            else:
                self.state += 2

        elif self.state == 7:
            self.buffer.append(b)
            self.remaining -= 1
            if self.remaining == 0:
                self.state += 1

        elif self.state == 9:
            self.buffer.append(b)
            packet = Packet.from_bytes(self.buffer)
            self.reset()
            return packet
        else:
            logging.error('Dropped: 0x{:02X}'.format(b))
            self.reset()
        return False


    def reset(self):
        self.buffer = []
        self.expecting_checksum = False
        self.remaining = 0
        self.state = 0



class Packet(object):
    def __init__(self, command:int = 0, data:list = [],
                 include_checksum:bool = True, slave_reply:bool = False,
                 invalid_data:bool = False, command_not_supported:bool= False,
                 checksum_not_valid:bool = False, 
                 too_long_tmp:bool = False, too_long:bool = False):

        self.command = command
        self.data = data
        self.includes_checksum = include_checksum
        self.slave_reply = slave_reply
        self.invalid_data = invalid_data
        self.command_not_supported = command_not_supported
        self.checksum_not_valid = checksum_not_valid
        self.too_long_tmp = too_long_tmp
        self.too_long = too_long
        self._parsed_checksum_valid = None

    @classmethod
    def from_bytes(cls, data:list):
        if len(data) < 9:
            raise UserWarning('Packet [%s] too small' % (repr(data),))
        status = data[4]
        command = data[5]
        length = data[6]
        if len(data) != length + 9:
            raise UserWarning('Packet length mismatch: got %d expected %d' % 
                (len(data), length + 9))
        checksum = data[-2:]
        if length:
            payload = data[7:7+length]
        else:
            payload = []

        includes_checksum = bool(status & STATUS_INCLUDES_CHECKSUM)
        slave_reply = bool(status & STATUS_IS_SLAVE_REPLY)
        invalid_data = bool(status & STATUS_INVALID_DATA)
        command_not_supported = bool(status & STATUS_COMMAND_NOT_SUPPORTED)
        checksum_not_valid = bool(status & STATUS_CHECKSUM_NOT_VALID)
        too_long_tmp = bool(status & STATUS_PACKET_TOO_LONG_TMP)
        too_long = bool(status & STATUS_PACKET_TOO_LONG)

        packet = Packet(
            command=command,
            data=payload,
            include_checksum = includes_checksum,
            slave_reply = slave_reply,
            invalid_data = invalid_data,
            command_not_supported = command_not_supported,
            checksum_not_valid = checksum_not_valid,
            too_long_tmp = too_long_tmp,
            too_long = too_long,
            )

        if includes_checksum:
            calc_checksum = packet.to_bytes(force_checksum=True)[-2:]
            if checksum == calc_checksum:
                packet._parsed_checksum_valid = True
            else:
                logging.warn('Packet checksum mismatch [%s != %s]' % (
                    repr(checksum),
                    repr(calc_checksum)
                    ))
                packet._parsed_checksum_valid = False
        return packet


    def _checksum(self, data):
        def _initial(c):
            crc = 0
            c = c << 8
            for j in range(8):
                if (crc ^ c) & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                c = c << 1
            return crc

        _tab = [ _initial(i) for i in range(256) ]
        def _update(crc, c):
            cc = 0xff & c

            tmp = (crc >> 8) ^ cc
            crc = (crc << 8) ^ _tab[tmp & 0xff]
            crc = crc & 0xffff
            return crc

        crc = 0x1D0F
        for c in data:
            crc = _update(crc, c)
        return [ord(i) for i in struct.unpack('cc', crc.to_bytes(2, ENDIAN))]


    def to_bytes(self, force_checksum=True):
        status = 0
        do_checksum = self.includes_checksum | force_checksum
        if do_checksum: status = status|STATUS_INCLUDES_CHECKSUM
        if self.slave_reply: status = status|STATUS_IS_SLAVE_REPLY
        if self.invalid_data: status = status|STATUS_INVALID_DATA
        if self.command_not_supported: status = status|STATUS_COMMAND_NOT_SUPPORTED
        if self.checksum_not_valid: status = STATUS_CHECKSUM_NOT_VALID
        if self.too_long_tmp: status = status|STATUS_PACKET_TOO_LONG_TMP
        if self.too_long: status = status|STATUS_PACKET_TOO_LONG

        data = [0x55, 0x55, 0x42, 0x42]
        data.extend([status, self.command, len(self.data)])
        data.extend(self.data)

        if do_checksum:
            data.extend(self._checksum(data[2:]))
        else:
            data.extend(b'\x00\x00')

        return data


    def to_hex(self, **kwargs):
        # return ' '.join(["0x%0.2X" % b for b in self.to_bytes(**kwargs)])
        return ''.join(["%0.2X" % b for b in self.to_bytes(**kwargs)])


    def __repr__(self):
        if self._parsed_checksum_valid is None:
            parsed_checksum = ' '
        else:
            parsed_checksum = 'cs={:b} '.format(self._parsed_checksum_valid)

        data_string = ','.join(['0x{:02X}'.format(b) for b in self.data])
        if not len(data_string):
            data_string = '-'
        fs = '[ic={:b} sr={:b} id={:b} ns={:b} ci={:b} tt={:b} tl={:b} {}0x{:02X} {}]'
        return fs.format(
            self.includes_checksum,
            self.slave_reply,
            self.invalid_data,
            self.command_not_supported,
            self.checksum_not_valid,
            self.too_long_tmp,
            self.too_long,
            parsed_checksum,
            self.command,
            data_string
            )



def cli():
        import argparse
        parser = argparse.ArgumentParser()

        sub_parsers = parser.add_subparsers()
        reader = sub_parsers.add_parser('R')
        reader.set_defaults(mode='R')
        reader.add_argument("data", nargs="*")

        writer = sub_parsers.add_parser('W')
        writer.set_defaults(mode='W')
        writer.add_argument("command")
        writer.add_argument("--include-checksum", dest='cs',
            action='store_true')
        writer.add_argument("--slave-reply", dest='sr', action='store_true')
        writer.add_argument("--invalid-data", dest='id', action='store_true')
        writer.add_argument("--command-not-supported", dest='cns',
            action='store_true')
        writer.add_argument("--checksum-not-valid", dest='cnv',
            action='store_true')
        writer.add_argument("--too-long-tmp", dest='tlt',
            action='store_true')
        writer.add_argument("--too-long", dest='tl', action='store_true')
        writer.add_argument("data", nargs="*")

        args = vars(parser.parse_args())

        if 'mode' not in args:
            parser.print_help()
        elif args['mode'] == 'R':
            streamproc = StreamProcessor()
            for b in args['data']:
                for i in b.split(','):
                    packet = streamproc.process(int(i, 16))
                    if packet:
                        print(packet)
        else:
            packet = Packet(
                command = int(args["command"]),
                data = [int(i) for i in args['data']],
                include_checksum = args["cs"],
                slave_reply = args["sr"],
                invalid_data = args["id"],
                command_not_supported = args["cns"],
                checksum_not_valid = args["cnv"],
                too_long_tmp = args["tlt"],
                too_long = args["tl"],
                )

            print(packet.to_hex())



if __name__ == '__main__':
    cli()
