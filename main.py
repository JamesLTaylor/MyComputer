from time import sleep

from connection import translate_to_machine_instruction, MyComputerInterface, ExpectedMachineState
from PyQt5.QtWidgets import QApplication, QWidget, QTabWidget, QGridLayout, QLabel, QPlainTextEdit, QFrame, QScrollArea, \
    QCheckBox
from PyQt5.QtCore import Qt, QSize, QObject, pyqtSignal, QThread
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

from utils import bin_to_value


class Worker(QObject):
    """ Worker to run program off main UI thread.
    """
    finished = pyqtSignal()
    progress = pyqtSignal()
    interface = None
    state = None

    def run(self):
        try:
            count = 0
            while count < 1000:
                count += 1
                self.interface.read_write_cycle()  # read instruction
                if self.state.bus_from_device == [0, 0, 0, 0, 0, 0, 0, 0]:
                    return
                self.interface.toggle_clock()  # click 1
                self.progress.emit()
                self.interface.toggle_clock()  # to phase 2
                self.interface.read_write_cycle()  # read immediate or *M
                self.interface.toggle_clock()  # click 2
                self.progress.emit()
                self.interface.toggle_clock()  # to phase 3
                self.interface.read_write_cycle()  # write to *M if required
                self.interface.toggle_clock()  # click 3
                self.progress.emit()
                self.interface.toggle_clock()  # to phase 4

                self.interface.toggle_clock()  # click 4
                self.progress.emit()
                self.interface.toggle_clock()  # to phase 0
        except Exception as ex:
            print(ex)
            print(traceback.format_exc())
        finally:
            self.finished.emit()



