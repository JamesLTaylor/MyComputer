import copy

import pyk8055
import time


instructions = {'NOP': '00000',
                'RDV': '00011',
                'CPY': '00010',
                'ADV': '01001',
                'JMZ': '10001'}
instructions_inv = {v: k for k, v in instructions.items()}
registers = {'P0': '000',
             'P1': '001',
             'M0': '010',
             'M1':  '011',
             '*P': '100',
             '*M': '101',
             'A': '110',
             'R': '111'
             }
registers_inv = {v: k for k, v in registers.items()}

device_bus_addr = {0: '000',  # P1 first 4
                   1: '001',
                   2: '010',  # P2 first 4 - not used yet
                   3: '011',
                   4: '100',  # general read from computer first 4
                   5: '101',
                   6: '110',  # output
                   7: '111'}
device_bus_addr_inv = {v: k for k, v in device_bus_addr.items()}


def bin_fixed_width(val, width):
    return '{:0{}b}'.format(val, width)


def translate_to_readable(val1, val2):
    """ Returns list of Instruction, value pair, single value
    """
    instruction = instructions_inv.get(val1 % 32, '??')
    buffer = registers_inv.get(val1 // 32, '??')
    value = val2
    return [f'{instruction:<5}{buffer:<4}{value:<3}', (val1, val2), {val1 + val2*256}]


def translate_to_bin(line):
    parts = line.split()
    for i in range(len(parts)):
        try:
            parts[i] = int(parts[i])
        except ValueError:
            pass
    val2 = '00000000'
    if parts[0] in instructions:
        val1 = instructions[parts[0]]
    elif isinstance(parts[0], int) and parts[0] < 256:
        val1 = bin_fixed_width(parts[0], 8)
    elif isinstance(parts[0], int) and parts[0] >= 256:
        val1 = bin_fixed_width(parts[0] % 256, 8)
        val2 = bin_fixed_width(parts[0] // 256,8)
    else:
        raise Exception(f'First value must be an instruction or a number: ({line})')
    if len(parts) > 1:
        if parts[1] in registers:
            val1 += registers[parts[1]]
        elif isinstance(parts[1], int) and parts[1] < 256:
            val2 = bin_fixed_width(parts[1], 8)
        else:
            raise Exception(f'Second value must be a buffer or a number: ({line})')
    if len(parts) == 3:
        if isinstance(parts[2], int):
            if abs(parts[2]) < 256:
                v = parts[2] if parts[2] >= 0 else 256 - parts[2]
                val2 = bin_fixed_width(v, 8)
            else:
                raise Exception(f'Immediate value must be a between -255 and 255: ({line})')
        else:
            val2 = '00000' + registers[parts[2]]
    return val1 + ' ' + val2


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


class DummyDevice:
    def __init__(self, expected_machine_state: 'ExpectedMachineState'):
        self.state = expected_machine_state

    def digital_off(self, position):
        self.state.set(position, 0)

    def digital_on(self, position):
        self.state.set(position, 1)

    def digital_in(self, position):
        return self.state.get(position)


class ExpectedMachineState:
    """ 8 lines in
    5 lines out
    A bunch of internal lines and registers

    """
    def __init__(self):
        # lines to and from device
        self.lines_in = [0 for _ in range(8)]
        self.lines_out = [0 for _ in range(5)]

        # device to computer bus
        self.bus_from_device = [0 for _ in range(8)]  # includes lines and a 4bit reg

        # "computer"
        self.N = [0 for _ in range(8)]
        self.T = [0 for _ in range(8)]
        self.P1 = [0 for _ in range(8)]
        self.M1 = [0 for _ in range(8)]
        self.A = [0 for _ in range(8)]
        self.R = [0 for _ in range(8)]
        self.W = [0 for _ in range(8)]  # window to *M or *P
        self.TP1 = [0 for _ in range(8)]  # temp value for pointer incrementing
        self.f = [1,0,0,0]
        self.nf = [0, 1, 1, 1]
        self.clock = 0

        self.cmp = 0
        self.write = 0
        self.carry = 0

    def bus_addr(self):
        addr = ''.join([str(self.lines_in[i]) for i in [1, 2, 3]])
        return device_bus_addr_inv[addr]

    def set(self, line, value):
        line = line - 1
        if line == 0:
            if value:
                self.clock = 1
                self.reg_write()
                print(f'click while in phase {self.f}')
            else:
                self.clock = 0
                if self.f == [1,0,0,0]:
                    self.f = [0,1,0,0]
                elif self.f == [0,1, 0,0]:
                    self.f = [0,0,1, 0]
                elif self.f == [0,0, 1,0]:
                    self.f = [0,0,0, 1]
                elif self.f == [0, 0, 0, 1]:
                    self.f = [1, 0, 0, 0]
                self.nf = [0 if (i == 1) else 1 for i in self.f]
                print(f'move to phase {self.f}')
            if self.clock == 1 and self.f == [0,0,0,1]:
                a=1
        elif line in [4, 5, 6, 7]:
            if self.bus_addr() == 6:
                self.bus_from_device[line-4] = value
            elif self.bus_addr() == 7:
                self.bus_from_device[line] = value
            else:
                raise Exception('Tried to write to an input location')
        else:
            self.lines_in[line] = value

    @staticmethod
    def _src_tgt(bits):
        val = [1, 1, 1, 1, 1, 1, 1, 1]
        ind = 4*bits[0] + 2*bits[1] + bits[2]
        val[ind] = 0
        return val

    def src(self):
        return self._src_tgt(self.N[5:])

    def tgt(self):
        return self._src_tgt(self.T[5:])

    def get(self, line):
        if line == 1:
            return self.write
        if self.bus_addr() == 0:
            return self.bus_from_registers()[line-2]
        elif self.bus_addr() == 1:
            return self.bus_from_registers()[line+2]
        return 0

    def bus_from_registers(self):
        # f0 or (f1 and n4)
        flag_p1 = (self.nf[0]) and (self.nf[1] or not (self.N[4]))
        # f1 and not n4
        flag_m1 = (self.nf[1]) or self.N[4]
        # f2 and src[6]
        flag_a = self.nf[2] or self.src()[6]
        # f2 and (n4 or src[4] or src[5])
        flag_w = self.nf[2] or (not(self.N[4]) and self.src()[4] and self.src()[5])
        # f2 and src[7]
        flag_r = self.nf[2] or self.src()[7]

        if not flag_p1:
            return self.P1
        if not flag_m1:
            return self.M1
        if not flag_w:
            return self.W
        if not flag_a:
            return self.A
        if not flag_r:
            return self.R

    def bus_to_registers(self):
        '''
        logic of computer
        '''
        if self.f[0]:
            return self.bus_from_device
        if self.f[1]:
            return self.bus_from_device
        if self.f[2] and self.N[3]:  # CPY
            return self.bus_from_registers()
        if self.f[2] and self.N[1]:  # ADV
            return self.bus_from_registers()
        if self.f[2] and self.N[1]:  # JMZ
            return self.bus_from_registers()
        if self.f[3]:
            return None  # this will be the incremented program counter

    def reg_write(self):
        """ Clock has had rising edge, write registers
        """
        clk = 1
        click_n = self.f[0] and clk
        click_t = self.f[1] and clk
        click_w = self.f[1] and clk
        click_p1 = ((self.f[2] and self.N[3] and not self.tgt()[1])
                    or (self.f[2] and self.N[4] and not self.src()[1])
                    # or (self.f[2] and self.cmp and clk)
                    # or (self.f[3] and not self.cmp)
                    )
        click_m1 = ((self.f[2] and self.N[3] and not self.tgt()[3])
                    or (self.f[2] and self.N[4] and not self.src()[3]))
        click_a = ((self.f[2] and self.N[3] and not self.tgt()[6])
                   or (self.f[2] and self.N[4] and not self.src()[6]))
        click_r = ((self.f[2] and self.N[3] and not self.tgt()[7])
                   or (self.f[2] and self.N[4] and not self.src()[7]))

        if click_n:
            self.N = copy.copy(self.bus_from_device)
        if click_t:
            self.T = copy.copy(self.bus_from_device)
        if click_p1:
            self.P1 = copy.copy(self.bus_to_registers())
        if click_m1:
            self.M1 = copy.copy(self.bus_to_registers())
        if click_w:
            self.W = copy.copy(self.bus_to_registers())
        if click_a:
            self.A = copy.copy(self.bus_to_registers())
        if click_r:
            self.R = copy.copy(self.bus_to_registers())


class MyComputerInterface:
    """ Controls the device that sends and receives data from the computer. And acts as the
    clock and memory for that computer.

    device has 16 bit address on 0, 1, 2, 3
    reads 8 bits in on 4, 5
    writes 8 bits out on 6, 7

    """
    MEMORY_DELAY = 0.01

    def __init__(self, program, expected_machine_state):
        # self.device = pyk8055.device()
        self.device = DummyDevice(expected_machine_state)
        self.readable_memory = program
        self.memory = [translate_to_bin(line) for line in program]
        self.expected_machine_state = expected_machine_state
        self.clock = 0
        self.phase = 1
        self.saved_address = 0

    def log(self, message):
        print(message)

    def sleep(self):
        time.sleep(self.MEMORY_DELAY)

    def set_mem_bus_addr(self, value):
        vals = device_bus_addr[value]
        for i, c in enumerate(vals):
            if c == '0':
                self.device.digital_off(2+i)
            else:
                self.device.digital_on(2+i)

    def read_from_bus(self, address):
        """ Read from bus and return value
        """
        self.set_mem_bus_addr(address)
        self.sleep()
        vals = [str(self.device.digital_in(2+i)) for i in range(4)]
        self.log(f'reading {"".join(vals)} from address = {address}')
        return (8 * int(vals[0])
                + 4 * int(vals[1])
                + 2 * int(vals[2])
                + 1 * int(vals[3]))


    def write_to_bus(self, address, vals):
        self.log(f'writing {"".join(vals)} to address = {address}')
        self.set_mem_bus_addr(address)
        self.sleep()
        for i, c in enumerate(vals):
            if c == '0':
                self.device.digital_off(5+i)
            else:
                self.device.digital_on(5+i)

    def read_write_cycle(self):
        address = 0
        mult = 16
        for i in range(2):
            self.set_mem_bus_addr(i)
            address = address + mult * self.read_from_bus(i)
            mult = mult // 16

        write = self.device.digital_in(1)
        if write:
            # Do something if write is True
            pass

        if (address // 2) >= len(self.memory):
            self.log(f'address {address} is out of range,  returning 0')
            address = 0
        if self.phase == 2:
            # hack while I think of how to pass the address and value back to the device on the same cycle
            self.saved_address == address
        value = self.memory[address//2]
        self.log(f'contents at {address}: {self.memory[address//2]} / {self.readable_memory[address//2]}')
        if (address % 2) == 1:
            offset = 9
        else:
            offset = 0
        self.write_to_bus(6, value[offset:(offset+4)])
        self.write_to_bus(7, value[(offset+4):(offset+8)])


    def toggle_clock(self):
        # Get address from computer via device
        if self.clock == 0:
            self.clock = 1
            self.device.digital_on(1)
        else:
            self.clock = 0
            self.device.digital_off(1)
            self.phase += 1
            if self.phase == 5:
                self.phase = 1


