from connection import MyComputerInterface, ExpectedMachineState, translate_to_machine_instruction
from utils import bin_to_value

'''
Everything to test:

CPY - from (A, R, P1, M1) to (A, R, P1, M1) AND (M0, P0)
RDV - to (A, R, P1, M1, M0, P0)
WRT - from (A, R, P1, M1)
RDM - to (A, R, P1, M1, M0, P0)
ADV - source is (A, P1, M1)
ADM - source is (A, P1, M1)
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
    interface = MyComputerInterface(program, state, **kwargs)
    interface.full_cycle(2)

    for test_value in ['165', '90']:
        for r in ['A', 'R']:
            program = [f'RDV M1 6', f'RDV {r} {test_value}', f'WRT {r}', '0']
            state = ExpectedMachineState()
            interface = MyComputerInterface(program, state, **kwargs)
            interface.full_cycle(3)
            val = bin_to_value(interface.memory[3][:8])
            print(f'\nRead/write for {r}: Asserting {val} = {test_value}\n')
            assert str(val) == test_value


def test_rdv_p0():
    program = ['::PAGE0', 'RDV M0 PAGE0', 'RDV P0 PAGE1', '::PAGE1', 'NOP', 'NOP', 'RDV A 101', 'RDV M1 8', 'WRT A']
    state = ExpectedMachineState()
    interface = MyComputerInterface(program, state, **kwargs)
    interface.full_cycle(5)
    val = bin_to_value(interface.memory[4][:8])
    print(f'\nAsserting RDV to P0: {val}\n')
    assert val == 101


def test_cpy_p0():
    program = ['::PAGE0', 'RDV A PAGE1', 'CPY A P0', '::PAGE1', 'NOP', 'NOP', 'RDV A 101', 'RDV M1 8', 'WRT A']
    state = ExpectedMachineState()
    interface = MyComputerInterface(program, state, **kwargs)
    interface.full_cycle(5)
    val = bin_to_value(interface.memory[4][:8])
    print(f'\nAsserting CPY to P0: {val}\n')
    assert val == 101


def test_rdv_m0():
    program = ['::PAGE0', 'RDV M0 PAGE1', 'RDV M1 result', 'RDV A 165', 'WRT A', '::PAGE1', '*result = 0']
    state = ExpectedMachineState()
    interface = MyComputerInterface(program, state, **kwargs)
    interface.full_cycle(4)
    val = bin_to_value(interface.memory[128][:8])
    print(f'\nAsserting RDV to M0: {val}\n')
    assert val == 165


def test_cpy_m0():
    program = ['::PAGE0', 'RDV A PAGE1', 'CPY A M0', 'RDV M1 result', 'RDV A 165', 'WRT A', '::PAGE1', '*result = 0']
    state = ExpectedMachineState()
    interface = MyComputerInterface(program, state, **kwargs)
    interface.full_cycle(5)
    val = bin_to_value(interface.memory[128][:8])
    print(f'\nAsserting CPY to M0: {val}\n')
    assert val == 165


def test_wrt():
    program = ['*a=0', '*r=0', '*m1=0', '*p1=0',
               'RDV M1 a', 'RDV A 125', 'WRT A',
               'RDV M1 r', 'RDV R 115', 'WRT R',
               'RDV M1 m1', 'WRT M1',
               'RDV M1 p1', 'WRT P1'
               ]
    state = ExpectedMachineState()
    interface = MyComputerInterface(program, state, **kwargs)
    interface.full_cycle(10)
    a = bin_to_value(interface.memory[10][:8])
    r = bin_to_value(interface.memory[11][:8])
    m1 = bin_to_value(interface.memory[12][:8])
    p1 = bin_to_value(interface.memory[13][:8])
    print(f'\nAsserting WRT\n')
    assert a == 125
    assert r == 115
    assert m1 == 24
    assert p1 == 19


def test_adv():
    """
    ADV - source is (A, P1, M1)
    ADM - source is (A, P1, M1)
    ADV - using prior carry
    ADV - ignoring prior carry
    :return:
    """
    program = ['*r = 0', '*rc=0', '*r2=0', '*rnc=0', 'RDV A 100',
               'ADV A 200', 'RDV M1 r', 'WRT R',  # add with carry
               'ADV A 1', 'RDV M1 rc', 'WRT R',  # use carry
               'ADV A 200', 'RDV M1 r2', 'WRT R', # set carry again
               'ADV A 0', 'ADV A 1', 'RDV M1 rnc', 'WRT R',  # reset carry before add
               ]
    state = ExpectedMachineState()
    interface = MyComputerInterface(program, state, **kwargs)
    interface.full_cycle(14)
    r = bin_to_value(interface.memory[14][:8])
    rc = bin_to_value(interface.memory[15][:8])
    r2 = bin_to_value(interface.memory[16][:8])
    rnc = bin_to_value(interface.memory[17][:8])
    print(f'\nAsserting WRT\n')
    assert r == 44
    assert rc == 102
    assert r2 == 44
    assert rnc == 101


def test_adm_16bit():
    program = ['*r=0', '*a = 10000', '*b = 2152',
               'RDV M1 a.0', 'RDM A', 'RDV M1 b.0', 'ADM A', 'RDV M1 r.0', 'WRT R',
               'RDV M1 a.1', 'RDM A', 'RDV M1 b.1', 'ADM A', 'RDV M1 r.1', 'WRT R',
               ]
    state = ExpectedMachineState()
    interface = MyComputerInterface(program, state, **kwargs)
    interface.full_cycle(12)
    r0 = bin_to_value(interface.memory[12][:8])
    r1 = bin_to_value(interface.memory[12][9:])
    print(f'\nAsserting ADM\n')
    assert 256*r1 + r0 == 12152


def test_neg_16bit():
    program = ['*a = 12500', '*r = 0', '*carry0 = 0', '*carry1 = 0',
               'RDV A 0', 'NEG A 0',  'RDV A 0', 'NEG A 1', 'CPY R A', 'NEG A 0', 'RDV M1 carry1', 'WRT R',  # extract carry bit
               'RDV A 1', 'NEG A 0',  'RDV A 0', 'NEG A 1', 'CPY R A', 'NEG A 0', 'RDV M1 carry1', 'WRT R',
               'RDV M1 a.0', 'RDM A', 'NEG A 0', 'RDV M1 r.0', 'WRT R',
               'RDV M1 a.1', 'RDM A', 'NEG A 1', 'RDV M1 r.1', 'WRT R',
               ]
    state = ExpectedMachineState()
    interface = MyComputerInterface(program, state, **kwargs)
    interface.full_cycle(26)
    r0 = bin_to_value(interface.memory[27][:8])
    r1 = bin_to_value(interface.memory[27][9:])
    carry0 = bin_to_value(interface.memory[28][:8])
    carry1 = bin_to_value(interface.memory[29][:8])
    print(f'\nAsserting NEG {256*r1 + r0} == {2**16 - 12500} \n')
    assert 256*r1 + r0 == 2**16 - 12500
    assert carry0 == 0
    assert carry1 == 1


def test_jmz():
    for value in [0, 1]:
        for reg in ['A', 'R']:
            program = ['*result=100', 'RDV M1 result', f'RDV {reg} {value}', f'JMZ {reg} ZERO', 'RDV P1 NOTZERO',
                       ':ZERO', 'RDV A 11', 'WRT A', 'RDV P1 END',
                       ':NOTZERO', 'RDV A 22', 'WRT A', 'RDV P1 END',
                       ':END', 'HLT']
            state = ExpectedMachineState()
            interface = MyComputerInterface(program, state, **kwargs)
            interface.full_cycle(7)
            r0 = bin_to_value(interface.memory[11][:8])
            test = 22 if value else 11
            print(f'\nAsserting JMZ {reg} {value} is {"not" if value else ""} zero\n')
            assert test == r0


kwargs = dict(verbose=True, real_device=True)
# kwargs = dict(verbose=False, real_device=False)
test_rdv_to_any()
test_cpy_p0()
test_rdv_m0()
test_cpy_m0()
test_rdv_p0()
test_wrt()
test_adv()
test_adm_16bit()
test_neg_16bit()
test_jmz()
