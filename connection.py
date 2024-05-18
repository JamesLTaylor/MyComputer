import copy

import pyk8055
import time

instructions = {'NOP': '00000',
                'RDV': '00111',
                'CPY': '00101',
                'WRT': '00100',
                'RDM': '00110',
                'ADV': '01001',
                'ADM': '01000',
                'JMZ': '10001'}
instructions_inv = {v: k for k, v in instructions.items()}
registers = {'P0': '000',
             'P1': '001',
             'M0': '010',
             'M1': '011',
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


def bin_fixed_width(val, width=8):
    """ Convert a number to a binary string

    :param val:
    :param width:
    :return:
    """
    return '{:0{}b}'.format(val, width)


def bin_to_value(vals):
    mult = 1
    value = 0
    for v in vals[::-1]:
        value += mult * int(v)
        mult *= 2
    return value


def translate_to_readable(val1, val2):
    """ Returns list of Instruction, value pair, single value
    """
    instruction = instructions_inv.get(val1 % 32, '??')
    register = registers_inv.get(val1 // 32, '??')
    value = val2
    return [f'{instruction:<5}{register:<4}{value:<3}', (val1, val2), {val1 + val2 * 256}]


def translate_to_machine_instruction(line):
    """ Translate readable instructions into binary memory contents

    :param line:
    :return:
    """
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
        val2 = bin_fixed_width(parts[0] // 256, 8)
    else:
        raise Exception(f'First value must be an instruction or a number: ({line})')
    if len(parts) > 1:
        if parts[1] in registers:
            val1 += registers[parts[1]]
        elif isinstance(parts[1], int) and parts[1] < 256:
            val2 = bin_fixed_width(parts[1], 8)
        else:
            raise Exception(f'Second value must be a register or a number: ({line})')
    if len(parts) == 3:
        if isinstance(parts[2], int):
            if abs(parts[2]) < 256:
                v = parts[2] if parts[2] >= 0 else 256 + parts[2]
                val2 = bin_fixed_width(v, 8)
            else:
                raise Exception(f'Immediate value must be a between -255 and 255: ({line})')
        else:
            val2 = '00000' + registers[parts[2]]
    return val1.zfill(8) + ' ' + val2.zfill(8)


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
        self.r = {'N': [0 for _ in range(8)], 'T': [0 for _ in range(8)], 'P1': [0 for _ in range(8)],
                  'M1': [0 for _ in range(8)], 'A': [0 for _ in range(8)], 'R': [0 for _ in range(8)],
                  'W': [0 for _ in range(8)], 'TP1': [0 for _ in range(8)]}
        self.f = [1, 0, 0, 0]
        self.nf = [0, 1, 1, 1]
        self.clock = 0

        self.cmp = 0
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
            else:
                self.clock = 0
                if self.f == [1, 0, 0, 0]:
                    self.f = [0, 1, 0, 0]
                elif self.f == [0, 1, 0, 0]:
                    self.f = [0, 0, 1, 0]
                elif self.f == [0, 0, 1, 0]:
                    self.f = [0, 0, 0, 1]
                elif self.f == [0, 0, 0, 1]:
                    self.f = [1, 0, 0, 0]
                self.nf = [0 if (i == 1) else 1 for i in self.f]
            if self.clock == 1 and self.f == [0, 0, 0, 1]:
                a = 1
        elif line in [4, 5, 6, 7]:
            if self.bus_addr() == 6:
                self.bus_from_device[line - 4] = value
            elif self.bus_addr() == 7:
                self.bus_from_device[line] = value
            else:
                raise Exception('Tried to write to an input location')
        else:
            self.lines_in[line] = value

    @staticmethod
    def _src_tgt(bits):
        val = [1, 1, 1, 1, 1, 1, 1, 1]
        ind = 4 * bits[0] + 2 * bits[1] + bits[2]
        val[ind] = 0
        return val

    def _src_n(self):
        """ The source in last 3 bits of N; is sometimes a source
        """
        return self._src_tgt(self.r['N'][5:])

    def _tgt_t(self):
        """ the source in last 3 bits of T; is sometimes a target

        """
        return self._src_tgt(self.r['T'][5:])

    def src(self):
        """
        each bit should be implemented as src_n and not n3 or tgt_t and n3

        ssi = (n3 and ti) or (not n3) and si

        """
        return self._src_n()
        if self.r['N'][3]:
            return self._tgt_t()
        else:
            return self._src_n()

    def tgt(self):
        """
        each bit should be implemented as tgt_t and not n3 or src_n and n3

        """
        if self.r['N'][3]:
            return self._src_n()
        else:
            return self._tgt_t()

    def write(self):
        # This will write on WRT and RDM, but that is OK since RDM will rewrite the same value.
        return self.r['N'][2] and not self.r['N'][4]

    def get(self, line):
        if line == 1:
            return self.write()
        if self.bus_addr() == 0:
            return self.bus_from_registers()[line - 2]
        elif self.bus_addr() == 1:
            return self.bus_from_registers()[line + 2]
        if self.bus_addr() == 4:
            return self.bus_from_registers()[line - 2]
        elif self.bus_addr() == 5:
            return self.bus_from_registers()[line + 2]
        return 0

    def flags(self):
        """
        Flag to disable data from registers to bus.
        In phase 2 always expose SRC unless RDV or RDM

        """
        flag = {}
        n_read_source = self.nf[2] or self.r['N'][3] # not read source

        # f0 or (f1 and n4) or (read_source and src[1])
        flag['P1'] = (self.nf[0]) and (self.nf[1] or not (self.r['N'][4])) and (n_read_source or self.src()[1])
        # (f1 and not n4) or (f2 and src[3])
        flag['M1'] = (self.nf[1] or self.r['N'][4]) and (n_read_source or self.src()[3])

        # f2 and src[6]
        flag['A'] = n_read_source or self.src()[6]
        # f2 and (n2 and n3)
        # negated: f2' or (n2 nand n3)
        flag['W'] = self.nf[2] or (not (self.r['N'][2] and self.r['N'][3]))
        # f2 and src[7]
        flag['R'] = n_read_source or self.src()[7]
        return flag

    def bus_from_registers(self):
        flag = self.flags()
        for key in ['P1', 'M1', 'W', 'A', 'R']:
            if not flag[key]:
                return self.r[key]

    def bus_to_registers(self):
        '''
        logic of computer
        '''
        if self.f[0]:
            return self.bus_from_device
        if self.f[1]:
            return self.bus_from_device
        if self.f[2] and self.r['N'][2]:  # CPY
            return self.bus_from_registers()
        if self.f[2] and self.r['N'][1]:  # ADV
            a = bin_to_value(self.bus_from_registers())
            b = bin_to_value(self.r['T'])
            res = a + b
            if res > 255:
                self.carry = 1
                res = res - 256
            return [int(i) for i in bin_fixed_width(res)]
        if self.f[2] and self.r['N'][0]:  # JMZ
            a = bin_to_value(self.bus_from_registers())
            self.cmp = a == 0
            if self.cmp:
                return copy.copy(self.r['T'])
            else:
                return None
        if self.f[3]:
            return None  # this will be the incremented program counter

    def clicks(self):
        click = {}
        n = self.r['N']
        click['N'] = self.f[0]
        click['T'] = self.f[1]
        click['W'] = self.f[1]
        # write in phase 2 for RDV, CPY, RDM - not WRT
        write_target = (self.r['N'][2] and (self.r['N'][3] or self.r['N'][4]))
        click['P1'] = (self.f[2] and not self.tgt()[1] and write_target
                       or (self.f[2] and self.cmp)
                       # or (self.f[3] and not self.cmp)  # this will pick up the program counter
                       )
        click['M1'] = self.f[2] and not self.tgt()[3] and write_target
        click['A'] = self.f[2] and not self.tgt()[6] and write_target
        # write to R for n1 (add) or n2 (cpy) and target is R
        click['R'] = self.f[2] and ((not self.tgt()[7] and write_target) or self.r['N'][1])
        click['TP1'] = False
        return click

    def reg_write(self):
        """ Clock has had rising edge, write registers
        """
        bus_value = copy.copy(self.bus_to_registers())
        click = self.clicks()
        if click['N']:
            self.r['N'] = copy.copy(self.bus_from_device)
        if click['T']:
            self.r['T'] = copy.copy(self.bus_from_device)
        for key in ['P1', 'M1', 'W', 'A', 'R']:
            if click[key]:
                self.r[key] = bus_value


class MyComputerInterface:
    """ Controls the device that sends and receives data from the computer. And acts as the
    clock and memory for that computer.

    device has 16 bit address on 0, 1, 2, 3
    reads 8 bits in on 4, 5
    writes 8 bits out on 6, 7

    """
    MEMORY_DELAY = 0.01

    def __init__(self, program, expected_machine_state: ExpectedMachineState, verbose=True):
        # self.device = pyk8055.device()
        self.device = DummyDevice(expected_machine_state)
        self.readable_memory = program
        self.memory = [translate_to_machine_instruction(line) for line in program]
        self.expected_machine_state = expected_machine_state
        self.verbose = verbose
        self.clock = 0
        self.phase = 1
        self.saved_address = -2
        self.calculated_address = -2
        self.prior_address = 0
        self.custom_command = None

    def log(self, message):
        if self.verbose:
            print(message)

    def sleep(self):
        time.sleep(self.MEMORY_DELAY)

    def set_mem_bus_addr(self, value):
        vals = device_bus_addr[value]
        for i, c in enumerate(vals):
            if c == '0':
                self.device.digital_off(2 + i)
            else:
                self.device.digital_on(2 + i)

    def read_from_bus(self, address):
        """ Read from bus and return value
        """
        self.set_mem_bus_addr(address)
        self.sleep()
        vals = [str(self.device.digital_in(2 + i)) for i in range(4)]
        # self.log(f'reading {"".join(vals)} from address = {address}')
        return (8 * int(vals[0])
                + 4 * int(vals[1])
                + 2 * int(vals[2])
                + 1 * int(vals[3]))

    def write_to_bus(self, address, vals):
        # self.log(f'writing {"".join(vals)} to address = {address}')
        self.set_mem_bus_addr(address)
        self.sleep()
        for i, c in enumerate(vals):
            if c == '0':
                self.device.digital_off(5 + i)
            else:
                self.device.digital_on(5 + i)

    def _ind_and_offset(self, address):
        """
        Index and offset in memory array

        """
        ind = address // 2
        if (address % 2) == 1:
            offset = 9
        else:
            offset = 0
        return ind, offset

    def full_cycle(self, n_cycles=1):
        for i in range(n_cycles):
            self.read_write_cycle()  # read instruction
            self.toggle_clock()  # click 1

            self.toggle_clock()  # to phase 2
            self.read_write_cycle()  # read immediate or *M
            self.toggle_clock()  # click 2

            self.toggle_clock()  # to phase 3
            self.read_write_cycle()  # write to *M if required
            self.toggle_clock()  # click 3

            self.toggle_clock()  # to phase 4
            self.toggle_clock()  # click 4
            self.toggle_clock()  # to phase 0

    def read_write_cycle(self):
        # Get address from device
        address = 0
        mult = 16
        for i in range(2):
            self.set_mem_bus_addr(i)
            address = address + mult * self.read_from_bus(i)
            mult = mult // 16

        read_address = address
        # Check if program counter is not incrementing - for now
        if self.phase == 1:
            if read_address == self.prior_address:
                self.calculated_address += 2
                address = self.calculated_address
                self.log(f'Looks like address is not incrementing, manually setting to {address}')
            else:
                self.calculated_address = address
                self.log(f'Looks like address has actually been set to {address}')
        elif self.phase == 2 and (read_address == self.prior_address):
            address = self.calculated_address + 1
            self.log(f'Looks like address is not incrementing, manually setting to {address}')

        if self.phase == 1:
            self.prior_address = read_address

        # save phase 2 address in case needed for write in phase 3
        # hack while I think of how to pass the address and value back to the device on the same cycle
        if self.phase == 2:
            self.saved_address = address

        # If we are in phase 3, check if write is required
        if self.phase == 3:
            write = self.device.digital_in(1)
            if write:
                # Do something if write is True
                mult = 16
                value = 0
                for i in [4, 5]:
                    self.set_mem_bus_addr(i)
                    value = value + mult * self.read_from_bus(i)
                    mult = mult // 16
                self.log(f'writing {value} to {self.saved_address}')
                ind, offset = self._ind_and_offset(self.saved_address)
                parts = self.readable_memory[ind].split()
                parts = parts + ['0'] * (2-len(parts))
                if offset == 0:
                    self.memory[ind] = bin_fixed_width(value) + self.memory[ind][8:]
                    self.readable_memory[ind] = str(value) + ' ' + parts[1]
                else:
                    self.memory[ind] = self.memory[ind][:9] + bin_fixed_width(value)
                    self.readable_memory[ind] = parts[0] + ' ' + str(value)
            else:
                return

        # Read contents of location and send to device
        ind, offset = self._ind_and_offset(address)
        if ind >= len(self.memory):
            self.log(f'address {address} is out of range,  returning 0')
            address = 0
            ind = 0
            offset = 0
        if self.custom_command:
            value = self.custom_command
            self.log(f'Running custom command: {value}')
        else:
            value = self.memory[ind]
            self.log(f'contents at {address}: {self.memory[ind]} / {self.readable_memory[ind]}')
        self.write_to_bus(6, value[offset:(offset + 4)])
        self.write_to_bus(7, value[(offset + 4):(offset + 8)])

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
