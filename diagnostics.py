from connection import MyComputerInterface, ExpectedMachineState, translate_to_machine_instruction
from utils import bin_to_value

'''
Everything to test:

CPY - from (A, R, P1, M1) to (A, R, P1, M1) AND (M0, P0)
RDV - to (A, R, P1, M1, M0, P0)
WRT - from (A, R, P1, M1)
RDM - to (A, R, P1, M1, M0, P0)
ADV - source is (A, P1, M1)
ADV - using prior carry
ADV - ignoring prior carry
NEG - source is (A, P1, M1)
NEG - using prior carry
NEG - ignoring prior carry
JMZ - source is (A, R, P1, M1) zero and non zero
'''


def test_rdv_to_any():
    # Make sure that page counters are both set to zero
    program = [f'RDV M0 0', 'RDV P0 0']
    state = ExpectedMachineState()
    interface = MyComputerInterface(program, state, verbose=True, real_device=True)
    interface.full_cycle(2)

    for test_value in ['165', '90']:
        for r in ['A', 'R']:
            program = [f'RDV M1 6', f'RDV {r} {test_value}', f'WRT {r}', '0']
            state = ExpectedMachineState()
            interface = MyComputerInterface(program, state, verbose=True, real_device=True)
            interface.full_cycle(3)
            val = bin_to_value(interface.memory[3][:8])
            print(f'\nRead/write for {r}: Asserting {val} = {test_value}\n')
            assert str(val) == test_value


def test_rdv_p0():
    program = ['::PAGE0', 'RDV M0 PAGE0', 'RDV P0 PAGE1', '::PAGE1', 'NOP', 'RDV A 101', 'RDV M1 8', 'WRT A']
    state = ExpectedMachineState()
    interface = MyComputerInterface(program, state, verbose=True, real_device=True)
    interface.full_cycle(5)
    val = bin_to_value(interface.memory[4][:8])
    print(f'\nAsserting RDV to P0: {val}\n')
    assert val == 101


def test_cpy_p0():
    program = ['::PAGE0', 'RDV A PAGE1', 'CPY A P0', '::PAGE1', 'NOP', 'NOP', 'RDV A 101', 'RDV M1 8', 'WRT A']
    state = ExpectedMachineState()
    interface = MyComputerInterface(program, state, verbose=True, real_device=True)
    interface.full_cycle(5)
    val = bin_to_value(interface.memory[4][:8])
    print(f'\nAsserting CPY to P0: {val}\n')
    assert val == 101


def test_rdv_m0():
    program = ['::PAGE0', 'RDV M0 PAGE1', 'RDV M1 result', 'RDV A 165', 'WRT A', '::PAGE1', '*result = 0']
    state = ExpectedMachineState()
    interface = MyComputerInterface(program, state, verbose=True, real_device=True)
    interface.full_cycle(4)
    val = bin_to_value(interface.memory[128][:8])
    print(f'\nAsserting RDV to M0: {val}\n')
    assert val == 165


def test_cpy_m0():
    program = ['::PAGE0', 'RDV A PAGE1', 'CPY A M0', 'RDV M1 result', 'RDV A 165', 'WRT A', '::PAGE1', '*result = 0']
    state = ExpectedMachineState()
    interface = MyComputerInterface(program, state, verbose=True, real_device=True)
    interface.full_cycle(5)
    val = bin_to_value(interface.memory[128][:8])
    print(f'\nAsserting CPY to M0: {val}\n')
    assert val == 165




# test_rdv_to_any()
test_cpy_p0()
test_rdv_m0()
test_cpy_m0()
test_rdv_p0()