class MainWindow(QWidget):
    def __init__(self, interface, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interface = interface
        self.setWindowTitle('MyComputer')
        self.width = 400
        self.height = 800
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
    def __init__(self, parent, interface):
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
    def __init__(self, parent, interface: MyComputerInterface):
        super(QWidget, self).__init__(parent)
        self.counter = 0
        self.interface = interface
        self.state = self.interface.expected_machine_state
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Memory

        rows = []
        for i, (m, rm) in enumerate(zip(self.interface.memory, self.interface.readable_memory)):
            rows.append(f'{i*2:<5} {m:<20}  {rm}')
        self.mem = QPlainTextEdit('\n'.join(rows), readOnly=True)
        self.mem.setMinimumSize(QSize(600, 600))
        # scrollArea = QScrollArea()
        # scrollArea.setBackgroundRole(QPalette.Dark)
        # scrollArea.setWidget(self.mem)
        # self.layout.addWidget(scrollArea)
        self.layout.addWidget(self.mem)

        # # Control
        # sep = QFrame()
        # sep.Shape(QFrame.HLine)
        # sep.setLineWidth(3)
        # layout.addWidget(sep)

        row_custom = QHBoxLayout()
        self.use_custom = QCheckBox()

        self.use_custom.clicked.connect(self.custom_toggle)
        row_custom.addWidget(self.use_custom)
        row_custom.addWidget(QLabel('Custom'))
        self.custom_command = QLineEdit('command', enabled=False)
        self.custom_command.textChanged.connect(self.command_changed)
        row_custom.addWidget(self.custom_command)
        row_custom.addWidget(QLabel('Translated'))
        self.translated_command = QLineEdit('', enabled=False)
        row_custom.addWidget(self.translated_command)
        row_custom.addWidget(QLabel('Curr Address'))
        self.curr_address = QLineEdit('0', readOnly=True)
        row_custom.addWidget(self.curr_address)
        row_custom.addStretch()
        self.layout.addLayout(row_custom)

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
        self.cancel = QPushButton('Cancel')
        self.cancel.clicked.connect(self.cancel_clicked)
        row_clock.addWidget(self.cancel)
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

        row_src_tgt.addWidget(QLabel('carry'))
        self.carry = QLineEdit('0', readOnly=True)
        self.carry.setFixedWidth(30)
        row_src_tgt.addWidget(self.carry)
        row_src_tgt.addWidget(QLabel('cmp'))
        self.cmp = QLineEdit('0', readOnly=True)
        self.cmp.setFixedWidth(30)
        row_src_tgt.addWidget(self.cmp)
        row_src_tgt.addWidget(QLabel('write'))
        self.write = QLineEdit('0', readOnly=True)
        self.write.setFixedWidth(30)
        row_src_tgt.addWidget(self.write)
        row_src_tgt.addStretch()
        self.layout.addLayout(row_src_tgt)

        self.rows = {}
        self.writes_to_reg_bus = ['P1', 'M1', 'W', 'A', 'R']
        for name in ['N', 'T', 'P1', 'M1', 'W', 'A', 'R', 'TP1', 'TM1']:
            self.add_row(name)

        self.update_data()

    def command_changed(self):
        try:
            self.translated_command.setText(translate_to_machine_instruction(self.custom_command.text()))
            self.interface.custom_command = self.translated_command.text()
        except Exception as ex:
            print(ex)
            print(traceback.format_exc())

    def custom_toggle(self, value):
        if value:
            self.custom_command.setEnabled(True)
        else:
            self.custom_command.setEnabled(False)
            self.interface.custom_command = None

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
        rows = []
        for i, (m, rm) in enumerate(zip(self.interface.memory, self.interface.readable_memory)):
            prefix = '>> ' if i == self.interface.current_address // 2 else ''
            rows = rows + self.interface.insert_rows.get(i*2, [])
            rows.append(f'{prefix}{i * 2:<5} {m:<20}  {rm}')
        self.mem.setPlainText('\n'.join(rows))
        self.curr_address.setText(str(self.interface.current_address))

        # bus from device and clock
        self.bus_from_device.setText(txt(self.state.bus_from_device))
        self.clock.setText(txt(self.state.clock))
        self.phase.setText(txt(self.state.f))
        # register busses
        self.bus_to_regs.setText(txt(self.state.bus_to_registers()))
        self.bus_from_regs.setText(txt(self.state.bus_from_registers()))
        # SRC/TGT row
        self.src.setText(txt(self.state.src()))
        self.tgt.setText(txt(self.state.tgt()))

        self.carry.setText(txt(self.state.jk['Carry']))
        self.cmp.setText(txt(self.state.jk['Cmp']))
        self.write.setText(txt(self.state.write()))

        for name, (click, value, disable) in self.rows.items():
            click.setText(txt(self.state.clicks()[name]))
            value.setText(txt(self.state.r[name]))
            if name in self.writes_to_reg_bus:
                disable.setText(txt(self.state.flags()[name]))

    def toggle_clicked(self):
        try:
            self.interface.toggle_clock()
            self.update_data()
        except Exception as ex:
            print(ex)
            print(traceback.format_exc())

    def rw_clicked(self):
        try:
            self.interface.read_write_cycle()
            self.update_data()
        except Exception as ex:
            print(ex)
            print(traceback.format_exc())

    def disable(self):
        self.toggle.setEnabled(False)
        self.rw.setEnabled(False)
        self.cycle.setEnabled(False)
        self.auto.setEnabled(False)

    def reenable(self):
        self.toggle.setEnabled(True)
        self.rw.setEnabled(True)
        self.cycle.setEnabled(True)
        self.auto.setEnabled(True)

    def cancel_clicked(self):
        pass

    def auto_clicked(self):
        """ Run until NOP encountered
        """
        self.thread = QThread()
        self.worker = Worker()
        self.worker.interface = self.interface
        self.worker.state = self.state
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.update_data)

        self.thread.start()

        self.disable()
        self.worker.finished.connect(self.reenable)

    def cycle_clicked(self):
        try:
            self.interface.full_cycle(1)
            self.update_data()
        except Exception as ex:
            print(ex)
            print(traceback.format_exc())


def run():
    # 7x11
    # prog_name = 'mult.prog'
    # prog_name = 'read_write_a.prog'
    # prog_name = 'fibonacci.prog'
    # prog_name = 'add16bit.prog'
    # prog_name = 'subtract16bit.prog'
    # prog_name = 'find_largest.prog'
    # prog_name = 'test.prog'
    prog_name = 'turing_or.prog'
    with open(f'./progs/{prog_name}') as f:
        program = f.readlines()
    expected_machine_state = ExpectedMachineState()
    interface = MyComputerInterface(program, expected_machine_state, real_device=True)
    # interface = MyComputerInterface(program, expected_machine_state, real_device=False)

    app = QApplication(sys.argv)
    window = MainWindow(interface)
    sys.exit(app.exec())


if __name__ == '__main__':
    run()

