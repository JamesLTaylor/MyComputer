from connection import MyComputerInterface, ExpectedMachineState, translate_to_machine_instruction
from utils import bin_to_value


def test_rdv_to_any():
    for test_value in ['165', '90']:
        for r in ['A', 'R']:
            program = [f'RDV M1 6', f'RDV {r} {test_value}', f'WRT {r}', '0']
            state = ExpectedMachineState()
            interface = MyComputerInterface(program, state, verbose=True, real_device=True)
            interface.full_cycle(3)
            val = bin_to_value(interface.memory[3][:8])
            print(f'\nRead/write for {r}: Asserting {val} = {test_value}\n')
            assert str(val) == test_value


test_rdv_to_any()