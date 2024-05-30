from connection import MyComputerInterface, ExpectedMachineState, bin_to_value, translate_to_machine_instruction


def test_rdv_to_any():
    for test_value in ['165', '90']:
        for r in ['R']:
            program = [f'RDV M1 6', f'RDV {r} {test_value}', f'WRT {r}', '0']
            state = ExpectedMachineState()
            interface = MyComputerInterface(program, state, verbose=True, real_device=True)

            interface.custom_command = translate_to_machine_instruction('RDV P1 2')
            interface.full_cycle()
            interface.custom_command = translate_to_machine_instruction('RDV P1 0')
            interface.full_cycle()
            interface.custom_command = None

            interface.full_cycle(3)
            val = bin_to_value(interface.memory[3][:8])
            print(f'\nAsserting {val} = {test_value}\n')
            assert str(val) == test_value


test_rdv_to_any()