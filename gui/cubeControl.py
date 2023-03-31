import tkinter as tk
from tkinter import ttk, messagebox, StringVar
import sv_ttk
import serial.tools.list_ports
import serial
import threading
import re
import os

# current file path to allow the app to be called from outside its own workspace
current_path = os.path.dirname(os.path.realpath(__file__))


class ConfigWindow:
    def __init__(self, parent):
        # refernce to the window and parent
        self.window = None
        self.parent = parent

        # default config variables
        ontime_var = 4000
        offtime_var = 12000
        lower_thr_var = 3.5
        upper_thr_var = 30.0
        auto_sens_var = 10

        self.config = {
            "ontime": [ontime_var, StringVar(value=str(ontime_var))],
            "offtime": [offtime_var, StringVar(value=str(offtime_var))],
            "lower_thr": [lower_thr_var, StringVar(value=str(lower_thr_var))],
            "upper_thr": [upper_thr_var, StringVar(value=str(upper_thr_var))],
            "auto_sens": [auto_sens_var, StringVar(value=str(auto_sens_var))],
        }

    def open(self):
        if self.window and self.window.winfo_exists():
            self.window.destroy()  # Close the existing config window
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Config")
        self.window.resizable(False, False)

        # Make the window spawn in front of the main window
        self.window.transient(self.parent)

        # Add inner padding using a ttk.Frame
        inner_frame = ttk.Frame(self.window, padding=(20, 20, 20, 20))
        inner_frame.pack(fill="both", expand=True)

        # Position the window relative to the main window
        self.window.geometry(
            "+%d+%d" % (self.parent.winfo_x() + 400, self.parent.winfo_y() + 200)
        )
        # Generator Config LabelFrame
        generator_config_label_frame = ttk.LabelFrame(
            inner_frame, text="Generator Settings", padding=10
        )
        generator_config_label_frame.grid(
            column=0, row=0, columnspan=3, sticky="nesw", padx=0, pady=5
        )

        # on Time
        self.ontime_label = ttk.Label(generator_config_label_frame, text="OnTime (ns):")
        self.ontime_label.grid(column=0, row=0)
        self.ontime_entry = ttk.Entry(
            generator_config_label_frame,
            width=9,
            validate="focusout",
            validatecommand=(self.window.register(lambda s: self.validate_entry(s, "ontime", int)),"%P"),
            textvariable=self.config["ontime"][1],
        )
        self.ontime_entry.grid(column=1, row=0, sticky="nesw", padx=15)

        # off Time
        self.offtime_label = ttk.Label(
            generator_config_label_frame, text="OffTime (ns):"
        )
        self.offtime_label.grid(column=0, row=1)
        self.offtime_entry = ttk.Entry(
            generator_config_label_frame,
            width=9,
            validate="focusout",
            validatecommand=(self.window.register(lambda s: self.validate_entry(s, "offtime", int)),"%P"),
            textvariable=self.config["offtime"][1],
        )
        self.offtime_entry.grid(column=1, row=1, sticky="nesw", padx=15)

        # ADC Config LabelFrame
        generator_config_label_frame = ttk.LabelFrame(
            inner_frame, text="ADC Settings", padding=10
        )
        generator_config_label_frame.grid(
            column=0, row=1, columnspan=3, sticky="nesw", padx=0, pady=5
        )

        # lower threshold
        self.lower_thr_label = ttk.Label(
            generator_config_label_frame, text="Lower Threshold (V):"
        )
        self.lower_thr_label.grid(column=0, row=0)
        self.lower_thr_entry = ttk.Entry(
            generator_config_label_frame,
            width=9,
            validate="focusout",
            validatecommand=(self.window.register(lambda s: self.validate_entry(s, "lower_thr", float)),"%P"),
            textvariable=self.config["lower_thr"][1],
        )
        self.lower_thr_entry.grid(column=1, row=0, sticky="nesw", padx=15)

        # higher treshold
        self.upper_thr_label = ttk.Label(
            generator_config_label_frame, text="Upper Threshold (V):"
        )
        self.upper_thr_label.grid(column=0, row=1)
        self.upper_thr_entry = ttk.Entry(
            generator_config_label_frame,
            width=9,
            validate="focusout",
            validatecommand=(self.window.register(lambda s: self.validate_entry(s, "upper_thr", float)),"%P"),
            textvariable=self.config["upper_thr"][1],
        )
        self.upper_thr_entry.grid(column=1, row=1, sticky="nesw", padx=15)

        # auto mode Config LabelFrame
        automode_config_label_frame = ttk.LabelFrame(
            inner_frame, text="Automode Settings", padding=10
        )
        automode_config_label_frame.grid(
            column=0, row=2, columnspan=3, sticky="nesw", padx=0, pady=5
        )

        # auto detection parameter
        self.automode_label = ttk.Label(
            automode_config_label_frame, text="Sensitivity:"
        )
        self.automode_label.grid(column=0, row=0)
        self.automode_entry = ttk.Entry(
            automode_config_label_frame,
            width=9,
            validate="focusout",
            validatecommand=(self.window.register(lambda s: self.validate_entry(s, "auto_sens", int)),"%P"),
            textvariable=self.config["auto_sens"][1],
        )
        self.automode_entry.grid(column=1, row=0, sticky="nesw", padx=15)

    def validate_entry(self, input_str, strvar, type):
        input_value = 0
        try:
            if type == int:
                input_value = int(input_str)
            elif type == float:
                input_value = float(input_str)
            else:
                input_value = -1
            if 0 < input_value <= 100000:
                self.config[strvar][0] = input_value
                return True
        except ValueError:
            pass
        self.config[strvar][1].set(str(self.config[strvar][0]))
        return False


