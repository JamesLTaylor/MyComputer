from PyQt5.QtWidgets import QApplication, QWidget
import pyk8055
import time

# # create the QApplication
# app = QApplication([])
#
# # create the main window
# window = QWidget(windowTitle='Hello World')
# window.show()
#
# # start the event loop
# app.exec()


instructions = {'NOP': 0,
                'RDV': 1,
                'RDD': 2,
                'WRT': 3,
                'ADD': 4,
                'ADV': 5,
                'JZ': 6}
instructions_inv = {v: k for k, v in instructions.items()}
buffers = {'': 0,  # 000
           'R': 1,  # 001
           'P1': 2, # 010
           'P2': 3, # 011
           'M1': 4, # 100
           'M2': 5, # 101
           'A': 6,  # 110
           'B': 7}  # 111
buffers_inv = {v: k for k, v in buffers.items()}


def bin_fixed_width(val, width):
    return '{:0{}b}'.format(val, width)


def translate_to_readable(val1, val2):
    """ Returns list of Instruction, value pair, single value
    """
    instruction = instructions_inv.get(val1 % 32, '??')
    buffer = buffers_inv.get(val1 // 32, '??')
    value = val2
    return [f'{instruction:<5}{buffer:<4}{value:<3}', (val1, val2), {val1 + val2*256}]


def translate_to_bin(line):
    parts = line.split()
    for i in range(len(parts)):
        try:
            parts[i] = int(parts[i])
        except ValueError:
            pass
    val2 = 0
    if parts[0] in instructions:
        val1 = instructions[parts[0]]
    elif isinstance(parts[0], int) and parts[0] < 256:
        val1 = parts[0]
    elif isinstance(parts[0], int) and parts[0] >= 256:
        val1 = parts[0] % 256
        val2 = parts[0] // 256
    else:
        raise Exception(f'First value must be an instruction or a number: ({line})')
    if len(parts) > 1:
        if parts[1] in buffers:
            val1 += 32 * buffers[parts[1]]
        elif isinstance(parts[1], int) and parts[1] < 256:
            val2 = parts[1]
        else:
            raise Exception(f'Second value must be a buffer or a number: ({line})')
    if len(parts) > 2:
        val2 = parts[2]
    return val1, val2


def get_add_numbers_prog():
    code = '''\
RDV  A  7
RDV  B  5
ADV  A  7
ADV  B  255
JZ   B  12
RDD  P1 4
ADD  R
NOP
75
10000
12   15
'''
    listing = [translate_to_bin(line) for line in code.splitlines()]
    return listing


class MyComputer:
    MEMORY_DELAY = 0.5

    def __init__(self):
        self.device = pyk8055.device()
        self.program = get_add_numbers_prog()
        for v1, v2 in self.program:
            print(translate_to_readable(v1, v2))

    def sleep(self):
        time.sleep(self.MEMORY_DELAY)

    def set_mem_bus_addr(self, value):
        vals = bin_fixed_width(value, 3)
        for i, c in enumerate(vals):
            if c == '0':
                self.device.digital_off(2+i)
            else:
                self.device.digital_on(2+i)

    def read_from_bus(self, address):
        self.set_mem_bus_addr(address)
        self.sleep()
        return (self.device.digital_in(2)
                + 2 * self.device.digital_in(3)
                + 4 * self.device.digital_in(4)
                + 8 * self.device.digital_in(5))

    def write_to_bus(self, address, value):
        self.set_mem_bus_addr(address)
        self.sleep()
        vals = bin_fixed_width(value, 4)
        for i, c in enumerate(vals):
            if c == '0':
                self.device.digital_off(5+i)
            else:
                self.device.digital_on(5+i)

    def read_write_cycle(self):
        address = 0
        mult = 1
        for i in range(4):
            self.set_mem_bus_addr(i)
            address = address + mult * self.read_from_bus()
            mult = mult * 16

        write = self.device.digital_in(1)
        if write:
            pass
        else:
            value = self.program[address//2][address % 2]
            self.write_to_bus(4, value // 16)
            self.write_to_bus(4, value % 16)


computer = MyComputer()
computer.write_to_bus(5, 1)
computer.write_to_bus(6, 2)
computer.write_to_bus(5, 3)
computer.write_to_bus(6, 4)
