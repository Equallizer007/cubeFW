import tkinter as tk
import serial.tools.list_ports
import serial
import threading


class SerialConsole(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("Serial Console")
        self.pack()
        self.create_widgets()
        self.serial_port = None
        self.serial_thread = None
        self.stop_serial = False

    def create_widgets(self):
        self.console_text = tk.Text(self, state="disabled")
        self.console_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.input_text = tk.Entry(self)
        self.input_text.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)
        self.input_text.focus_set()
        self.input_text.bind("<Return>", lambda event: self.send_serial())

        self.send_button = tk.Button(self, text="Send", command=self.send_serial)
        self.send_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.serial_ports = serial.tools.list_ports.comports()
        self.serial_port_var = tk.StringVar(self)

        self.connect_button = tk.Button(
            self, text="Connect", command=self.connect_serial
        )
        self.connect_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.disconnect_button = tk.Button(
            self, text="Disconnect", command=self.disconnect_serial, state="disabled"
        )
        self.disconnect_button.pack(side=tk.LEFT, padx=5, pady=5)

        if len(self.serial_ports) > 0:
            self.serial_port_var.set(self.serial_ports[0].device)
            self.serial_port_dropdown = tk.OptionMenu(
                self, self.serial_port_var, *[port.device for port in self.serial_ports]
            )
        else:
            self.serial_port_var.set("No serial port available")
            self.serial_port_dropdown = tk.OptionMenu(
                self, self.serial_port_var, "No serial port available"
            )
            self.connect_button.config(state="disabled")
            self.send_button.config(state="disabled")

        self.serial_port_dropdown.pack(side=tk.LEFT, padx=5, pady=5)
        self.baud_rates = [
            300,
            600,
            1200,
            2400,
            4800,
            9600,
            19200,
            38400,
            57600,
            115200,
        ]
        self.baud_rate_var = tk.IntVar(self)
        self.baud_rate_var.set(self.baud_rates[5])
        self.baud_rate_dropdown = tk.OptionMenu(
            self, self.baud_rate_var, *self.baud_rates
        )
        self.baud_rate_dropdown.pack(side=tk.LEFT, padx=5, pady=5)

    def connect_serial(self):
        if self.serial_port is None:
            self.stop_serial = False
            self.serial_port = serial.Serial(
                self.serial_port_var.get(), self.baud_rate_var.get()
            )
            self.console_text.config(state="normal")
            self.console_text.insert(tk.END, f"Connected to {self.serial_port.name}.\n")
            self.console_text.config(state="disabled")
            self.serial_thread = threading.Thread(target=self.read_serial)
            self.serial_thread.start()
            self.disconnect_button.config(state="normal")
            self.connect_button.config(state="disabled")
            self.baud_rate_dropdown.config(state="disabled")
            self.serial_port_dropdown.config(state="disabled")

    def send_serial(self):
        if self.serial_port is not None:
            input_data = self.input_text.get() + "\n"
            self.serial_port.write(input_data.encode())
            self.console_text.config(state="normal")
            self.console_text.insert(tk.END, f">>> {input_data}")
            self.console_text.config(state="disabled")
            self.input_text.delete(0, tk.END)
        else:
            self.console_text.config(state="normal")
            self.console_text.insert(tk.END, "Serial port not connected.\n")
            self.console_text.config(state="disabled")

    def read_serial(self):
        while not self.stop_serial and self.serial_port is not None:
            if self.serial_port.inWaiting() > 0:
                data = self.serial_port.readline().decode()
                self.console_text.config(state="normal")
                self.console_text.insert(tk.END, f"{data}")
                self.console_text.config(state="disabled")
        # print("closed")
        self.serial_port.close()
        self.serial_port = None

    def disconnect_serial(self):
        if self.serial_port is not None:
            self.stop_serial = True
            self.serial_thread.join()
            self.disconnect_button.config(state="disabled")
            self.baud_rate_dropdown.config(state="normal")
            self.serial_port_dropdown.config(state="normal")
            self.connect_button.config(state="normal")

    def __del__(self):
        self.disconnect_serial()


root = tk.Tk()
root.resizable(False, False)
app = SerialConsole(master=root)
app.mainloop()
