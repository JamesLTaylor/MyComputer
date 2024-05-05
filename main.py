from connection import translate_to_bin, MyComputerInterface, ExpectedMachineState, bin_to_value
from PyQt5.QtWidgets import QApplication, QWidget, QTabWidget, QGridLayout, QLabel, QPlainTextEdit, QFrame, QScrollArea
from PyQt5.QtCore import Qt, QSize
import traceback

import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout
)


class MainWindow(QWidget):
    def __init__(self, interface, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interface = interface
        self.setWindowTitle('MyComputer')
        self.width = 400
        self.height = 600
        self.setMinimumSize(self.width, self.height)

        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tab_run = RunTab(self, self.interface)
        self.tab_test = TestTab(self, self.interface)
        self.tabs.resize(300, 200)

        # Add tabs
        self.tabs.addTab(self.tab_test, "Test")
        self.tabs.addTab(self.tab_run, "Run")

        layout.addWidget(self.tabs)
        self.setLayout(layout)
        self.show()


class RunTab(QWidget):
    def __init__(self, parent, computer):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)


def txt(vals):
    if vals is None:
        return '#NA'
    if not isinstance(vals, list):
        vals = [vals]
    result = ''.join(str(int(v)) for v in vals)
    if len(vals) == 8:
        result = result + f' ({bin_to_value(vals)})'
    return result


class TestTab(QWidget):
    def __init__(self, parent, computer:MyComputerInterface):
        super(QWidget, self).__init__(parent)
        self.computer = computer
        self.state = self.computer.expected_machine_state
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Memory

        rows = []
        for i, (m, rm) in enumerate(zip(self.computer.memory, self.computer.readable_memory)):
            rows.append(f'{i*2:<5} {m:<20}  {rm}')
        self.mem = QPlainTextEdit('\n'.join(rows), readOnly=True)
        self.mem.setMinimumSize(QSize(600, 600))
        scrollArea = QScrollArea()
        # scrollArea.setBackgroundRole(QPalette.Dark)
        scrollArea.setWidget(self.mem)
        # layout.addWidget(self.mem)
        self.layout.addWidget(scrollArea)

        # # Control
        # sep = QFrame()
        # sep.Shape(QFrame.HLine)
        # sep.setLineWidth(3)
        # layout.addWidget(sep)

        # Command:
        row_clock = QHBoxLayout()
        self.toggle = QPushButton('Toggle Clock')
        self.toggle.clicked.connect(self.toggle_clicked)
        row_clock.addWidget(self.toggle)
        self.rw = QPushButton('Read/Write')
        self.rw.clicked.connect(self.rw_clicked)
        row_clock.addWidget(self.rw)
        self.cycle = QPushButton('1 Cycle')
        self.cycle.clicked.connect(self.cycle_clicked)
        row_clock.addWidget(self.cycle)
        self.auto = QPushButton('AUTO')
        self.auto.clicked.connect(self.auto_clicked)
        row_clock.addWidget(self.auto)
        self.test = QPushButton('Test')
        self.test.clicked.connect(self.update_data)
        row_clock.addWidget(self.test)
        self.layout.addLayout(row_clock)
        row_rw = QHBoxLayout()

        self.layout.addLayout(row_rw)

        # Computer
        row_phase = QHBoxLayout()
        row_phase.addWidget(QLabel('bus from device'))
        self.bus_from_device = QLineEdit('00000000', readOnly=True)
        row_phase.addWidget(self.bus_from_device)
        row_phase.addWidget(QLabel('clock'))
        self.clock = QLineEdit('0', readOnly=True)
        row_phase.addWidget(self.clock)
        row_phase.addWidget(QLabel('phase'))
        self.phase = QLineEdit('0000', readOnly=True)
        row_phase.addWidget(self.phase)
        row_phase.addStretch()
        self.layout.addLayout(row_phase)

        # busses to/from registers
        row_busses = QHBoxLayout()
        row_busses.addWidget(QLabel('bus to regs'))
        self.bus_to_regs = QLineEdit('00000000', readOnly=True)
        self.bus_to_regs.setFixedWidth(160)
        row_busses.addWidget(self.bus_to_regs)
        row_busses.addWidget(QLabel('bus from regs'))
        self.bus_from_regs = QLineEdit('00000000', readOnly=True)
        self.bus_from_regs.setFixedWidth(160)
        row_busses.addWidget(self.bus_from_regs)
        row_busses.addStretch()
        self.layout.addLayout(row_busses)

        # SRC and TGT
        row_src_tgt = QHBoxLayout()
        row_src_tgt.addWidget(QLabel('SRC'))
        self.src = QLineEdit('00000000', readOnly=True)
        self.src.setFixedWidth(160)
        row_src_tgt.addWidget(self.src)
        row_src_tgt.addWidget(QLabel('TGT'))
        self.tgt = QLineEdit('00000000', readOnly=True)
        self.tgt.setFixedWidth(160)
        row_src_tgt.addWidget(self.tgt)
        row_src_tgt.addStretch()
        self.layout.addLayout(row_src_tgt)

        self.state.carry
        self.state.cmp
        self.state.write

        self.rows = {}
        self.writes_to_reg_bus = ['P1', 'M1', 'W', 'A', 'R']
        for name in ['N', 'T', 'P1', 'M1', 'W', 'A', 'R', 'TP1']:
            self.add_row(name)
        self.update_data()

    def add_row(self, name):
        row_n = QHBoxLayout()
        row_n.addWidget(QLabel(f'{name}:'))
        row_n.addWidget(QLabel('clock'))
        click = QLineEdit('0', readOnly=True)
        click.setFixedWidth(30)
        row_n.addWidget(click)
        row_n.addWidget(QLabel('value'))
        value = QLineEdit('00000000', readOnly=True)
        value.setFixedWidth(160)
        row_n.addWidget(value)
        if name in self.writes_to_reg_bus:
            row_n.addWidget(QLabel('disable'))
            disable = QLineEdit('0', readOnly=True)
            disable.setFixedWidth(30)
            row_n.addWidget(disable)
        else:
            disable = None
        self.rows[name] = (click, value, disable)
        row_n.addStretch()
        self.layout.addLayout(row_n)

    def update_data(self):
        # bus from device and clock
        self.bus_from_device.setText(txt(self.state.bus_from_device))
        self.clock.setText(txt(self.state.clock))
        self.phase.setText(txt(self.state.f))
        # register busses
        self.bus_to_regs.setText(txt(self.state.bus_to_registers()))
        self.bus_from_regs.setText(txt(self.state.bus_from_registers()))
        #
        self.src.setText(txt(self.state.src()))
        self.tgt.setText(txt(self.state.tgt()))

        for name, (click, value, disable) in self.rows.items():
            click.setText(txt(self.state.clicks()[name]))
            value.setText(txt(self.state.r[name]))
            if name in self.writes_to_reg_bus:
                disable.setText(txt(self.state.flags()[name]))

    def toggle_clicked(self):
        try:
            self.computer.toggle_clock()
            self.update_data()
        except Exception as ex:
            print(ex)
            print(traceback.format_exc())

    def rw_clicked(self):
        try:
            self.computer.read_write_cycle()
            self.update_data()
        except Exception as ex:
            print(ex)
            print(traceback.format_exc())

    def auto_clicked(self):
        try:
            count = 0
            while count < 100:
                count +=1
                interface.read_write_cycle()  # read instruction
                if self.state.bus_from_device == [0, 0, 0, 0, 0, 0, 0, 0]:
                    return
                interface.toggle_clock()  # click 1
                self.update_data()
                interface.toggle_clock()  # to phase 2
                interface.read_write_cycle()  # read immediate or *M
                interface.toggle_clock()  # click 2
                self.update_data()
                interface.toggle_clock()  # to phase 3
                interface.read_write_cycle()  # write to *M if required
                interface.toggle_clock()  # click 3
                self.update_data()
                interface.toggle_clock()  # to phase 4

                interface.toggle_clock()  # click 4
                self.update_data()
                interface.toggle_clock()  # to phase 0
        except Exception as ex:
            print(ex)
            print(traceback.format_exc())

    def cycle_clicked(self):
        try:
            interface.read_write_cycle()  # read instruction
            if self.state.bus_from_device == [0, 0, 0, 0, 0, 0, 0, 0]:
                return
            interface.toggle_clock()  # click 1
            self.update_data()
            interface.toggle_clock()  # to phase 2
            interface.read_write_cycle()  # read immediate or *M
            interface.toggle_clock()  # click 2
            self.update_data()
            interface.toggle_clock()  # to phase 3
            interface.read_write_cycle()  # write to *M if required
            interface.toggle_clock()  # click 3
            self.update_data()
            interface.toggle_clock()  # to phase 4

            interface.toggle_clock()  # click 4
            interface.toggle_clock()  # to phase 0
            self.update_data()
        except Exception as ex:
            print(ex)
            print(traceback.format_exc())



