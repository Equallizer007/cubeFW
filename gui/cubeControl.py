import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk  # pip install sv-ttk
import serial.tools.list_ports
import serial
import threading
import re


class CubeControlApp:
    def __init__(self) -> None:
        self.device = None
        self.serial_devices = []
        self.update_serial_handle = None

        self.app = tk.Tk()
        self.app.title("CUBEcontrol")
        self.app.geometry("800x500")
        self.app.resizable(False, False)

        self.adc_pattern = re.compile(r"<ADC>.*calc:(\d+\.\d+)V")
        self.pos_pattern = re.compile(r"POS> homed:(\d) steps:(\d+) pos:(\d+\.\d{4})")


        self.setup_ui()

    def setup_ui(self) -> None:
        sv_ttk.set_theme("light")

        # Create right frame for the image
        self.right_frame = ttk.Frame(
            self.app,
            height=500,
            width=400,
            padding=0,
            borderwidth=0,
        )
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        self.right_frame.pack_propagate(False)
        self.right_frame.grid_propagate(False)

        # Create left frame for the labels and dropdown
        self.left_frame = ttk.Frame(
            self.app,
            height=500,
            width=400,
            padding=20,
            borderwidth=0,
        )
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        self.left_frame.pack_propagate(False)
        self.left_frame.grid_propagate(False)

        # Configure grid in the left frame
        self.left_frame.columnconfigure(1, weight=1)
        self.left_frame.rowconfigure(0, weight=1)

        # Load and display the image in the right frame
        image_file = "image.png"
        self.image = tk.PhotoImage(file=image_file)
        self.image_label = ttk.Label(
            self.right_frame,
            # background="green",
            image=self.image,
            borderwidth=0,
            padding=0,
        )
        self.image_label.grid()
        self.image_label.update()
        print(self.image_label.winfo_height())
        print(self.image_label.winfo_width())

        # Logo text
        self.logo_text_label = ttk.Label(
            self.left_frame,
            text="CUBEcontrol",
            anchor="center",
            font=("Arial", 24, "bold"),
            width=400,
        )
        self.logo_text_label.grid(column=0, row=0, columnspan=3)

        # Label
        self.select_device_label = ttk.Label(
            self.left_frame, text="Select a Device:", font=("Arial", 12)
        )
        self.select_device_label.grid(
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
            self.device = serial.Serial(selected_device, 115200, timeout=1)
        except Exception as e:
            messagebox.showerror(
                "Error connecting to device!",
                message=f"Error connecting to device: {e}",
            )
            return
        if self.device.is_open:
            self.stop_serial = False
            self.connect_button.configure(
                text="Disconnect", command=self.disconnect_device
            )
            self.device_dropdown.configure(state="disabled")
            self.create_control_widgets()
            self.create_console()
            self.serial_thread = threading.Thread(target=self.read_serial)
            self.update_console_text(
                f"Connected to {self.device.port} @  baudrate {self.device.baudrate}"
            )
            #send intial messages
            self.send_msg("M0 ;restart device")
            self.send_msg("M1 500 ;set report interval to 500ms")
            self.serial_thread.start()

    def disconnect_device(self) -> None:
        print("Disconnected from device")
        self.stop_serial = True
        self.serial_thread.join()
        self.connect_button.configure(
            text="Connect", command=self.connect_device, state="enabled"
        )
        self.device_dropdown.configure(state="readonly")
        self.select_device_label.grid()
        self.remove_console()
        self.remove_control_widgets()

    def update_serial_devices(self) -> None:
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
                self.disconnect_device()
                messagebox.showerror(
                    "Connection Lost!", message="Connection to device lost!"
                )

        # Schedule the next update
        self.update_serial_handle = self.app.after(1000, self.update_serial_devices)

    def create_control_widgets(self) -> None:
        self.logo_text_label.grid(column=0, row=0, sticky="n")
        self.select_device_label.grid_remove()

        self.control_frame = ttk.Frame(
            self.left_frame, padding=10, width=400, height=500
        )
        self.control_frame.grid(column=0, row=1, columnspan=3, sticky="nesw")

        # ADC LabelFrame
        self.adc_label_frame = ttk.LabelFrame(
            self.control_frame, text="ADC", padding=0
        )
        self.adc_label_frame.grid(column=0, row=0, columnspan=3, sticky="nesw", padx=0, pady=5)

        # Current adc_voltage label
        self.adc_voltage_label = ttk.Label(
            self.adc_label_frame,
            text="ADC voltage: ?"
        )
        self.adc_voltage_label.grid(column=0, row=0, pady=5, padx=(10, 0))

        # Movement LabelFrame
        self.movement_label_frame = ttk.LabelFrame(
            self.control_frame, text="Manual Movement", padding=0
        )
        self.movement_label_frame.grid(column=0, row=1, columnspan=3, sticky="nesw", padx=0, pady=5)

        # Home button
        self.home_button = ttk.Button(
            self.movement_label_frame,
            text="Home",
            command=lambda: self.send_msg("G28 ;home")
        )
        self.home_button.grid(column=0, row=3, pady=5, padx=(10, 0), sticky="w" )

        # Current position label
        self.current_position_label = ttk.Label(
            self.movement_label_frame,
            text="?"
        )
        self.current_position_label.grid(column=0, row=0, pady=5, padx=(10, 0))

        # Current steps label
        self.current_steps_label = ttk.Label(
            self.movement_label_frame,
            text="Steps: ?"
        )
        self.current_steps_label.grid(column=1, row=0, pady=5, padx=(0, 0))

        # Homed label
        self.homed_label = ttk.Label(
            self.movement_label_frame,
            text="Not Homed"
        )
        self.homed_label.grid(column=2, row=0, pady=5, padx=(0, 0))

        # Up arrow button
        self.up_arrow_button = ttk.Button(
            self.movement_label_frame,
            text="↑ Up",
            # command = lambda: self.send_msg(f"G1 Z{self.movement_steps_dropdown["text"])} ; move up")
        )
        self.up_arrow_button.grid(column=0, row=1, pady=5, padx=(10, 0), sticky="w" )

        # Down arrow button
        self.down_arrow_button = ttk.Button(
            self.movement_label_frame,
            text="↓ Down",
        )
        self.down_arrow_button.grid(column=1, row=1, pady=5, padx=(0, 0), sticky="w" )

        # Movement Step dropdown
        self.movement_steps = [0.5, 1, 2.5, 5, 10, 100, 1000, 5000]
        movement_steps_labels = ["0.5µm", "1µm", "2.5µm", "5µm", "10µm", "100µm", "1mm", "5mm"]
        self.movement_steps_dropdown = ttk.Combobox(
            self.movement_label_frame,
            values=movement_steps_labels,
            font=("Arial", 11),
            state="readonly",
            width=5,
        )
        self.movement_steps_dropdown.current(0)
        self.movement_steps_dropdown.grid(column=2, row=1, padx = 0)

        # Restart button
        self.restart_button = ttk.Button(
            self.movement_label_frame,
            text="Restart",
            command = lambda: self.send_msg("M0 ;restart")
        )
        self.restart_button.grid(column=1, row=3, pady=5, padx=(0, 0), sticky="w" )


    def remove_control_widgets(self) -> None:
        self.logo_text_label.grid(column=0, row=0, sticky="")
        self.control_frame.destroy()

    def create_console(self) -> None:
        # Create a console frame within the right frame
        print("create console")
        self.console_frame = ttk.Frame(
            self.right_frame, padding=20, width=400, height=500
        )
        self.console_frame.pack()
        self.console_frame.grid_propagate(False)

        console_label = ttk.Label(
            self.console_frame, text="Console:", font=("Arial", 12), anchor="center"
        )
        console_label.grid(column=0, row=0, columnspan=3, sticky="w")

        self.console_text = tk.Text(self.console_frame, wrap=tk.WORD, state="disabled", font=("Arial", 10))
        self.console_text.grid(
            column=0, row=1, columnspan=3, sticky="nsew"
        )  # Fill available space

        # Create a scrollbar and associate it with console_text
        scrollbar = ttk.Scrollbar(
            self.console_frame, orient="vertical", command=self.console_text.yview
        )
        scrollbar.grid(column=3, row=1, sticky="ns")

        # Set the yscrollcommand option of console_text to the set method of the scrollbar
        self.console_text.configure(yscrollcommand=scrollbar.set)
        self.console_frame.grid_rowconfigure(2, weight=1)  # Add empty row with weight 1

        self.placeholder_text = "Type your command here..."

        def remove_placeholder_text():
            if self.console_input.get() == self.placeholder_text:
                self.console_input.delete(0, "end")
                self.console_input.configure(foreground="black")

        def set_placeholder_text():
            if len(self.console_input.get()) == 0:
                self.console_input.delete(0, "end")
                self.console_input.insert(0, self.placeholder_text)
                self.console_input.configure(foreground="#a9a9a9")

        self.console_input = ttk.Entry(self.console_frame, font=("Arial", 12))
        self.console_input.bind("<Return>", lambda event: self.send_serial())
        set_placeholder_text()
        self.console_input.bind("<FocusIn>", lambda event: remove_placeholder_text())
        self.console_input.bind("<FocusOut>", lambda event: set_placeholder_text())
        self.console_input.grid(column=0, row=3, columnspan=2, sticky="ew")

        send_button = ttk.Button(
            self.console_frame,
            text="Send",
            style="Accent.TButton",
            command=self.send_serial,
        )
        send_button.grid(column=2, row=3, sticky="e", padx=(5, 0))

        # Create the clear button and bind it to the clear_console_text function
        clear_button = ttk.Button(
            self.console_frame,
            text="Clear",
            style="Accent.TButton",
            command=self.clear_console_text,
        )
        clear_button.grid(column=0, row=4, sticky="w", padx=(0, 5))

        # Create a toggle button and bind it to the toggle_auto_scroll function
        self.auto_scroll_enabled = tk.BooleanVar(value=True)
        toggle_button = ttk.Checkbutton(
            self.console_frame, text="Auto Scroll", variable=self.auto_scroll_enabled
        )
        toggle_button.grid(column=1, row=4, sticky="w", pady=(10, 0))

        # Create a toggle button and bind it to the show_all function
        self.show_all_enabled = tk.BooleanVar(value=False)
        toggle_button = ttk.Checkbutton(
            self.console_frame, text="Show All", variable=self.show_all_enabled
        )
        toggle_button.grid(column=2, row=4, sticky="w", pady=(10, 0))

        # Configure column and row weights to ensure proper resizing behavior
        self.console_frame.columnconfigure(0, weight=1)
        self.console_frame.columnconfigure(1, weight=1)
        self.console_frame.columnconfigure(2, weight=1)
        self.console_frame.rowconfigure(1, weight=1)

    def update_console_text(self, new_text: str) -> None:
        if new_text[-1] != "\n":
            new_text += "\n"
        
        #filter esp-inernal messages
        if not self.show_all_enabled.get() and '\r\n' in new_text and "parse" not in new_text:
            return
        
        new_text = new_text.replace('\r','')
        print(">> ", new_text.encode())
        self.console_text.configure(state="normal")
        self.console_text.insert("end", new_text)
        self.console_text.configure(state="disabled")
        # Add auto-scrolling functionality
        if self.auto_scroll_enabled.get():
            self.console_text.see("end")

    def clear_console_text(self) -> None:
        self.console_text.configure(state="normal")
        self.console_text.delete("1.0", "end")
        self.console_text.configure(state="disabled")

    def remove_console(self) -> None:
        self.console_frame.destroy()


    def send_msg(self, input_data):
        if len(input_data) <= 0:
                return
        if input_data[-1] != "\n":
            input_data += "\n"
        self.device.write(input_data.encode())
        self.console_text.config(state="normal")
        self.update_console_text(f">>> {input_data}")
        self.console_text.config(state="disabled")
        self.console_input.delete(0, tk.END)


    def send_serial(self):
        if self.device is not None:
            input_data = self.console_input.get()
            if len(input_data) <= 0:
                return
            if input_data == self.placeholder_text:
                return
            self.send_msg(input_data)
            
        else:
            self.console_text.config(state="normal")
            self.update_console_text("Serial port not connected.\n")
            self.console_text.config(state="disabled")

    def parse_msg(self,msg):
        
        match_adc_voltage = self.adc_pattern.search(msg)
        if match_adc_voltage:
            voltage = float(match_adc_voltage.group(1))
            self.adc_voltage_label.configure(text=f"ADC voltage: {voltage}V")
            return 1
        pos_match = self.pos_pattern.search(msg)

        if pos_match:
            homed = bool(int(pos_match.group(1)))
            steps = int(pos_match.group(2))
            pos = float(pos_match.group(3))
            self.current_steps_label.configure(text = f"Steps: {steps}")
            self.current_position_label.configure(text = f"{pos:.4f}mm")
            self.homed_label.configure(text = "Homed" if homed else "Not Homed")
            return 1
        return 0

    def read_serial(self):
        while not self.stop_serial and self.device is not None:
            if self.device.inWaiting() > 0:
                data = self.device.readline().decode()
                if self.parse_msg(data) == 0:
                    self.update_console_text(data)
        # print("closed")
        if self.device is not None:
            self.device.close()
        self.device = None

    def start(self):
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.app.mainloop()

    def on_closing(self):
        print("closing all threads...")
        self.stop_serial = True
        if hasattr(self, "serial_thread"):
            self.serial_thread.join()
        self.app.destroy()


if __name__ == "__main__":
    app = CubeControlApp()
    app.start()
