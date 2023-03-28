import serial.tools.list_ports
import serial
import threading
from PyQt6.QtWidgets import QApplication, QTextEdit, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QComboBox, QLineEdit

class SerialConsole(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Serial Console")
        self.setFixedSize(700, 500)
        self.serial_port = None
        self.serial_thread = None
        self.stop_serial = False
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.input_text = QLineEdit()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_serial)
        self.serial_ports = serial.tools.list_ports.comports()
        self.serial_port_var = QComboBox()
        self.serial_port_var.addItems([port.device for port in self.serial_ports])
        self.serial_port_var.setCurrentIndex(0)
        self.baud_rates = [300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
        self.baud_rate_var = QComboBox()
        self.baud_rate_var.addItems([str(rate) for rate in self.baud_rates])
        self.baud_rate_var.setCurrentIndex(5)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_serial)
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect_serial)
        self.disconnect_button.setDisabled(True)
        self.create_widgets()
        
    def create_widgets(self):
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_text)
        input_layout.addWidget(self.send_button)

        port_layout = QHBoxLayout()
        port_layout.addWidget(self.serial_port_var)
        port_layout.addWidget(self.baud_rate_var)
        port_layout.addWidget(self.connect_button)
        port_layout.addWidget(self.disconnect_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.console_text)
        main_layout.addLayout(input_layout)
        main_layout.addLayout(port_layout)

        self.setLayout(main_layout)

    def connect_serial(self):
        if self.serial_port is None:
            self.stop_serial = False
            self.serial_port = serial.Serial(self.serial_port_var.currentText(), int(self.baud_rate_var.currentText()))
            self.console_text.insertPlainText(f"Connected to {self.serial_port.name}.\n")
            self.serial_thread = threading.Thread(target=self.read_serial)
            self.serial_thread.start()
            self.disconnect_button.setDisabled(False)
            self.connect_button.setDisabled(True)
            self.baud_rate_var.setDisabled(True)
            self.serial_port_var.setDisabled(True)

    def send_serial(self):
        if self.serial_port is not None:
            input_data = self.input_text.text() + "\n"
            self.serial_port.write(input_data.encode())
            self.console_text.insertPlainText(f">>> {input_data}")
            self.input_text.clear()
        else:
            self.console_text.insertPlainText("Serial port not connected.\n")

    def read_serial(self):
        while not self.stop_serial and self.serial_port is not None:
            if (self.serial_port.inWaiting() > 0):
                data = self.serial_port.readline().decode()
                self.console_text.insertPlainText(f"{data}")
        #print("closed")
        self.serial_port.close()
        self.serial_port = None


    def disconnect_serial(self):
        if self.serial_port is not None:
            self.stop_serial = True
            self.serial_thread.join()
            self.disconnect_button.setDisabled(True)
            self.baud_rate_var.setDisabled(False)
            self.serial_port_var.setDisabled(False)
            self.connect_button.setDisabled(False)
            
            

    def closeEvent(self, event):
        self.disconnect_serial()

if __name__ == '__main__':
    app = QApplication([])
    window = SerialConsole()
    window.show()
    app.exec()
