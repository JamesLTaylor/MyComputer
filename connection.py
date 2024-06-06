import copy

import pyk8055
import time

from simulator import ExpectedMachineState, DummyDevice
from utils import translate_to_machine_instruction, device_bus_addr, bin_fixed_width


class MyComputerInterface:
    """ Controls the device that sends and receives data from the computer. And acts as the
    clock and memory for that computer.

    device has 16 bit address on 0, 1, 2, 3
    reads 8 bits in on 4, 5
    writes 8 bits out on 6, 7

    """
    MEMORY_DELAY = 0.25

    def __init__(self, program, expected_machine_state: ExpectedMachineState, verbose=True, real_device=False):
        if real_device:
            self.real_device = pyk8055.device()
        else:
            self.real_device = None
        self.device = DummyDevice(expected_machine_state)
        self.readable_memory = program
        self.memory = [translate_to_machine_instruction(line) for line in program]
        self.expected_machine_state = expected_machine_state
        self.verbose = verbose
        self.clock = 0
        self.phase = 1
        self.current_address = -1
        self.custom_command = None
        self.set_p1()

    def enable_real(self):
        self.real_device = pyk8055.device()

    def log(self, message):
        if self.verbose:
            print(message)

    def sleep(self):
        if self.real_device:
            time.sleep(self.MEMORY_DELAY)
        elif self.verbose:
            time.sleep(self.MEMORY_DELAY/10)

    def set_mem_bus_addr(self, value):
        vals = device_bus_addr[value]
        for i, c in enumerate(vals):
            if c == '0':
                self.digital_off(2 + i)
            else:
                self.digital_on(2 + i)

    def read_from_bus(self, address):
        """ Read from bus and return value
        """
        self.set_mem_bus_addr(address)
        self.sleep()
        vals = [str(self.digital_in(1 + i)) for i in range(4)]
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
                self.digital_off(5 + i)
            else:
                self.digital_on(5 + i)

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

    def set_p1(self):
        self.custom_command = translate_to_machine_instruction('RDV P1 1')
        self.full_cycle()
        self.custom_command = None

    def get8bit(self, addr1, addr2):
        value = 0
        mult = 16
        for i in [addr1, addr2]:
            value = value + mult * self.read_from_bus(i)
            mult = mult // 16
        return value

    def run_custom(self):
        if self.phase == 1:
            offset = 0
        else:
            offset = 9
            if self.custom_command[:5] == '00110':  # Special treatment for custom RDM command
                address = self.get8bit(0, 1)
                self.memory[address // 2]
        value = self.custom_command
        self.log(f'Running custom command: {value}')
        self.write_to_bus(7, value[(offset + 4):(offset + 8)])
        self.write_to_bus(6, value[offset:(offset + 4)])

    def read_write_cycle(self):
        if self.custom_command:
            self.run_custom()
            return
        # Get address from device
        if self.phase in [1, 2]:
            address = self.get8bit(0, 1)
            self.current_address = address
            # Read contents of location and send to device
            if address >= 2 * len(self.memory):
                self.log(f'address {address} is out of range,  returning 0')
                address = 0
            ind, offset = self._ind_and_offset(address)
            value = self.memory[ind]
            self.log(f'contents at {address}: {self.memory[ind]} / {self.readable_memory[ind]}')
            self.write_to_bus(7, value[(offset + 4):(offset + 8)])
            self.write_to_bus(6, value[offset:(offset + 4)])
        # If we are in phase 3, check if write is required
        elif self.phase == 3 and self.digital_in(5):
            # Do something if write is True
            address = self.get8bit(4, 5)
            value = self.get8bit(0, 1)
            self.log(f'writing {value} to {address}')
            ind, offset = self._ind_and_offset(address)
            parts = self.readable_memory[ind].split()
            parts = parts + ['0'] * (2-len(parts))
            if offset == 0:
                self.memory[ind] = bin_fixed_width(value) + self.memory[ind][8:]
                self.readable_memory[ind] = str(value) + ' ' + parts[1]
            else:
                self.memory[ind] = self.memory[ind][:9] + bin_fixed_width(value)
                self.readable_memory[ind] = parts[0] + ' ' + str(value)

    def digital_on(self, pos):
        self.device.digital_on(pos)
        if self.real_device:
            self.real_device.digital_on(pos)

    def digital_off(self, pos):
        self.device.digital_off(pos)
        if self.real_device:
            self.real_device.digital_off(pos)

    def digital_in(self, pos):
        if self.real_device:
            val = self.real_device.digital_in(pos)
            val = 0 if val == 1 else 1
            return val
        else:
            return self.device.digital_in(pos)

    def toggle_clock(self):
        # Get address from computer via device
        if self.real_device:
            time.sleep(0.1)
        if self.clock == 0:
            self.clock = 1
            self.digital_on(1)
        else:
            self.clock = 0
            self.digital_off(1)
            self.phase += 1
            if self.phase == 5:
                self.phase = 1
