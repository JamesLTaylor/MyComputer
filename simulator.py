import copy

from utils import device_bus_addr_inv, bin_to_value, bin_fixed_width, neg


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
        self.r = {'N': [0 for _ in range(8)],
                  'T': [0 for _ in range(8)],
                  'P1': [0 for _ in range(8)],
                  'M1': [0 for _ in range(8)],
                  'A': [0 for _ in range(8)],
                  'R': [0 for _ in range(8)],
                  'W': [0 for _ in range(8)],
                  'TP1': [0 for _ in range(8)],    # temp result of P1 + 2, to be copied to P1 in phase 3
                  'TM1': [0 for _ in range(8)],    # temp copy of bus_from_regs in phase 1, which is M1 in a write
                  'P0': [0 for _ in range(8)],     # high bits of instruction pointer, can be written to but not read
                  'M0': [0 for _ in range(8)],     # high bits of data pointer, can be written to but not read
                  }
        self.jk = {'Carry': 0,
                   'Cmp': 0,
                   'NegCarry': 0}
        self.data = {'Carry': 0,  # D flip flops that copy from the JK flipflops in phase 3
                     'Cmp': 0,
                     'NegCarry': 0}
        self.f = [1, 0, 0, 0]
        self.nf = [0, 1, 1, 1]
        self.clock = 0

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

    def tgt(self):
        """
        each bit should be implemented as tgt_t and not n3 or src_n and n3

        """
        if self.r['N'][3]:
            return self._src_n()
        else:
            return self._tgt_t()

    def instruction(self):
        """ n0, n1, n2 are coded into instructions
        000 = NOP
        001 = CPY etc
        010 = ADV
        100 = JMZ
        110 = NEG
        """
        val = [0, 0, 0, 0, 0, 0, 0, 0]
        ind = 4 * self.r['N'][0] + 2 * self.r['N'][1] + self.r['N'][2]
        val[ind] = 1
        return val

    def write(self):
        # This will write on WRT and RDM, but that is OK since RDM will rewrite the same value.
        return self.instruction()[1] and not self.r['N'][4] and not self.r['N'][3]

    def get(self, line):
        if line == 5:
            return self.write()
        if self.bus_addr() == 0:
            return self.bus_from_registers()[line - 1]
        elif self.bus_addr() == 1:
            val = self.bus_from_registers()[line + 3]
            if line == 4:
                val = int(self.nf[0] and bool(val))
            return val
        if self.bus_addr() == 4:
            return self.r['TM1'][line - 1]
        elif self.bus_addr() == 5:
            return self.r['TM1'][line + 3]
        return 0

    def flags(self):
        """
        Flag to disable data from registers to bus.
        In phase 2 always expose SRC unless RDV or RDM

        """
        flag = {}
        n_read_source = self.nf[2] or self.r['N'][3] # not read source

        # f0 or (f1 and n4) or (read_source and src[1])
        # negated: f0' and (f1 nand n4) and (n_read_source or s1)
        flag['P1'] = (self.nf[0]) and (self.nf[1] or not (self.r['N'][4])) and (n_read_source or self.src()[1])
        # (f1 and not n4) or (f2 and src[3])
        flag['M1'] = (self.nf[1] or self.r['N'][4]) and (n_read_source or self.src()[3])

        # f2 and src[6]
        flag['A'] = n_read_source or self.src()[6]
        # f2 and (n2 and n3)
        # negated: f2' or (n2 nand n3)
        flag['W'] = self.nf[2] or (not (self.instruction()[1] and self.r['N'][3]))
        # f2 and src[7]
        flag['R'] = n_read_source or self.src()[7]
        return flag

    def bus_from_registers(self):
        """ Only some registers can be read from

        """
        flag = self.flags()
        for key in ['P1', 'M1', 'W', 'A', 'R']:
            if not flag[key]:
                return self.r[key]

    def cmp(self):
        """ Wire from compare. In phase 2 checks if bus_from_regs is zero - if it is then T will be put on
        bus_to_regs and TP1 will not be written in phase 3.

        Only defined in phase 2 for instruction 4.

        One means the test value is zero and the instruction 4 is running.
        """
        a = bin_to_value(self.bus_from_registers())
        return a == 0  # On device this is: not (v0+v1+v2+...)

    def carry(self):
        """ Wire from add
        """
        if self.f[2] and self.instruction()[2]:  # ADV
            a = bin_to_value(self.bus_from_registers())
            b = bin_to_value(self.r['T'])
            res = a + b + self.data['Carry']
            return res > 255

    def neg_carry(self):
        if self.f[2] and self.instruction()[6]:  # NEG
            result, carry = neg(self.bus_from_registers(), self.data['NegCarry'] and self.r['T'][7])
            return carry

    def bus_to_registers(self):
        """
        logic of computer
        """
        if self.f[0]:
            return self.bus_from_device
        if self.f[1]:
            return self.bus_from_device
        if self.f[2] and self.instruction()[1]:  # CPY
            return self.bus_from_registers()
        if self.f[2] and self.instruction()[2]:  # ADV
            a = bin_to_value(self.bus_from_registers())
            b = bin_to_value(self.r['T'])
            res = a + b + self.data['Carry']
            if res > 255:
                res = res - 256
            return [int(i) for i in bin_fixed_width(res)]
        if self.f[2] and self.instruction()[4]:  # JMZ
            a = bin_to_value(self.bus_from_registers())
            if a == 0:
                return copy.copy(self.r['T'])
            else:
                return None
        if self.f[2] and self.instruction()[6]:  # NEG
            result, carry = neg(self.bus_from_registers(), self.data['NegCarry'] and self.r['T'][7])
            return result
        if self.f[3]:
            return copy.copy(self.r['TP1'])

    def clicks(self):
        click = {}
        click['N'] = self.f[0]
        click['T'] = self.f[1]
        click['W'] = self.f[1]
        # write in phase 2 for RDV, CPY, RDM - not WRT
        write_target = (self.instruction()[1] and (self.r['N'][3] or self.r['N'][4]))
        p1_wrt_tmp = not self.tgt()[1] and write_target
        click['P1'] = (self.f[2] and p1_wrt_tmp
                       or (self.f[2] and self.instruction()[4] and self.cmp())
                       or (self.f[3] and not (self.instruction()[4] and self.jk['Cmp']) and not p1_wrt_tmp)  # this will pick up the program counter
                       )
        click['M1'] = self.f[2] and not self.tgt()[3] and write_target
        click['A'] = self.f[2] and not self.tgt()[6] and write_target
        click['M0'] = self.f[2] and not self.tgt()[2] and write_target
        click['P0'] = self.f[2] and not self.tgt()[0] and write_target
        # write to R for n1 (add) or n2 (cpy) and target is R
        click['R'] = ((self.f[2] and (not self.tgt()[7] and write_target))
                      or (self.f[2] and self.r['N'][1])  # NB. still use n1 here instead of instructions, assuming all
                                                         # n1=1 instructions must write to R
                      )
        click['TP1'] = self.f[0]
        click['TM1'] = self.f[1]  # Take copy of Mem pointer in phase 2 for use in writing.
        click['Carry'] = self.f[2] and self.instruction()[2]
        click['NegCarry'] = self.f[2] and self.instruction()[6]
        click['Data'] = self.f[3]
        click['Cmp'] = self.f[2] and self.instruction()[4]
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
        if click['TP1']:
            v = bin_to_value(self.bus_from_registers())
            res = v + 2
            if res > 255:
                res = res - 256
            self.r['TP1'] = [int(i) for i in bin_fixed_width(res)]
        if click['TM1']:
            self.r['TM1'] = copy.copy(self.bus_from_registers())
        if click['Carry']:
            self.jk['Carry'] = self.carry()  # PROBLEM - carry() uses self.jk['Carry']
        if click['NegCarry']:
            self.jk['NegCarry'] = self.neg_carry()
        if click['Cmp']:
            self.jk['Cmp'] = self.cmp()
        if click['Data']:
            self.data['Carry'] = self.jk['Carry']
            self.data['NegCarry'] = self.jk['NegCarry']
        for key in ['P1', 'M1', 'W', 'A', 'R']:
            if click[key]:
                self.r[key] = bus_value
