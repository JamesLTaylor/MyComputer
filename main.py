from connection import translate_to_bin, MyComputerInterface, ExpectedMachineState
from PyQt5.QtWidgets import QApplication, QWidget, QTabWidget, QGridLayout, QLabel
from PyQt5.QtCore import Qt

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.computer = MyComputer()
        self.computer = None
        self.setWindowTitle('MyComputer')
        self.width = 400
        self.height = 600
        self.setMinimumSize(self.width, self.height)

        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tab_run = RunTab(self, self.computer)
        self.tab_test = TestTab(self, self.computer)
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


class TestTab(QWidget):
    def __init__(self, parent, computer):
        super(QWidget, self).__init__(parent)
        self.computer = computer
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Command:
        row1 = QHBoxLayout()
        self.command_test = QLineEdit()
        self.translate = QPushButton('Translate')
        self.translate.clicked.connect(self.translate_clicked)
        self.command = QLineEdit(readOnly=True)
        row1.addWidget(self.command_test)
        row1.addWidget(self.translate)
        row1.addWidget(self.command)

        layout.addLayout(row1)

    def translate_clicked(self):
        try:
            self.command.setText(translate_to_bin(self.command_test.text()))
        except Exception as ex:
            print(ex)
            self.command.setText('Error')


if __name__ == '__main__':
    # app = QApplication(sys.argv)
    # window = MainWindow()
    # sys.exit(app.exec())
    # 7x11
    program711 = ['RDV M1 40',  # Initialize
                  'RDV A 11',
                  'CPY *M A',
                  'RDV M1 42',
                  'RDV A 7',
                  'CPY *M A',
                  'RDV M1 40',   #addr 12 / start of loop / adds 11 to m20
                  'CPY A *M',
                  'ADV A 11',
                  'CPY *M A',
                  'RDV M1 42',  # Subtract 1 from m22
                  'CPY A *M',
                  'ADV A -1',
                  'CPY *M A',
                  'JMZ A 32',  # if m22 is zero then exit loop
                  'RDV P1 12',  # 30
                  'NOP'        # end of program
                  ]

    expected_machine_state = ExpectedMachineState()
    interface = MyComputerInterface(program711, expected_machine_state)
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
