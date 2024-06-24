from collections import defaultdict

from utils import translate_to_machine_instruction


def expand_macros(program):
    """
    Global search for all macros and replace them
    """
    macros = defaultdict(list)
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
            i += 1
    expanded = []
    for full_line in removed:
        is_macro = False
        for macro, lines in macros.items():
            if macro in full_line.split():
                expanded += lines
                is_macro = True
        if not is_macro:
            expanded.append(full_line)
    return expanded


def allocate_data_mem(new_var, variables, address, asm, readable, fill_page=True):
    """

    :param new_var:
    :param variables:
    :param address:
    :param asm:
    :param readable:
    :param fill_page: For all but the last page, the memory should be filled with zeros
    :return:
    """
    var_addresses = {}
    for name, (_, value) in variables.items():
        if name not in new_var:
            continue
        var_addresses[name] = address
        for i, v in enumerate(value):
            asm.append(str(v))
            readable.append(f'{v} # {name}')
            address += 2
    for name, addr in var_addresses.items():
        value = variables[name][1]
        variables[name] = (addr % 256, value)
    fill_addr = address % 256
    if fill_page:
        while fill_addr < 256:
            fill_addr += 2
            readable.append('')
            asm.append('0')


def extract_names_and_labels(program):
    address = 0
    variables = {}  # name->address
    labels = {}  # name->address
    page = -1
    readable = []
    asm = []
    insert_rows = defaultdict(list)
    new_var = []
    for full_line in program:
        full_line = full_line.strip()
        line = full_line.split('#')[0].strip()
        if len(line) == 0:
            insert_rows[address].append(full_line)
        elif line.startswith('::'):  # a new page
            # New page, allocate variable data and fill up rest of page with zeros
            if page >= 0:
                allocate_data_mem(new_var, variables, address, asm, readable)
            page += 1
            address = 256*page
            labels[line[2:]] = page
            insert_rows[address].append(full_line)
            new_var = []
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
            new_var.append(name.strip())
            insert_rows[address].append(full_line)
        elif line[0] == ':':
            labels[line[1:]] = (address % 256) + 1
            insert_rows[address].append(full_line)
        else:
            readable.append(full_line)
            asm.append(line)
            address += 2
    allocate_data_mem(new_var, variables, address, asm, readable, fill_page=False)
    return variables, labels, asm, readable, insert_rows


def compile(program):
    # Extract variables and labels
    program = expand_macros(program)
    variables, labels, asm, readable, insert_rows = extract_names_and_labels(program)
    machine_ready = []

    # replace variables and labels with their memory values and compile the assembler lines
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
        try:
            machine_ready.append(translate_to_machine_instruction(line))
        except Exception as ex:
            print(f'error on line {line}')
            raise

    return machine_ready, readable, insert_rows


def main():
    prog_name = 'pages2.prog'
    with open(f'./progs/{prog_name}') as f:
        program = f.readlines()
    machine_ready, readable, insert_rows = compile(program)
    for line in readable:
        print(line)


if __name__ == '__main__':
    main()

