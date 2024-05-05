from connection import translate_to_bin


def get_add_numbers_prog():
    code = '''\
RDV  A  7
RDV  B  5
ADV  A  7
ADV  B  255
JZ   B  12
RDD  P1 4
ADD  R
NOP
75
10000
12   15
'''
    listing = [translate_to_bin(line) for line in code.splitlines()]
    return listing