import serial.tools.list_ports
import serial
import threading
import PySimpleGUI as sg

class SerialConsole:
    def __init__(self):
        self.serial_port = None
        self.serial_thread = None
        self.stop_serial = False
        self.serial_ports = serial.tools.list_ports.comports()
        self.baud_rates = [300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]

        self.layout = [
            [sg.Text("Serial Console")],
            [sg.Multiline(size=(80, 20), key="console_text", autoscroll=True, disabled=True)],
            [sg.Input(key="input_text"), sg.Button("Send", key="send_button")],
            [sg.Combo([port.device for port in self.serial_ports], default_value=self.serial_ports[0].device, key="serial_port_var", readonly=True),
             sg.Combo([str(rate) for rate in self.baud_rates], default_value="9600", key="baud_rate_var", readonly=True),
             sg.Button("Connect", key="connect_button"), sg.Button("Disconnect", key="disconnect_button", disabled=True)]
        ]

        self.window = sg.Window("Serial Console", self.layout)

    def run(self):
        while True:
            event, values = self.window.read()
            if event == sg.WIN_CLOSED:
                self.disconnect_serial()
                break
            elif event == "connect_button":
                self.connect_serial(values)
            elif event == "disconnect_button":
                self.disconnect_serial()
            elif event == "send_button":
                self.send_serial(values)

    def connect_serial(self, values):
        if self.serial_port is None:
            self.stop_serial = False
            self.serial_port = serial.Serial(values["serial_port_var"], int(values["baud_rate_var"]))
            self.window["console_text"].print(f"Connected to {self.serial_port.name}.")
            self.serial_thread = threading.Thread(target=self.read_serial)
            self.serial_thread.start()
            self.window["disconnect_button"].update(disabled=False)
            self.window["connect_button"].update(disabled=True)
            self.window["baud_rate_var"].update(disabled=True)
            self.window["serial_port_var"].update(disabled=True)

    def send_serial(self, values):
        if self.serial_port is not None:
            input_data = values["input_text"] + "\n"
            self.serial_port.write(input_data.encode())
            self.window["console_text"].print(f">>> {input_data}", end="")
            self.window["input_text"].update(value="")
        else:
            self.window["console_text"].print("Serial port not connected.")

    def read_serial(self):
        while not self.stop_serial and self.serial_port is not None:
            if (self.serial_port.inWaiting() > 0):
                data = self.serial_port.readline().decode()
                self.window["console_text"].print(data, end="")
        self.serial_port.close()
        self.serial_port = None

    def disconnect_serial(self):
        if self.serial_port is not None:
            self.stop_serial = True
            self.serial_thread.join()
            self.window["disconnect_button"].update(disabled=True)
            self.window["baud_rate_var"].update(disabled=False)
            self.window["serial_port_var"].update(disabled=False)
            self.window["connect_button"].update(disabled=False)

if __name__ == '__main__':
    console = SerialConsole()
    console.run()
