from collections import defaultdict

from utils import translate_to_machine_instruction


def compile(program):
    variables = {}  # name->address
    labels = {}     # name->address
    macros = defaultdict(list)
    # Extract variables and labels
    address = 0
    asm = []
    readable = []
    insert_rows = defaultdict(list)
    # Find Macros
    removed = []
    i = 0
    while i < len(program):
        full_line = program[i]
        if full_line.startswith('DEFINE'):
            is_open = True
            name = None
            while is_open:
                full_line = program[i]
                if '{' in full_line:
                    name = full_line.split()[1]
                    full_line = full_line.split('{')[1]
                elif '}' in full_line:
                    full_line = full_line.split('}')[0]
                    is_open = False
                if name is None:
                    raise Exception('Macro does not appear to have a name')
                if len(full_line.strip()) > 0:
                    macros[name].append(full_line)
                i += 1
        else:
            removed.append(full_line)
            i+=1
    program = removed
    expanded = []
    for full_line in program:
        is_macro = False
        for macro, lines in macros.items():
            if macro in full_line.split():
                expanded += lines
                is_macro = True
        if not is_macro:
            expanded.append(full_line)
    program = expanded

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
            labels[line[1:]] = address + 1
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

    # replace variables and labels with their memory values
    for line in asm:
        parts = line.split()
        for name, (address, value) in variables.items():
            if name+'.0' in parts:
                line = line.replace(f'{name}.0', str(address))
            elif name + '.1' in parts:
                address += 1
                line = line.replace(f'{name}.1', str(address))
            elif name in parts:
                line = line.replace(name, str(address))

        for name, address in labels.items():
            if name in parts:
                line = line.replace(name, str(address))
        machine_ready.append(translate_to_machine_instruction(line))

    return machine_ready, readable, insert_rows


if __name__ == '__main__':
    prog_name = 'turing_or.prog'
    with open(f'./progs/{prog_name}') as f:
        program = f.readlines()
    asm = compile(program)
