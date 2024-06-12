from collections import defaultdict

from utils import translate_to_machine_instruction


def compile(program):
    variables = {}  # name->address
    labels = {}     # name->address
    # Extract variables and labels
    address = 0
    asm = []
    readable = []
    insert_rows = defaultdict(list)
    for full_line in program:
        full_line = full_line.strip()
        line = full_line.split('#')[0].strip()
        if len(line) == 0:
            insert_rows[address].append(full_line)
        elif line[0] == '*':  # a variable declaration
            name, value = line[1:].split('=')
            parts = value.strip().split(',')
            if len(parts) > 1:
                values = [int(s.strip()) for s in value.strip()[1:-1].split(',')]
                length = len(parts)
            else:
                values = [int(parts[0])]
                length = 1
            variables[name.strip()] = (length, values)
            insert_rows[address].append(full_line)
        elif line[0] == ':':
            labels[line[1:]] = address
            insert_rows[address].append(full_line)
        else:
            readable.append(full_line)
            asm.append(line)
            address += 2
    for name, (length, value) in variables.items():
        variables[name] = (address, value)
        address += 2*length
    machine_ready = []
    data_rows = (address//2 - len(asm))
    asm += [0] * data_rows
    readable += [''] * data_rows
    for name, (address, value) in variables.items():
        for i, v in enumerate(value):
            asm[address//2 + i] = str(v)
            readable[address//2 + i] = f'{v} # {name}'

    for line in asm:
        for name, (address, value) in variables.items():
            if name in line:
                line = line.replace(name, str(address))
        for name, address in labels.items():
            if name in line:
                line = line.replace(name, str(address))
        machine_ready.append(translate_to_machine_instruction(line))

    return machine_ready, readable, insert_rows


if __name__ == '__main__':
    prog_name = 'fibonacci.prog'
    with open(f'./progs/{prog_name}') as f:
        program = f.readlines()
    asm = compile(program)