def test_run():
    for i in range(4):
        # start in phase 0 with clock on low
        interface.read_write_cycle()  # read instruction
        interface.toggle_clock()  # click 1
        interface.toggle_clock()  # to phase 2
        interface.read_write_cycle()  # read immediate or *M
        interface.toggle_clock()  # click 2
        interface.toggle_clock()  # to phase 3
        interface.read_write_cycle()  # write to *M if required
        interface.toggle_clock()  # click 3
        interface.toggle_clock()  # to phase 4

        interface.toggle_clock()  # click 4
        interface.toggle_clock()  # to phase 0

    # computer = MyComputer()
    # computer.write_to_bus(5, 1)
    # computer.write_to_bus(6, 2)
    # computer.write_to_bus(5, 3)
    # computer.write_to_bus(6, 4)



if __name__ == '__main__':

    # 7x11
    program711 = ['RDV M1 40',  # Initialize
                  'RDV A 11',
                  'CPY A *M',
                  'RDV M1 42',
                  'RDV A 7',
                  'CPY A *M',
                  'RDV M1 40',   #addr 12 / start of loop / adds 11 to m20
                  'CPY *M A',
                  'ADV A 11',
                  'CPY A *M',
                  'RDV M1 42',  # Subtract 1 from m22
                  'CPY *M A',
                  'ADV A -1',
                  'CPY A *M',
                  'JMZ A 32',  # if m22 is zero then exit loop
                  'RDV P1 12',  # location 30
                  'NOP'        # end of program
                  ]
    program711 += ['0']*10
    expected_machine_state = ExpectedMachineState()
    interface = MyComputerInterface(program711, expected_machine_state)

    app = QApplication(sys.argv)
    window = MainWindow(interface)
    sys.exit(app.exec())
