from unittest import TestCase

from connection import ExpectedMachineState, MyComputerInterface, bin_to_value


class TestMyComputerInterface(TestCase):
    regs = ['A', 'R', 'P1', 'M1']

    def test_rdv(self):
        program = ['RDV A 40', '0']
        state = ExpectedMachineState()
        interface = MyComputerInterface(program, state, verbose=False)
        interface.full_cycle()
        a = bin_to_value(state.r['A'])
        self.assertEqual(a, 40)

    def test_rdv_to_any(self):
        for r in self.regs:
            program = [f'RDV {r} 42', '0']
            state = ExpectedMachineState()
            interface = MyComputerInterface(program, state, verbose=False)
            interface.full_cycle()
            val = bin_to_value(state.r[r])
            self.assertEqual(val, 42)

    def test_adv(self):
        program = ['RDV A 17', 'ADV A 14', '0']
        state = ExpectedMachineState()
        interface = MyComputerInterface(program, state, verbose=False)
        interface.full_cycle(2)
        r = bin_to_value(state.r['R'])
        self.assertEqual(r, 31)

    def test_adv_to_any(self):
        for r in ['A', 'P1', 'M1']:
            program = [f'RDV {r} 2', f'ADV {r} 14', '0']
            state = ExpectedMachineState()
            interface = MyComputerInterface(program, state, verbose=False)
            interface.full_cycle(2)
            r = bin_to_value(state.r['R'])
            self.assertEqual(r, 16)

    def test_wrt_any(self):
        for r in ['A', 'R', 'P1']:
            program = [f'RDV M1 6', f'RDV {r} 4', f'WRT {r}', '0']
            state = ExpectedMachineState()
            interface = MyComputerInterface(program, state, verbose=False)
            self.assertEqual(interface.memory[3], '00000000 00000000')
            interface.full_cycle(3)
            self.assertEqual(interface.memory[3], '00000100 00000000')

    def test_adv_neg(self):
        program = ['RDV A 17', 'ADV A -1', '0']
        state = ExpectedMachineState()
        interface = MyComputerInterface(program, state, verbose=False)
        interface.full_cycle(2)
        r = bin_to_value(state.r['R'])
        self.assertEqual(r, 16)

    def test_adv_carry(self):
        program = ['RDV A 130', 'ADV A 130', '0']
        state = ExpectedMachineState()
        interface = MyComputerInterface(program, state, verbose=False)
        interface.full_cycle(2)
        r = bin_to_value(state.r['R'])
        self.assertEqual(r, 4)

    def test_jmz(self):
        program = ['RDV A 17', 'JMZ A 6', 'RDV A 0', 'JMZ A 10', '0', '0']
        state = ExpectedMachineState()
        interface = MyComputerInterface(program, state, verbose=False)
        interface.full_cycle(2)
        p1 = bin_to_value(state.r['P1'])
        self.assertEqual(p1, 0)

        interface.full_cycle(2)
        p1 = bin_to_value(state.r['P1'])
        self.assertEqual(p1, 10)

    def test_set_p1(self):
        program = ['RDV A 1', 'RDV P1 6', 'RDV A 2', 'RDV A 3']
        state = ExpectedMachineState()
        interface = MyComputerInterface(program, state, verbose=False)
        interface.full_cycle(3)
        p1 = bin_to_value(state.r['P1'])
        a = bin_to_value(state.r['A'])
        self.assertEqual(p1, 6)
        self.assertEqual(a, 3)