class CubeControlApp:
    def __init__(self) -> None:
        self.device = None
        self.serial_devices = []
        self.update_serial_handle = None

        self.app = tk.Tk()
        self.app.iconbitmap(current_path + "/img/icon.ico")
        self.app.title("CUBEcontrol --- version 1.0")
        self.app.geometry("800x500")
        self.app.resizable(False, False)

        self.adc_pattern = re.compile(r"<ADC>.*calc:(\d+\.\d+)V")
        self.pos_pattern = re.compile(r"POS> homed:(\d) steps:(\d+) pos:(\d+\.\d{4})")
        self.config_window = ConfigWindow(self.app)

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
        image_file = current_path + "/img/background.png"
        self.image = tk.PhotoImage(file=image_file)

        # Create a Canvas widget to hold the image and the text
        self.image_canvas = tk.Canvas(
            self.right_frame, width=400, height=500, bd=0, highlightthickness=0
        )
        self.image_canvas.grid()

        # Display the image on the Canvas
        self.image_canvas.create_image(0, 0, anchor=tk.NW, image=self.image)

        # Add the semi-transparent text in the lower right corner over the image
        version_text = "Marcus Voß 2023"
        self.image_canvas.create_text(330, 480, text=version_text)

        # Logo image
        self.logo_image = tk.PhotoImage(file=current_path + "/img/logo.png")
        self.logo_image_label = ttk.Label(self.left_frame, image=self.logo_image)
        self.logo_image_label.grid(column=0, row=0, columnspan=3)

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
            # send intial messages
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

    def fill_movement_frame(self, parent):
        # Current position label
        self.current_position_label = ttk.Label(parent, text="?")
        self.current_position_label.grid(column=0, row=0, pady=0, padx=(10, 0))

        # Current steps label
        self.current_steps_label = ttk.Label(parent, text="Steps: ?")
        self.current_steps_label.grid(column=1, row=0, pady=0, padx=(0, 0))

        # Homed label
        self.homed_label = ttk.Label(parent, text="Not Homed")
        self.homed_label.grid(column=2, row=0, pady=0, padx=(0, 0))

        # Up arrow button
        self.up_arrow_button = ttk.Button(
            parent,
            text="↑ Up",
            width=9,
            command=lambda: self.send_msg(
                f"G1 Z-{self.movement_steps[self.movement_steps_dropdown.current()]} ;move up {self.movement_steps_dropdown.get()}"
            ),
        )
        self.up_arrow_button.grid(column=0, row=1, pady=10, padx=(0, 0), sticky="nesw")

        # Down arrow button
        self.down_arrow_button = ttk.Button(
            parent,
            text="↓ Down",
            width=9,
            command=lambda: self.send_msg(
                f"G1 Z{self.movement_steps[self.movement_steps_dropdown.current()]} ;move down {self.movement_steps_dropdown.get()}"
            ),
        )
        self.down_arrow_button.grid(
            column=1, row=1, pady=10, padx=(15, 15), sticky="nesw"
        )

        # Movement Step dropdown
        self.movement_steps = [0.5, 1, 2.5, 5, 10, 100, 1000, 5000]
        movement_steps_labels = [
            "0.5µm",
            "1µm",
            "2.5µm",
            "5µm",
            "10µm",
            "100µm",
            "1mm",
            "5mm",
        ]
        self.movement_steps_dropdown = ttk.Combobox(
            parent,
            values=movement_steps_labels,
            font=("Arial", 11),
            state="readonly",
            width=6,
        )
        self.movement_steps_dropdown.current(0)
        self.movement_steps_dropdown.grid(
            column=2, row=1, pady=10, padx=(0, 0), sticky="w"
        )

        # Home button
        self.home_button = ttk.Button(
            parent,
            text="Home",
            width=9,
            command=lambda: self.send_msg("G28 ;home"),
        )
        self.home_button.grid(column=0, row=3, pady=0, padx=(0, 0), sticky="nesw")

        # Restart button
        self.restart_button = ttk.Button(
            parent,
            text="Restart",
            width=9,
            command=lambda: self.send_msg("M0 ;restart"),
        )
        self.restart_button.grid(column=1, row=3, pady=0, padx=(15, 15), sticky="nesw")

        # Touch button
        self.touch_button = ttk.Button(
            parent,
            text="Touch",
            width=9,
            command=lambda: self.send_msg("M102 ;touchmode"),
        )
        self.touch_button.grid(column=2, row=3, pady=0, padx=(0, 0), sticky="nesw")

    def fill_generator_frame(self, parent):
        # Config Button
        self.config_button = ttk.Button(
            parent, text="Config", width=9, command=self.config_window.open
        )
        self.config_button.grid(
            column=0, row=0, pady=(0, 10), padx=(0, 0), sticky="nesw"
        )

        # Enable Button
        self.generator_enable_button = ttk.Button(parent, text="Enable", width=9)
        self.generator_enable_button.grid(
            column=0, row=1, pady=0, padx=(0, 0), sticky="nesw"
        )

        # Disable Button
        self.generator_disable_button = ttk.Button(
            parent,
            text="Disable",
            width=9,
            command=lambda: self.send_msg("M101 ;disable generator"),
        )
        self.generator_disable_button.grid(
            column=1, row=1, pady=0, padx=(15, 15), sticky="nesw"
        )

        # Auto on Button
        self.generator_auto_button = ttk.Button(
            parent,
            text="Auto",
            width=9,
            command=lambda: self.send_msg("M103 ;auto mode"),
        )
        self.generator_auto_button.grid(
            column=2, row=1, pady=0, padx=(0, 0), sticky="nesw"
        )

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

        self.control_frame = ttk.Frame(self.left_frame, padding=10)
        self.control_frame.grid(column=0, row=1, columnspan=2, sticky="w")

        # Generator LabelFrame
        self.generator_label_frame = ttk.LabelFrame(
            self.control_frame, text="Generator", padding=10
        )
        self.generator_label_frame.grid(
            column=0, row=0, columnspan=3, sticky="nesw", padx=0, pady=5
        )

        # ADC LabelFrame
        self.adc_label_frame = ttk.LabelFrame(self.control_frame, text="ADC", padding=0)
        self.adc_label_frame.grid(
            column=0, row=1, columnspan=3, sticky="nesw", padx=0, pady=5
        )

        # Current adc_voltage label
        self.adc_voltage_label = ttk.Label(self.adc_label_frame, text="ADC voltage: ?")
        self.adc_voltage_label.grid(column=0, row=0, pady=5, padx=(10, 0))

        # Movement LabelFrame
        self.movement_label_frame = ttk.LabelFrame(
            self.control_frame, text="Movement", padding=10
        )
        self.movement_label_frame.grid(
            column=0, row=2, columnspan=3, sticky="nesw", padx=0, pady=5
        )
        self.fill_generator_frame(self.generator_label_frame)
        self.fill_movement_frame(self.movement_label_frame)

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

        self.console_text = tk.Text(
            self.console_frame, wrap=tk.WORD, state="disabled", font=("Arial", 10)
        )
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

        # filter esp-inernal messages
        if (
            not self.show_all_enabled.get()
            and "\r\n" in new_text
            and "parse" not in new_text
        ):
            return

        new_text = new_text.replace("\r", "")
        # print(">> ", new_text.encode())
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

    def parse_msg(self, msg):

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
            self.current_steps_label.configure(text=f"Steps: {steps}")
            self.current_position_label.configure(text=f"{pos:.4f}mm")
            self.homed_label.configure(text="Homed" if homed else "Not Homed")
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
