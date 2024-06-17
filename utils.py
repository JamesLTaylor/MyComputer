instructions = {'NOP': '00000',
                'RDV': '00111',
                'CPY': '00101',
                'WRT': '00100',
                'RDM': '00110',
                'ADV': '01001',
                'ADM': '01000',
                'JMZ': '10001',
                'NEG': '11001'}
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

device_bus_addr = {0: '111',  # P1 first 4
                   1: '011',
                   2: '010',  # P2 first 4 - not used yet
                   3: '001',
                   4: '110',  # general read from computer first 4
                   5: '010',
                   6: '100',  # output
                   7: '000'}
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


def neg(bits, carry):
    """

    :param bits:
    :param carry:
    :return: result (8bits) and carry (1bit). All inputs other than zero produce a carry out.
    """
    result = [0] * len(bits)
    for i in range(len(bits)-1, -1, -1):
        result[i] = int(bits[i]) ^ carry
        carry = carry or int(bits[i])
    return result, carry


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

