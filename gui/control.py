import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports
import serial
import threading


class CubeControlApp:
    def __init__(self) -> None:
        self.device = None
        self.serial_devices = []
        self.update_serial_handle = None

        self.app = tk.Tk()
        self.app.title("CUBEcontrol")
        self.app.geometry("800x500")
        self.app.resizable(False, False)

        self.setup_ui()

    def setup_ui(self) -> None:
        # Dark theme with blue accent color
        self.app.tk.call("source", "azure.tcl")
        self.app.tk.call("set_theme", "dark")

        # Create right frame for the image
        self.right_frame = ttk.Frame(self.app, padding=0, borderwidth=0)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create left frame for the labels and dropdown
        self.left_frame = ttk.Frame(self.app, padding=20)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure grid in the left frame
        self.left_frame.columnconfigure(1, weight=1)
        self.left_frame.rowconfigure(0, weight=1)

        # Load and display the image in the right frame
        image_file = "image.png"
        self.image = tk.PhotoImage(file=image_file)
        self.image_label = ttk.Label(self.right_frame, image=self.image)
        self.image_label.pack(anchor="e", expand=True)

        # Logo text
        self.logo_text = ttk.Label(
            self.left_frame, text="CUBEcontrol", font=("Arial", 24, "bold")
        )
        self.logo_text.grid(column=0, row=0, columnspan=3, pady=10)

        # Label
        ttk.Label(self.left_frame, text="Select a Device:", font=("Arial", 12)).grid(
            column=0, row=1, sticky=tk.W, columnspan=3, pady=10, padx=10
        )

        # Serial devices dropdown
        self.serial_devices = [
            str(port.device) for port in serial.tools.list_ports.comports()
        ]
        self.device_dropdown = ttk.Combobox(
            self.left_frame,
            values=self.serial_devices,
            font=("Arial", 12),
            state="disabled",
        )
        self.device_dropdown.grid(column=0, row=2, sticky=(tk.W, tk.E), padx=10)

        # Connect button
        self.connect_button = ttk.Button(
            self.left_frame,
            text="Connect",
            style="Accent.TButton",
            state="disabled",
            command=self.connect_device,
        )
        self.connect_button.grid(column=1, row=2, sticky=tk.W)

        # Schedule the automatic update of the serial devices list
        self.update_serial_handle = self.app.after(0, self.update_serial_devices)

    def connect_device(self) -> None:
        selected_device = self.device_dropdown.get()
        print(f"Connecting to {selected_device}...")
        try:
            self.device = serial.Serial(selected_device, 9600, timeout=1)
            if self.device.is_open:
                self.connect_button.configure(
                    text="Disconnect", command=self.disconnect_device
                )
                self.device_dropdown.configure(state="disabled")
                # create_console()
        except Exception as e:
            print(f"Error connecting to device: {e}")

    def disconnect_device(self):
        if self.device.is_open:
            self.device.close()
            self.device = None
            print("Disconnected from device")
            self.connect_button.configure(
                text="Connect", command=self.connect_device, state="enabled"
            )
            self.device_dropdown.configure(state="readonly")
            # remove_console()

    def update_serial_devices(self):
        # Get the list of serial devices and update the dropdown
        self.serial_devices = [
            str(port.device) for port in serial.tools.list_ports.comports()
        ]
        if self.device == None:
            if len(self.serial_devices) > 0:
                self.device_dropdown["values"] = self.serial_devices
                self.device_dropdown.configure(state="readonly")
                self.connect_button.configure(state="enabled")
                if self.device_dropdown.current() < 0:
                    self.device_dropdown.current(0)

            else:
                self.device_dropdown.set("No Device Connected")
                self.device_dropdown.configure(state="disabled")
                self.connect_button.configure(state="disabled")
        else:
            if self.device.port not in self.serial_devices:
                print("ERROR: connection lost")

        # Schedule the next update
        self.update_serial_handle = self.app.after(1000, self.update_serial_devices)

    def start(self):
        self.app.mainloop()

if __name__ == "__main__":
    app = CubeControlApp()
    app.start()